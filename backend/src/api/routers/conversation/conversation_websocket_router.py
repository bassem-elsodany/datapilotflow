"""
Conversation WebSocket Router - Real-time Communication

This module contains all WebSocket endpoints for real-time conversation communication
including chat and knowledge search functionality.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Query
from pydantic import BaseModel
from loguru import logger
import traceback
import json
import asyncio


from src.api.routers.auth.auth_router import get_current_user, validate_jwt_token, decode_access_token
from src.domain.user import User
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.application.data.llm.llm_responder import generate_ai_response_streaming, generate_context_aware_response_streaming
from src.services.conversation.conversation_history_service import conversation_history_service
from src.config import settings

# Create router
router = APIRouter(tags=["Conversations Search WebSocket"])

# Define metadata_fields for reuse
metadata_fields = [
    "page_content", "title", "knowledge_source", "chunk_id",
    "entities", "relationships", "tags", "source_url", "original_filename"
]


def get_milvus_client():
    """Helper function to create MilvusClientWrapper with proper error handling."""
    try:
        return MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory"
        )
    except Exception as e:
        logger.error(f"Failed to create Milvus client: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=503,
            detail="Vector database connection failed"
        )


def process_search_results(results, retrieval_method):
    """Helper function to process and format search results consistently."""
    results_out = []
    
    for i, result in enumerate(results):
        # Support both object-with-properties and dict
        if hasattr(result, "properties"):
            props = result.properties
        elif isinstance(result, dict):
            # Handle nested structure: result -> properties -> actual fields
            if "properties" in result:
                props = result["properties"]
            else:
                props = result
        else:
            props = {}
        
        metadata = {
            "chunk_id": props.get("chunk_id"),
            "source_url": props.get("source_url"),
            "knowledge_source": props.get("knowledge_source"),
            "title": props.get("title"),
            "original_filename": props.get("original_filename"),
            "entities": props.get("entities", []),
            "relationships": props.get("relationships", []),
            "tags": props.get("tags", []),
            "retrieval_method": retrieval_method
        }
        
        # Try multiple possible content fields
        content = props.get("page_content") or props.get("content") or props.get("text") or ""
        
        results_out.append({
            'text': content,
            'metadata': metadata
        })
    
    return results_out



@router.websocket("/ws/conversations/{conversation_id}/search")
async def ws_knowledge_search(websocket: WebSocket, conversation_id: str, token: str = Query(None)):
    """
    Interactive WebSocket endpoint for real-time knowledge search with streaming results.
    Requires valid JWT token for authentication.
    """
    logger.info(f"Knowledge search websocket connection requested")
    # Validate JWT token
    timeout = settings.WEBSOCKET_TIMEOUT
    try:
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        # Decode and validate token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token payload")
            return
            
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    await websocket.accept()
    logger.info(f"WebSocket connection established for user: {user_id} with timeout: {timeout}")
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
                msg = json.loads(data)
                query = msg.get("query")
                use_llm = msg.get("use_llm", True)
                custom_k = msg.get("k", settings.RAG_TOP_K)
                custom_alpha = msg.get("alpha", settings.RAG_SIMILARITY_THRESHOLD)
                session_id = msg.get("session_id")  # Add session_id support
                create_new_session = msg.get("create_new_session", False)  # Add create_new_session support
                if not query or not query.strip():
                    try:
                        await websocket.send_text(json.dumps({"error": "Query is required"}))
                    except WebSocketDisconnect:
                        logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return
                    continue
                
                # Handle session management
                if not session_id:
                    if create_new_session:
                        # Generate a session name based on the query
                        session_name = f"Search: {query[:30]}{'...' if len(query) > 30 else ''}"
                        session_id = conversation_history_service.create_conversation(user_id, session_name)
                        logger.info(f"Created new conversation session: {session_id} with name: {session_name}")
                    else:
                        # Get most recent session for user
                        sessions = conversation_history_service.get_user_conversations(user_id, limit=1)
                        session_id = sessions[0].id if sessions else None
                        if not session_id:
                            session_name = f"Search: {query[:30]}{'...' if len(query) > 30 else ''}"
                            session_id = conversation_history_service.create_conversation(user_id, session_name)
                            logger.info(f"Created new conversation session: {session_id} with name: {session_name}")
                
                logger.info(f"Using session_id: {session_id} for user: {user_id}")
                # Send initial status
                try:
                    await websocket.send_text(json.dumps({
                        "stage": "starting",
                        "message": f"Starting search for: {query}"
                    }))
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return
                # Get Weaviate client with proper cleanup
                milvus_client = None
                try:
                    milvus_client = get_milvus_client() 
                except Exception as e:
                    logger.error(f"Failed to create Milvus client: {e}")
                    try:
                        await websocket.send_text(json.dumps({
                            "stage": "error",
                            "error": "Vector Database connection failed"
                        }))
                    except WebSocketDisconnect:
                        return
                    return
                
                # Get conversation context if session_id is provided
                conversation_context = ""
                if session_id:
                    conversation_context = conversation_history_service.get_conversation_context(session_id)
                    logger.info(f"Retrieved conversation context for session: {session_id}")
                
                # Send searching status
                try:
                    await websocket.send_text(json.dumps({
                        "stage": "searching",
                        "message": "Searching knowledge base..."
                    }))
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return
                # Perform search based on mode
                k = custom_k
                alpha = custom_alpha
                raw_results = milvus_client.search_hybrid(
                    query=query,
                    limit=k,
                    alpha=alpha,
                    fusion_type="relative_score",
                    return_metadata=metadata_fields
                )
                results_out = process_search_results(raw_results, "weaviate_hybrid")

                # Filter by similarity score
                filtered_results = []
                for i, raw in enumerate(raw_results):
                    score = None
                    if isinstance(raw, dict):
                        score = raw.get("metadata", {}).get("score")
                    elif hasattr(raw, "metadata"):
                        score = getattr(raw.metadata, "score", None)
                    if score is not None and score >= settings.RAG_SIMILARITY_THRESHOLD:
                        filtered_results.append(results_out[i])
                
                # Send raw results immediately
                try:
                    await websocket.send_text(json.dumps({
                        "stage": "raw_results",
                        "results": filtered_results,
                        "count": len(filtered_results),
                        "query": query,
                        "search_params": {
                            "k": k,
                            "alpha": alpha,
                            "fusion_type": "relative_score"
                        }
                    }))
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return
                # Note: Individual result streaming removed for better performance
                # Raw results are already sent above, and LLM streaming provides real-time feedback
                # If LLM synthesis is requested
                if use_llm:
                    try:
                        await websocket.send_text(json.dumps({
                            "stage": "llm_synthesis",
                            "message": "Generating AI response..."
                        }))
                    except WebSocketDisconnect:
                        logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return
                    
                    # Stream the AI response chunks with buffering
                    full_response = ""
                    chunk_count = 0
                    buffer = ""
                    buffer_size = 50  # Send chunks every 100 characters (configurable)
                    
                    try:
                        logger.info(f"Starting to stream AI response for query: {query[:50]}...")
                        # Use context-aware response generation if session_id is provided
                        if session_id and conversation_context:
                            logger.info(f"Using context-aware response generation for session: {session_id}")
                            async for chunk in generate_context_aware_response_streaming(
                                query, filtered_results, session_id, user_id
                            ):
                                if chunk:
                                    full_response += chunk
                                    buffer += chunk
                                    chunk_count += 1
                                    
                                    # Send buffered chunks when buffer is full
                                    if len(buffer) >= buffer_size:
                                        try:
                                            await websocket.send_text(json.dumps({
                                                "stage": "llm_response_chunk",
                                                "chunk": buffer,
                                                "chunk_index": chunk_count,
                                                "partial_response": full_response
                                            }))
                                            buffer = ""  # Reset buffer
                                        except WebSocketDisconnect:
                                            logger.info(f"WebSocket disconnected for user: {user_id} (during streaming)")
                                            logger.error(f"Traceback: {traceback.format_exc()}")
                                            return
                        else:
                            # Use regular response generation
                            async for chunk in generate_ai_response_streaming(query, filtered_results):
                                if chunk:
                                    full_response += chunk
                                    buffer += chunk
                                    chunk_count += 1
                                    
                                    # Send buffered chunks when buffer is full
                                    if len(buffer) >= buffer_size:
                                        try:
                                            await websocket.send_text(json.dumps({
                                                "stage": "llm_response_chunk",
                                                "chunk": buffer,
                                                "chunk_index": chunk_count,
                                                "partial_response": full_response
                                            }))
                                            buffer = ""  # Reset buffer
                                        except WebSocketDisconnect:
                                            logger.info(f"WebSocket disconnected for user: {user_id} (during streaming)")
                                            logger.error(f"Traceback: {traceback.format_exc()}")
                                            return
                        
                        # Send any remaining buffer content
                        if buffer:
                            try:
                                await websocket.send_text(json.dumps({
                                    "stage": "llm_response_chunk",
                                    "chunk": buffer,
                                    "chunk_index": chunk_count,
                                    "partial_response": full_response
                                }))
                            except WebSocketDisconnect:
                                logger.info(f"WebSocket disconnected for user: {user_id} (during final buffer send)")
                                logger.error(f"Traceback: {traceback.format_exc()}")
                                return
                        
                        logger.info(f"Completed streaming {chunk_count} chunks for query: {query[:50]}...")
                        
                        # DEBUG: Log the final response
                        logger.info(f"DEBUG - Final response length: {len(full_response)}")
                        logger.info(f"DEBUG - Final response preview: {repr(full_response[:200])}")
                        
                        # Send final complete response
                        try:
                            await websocket.send_text(json.dumps({
                                "stage": "llm_response_complete",
                                "response": full_response,
                                "total_chunks": chunk_count
                            }))
                        except WebSocketDisconnect:
                            logger.info(f"WebSocket disconnected for user: {user_id} (during final response)")
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            return
                            
                    except Exception as e:
                        logger.error(f"Error during streaming response: {e}")
                        try:
                            await websocket.send_text(json.dumps({
                                "stage": "llm_response_error",
                                "error": f"Failed to generate response: {str(e)}"
                            }))
                        except WebSocketDisconnect:
                            return
                # Save conversation history if session_id is provided
                if session_id and user_id:
                    try:
                        from datetime import datetime
                        from skillpilot.application.services.conversation.conversation_history_service import ConversationMessage
                        
                        # Collect source URLs for reference
                        source_urls = []
                        for result in filtered_results:
                            metadata = result.get('metadata', {})
                            source_url = metadata.get('source_url', '')
                            if source_url:
                                source_urls.append(source_url)
                        
                        # Add user message
                        user_message = ConversationMessage(
                            role="user",
                            content=query,
                            timestamp=datetime.utcnow(),
                            search_query=query,
                            source_urls=source_urls
                        )
                        conversation_history_service.add_message(session_id, user_message)
                        
                        # Add assistant message if LLM was used
                        if use_llm and full_response:
                            assistant_message = ConversationMessage(
                                role="assistant",
                                content=full_response,
                                timestamp=datetime.utcnow(),
                                search_query=query,
                                search_results=filtered_results,
                                source_urls=source_urls
                            )
                            conversation_history_service.add_message(session_id, assistant_message)
                        elif not use_llm:
                            # Add assistant message with raw results
                            assistant_message = ConversationMessage(
                                role="assistant",
                                content=f"Raw search results returned ({len(filtered_results)} results)",
                                timestamp=datetime.utcnow(),
                                search_query=query,
                                search_results=filtered_results,
                                source_urls=source_urls
                            )
                            conversation_history_service.add_message(session_id, assistant_message)
                        
                        logger.info(f"Saved conversation history for session: {session_id}")
                    except Exception as e:
                        logger.error(f"Error saving conversation history: {e}")
                
                # Send completion status with enhanced summary
                completion_data = {
                    "stage": "completed",
                    "message": "Search completed successfully",
                    "results": filtered_results,  # <-- Added for UI compatibility
                    "raw_results": filtered_results,  # <-- Added for UI compatibility
                    "session_id": session_id,  # <-- Added session_id to completion data
                    "summary": {
                        "total_results": len(filtered_results),
                        "query": query,
                        "search_time": "completed",
                        "has_content": any(result.get('text', '').strip() for result in filtered_results),
                        "content_count": sum(1 for result in filtered_results if result.get('text', '').strip()),
                        "empty_count": sum(1 for result in filtered_results if not result.get('text', '').strip())
                    }
                }
                if use_llm:
                    completion_data["summary"]["llm_synthesis"] = True
                    completion_data["summary"]["ai_response"] = full_response
                    completion_data["response"] = full_response  # <-- Added for UI compatibility
                else:
                    # Ensure response field exists even when not using LLM
                    completion_data["response"] = ""
                    completion_data["summary"]["llm_synthesis"] = False
                try:
                    await websocket.send_text(json.dumps(completion_data))
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user: {user_id} (during send)")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return
                finally:
                    # Cleanup Weaviate client
                    if milvus_client and hasattr(milvus_client, 'close'):
                        try:
                            milvus_client.close()
                        except Exception as e:
                            logger.warning(f"Error closing Weaviate client: {e}")
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user: {user_id}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return
            except asyncio.TimeoutError:
                logger.info(f"WebSocket timeout for user: {user_id}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                await websocket.close(code=1000, reason="Connection timeout")
                return
            except Exception as e:
                logger.error(f"WebSocket search error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    await websocket.send_text(json.dumps({
                        "stage": "error",
                        "error": f"Search failed: {str(e)}"
                    }))
                except Exception:
                    return
    except asyncio.TimeoutError:
        logger.info(f"WebSocket timeout for user: {user_id}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await websocket.close(code=1000, reason="Connection timeout")
        return
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
        return
