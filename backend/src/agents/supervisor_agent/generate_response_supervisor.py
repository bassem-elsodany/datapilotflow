"""
Generate Response Service using Custom ReAct Graph Pattern

This module is an adaptation of the assistant_agent's generate_response_supervisor.py
with the ONLY difference being:
- Assistant Agent: Uses LangChain's built-in create_agent()
- Supervisor Agent: Uses our custom create_graph() for the ReAct pattern

All other functionality (provider setup, LLM client, tool loading, streaming events,
error handling) remains identical.

Reference: src/agents/assistant_agent/services/generate_response_supervisor.py
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
from src.agents.supervisor_agent.tool_initialization import (
    initialize_tools_from_config_async,
)

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

    Uses our custom ReAct graph instead of LangChain's create_agent().
    All other functionality (provider setup, tools, streaming, error handling)
    is identical to the assistant_agent version.

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
            conversation = conversation_history_service.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation not found: {conversation_id}")
        except Exception as e:
            response_state["error_occurred"] = True
            response_state["error_details"] = f"Failed to load conversation: {str(e)}"
            logger.error(f"Conversation loading failed: {e}")
            raise

        logger.info(f"Supervisor initialized with model: {model_string}")

        # Initialize supervisor service and create custom ReAct graph
        logger.info("Creating custom ReAct graph with ToolRegistry")

        try:
            # Initialize tools from conversation configuration
            tool_registry = await initialize_tools_from_config_async(
                assistant_config=conversation.assistant_config,
                llm_client=llm_client,
                rag_context="",
                tool_instances={},  # Tools will be loaded from config
            )

            # *** KEY DIFFERENCE: Create our custom ReAct graph instead of create_agent() ***
            main_agent = create_graph(tool_registry)

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

        # Prepare conversation messages
        messages = [{"role": "user", "content": query}]
        if conversation.messages:
            for msg in conversation.messages[-10:]:  # Last 10 messages
                messages.append({"role": msg.role, "content": msg.content})

        # Configure graph execution
        config_for_stream = {
            "recursion_limit": 10,
        }

        final_response = ""
        tools_used = []

        try:
            # Stream events from custom ReAct graph
            # Pass model_str from enhancement strategy (or answer_generation) to graph via state
            async for event in main_agent.astream(
                {
                    "messages": messages,
                    "model_str": model_string,
                },
                config=config_for_stream,
            ):
                # Process graph events
                if isinstance(event, dict) and "messages" in event:
                    messages_list = event.get("messages", [])
                    if messages_list:
                        last_msg = messages_list[-1]

                        # Track tool calls
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            for tool_call in last_msg.tool_calls:
                                tool_name = tool_call.get("name", "")
                                if tool_name and tool_name not in tools_used:
                                    tools_used.append(tool_name)
                                    logger.info(f"Tool called: {tool_name}")

                        # Stream content chunks
                        if hasattr(last_msg, "content") and last_msg.content:
                            final_response = last_msg.content
                            yield {
                                "type": "streaming_response",
                                "chunk": final_response,
                                "metadata": {
                                    "tools_used": tools_used,
                                    "orchestrator_type": "custom_react_pattern",
                                },
                                "execution_time_ms": (
                                    time.time() - start_time
                                ) * 1000,
                            }

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
            },
            "execution_time_ms": execution_time_ms,
        }

        # Save to conversation history
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
                processing_time_ms=int(execution_time_ms),
            )
            conversation_history_service.add_message(conversation_id, assistant_message)

            logger.info(
                f"✅ Saved conversation messages to {conversation_id}"
            )
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            # Continue - don't fail the entire operation

        # Final result
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
            },
        }

        yield final_result

        logger.info(
            f"Custom ReAct Pattern completed in {execution_time_ms:.2f}ms"
        )

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
            user_message = f"Failed to initialize supervisor agent. Error: {str(e)[:100]}"
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
