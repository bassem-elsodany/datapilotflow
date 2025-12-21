"""
RAG WebSocket Router - Pure RAG Workflow Interface

This module provides WebSocket endpoints for real-time RAG-only interactions
using the LangGraph workflow with query enhancement capabilities.
"""

import asyncio
import json
import time
import traceback
from typing import List

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from datapilotflow.rag_agent.services.generate_response_rag import get_response_stream_rag
from datapilotflow.api.routers.auth.auth_router import decode_access_token
from datapilotflow.domain.config import settings
from datapilotflow.services.conversation.conversation_history_service import (
    conversation_history_service,
)

router = APIRouter(tags=["RAG WebSocket"])


def extract_agent_config(agent, conversation=None) -> dict:
    """
    Extract configuration from Agent object (new architecture).

    Args:
        agent: Agent object with configuration
        conversation: Optional ConversationSession for description

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

    if not agent:
        return config

    # Load primary LLM provider (used for enhancement, answer generation, etc.)
    if agent.llm_provider:
        config["llm_provider_id"] = agent.llm_provider.id
        config["llm_model_name"] = agent.llm_provider.model_name

    # Load answer generation settings
    # CRITICAL: Only enable LLM generation if user has explicitly enabled it
    config["enable_llm_generation"] = agent.is_llm_generation_enabled
    if agent.is_llm_generation_enabled:
        logger.info("✅ LLM generation ENABLED by user")
    else:
        logger.info("❌ LLM generation DISABLED by user - will return raw documents")

    # Load vector database settings
    if agent.vector_database:
        config["collection_name"] = agent.vector_database.collection_name
        config["top_k"] = agent.vector_database.top_k

    # Load enhancement strategy (uses primary llm_provider)
    config["selected_strategy"] = agent.enhancement_strategy or "native"

    # Load reranking settings
    # CRITICAL: Only enable reranking if user has explicitly enabled it
    if agent.reranker and agent.reranker.enabled and agent.reranker.provider:
        config["enable_reranking"] = True
        config["relevance_threshold"] = agent.reranker.relevance_threshold
        config["reranker_model_name"] = agent.reranker.provider.model_name
        logger.info("✅ Reranking ENABLED by user")
    else:
        logger.info("❌ Reranking DISABLED by user")

    # Load conversation description for query enhancement context
    if conversation and conversation.description:
        config["conversation_description"] = conversation.description
    elif agent.description:
        config["conversation_description"] = agent.description

    return config


@router.websocket("/ws/agent/query/rag")
async def agent_query_rag_websocket(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for RAG-only query processing (no supervisor/agent routing).

    This endpoint processes user queries using ONLY the RAG pipeline without any intent detection
    or task agent routing. It provides direct access to the knowledge base retrieval and answer
    generation pipeline.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database"
    }
    ```

    **Response Format** (to client - RAG events):
    ```json
    {
        "type": "workflow_progress",
        "stage": "query_enhancement|query_enhancement_complete|document_retrieval|document_retrieval_complete|document_judging|document_judging_complete|answer_generation|answer_generation_complete",
        "message": "Status message",
        "data": {},
        "execution_time_ms": 123.45
    }
    ```

    **Stages**:
    1. `query_enhancement` (START) - Beginning query enhancement
    2. `query_enhancement_complete` (COMPLETE) - Query enhanced with variants
    3. `document_retrieval` (START) - Beginning document retrieval
    4. `document_retrieval_complete` (COMPLETE) - Documents retrieved
    5. `document_judging` (START) - Beginning document ranking (if enabled)
    6. `document_judging_complete` (COMPLETE) - Documents ranked
    7. `answer_generation` (START) - Beginning answer generation
    8. `answer_generation_complete` (COMPLETE) - Response generated
    9. `workflow_complete` - Final result with complete response

    RAG-only mode is ideal for:
    - Pure knowledge base retrieval without task execution
    - Consistent, deterministic retrieval pipelines
    - Lower latency compared to supervisor with multiple agents
    """
    logger.info("=" * 80)
    logger.info("RAG AGENT ENDPOINT INVOKED | /ws/agent/query/rag")
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
    logger.info(f"RAG WebSocket connected for user: {user_id} with timeout: {timeout}")

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
                    f"[RAG QUERY RECEIVED] Query: {query[:100]}{'...' if len(query) > 100 else ''} | Conversation ID: {conversation_id}"
                )

                # Initialize defaults
                llm_provider_id = None
                llm_model_name = None
                selected_strategy = None
                collection_name: str = "LongTermMemory"  # Default collection
                enhancement_config = {}
                enable_reranking = False
                enable_llm_generation = False
                top_k = 5
                conversation_description = None
                relevance_threshold = 0.6
                retrieval_strategy = None
                reranker_model_name = None

                # Load ALL settings from agent (via conversation) - UI should NOT send these
                if conversation_id:
                    try:
                        logger.debug(
                            f"Loading conversation and agent settings for conversation_id: {conversation_id}"
                        )
                        conversation = conversation_history_service.get_conversation(
                            conversation_id
                        )
                        if conversation:
                            logger.debug(f"Conversation found: {conversation.name}")

                            # NEW ARCHITECTURE: Configuration is stored in Agent, not Conversation
                            agent = None
                            if conversation.agent_id:
                                logger.info(
                                    f"🔗 Conversation linked to agent {conversation.agent_id}"
                                )
                                from datapilotflow.services.agent.agent_service import (
                                    get_agent_service,
                                )

                                agent_service = get_agent_service()
                                agent = agent_service.get_agent(
                                    conversation.agent_id, user_id
                                )

                                if agent:
                                    logger.info(
                                        f"✅ Loaded agent '{agent.name}' configuration"
                                    )
                                else:
                                    logger.warning(
                                        f"⚠️ Agent {conversation.agent_id} not found"
                                    )

                            if not agent:
                                error_msg = f"Agent not found for conversation {conversation_id}"
                                logger.error(error_msg)
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "error",
                                            "stage": "error",
                                            "message": "Agent configuration not found. Please check the agent settings.",
                                            "timestamp": time.time(),
                                        }
                                    )
                                )
                                continue

                            # Load ALL settings from agent using helper function
                            config = extract_agent_config(agent, conversation)
                            llm_provider_id = config["llm_provider_id"]
                            llm_model_name = config["llm_model_name"]
                            selected_strategy = config["selected_strategy"]
                            collection_name = config["collection_name"]
                            enhancement_config = config["enhancement_config"]
                            enable_reranking = config["enable_reranking"]
                            relevance_threshold = config["relevance_threshold"]
                            enable_llm_generation = config["enable_llm_generation"]
                            top_k = config["top_k"]
                            conversation_description = config[
                                "conversation_description"
                            ]
                            reranker_model_name = config["reranker_model_name"]

                            # Retrieval strategy is auto-detected at runtime based on query variants
                            retrieval_strategy = None

                            if conversation_description:
                                logger.debug(
                                    f"Loaded conversation description: '{conversation_description[:50]}...'"
                                )

                            logger.info(
                                f"Loaded ALL settings from agent: provider={llm_provider_id}, model={llm_model_name}, strategy={selected_strategy}, collection={collection_name}, reranking={enable_reranking}, llm_generation={enable_llm_generation}, top_k={top_k}"
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

                # Always require a collection and conversation_id
                base_missing = []
                if not collection_name:
                    base_missing.append("collection_name")
                if not conversation_id:
                    base_missing.append("conversation_id")

                # Only require LLM provider/model when generation or reranking is enabled
                llm_missing: List[str] = []
                if enable_llm_generation or enable_reranking:
                    if not llm_provider_id:
                        llm_missing.append("llm_provider_id")
                    if not llm_model_name:
                        llm_missing.append("llm_model_name")

                missing = base_missing + llm_missing
                if missing:
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
                            "message": "Starting RAG workflow processing",
                            "timestamp": time.time(),
                        }
                    )
                )

                logger.info(
                    f"Processing RAG query: '{query[:50]}...' with strategy={selected_strategy}"
                )

                # Call RAG-specific function
                stream = get_response_stream_rag(
                    query=query,
                    user_id=user_id,
                    llm_provider_id=llm_provider_id,
                    llm_model_name=llm_model_name,
                    conversation_id=conversation_id,
                    collection_name=collection_name,
                    selected_strategy=selected_strategy,
                    retrieval_strategy=retrieval_strategy,
                    enhancement_config=enhancement_config,
                    enable_reranking=enable_reranking,
                    relevance_threshold=relevance_threshold,
                    enable_llm_generation=enable_llm_generation,
                    top_k=top_k,
                    conversation_description=conversation_description,
                )

                # Stream events to WebSocket
                # NOTE: Message saving is handled inside get_response_stream_rag()
                async for chunk in stream:
                    chunk_type = chunk.get("type")
                    chunk_stage = chunk.get("stage")

                    if chunk_type in [
                        "workflow_progress",
                        "workflow_complete",
                        "workflow_error",
                        "streaming_response",
                    ]:
                        await websocket.send_text(json.dumps(chunk))
                    else:
                        logger.warning(
                            f"Skipping unexpected RAG event type: {chunk_type}"
                        )

                logger.debug("RAG query processing completed, waiting for next query")

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
            except Exception as e:
                logger.error(f"Error processing RAG message: {str(e)}")
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
        logger.debug(f"RAG WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"RAG WebSocket error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
