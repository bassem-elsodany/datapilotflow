"""
Assistant Agent WebSocket Router.

WebSocket endpoint for Assistant Agent conversations with full DataPilotFlow integration.
Uses factory.py to create agents with user's LLM config and tools.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, WebSocket
from fastapi.websockets import WebSocketDisconnect
from langchain_core.runnables import RunnableConfig
from loguru import logger

from datapilotflow.assistant_agent import create_assistant_agent_for_conversation
from datapilotflow.api.routers.auth.auth_router import decode_access_token
from datapilotflow.domain.config import settings
from datapilotflow.services.conversation.conversation_history_service import (
    conversation_history_service,
)

router = APIRouter(tags=["Assistant Agent WebSocket"])


async def _retrieve_persistent_files(agent_id: str) -> dict:
    """
    Retrieve persistent files from agent-specific MongoDB collection.

    Files saved with /memories/ prefix are stored in MongoDBStore
    under persistent_storage_{agent_id} collection.

    Args:
        agent_id: Agent ID to query persistent files for

    Returns:
        Dict mapping file paths to file metadata
    """
    try:
        if not agent_id:
            logger.debug("No agent_id provided, skipping persistent file retrieval")
            return {}

        from pymongo import MongoClient

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

        files_dict = {}
        for doc in docs:
            file_path = doc.get("key")
            value = doc.get("value", {})

            if file_path and isinstance(value, dict) and "content" in value:
                files_dict[file_path] = value

        logger.debug(f"Retrieved {len(files_dict)} persistent files")

        return files_dict

    except Exception as e:
        logger.error(f"Error retrieving persistent files from store: {e}", exc_info=True)
        return {}


@router.websocket("/ws/agent/query/assistant")
async def agent_query_assistant_websocket(
    websocket: WebSocket, token: str = Query(None)
):
    """
    WebSocket endpoint for Assistant Agent query processing.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database"
    }
    ```

    **Response Format** (to client):
    ```json
    {
        "type": "chunk|todos|files|tool_call|error|done",
        "data": {...},
        "timestamp": "ISO timestamp"
    }
    ```
    """
    logger.debug("WebSocket endpoint invoked: /ws/agent/query/assistant")

    # Accept connection FIRST
    await websocket.accept()

    # Validate JWT token
    timeout = settings.WEBSOCKET_TIMEOUT

    try:
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Decode and validate token
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        username = payload.get("sub")

        if not user_id:
            await websocket.close(code=1008, reason="Invalid token payload")
            return

        logger.debug(f"WebSocket auth: user_id={user_id}, username={username}")

    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    logger.debug(f"WebSocket connected for user: {user_id}")

    try:
        while True:
            try:
                # Wait for message from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                msg = json.loads(data)

                query = msg.get("query")
                conversation_id = msg.get("conversation_id") or msg.get("session_id")

                logger.info(
                    f"📨 [ASSISTANT AGENT QUERY] Query: {query[:100]}{'...' if len(query) > 100 else ''} | Conversation: {conversation_id}"
                )

                if not conversation_id:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {"message": "No conversation_id provided"},
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # Load conversation configuration
                conversation = conversation_history_service.get_conversation(
                    conversation_id
                )
                if not conversation:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {"message": "Conversation not found"},
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # NEW ARCHITECTURE: Configuration is stored in Agent, not Conversation
                agent = None
                if conversation.agent_id:
                    logger.info(
                        f"🔗 Conversation linked to agent {conversation.agent_id}"
                    )
                    from datapilotflow.services.agent.agent_service import get_agent_service

                    agent_service = get_agent_service()
                    agent = agent_service.get_agent(conversation.agent_id, user_id)

                    if agent:
                        logger.debug(f"Loaded agent '{agent.name}'")
                    else:
                        logger.warning(f"Agent {conversation.agent_id} not found")

                if not agent:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {"message": "Agent configuration not found"},
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # Use primary LLM provider (required for Assistant mode)
                if not agent.llm_provider:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {
                                    "message": "No LLM provider configured for agent"
                                },
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                llm_provider_id = agent.llm_provider.id
                llm_model_name = agent.llm_provider.model_name

                logger.debug(
                    f"Creating Assistant Agent: provider={llm_provider_id}, model={llm_model_name}"
                )

                if settings.MONGO_AGENT_STATE_CHECKPOINT_ENABLED:
                    # Get global checkpointer (set during app startup)
                    from datapilotflow.assistant_agent.response_handler import (
                        _global_checkpointer,
                    )

                    if not _global_checkpointer:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "data": {"message": "Checkpointer not initialized"},
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                    # DEBUG: Check what checkpoint data exists before agent creation
                    logger.debug(
                        f"Checking for existing checkpoint data for thread_id={conversation_id}"
                    )
                    try:
                        checkpoint_mongo_client = (
                            _global_checkpointer.client
                            if hasattr(_global_checkpointer, "client")
                            else None
                        )
                        if checkpoint_mongo_client:
                            checkpoint_db = checkpoint_mongo_client[
                                settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME
                            ]
                            checkpoints_col = checkpoint_db[
                                settings.MONGO_AGENT_STATE_CHECKPOINT_COLLECTION
                            ]
                            writes_col = checkpoint_db[
                                settings.MONGO_AGENT_STATE_WRITES_COLLECTION
                            ]
                            # Agent-specific memory store collection
                            memory_collection_name = (
                                f"persistent_storage_{conversation.agent_id}"
                                if conversation.agent_id
                                else "persistent_storage_default"
                            )
                            memory_col = checkpoint_db[memory_collection_name]

                            # Use count_documents for checkpoint counts
                            checkpoint_count = checkpoints_col.count_documents(
                                {"thread_id.thread_id": conversation_id}
                            )
                            writes_count = writes_col.count_documents(
                                {"thread_id.thread_id": conversation_id}
                            )

                            # Check memory store for this agent/conversation
                            memory_count = memory_col.count_documents(
                                {"namespace": {"$exists": True}}
                            )

                            logger.debug(
                                f"Found {checkpoint_count} checkpoint(s) for thread {conversation_id}"
                            )
                    except Exception as debug_error:
                        logger.warning(
                            f"Could not check checkpoint data: {debug_error}",
                            exc_info=True,
                        )
                else:
                    _global_checkpointer = None
                # Create Assistant Agent using factory
                # Note: Uses hybrid storage (StateBackend + StoreBackend with agent-specific MongoDB collection)
                logger.info(
                    f"🔧 [CREATING AGENT] Creating Assistant Agent for conversation {conversation_id}, agent {conversation.agent_id}"
                )
                agent = await create_assistant_agent_for_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    llm_provider_id=llm_provider_id,
                    llm_model_name=llm_model_name,
                    agent_id=conversation.agent_id,
                    checkpointer=_global_checkpointer,
                    store=None,  # Will use agent-specific MongoDBStore
                )

                # Stream agent execution
                config: RunnableConfig = {
                    "configurable": {
                        "thread_id": conversation_id,
                        "checkpoint_ns": "",
                    }
                }
                logger.info(
                    f"🚀 [STREAMING START] Starting agent stream with config: thread_id={conversation_id}"
                )

                # Send start event
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "start",
                            "data": {"query": query},
                            "timestamp": time.time(),
                        }
                    )
                )

                # Track complete assistant response for persistence
                full_assistant_response = ""

                # DEBUG: Log what we're sending to the agent
                logger.debug(f"Sending query to agent (thread_id={config['configurable']['thread_id']})")

                # Stream events from agent
                stream_events_logged = False
                async for event in agent.astream_events(
                    {"messages": [{"role": "human", "content": query}]},
                    config=config,
                    version="v2",
                ):
                    event_type = event.get("event")
                    event_name = event.get("name")
                    event_data = event.get("data", {})

                    # Log initial state on first event
                    if not stream_events_logged and event_type == "on_chain_start":
                        stream_events_logged = True
                        logger.debug(f"Agent stream started")

                    # Stream message chunks
                    if event_type == "on_chat_model_stream":
                        chunk = event_data.get("chunk")
                        if chunk and hasattr(chunk, "content"):
                            content = chunk.content
                            if content:
                                # Accumulate full response
                                full_assistant_response += content

                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "chunk",
                                            "data": {"content": content},
                                            "timestamp": time.time(),
                                        }
                                    )
                                )

                    # Stream tool calls
                    elif event_type == "on_tool_start":
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "tool_call",
                                    "data": {
                                        "name": event_name,
                                        "inputs": event_data.get("input"),
                                        "status": "started",
                                    },
                                    "timestamp": time.time(),
                                }
                            )
                        )

                    elif event_type == "on_tool_end":
                        # Serialize tool output (may contain LangChain message objects)
                        tool_output = event_data.get("output")
                        if tool_output:
                            # Convert to string if it's a complex object
                            if hasattr(tool_output, "content"):
                                tool_output = tool_output.content
                            elif not isinstance(
                                tool_output, (str, int, float, bool, dict, list)
                            ):
                                tool_output = str(tool_output)

                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "tool_call",
                                    "data": {
                                        "name": event_name,
                                        "output": tool_output,
                                        "status": "completed",
                                    },
                                    "timestamp": time.time(),
                                }
                            )
                        )

                    # Stream state updates (todos, files)
                    elif event_type == "on_chain_end" and event_name == "LangGraph":
                        output = event_data.get("output", {})

                        # Send todos if present
                        if "todos" in output:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "todos",
                                        "data": output["todos"],
                                        "timestamp": time.time(),
                                    }
                                )
                            )

                        # Send files if present
                        if "files" in output:
                            files_data = output["files"]
                            file_count = len(files_data) if files_data else 0
                            logger.debug(f"Sending {file_count} file(s) to frontend")
                            # Log file structure and content for debugging
                            if files_data:
                                for file_path, file_obj in files_data.items():
                                    # Extract content
                                    if (
                                        isinstance(file_obj, dict)
                                        and "content" in file_obj
                                    ):
                                        content = file_obj["content"]

                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "files",
                                        "data": files_data,
                                        "timestamp": time.time(),
                                    }
                                )
                            )

                # Save conversation messages to database
                try:
                    from datetime import datetime

                    # Add user message
                    conversation_history_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="user",
                        content=query,
                    )
                    logger.debug(
                        f"Saved user message to conversation {conversation_id}"
                    )

                    # Add assistant message
                    if full_assistant_response:
                        conversation_history_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role="assistant",
                            content=full_assistant_response,
                        )
                        logger.debug(
                            f"Saved assistant message to conversation {conversation_id}"
                        )

                    logger.debug("Messages saved to database")
                except Exception as e:
                    logger.error(f"Failed to save messages: {e}", exc_info=True)

                # Extract and send persistent files from MongoDB store
                try:
                    if conversation.agent_id:
                        persistent_files = await _retrieve_persistent_files(
                            conversation.agent_id
                        )
                        if persistent_files:
                            logger.debug(
                                f"Sending {len(persistent_files)} persistent file(s)"
                            )
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "files",
                                        "data": persistent_files,
                                        "timestamp": time.time(),
                                    }
                                )
                            )
                    else:
                        logger.debug("No agent_id available, skipping file retrieval")
                except Exception as file_error:
                    logger.error(
                        f"Error retrieving persistent files: {file_error}",
                        exc_info=True,
                    )

                # Send completion
                await websocket.send_text(
                    json.dumps({"type": "done", "data": {}, "timestamp": time.time()})
                )

                logger.debug("Query processed successfully")

            except asyncio.TimeoutError:
                logger.warning(f"WebSocket timeout after {timeout}s of inactivity")
                await websocket.close(code=1000, reason="Timeout")
                break

            except WebSocketDisconnect:
                logger.debug("WebSocket disconnected by client")
                break

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "data": {"message": "Invalid JSON format"},
                            "timestamp": time.time(),
                        }
                    )
                )

            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {"message": str(e)},
                                "timestamp": time.time(),
                            }
                        )
                    )
                except:
                    pass

    except Exception as e:
        logger.error(f"Fatal WebSocket error: {e}", exc_info=True)
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.debug("WebSocket connection closed")
