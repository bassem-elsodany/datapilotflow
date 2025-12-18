"""
Assistant Agent WebSocket Router.

WebSocket endpoint for Assistant Agent conversations with full DataPilotFlow integration.
Uses factory.py to create agents with user's LLM config and tools.
"""

import asyncio
import json
import time
import traceback
from typing import cast

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from langchain_core.runnables import RunnableConfig
from loguru import logger

from src.agents.assistant_agent.factory import create_assistant_agent_for_conversation
from src.api.routers.auth.auth_router import decode_access_token
from src.config import settings
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

router = APIRouter(tags=["Assistant Agent WebSocket"])


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
    logger.info("=" * 80)
    logger.info("ASSISTANT AGENT ENDPOINT INVOKED | /ws/agent/query/assistant")
    logger.info("=" * 80)

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

    logger.info(f"Assistant Agent WebSocket connected for user: {user_id}")

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
                    from src.services.agent.agent_service import get_agent_service

                    agent_service = get_agent_service()
                    agent = agent_service.get_agent(conversation.agent_id, user_id)

                    if agent:
                        logger.info(f"✅ Loaded agent '{agent.name}' configuration")
                    else:
                        logger.warning(
                            f"⚠️ Agent {conversation.agent_id} not found"
                        )

                if not agent:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "data": {
                                    "message": "Agent configuration not found"
                                },
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

                logger.info(
                    f"Creating Assistant Agent: provider={llm_provider_id}, model={llm_model_name}"
                )

                # Get global checkpointer (set during app startup)
                from src.agents.assistant_agent.response_handler import (
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
                logger.info(f"🔍 [CHECKPOINT DEBUG] Checking for existing checkpoint data for thread_id={conversation_id}")
                try:
                    checkpoint_mongo_client = _global_checkpointer.client if hasattr(_global_checkpointer, 'client') else None
                    if checkpoint_mongo_client:
                        checkpoint_db = checkpoint_mongo_client[settings.MONGO_AGENT_STATE_CHECKPOINT_DB_NAME]
                        checkpoints_col = checkpoint_db[settings.MONGO_AGENT_STATE_CHECKPOINT_COLLECTION]
                        writes_col = checkpoint_db[settings.MONGO_AGENT_STATE_WRITES_COLLECTION]
                        memory_col = checkpoint_db["agent_memory_store"]

                        # Use count_documents for checkpoint counts
                        checkpoint_count = checkpoints_col.count_documents({"thread_id.thread_id": conversation_id})
                        writes_count = writes_col.count_documents({"thread_id.thread_id": conversation_id})

                        # Check memory store for this conversation
                        memory_namespace = f"user:{user_id}:conversation:{conversation_id}"
                        memory_count = memory_col.count_documents({"namespace": memory_namespace})

                        logger.info(f"📊 [CHECKPOINT DEBUG] Found {checkpoint_count} checkpoint(s) for thread {conversation_id}")
                        logger.info(f"📊 [WRITES DEBUG] Found {writes_count} write(s) for thread {conversation_id}")
                        logger.info(f"📊 [MEMORY STORE DEBUG] Found {memory_count} memory item(s) with namespace: {memory_namespace}")
                except Exception as debug_error:
                    logger.warning(f"⚠️ [CHECKPOINT DEBUG ERROR] Could not check checkpoint data: {debug_error}", exc_info=True)

                # Create Assistant Agent using factory
                # Note: Uses hybrid storage (StateBackend + StoreBackend with InMemoryStore)
                logger.info(f"🔧 [CREATING AGENT] Creating Assistant Agent for conversation {conversation_id}")
                agent = await create_assistant_agent_for_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    llm_provider_id=llm_provider_id,
                    llm_model_name=llm_model_name,
                    checkpointer=_global_checkpointer,
                    store=None,  # Will use InMemoryStore by default
                )

                # Stream agent execution
                config: RunnableConfig = {
                    "configurable": {
                        "thread_id": conversation_id,
                        "checkpoint_ns": "",
                    }
                }
                logger.info(f"🚀 [STREAMING START] Starting agent stream with config: thread_id={conversation_id}")

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
                logger.info(f"📤 [AGENT INPUT] Sending to agent:")
                logger.info(f"   Query: {query[:100]}{'...' if len(query) > 100 else ''}")
                logger.info(f"   Thread ID (from config): {config['configurable']['thread_id']}")
                logger.info(f"   Input format: messages=[{{'role': 'human', 'content': query}}]")
                logger.info(f"   Note: Agent will automatically load checkpoint data from checkpoint storage if it exists")

                # Stream events from agent
                logger.info(f"⏳ [AGENT STREAM START] Beginning agent execution stream...")
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
                        logger.info(f"✅ [AGENT STATE AT START] First event received from agent")
                        logger.info(f"   Event name: {event_name}")
                        if "input" in event_data:
                            input_data = event_data["input"]
                            logger.info(f"   Input type: {type(input_data)}")
                            if isinstance(input_data, dict) and "messages" in input_data:
                                logger.info(f"   Messages in state: {len(input_data['messages'])}")
                                if input_data['messages']:
                                    logger.info(f"   First message: role={input_data['messages'][0].get('role')}, content_len={len(str(input_data['messages'][0].get('content', '')))}")

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
                            logger.info(
                                f"📁 Sending {file_count} file(s) to frontend: {list(files_data.keys()) if files_data else []}"
                            )
                            # Log file structure and content for debugging
                            if files_data:
                                for file_path, file_obj in files_data.items():
                                    logger.info(f"📄 File: {file_path}")
                                    logger.info(f"   Type: {type(file_obj)}")

                                    # Extract content
                                    if (
                                        isinstance(file_obj, dict)
                                        and "content" in file_obj
                                    ):
                                        content = file_obj["content"]
                                        if isinstance(content, list):
                                            total_length = sum(
                                                len(line) for line in content
                                            )
                                            logger.info(
                                                f"   Content: {len(content)} lines, {total_length} chars total"
                                            )
                                            logger.info(
                                                f"   First line: {content[0][:100] if content else 'EMPTY'}"
                                            )
                                            logger.info(
                                                f"   Last line: {content[-1][:100] if content else 'EMPTY'}"
                                            )
                                        else:
                                            logger.info(
                                                f"   Content length: {len(str(content))} chars"
                                            )
                                    elif isinstance(file_obj, list):
                                        total_length = sum(
                                            len(line) for line in file_obj
                                        )
                                        logger.info(
                                            f"   Content: {len(file_obj)} lines, {total_length} chars total"
                                        )
                                    else:
                                        logger.info(
                                            f"   Content length: {len(str(file_obj))} chars"
                                        )

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

                    logger.info("✅ Messages saved to database")
                except Exception as e:
                    logger.error(f"Failed to save messages: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

                # Send completion
                await websocket.send_text(
                    json.dumps({"type": "done", "data": {}, "timestamp": time.time()})
                )

                logger.info(
                    "✅ [ASSISTANT AGENT COMPLETE] Query processed successfully"
                )

            except asyncio.TimeoutError:
                logger.warning(f"WebSocket timeout after {timeout}s of inactivity")
                await websocket.close(code=1000, reason="Timeout")
                break

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client")
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
                logger.error(f"Error processing query: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
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
        logger.error(f"Fatal WebSocket error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("Assistant Agent WebSocket connection closed")
