"""
Generate Response Service using Custom ReAct Pattern.

This module implements the supervisor agent for DataPilot using a custom
ReAct (Reasoning + Acting) graph based on langchain-ai/react-agent.

Key differences from previous implementation:
- Explicit graph nodes instead of create_agent (LangChain prebuilt)
- Direct tool execution instead of event stream parsing
- Cleaner progress event emission
- Same RAG + task tools + custom prompt capability
"""

import asyncio
import json
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Any, cast

import litellm
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from loguru import logger

from src.agents.common.prompts import MAIN_AGENT_SYSTEM_PROMPT
from src.agents.supervisor_agent.graph import create_supervisor_graph, SupervisorReActState
from src.agents.assistant_agent.tools.rag_knowledge_tool import create_rag_knowledge_tool
from src.agents.task_agent.tools import get_task_agent_tools
from src.config import settings
from src.domain.conversation import ConversationMessage
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Enable LiteLLM flexibility
litellm.drop_params = True


def _format_rag_documents_as_context(documents: List[Dict[str, Any]]) -> str:
    """Format RAG documents into context string for task tools."""
    if not documents:
        return ""

    context_parts = []
    for idx, doc in enumerate(documents, 1):
        text = doc.get("content") or doc.get("text") or ""
        if text.strip():
            context_parts.append(f"## Document {idx}\n{text}\n")

    return "".join(context_parts)


async def get_response_stream_supervisor(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    conversation_id: str,
    collection_name: str,
    enable_reranking: bool = True,
    relevance_threshold: float = 0.5,
    enable_llm_generation: bool = True,
    top_k: int = 5,
    conversation_description: Optional[str] = None,
    selected_system_prompt_id: Optional[str] = None,
    rag_agent_name: str = "knowledge_expert",
    rag_agent_description: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using Custom ReAct Graph.

    Similar API to previous create_agent implementation but using explicit graph nodes.

    Args:
        query: User's query
        user_id: User ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        conversation_id: Conversation ID
        collection_name: RAG collection name
        enable_reranking: Enable reranking in RAG
        relevance_threshold: Relevance threshold for RAG
        enable_llm_generation: Enable generation tools
        top_k: Top K documents to retrieve
        conversation_description: Description of conversation domain
        selected_system_prompt_id: Custom system prompt ID
        rag_agent_name: Name of RAG tool (default: knowledge_expert)
        rag_agent_description: Description of RAG tool

    Yields:
        Progress events and final response
    """
    start_time = time.time()

    # Track execution state
    response_state = {
        "has_yielded_response": False,
        "error_occurred": False,
        "error_details": None,
        "initialization_complete": False,
        "llm_client": None,
        "final_response": "",
    }

    try:
        logger.info("[Supervisor] Starting ReAct agent execution")

        # Yield initialization START event
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing Supervisor ReAct Agent",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # Build workflow config for RAG tool
        top_k_per_query = max(5, int(top_k * 1.5))

        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "conversation_id": conversation_id,
            "conversation_description": conversation_description,
            "selected_strategy": "custom_variants",
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

        # Get provider configuration
        try:
            provider_service = get_model_provider_service()
            provider = provider_service.get_model_provider(llm_provider_id, user_id)

            if not provider:
                raise ValueError(f"Provider not found: {llm_provider_id}")
            if not provider.is_active:
                raise ValueError(f"Provider is not active: {provider.name}")
            if not provider.api_key or provider.api_key.strip() == "":
                raise ValueError(f"API key not configured for provider '{provider.name}'")

        except ValueError as e:
            response_state["error_occurred"] = True
            response_state["error_details"] = str(e)
            logger.error(f"Provider error: {e}")
            raise

        # Create LLM client
        try:
            model_string = f"{provider.provider_type}/{llm_model_name}"
            generative_config = provider.generative.config if provider.generative else {}
            temperature = generative_config.get("temperature", 0.7)
            max_tokens = generative_config.get("max_tokens", 4096)

            llm_client = ChatLiteLLM(
                model=model_string,
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
                timeout=provider.timeout if provider.timeout else 60,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,
            )
            response_state["llm_client"] = llm_client
            logger.info(f"Created LLM client: {model_string}")

        except Exception as e:
            error_msg = f"Failed to create LLM client: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            raise

        # Add LLM client to workflow config
        workflow_config["llm_client"] = llm_client

        # Track RAG execution state
        rag_execution_state = {
            "documents": [],
            "enhanced_queries": [],
            "enhancement_strategy": "custom_variants",
        }

        # Create RAG tool
        default_rag_description = (
            "Retrieves and ranks relevant documents from the knowledge base. "
            "This is the PRIMARY SOURCE OF TRUTH for accurate information."
        )

        if conversation_description and not rag_agent_description:
            final_rag_description = (
                "Retrieves and ranks relevant documents from the knowledge base. "
                f"Knowledge base domain: {conversation_description}"
            )
        else:
            final_rag_description = rag_agent_description or default_rag_description

        retrieve_knowledge_tool = create_rag_knowledge_tool(
            rag_agent_name=rag_agent_name,
            rag_agent_description=final_rag_description,
            workflow_config=workflow_config,
            rag_execution_state=rag_execution_state,
        )

        # Get task tools
        task_tools = []
        conversation = conversation_history_service.get_conversation(conversation_id)

        if (
            conversation
            and conversation.assistant_config
            and conversation.assistant_config.tools
        ):
            from src.agents.assistant_agent.tools import get_dynamic_task_tools

            try:
                task_tools = await get_dynamic_task_tools(
                    conversation.assistant_config, llm_client, conversation.user_id
                )
                logger.info(f"Loaded {len(task_tools)} dynamic tools")
            except Exception as e:
                logger.error(f"Failed to load dynamic tools: {e}")
                task_tools = get_task_agent_tools()
        else:
            task_tools = get_task_agent_tools()
            logger.info(f"Using {len(task_tools)} default tools")

        # Build system prompt
        system_prompt = MAIN_AGENT_SYSTEM_PROMPT.prompt

        if conversation_description:
            system_prompt += f"\n\n**Knowledge Base Context:**\n{conversation_description}"

        logger.info(f"System prompt length: {len(system_prompt)} chars")

        # Create ReAct graph
        logger.info("Creating supervisor ReAct graph")
        main_agent = create_supervisor_graph(
            llm=llm_client,
            rag_tool=retrieve_knowledge_tool,
            task_tools=task_tools,
            system_prompt=system_prompt,
        )

        response_state["initialization_complete"] = True

        # Yield initialization COMPLETE event
        yield {
            "type": "workflow_progress",
            "stage": "supervisor_init_complete",
            "message": "Supervisor ReAct Agent initialized",
            "data": {
                "orchestrator_type": "custom_react_graph",
                "tools_available": [rag_agent_name] + [t.name for t in task_tools],
                "rag_agent_name": rag_agent_name,
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Yield agent execution STARTING event
        yield {
            "type": "workflow_progress",
            "stage": "agent_execution_starting",
            "message": "Agent analyzing query and planning execution",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Execute graph
        logger.info("Executing ReAct graph")

        config = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 10,
        }

        # Stream graph execution
        final_state = None
        async for event in main_agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
        ):
            logger.debug(f"Graph event: {list(event.keys())}")
            final_state = event

        if final_state is None:
            raise RuntimeError("Graph execution returned no state")

        logger.info("ReAct graph execution completed")

        # Extract final response from state messages
        messages = final_state.get("messages", [])
        logger.debug(f"Final state has {len(messages)} messages")

        final_response = ""
        tools_used = []

        # Extract response and metadata from messages
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                # Prefer task tool output
                if msg.name != rag_agent_name and msg.name in [t.name for t in task_tools]:
                    final_response = str(msg.content)
                    logger.info(f"Using output from task tool: {msg.name}")
                    break
            elif isinstance(msg, AIMessage) and msg.content:
                # Fallback to AI response
                if not final_response:
                    final_response = msg.content
                    logger.info("Using AI message as response")

        # Extract tool usage
        tools_used = final_state.get("tools_used", [])

        # Extract RAG context from state
        rag_documents = final_state.get("rag_documents", {}).get("documents", [])
        rag_context = final_state.get("rag_context", "")

        logger.info(
            f"Response extracted: {len(final_response)} chars, "
            f"{len(tools_used)} tools used, {len(rag_documents)} docs retrieved"
        )

        # Emit response generation events
        yield {
            "type": "workflow_progress",
            "stage": "response_generation_complete",
            "message": "Final response generated",
            "data": {
                "response_length": len(final_response),
                "tools_used": tools_used,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Stream response
        response_state["has_yielded_response"] = True
        yield {
            "type": "streaming_response",
            "chunk": final_response,
            "metadata": {
                "tools_used": tools_used,
                "orchestrator_type": "custom_react_graph",
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Save to conversation history
        try:
            user_message = ConversationMessage(
                role="user",
                content=query,
                timestamp=datetime.now(timezone.utc),
                search_query=query,
            )
            conversation_history_service.add_message(conversation_id, user_message)

            assistant_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
                source_urls=[],
                chunk_ids=[],
                enhancement_strategy_used="custom_variants",
                enhanced_queries=[],
                document_count=len(rag_documents),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(f"Saved conversation to database")

        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

        # Final result
        execution_time_ms = (time.time() - start_time) * 1000

        yield {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "metadata": {
                "orchestrator_type": "custom_react_graph",
                "tools_used": tools_used,
                "document_count": len(rag_documents),
            },
            "documents": rag_documents,
        }

        logger.info(f"ReAct agent completed in {execution_time_ms:.2f}ms")

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Supervisor ReAct execution failed: {str(e)}"
        response_state["error_occurred"] = True
        response_state["error_details"] = error_msg

        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Clean up LLM client
        try:
            if response_state["llm_client"] and hasattr(response_state["llm_client"], "close"):
                response_state["llm_client"].close()
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")

        # Yield error event
        if not response_state["has_yielded_response"]:
            error_category = (
                "initialization_error"
                if not response_state["initialization_complete"]
                else "execution_error"
            )

            yield {
                "type": "supervisor_error",
                "error": str(e),
                "error_category": error_category,
                "execution_time_ms": execution_time_ms,
                "workflow_completed": False,
                "query": query,
                "response": f"Error: {str(e)[:100]}",
                "initialization_complete": response_state["initialization_complete"],
            }
