"""
Knowledge Management Router

This module contains endpoints for knowledge ingestion and search functionality.
Conversation management endpoints have been moved to the conversation router.
"""

import asyncio
import json
import os
import traceback
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, validator

from datapilotflow.api.routers.auth.auth_router import (
    decode_access_token,
    get_current_user,
    validate_jwt_token,
)

# LLM responder functionality removed - using LangGraph workflow instead
# Note: LLM synthesis functionality has been removed from this router
# Use the agent WebSocket endpoint (/ws/agent/query) for LLM-powered responses
from datapilotflow.domain.config import settings
from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
from datapilotflow.domain.user import User
from datapilotflow.infrastructure.vectordb import MilvusClientWrapper
from datapilotflow.services.conversation.conversation_history_service import (
    conversation_history_service,
)
from datapilotflow.infrastructure.dao.file_management import (
    RagFileUploadService,
)
from datapilotflow.services.file_management.file_upload_service import handle_file_upload

# Create router
router = APIRouter(prefix="/knowledge", tags=["Knowledge Management"])


# metadata_fields removed - no longer needed since search functionality moved to agent WebSocket


# Milvus client creation moved to agent WebSocket workflow


# process_search_results removed - use agent WebSocket instead


# SearchQuery removed - use agent WebSocket instead


# ContextAwareSearchQuery removed - use agent WebSocket instead


# Search endpoint removed - use agent WebSocket instead


# Context-aware search endpoint removed - use agent WebSocket instead


# ============================================================================
# KNOWLEDGE INGESTION ENDPOINTS
# ============================================================================


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_knowledge_file(
    file: UploadFile = File(...),
    user_id: str = Form(None),
    description: str = Form(""),
    request: Request = None,
    current_user: User = Depends(get_current_user),
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
            file=file, user_id=user_id, description=description
        )

        return {
            "success": True,
            "file_id": result.get("file_id"),
            "message": "File uploaded and processing started",
            "status": "processing",
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
            "completed_at": status_info.get("completed_at"),
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

        return {"success": True, "jobs": jobs, "total_count": len(jobs)}

    except Exception as e:
        logger.error(f"Error getting ingestion jobs: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINTS (Moved to conversation/chat_router.py)
# ============================================================================
