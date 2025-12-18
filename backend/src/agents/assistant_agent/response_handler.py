"""
Response Handler for Deep Agent.

Provides high-level functions for executing deep agents with streaming support.
Integrates with DataPilotFlow's WebSocket infrastructure.
"""

import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from src.agents.assistant_agent.factory import create_assistant_agent_for_conversation
from src.agents.assistant_agent.memory import create_memory_namespace, get_memory_store

# Global checkpointer - set during app startup
_global_checkpointer: Optional[Any] = None


def set_checkpointer(checkpointer: Any) -> None:
    """Set the global checkpointer for deep agent (called during app startup)."""
    global _global_checkpointer
    _global_checkpointer = checkpointer
    logger.info("Checkpointer set for assistant_agent")


async def get_assistant_agent_response(
    user_message: str,
    user_id: str,
    conversation_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    system_prompt: Optional[str] = None,
    use_long_term_memory: bool = False,
    new_thread: bool = False,
) -> tuple[str, Dict[str, Any]]:
    """
    Execute deep agent and return the final response (non-streaming).

    Uses hybrid storage pattern:
    - Transient files: StateBackend (ephemeral, per-thread)
    - Persistent files (/memories/): StoreBackend (cross-thread)

    Args:
        user_message: User's input message
        user_id: User ID
        conversation_id: Conversation ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        system_prompt: Optional custom system prompt
        use_long_term_memory: Whether to enable long-term memory store
        new_thread: Whether to create a new conversation thread

    Returns:
        Tuple of (response_text, final_state)
    """
    logger.info(f"Getting deep agent response for conversation {conversation_id}")

    # Create conversation ID if needed
    local_conversation_id = conversation_id
    if not local_conversation_id or new_thread:
        local_conversation_id = f"conv_{uuid.uuid4()}"

    # Get global checkpointer
    global _global_checkpointer
    checkpointer = _global_checkpointer

    # Setup memory store if enabled
    store = None
    if use_long_term_memory:
        store = get_memory_store()
        logger.info("Using long-term memory store")

    # Create assistant agent with hybrid storage
    agent = await create_assistant_agent_for_conversation(
        conversation_id=local_conversation_id,
        user_id=user_id,
        llm_provider_id=llm_provider_id,
        llm_model_name=llm_model_name,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=store,
    )

    # Setup config
    config: Dict[str, Any] = {"configurable": {"thread_id": local_conversation_id}}

    # Add long-term memory if enabled
    # TODO: Deep Agents handles store configuration internally
    # For now, we'll just use the thread_id for persistence via checkpointer
    if use_long_term_memory:
        memory_namespace = create_memory_namespace(user_id, local_conversation_id)
        config["configurable"]["memory_namespace"] = memory_namespace
        logger.info(f"Long-term memory namespace: {memory_namespace}")

    # Execute agent
    logger.info("Invoking deep agent...")
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]}, config=config  # type: ignore
    )

    # Extract response
    response_text = result["messages"][-1].content if result.get("messages") else ""

    logger.info(f"Deep agent completed. Response length: {len(response_text)} chars")

    return response_text, result


async def get_assistant_agent_streaming_response(
    user_message: str,
    user_id: str,
    conversation_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    system_prompt: Optional[str] = None,
    use_long_term_memory: bool = False,
    new_thread: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute deep agent with streaming responses.

    Yields real-time updates including tool calls, planning, and responses.
    Uses hybrid storage pattern (StateBackend + StoreBackend).

    Args:
        user_message: User's input message
        user_id: User ID
        conversation_id: Conversation ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        system_prompt: Optional custom system prompt
        use_long_term_memory: Whether to enable long-term memory store
        new_thread: Whether to create a new conversation thread

    Yields:
        Dict with streaming updates (type, content, metadata)
    """
    logger.info(
        f"Getting deep agent streaming response for conversation {conversation_id}"
    )

    # Create conversation ID if needed
    local_conversation_id = conversation_id
    if not local_conversation_id or new_thread:
        local_conversation_id = f"conv_{uuid.uuid4()}"

    # Get global checkpointer
    global _global_checkpointer
    checkpointer = _global_checkpointer

    # Setup memory store if enabled
    store = None
    if use_long_term_memory:
        store = get_memory_store()
        logger.info("Using long-term memory store")

    # Create assistant agent with hybrid storage
    agent = await create_assistant_agent_for_conversation(
        conversation_id=local_conversation_id,
        user_id=user_id,
        llm_provider_id=llm_provider_id,
        llm_model_name=llm_model_name,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=store,
    )

    # Setup config
    config: Dict[str, Any] = {"configurable": {"thread_id": local_conversation_id}}

    # Add long-term memory if enabled
    # TODO: Deep Agents handles store configuration internally
    # For now, we'll just use the thread_id for persistence via checkpointer
    if use_long_term_memory:
        memory_namespace = create_memory_namespace(user_id, local_conversation_id)
        config["configurable"]["memory_namespace"] = memory_namespace
        logger.info(f"Long-term memory namespace: {memory_namespace}")

    # Stream agent execution
    try:
        logger.info("Starting deep agent stream...")

        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,  # type: ignore
            version="v2",
        ):
            try:
                event_type = event.get("event")
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Tool call start
                if event_type == "on_chat_model_stream" and "tool_calls" in event_data:
                    for tool_call in event_data.get("tool_calls", []):
                        yield {
                            "type": "tool_call",
                            "content": {
                                "tool_name": tool_call.get("name"),
                                "tool_args": tool_call.get("args"),
                            },
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {"event_name": event_name},
                        }

                # AI message content
                elif event_type == "on_chat_model_stream" and "content" in event_data:
                    content = event_data.get("content")
                    if content:
                        yield {
                            "type": "content",
                            "content": content,
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {"event_name": event_name},
                        }

                # Tool execution result
                elif event_type == "on_tool_end":
                    yield {
                        "type": "tool_result",
                        "content": {"tool_name": event_name, "result": event_data},
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"event_name": event_name},
                    }

            except Exception as e:
                logger.warning(f"Error processing stream event: {e}")
                continue

        # Send completion
        yield {
            "type": "stream_complete",
            "content": "Deep agent execution completed",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"conversation_id": local_conversation_id},
        }

    except Exception as e:
        logger.error(f"Error in deep agent stream: {e}")
        yield {
            "type": "error",
            "content": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"error_type": "stream_error"},
        }
