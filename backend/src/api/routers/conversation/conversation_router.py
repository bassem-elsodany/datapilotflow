"""
Conversation Router - REST Endpoints

This module contains conversation management REST endpoints.

NEW ARCHITECTURE:
- Conversations are lightweight threads linked to agents via agent_id
- Configuration (enhancement, vector_database, reranker, answer_generation, assistant_config)
  is stored in the Agent, not in the Conversation
- Messages are stored in a separate collection
"""

from typing import List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.conversation import ConversationSession
from src.domain.user import User
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

# Create router
router = APIRouter(prefix="/conversations", tags=["Conversations Management"])


def get_user_id(user: User) -> str:
    """Get user ID with type safety. Raises HTTPException if user ID is not set."""
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")
    return user.id


# ============================================================================
# REQUEST MODELS
# ============================================================================


class CreateSessionRequest(BaseModel):
    """
    Request model for creating a new conversation session.

    NEW ARCHITECTURE: Conversations are linked to agents.
    Create an agent first, then create conversations using that agent's ID.
    """

    agent_id: str = Field(..., description="ID of agent to use (REQUIRED)")
    name: Optional[str] = Field(None, max_length=100, description="Conversation name")
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags for organizing conversations"
    )


def _serialize_conversation_to_response(
    session: "ConversationSession", message_count: int = 0
) -> dict:
    """
    Serialize ConversationSession to API response format.

    NEW ARCHITECTURE: Configuration is now stored in the linked Agent, not in the conversation.
    """
    return {
        "id": session._id,
        "agent_id": session.agent_id,
        "name": session.name or f"Conversation {session._id[:8]}",
        "description": session.description,
        "created_at": session.created_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "last_message_at": (
            session.last_message_at.isoformat() if session.last_message_at else None
        ),
        "message_count": message_count,
        "tags": session.tags or [],
        "is_archived": session.is_archived,
    }


class RenameSessionRequest(BaseModel):
    """Request model for renaming a conversation."""

    new_name: str = Field(
        ..., min_length=1, max_length=100, description="New name for the conversation"
    )


# ============================================================================
# CONVERSATION SESSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation_session(
    create_request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new conversation session linked to an agent.

    Request body:
    {
      "agent_id": "string (REQUIRED)",
      "name": "string (optional)",
      "description": "string (optional)",
      "tags": ["string"] (optional)
    }
    """
    try:
        logger.info(f"Creating conversation from agent {create_request.agent_id}")

        # Validate agent exists and belongs to user
        from src.services.agent.agent_service import get_agent_service

        agent_service = get_agent_service()
        user_id = get_user_id(current_user)
        agent = agent_service.get_agent(create_request.agent_id, user_id)

        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent {create_request.agent_id} not found"
            )

        # Create conversation (metadata only)
        session_id = conversation_history_service.create_conversation(
            user_id=user_id,
            agent_id=create_request.agent_id,
            name=create_request.name,
            description=create_request.description,
            tags=create_request.tags,
        )

        logger.info(
            f"Created conversation {session_id} for agent {create_request.agent_id}"
        )

        return {
            "success": True,
            "id": session_id,
            "agent_id": create_request.agent_id,
            "agent_name": agent.name,
            "agent_type": agent.agent_type.value,
            "name": create_request.name or f"Conversation {session_id[:8]}",
            "message": "Conversation created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoint - commented out as get_response function no longer exists
# @router.post("/{conversation_id}/messages", status_code=status.HTTP_200_OK)
# async def send_chat_message(
#     conversation_id: str,
#     chat_message: ChatMessage,
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Send a chat message to a specific conversation session.
#     """
#     # This endpoint used a legacy get_response function that no longer exists
#     raise HTTPException(status_code=501, detail="Endpoint not implemented")


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
        user_id = get_user_id(current_user)
        success = conversation_history_service.reset_conversation_messages(
            conversation_id, user_id
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
async def get_conversation_sessions(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of conversations"
    ),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    current_user: User = Depends(get_current_user),
):
    """
    Get all conversation sessions for the current user with new nested configuration structure.

    Query Parameters:
        - agent_id: Optional filter by agent ID
        - limit: Maximum number of conversations to return (default: 100)
        - offset: Number of conversations to skip (default: 0)
    """
    try:
        user_id = get_user_id(current_user)
        logger.info(
            f"GET /conversations called with agent_id={agent_id}, user_id={user_id}"
        )

        sessions = conversation_history_service.get_user_conversations(
            user_id=user_id,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )

        logger.info(f"Found {len(sessions)} conversations")

        session_responses = []
        for session in sessions:
            # Get message count for this conversation
            message_count = conversation_history_service.get_message_count(session._id)

            session_data = {
                "id": session._id,
                "agent_id": session.agent_id,
                "name": session.name or f"Conversation {session._id[:8]}",
                "description": session.description,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "last_message_at": (
                    session.last_message_at.isoformat()
                    if session.last_message_at
                    else None
                ),
                "message_count": message_count,
                "tags": session.tags or [],
                "is_archived": session.is_archived,
            }
            session_responses.append(session_data)

        return {
            "success": True,
            "sessions": session_responses,
            "total_count": len(session_responses),
            "agent_id": agent_id,
        }

    except Exception as e:
        logger.error(f"Error retrieving conversation sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_conversation_session(
    conversation_id: str,
    expand: Optional[str] = Query(
        None, description="Comma-separated fields to expand (e.g., agent, messages)"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Get specific conversation session details.

    Query Parameters:
        - expand: Comma-separated fields to expand
            - "messages": Include full message history
            - "agent": Include agent details
    """
    try:
        user_id = get_user_id(current_user)
        session = conversation_history_service.get_conversation(
            conversation_id, user_id
        )

        if not session:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        # Get message count
        message_count = conversation_history_service.get_message_count(conversation_id)

        # Serialize conversation
        session_data = _serialize_conversation_to_response(session, message_count)

        # Handle expansions
        expand_fields = expand.split(",") if expand else []

        # Expand messages if requested
        messages = None
        if "messages" in expand_fields:
            message_list = conversation_history_service.get_conversation_messages(
                conversation_id
            )
            messages = [
                {
                    "id": msg._id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "message_index": msg.message_index,
                    "source_links": msg.source_links,
                    "enhancement_strategy_used": msg.enhancement_strategy_used,
                    "enhanced_queries": msg.enhanced_queries,
                    "processing_time_ms": msg.processing_time_ms,
                    "document_count": msg.document_count,
                }
                for msg in message_list
            ]

        # Expand agent if requested
        agent_data = None
        if "agent" in expand_fields:
            from dataclasses import asdict

            from src.services.agent.agent_service import get_agent_service

            agent_service = get_agent_service()
            agent = agent_service.get_agent(session.agent_id, user_id)
            if agent:
                # Serialize configuration objects to dicts
                def config_to_dict(obj):
                    if obj is None:
                        return None
                    if hasattr(obj, "__dataclass_fields__"):
                        result = {}
                        for field in obj.__dataclass_fields__:
                            value = getattr(obj, field)
                            result[field] = config_to_dict(value)
                        return result
                    return obj

                agent_data = {
                    "id": agent._id,
                    "name": agent.name,
                    "agent_type": agent.agent_type.value,
                    "description": agent.description,
                    # Include full configuration for frontend
                    "enhancement": config_to_dict(agent.enhancement),
                    "vector_database": config_to_dict(agent.vector_database),
                    "reranker": config_to_dict(agent.reranker),
                    "answer_generation": config_to_dict(agent.answer_generation),
                    "assistant_config": config_to_dict(agent.assistant_config),
                }

        response = {"success": True, "session": session_data}
        if messages is not None:
            response["messages"] = messages
        if agent_data is not None:
            response["agent"] = agent_data

        return response

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
        user_id = get_user_id(current_user)
        success = conversation_history_service.delete_conversation(
            conversation_id, user_id
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
        user_id = get_user_id(current_user)
        success = conversation_history_service.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            name=rename_request.new_name,
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


class UpdateConversationRequest(BaseModel):
    """Request model for updating conversation metadata."""

    name: Optional[str] = Field(None, max_length=100, description="Conversation name")
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags for organizing conversations"
    )
    is_archived: Optional[bool] = Field(
        None, description="Whether the conversation is archived"
    )


@router.put("/{conversation_id}", status_code=status.HTTP_200_OK)
async def update_conversation_session(
    conversation_id: str,
    update_request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update conversation metadata.

    NOTE: Configuration (enhancement, vector_database, reranker, answer_generation, assistant_config)
    is now stored in the linked Agent. Use PUT /agents/{agent_id} to update configuration.
    """
    try:
        user_id = get_user_id(current_user)
        success = conversation_history_service.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            name=update_request.name,
            description=update_request.description,
            tags=update_request.tags,
            is_archived=update_request.is_archived,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "id": conversation_id,
            "message": "Conversation updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
