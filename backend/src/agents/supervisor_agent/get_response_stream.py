"""Generate Response Stream using Supervisor Agent.

Streaming async generator that yields progress events as the supervisor agent executes.
Matches the assistant_agent pattern for compatibility.
"""

import asyncio
import time
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import HumanMessage
from loguru import logger

from src.agents.supervisor_agent.service import SupervisorAgentService
from src.agents.supervisor_agent.context import Context
from src.domain.conversation.models import ConversationSession
from src.domain.tool.models import Tool
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)


async def get_response_stream_supervisor(
    query: str,
    user_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    conversation_id: str,
    collection_name: str,
    enable_reranking: bool = True,
    relevance_threshold: float = 0.5,
    top_k: int = 5,
    conversation_description: Optional[str] = None,
    max_iterations: int = 10,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate AI response using Supervisor Agent with streaming events.

    Yields progress events as the supervisor executes:
    - supervisor_started: Agent initialized
    - supervisor_executing: Agent running
    - tool_executing: Tool being called
    - tool_executed: Tool completed
    - supervisor_response_ready: Final response ready
    - workflow_complete: Execution finished

    Args:
        query: User's question/request
        user_id: User ID for conversation
        llm_provider_id: LLM provider ID (e.g., "anthropic")
        llm_model_name: Model name (e.g., "claude-sonnet-4-5-20250929")
        conversation_id: Conversation session ID
        collection_name: RAG collection name
        enable_reranking: Whether to enable reranking
        relevance_threshold: Reranking relevance threshold
        top_k: Max documents to retrieve
        conversation_description: Optional description of conversation domain
        max_iterations: Max agent iterations

    Yields:
        Event dictionaries with type, timestamp, and event-specific data
    """
    start_time = time.time()

    # Central state tracking
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
        # ============================================================
        # PHASE 1: INITIALIZATION
        # ============================================================

        logger.info(
            f"Supervisor Agent starting - provider={llm_provider_id}, model={llm_model_name}"
        )

        # Yield initialization START
        yield {
            "type": "supervisor_started",
            "stage": "supervisor_init",
            "message": "Initializing Supervisor Agent System",
            "execution_time_ms": (time.time() - start_time) * 1000,
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
            from langchain_community.chat_models import ChatLiteLLM

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
            logger.info(f"LLM client created: {model_string}")

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

        # Load tools from conversation config
        tool_instances: Dict[str, Tool] = {}
        if (
            conversation.assistant_config
            and conversation.assistant_config.tools
        ):
            try:
                # TODO: Implement tool loading from database
                # For now, tools will be loaded dynamically by SupervisorAgentService
                logger.info(
                    f"Supervisor will load {len(conversation.assistant_config.tools)} tools from config"
                )
            except Exception as e:
                logger.error(f"Failed to load tools: {e}")
                # Continue - service will use defaults

        response_state["initialization_complete"] = True

        yield {
            "type": "supervisor_initialized",
            "stage": "supervisor_ready",
            "message": "Supervisor Agent Initialized",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # ============================================================
        # PHASE 2: AGENT EXECUTION
        # ============================================================

        logger.info("Starting supervisor agent execution")

        yield {
            "type": "agent_execution_starting",
            "stage": "agent_executing",
            "message": "Analyzing Query and Executing Tasks",
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Initialize supervisor service
        context = Context(model=f"{provider.provider_type}/{llm_model_name}")
        service = SupervisorAgentService(context=context)

        # Initialize agent for conversation
        # Pass the llm_client we already created to avoid creating it twice
        await service.initialize_for_conversation(
            conversation=conversation,
            tool_instances=tool_instances,
            rag_context="",  # Will be populated during execution
            llm_client=llm_client,  # Use the one we already created
        )

        # Get previous conversation messages
        conversation_messages = []
        if conversation.messages:
            from langchain_core.messages import HumanMessage, AIMessage

            for msg in conversation.messages:
                if msg.role == "user":
                    conversation_messages.append(HumanMessage(content=msg.content))
                else:
                    conversation_messages.append(AIMessage(content=msg.content))

        # Execute conversation turn
        try:
            async for event in service.stream_conversation(
                user_message=query,
                conversation_messages=conversation_messages,
                max_iterations=max_iterations,
            ):
                # Relay events from service to client
                yield {
                    **event,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

                # Track if we've got a response
                if event["type"] == "workflow_complete":
                    response_state["has_yielded_response"] = True

        except Exception as e:
            response_state["error_occurred"] = True
            response_state["error_details"] = str(e)
            logger.error(f"Agent execution failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        # ============================================================
        # PHASE 3: COMPLETION
        # ============================================================

        logger.info("Supervisor agent execution completed")

        yield {
            "type": "workflow_complete",
            "stage": "complete",
            "message": "Workflow Completed Successfully",
            "execution_time_ms": (time.time() - start_time) * 1000,
            "total_iterations": 0,  # TODO: track from service
            "final_response_length": len(response_state["final_response"]),
        }

    except Exception as e:
        # Error occurred - yield error event
        logger.error(f"Supervisor stream error: {e}")

        error_event = {
            "type": "workflow_complete",
            "stage": "error",
            "message": f"Workflow Failed: {str(e)}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

        # Only yield error if we haven't already yielded a response
        if not response_state["has_yielded_response"]:
            yield error_event

        # Log full error details
        logger.error(f"Error details: {response_state['error_details']}")
        if response_state.get("error_details"):
            logger.error(f"Error context: {response_state['error_details']}")

        raise
