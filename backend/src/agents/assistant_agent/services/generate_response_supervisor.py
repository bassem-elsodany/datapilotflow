"""
Generate Response Service using Tool Calling Pattern (LangChain Recommended)

This module implements the OFFICIAL LangChain multi-agent pattern:
https://docs.langchain.com/oss/python/langchain/multi-agent

The RAG agent is wrapped as a tool that the main ReAct agent can invoke.
"""

import asyncio
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional

import litellm
from langchain.agents import create_agent
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import AIMessage, ToolMessage
from loguru import logger
from opik.integrations.langchain import OpikTracer
from opik.integrations.litellm import opik_tracker

# Import compatibility shim for opik with LangChain 1.0+ (MUST be first)
import src.compat_langchain_load  # noqa: F401
from src.agents.assistant_agent.tools.rag_knowledge_tool import (
    create_rag_knowledge_tool,
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
                timeout=provider.timeout if provider.timeout else 60,
                temperature=temperature,
                max_tokens=max_tokens,
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
        selected_system_prompt = None
        if selected_system_prompt_id:
            try:
                selected_system_prompt = conversation_history_service.get_system_prompt(
                    conversation_id=conversation_id,
                    prompt_id=selected_system_prompt_id,
                    user_id=user_id,
                )
                if selected_system_prompt:
                    logger.info(f"Using system prompt: '{selected_system_prompt.name}'")
                else:
                    # System prompt not found - log and continue (fallback to default)
                    logger.warning(
                        f"System prompt not found: {selected_system_prompt_id} - will use default prompt"
                    )
                    # Do NOT raise error here - fallback to default is acceptable
            except Exception as e:
                # System prompt retrieval failed - log and continue
                error_msg = f"Error retrieving system prompt (will use default): {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Do NOT set error_occurred here - this is not fatal

        # Track RAG execution state (shared across tool invocations)
        rag_execution_state = {
            "stages_emitted": set(),
            "total_docs": 0,
            "relevant_docs": 0,
            "documents": [],
            "enhanced_queries": [],
            "enhancement_strategy": selected_strategy or "native",
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

        # Combine RAG tool + task tools
        all_tools = [retrieve_knowledge_tool] + task_tools

        logger.info(
            f"Created {len(all_tools)} tools total: 1 RAG tool + {len(task_tools)} task tools"
        )

        # Build system prompt for main agent
        system_prompt_parts = []

        # Base prompt: Use custom prompt if provided, otherwise use our standard main agent prompt
        if selected_system_prompt and selected_system_prompt.prompt_template:
            system_prompt_parts.append(selected_system_prompt.prompt_template)
        else:
            # Use the properly structured prompt from our prompts package
            system_prompt_parts.append(MAIN_AGENT_SYSTEM_PROMPT.prompt)

        # Add knowledge base context if available
        if conversation_description:
            system_prompt_parts.append(
                f"\n\n**Knowledge Base Context:**\n{conversation_description}"
            )

        system_prompt = "\n".join(system_prompt_parts)

        # Create main ReAct agent with all tools
        logger.info("Creating main ReAct agent with Tool Calling pattern")

        main_agent = create_agent(
            model=llm_client,
            tools=all_tools,
            system_prompt=system_prompt,
        )

        logger.info("Main ReAct agent created successfully")

        # Configure Opik tracing (if enabled)
        config_for_stream = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 50,
        }

        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Supervisor config: strategy={selected_strategy}, "
                f"collection={collection_name}, provider={llm_provider_id}, model={llm_model_name}"
            )

            # Enable LiteLLM tracking for cost and token usage
            opik_tracker.track_litellm()
            logger.debug("LiteLLM tracking enabled for cost and token usage")

            # Build tags for Opik trace
            trace_tags = [
                "supervisor_agent",
                "tool_calling_pattern",
                f"strategy:{selected_strategy or 'native'}",
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

        # Yield initialization complete event
        yield {
            "type": "supervisor_progress",
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
        logger.info("Starting main agent execution")

        # Track state
        final_messages = []
        tools_used = []
        rag_tool_called = False

        # Stream events from main agent with explicit error tracking
        try:
            async for event in main_agent.astream_events(
                {"messages": [{"role": "user", "content": query}]},
                config=config_for_stream,
                version="v2",
            ):
                event_type = event.get("event", "")
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Track tool calls with error detection
                try:
                    if event_type == "on_chat_model_stream":
                        chunk = event_data.get("chunk", {})
                        if "tool_calls" in chunk:
                            for tool_call in chunk.get("tool_calls", []):
                                tool_name = tool_call.get("name", "")

                                if tool_name and tool_name not in tools_used:
                                    tools_used.append(tool_name)
                                    logger.info(f"Tool call detected: {tool_name}")

                                    # Emit RAG agent execution event
                                    if tool_name == rag_agent_name:
                                        rag_tool_called = True
                                        yield {
                                            "type": "supervisor_progress",
                                            "stage": "rag_agent_executing",
                                            "message": f"{rag_agent_name.replace('_', ' ').title()}: Retrieving and ranking documents",
                                            "execution_time_ms": (time.time() - start_time)
                                            * 1000,
                                        }

                                    # Emit task tool execution event
                                    elif tool_name in [t.name for t in task_tools]:
                                        yield {
                                            "type": "supervisor_progress",
                                            "stage": "task_agent_executing",
                                            "message": f"Task Tool: Executing {tool_name}",
                                            "execution_time_ms": (time.time() - start_time)
                                            * 1000,
                                        }
                except Exception as e:
                    # Tool call tracking error - log but continue
                    error_msg = f"Error tracking tool call: {str(e)}"
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

                        if isinstance(final_output, dict) and "messages" in final_output:
                            final_messages = final_output["messages"]
                            logger.info(
                                f"Main agent completed with {len(final_messages)} messages"
                            )
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
        execution_time_ms = (time.time() - start_time) * 1000

        final_response = ""
        try:
            if final_messages:
                # Get last AI message content
                for msg in reversed(final_messages):
                    if isinstance(msg, AIMessage) or (
                        isinstance(msg, dict) and msg.get("role") == "assistant"
                    ):
                        final_response = (
                            msg.content
                            if hasattr(msg, "content")
                            else msg.get("content", "")
                        )
                        break

            logger.info(f"Final response length: {len(final_response)}")
            response_state["final_response"] = final_response
        except Exception as e:
            error_msg = f"Error extracting final response: {str(e)}"
            response_state["error_occurred"] = True
            response_state["error_details"] = error_msg
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # Emit completion events
        yield {
            "type": "supervisor_progress",
            "stage": "response_generation_complete",
            "message": "Final response generated",
            "data": {
                "response_length": len(final_response),
                "tools_used": tools_used,
                "rag_tool_called": rag_tool_called,
            },
            "execution_time_ms": execution_time_ms,
        }

        # Stream response in chunks - ONLY if we have a valid response
        if final_response:
            try:
                chunk_size = 500
                for i in range(0, len(final_response), chunk_size):
                    chunk = final_response[i : i + chunk_size]
                    response_state["has_yielded_response"] = True

                    if i == 0:
                        # First chunk with metadata
                        metadata = {
                            "tools_used": tools_used,
                            "orchestrator_type": "tool_calling_pattern",
                            "enhancement_strategy": rag_execution_state[
                                "enhancement_strategy"
                            ],
                        }

                        # Add RAG-specific metadata if RAG tool was called
                        if rag_tool_called:
                            source_urls = []
                            chunk_ids = []

                            # Extract source URLs and chunk IDs from documents
                            for doc in rag_execution_state["documents"]:
                                if (
                                    doc.get("source_url")
                                    and doc["source_url"] not in source_urls
                                ):
                                    source_urls.append(doc["source_url"])
                                if doc.get("chunk_id") and doc["chunk_id"] not in chunk_ids:
                                    chunk_ids.append(doc["chunk_id"])

                            metadata.update(
                                {
                                    "source_urls": source_urls,
                                    "chunk_ids": chunk_ids,
                                    "document_count": rag_execution_state["total_docs"],
                                    "relevant_document_count": rag_execution_state[
                                        "relevant_docs"
                                    ],
                                    "enhanced_queries": rag_execution_state[
                                        "enhanced_queries"
                                    ],
                                }
                            )

                        yield {
                            "type": "streaming_response",
                            "chunk": chunk,
                            "metadata": metadata,
                            "execution_time_ms": execution_time_ms,
                        }
                    else:
                        # Subsequent chunks
                        yield {
                            "type": "streaming_response",
                            "chunk": chunk,
                            "execution_time_ms": execution_time_ms,
                        }
            except Exception as e:
                error_msg = f"Error streaming response chunks: {str(e)}"
                response_state["error_occurred"] = True
                response_state["error_details"] = error_msg
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

        # Save to conversation history (non-fatal failure)
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
                processing_time_ms=int(execution_time_ms),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(f"Saved messages to conversation {conversation_id}")
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
                "enhancement_strategy": rag_execution_state["enhancement_strategy"],
            },
        }

        # Add RAG documents if RAG tool was called
        if rag_tool_called:
            final_result["documents"] = rag_execution_state["documents"]
            final_result["metadata"]["document_count"] = rag_execution_state[
                "total_docs"
            ]
            final_result["metadata"]["relevant_document_count"] = rag_execution_state[
                "relevant_docs"
            ]
            final_result["metadata"]["enhanced_queries"] = rag_execution_state[
                "enhanced_queries"
            ]
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
                f"An error occurred while processing your query. "
                f"Please try again."
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
