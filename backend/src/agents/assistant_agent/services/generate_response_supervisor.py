"""
Generate Response Service using Tool Calling Pattern (LangChain Recommended)

This module implements the OFFICIAL LangChain multi-agent pattern:
https://docs.langchain.com/oss/python/langchain/multi-agent

The RAG agent is wrapped as a tool that the main ReAct agent can invoke.

**ORCHESTRATION FLOW & UI PROGRESS STAGES:**

Supervisor Orchestration → Progress Stages Sent to UI:

1. supervisor_init_complete
   └─ UI Display: "Initializing Multi-Agent System"

2. agent_execution_starting
   └─ UI Display: "Analyzing Query & Planning"

3. rag_agent_executing
   └─ UI Display: "Retrieving Knowledge Base Documents"

4. rag_documents_extracted
   └─ UI Display: "Processing Retrieved Documents"

5. task_agent_executing (if generation tools needed)
   └─ UI Display: "Generating Response with Tools"

6. response_generation_complete
   └─ UI Display: "Response Generated"

7. response_streaming_started
   └─ UI Display: "Streaming Response"

8. workflow_complete
   └─ UI Display: "Complete"

**IMPORTANT: Frontend should map these stage names to UI progress nodes.
DO NOT show "Intent Detection" - that is from old architecture.**
"""

import asyncio
import json
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional, TypedDict, cast

import litellm
from langchain.agents import create_agent
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from loguru import logger
from opik.integrations.langchain import OpikTracer

# Import compatibility shim for opik with LangChain 1.0+ (MUST be first)
import src.compat_langchain_load  # noqa: F401
from src.agents.assistant_agent.services.agent_state import (
    SupervisorAgentState,
    create_initial_state,
    extract_execution_metrics,
)
from src.agents.assistant_agent.services.error_retry_middleware import (
    RetryConfig,
    create_circuit_breakers,
    execute_with_retry,
)
from src.agents.assistant_agent.tools.rag_knowledge_tool import (
    create_rag_knowledge_tool,
)
from src.agents.assistant_agent.tools.tool_middleware import (
    apply_middleware_to_tools,
    inject_rag_context_to_task_tool,
    set_current_agent_state,
)
from src.agents.common.prompts import MAIN_AGENT_SYSTEM_PROMPT
from src.agents.task_agent.tools import get_task_agent_tools
from src.config import settings
from src.domain.conversation import ConversationMessage
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Enable dropping unsupported params for different LLM providers
litellm.drop_params = True

# Enable Opik integration for cost and token tracking
# This will track all LLM invocations automatically when OPIK_API_KEY is set
# litellm.callbacks = ["opik"]


def _format_rag_documents_as_context(documents: List[Dict[str, Any]]) -> str:
    """
    Format RAG documents into a context string for task tools.
    Only includes document content - no metadata (to save tokens).

    Args:
        documents: List of document dictionaries from RAG

    Returns:
        Formatted context string with document content only
    """
    if not documents:
        return ""

    context_parts = []
    for idx, doc in enumerate(documents, 1):
        # RAG tool returns 'content', also support 'text' for backward compatibility
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
    # Note: selected_strategy, retrieval_strategy, enhancement_config removed
    # Supervisor ALWAYS uses 'custom_variants' (no LLM enhancement, supervisor generates variants)
    # RRF is auto-enabled when multiple variants are passed to RAG
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
    Generate AI response using Tool Calling Pattern (LangChain recommended).

    The RAG agent is wrapped as a tool that the main ReAct agent invokes.
    Reference: https://docs.langchain.com/oss/python/langchain/multi-agent

    **IMPORTANT**: The supervisor agent ALWAYS uses 'custom_variants' strategy.
    The supervisor generates query variants through intent analysis and passes them
    to the RAG agent for parallel search with RRF fusion.

    **Resource Management**:
    - All resources are properly tracked in response_state dict
    - Errors during execution are properly caught and propagated
    - Partial responses are prevented by tracking streaming state
    """
    start_time = time.time()

    # Central response state tracking - ensures no silent failures
    response_state = {
        "has_yielded_response": False,  # Tracks if we've started streaming the final response
        "error_occurred": False,  # Tracks if any error has occurred
        "error_details": None,  # Stores error information
        "initialization_complete": False,  # Tracks initialization success
        "llm_client": None,  # Reference for cleanup
        "final_response": "",  # Stores final response
        "execution_messages": [],  # Messages from agent execution
    }

    try:
        # Supervisor agent ALWAYS uses custom_variants strategy (hardcoded)
        # The supervisor generates query variants through intent analysis
        selected_strategy = "custom_variants"

        logger.info(
            f"Supervisor Agent Mode: Using strategy='custom_variants' (intent analysis + variant generation)"
        )

        # Yield initialization START event
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing Multi-Agent System (Tool Calling Pattern)",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # Initialize workflow config for RAG agent
        top_k_per_query = max(5, int(top_k * 1.5))

        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "enhancement_config": {},  # Empty - custom_variants doesn't use LLM enhancement
            "conversation_id": conversation_id,
            "conversation_description": conversation_description,  # Added for RAG state creation
            "selected_strategy": selected_strategy,  # Added - always 'custom_variants' for supervisor
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
                error_msg = f"Provider not found: {llm_provider_id}"
                response_state["error_occurred"] = True
                response_state["error_details"] = error_msg
                logger.error(error_msg)
                raise ValueError(error_msg)

            if not provider.is_active:
                error_msg = f"Provider is not active: {provider.name}"
                response_state["error_occurred"] = True
                response_state["error_details"] = error_msg
                logger.error(error_msg)
                raise ValueError(error_msg)

            if not provider.api_key or provider.api_key.strip() == "":
                error_msg = f"API key not configured for provider '{provider.name}'"
                response_state["error_occurred"] = True
                response_state["error_details"] = error_msg
                logger.error(error_msg)
                raise ValueError(error_msg)

        except ValueError as e:
            # Re-raise ValueError with proper context
            raise

        # Get temperature and max_tokens from provider's generative config
        generative_config = provider.generative.config if provider.generative else {}
        temperature = generative_config.get("temperature", 0.7)
        max_tokens = generative_config.get("max_tokens", 4096)

        # Create LLM client
        try:
            model_string = f"{provider.provider_type}/{llm_model_name}"

            llm_client = ChatLiteLLM(
                model=model_string,
                api_key=provider.api_key,
                api_base=provider.endpoint if provider.endpoint else None,
                timeout=provider.timeout if provider.timeout else 60,  # type: ignore[call-arg]
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,  # Enable streaming for real-time response chunks
            )
            response_state["llm_client"] = llm_client  # Track for cleanup
            logger.info(f"Created LLM client: {model_string}")
        except Exception as e:
            error_msg = f"Failed to create LLM client: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Add LLM client to workflow config
        workflow_config["llm_client"] = llm_client

        # Retrieve selected system prompt if provided
        # TODO: Implement get_system_prompt method in ConversationHistoryService
        # For now, system prompt selection is not implemented - always use default
        selected_system_prompt = None
        if selected_system_prompt_id:
            logger.warning(
                f"System prompt selection requested (ID: {selected_system_prompt_id}) but not yet implemented - using default prompt"
            )

        # Track RAG execution state (shared across tool invocations)
        rag_execution_state = {
            "stages_emitted": set(),
            "total_docs": 0,
            "relevant_docs": 0,
            "documents": [],
            "enhanced_queries": [],
            "enhancement_strategy": selected_strategy or "custom_variants",
            "final_answer": "",
        }

        # Build RAG agent description
        # For custom_variants strategy: Tool description should just describe what it does,
        # not how to use it (that's in the system prompt)
        default_rag_description = (
            "Retrieves and ranks relevant documents from the knowledge base. "
            "This is the PRIMARY SOURCE OF TRUTH for accurate information."
        )

        # Use conversation description as the tool description if available
        # This tells the agent what domain/topic the knowledge base covers
        if conversation_description and not rag_agent_description:
            final_rag_description = (
                "Retrieves and ranks relevant documents from the knowledge base. "
                f"Knowledge base domain: {conversation_description}"
            )
        else:
            final_rag_description = rag_agent_description or default_rag_description

        # Create RAG tool using factory function from tools package
        # All config is in workflow_config - no duplication
        retrieve_knowledge_tool = create_rag_knowledge_tool(
            rag_agent_name=rag_agent_name,
            rag_agent_description=final_rag_description,
            workflow_config=workflow_config,  # Contains ALL config including strategy, descriptions, IDs
            rag_execution_state=rag_execution_state,
        )

        # Get task agent tools - dynamic or hardcoded fallback
        task_tools = []

        # Load conversation to check for dynamic tool configuration
        conversation = conversation_history_service.get_conversation(conversation_id)

        if (
            conversation
            and conversation.assistant_config
            and conversation.assistant_config.tools
        ):
            # Use dynamic tools from conversation configuration
            from src.agents.assistant_agent.tools import get_dynamic_task_tools

            try:
                task_tools = await get_dynamic_task_tools(
                    conversation.assistant_config, llm_client, conversation.user_id
                )
                logger.info(
                    f"Loaded {len(task_tools)} dynamic tools from conversation config"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load dynamic tools, falling back to defaults: {e}"
                )
                task_tools = get_task_agent_tools()
        else:
            # Fallback to hardcoded default tools for backward compatibility
            task_tools = get_task_agent_tools()
            logger.info(
                f"No dynamic tools configured, using {len(task_tools)} default hardcoded tools"
            )

        # Inject RAG context injection into task tools
        # This wraps each task tool so it will receive RAG context as a parameter at call time
        logger.info("Applying RAG context injection to task tools")
        try:
            task_tools_with_rag = []
            for task_tool in task_tools:
                wrapped_tool = inject_rag_context_to_task_tool(task_tool)
                task_tools_with_rag.append(wrapped_tool)
            task_tools = task_tools_with_rag
            logger.info(
                f"✅ RAG context injection applied to {len(task_tools)} task tools"
            )
        except Exception as e:
            logger.warning(f"Failed to apply RAG context injection to task tools: {e}")
            # Continue with unwrapped tools

        # Combine RAG tool + task tools
        all_tools = [retrieve_knowledge_tool] + task_tools

        logger.info(
            f"Created {len(all_tools)} tools total: 1 RAG tool + {len(task_tools)} task tools"
        )

        # Apply tool middleware for timeouts and validation
        logger.info("Applying tool middleware (timeouts + validation)")
        try:
            all_tools = apply_middleware_to_tools(
                all_tools,
                timeout_seconds=60.0,  # 60s timeout for all tools
                validate_input=True,
                validate_output=True,
            )
            logger.info("✅ Tool middleware applied successfully")
        except Exception as e:
            logger.warning(
                f"Failed to apply tool middleware: {e}. Using tools without middleware."
            )

        # Store original task tools for reference
        response_state["original_task_tools"] = task_tools
        response_state["all_tools"] = all_tools

        # Create circuit breakers for error resilience
        circuit_breakers = create_circuit_breakers()
        logger.info("✅ Circuit breakers initialized")

        # Build system prompt for main agent
        system_prompt_parts = []

        # Base prompt: Use custom prompt if provided, otherwise use our standard main agent prompt
        if selected_system_prompt and selected_system_prompt.prompt_template:
            base_prompt = selected_system_prompt.prompt_template
        else:
            # Use the properly structured prompt from our prompts package
            base_prompt = MAIN_AGENT_SYSTEM_PROMPT.prompt

        # If user has tool instructions, inject them INTO STEP 5 (where tool decisions are made)
        if (
            assistant_config
            and assistant_config.tool_instructions
            and assistant_config.tool_instructions.strip()
        ):
            logger.info(
                "✅ User-configured tool instructions found - injecting into STEP 5"
            )

            # Find STEP 5 in the prompt
            step_5_marker = "**STEP 5️⃣: EXECUTE TOOLS WITH COMPLETE CONTEXT**"
            if step_5_marker in base_prompt:
                # Find the injection point (right after the step header)
                injection_point = base_prompt.find(step_5_marker) + len(step_5_marker)

                # Create user instructions section with high priority
                user_instructions_section = f"""

🎯 **USER-SPECIFIC TOOL ORCHESTRATION (HIGHEST PRIORITY):**

{assistant_config.tool_instructions}

**NOTE:** The above instructions are user-configured and take PRECEDENCE over default tool usage patterns below.

---
"""
                # Inject into the prompt
                base_prompt = (
                    base_prompt[:injection_point]
                    + user_instructions_section
                    + base_prompt[injection_point:]
                )
                logger.info(
                    f"✅ Injected {len(assistant_config.tool_instructions)} chars of tool instructions into STEP 5"
                )
            else:
                # Fallback: If STEP 5 not found (custom prompt), append at the end
                logger.warning(
                    "⚠️ STEP 5 marker not found in prompt - appending instructions at end"
                )
                system_prompt_parts.append(base_prompt)
                system_prompt_parts.append(
                    f"\n\n**User-Configured Tool Usage Instructions:**\n\n{assistant_config.tool_instructions}"
                )
                base_prompt = None  # Signal that we already appended

        # Add the base prompt (if not already added in fallback path)
        if base_prompt is not None:
            system_prompt_parts.append(base_prompt)

        # Add knowledge base context if available
        if conversation_description:
            system_prompt_parts.append(
                f"\n\n**Knowledge Base Context:**\n{conversation_description}"
            )

        system_prompt = "\n".join(system_prompt_parts)

        # Create main ReAct agent with Tool Calling pattern (LangChain recommended)
        logger.info("Creating main ReAct agent with Tool Calling pattern")
        logger.info(
            f"Passing {len(all_tools)} tools to agent: {[t.name for t in all_tools]}"
        )
        logger.debug(f"System prompt length: {len(system_prompt)} characters")
        logger.debug(f"System prompt first 500 chars: {system_prompt[:500]}...")

        # Initialize agent state using LangGraph MessagesState pattern
        agent_state: SupervisorAgentState = create_initial_state(query)
        logger.debug(f"Initialized LangGraph agent state for query: {query[:100]}...")

        # Set agent state for RAG context injection (tools will retrieve from here)
        set_current_agent_state(agent_state)
        logger.debug("Agent state set in tool middleware for RAG context injection")

        main_agent = create_agent(
            model=llm_client,
            tools=all_tools,
            system_prompt=system_prompt,
        )

        logger.info("Main ReAct agent created successfully")
        logger.info(
            f"✅ Agent created with {len(all_tools)} tools: {[t.name for t in all_tools]}"
        )

        # Configure Opik tracing (if enabled)
        config_for_stream = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 10,
        }

        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Supervisor config: strategy={selected_strategy}, "
                f"collection={collection_name}, provider={llm_provider_id}, model={llm_model_name}"
            )
            # OpikTracer will be added to config_for_stream callbacks below
            logger.debug("Opik tracing configured via OpikTracer in config")

            # Build tags for Opik trace
            trace_tags = [
                "supervisor_agent",
                "tool_calling_pattern",
                f"strategy:{selected_strategy or 'custom_variants'}",
                f"provider:{llm_provider_id}",
                f"model:{llm_model_name}",
                f"collection:{collection_name}",
                f"conversation:{conversation_id}",
            ]
            if conversation_description:
                trace_tags.append(f"domain:{conversation_description[:50]}")

            # Create OpikTracer for main agent graph
            opik_tracer = OpikTracer(
                graph=main_agent.get_graph(xray=True),
                tags=trace_tags,
                project_name=settings.AGENT_TRACING_PROJECT_NAME,
            )

            # Add tracer to config callbacks
            config_for_stream["callbacks"] = [opik_tracer]
            logger.debug("OpikTracer configured for supervisor agent")
        else:
            logger.debug(
                f"Agent tracing disabled: Supervisor config: strategy={selected_strategy}, collection={collection_name}"
            )

        # Mark initialization as complete (critical for error handling)
        response_state["initialization_complete"] = True
        logger.info("Supervisor initialization completed successfully")

        # Yield supervisor initialization START event
        yield {
            "type": "workflow_progress",
            "stage": "supervisor_init_complete",
            "message": "Multi-Agent System initialized (Tool Calling Pattern)",
            "data": {
                "orchestrator_type": "tool_calling_pattern",
                "tools_available": [f"{rag_agent_name} (RAG)"]
                + [t.name for t in task_tools],
                "rag_agent_name": rag_agent_name,
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
                "tracing_enabled": settings.AGENT_TRACING_ENABLED,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Execute main agent and stream events
        logger.info("Starting main agent execution with error resilience")

        # Emit agent execution STARTING event (no _complete suffix - just the stage name)
        yield {
            "type": "workflow_progress",
            "stage": "agent_execution_starting",
            "message": "Agent analyzing query and preparing execution plan",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Track state
        final_messages = []
        tools_used = []
        rag_tool_called = False
        agent_execution_complete_emitted = (
            False  # Track if we've emitted agent_execution_starting_complete
        )
        retrieved_rag_documents = (
            None  # Track RAG results for injection into task tools
        )

        # Stream events from main agent with explicit error tracking and retry logic
        try:
            # Configure retry for agent execution
            retry_config = RetryConfig(
                max_attempts=3,
                initial_delay_ms=500,
                max_delay_ms=5000,
                exponential_base=2.0,
                jitter=True,
            )

            # Execute agent with retry logic and circuit breaker
            async def agent_execution():
                """Execute agent with astream_events"""
                event_stream = main_agent.astream_events(
                    {"messages": [{"role": "user", "content": query}]},
                    config=cast(RunnableConfig, config_for_stream),
                    version="v2",
                )
                return event_stream

            logger.info(
                "Starting agent execution with retry protection and circuit breaker"
            )
            event_iterator = await execute_with_retry(
                agent_execution,
                func_name="main_agent_execution",
                retry_config=retry_config,
                circuit_breaker=circuit_breakers.get("llm_client"),
            )

            async for event in event_iterator:
                event_type = event.get("event", "")
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Early extraction of RAG documents (on_tool_end event)
                # This must happen before checking tool calls to ensure context is available
                if event_type == "on_tool_end":
                    try:
                        tool_name = event.get("name", "")

                        # Track tool execution (add to tools_used if not already there)
                        if tool_name and tool_name not in tools_used:
                            tools_used.append(tool_name)
                            logger.info(f"✅ Tool execution completed: {tool_name}")

                        # Emit tool completion events
                        if tool_name == rag_agent_name:
                            # Will emit rag_agent_executing_complete after documents extracted
                            pass
                        elif tool_name in [t.name for t in task_tools]:
                            # Emit task agent execution COMPLETE event
                            yield {
                                "type": "workflow_progress",
                                "stage": f"{tool_name}_complete",
                                "message": f"Task execution completed: {tool_name}",
                                "data": {
                                    "tool_name": tool_name,
                                    "tools_used": agent_state.get("tools_used", []),
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                        if tool_name == rag_agent_name:
                            # Extract RAG documents from tool output
                            tool_output = event_data.get("output", "")
                            logger.debug(
                                f"Processing RAG tool output: {type(tool_output).__name__}"
                            )

                            if tool_output:
                                # Handle ToolMessage objects from LangChain
                                # ToolMessage has a 'content' attribute
                                if hasattr(tool_output, "content"):
                                    tool_output_content = tool_output.content
                                else:
                                    tool_output_content = tool_output

                                if tool_output_content:
                                    try:
                                        # Handle both string and dict outputs
                                        if isinstance(tool_output_content, str):
                                            rag_response = json.loads(
                                                tool_output_content
                                            )
                                        else:
                                            rag_response = tool_output_content

                                        if (
                                            isinstance(rag_response, dict)
                                            and "documents" in rag_response
                                        ):
                                            retrieved_rag_documents = rag_response.get(
                                                "documents", []
                                            )

                                            # Format RAG documents as context string
                                            rag_context_str = (
                                                _format_rag_documents_as_context(
                                                    retrieved_rag_documents
                                                )
                                            )

                                            # Store RAG context in agent state using LangGraph method
                                            agent_state.set_rag_context(
                                                retrieved_rag_documents, rag_context_str
                                            )

                                            # CRITICAL: Store documents in rag_execution_state for metadata
                                            rag_execution_state["documents"] = (
                                                retrieved_rag_documents
                                            )
                                            rag_execution_state["total_docs"] = len(
                                                retrieved_rag_documents
                                            )
                                            rag_execution_state["relevant_docs"] = len(
                                                retrieved_rag_documents
                                            )

                                            logger.info(
                                                f"✅ RAG retrieval complete: {len(retrieved_rag_documents)} documents ({len(rag_context_str)} chars)"
                                            )

                                            # Emit RAG documents extracted COMPLETE event
                                            yield {
                                                "type": "workflow_progress",
                                                "stage": "rag_documents_extracted",
                                                "message": f"RAG Complete: Extracted {len(retrieved_rag_documents)} documents",
                                                "data": {
                                                    "rag_documents_count": len(
                                                        retrieved_rag_documents
                                                    ),
                                                    "rag_context_size": len(
                                                        rag_context_str
                                                    ),
                                                    "tools_used": agent_state.get(
                                                        "tools_used", []
                                                    ),
                                                    "enhanced_queries": rag_execution_state.get(
                                                        "enhanced_queries", []
                                                    ),
                                                },
                                                "execution_time_ms": (
                                                    time.time() - start_time
                                                )
                                                * 1000,
                                            }

                                            # Emit agent execution COMPLETE event (after RAG retrieval)
                                            if not agent_execution_complete_emitted:
                                                agent_execution_complete_emitted = True
                                                yield {
                                                    "type": "workflow_progress",
                                                    "stage": "agent_execution_starting_complete",
                                                    "message": "Agent execution planning completed",
                                                    "data": {
                                                        "rag_documents_count": len(
                                                            retrieved_rag_documents
                                                        ),
                                                        "tools_used": agent_state.get(
                                                            "tools_used", []
                                                        ),
                                                    },
                                                    "execution_time_ms": (
                                                        time.time() - start_time
                                                    )
                                                    * 1000,
                                                }

                                            # Emit RAG agent execution COMPLETE event
                                            yield {
                                                "type": "workflow_progress",
                                                "stage": "rag_agent_executing_complete",
                                                "message": f"RAG agent execution completed with {len(retrieved_rag_documents)} documents",
                                                "data": {
                                                    "document_count": len(
                                                        retrieved_rag_documents
                                                    ),
                                                    "context_size": len(
                                                        rag_context_str
                                                    ),
                                                    "strategy": rag_execution_state.get(
                                                        "enhancement_strategy",
                                                        "unknown",
                                                    ),
                                                    "tools_used": agent_state.get(
                                                        "tools_used", []
                                                    ),
                                                },
                                                "execution_time_ms": (
                                                    time.time() - start_time
                                                )
                                                * 1000,
                                            }

                                            # Emit task agent execution START event
                                            # This marks the beginning of task tool execution phase
                                            yield {
                                                "type": "workflow_progress",
                                                "stage": "task_agent_executing",
                                                "message": "Starting task tool execution with RAG context",
                                                "data": {
                                                    "available_tools": [
                                                        t.name for t in task_tools
                                                    ],
                                                    "rag_context_available": True,
                                                },
                                                "execution_time_ms": (
                                                    time.time() - start_time
                                                )
                                                * 1000,
                                            }
                                        else:
                                            logger.debug(
                                                f"RAG response missing 'documents' key. Keys: {rag_response.keys() if isinstance(rag_response, dict) else 'N/A'}"
                                            )
                                    except (
                                        json.JSONDecodeError,
                                        TypeError,
                                    ) as parse_error:
                                        logger.warning(
                                            f"RAG tool output not valid JSON: {parse_error}"
                                        )
                    except Exception as e:
                        logger.warning(
                            f"Error processing RAG tool end event: {e} | {traceback.format_exc()}"
                        )

                # Track tool calls and stream content chunks in real-time
                try:
                    if event_type == "on_chat_model_stream":
                        chunk = event_data.get("chunk", {})

                        # Try multiple ways to extract content
                        content_chunk = ""
                        if hasattr(chunk, "content"):
                            content_chunk = (
                                chunk.content if isinstance(chunk.content, str) else ""
                            )

                        elif isinstance(chunk, dict) and "content" in chunk:
                            content_chunk = chunk.get("content", "")

                        # Stream content chunks to frontend in real-time (WHILE generating)
                        if (
                            content_chunk
                            and isinstance(content_chunk, str)
                            and content_chunk.strip()
                        ):
                            # Emit response_generation START event on first chunk (once only)
                            if (
                                "response_generation_started"
                                not in rag_execution_state.get("stages_emitted", set())
                            ):
                                logger.info("Response streaming started")
                                rag_execution_state.setdefault(
                                    "stages_emitted", set()
                                ).add("response_generation_started")
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "response_generation",
                                    "message": "Generating final response",
                                    "data": {
                                        "tools_used": tools_used,
                                    },
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }
                                # Also emit streaming started
                                yield {
                                    "type": "workflow_progress",
                                    "stage": "response_streaming_started",
                                    "message": "Streaming response to client",
                                    "execution_time_ms": (time.time() - start_time)
                                    * 1000,
                                }

                            # Stream this chunk immediately to the frontend
                            yield {
                                "type": "streaming_response",
                                "chunk": content_chunk,
                                "metadata": {
                                    "tools_used": tools_used,
                                    "orchestrator_type": "tool_calling_pattern",
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                        # Track tool calls
                        if "tool_calls" in chunk:
                            for tool_call in chunk.get("tool_calls", []):
                                tool_name = tool_call.get("name", "")

                                if tool_name and tool_name not in tools_used:
                                    tools_used.append(tool_name)
                                    # Also track in agent state using LangGraph method
                                    agent_state.add_tool_used(tool_name)
                                    logger.info(f"Tool call detected: {tool_name}")

                                    # Emit RAG agent execution START event
                                    if tool_name == rag_agent_name:
                                        rag_tool_called = True
                                        yield {
                                            "type": "workflow_progress",
                                            "stage": "rag_agent_executing",
                                            "message": f"{rag_agent_name.replace('_', ' ').title()}: Retrieving and ranking documents",
                                            "execution_time_ms": (
                                                time.time() - start_time
                                            )
                                            * 1000,
                                        }

                                    # Track task tool execution (no event emission to avoid duplicate START event)
                                    elif tool_name in [t.name for t in task_tools]:
                                        # Track task tool execution in agent state using LangGraph method
                                        agent_state.add_task_tool_executed(tool_name)
                                        logger.debug(f"Task tool called: {tool_name}")

                                        # RAG context already in agent_state, no need to set again
                                        # Task tools will read from agent_state["rag_context"]

                                        # NOTE: We do NOT emit another task_agent_executing event here
                                        # The START event was already emitted after RAG completion
                                        # Emitting again would cause the stage to flicker/restart in the UI
                except Exception as e:
                    # Tool call tracking error - log but continue
                    error_msg = f"Error streaming/tracking: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Traceback: {traceback.format_exc()}")

                # Capture final output
                if event_type == "on_chain_end" and event_name == "LangGraph":
                    try:
                        if hasattr(event_data, "output"):
                            final_output = event_data.output
                        elif isinstance(event_data, dict) and "output" in event_data:
                            final_output = event_data["output"]
                        else:
                            final_output = event_data

                        if (
                            isinstance(final_output, dict)
                            and "messages" in final_output
                        ):
                            final_messages = final_output["messages"]
                            logger.info(
                                f"Main agent completed with {len(final_messages)} messages"
                            )

                            # Extract RAG documents from message history for task tools
                            try:
                                for msg in final_messages:
                                    if isinstance(msg, dict):
                                        # Handle dict messages
                                        if msg.get("role") == "tool":
                                            tool_name = msg.get("name", "")
                                            if tool_name == rag_agent_name:
                                                # Parse RAG response as JSON
                                                content = msg.get("content", "")
                                                if content:
                                                    try:
                                                        rag_response = json.loads(
                                                            content
                                                        )
                                                        if (
                                                            isinstance(
                                                                rag_response, dict
                                                            )
                                                            and "documents"
                                                            in rag_response
                                                        ):
                                                            retrieved_rag_documents = (
                                                                rag_response.get(
                                                                    "documents", []
                                                                )
                                                            )
                                                            logger.info(
                                                                f"Extracted {len(retrieved_rag_documents)} documents from RAG response"
                                                            )
                                                    except json.JSONDecodeError:
                                                        logger.warning(
                                                            "Could not parse RAG response as JSON"
                                                        )
                                    elif isinstance(msg, ToolMessage):
                                        # Handle langchain ToolMessage objects
                                        if msg.name == rag_agent_name:
                                            try:
                                                content = msg.content
                                                # ToolMessage.content can be str or list, we need str for JSON parsing
                                                if isinstance(content, str) and content:
                                                    rag_response = json.loads(content)
                                                    if (
                                                        isinstance(rag_response, dict)
                                                        and "documents" in rag_response
                                                    ):
                                                        retrieved_rag_documents = (
                                                            rag_response.get(
                                                                "documents", []
                                                            )
                                                        )
                                            except (
                                                json.JSONDecodeError,
                                                AttributeError,
                                            ):
                                                pass
                            except Exception as e:
                                logger.warning(f"Error extracting RAG documents: {e}")
                    except Exception as e:
                        error_msg = f"Error capturing final output: {str(e)}"
                        logger.error(error_msg)
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        # Do not set error_occurred - final output is secondary

        except Exception as e:
            # Agent execution error - this is a critical failure
            error_msg = f"Error during main agent execution: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Extract final response with error handling
        # Note: response_generation and response_streaming_started events
        # are emitted when first chunk arrives (in on_chat_model_stream handler)
        execution_time_ms = (time.time() - start_time) * 1000

        final_response = ""
        try:
            if final_messages:
                logger.debug(
                    f"Extracting final response from {len(final_messages)} messages"
                )

                # CRITICAL: Extract from ToolMessage (task tool output), NOT AIMessage (agent thinking)
                # The agent's AIMessage contains reasoning/analysis, the ToolMessage contains the actual generated content
                task_tool_output_found = False
                for msg in reversed(final_messages):
                    # Check for ToolMessage from task tools (mulesoft_flow_generator, etc.)
                    if isinstance(msg, ToolMessage):
                        # Check if it's from a task tool (not RAG)
                        if msg.name != rag_agent_name and msg.name in [
                            t.name for t in task_tools
                        ]:
                            final_response = str(msg.content)
                            task_tool_output_found = True
                            logger.info(
                                f"✅ Final response extracted from task tool: '{msg.name}' ({len(final_response)} chars)"
                            )
                            break
                    elif isinstance(msg, dict) and msg.get("role") == "tool":
                        # Dict-based tool message
                        tool_name = msg.get("name", "")
                        if tool_name != rag_agent_name and tool_name in [
                            t.name for t in task_tools
                        ]:
                            final_response = str(msg.get("content", ""))
                            task_tool_output_found = True
                            logger.info(
                                f"✅ Final response extracted from task tool: '{tool_name}' ({len(final_response)} chars)"
                            )
                            break

                # Fallback to AIMessage if no task tool output found (for pure Q&A without generation)
                if not task_tool_output_found:
                    logger.debug(
                        "No task tool output found, checking for AIMessage (Q&A mode)"
                    )
                    for msg in reversed(final_messages):
                        if isinstance(msg, AIMessage):
                            final_response = msg.content
                            logger.info(
                                f"✅ Final response extracted from AIMessage (Q&A mode, {len(final_response)} chars)"
                            )
                            break
                        elif isinstance(msg, dict) and msg.get("role") == "assistant":
                            final_response = msg.get("content", "")
                            logger.info(
                                f"✅ Final response extracted from assistant message (Q&A mode, {len(final_response)} chars)"
                            )
                            break

            response_state["final_response"] = final_response
        except Exception as e:
            error_msg = f"Error extracting final response: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Emit response generation COMPLETE event
        yield {
            "type": "workflow_progress",
            "stage": "response_generation_complete",
            "message": "Final response generated",
            "data": {
                "response_length": len(final_response),
                "tools_used": tools_used,
                "rag_tool_called": rag_tool_called,
            },
            "execution_time_ms": execution_time_ms,
        }

        # Emit response streaming COMPLETE event
        # Note: response_streaming_started was emitted when first chunk arrived
        # Streaming happened in real-time via on_chat_model_stream events
        if final_response:
            response_state["has_yielded_response"] = True
            yield {
                "type": "workflow_progress",
                "stage": "response_streaming_started_complete",
                "message": "Response streaming completed",
                "data": {
                    "total_chunks": len(final_response)
                    // 10,  # Approximate, actual chunks from LLM
                    "response_length": len(final_response),
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Extract metadata from RAG execution state BEFORE saving to database
        has_rag_documents = (
            rag_execution_state.get("documents")
            and len(rag_execution_state.get("documents", [])) > 0
        )

        logger.info(
            f"Final result preparation: rag_tool_called={rag_tool_called}, has_rag_documents={has_rag_documents}, document_count={len(rag_execution_state.get('documents', []))}"
        )

        # Initialize metadata variables
        source_urls = []
        chunk_ids = []
        enhanced_queries = []
        enhancement_strategy = rag_execution_state.get(
            "enhancement_strategy", "unknown"
        )
        document_count = 0

        if has_rag_documents:
            document_count = len(rag_execution_state["documents"])
            enhanced_queries = rag_execution_state.get("enhanced_queries", [])

            # Extract source URLs and chunk IDs from documents
            for doc in rag_execution_state["documents"]:
                # Try multiple paths for source_url (top-level, nested in metadata, or 'source' field)
                source_url = doc.get("source_url") or doc.get("source")
                if not source_url and doc.get("metadata", {}).get("metadata"):
                    source_url = doc["metadata"]["metadata"].get("source_url")

                if source_url and source_url not in source_urls:
                    source_urls.append(source_url)

                # Try multiple paths for chunk_id (top-level or nested in metadata)
                chunk_id = doc.get("chunk_id")
                if not chunk_id and doc.get("metadata", {}).get("metadata"):
                    chunk_id = doc["metadata"]["metadata"].get("chunk_id")

                if chunk_id and chunk_id not in chunk_ids:
                    chunk_ids.append(chunk_id)

            logger.info(
                f"📦 Extracted {len(source_urls)} source URLs and {len(chunk_ids)} chunk IDs from {document_count} documents"
            )

        # Save to conversation history with metadata (non-fatal failure)
        try:
            user_message = ConversationMessage(
                role="user",
                content=query,
                timestamp=datetime.now(timezone.utc),
                search_query=query,
            )
            conversation_history_service.add_message(conversation_id, user_message)

            # Save assistant message WITH metadata (matching RAG mode behavior)
            assistant_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
                source_urls=source_urls,
                chunk_ids=chunk_ids,
                enhancement_strategy_used=enhancement_strategy,
                enhanced_queries=enhanced_queries,
                document_count=document_count,
                processing_time_ms=int(execution_time_ms),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(
                f"✅ [CONVERSATION] Saved assistant response with metadata to conversation {conversation_id} "
                f"(sources={len(source_urls)}, chunks={len(chunk_ids)}, queries={len(enhanced_queries)}, docs={document_count})"
            )
        except Exception as e:
            # Conversation save failure is logged but NOT fatal
            error_msg = f"Failed to save conversation (continuing): {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Do NOT set error_occurred or raise - response has already been streamed

        # Final result with RAG documents if available
        final_result = {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "metadata": {
                "orchestrator_type": "tool_calling_pattern",
                "tools_used": tools_used,
                "enhancement_strategy": enhancement_strategy,
            },
        }

        if has_rag_documents:
            final_result["documents"] = rag_execution_state["documents"]
            final_result["metadata"]["document_count"] = rag_execution_state[
                "total_docs"
            ]
            final_result["metadata"]["relevant_document_count"] = rag_execution_state[
                "relevant_docs"
            ]
            final_result["metadata"]["enhanced_queries"] = enhanced_queries
            final_result["metadata"]["source_urls"] = source_urls
            final_result["metadata"]["chunk_ids"] = chunk_ids

            # Add source details for each document
            final_result["metadata"]["document_sources"] = [
                {
                    "title": doc.get("title", "Unknown"),
                    "source": doc.get("source", doc.get("source_url", "Unknown")),
                    "distance": doc.get("distance", None),
                }
                for doc in rag_execution_state["documents"]
            ]

            # Add search variants for transparency
            final_result["metadata"]["search_variants"] = rag_execution_state.get(
                "enhanced_queries", []
            )
            final_result["metadata"]["rag_strategy"] = rag_execution_state.get(
                "enhancement_strategy", "unknown"
            )
        else:
            final_result["documents"] = []

        yield final_result

        logger.info(f"Tool Calling Pattern completed in {execution_time_ms:.2f}ms")

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000

        # CRITICAL: Comprehensive error handling with resource cleanup
        # Ensure all errors are surfaced, even if we've already started streaming

        error_msg = f"Tool Calling Pattern failed: {str(e)}"
        response_state["error_occurred"] = True
        response_state["error_details"] = error_msg

        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Resource Cleanup: Close LLM client if it was created
        try:
            if response_state["llm_client"] is not None:
                logger.debug("Cleaning up LLM client resources")
                if hasattr(response_state["llm_client"], "close"):
                    response_state["llm_client"].close()
        except Exception as cleanup_error:
            logger.warning(f"Error during LLM client cleanup: {cleanup_error}")

        # Determine if response was partially streamed
        has_partial_response = response_state["has_yielded_response"]
        initialization_failed = not response_state["initialization_complete"]

        # Categorize error for client
        if initialization_failed:
            # Initialization error - client should not have received any response
            error_category = "initialization_error"
            user_message = (
                f"Failed to initialize the AI system. Please try again. "
                f"Error: {str(e)[:100]}"
            )
        elif has_partial_response:
            # Partial response already sent - mark as incomplete
            error_category = "partial_response_error"
            user_message = (
                f"Response was incomplete due to an error. "
                f"Please refresh and try again."
            )
        else:
            # Error after initialization but before streaming
            error_category = "execution_error"
            user_message = (
                f"An error occurred while processing your query. " f"Please try again."
            )

        # Yield error event ONLY if we haven't started streaming response
        # If we did start streaming, the client is already receiving a response
        if not has_partial_response:
            yield {
                "type": "supervisor_error",
                "error": str(e),
                "error_category": error_category,
                "execution_time_ms": execution_time_ms,
                "workflow_completed": False,
                "query": query,
                "response": user_message,
                "initialization_complete": response_state["initialization_complete"],
                "partial_response_sent": False,
            }
        else:
            # Partial response was sent - send error marker event
            yield {
                "type": "supervisor_error",
                "error": str(e),
                "error_category": error_category,
                "execution_time_ms": execution_time_ms,
                "workflow_completed": False,
                "response": "[ERROR] Response was interrupted. The above message may be incomplete.",
                "initialization_complete": response_state["initialization_complete"],
                "partial_response_sent": True,
            }
