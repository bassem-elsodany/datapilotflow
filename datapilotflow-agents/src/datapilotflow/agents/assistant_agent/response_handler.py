"""
Response Handler for Deep Agent.

Provides high-level functions for executing deep agents with streaming support.
Integrates with DataPilotFlow's WebSocket infrastructure.
"""

import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from datapilotflow.agents.assistant_agent.factory import create_assistant_agent_for_conversation

# Global checkpointer - set during app startup
_global_checkpointer: Optional[Any] = None


async def _extract_files_from_state(final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract files from agent's final state.

    Deep Agents automatically populates the "files" key in the output state
    when the agent calls file manipulation tools (write_file, edit_file).

    Args:
        final_state: Final state dict from agent execution

    Returns:
        Dict mapping file paths to content
    """
    try:
        # The "files" key is populated by FilesystemMiddleware in Deep Agents
        # Structure: {"path": {"content": list[str], "created_at": str, "modified_at": str}}
        files = final_state.get("files", {})

        if files:
            logger.debug(f"Extracted {len(files)} files from agent state")

        return files

    except Exception as e:
        logger.error(f"Error extracting files from state: {e}")
        return {}


async def _extract_persistent_files_from_store(agent_id: Optional[str]) -> Dict[str, Any]:
    """
    Extract persistent files from MongoDBStore.

    Files saved with /memories/ prefix are stored in the MongoDBStore
    under agent-specific collections.

    Args:
        agent_id: Agent ID for accessing agent-specific store

    Returns:
        Dict mapping file paths to content
    """
    try:
        if not agent_id:
            logger.debug("No agent_id provided, skipping persistent file retrieval")
            return {}

        from pymongo import MongoClient
        from src.config import settings

        # Build MongoDB URI
        if settings.MONGO_USER and settings.MONGO_PASS:
            mongo_uri = f"mongodb://{settings.MONGO_USER}:{settings.MONGO_PASS}@{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        else:
            mongo_uri = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}"

        client = MongoClient(mongo_uri)
        db = client[settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME]

        # Query the agent-specific persistent storage collection
        collection_name = f"persistent_storage_{agent_id}"
        if collection_name not in db.list_collection_names():
            logger.debug(f"No persistent store collection found: {collection_name}")
            return {}

        collection = db[collection_name]

        # Query all files (namespace='filesystem' for all file documents)
        docs = list(collection.find({"namespace": ["filesystem"]}))

        files_dict: Dict[str, Any] = {}
        for doc in docs:
            file_path = doc.get("key")
            value = doc.get("value", {})

            if file_path and isinstance(value, dict) and "content" in value:
                files_dict[file_path] = value

        logger.debug(f"Loaded {len(files_dict)} persistent files")

        return files_dict

    except Exception as e:
        logger.error(f"Error extracting persistent files from store: {e}")
        return {}


def set_checkpointer(checkpointer: Any) -> None:
    """Set the global checkpointer for deep agent (called during app startup)."""
    global _global_checkpointer
    _global_checkpointer = checkpointer
    logger.debug("Checkpointer initialized")


async def get_assistant_agent_response(
    user_message: str,
    user_id: str,
    conversation_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    system_prompt: Optional[str] = None,
    new_thread: bool = False,
) -> tuple[str, Dict[str, Any]]:
    """
    Execute deep agent and return the final response (non-streaming).

    Uses hybrid storage pattern:
    - Transient files: StateBackend (ephemeral, per-thread)
    - Persistent files (/memories/): StoreBackend with agent-specific MongoDB collection

    Args:
        user_message: User's input message
        user_id: User ID
        conversation_id: Conversation ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        system_prompt: Optional custom system prompt
        new_thread: Whether to create a new conversation thread

    Returns:
        Tuple of (response_text, final_state)
    """
    logger.debug(f"Getting agent response for conversation {conversation_id}")

    # Create conversation ID if needed
    local_conversation_id = conversation_id
    if not local_conversation_id or new_thread:
        local_conversation_id = f"conv_{uuid.uuid4()}"

    # Get global checkpointer
    global _global_checkpointer
    checkpointer = _global_checkpointer

    # Get agent_id from conversation
    from src.services.conversation.conversation_history_service import (
        conversation_history_service,
    )
    conversation = conversation_history_service.get_conversation(local_conversation_id)
    agent_id = conversation.agent_id if conversation else None

    # Create assistant agent with hybrid storage
    # Long-term memory is handled via MongoDBStore with agent-specific collections
    agent = await create_assistant_agent_for_conversation(
        conversation_id=local_conversation_id,
        user_id=user_id,
        llm_provider_id=llm_provider_id,
        llm_model_name=llm_model_name,
        agent_id=agent_id,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=None,  # Will use agent-specific MongoDBStore
    )

    # Setup config with thread_id for checkpoint persistence
    config: Dict[str, Any] = {"configurable": {"thread_id": local_conversation_id}}

    # Execute agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]}, config=config  # type: ignore
    )

    # Extract response
    response_text = result["messages"][-1].content if result.get("messages") else ""

    logger.debug(f"Agent response completed ({len(response_text)} chars)")

    return response_text, result


async def get_assistant_agent_streaming_response(
    user_message: str,
    user_id: str,
    conversation_id: str,
    llm_provider_id: str,
    llm_model_name: str,
    system_prompt: Optional[str] = None,
    new_thread: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute deep agent with streaming responses.

    Yields real-time updates including tool calls, planning, and responses.
    Uses hybrid storage pattern with agent-specific MongoDB collection for persistent memory.

    Args:
        user_message: User's input message
        user_id: User ID
        conversation_id: Conversation ID
        llm_provider_id: LLM provider ID
        llm_model_name: LLM model name
        system_prompt: Optional custom system prompt
        new_thread: Whether to create a new conversation thread

    Yields:
        Dict with streaming updates (type, content, metadata)
    """
    logger.debug(
        f"Starting agent stream for conversation {conversation_id}"
    )

    # Create conversation ID if needed
    local_conversation_id = conversation_id
    if not local_conversation_id or new_thread:
        local_conversation_id = f"conv_{uuid.uuid4()}"

    # Get global checkpointer
    global _global_checkpointer
    checkpointer = _global_checkpointer

    # Get agent_id from conversation
    from src.services.conversation.conversation_history_service import (
        conversation_history_service,
    )
    conversation = conversation_history_service.get_conversation(local_conversation_id)
    agent_id = conversation.agent_id if conversation else None

    # Create assistant agent with hybrid storage
    # Long-term memory is handled via MongoDBStore with agent-specific collections
    agent = await create_assistant_agent_for_conversation(
        conversation_id=local_conversation_id,
        user_id=user_id,
        llm_provider_id=llm_provider_id,
        llm_model_name=llm_model_name,
        agent_id=agent_id,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=None,  # Will use agent-specific MongoDBStore
    )

    # Setup config with thread_id for checkpoint persistence
    config: Dict[str, Any] = {"configurable": {"thread_id": local_conversation_id}}

    # Stream agent execution
    try:
        final_state: Dict[str, Any] = {}

        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,  # type: ignore
            version="v2",
        ):
            try:
                event_type = event.get("event")
                event_name = event.get("name", "")
                event_data = event.get("data", {})

                # Capture final state output
                if event_type == "on_chain_end" and event_name == "LangGraph":
                    output = event_data.get("output", {})
                    final_state.update(output)
                    logger.debug(f"Captured final state with keys: {list(output.keys())}")

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

        # Extract files from both transient state and persistent store
        # Get transient files from final state
        transient_files = await _extract_files_from_state(final_state)

        # Get persistent files from MongoDBStore
        persistent_files = await _extract_persistent_files_from_store(agent_id)

        # Merge all files (persistent takes precedence if paths overlap)
        all_files = {**transient_files, **persistent_files}

        if all_files:
            logger.debug(f"Sending {len(all_files)} files (transient: {len(transient_files)}, persistent: {len(persistent_files)})")
            yield {
                "type": "files",
                "data": all_files,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "conversation_id": local_conversation_id,
                    "file_count": len(all_files),
                    "transient_count": len(transient_files),
                    "persistent_count": len(persistent_files),
                },
            }

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
