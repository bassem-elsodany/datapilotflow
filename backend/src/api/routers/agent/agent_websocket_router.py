"""
Agent WebSocket Router - LangGraph Workflow Interface

This module provides WebSocket endpoints for real-time AI agent interactions
using the LangGraph workflow with query enhancement capabilities.
"""

import asyncio
import json
import time
import traceback
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger
from opik.integrations.langchain import OpikTracer

from src.api.routers.auth.auth_router import decode_access_token
from src.config import settings
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from src.services.conversation.generate_response_rag import get_response_stream_rag
from src.services.conversation.generate_response_supervisor import (
    get_response_stream_supervisor,
)
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Workflow logic split into:
# - generate_response_rag: RAG-only pipeline execution
# - generate_response_supervisor: Supervisor Agent orchestration with intent routing

router = APIRouter(tags=["Agent WebSocket"])


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
        "relevance_threshold": 0.5,
        "enable_llm_generation": False,
        "top_k": 5,
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
        if (conversation.enhancement.strategy != "native" 
            and conversation.enhancement.provider 
            and not config["llm_provider_id"]):
            config["llm_provider_id"] = conversation.enhancement.provider.id
            config["llm_model_name"] = conversation.enhancement.provider.model_name
            logger.debug(f"Using enhancement provider for non-native strategy: {config['llm_provider_id']}/{config['llm_model_name']}")

    # Load reranking settings
    if conversation.reranker and conversation.reranker.provider:
        config["enable_reranking"] = True
        config["relevance_threshold"] = conversation.reranker.relevance_threshold
        config["reranker_model_name"] = conversation.reranker.provider.model_name

    # Load conversation description for query enhancement context
    if conversation.description:
        config["conversation_description"] = conversation.description

    return config


def extract_enhanced_query_text(enhanced_query_dict: dict, strategy: str = None) -> str:
    """
    Extract the actual enhanced query text from the enhanced_query dictionary.

    Args:
        enhanced_query_dict: Dictionary containing enhanced query data
        strategy: The enhancement strategy used

    Returns:
        The enhanced query as a string
    """
    if not enhanced_query_dict:
        return None

    logger.debug(
        f"📝 Extracting enhanced query text from dict keys: {list(enhanced_query_dict.keys())}, strategy: {strategy}"
    )

    # Try to extract based on known keys
    if "hypothetical_answer" in enhanced_query_dict:
        result = enhanced_query_dict["hypothetical_answer"]
        logger.debug(
            f"✅ Extracted hypothetical_answer: {result[:100] if result else None}..."
        )
        return result
    elif "multi_query_variants" in enhanced_query_dict:
        variants = enhanced_query_dict["multi_query_variants"]
        result = variants[0] if variants and len(variants) > 0 else None
        logger.debug(
            f"✅ Extracted multi_query_variants[0]: {result[:100] if result else None}..."
        )
        return result
    elif "augmented_queries" in enhanced_query_dict:
        augmented = enhanced_query_dict["augmented_queries"]
        # Return first variant after original (index 1), or first if only one
        result = (
            augmented[1]
            if augmented and len(augmented) > 1
            else (augmented[0] if augmented else None)
        )
        logger.debug(
            f"✅ Extracted augmented_queries[1]: {result[:100] if result else None}..."
        )
        return result
    elif "sub_queries" in enhanced_query_dict:
        sub_queries = enhanced_query_dict["sub_queries"]
        result = sub_queries[0] if sub_queries and len(sub_queries) > 0 else None
        logger.debug(
            f"✅ Extracted sub_queries[0]: {result[:100] if result else None}..."
        )
        return result
    elif "fusion_perspectives" in enhanced_query_dict:
        perspectives = enhanced_query_dict["fusion_perspectives"]
        result = perspectives[0] if perspectives and len(perspectives) > 0 else None
        logger.debug(
            f"✅ Extracted fusion_perspectives[0]: {result[:100] if result else None}..."
        )
        return result

    logger.warning(
        f"⚠️ Could not extract enhanced query from dict: {enhanced_query_dict}"
    )
    return None


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
    logger.info("🚀 📚 RAG AGENT ENDPOINT INVOKED | /ws/agent/query/rag")
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
                logger.info(f"📨 [RAG QUERY RECEIVED] Query: {query[:100]}{'...' if len(query) > 100 else ''} | Conversation ID: {conversation_id}")

                # Initialize defaults
                llm_provider_id = None
                llm_model_name = None
                selected_strategy = None
                collection_name = None
                enhancement_config = {}
                enable_reranking = True
                enable_llm_generation = True
                top_k = 5
                conversation_description = None

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
                            selected_strategy = config["selected_strategy"]
                            collection_name = config["collection_name"]
                            enhancement_config = config["enhancement_config"]
                            enable_reranking = config["enable_reranking"]
                            relevance_threshold = config["relevance_threshold"]
                            enable_llm_generation = config["enable_llm_generation"]
                            top_k = config["top_k"]
                            conversation_description = config["conversation_description"]
                            reranker_model_name = config["reranker_model_name"]

                            # Retrieval strategy is auto-detected at runtime based on query variants
                            retrieval_strategy = None

                            if conversation_description:
                                logger.debug(
                                    f"📝 Loaded conversation description: '{conversation_description[:50]}...'"
                                )

                            logger.info(
                                f"📋 Loaded ALL settings from conversation: provider={llm_provider_id}, model={llm_model_name}, strategy={selected_strategy}, collection={collection_name}, reranking={enable_reranking}, llm_generation={enable_llm_generation}, top_k={top_k}"
                            )
                        else:
                            error_msg = f"Conversation not found: {conversation_id}"
                            logger.error(f"❌ {error_msg}")
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
                        logger.error(f"❌ {error_msg}")
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
                    logger.error(f"❌ {error_msg}")
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
                    f"🚀 Processing RAG query: '{query[:50]}...' with strategy={selected_strategy}"
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
                async for chunk in stream:
                    chunk_type = chunk.get("type")
                    chunk_stage = chunk.get("stage")
                    logger.debug(
                        f"📡 [RAG EVENT] Received from backend: type={chunk_type}, stage={chunk_stage}"
                    )
                    logger.debug(f"📡 [RAG EVENT DATA] {json.dumps(chunk)}")

                    if chunk_type in ["workflow_progress", "workflow_complete", "workflow_error", "streaming_response"]:
                        logger.debug(f"📡 [RAG SEND] Sending to client: type={chunk_type}, stage={chunk_stage}")
                        await websocket.send_text(json.dumps(chunk))
                        logger.debug(f"✅ [RAG SENT] Event sent to client")
                    else:
                        logger.warning(
                            f"⚠️ Skipping unexpected RAG event type: {chunk_type}"
                        )

                logger.info("✅ RAG query processing completed, waiting for next query...")

            except WebSocketDisconnect:
                logger.debug(f"📤 WebSocket disconnected by client")
                return
            except asyncio.TimeoutError:
                logger.debug(f"⏱️ WebSocket receive timeout after {timeout}s - closing connection")
                await websocket.close(code=1000, reason="Connection idle timeout")
                return
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON received")
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
                logger.error(f"❌ Error processing RAG message: {str(e)}")
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
                    logger.debug(f"Could not send error message to client (connection may be closed): {send_error}")

    except WebSocketDisconnect:
        logger.info(f"❌ RAG WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"❌ RAG WebSocket error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass


@router.websocket("/ws/agent/query/supervisor")
async def agent_query_supervisor_websocket(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for AI agent query processing with SUPERVISOR MODE.

    This endpoint processes user queries through the multi-agent supervisor architecture,
    with intent detection and routing to RAG and/or Task agents.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "conversation_id": "conversation_id_from_database",
        "llm_provider_id": "provider_id_from_database",
        "llm_model_name": "model-name",
        "collection_name": "LongTermMemory"
    }
    ```

    **Response Format** (to client - supervisor events):
    ```json
    {
        "type": "supervisor_progress",
        "stage": "supervisor_init|intent_detection|rag_agent_executing|task_agent_executing|response_generation|completed",
        "message": "Status message",
        "data": {},
        "timestamp": "ISO timestamp"
    }
    ```
    """
    logger.info("=" * 80)
    logger.info("🚀 ∞ ASSISTANT AGENT ENDPOINT INVOKED | /ws/agent/query/supervisor")
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
    logger.info(f"Supervisor WebSocket connected for user: {user_id} with timeout: {timeout}")

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
                logger.info(f"📨 [SUPERVISOR QUERY RECEIVED] Query: {query[:100]}{'...' if len(query) > 100 else ''} | Conversation ID: {conversation_id}")

                # Initialize defaults
                llm_provider_id = None
                llm_model_name = None
                selected_strategy = None
                collection_name = None
                enhancement_config = {}
                enable_reranking = True
                enable_llm_generation = True
                top_k = 5
                conversation_description = None

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
                            selected_strategy = config["selected_strategy"]
                            collection_name = config["collection_name"]
                            enhancement_config = config["enhancement_config"]
                            enable_reranking = config["enable_reranking"]
                            relevance_threshold = config["relevance_threshold"]
                            enable_llm_generation = config["enable_llm_generation"]
                            top_k = config["top_k"]
                            conversation_description = config["conversation_description"]
                            reranker_model_name = config["reranker_model_name"]

                            # Retrieval strategy is auto-detected at runtime based on query variants
                            retrieval_strategy = None

                            if conversation_description:
                                logger.debug(
                                    f"📝 Loaded conversation description: '{conversation_description[:50]}...'"
                                )

                            logger.info(
                                f"📋 Loaded ALL settings from conversation: provider={llm_provider_id}, model={llm_model_name}, strategy={selected_strategy}, collection={collection_name}, reranking={enable_reranking}, llm_generation={enable_llm_generation}, top_k={top_k}"
                            )
                        else:
                            error_msg = f"Conversation not found: {conversation_id}"
                            logger.error(f"❌ {error_msg}")
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
                        logger.error(f"❌ {error_msg}")
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
                    logger.error(f"❌ {error_msg}")
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
                            "message": "Starting supervisor workflow processing",
                            "timestamp": time.time(),
                        }
                    )
                )

                logger.info(
                    f"🚀 Processing supervisor query: '{query[:50]}...' with strategy={selected_strategy}"
                )

                # Call Supervisor-specific function
                stream = get_response_stream_supervisor(
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
                async for chunk in stream:
                    chunk_type = chunk.get("type")
                    logger.info(
                        f"📡 Forwarding Supervisor event: type={chunk_type}, stage={chunk.get('stage')}"
                    )
                    logger.debug(f"📡 Full event payload: {json.dumps(chunk)}")

                    if chunk_type in ["supervisor_progress", "supervisor_started", "workflow_complete", "workflow_started", "streaming_response", "supervisor_error"]:
                        await websocket.send_text(json.dumps(chunk))
                        logger.info(f"✅ Supervisor event sent to client successfully")
                    else:
                        logger.warning(
                            f"⚠️ Skipping unexpected Supervisor event type: {chunk_type}"
                        )

                logger.info("✅ Supervisor query processing completed, waiting for next query...")

            except WebSocketDisconnect:
                logger.debug(f"📤 WebSocket disconnected by client")
                return
            except asyncio.TimeoutError:
                logger.debug(f"⏱️ WebSocket receive timeout after {timeout}s - closing connection")
                await websocket.close(code=1000, reason="Connection idle timeout")
                return
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON received")
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
                    logger.debug(f"Could not send error message to client (connection may be closed): {send_error}")
            except Exception as e:
                logger.error(f"❌ Error processing Supervisor message: {str(e)}")
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
                    logger.debug(f"Could not send error message to client (connection may be closed): {send_error}")

    except WebSocketDisconnect:
        logger.info(f"❌ Supervisor WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"❌ Supervisor WebSocket error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass


