"""
Generate Response Service using Custom ReAct Graph Pattern

This module implements the supervisor agent's response generation using a custom
LangGraph ReAct pattern with tool calling capabilities.

Key Features:
- Custom create_graph() implementation for the ReAct agent pattern
- RAG-first knowledge retrieval with knowledge_expert tool
- Dynamic tool binding from conversation configuration
- Streaming response events for real-time UI updates
- Provider setup, LLM client management, and error handling
"""

import asyncio
import json
import time
import traceback
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import litellm
from langchain_community.chat_models import ChatLiteLLM
from loguru import logger

# Import supervisor agent components
from src.agents.supervisor_agent.graph import create_graph
from src.agents.supervisor_agent.tools import ToolRegistry

# Import shared services and utilities
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


def _format_rag_documents_as_context(documents: List[Dict[str, Any]]) -> str:
    """Format RAG documents into a context string for task tools."""
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
    Generate AI response using Custom ReAct Graph Pattern.

    Uses our custom ReAct graph with RAG-first tool calling pattern.
    Handles provider setup, dynamic tool loading, streaming, and error handling.

    Args:
        query: User's question/request
        user_id: User ID for conversation
        llm_provider_id: LLM provider ID (e.g., "anthropic")
        llm_model_name: Model name (e.g., "claude-sonnet-4-5-20250929")
        conversation_id: Conversation session ID
        collection_name: RAG collection name
        enable_reranking: Whether to enable reranking
        relevance_threshold: Reranking relevance threshold
        enable_llm_generation: Whether to enable LLM-based tool generation
        top_k: Max documents to retrieve
        conversation_description: Optional description of conversation domain
        selected_system_prompt_id: Optional custom system prompt ID
        rag_agent_name: Name of RAG tool (default: "knowledge_expert")
        rag_agent_description: Description of RAG tool

    Yields:
        Event dictionaries with progress updates and final response
    """
    start_time = time.time()

    # Central response state tracking
    response_state = {
        "has_yielded_response": False,
        "error_occurred": False,
        "error_details": None,
        "initialization_complete": False,
        "llm_client": None,
        "final_response": "",
        "execution_messages": [],
    }

    try:
        selected_strategy = "custom_variants"

        logger.info(
            f"Supervisor Agent (Custom ReAct) Mode: Using strategy='custom_variants'"
        )

        # Yield initialization START event
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing Supervisor Agent (Custom ReAct Pattern)",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        supervisor_init_start = time.time()

        # ========================================================================
        # PHASE 1: INITIALIZATION
        # ========================================================================

        # Get provider configuration
        try:
            provider_service = get_model_provider_service()
            provider = provider_service.get_model_provider(llm_provider_id, user_id)

            if not provider:
                raise ValueError(f"Provider not found: {llm_provider_id}")
            if not provider.is_active:
                raise ValueError(f"Provider is not active: {provider.name}")
            if not provider.api_key or provider.api_key.strip() == "":
                raise ValueError(
                    f"API key not configured for provider '{provider.name}'"
                )

        except ValueError as e:
            response_state["error_occurred"] = True
            response_state["error_details"] = str(e)
            logger.error(f"Provider configuration error: {e}")
            raise

        # Create LLM client
        try:
            model_string = f"{provider.provider_type}/{llm_model_name}"

            generative_config = (
                provider.generative.config if provider.generative else {}
            )
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
            response_state["error_occurred"] = True
            response_state["error_details"] = f"Failed to create LLM client: {str(e)}"
            logger.error(f"LLM client creation failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Load conversation
        try:
            conversation = conversation_history_service.get_conversation(
                conversation_id
            )
            if not conversation:
                raise ValueError(f"Conversation not found: {conversation_id}")
        except Exception as e:
            response_state["error_occurred"] = True
            response_state["error_details"] = f"Failed to load conversation: {str(e)}"
            logger.error(f"Conversation loading failed: {e}")
            raise

        logger.info(f"Supervisor initialized with model: {model_string}")

        # ========================================================================
        # TOOL INITIALIZATION - Use assistant agent pattern
        # ========================================================================

        # Initialize workflow config for RAG (matching assistant agent)
        top_k_per_query = max(5, int(top_k * 1.5))

        workflow_config = {
            "collection_name": collection_name,
            "user_id": user_id,
            "llm_provider_id": llm_provider_id,
            "llm_model_name": llm_model_name,
            "llm_client": llm_client,
            "enhancement_config": {},
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

        # Track RAG execution state (shared across tool invocations)
        rag_execution_state = {
            "stages_emitted": set(),
            "total_docs": 0,
            "relevant_docs": 0,
            "documents": [],
            "enhanced_queries": [],
            "enhancement_strategy": "custom_variants",
            "final_answer": "",
        }

        # Build RAG tool description
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

        # Create RAG tool using factory
        from src.agents.supervisor_agent.tools.rag_knowledge_tool import (
            create_rag_knowledge_tool,
        )

        retrieve_knowledge_tool = create_rag_knowledge_tool(
            rag_agent_name=rag_agent_name,
            rag_agent_description=final_rag_description,
            workflow_config=workflow_config,
            rag_execution_state=rag_execution_state,
        )

        # Get task tools (matching assistant agent)
        task_tools = []

        if conversation.assistant_config and conversation.assistant_config.tools:
            # Use dynamic tools from conversation configuration
            from src.agents.supervisor_agent.tools import get_dynamic_task_tools

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
                from src.agents.task_agent.tools import get_task_agent_tools

                task_tools = get_task_agent_tools()
        else:
            # Fallback to hardcoded default tools
            from src.agents.task_agent.tools import get_task_agent_tools

            task_tools = get_task_agent_tools()
            logger.info(
                f"No dynamic tools configured, using {len(task_tools)} default tools"
            )

        # Create tool registry and register all tools
        logger.info("Creating tool registry with RAG + task tools")
        tool_registry = ToolRegistry()

        # Register RAG tool
        tool_registry.register(rag_agent_name, retrieve_knowledge_tool)
        logger.info(f"Registered RAG tool: {rag_agent_name}")

        # Register task tools
        for task_tool in task_tools:
            tool_registry.register(task_tool.name, task_tool)
            logger.info(f"Registered task tool: {task_tool.name}")

        logger.info(
            f"Tool registry created with {len(tool_registry)} tools: {tool_registry.list_ids()}"
        )

        # Build system prompt with user-defined instructions
        from src.agents.supervisor_agent.base_system_prompt import (
            BASE_SYSTEM_PROMPT,
            DEFAULT_INSTRUCTIONS,
        )
        from datetime import datetime, UTC

        # Get user's custom instructions or use defaults
        user_instructions = ""
        if (
            conversation.assistant_config
            and conversation.assistant_config.instructions
            and conversation.assistant_config.instructions.strip()
        ):
            user_instructions = conversation.assistant_config.instructions
            logger.info(
                f"✅ Using user-defined instructions ({len(user_instructions)} chars)"
            )
        else:
            user_instructions = DEFAULT_INSTRUCTIONS
            logger.info("✅ Using default instructions (no user customization)")

        # Add knowledge base context to user instructions if available
        if conversation_description:
            user_instructions += f"\n\n**Knowledge Base Context:**\n{conversation_description}"

        # Build final prompt: BASE (RAG protocol) + USER (personality/domain)
        system_prompt = BASE_SYSTEM_PROMPT.prompt.format(
            user_instructions=user_instructions,
            system_time=datetime.now(UTC).isoformat(),
        )

        logger.info(
            f"System prompt built: {len(system_prompt)} chars (base + user instructions)"
        )

        # Initialize supervisor service and create custom ReAct graph
        logger.info("Creating custom ReAct graph with ToolRegistry")

        try:
            # *** KEY DIFFERENCE: Create our custom ReAct graph instead of create_agent() ***
            # Pass llm_client and system_prompt to the graph
            main_agent = create_graph(
                tool_registry=tool_registry,
                llm_client=llm_client,
                system_prompt=system_prompt,
            )

            logger.info(
                f"✅ Custom ReAct graph created with {len(tool_registry)} tools"
            )

        except Exception as e:
            error_msg = f"Failed to create custom ReAct graph: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Mark initialization as complete
        response_state["initialization_complete"] = True
        logger.info("Supervisor initialization completed successfully")

        # Yield initialization COMPLETE event
        yield {
            "type": "workflow_progress",
            "stage": "supervisor_init_complete",
            "message": "Supervisor Agent initialized (Custom ReAct Pattern)",
            "data": {
                "orchestrator_type": "custom_react_pattern",
                "tools_available": tool_registry.list_ids(),
                "model": model_string,
                "initialization_time_ms": (time.time() - supervisor_init_start) * 1000,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # ========================================================================
        # PHASE 2: AGENT EXECUTION
        # ========================================================================

        logger.info("Starting custom ReAct agent execution")

        yield {
            "type": "workflow_progress",
            "stage": "agent_execution_starting",
            "message": "Agent analyzing query and executing ReAct loop",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Prepare conversation messages - history FIRST, then new query
        messages = []
        if conversation.messages:
            for msg in conversation.messages[-10:]:  # Last 10 messages
                messages.append({"role": msg.role, "content": msg.content})
        # Add new user query at the END
        messages.append({"role": "user", "content": query})

        # Configure graph execution
        config_for_stream = {
            "recursion_limit": 10,
        }

        final_response = ""
        tools_used = []
        rag_tool_called = False
        agent_execution_complete_emitted = False
        retrieved_rag_documents = None
        final_messages = []  # Capture all messages for final response extraction

        try:
            # CRITICAL FIX: Use astream_events() for proper event tracking
            # astream() only returns state updates, not detailed events
            from langchain_core.messages import AIMessage, ToolMessage
            from langchain_core.runnables import RunnableConfig

            # Track content for streaming (for real-time display only)
            content_buffer = ""
            has_started_streaming = False

            async for event in main_agent.astream_events(
                {
                    "messages": messages,
                },
                config=config_for_stream,
                version="v2",  # Use v2 for better event structure
            ):
                event_type = event.get("event", "")
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # EARLY: Extract RAG documents from on_tool_end (before processing streaming)
                if event_type == "on_tool_end":
                    tool_name = event.get("name", "")
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)

                    logger.info(f"Tool execution completed: {tool_name}")

                    # Handle RAG tool completion - extract documents
                    if tool_name == rag_agent_name:
                        try:
                            tool_output = event_data.get("output", "")
                            logger.debug(
                                f"Processing RAG tool output: {type(tool_output).__name__}"
                            )

                            if tool_output:
                                # Handle ToolMessage objects from LangChain
                                if hasattr(tool_output, "content"):
                                    tool_output_content = tool_output.content
                                else:
                                    tool_output_content = tool_output

                                if tool_output_content:
                                    try:
                                        # Parse RAG response as JSON
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

                                            # CRITICAL: Store documents in rag_execution_state
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
                                                    "tools_used": tools_used,
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
                                                        "tools_used": tools_used,
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
                                                    "tools_used": tools_used,
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
                                    except (
                                        json.JSONDecodeError,
                                        TypeError,
                                    ) as parse_error:
                                        logger.warning(
                                            f"RAG tool output not valid JSON: {parse_error}"
                                        )
                        except Exception as e:
                            logger.warning(f"Error processing RAG tool end event: {e}")

                    # Emit standard tool completion event for all tools
                    yield {
                        "type": "workflow_progress",
                        "stage": f"{tool_name}_complete",
                        "message": f"Tool execution completed: {tool_name}",
                        "execution_time_ms": (time.time() - start_time) * 1000,
                    }

                # Track tool calls from chat model
                if event_type == "on_chat_model_stream":
                    chunk = event_data.get("chunk", {})

                    # Extract content for streaming
                    content_chunk = ""
                    if hasattr(chunk, "content"):
                        content_chunk = (
                            chunk.content if isinstance(chunk.content, str) else ""
                        )
                    elif isinstance(chunk, dict) and "content" in chunk:
                        content_chunk = chunk.get("content", "")

                    # Stream content chunks in real-time
                    if (
                        content_chunk
                        and isinstance(content_chunk, str)
                        and content_chunk.strip()
                    ):
                        if not has_started_streaming:
                            has_started_streaming = True

                            # Emit response generation START event (before streaming)
                            yield {
                                "type": "workflow_progress",
                                "stage": "response_generation",
                                "message": "Generating final response",
                                "data": {
                                    "tools_used": tools_used,
                                },
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                            # Also emit streaming started
                            yield {
                                "type": "workflow_progress",
                                "stage": "response_streaming_started",
                                "message": "Streaming response to client",
                                "execution_time_ms": (time.time() - start_time) * 1000,
                            }

                        content_buffer += content_chunk
                        yield {
                            "type": "streaming_response",
                            "chunk": content_chunk,
                            "metadata": {
                                "tools_used": tools_used,
                                "orchestrator_type": "custom_react_pattern",
                            },
                            "execution_time_ms": (time.time() - start_time) * 1000,
                        }

                    # Track tool calls
                    if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        for tool_call in chunk.tool_calls:
                            tool_name = tool_call.get("name", "")
                            if tool_name and tool_name not in tools_used:
                                tools_used.append(tool_name)
                                logger.info(f"Tool call detected: {tool_name}")

                                # Emit RAG agent execution START event
                                if tool_name == rag_agent_name:
                                    rag_tool_called = True
                                    yield {
                                        "type": "workflow_progress",
                                        "stage": "rag_agent_executing",
                                        "message": f"{rag_agent_name.replace('_', ' ').title()}: Retrieving and ranking documents",
                                        "execution_time_ms": (time.time() - start_time)
                                        * 1000,
                                    }

                                # For task tools, just track (no duplicate START event)
                                # task_agent_executing was already emitted after RAG completion

                # Capture final output (messages from the graph)
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
                                f"Captured {len(final_messages)} messages from graph completion"
                            )
                    except Exception as e:
                        logger.warning(f"Error capturing final output: {e}")

            # CRITICAL: Extract final response from ToolMessage (task tool output), NOT from streaming buffer
            # The streaming buffer contains agent's thoughts, ToolMessage contains the actual generated content
            logger.info("Extracting final response from messages...")

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
            else:
                # Fallback to content_buffer only if no messages captured
                logger.warning(
                    "No final messages captured, falling back to content_buffer (may contain agent thoughts!)"
                )
                final_response = content_buffer

            logger.info(
                f"Custom ReAct agent execution completed: {len(final_response)} chars response"
            )

        except Exception as e:
            error_msg = f"Error during custom ReAct execution: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # ========================================================================
        # PHASE 3: COMPLETION
        # ========================================================================

        execution_time_ms = (time.time() - start_time) * 1000

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

        # Emit response streaming COMPLETE event (matching assistant agent)
        if final_response:
            yield {
                "type": "workflow_progress",
                "stage": "response_streaming_started_complete",
                "message": "Response streaming completed",
                "data": {
                    "total_chunks": len(final_response) // 10,  # Approximate
                    "response_length": len(final_response),
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Extract RAG metadata if available
        has_rag_documents = (
            rag_execution_state.get("documents")
            and len(rag_execution_state.get("documents", [])) > 0
        )

        source_links = []  # Structured list with URL, title, and chunk_id
        enhanced_queries = []
        enhancement_strategy = rag_execution_state.get(
            "enhancement_strategy", "unknown"
        )
        document_count = 0

        if has_rag_documents:
            document_count = len(rag_execution_state["documents"])
            enhanced_queries = rag_execution_state.get("enhanced_queries", [])

            # Extract source links with URL, title, and chunk_id from each document
            for doc in rag_execution_state["documents"]:
                source_url = doc.get("source_url") or doc.get("source")
                if not source_url and doc.get("metadata", {}).get("metadata"):
                    source_url = doc["metadata"]["metadata"].get("source_url")

                # Extract title from multiple possible locations
                title = doc.get("title")
                if not title and doc.get("metadata", {}).get("metadata"):
                    title = doc["metadata"]["metadata"].get("title")
                if not title and doc.get("metadata"):
                    title = doc["metadata"].get("title")

                # Extract chunk_id
                chunk_id = doc.get("chunk_id")
                if not chunk_id and doc.get("metadata", {}).get("metadata"):
                    chunk_id = doc["metadata"]["metadata"].get("chunk_id")

                # Extract query variant info (which variant retrieved this document)
                query_variant_index = doc.get("query_variant_index")
                query_variant = doc.get("query_variant")

                if source_url:
                    # Add structured link with URL, title, chunk_id, and variant info
                    source_links.append(
                        {
                            "url": source_url,
                            "title": title or "Untitled Document",
                            "chunk_id": chunk_id or "",
                            "query_variant_index": query_variant_index,
                            "query_variant": query_variant,
                        }
                    )

        # Save to conversation history with metadata
        try:
            user_message = ConversationMessage(
                role="user",
                content=query,
                timestamp=datetime.now(timezone.utc),
            )
            conversation_history_service.add_message(conversation_id, user_message)

            assistant_message = ConversationMessage(
                role="assistant",
                content=final_response,
                timestamp=datetime.now(timezone.utc),
                source_links=source_links,  # Structured links with URL, title, and chunk_id
                enhancement_strategy_used=enhancement_strategy,
                enhanced_queries=enhanced_queries,
                document_count=document_count,
                processing_time_ms=int(execution_time_ms),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(
                f"✅ Saved conversation with metadata to {conversation_id} "
                f"(sources={len(source_links)}, docs={document_count})"
            )
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue - don't fail the entire operation

        # Final result with RAG documents if available
        final_result = {
            "type": "workflow_complete",
            "execution_time_ms": execution_time_ms,
            "workflow_completed": True,
            "query": query,
            "response": final_response,
            "metadata": {
                "orchestrator_type": "custom_react_pattern",
                "tools_used": tools_used,
                "model": model_string,
                "enhancement_strategy": enhancement_strategy,
            },
        }

        if has_rag_documents:
            final_result["documents"] = rag_execution_state["documents"]
            final_result["metadata"]["document_count"] = document_count
            final_result["metadata"]["enhanced_queries"] = enhanced_queries
            final_result["metadata"][
                "source_links"
            ] = source_links  # Structured links with URL, title, and chunk_id
        else:
            final_result["documents"] = []

        yield final_result

        logger.info(f"Custom ReAct Pattern completed in {execution_time_ms:.2f}ms")

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Custom ReAct Pattern failed: {str(e)}"
        response_state["error_occurred"] = True
        response_state["error_details"] = error_msg

        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Resource cleanup
        try:
            if response_state["llm_client"] is not None:
                logger.debug("Cleaning up LLM client resources")
                if hasattr(response_state["llm_client"], "close"):
                    response_state["llm_client"].close()
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")

        # Yield error event
        has_partial_response = response_state["has_yielded_response"]
        initialization_failed = not response_state["initialization_complete"]

        if initialization_failed:
            error_category = "initialization_error"
            user_message = (
                f"Failed to initialize supervisor agent. Error: {str(e)[:100]}"
            )
        elif has_partial_response:
            error_category = "partial_response_error"
            user_message = "Response was incomplete due to an error."
        else:
            error_category = "execution_error"
            user_message = "An error occurred while processing your query."

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
