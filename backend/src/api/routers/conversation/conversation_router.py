"""
Conversation Router - REST Endpoints

This module contains conversation management REST endpoints including
traditional chat, memory reset, and conversation session management.
All conversation-related functionality is centralized here.
"""

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.conversation import (
    AnswerGenerationConfig,
    AssistantConfig,
    ConversationSession,
    EnhancementConfig,
    ProviderConfig,
    RerankerConfig,
    VectorDatabaseConfig,
)
from src.domain.user import User
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

# Create router
router = APIRouter(prefix="/conversations", tags=["Conversations Management"])


# ============================================================================
# NEW PYDANTIC MODELS FOR RESTRUCTURED CONVERSATION SCHEMA
# ============================================================================


class ProviderConfigRequest(BaseModel):
    """Request model for provider configuration."""

    id: str = Field(..., description="Provider ID")
    model_name: str = Field(..., description="Model name")


class EnhancementConfigRequest(BaseModel):
    """Request model for enhancement strategy configuration."""

    strategy: str = Field(
        ...,
        description="Enhancement strategy (native, multi_query, augmented, hyde, decomposition)",
    )
    provider: Optional[ProviderConfigRequest] = Field(
        None, description="Provider for enhancement"
    )


class VectorDatabaseConfigRequest(BaseModel):
    """Request model for vector database configuration."""

    collection_name: str = Field(
        "LongTermMemory", description="Vector database collection name"
    )
    top_k: int = Field(5, ge=5, le=30, description="Number of documents to retrieve")


class RerankerConfigRequest(BaseModel):
    """Request model for reranker configuration."""

    enabled: bool = Field(False, description="Whether reranking is enabled")
    provider: Optional[ProviderConfigRequest] = Field(
        None, description="Reranker provider"
    )
    relevance_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Relevance score threshold for filtering documents",
    )


class AnswerGenerationConfigRequest(BaseModel):
    """Request model for answer generation configuration."""

    enabled: bool = Field(False, description="Whether answer generation is enabled")
    provider: Optional[ProviderConfigRequest] = Field(
        None, description="LLM provider for answer generation"
    )


class SystemPromptRequest(BaseModel):
    """Request model for embedded system prompt."""

    id: str = Field(..., description="System prompt ID")
    title: str = Field(..., description="System prompt title")
    content: str = Field(..., description="System prompt content")


class AssistantConfigRequest(BaseModel):
    """Request model for Assistant mode configuration."""

    enabled: bool = Field(
        True, description="Whether Assistant mode is enabled (true) or RAG mode (false)"
    )
    tools: Optional[List[str]] = Field(
        default_factory=list, description="List of tool IDs bound to this conversation agent"
    )
    instructions: Optional[str] = Field(
        None, description="User's custom instructions for agent personality, behavior, and tool usage"
    )


class CreateSessionRequest(BaseModel):
    """Request model for creating a new conversation session with new structure."""

    name: Optional[str] = Field(None, max_length=100, description="Conversation name")
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    system_prompt: Optional[SystemPromptRequest] = Field(
        None,
        description="Embedded system prompt (deprecated - use assistant_config for Assistant mode)",
    )
    enhancement: Optional[EnhancementConfigRequest] = Field(
        None, description="Query enhancement configuration"
    )
    vector_database: Optional[VectorDatabaseConfigRequest] = Field(
        None, description="Vector database configuration"
    )
    reranker: Optional[RerankerConfigRequest] = Field(
        None, description="Document reranker configuration"
    )
    answer_generation: Optional[AnswerGenerationConfigRequest] = Field(
        None, description="Answer generation configuration"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags for organizing conversations"
    )
    enable_knowledge_assistant: bool = Field(
        False,
        description="Enable multi-agent supervisor (deprecated - use assistant_config)",
    )
    assistant_config: Optional[AssistantConfigRequest] = Field(
        None,
        description="Complex nested configuration for Assistant mode (RAG=null, Assistant=object)",
    )


def _serialize_conversation_to_response(session: "ConversationSession") -> dict:
    """Serialize ConversationSession to API response format (new nested structure)."""
    # Determine agent mode based on assistant_config
    agent_mode = "assistant" if (session.assistant_config and session.assistant_config.enabled) else "rag"
    
    response = {
        "id": session._id,
        "name": session.name or f"Session {session._id[:8]}",
        "description": session.description,
        "created_at": session.created_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "message_count": session.message_count,
        "tags": session.tags or [],
        "agent_mode": agent_mode,  # "rag" or "assistant"
    }

    # Enhancement configuration
    if session.enhancement:
        response["enhancement"] = {
            "strategy": session.enhancement.strategy,
            "provider": (
                {
                    "id": session.enhancement.provider.id,
                    "model_name": session.enhancement.provider.model_name,
                }
                if session.enhancement.provider
                else None
            ),
        }

    # Vector database configuration
    if session.vector_database:
        response["vector_database"] = {
            "collection_name": session.vector_database.collection_name,
            "top_k": session.vector_database.top_k,
        }

    # Reranker configuration
    if session.reranker:
        response["reranker"] = {
            "enabled": session.reranker.enabled,
            "provider": (
                {
                    "id": session.reranker.provider.id,
                    "model_name": session.reranker.provider.model_name,
                }
                if session.reranker.provider
                else None
            ),
            "relevance_threshold": session.reranker.relevance_threshold,
        }

    # Answer generation configuration
    if session.answer_generation:
        response["answer_generation"] = {
            "enabled": session.answer_generation.enabled,
            "provider": (
                {
                    "id": session.answer_generation.provider.id,
                    "model_name": session.answer_generation.provider.model_name,
                }
                if session.answer_generation.provider
                else None
            ),
        }

    # Assistant configuration (tool bindings)
    if session.assistant_config:
        response["assistant_config"] = {
            "enabled": session.assistant_config.enabled,
            "tools": session.assistant_config.tools if session.assistant_config.tools else [],
            "instructions": session.assistant_config.instructions,
        }

    return response


class ChatMessage(BaseModel):
    message: str
    candidate_id: str
    role: str
    seniority: str
    domain: str


class RenameSessionRequest(BaseModel):
    new_name: str = Field(
        ..., min_length=1, max_length=100, description="New name for the conversation"
    )


class UpdateSessionConfigRequest(BaseModel):
    """Request model for updating conversation configuration with new nested structure."""

    name: Optional[str] = Field(None, max_length=100, description="Conversation name")
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    system_prompt: Optional[SystemPromptRequest] = Field(
        None,
        description="Embedded system prompt (deprecated - use assistant_config for Assistant mode)",
    )
    enhancement: Optional[EnhancementConfigRequest] = Field(
        None, description="Query enhancement configuration"
    )
    vector_database: Optional[VectorDatabaseConfigRequest] = Field(
        None, description="Vector database configuration"
    )
    reranker: Optional[RerankerConfigRequest] = Field(
        None, description="Document reranker configuration"
    )
    answer_generation: Optional[AnswerGenerationConfigRequest] = Field(
        None, description="Answer generation configuration"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags for organizing conversations"
    )
    enable_knowledge_assistant: Optional[bool] = Field(
        None,
        description="Enable multi-agent supervisor (deprecated - use assistant_config)",
    )
    assistant_config: Optional[AssistantConfigRequest] = Field(
        None,
        description="Complex nested configuration for Assistant mode (RAG=null, Assistant=object)",
    )


class AssistantConfigResponse(BaseModel):
    """Response model for Assistant mode configuration."""

    enabled: bool = Field(
        ..., description="Whether Assistant mode is enabled (true) or RAG mode (false)"
    )
    tools: List[str] = Field(
        default_factory=list, description="List of tool IDs bound to this conversation agent"
    )
    instructions: Optional[str] = Field(
        None, description="User's custom instructions for agent personality, behavior, and tool usage"
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
    Create a new conversation session with nested configuration structure.

    Request body structure:
    {
      "name": "string (optional)",
      "description": "string (optional)",
      "system_prompt": {...},  # optional
      "enhancement": {
        "strategy": "string",
        "provider": {"id": "string", "model_name": "string"} (optional)
      },
      "vector_database": {
        "collection_name": "string",
        "top_k": number
      },
      "reranker": {
        "provider": {"id": "string", "model_name": "string"} (optional),
        "relevance_threshold": number
      },
      "answer_generation": {
        "provider": {"id": "string", "model_name": "string"} (optional)
      },
      "assistant_config": {
        "enabled": boolean,
        "tools": ["tool_id_1", "tool_id_2"] (optional),
        "instructions": "string" (optional)
      },
      "tags": ["string"]
    }
    """
    try:
        # Convert request models to service dataclasses

        enhancement = None
        if create_request.enhancement:
            provider = None
            if create_request.enhancement.provider:
                provider = ProviderConfig(
                    id=create_request.enhancement.provider.id,
                    model_name=create_request.enhancement.provider.model_name,
                )
            enhancement = EnhancementConfig(
                strategy=create_request.enhancement.strategy, provider=provider
            )

        vector_database = None
        if create_request.vector_database:
            vector_database = VectorDatabaseConfig(
                collection_name=create_request.vector_database.collection_name,
                top_k=create_request.vector_database.top_k,
            )

        reranker = None
        if create_request.reranker:
            provider = None
            if create_request.reranker.provider:
                provider = ProviderConfig(
                    id=create_request.reranker.provider.id,
                    model_name=create_request.reranker.provider.model_name,
                )
            reranker = RerankerConfig(
                enabled=create_request.reranker.enabled,
                provider=provider,
                relevance_threshold=create_request.reranker.relevance_threshold,
            )

        answer_generation = None
        if create_request.answer_generation:
            provider = None
            if create_request.answer_generation.provider:
                provider = ProviderConfig(
                    id=create_request.answer_generation.provider.id,
                    model_name=create_request.answer_generation.provider.model_name,
                )
            answer_generation = AnswerGenerationConfig(
                enabled=create_request.answer_generation.enabled, provider=provider
            )

        # Build assistant_config if provided
        assistant_config = None
        if create_request.assistant_config:
            assistant_config = AssistantConfig(
                enabled=create_request.assistant_config.enabled,
                tools=create_request.assistant_config.tools if create_request.assistant_config.tools else [],
                instructions=create_request.assistant_config.instructions,
            )
            logger.info(
                f"Created AssistantConfig: enabled={assistant_config.enabled}, tools_count={len(assistant_config.tools)}, has_instructions={bool(create_request.assistant_config.instructions)}"
            )

        session_id = conversation_history_service.create_conversation(
            user_id=current_user.id,
            name=create_request.name,
            description=create_request.description,
            enhancement=enhancement,
            vector_database=vector_database,
            reranker=reranker,
            answer_generation=answer_generation,
            tags=create_request.tags,
            assistant_config=assistant_config,
        )

        # Determine agent type from assistant_config
        if assistant_config:
            agent_type = "supervisor" if assistant_config.enabled else "rag"
        else:
            agent_type = "rag"  # Default to RAG if no assistant_config

        # Fetch the created conversation and return the full session
        created_session = conversation_history_service.get_conversation(
            session_id, current_user.id
        )

        return {
            "success": True,
            "id": session_id,
            "session": (
                _serialize_conversation_to_response(created_session)
                if created_session
                else None
            ),
            "name": create_request.name or f"Session {session_id[:8]}",
            "agent_type": agent_type,
            "enhancement_strategy": (
                create_request.enhancement.strategy
                if create_request.enhancement
                else None
            ),
            "message": "Conversation session created successfully",
        }

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
    Get all conversation sessions for the current user with new nested configuration structure.
    """
    try:
        sessions = conversation_history_service.get_user_conversations(current_user.id)

        session_responses = []
        for session in sessions:
            # Serialize each conversation to response format (new nested structure)
            session_data = _serialize_conversation_to_response(session)
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

        # Serialize conversation to response format (new nested structure)
        session_data = _serialize_conversation_to_response(session)

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


@router.put("/{conversation_id}", status_code=status.HTTP_200_OK)
async def update_conversation_session(
    conversation_id: str,
    config_request: UpdateSessionConfigRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update conversation session with new nested configuration structure.
    """
    try:
        # Get current conversation
        conversation = conversation_history_service.get_conversation(
            conversation_id, current_user.id
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Build MongoDB update document with new nested structure
        update_doc = {}

        # Basic fields
        if config_request.name is not None:
            update_doc["name"] = config_request.name
        if config_request.description is not None:
            update_doc["description"] = config_request.description
        if config_request.tags is not None:
            update_doc["tags"] = config_request.tags

        # Enhancement configuration
        if config_request.enhancement is not None:
            provider = None
            if config_request.enhancement.provider:
                provider = {
                    "id": config_request.enhancement.provider.id,
                    "model_name": config_request.enhancement.provider.model_name,
                }
            update_doc["enhancement"] = {
                "strategy": config_request.enhancement.strategy,
                "provider": provider,
            }

        # Vector database configuration
        if config_request.vector_database is not None:
            update_doc["vector_database"] = {
                "collection_name": config_request.vector_database.collection_name,
                "top_k": config_request.vector_database.top_k,
            }

        # Reranker configuration
        if config_request.reranker is not None:
            provider = None
            if config_request.reranker.provider:
                provider = {
                    "id": config_request.reranker.provider.id,
                    "model_name": config_request.reranker.provider.model_name,
                }
            update_doc["reranker"] = {
                "enabled": config_request.reranker.enabled,
                "provider": provider,
                "relevance_threshold": config_request.reranker.relevance_threshold,
            }

        # Answer generation configuration
        if config_request.answer_generation is not None:
            provider = None
            if config_request.answer_generation.provider:
                provider = {
                    "id": config_request.answer_generation.provider.id,
                    "model_name": config_request.answer_generation.provider.model_name,
                }
            update_doc["answer_generation"] = {
                "enabled": config_request.answer_generation.enabled,
                "provider": provider,
            }

        # Assistant configuration (tool bindings)
        if config_request.assistant_config is not None:
            logger.info(
                f"Updating assistant_config: enabled={config_request.assistant_config.enabled}"
            )

            assistant_config_dict = {
                "enabled": config_request.assistant_config.enabled,
                "tools": config_request.assistant_config.tools if config_request.assistant_config.tools else [],
                "instructions": config_request.assistant_config.instructions,
            }

            if config_request.assistant_config.instructions:
                logger.info(f"Including instructions in update ({len(config_request.assistant_config.instructions)} chars)")

            logger.info(
                f"Updating AssistantConfig: enabled={config_request.assistant_config.enabled}, tools_count={len(assistant_config_dict['tools'])}"
            )
            update_doc["assistant_config"] = assistant_config_dict

        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update last_updated timestamp
        from datetime import datetime

        update_doc["last_updated"] = datetime.utcnow()

        # Update MongoDB document
        from bson import ObjectId

        result = conversation_history_service.collection.update_one(
            {"_id": ObjectId(conversation_id), "user_id": current_user.id},
            {"$set": update_doc},
        )

        if result.matched_count == 0:
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
