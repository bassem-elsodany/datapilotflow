"""
Knowledge Management Router

This module contains endpoints for knowledge ingestion and search functionality.
Conversation management endpoints have been moved to the conversation router.
"""

from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect, status, Request, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import traceback
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import json
import asyncio
import os

from src.services.file_management.file_upload_service import handle_file_upload
from src.api.routers.auth.auth_router import get_current_user, decode_access_token, validate_jwt_token
from src.domain.user import User
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.application.data.llm.llm_responder import generate_ai_response_async, generate_ai_response_with_metadata_async, generate_ai_response_streaming, generate_context_aware_response, generate_context_aware_response_streaming, ContentAggregator
from src.services.conversation.conversation_history_service import conversation_history_service
from src.config import settings
from src.services.file_management.dao.rag_file_upload_service import RagFileUploadService

# Create router
router = APIRouter(prefix="/knowledge", tags=["Knowledge Management"])


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


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    use_llm: bool = Field(default=True, description="Whether to use LLM synthesis")


class ContextAwareSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    use_llm: bool = Field(default=True, description="Whether to use LLM synthesis")
    create_new_session: bool = Field(default=False, description="Create new session if none provided")


@router.post("/search", status_code=status.HTTP_200_OK)
async def search_knowledge(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Search knowledge base with optional LLM synthesis.
    """
    try:
        milvus_client = get_milvus_client()
        
        # Perform vector search
        search_results = milvus_client.search(
            query=search_query.query,
            limit=10
        )
        
        if not search_results:
            return {
                "success": True,
                "results": [],
                "synthesis": "No relevant information found in the knowledge base.",
                "search_query": search_query.query
            }
        
        # Process results
        processed_results = process_search_results(search_results, "vector_search")
        
        # Generate synthesis if requested
        synthesis = None
        if search_query.use_llm and processed_results:
            try:
                synthesis = await generate_ai_response_async(
                    query=search_query.query,
                    search_results=processed_results
                )
            except Exception as e:
                logger.warning(f"LLM synthesis failed: {e}")
                synthesis = "Unable to generate synthesis at this time."
        
        return {
            "success": True,
            "results": processed_results,
            "synthesis": synthesis,
            "search_query": search_query.query,
            "result_count": len(processed_results)
        }
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/context-aware", status_code=status.HTTP_200_OK)
async def context_aware_search(
    search_query: ContextAwareSearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Perform context-aware search with conversation history.
    """
    try:
        milvus_client = get_milvus_client()
        
        # Get conversation context
        conversation_context = conversation_history_service.get_recent_context(
            user_id=current_user.username,
            limit=5
        )
        
        # Perform enhanced search with context
        search_results = milvus_client.search(
            query=search_query.query,
            limit=15,
            additional_context=conversation_context
        )
        
        if not search_results:
            return {
                "success": True,
                "results": [],
                "synthesis": "No relevant information found in the knowledge base.",
                "search_query": search_query.query,
                "context_used": bool(conversation_context)
            }
        
        # Process results
        processed_results = process_search_results(search_results, "context_aware_search")
        
        # Generate context-aware synthesis
        synthesis = None
        if search_query.use_llm and processed_results:
            try:
                synthesis = await generate_context_aware_response(
                    query=search_query.query,
                    search_results=processed_results,
                    conversation_context=conversation_context
                )
            except Exception as e:
                logger.warning(f"Context-aware synthesis failed: {e}")
                synthesis = "Unable to generate context-aware synthesis at this time."
        
        return {
            "success": True,
            "results": processed_results,
            "synthesis": synthesis,
            "search_query": search_query.query,
            "context_used": bool(conversation_context),
            "result_count": len(processed_results)
        }
        
    except Exception as e:
        logger.error(f"Context-aware search error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# KNOWLEDGE INGESTION ENDPOINTS
# ============================================================================


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_knowledge_file(
    file: UploadFile = File(...),
    user_id: str = Form(None),
    description: str = Form(""),
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a knowledge file into the vector database.
    """
    try:
        # Use current user ID if not provided
        if not user_id:
            user_id = current_user.username
        
        # Handle file upload and processing
        result = await handle_file_upload(
            file=file,
            user_id=user_id,
            description=description
        )
        
        return {
            "success": True,
            "file_id": result.get("file_id"),
            "message": "File uploaded and processing started",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Knowledge ingestion error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ingest/{file_id}/status", status_code=status.HTTP_200_OK)
async def get_knowledge_file_status(file_id: str):
    """
    Get the processing status of an ingested knowledge file.
    """
    try:
        rag_service = RagFileUploadService()
        status_info = rag_service.get_file_status(file_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "success": True,
            "file_id": file_id,
            "status": status_info.get("status", "unknown"),
            "progress": status_info.get("progress", 0),
            "message": status_info.get("message", ""),
            "created_at": status_info.get("created_at"),
            "completed_at": status_info.get("completed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file status: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ingest/jobs", status_code=status.HTTP_200_OK)
async def get_ingestion_jobs(user_id: str = None):
    """
    Get all ingestion jobs for a user.
    """
    try:
        rag_service = RagFileUploadService()
        jobs = rag_service.get_user_jobs(user_id)
        
        return {
            "success": True,
            "jobs": jobs,
            "total_count": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Error getting ingestion jobs: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINTS (Moved to conversation/chat_router.py)
# ============================================================================  