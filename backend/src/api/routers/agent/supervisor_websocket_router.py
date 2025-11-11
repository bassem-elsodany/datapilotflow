"""
Supervisor WebSocket Router - Multi-Agent Tool Calling Pattern

This module provides WebSocket endpoints for real-time multi-agent interactions
using the official LangChain Tool Calling Pattern with RAG agent as a tool.
"""

import asyncio
import json
import time
import traceback

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from src.agents.assistant_agent.services.generate_response_supervisor import (
    get_response_stream_supervisor,
)
from src.api.routers.auth.auth_router import decode_access_token
from src.config import settings
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

router = APIRouter(tags=["Supervisor WebSocket"])


def extract_conversation_config(conversation) -> dict:
    """
    Extract configuration from conversation object with new nested structure.

    Args:
        conversation: ConversationSession object with nested configuration

    Returns:
        Dictionary with extracted configuration values
    """
    config = {
        "llm_provider_id": None,
        "llm_model_name": None,
        "selected_strategy": "native",
        "collection_name": None,
        "enhancement_config": {},
        "enable_reranking": False,
        "relevance_threshold": 0.6,
        "enable_llm_generation": False,
        "top_k": 10,
        "conversation_description": None,
        "reranker_model_name": None,
    }

    if not conversation:
        return config

    # Load answer generation settings (LLM provider and model)
    if conversation.answer_generation and conversation.answer_generation.provider:
        config["llm_provider_id"] = conversation.answer_generation.provider.id
        config["llm_model_name"] = conversation.answer_generation.provider.model_name
        config["enable_llm_generation"] = True

    # Load vector database settings
    if conversation.vector_database:
        config["collection_name"] = conversation.vector_database.collection_name
        config["top_k"] = conversation.vector_database.top_k

    # Load enhancement strategy and provider
    if conversation.enhancement:
        config["selected_strategy"] = conversation.enhancement.strategy

        # For non-native strategies, the provider is required and stored in enhancement.provider
        # If answer_generation doesn't have a provider, use enhancement.provider as fallback
        if (
            conversation.enhancement.strategy != "native"
            and conversation.enhancement.provider
            and not config["llm_provider_id"]
        ):
            config["llm_provider_id"] = conversation.enhancement.provider.id
            config["llm_model_name"] = conversation.enhancement.provider.model_name
            logger.debug(
                f"Using enhancement provider for non-native strategy: {config['llm_provider_id']}/{config['llm_model_name']}"
            )

    # Load reranking settings
    if conversation.reranker and conversation.reranker.provider:
        config["enable_reranking"] = True
        config["relevance_threshold"] = conversation.reranker.relevance_threshold
        config["reranker_model_name"] = conversation.reranker.provider.model_name

    # Load conversation description for query enhancement context
    if conversation.description:
        config["conversation_description"] = conversation.description

    return config


@router.websocket("/ws/agent/query/supervisor")
async def agent_query_supervisor_websocket(
    websocket: WebSocket, token: str = Query(None)
):
    """
    WebSocket endpoint for AI agent query processing with TOOL CALLING PATTERN.

    This endpoint processes user queries through the multi-agent architecture using
    the official LangChain Tool Calling Pattern. The RAG agent is wrapped as a tool
    that the main ReAct agent invokes along with other task tools.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database"
    }
    ```

    **Response Format** (to client - supervisor events):
    ```json
    {
        "type": "supervisor_progress",
        "stage": "supervisor_init|rag_agent_executing|task_agent_executing|response_generation|completed",
        "message": "Status message",
        "data": {},
        "timestamp": "ISO timestamp"
    }
    ```

    **Architecture**:
    - Main ReAct Agent (create_agent from langchain.agents)
    - Tools: retrieve_knowledge (RAG), task_planner, code_explainer, calculator, text_analyzer, etc.
    - Reference: https://docs.langchain.com/oss/python/langchain/multi-agent
    """
    logger.info("=" * 80)
    logger.info("ASSISTANT AGENT ENDPOINT INVOKED | /ws/agent/query/supervisor")
    logger.info("=" * 80)

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

    await websocket.accept()
    logger.info(
        f"Supervisor WebSocket connected for user: {user_id} with timeout: {timeout}"
    )

    try:
        while True:
            try:
                # Wait for message from client with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                msg = json.loads(data)

                # Extract ONLY query and conversation_id from UI
                query = msg.get("query")
                conversation_id = msg.get("conversation_id") or msg.get("session_id")

                # Log the incoming query
                logger.info(
                    f"📨 [SUPERVISOR QUERY RECEIVED] Query: {query[:100]}{'...' if len(query) > 100 else ''} | Conversation ID: {conversation_id}"
                )

                # Initialize defaults
                llm_provider_id = None
                llm_model_name = None
                collection_name = None
                enable_reranking = True
                enable_llm_generation = True
                top_k = 5
                conversation_description = None
                # Note: selected_strategy, enhancement_config, retrieval_strategy removed
                # Supervisor ALWAYS uses 'custom_variants' (hardcoded in generate_response_supervisor)

                # Load ALL settings from conversation (UI should NOT send these)
                if conversation_id:
                    try:
                        logger.debug(
                            f"Loading ALL conversation settings from conversation_id: {conversation_id}"
                        )
                        conversation = conversation_history_service.get_conversation(
                            conversation_id
                        )
                        if conversation:
                            logger.debug(f"Conversation found: {conversation.name}")

                            # Load ALL settings from conversation using helper function
                            config = extract_conversation_config(conversation)
                            llm_provider_id = config["llm_provider_id"]
                            llm_model_name = config["llm_model_name"]
                            # selected_strategy - ignored (supervisor always uses custom_variants)
                            collection_name = config["collection_name"]
                            # enhancement_config - ignored (custom_variants has no LLM enhancement)
                            enable_reranking = config["enable_reranking"]
                            relevance_threshold = config["relevance_threshold"]
                            enable_llm_generation = config["enable_llm_generation"]
                            top_k = config["top_k"]
                            conversation_description = config[
                                "conversation_description"
                            ]
                            reranker_model_name = config["reranker_model_name"]
                            # retrieval_strategy - auto-determined by RAG based on variant count

                            if conversation_description:
                                logger.debug(
                                    f"Loaded conversation description: '{conversation_description[:50]}...'"
                                )

                            # Note: Removed strategy={selected_strategy} since supervisor always uses 'custom_variants'
                            logger.info(
                                f"Loaded ALL settings from conversation: provider={llm_provider_id}, model={llm_model_name}, collection={collection_name}, reranking={enable_reranking}, llm_generation={enable_llm_generation}, top_k={top_k}"
                            )
                        else:
                            error_msg = f"Conversation not found: {conversation_id}"
                            logger.error(f"{error_msg}")
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "stage": "error",
                                        "message": "Conversation not found. Please refresh and try again.",
                                        "timestamp": time.time(),
                                    }
                                )
                            )
                            continue
                    except Exception as e:
                        error_msg = f"Failed to load conversation settings: {str(e)}"
                        logger.error(f"{error_msg}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "stage": "error",
                                    "message": error_msg,
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                # Validate required fields
                if not query:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "stage": "error",
                                "message": "Query is required",
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                if not all(
                    [llm_provider_id, llm_model_name, collection_name, conversation_id]
                ):
                    missing = []
                    if not llm_provider_id:
                        missing.append("llm_provider_id")
                    if not llm_model_name:
                        missing.append("llm_model_name")
                    if not collection_name:
                        missing.append("collection_name")
                    if not conversation_id:
                        missing.append("conversation_id")

                    error_msg = f"Missing required fields: {', '.join(missing)}"
                    logger.error(f"{error_msg}")
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "stage": "error",
                                "message": error_msg,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # Send initial status event
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "workflow_started",
                            "stage": "starting",
                            "message": "Starting multi-agent workflow (Tool Calling Pattern)",
                            "timestamp": time.time(),
                        }
                    )
                )

                logger.info(
                    f"🚀 Processing supervisor query: '{query[:50]}...' (supervisor always uses custom_variants strategy)"
                )

                # Configure agent names (following LangChain multi-agent best practices)
                # https://docs.langchain.com/oss/python/langchain/multi-agent#tool-calling
                rag_agent_name = "knowledge_expert"
                rag_agent_description = None

                # Customize RAG agent description based on knowledge base
                if conversation_description:
                    rag_agent_description = (
                        f"Expert in {conversation_description}. "
                        "Retrieves and ranks relevant documents from the knowledge base. "
                        "This is the PRIMARY SOURCE OF TRUTH for accurate information. "
                        "ALWAYS call this tool FIRST to ground your response in factual knowledge."
                    )

                logger.debug(f"RAG agent configured: name={rag_agent_name}")

                # Call Supervisor-specific function (Tool Calling Pattern)
                # Note: selected_strategy, retrieval_strategy, enhancement_config removed
                # Supervisor always uses custom_variants (no LLM enhancement needed)
                stream = get_response_stream_supervisor(
                    query=query,
                    user_id=user_id,
                    llm_provider_id=llm_provider_id,
                    llm_model_name=llm_model_name,
                    conversation_id=conversation_id,
                    collection_name=collection_name,
                    enable_reranking=enable_reranking,
                    relevance_threshold=relevance_threshold,
                    enable_llm_generation=enable_llm_generation,
                    top_k=top_k,
                    conversation_description=conversation_description,
                    rag_agent_name=rag_agent_name,
                    rag_agent_description=rag_agent_description,
                )

                # Stream events to WebSocket with error tracking
                response_started = False
                try:
                    async for chunk in stream:
                        chunk_type = chunk.get("type")
                        logger.debug(
                            f"Forwarding Supervisor event: type={chunk_type}, stage={chunk.get('stage')}"
                        )
                        logger.debug(f"Full event payload: {json.dumps(chunk)}")

                        # Track if we've started sending response content
                        if chunk_type in ["streaming_response", "supervisor_error"]:
                            response_started = True

                        if chunk_type in [
                            "supervisor_progress",
                            "supervisor_started",
                            "workflow_complete",
                            "workflow_started",
                            "streaming_response",
                            "supervisor_error",
                        ]:
                            try:
                                await websocket.send_text(json.dumps(chunk))
                                logger.debug(f"Supervisor event sent to client successfully")
                            except Exception as send_error:
                                # Client connection lost while sending response
                                if response_started:
                                    # Response was partially sent
                                    logger.warning(
                                        f"WebSocket send error after response started: {send_error}"
                                    )
                                else:
                                    logger.error(
                                        f"WebSocket send error during initialization: {send_error}"
                                    )
                                raise
                        else:
                            logger.warning(
                                f"Skipping unexpected Supervisor event type: {chunk_type}"
                            )

                    logger.debug(
                        "Supervisor query processing completed successfully, waiting for next query"
                    )

                except Exception as stream_error:
                    # Stream processing error - client may have disconnected
                    if response_started:
                        logger.warning(
                            f"Stream error after response started (client may have disconnected): {stream_error}"
                        )
                    else:
                        logger.error(
                            f"Stream processing error (no response sent yet): {stream_error}"
                        )
                    # Continue to next query rather than closing connection
                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "stage": "error",
                                    "message": "Error processing request. Ready for next query.",
                                    "timestamp": time.time(),
                                }
                            )
                        )
                    except Exception:
                        # Cannot send to closed connection
                        logger.debug("Cannot send error to closed WebSocket connection")
                    continue

            except WebSocketDisconnect:
                logger.debug(f"WebSocket disconnected by client")
                return
            except asyncio.TimeoutError:
                logger.debug(
                    f"WebSocket receive timeout after {timeout}s - closing connection"
                )
                await websocket.close(code=1000, reason="Connection idle timeout")
                return
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "stage": "error",
                                "message": "Invalid JSON format",
                                "timestamp": time.time(),
                            }
                        )
                    )
                except Exception as send_error:
                    logger.debug(
                        f"Could not send error message to client (connection may be closed): {send_error}"
                    )
            except Exception as e:
                logger.error(f"Error processing Supervisor message: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "stage": "error",
                                "message": f"Error processing request: {str(e)}",
                                "timestamp": time.time(),
                            }
                        )
                    )
                except Exception as send_error:
                    logger.debug(
                        f"Could not send error message to client (connection may be closed): {send_error}"
                    )

    except WebSocketDisconnect:
        logger.debug(f"Supervisor WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"Supervisor WebSocket error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
