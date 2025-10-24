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
from src.services.conversation.generate_response import get_response
from src.services.model_provider.model_provider_service import (
    get_model_provider_service,
)

# Workflow logic moved to generate_response service

router = APIRouter(tags=["Agent WebSocket"])


@router.websocket("/ws/agent/query")
async def agent_query_websocket(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for AI agent query processing with LangGraph workflow.

    This endpoint processes user queries through the complete LangGraph workflow,
    including query enhancement, document retrieval, and response generation.

    **Authentication**: Requires JWT token

    **Message Format** (from client):
    ```json
    {
        "query": "User's question",
        "selected_strategy": "step_back|multi_query|hyde|decomposition|rag_fusion|query_fusion",
        "llm_provider_id": "provider_id_from_database",
        "llm_model_name": "model-name",
        "collection_name": "LongTermMemory",
        "enhancement_config": {
            "query_enhancement": {
                "enabled": true,
                "timeout_seconds": 30
            }
        }
    }
    ```

    **Response Format** (to client):
    ```json
    {
        "stage": "query_enhancement|document_retrieval|response_generation|completed|error",
        "message": "Status message",
        "data": {},
        "timestamp": "ISO timestamp"
    }
    ```

    **Stages**:
    1. `starting` - Connection established, processing initiated
    2. `query_enhancement` - Enhancing query using selected strategy
    3. `document_retrieval` - Retrieving relevant documents
    4. `response_generation` - Generating AI response
    5. `streaming_response` - Streaming AI response chunks
    6. `completed` - Processing completed successfully
    7. `error` - Error occurred during processing
    """
    logger.info("Agent query WebSocket connection requested")

    # Validate JWT token
    timeout = settings.WEBSOCKET_TIMEOUT

    try:
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Decode and validate token
        payload = decode_access_token(token)
        user_id = payload.get("user_id")  # Use user_id (ObjectId), not sub (username)
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
        f"Agent WebSocket connected for user: {user_id} with timeout: {timeout}"
    )

    try:
        while True:
            try:
                # Wait for message from client with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                msg = json.loads(data)

                # Extract required fields
                query = msg.get("query")
                selected_strategy = msg.get("selected_strategy")
                llm_provider_id = msg.get("llm_provider_id")
                llm_model_name = msg.get("llm_model_name")
                collection_name = msg.get("collection_name", "LongTermMemory")
                conversation_id = msg.get("conversation_id") or msg.get("session_id")
                enhancement_config = msg.get("enhancement_config", {})

                # If no provider ID provided but conversation_id exists, load from conversation
                if not llm_provider_id and conversation_id:
                    try:
                        logger.debug(
                            f"Loading conversation settings from conversation_id: {conversation_id}"
                        )
                        conversation = conversation_history_service.get_conversation(
                            conversation_id
                        )
                        if conversation:
                            logger.debug(f"Conversation found: {conversation.name}")
                            logger.debug(
                                f"Conversation user_id: {conversation.user_id}"
                            )
                            logger.debug(f"Current JWT user_id: {user_id}")
                            logger.debug(
                                f"Conversation llm_provider_id: {conversation.llm_provider_id}"
                            )

                            llm_provider_id = conversation.llm_provider_id
                            if not llm_model_name:
                                llm_model_name = conversation.llm_model_name
                            if (
                                not selected_strategy
                                and conversation.enhancement_config
                            ):
                                # EnhancementConfiguration is a dataclass, access as attribute
                                selected_strategy = (
                                    conversation.enhancement_config.strategy
                                )
                            if (
                                collection_name == "LongTermMemory"
                                and conversation.collection_name
                            ):
                                collection_name = conversation.collection_name
                            # Load reranking setting
                            enable_reranking = getattr(
                                conversation, "enable_reranking", True
                            )
                            logger.info(
                                f"📋 Loaded settings from conversation: provider={llm_provider_id}, model={llm_model_name}, strategy={selected_strategy}, collection={collection_name}, reranking={enable_reranking}"
                            )
                        else:
                            logger.warning(f"Conversation not found: {conversation_id}")
                    except Exception as e:
                        logger.warning(f"Failed to load conversation settings: {e}")
                        logger.warning(f"Traceback: {traceback.format_exc()}")

                # Validate required fields
                if not query or not query.strip():
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": "Query is required",
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                if not llm_provider_id:
                    error_msg = "LLM provider ID is required. Please configure a provider for this conversation."
                    logger.error(
                        f"❌ {error_msg} - conversation_id: {conversation_id}, user: {user_id}"
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": error_msg,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                logger.info(
                    f"Processing agent query: '{query[:50]}...' "
                    f"with strategy: {selected_strategy}, provider: {llm_provider_id}"
                )

                # Send initial status
                await websocket.send_text(
                    json.dumps(
                        {
                            "stage": "starting",
                            "message": f"Processing query: {query[:100]}...",
                            "data": {
                                "query": query,
                                "strategy": selected_strategy,
                                "provider_id": llm_provider_id,
                            },
                            "timestamp": time.time(),
                        }
                    )
                )

                # Resolve LLM provider configuration
                try:
                    provider_service = get_model_provider_service()
                    logger.debug(
                        f"Looking up provider ID: {llm_provider_id} for user: {user_id}"
                    )
                    provider = provider_service.get_model_provider(
                        llm_provider_id, user_id
                    )

                    if not provider:
                        error_msg = f"LLM provider not found: {llm_provider_id}"
                        logger.error(f"❌ {error_msg} for user: {user_id}")
                        logger.error(
                            f"This could mean: 1) Provider was deleted, 2) Provider belongs to different user, 3) Invalid provider ID"
                        )

                        # Try to get all providers for this user to help debug
                        try:
                            all_providers = provider_service.list_model_providers(
                                user_id
                            )
                            logger.error(
                                f"Available providers for user {user_id}: {[(p.id, p.name) for p in all_providers]}"
                            )
                        except Exception as debug_e:
                            logger.error(
                                f"Could not list available providers: {debug_e}"
                            )

                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "error",
                                    "message": error_msg,
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                    if not provider.is_active:
                        error_msg = f"LLM provider is not active: {provider.name}"
                        logger.error(
                            f"❌ {error_msg} - provider_id: {llm_provider_id}, user: {user_id}"
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "error",
                                    "message": error_msg,
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        continue

                    logger.info(
                        f"Using LLM provider: {provider.name} ({provider.provider_type})"
                    )

                    # Pass provider ID and model name to workflow
                    llm_provider_id = provider.id
                    llm_model_name = llm_model_name or provider.generative.default_model

                except Exception as e:
                    error_msg = f"Failed to configure LLM provider: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": error_msg,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    continue

                # Workflow state creation is now handled in get_response function

                # Execute LangGraph workflow
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "query_enhancement",
                                "message": (
                                    "Enhancing query..."
                                    if selected_strategy
                                    else "Skipping query enhancement..."
                                ),
                                "data": {"strategy": selected_strategy or "none"},
                                "timestamp": time.time(),
                            }
                        )
                    )

                    # Execute workflow using the generate_response service
                    result = await get_response(
                        query=query,
                        user_id=user_id,
                        llm_provider_id=llm_provider_id,
                        llm_model_name=llm_model_name,
                        conversation_id=conversation_id,
                        collection_name=collection_name,
                        selected_strategy=selected_strategy,
                        enhancement_config=enhancement_config,
                        enable_reranking=enable_reranking,
                    )

                    # Send query enhancement results
                    if result.get("enhanced_query"):
                        enhanced_query = result["enhanced_query"]
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "query_enhancement_complete",
                                    "message": f"Query enhanced using {selected_strategy or 'default'} strategy",
                                    "data": {
                                        "original_query": query,
                                        "enhanced_queries": enhanced_query.get(
                                            "queries", []
                                        ),
                                        "strategies_applied": result.get(
                                            "enhancement_strategies_applied", []
                                        ),
                                        "step_back_query": enhanced_query.get(
                                            "step_back_query"
                                        ),
                                        "hypothetical_answer": enhanced_query.get(
                                            "hypothetical_answer"
                                        ),
                                        "sub_queries": enhanced_query.get(
                                            "sub_queries", []
                                        ),
                                        "fusion_perspectives": enhanced_query.get(
                                            "fusion_perspectives", []
                                        ),
                                        "multi_query_variants": result.get(
                                            "multi_query_variants", []
                                        ),
                                    },
                                    "timestamp": time.time(),
                                }
                            )
                        )

                    # Send document retrieval status
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "document_retrieval",
                                "message": "Retrieving relevant documents...",
                                "timestamp": time.time(),
                            }
                        )
                    )

                    # Send retrieval results
                    documents = result.get("documents", [])
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "document_retrieval_complete",
                                "message": f"Retrieved {len(documents)} relevant documents",
                                "data": {
                                    "document_count": len(documents),
                                    "documents": documents[
                                        :5
                                    ],  # Send first 5 for preview
                                },
                                "timestamp": time.time(),
                            }
                        )
                    )

                    # Send response generation status
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "response_generation",
                                "message": "Generating AI response...",
                                "timestamp": time.time(),
                            }
                        )
                    )

                    # Get the final response
                    final_response = result.get("response", "")

                    # Stream response in chunks for better UX
                    chunk_size = 50  # Characters per chunk
                    for i in range(0, len(final_response), chunk_size):
                        chunk = final_response[i : i + chunk_size]
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "stage": "streaming_response",
                                    "message": "Streaming response...",
                                    "data": {
                                        "chunk": chunk,
                                        "chunk_index": i // chunk_size,
                                        "total_length": len(final_response),
                                    },
                                    "timestamp": time.time(),
                                }
                            )
                        )
                        # Small delay for smoother streaming
                        await asyncio.sleep(0.01)

                    # Send completion message
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "completed",
                                "message": "Query processing completed successfully",
                                "data": {
                                    "query": query,
                                    "response": final_response,
                                    "document_count": len(documents),
                                    "enhancement_strategy": selected_strategy,
                                    "strategies_applied": result.get(
                                        "enhancement_strategies_applied", []
                                    ),
                                    "query_info": result.get(
                                        "query_info"
                                    ),  # Add query comparison
                                    "workflow_metadata": {
                                        "steps_executed": result.get(
                                            "steps_executed", []
                                        ),
                                        "total_time_ms": result.get("total_time_ms", 0),
                                    },
                                },
                                "timestamp": time.time(),
                            }
                        )
                    )

                    logger.info(
                        f"✅ Agent query completed successfully for user {user_id}: "
                        f"'{query[:50]}...' -> {len(final_response)} chars"
                    )

                    # Save to conversation history if conversation_id provided
                    if conversation_id:
                        try:
                            from datetime import datetime

                            from src.services.conversation.conversation_history_service import (
                                ConversationMessage,
                            )

                            # Create user message
                            user_message = ConversationMessage(
                                role="user",
                                content=query,
                                timestamp=datetime.utcnow(),
                                search_query=query,
                            )

                            # Create assistant message
                            assistant_message = ConversationMessage(
                                role="assistant",
                                content=final_response,
                                timestamp=datetime.utcnow(),
                                enhancement_strategy_used=selected_strategy,
                                document_count=len(documents),
                            )

                            # Save messages
                            conversation_history_service.add_message(
                                conversation_id, user_message
                            )
                            conversation_history_service.add_message(
                                conversation_id, assistant_message
                            )

                            logger.info(
                                f"💾 Saved conversation messages to session: {conversation_id}"
                            )
                        except Exception as save_error:
                            logger.error(
                                f"Failed to save conversation history: {save_error}"
                            )
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            # Don't fail the whole request if history save fails

                except Exception as e:
                    logger.error(f"Error executing workflow: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": f"Workflow execution failed: {str(e)}",
                                "data": {
                                    "error_type": type(e).__name__,
                                    "error_details": str(e),
                                },
                                "timestamp": time.time(),
                            }
                        )
                    )

            except WebSocketDisconnect:
                logger.info(f"Agent WebSocket disconnected for user: {user_id}")
                return

            except asyncio.TimeoutError:
                logger.info(f"Agent WebSocket timeout for user: {user_id}")
                await websocket.close(code=1000, reason="Connection timeout")
                return

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "stage": "error",
                            "message": "Invalid JSON format",
                            "timestamp": time.time(),
                        }
                    )
                )

            except Exception as e:
                logger.error(f"Error processing agent query: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "stage": "error",
                                "message": f"Processing failed: {str(e)}",
                                "timestamp": time.time(),
                            }
                        )
                    )
                except Exception:
                    # Connection might be closed
                    return

    except asyncio.TimeoutError:
        logger.info(f"Agent WebSocket timeout for user: {user_id}")
        await websocket.close(code=1000, reason="Connection timeout")
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return

    except WebSocketDisconnect:
        logger.info(f"Agent WebSocket disconnected for user: {user_id}")
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return

    except Exception as e:
        logger.error(f"Agent WebSocket error for user {user_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
        if settings.AGENT_TRACING_ENABLED:
            logger.info("Flushing Opik tracer")
            opik_tracer = OpikTracer()
            opik_tracer.flush()
            logger.info("✅ Opik tracer flushed")
        else:
            logger.info("❌ Opik tracer not flushed")
        return
