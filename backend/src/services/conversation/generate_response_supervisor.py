"""
Generate Response Service for Supervisor Agent Mode

This module handles the execution of the multi-agent supervisor orchestration
using the LangGraph Supervisor library for intelligent intent routing and
multi-agent coordination.

The supervisor automatically:
- Detects user intent (via LLM reasoning)
- Routes to appropriate agents (RAG, Task, or both)
- Manages context injection between agents
- Returns synthesized final response
"""

import asyncio
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

import litellm
from langchain_community.chat_models import ChatLiteLLM
from loguru import logger
from opik.integrations.langchain import OpikTracer
from opik.integrations.litellm import track_litellm

from langgraph_supervisor import create_supervisor

from src.agents.common.agent_state import AgentState
from src.agents.rag_agent import RAGAgentService
from src.agents.task_agent import TaskAgentService
from src.agents.rag_agent.graph import graph_dev as workflow
from src.domain.conversation import ConversationMessage
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Enable dropping unsupported params for different LLM providers
litellm.drop_params = True


async def get_response_stream_supervisor(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    conversation_id: str,
    collection_name: str,
    selected_strategy: Optional[str] = None,
    retrieval_strategy: Optional[str] = None,
    enhancement_config: Optional[Dict[str, Any]] = None,
    enable_reranking: bool = True,
    relevance_threshold: float = 0.5,
    enable_llm_generation: bool = False,  # Default False in supervisor mode for Task Agent context
    top_k: int = 5,
    conversation_description: Optional[str] = None,
    selected_system_prompt_id: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using Supervisor Agent for intelligent routing.

    **SUPERVISOR MODE ONLY** - Uses LangGraph Supervisor library for:
    - LLM-driven intent detection and routing
    - Automatic tool-based handoff between agents
    - Context injection from RAG to Task Agent
    - Multi-turn agent orchestration

    The supervisor LLM decides whether to:
    1. Retrieve documents only (RAG)
    2. Execute task with document context (RAG → Task)
    3. Execute task directly (Task only)

    Args:
        query: User's input query
        user_id: User identifier
        llm_provider_id: LLM provider ID for supervisor reasoning
        llm_model_name: LLM model name
        conversation_id: Conversation session ID
        collection_name: Vector DB collection for document retrieval
        selected_strategy: Query enhancement strategy (decomposition, multi_query, etc.)
        enable_reranking: Whether to rerank retrieved documents
        enable_llm_generation: Whether to generate answers (False in supervisor - raw docs for Task)
        top_k: Number of documents to retrieve
        conversation_description: Optional knowledge base description
        selected_system_prompt_id: Optional system prompt for Task Agent

    Yields:
        Dict with progress events tracking supervisor orchestration
    """
    start_time = time.time()

    try:
        # ========== PHASE 1: INITIALIZATION ==========

        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing supervisor agent orchestration",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # Prepare workflow configuration
        top_k_per_query = max(5, int(top_k * 1.5))

        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "enhancement_config": enhancement_config or {},
            "conversation_id": conversation_id,
            "enable_reranking": enable_reranking,
            "reranking_config": {
                "relevance_threshold": relevance_threshold,
                "use_score_based": True,
            },
            "enable_llm_generation": enable_llm_generation,
            "top_k": top_k,
            "retrieval_config": {
                "top_k_per_query": top_k_per_query,
                "rrf_k": 60,
            },
        }

        logger.info(
            f"🔧 Supervisor Config: strategy={selected_strategy}, collection={collection_name}"
        )

        # Auto-set strategy to decomposition in supervisor mode
        original_strategy = selected_strategy
        if selected_strategy != "decomposition":
            selected_strategy = "decomposition"
            logger.info(
                f"🔄 [SUPERVISOR MODE] Auto-changing strategy: '{original_strategy or 'native'}' → 'decomposition'"
            )

            yield {
                "type": "supervisor_progress",
                "stage": "strategy_auto_adjusted",
                "message": f"Enhancement strategy auto-set to 'decomposition' (original: '{original_strategy or 'native'}')",
                "data": {
                    "original_strategy": original_strategy or "native",
                    "new_strategy": "decomposition",
                    "reason": "Decomposition provides optimal query breakdown for multi-agent coordination",
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Retrieve system prompt if selected
        selected_system_prompt = None
        if selected_system_prompt_id:
            try:
                selected_system_prompt = conversation_history_service.get_system_prompt(
                    conversation_id=conversation_id,
                    prompt_id=selected_system_prompt_id,
                    user_id=user_id,
                )
                if selected_system_prompt:
                    logger.info(
                        f"📝 [SUPERVISOR] Using system prompt: '{selected_system_prompt.name}'"
                    )
                    workflow_config["selected_system_prompt"] = selected_system_prompt
            except Exception as e:
                logger.error(f"⚠️ [SUPERVISOR] Error retrieving system prompt: {e}")

        # Get LLM provider and create client
        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(llm_provider_id, user_id)

        if not provider:
            raise ValueError(f"Provider not found: {llm_provider_id}")

        if not provider.is_active:
            raise ValueError(f"Provider is not active: {provider.name}")

        generative_config = provider.generative.config if provider.generative else {}
        temperature = generative_config.get("temperature", 0.7)
        max_tokens = generative_config.get("max_tokens", 4096)

        model_string = f"{provider.provider_type}/{llm_model_name}"
        llm_client = ChatLiteLLM(
            model=model_string,
            api_key=provider.api_key,
            api_base=provider.endpoint if provider.endpoint else None,
            timeout=provider.timeout if provider.timeout else 60,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"✅ Created LLM client: {model_string} (temperature={temperature}, max_tokens={max_tokens})"
        )

        workflow_config["llm_client"] = llm_client

        # ========== PHASE 2: SUPERVISOR CREATION ==========

        logger.info("🤖 Creating supervisor using langgraph-supervisor library")

        # Create RAG and Task agents
        rag_agent = RAGAgentService(
            llm_client=llm_client,
            rag_graph=workflow,
            conversation_service=None,
        )
        task_agent = TaskAgentService(llm_client=llm_client)

        # Create supervisor graph using official langgraph-supervisor pattern
        # Following: https://github.com/langchain-ai/langgraph-supervisor-py
        supervisor_prompt = """You are an intelligent supervisor orchestrating multiple specialist agents.

Available agents:
1. **RAG Agent** - Document retrieval and ranking from knowledge base
   - Use when user needs information from documents
   - Gather knowledge before task execution

2. **Task Agent** - Task execution, analysis, and code generation
   - Use for tasks requiring action or reasoning
   - Has access to RAG context if documents were retrieved

Your routing strategy:
- For document questions: Use RAG Agent
- For tasks needing knowledge: Use RAG Agent first, then Task Agent
- For pure tasks: Use Task Agent directly
- Always provide agents with full context

Be decisive about routing."""

        supervisor_graph = create_supervisor(
            agents=[rag_agent.rag_graph, task_agent.task_graph],
            model=llm_client,
            prompt=supervisor_prompt,
            output_mode="last_message",
            add_handoff_messages=True,
            handoff_tool_prefix="delegate_to_",
        )

        # Create initial state for supervisor
        supervisor_initial_state = AgentState(
            messages=[{"role": "user", "content": query}],
            conversation_id=conversation_id,
            user_id=user_id,
            config=workflow_config,
            conversation_description=conversation_description,
        )

        if selected_system_prompt:
            supervisor_initial_state["system_prompt_task"] = selected_system_prompt

        yield {
            "type": "supervisor_progress",
            "stage": "supervisor_init_complete",
            "message": "Supervisor orchestrator initialized successfully",
            "data": {
                "orchestrator_type": "langgraph_supervisor",
                "agents_available": ["rag_agent", "task_agent"],
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # ========== PHASE 3: SUPERVISOR EXECUTION ==========

        logger.info("📊 Executing supervisor orchestration with intent routing")

        yield {
            "type": "supervisor_progress",
            "stage": "supervisor_reasoning",
            "message": "Supervisor analyzing query and determining routing strategy",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        orchestration_start = time.time()

        # Execute the supervisor graph using official pattern
        # The LangGraph Supervisor library handles:
        # 1. LLM-driven intent detection
        # 2. Tool-based handoff to agents (delegate_to_rag_agent, delegate_to_task_agent)
        # 3. Context injection between agents
        # 4. Final response synthesis
        logger.info("🚀 Invoking supervisor graph for orchestration")

        # Use astream_events to track orchestration progress
        final_result_state = None

        async for event in supervisor_graph.astream_events(
            input=supervisor_initial_state,
            config={"configurable": {"thread_id": str(start_time)}},
            version="v2",
        ):
            event_type = event.get("event", "")
            node_name = event.get("name", "")
            event_data = event.get("data", {})

            # Log node execution for visibility
            if event_type == "on_chain_start":
                if node_name in ["supervisor", "delegate_to_rag_agent", "delegate_to_task_agent"]:
                    logger.info(f"▶️ Supervisor Graph: Entering node '{node_name}'")

            elif event_type == "on_chain_end":
                if node_name == "LangGraph":
                    # Final output from supervisor graph
                    logger.info(
                        "✅ Supervisor Graph completed - capturing final state"
                    )
                    output = event_data.get("output")
                    if output:
                        final_result_state = output

        # If we got the final state from events, use it
        if final_result_state:
            logger.info("📊 Using final state from graph astream_events")
            result_state = final_result_state
        else:
            # Fallback: invoke synchronously if events didn't provide final state
            logger.info(
                "📊 Events incomplete, invoking supervisor graph synchronously"
            )
            result_state = await supervisor_graph.ainvoke(
                supervisor_initial_state,
                config={"configurable": {"thread_id": str(start_time)}},
            )

        orchestration_time_ms = (time.time() - orchestration_start) * 1000
        logger.info(f"✅ Supervisor orchestration completed in {orchestration_time_ms:.2f}ms")

        # ========== PHASE 4: RESULTS SYNTHESIS ==========

        yield {
            "type": "supervisor_progress",
            "stage": "orchestration_complete",
            "message": "Supervisor orchestration completed successfully",
            "data": {
                "intent": result_state.get("intent", "unknown"),
                "rag_executed": bool(result_state.get("rag_context")),
                "task_executed": bool(result_state.get("task_result")),
                "orchestration_time_ms": orchestration_time_ms,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Extract final response from result state
        final_response = ""
        if result_state.get("task_result"):
            final_response = result_state.get("task_result")
        elif result_state.get("rag_context"):
            final_response = f"Retrieved {result_state['rag_context'].get('relevant_count', 0)} relevant documents"
        else:
            final_response = result_state.get("messages", [{}])[-1].get("content", "")

        # Save conversation messages
        try:
            conversation_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
            )
            conversation_history_service.add_message(
                conversation_id, user_id, conversation_message
            )
            logger.info("✅ Conversation message saved")
        except Exception as e:
            logger.error(f"⚠️ Failed to save conversation message: {e}")

        # Final result
        yield {
            "type": "supervisor_result",
            "workflow_completed": True,
            "response": final_response,
            "intent": result_state.get("intent", "unknown"),
            "rag_context": result_state.get("rag_context"),
            "task_result": result_state.get("task_result"),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"❌ Supervisor orchestration failed after {execution_time_ms:.2f}ms: {e}"
        )
        logger.error(f"Traceback: {traceback.format_exc()}")

        yield {
            "type": "supervisor_error",
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "workflow_completed": False,
            "response": f"I encountered an error while processing your query: {str(e)}",
        }
