"""
Conversation Router - REST Endpoints

This module contains conversation management REST endpoints including
traditional chat, memory reset, and conversation session management.
All conversation-related functionality is centralized here.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.user import User
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

# Create router
router = APIRouter(prefix="/conversations", tags=["Conversations Management"])


class ChatMessage(BaseModel):
    message: str
    candidate_id: str
    role: str
    seniority: str
    domain: str


class ConversationSessionResponse(BaseModel):
    id: str
    name: str
    created_at: str
    message_count: int
    topics_discussed: List[str]
    knowledge_sources_used: List[str]


class CreateSessionRequest(BaseModel):
    name: Optional[str] = Field(
        None, max_length=100, description="Optional name for the conversation"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Optional description"
    )
    llm_provider_id: Optional[str] = Field(
        None, description="LLM provider ID to use for this conversation"
    )
    llm_model_name: Optional[str] = Field(
        None,
        description="Specific model name (optional, uses provider default if not specified)",
    )
    enhancement_strategy: Optional[str] = Field(
        None,
        description="Query enhancement strategy (none, step_back, multi_query, hyde, decomposition, rag_fusion, augmented)",
    )
    collection_name: Optional[str] = Field(
        "LongTermMemory", description="Vector DB collection name"
    )
    enable_reranking: bool = Field(
        True, description="Enable document reranking/judging for better relevance"
    )
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID (Cohere/Voyage AI)"
    )
    reranker_model_name: Optional[str] = Field(None, description="Reranker model name")
    tags: Optional[str] = Field(None, description="Tags for organizing conversations")


class RenameSessionRequest(BaseModel):
    new_name: str = Field(
        ..., min_length=1, max_length=100, description="New name for the conversation"
    )


class UpdateSessionConfigRequest(BaseModel):
    llm_provider_id: Optional[str] = Field(None, description="LLM provider ID to use")
    llm_model_name: Optional[str] = Field(None, description="Specific model name")
    enhancement_strategy: Optional[str] = Field(
        None, description="Query enhancement strategy"
    )
    collection_name: Optional[str] = Field(
        None, description="Vector DB collection name"
    )
    enable_reranking: Optional[bool] = Field(
        None, description="Enable document reranking"
    )
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID"
    )
    reranker_model_name: Optional[str] = Field(None, description="Reranker model name")
    tags: Optional[List[str]] = Field(None, description="Tags for organizing")


# ============================================================================
# CONVERSATION SESSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation_session(
    create_request: CreateSessionRequest = CreateSessionRequest(),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new conversation session with optional LLM and enhancement configuration.
    """
    try:
        session_id = conversation_history_service.create_conversation(
            user_id=current_user.id,
            name=create_request.name,
            description=create_request.description,
            llm_provider_id=create_request.llm_provider_id,
            llm_model_name=create_request.llm_model_name,
            enhancement_strategy=create_request.enhancement_strategy,
            collection_name=create_request.collection_name or "LongTermMemory",
            enable_reranking=create_request.enable_reranking,
            reranker_provider_id=create_request.reranker_provider_id,
            reranker_model_name=create_request.reranker_model_name,
            tags=create_request.tags,
        )

        return {
            "success": True,
            "id": session_id,
            "name": create_request.name or f"Session {session_id[:8]}",
            "llm_provider_id": create_request.llm_provider_id,
            "enhancement_strategy": create_request.enhancement_strategy,
            "collection_name": create_request.collection_name or "LongTermMemory",
            "enable_reranking": create_request.enable_reranking,
            "reranker_provider_id": create_request.reranker_provider_id,
            "reranker_model_name": create_request.reranker_model_name,
            "message": "Conversation session created successfully",
        }

    except Exception as e:
        logger.error(f"Error creating conversation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", status_code=status.HTTP_200_OK)
async def send_chat_message(
    conversation_id: str,
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user),
):
    """
    Send a chat message to a specific conversation session.

    This endpoint uses the traditional approach with predefined role, seniority, and domain
    parameters to conduct interviews without resume/job description analysis.

    Parameters:
    - conversation_id: The conversation session ID
    - message: The chat message/question
    - candidate_id: Unique candidate identifier
    - role: Job role (e.g., "Software Engineer", "Data Scientist")
    - seniority: Experience level (e.g., "Junior", "Senior", "Lead")
    - domain: Technical domain (e.g., "Python", "JavaScript", "DevOps")
    """
    try:
        response, _ = await get_response(
            messages=chat_message.message,
            candidate_id=chat_message.candidate_id,
            interview_context={
                "role": chat_message.role,
                "seniority": chat_message.seniority,
                "domain": chat_message.domain,
            },
            user_id=current_user.id,
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def reset_conversation_messages(
    conversation_id: str, current_user: User = Depends(get_current_user)
):
    """
    Reset messages for a specific conversation session.

    This endpoint clears all messages and context for the specified conversation,
    but keeps the session itself. Useful for starting fresh within a conversation.
    """
    try:
        success = conversation_history_service.reset_conversation_messages(
            conversation_id, current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONVERSATION SESSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.get("", status_code=status.HTTP_200_OK)
async def get_conversation_sessions(current_user: User = Depends(get_current_user)):
    """
    Get all conversation sessions for the current user.
    """
    try:
        sessions = conversation_history_service.get_user_conversations(current_user.id)

        session_responses = []
        for session in sessions:
            session_data = {
                "id": str(session._id),
                "name": session.name or f"Session {str(session._id)[:8]}",
                "description": session.description,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "message_count": session.message_count,
                "topics_discussed": session.topics_discussed or [],
                "knowledge_sources_used": session.knowledge_sources_used or [],
                "llm_provider_id": session.llm_provider_id,
                "llm_model_name": session.llm_model_name,
                "collection_name": session.collection_name,
                "total_queries": session.total_queries,
                "total_documents_retrieved": session.total_documents_retrieved,
                "average_response_time_ms": session.average_response_time_ms,
                "tags": session.tags or [],
            }

            # Add enhancement config
            if session.enhancement_config:
                session_data["enhancement_strategy"] = (
                    session.enhancement_config.strategy
                )
                session_data["enhancement_enabled"] = session.enhancement_config.enabled
            else:
                session_data["enhancement_strategy"] = "none"
                session_data["enhancement_enabled"] = False

            session_responses.append(session_data)

        return {
            "success": True,
            "sessions": session_responses,
            "total_count": len(session_responses),
        }

    except Exception as e:
        logger.error(f"Error retrieving conversation sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_conversation_session(
    conversation_id: str,
    expand: Optional[str] = Query(
        None, description="Comma-separated fields to expand (e.g., llm_provider)"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Get specific conversation session details and messages with optional provider expansion.
    """
    try:
        # Check if we need to expand provider
        expand_provider = expand and "llm_provider" in expand.split(",")

        if expand_provider:
            result = conversation_history_service.get_conversation_with_provider(
                conversation_id, current_user.id
            )
            if not result:
                raise HTTPException(
                    status_code=404, detail="Conversation session not found"
                )
            session = result["session"]
            llm_provider = result["llm_provider"]
        else:
            session = conversation_history_service.get_conversation(
                conversation_id, current_user.id
            )
            llm_provider = None

        if not session:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        messages = conversation_history_service.get_session_messages(
            conversation_id, current_user.id
        )

        session_data = {
            "id": session._id,
            "name": session.name or f"Session {session._id[:8]}",
            "description": session.description,
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat(),
            "message_count": session.message_count,
            "topics_discussed": session.topics_discussed or [],
            "knowledge_sources_used": session.knowledge_sources_used or [],
            "llm_provider_id": session.llm_provider_id,
            "llm_model_name": session.llm_model_name,
            "collection_name": session.collection_name,
            "total_queries": session.total_queries,
            "total_documents_retrieved": session.total_documents_retrieved,
            "average_response_time_ms": session.average_response_time_ms,
            "tags": session.tags or [],
        }

        # Add enhancement config
        if session.enhancement_config:
            session_data["enhancement_config"] = {
                "strategy": session.enhancement_config.strategy,
                "enabled": session.enhancement_config.enabled,
            }
        else:
            session_data["enhancement_config"] = {"strategy": "none", "enabled": False}

        # Add expanded provider if requested
        if llm_provider:
            session_data["llm_provider"] = llm_provider

        return {"success": True, "session": session_data, "messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_session(
    conversation_id: str, current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation session and all its messages.
    """
    try:
        success = conversation_history_service.delete_conversation(
            conversation_id, current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_conversation_session(
    create_request: CreateSessionRequest = CreateSessionRequest(),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new conversation session.
    """
    try:
        session_id = conversation_history_service.create_conversation(
            user_id=current_user.id, name=create_request.name
        )

        return {
            "success": True,
            "id": session_id,
            "name": create_request.name or f"Session {session_id[:8]}",
            "message": "Conversation session created successfully",
        }

    except Exception as e:
        logger.error(f"Error creating conversation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/name", status_code=status.HTTP_200_OK)
async def rename_conversation_session(
    conversation_id: str,
    rename_request: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Rename a conversation session.
    """
    try:
        success = conversation_history_service.rename_conversation(
            conversation_id=conversation_id,
            new_name=rename_request.new_name,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        return {
            "success": True,
            "id": conversation_id,
            "new_name": rename_request.new_name,
            "message": "Conversation session renamed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming conversation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/config", status_code=status.HTTP_200_OK)
async def update_conversation_config(
    conversation_id: str,
    config_request: UpdateSessionConfigRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update conversation configuration (LLM provider, enhancement strategy, etc).
    """
    try:
        success = conversation_history_service.update_conversation_config(
            conversation_id=conversation_id,
            user_id=current_user.id,
            llm_provider_id=config_request.llm_provider_id,
            llm_model_name=config_request.llm_model_name,
            enhancement_strategy=config_request.enhancement_strategy,
            collection_name=config_request.collection_name,
            enable_reranking=config_request.enable_reranking,
            reranker_provider_id=config_request.reranker_provider_id,
            reranker_model_name=config_request.reranker_model_name,
            tags=config_request.tags,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found or no changes made",
            )

        return {
            "success": True,
            "id": conversation_id,
            "message": "Conversation configuration updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
