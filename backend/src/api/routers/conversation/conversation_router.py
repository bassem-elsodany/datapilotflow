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
from src.domain.conversation import (
    AnswerGenerationConfig,
    AssistantConfig,
    EnhancementConfig,
    ProviderConfig,
    RerankerConfig,
    SystemPromptTask,
    VectorDatabaseConfig,
)
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
    top_k: int = Field(
        5, ge=5, le=30, description="Number of documents to retrieve"
    )


class RerankerConfigRequest(BaseModel):
    """Request model for reranker configuration."""

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

    provider: Optional[ProviderConfigRequest] = Field(
        None, description="LLM provider for answer generation"
    )


class SystemPromptRequest(BaseModel):
    """Request model for embedded system prompt."""

    id: str = Field(..., description="System prompt ID")
    title: str = Field(..., description="System prompt title")
    content: str = Field(..., description="System prompt content")


class SystemPromptTaskRequest(BaseModel):
    """Request model for system prompt task (for assistant_config)."""

    title: str = Field(..., min_length=1, max_length=100, description="System prompt task title")
    content: str = Field(..., min_length=10, description="System prompt task content")
    is_active: bool = Field(True, description="Whether this prompt is active")


class AssistantConfigRequest(BaseModel):
    """Request model for complex nested Assistant mode configuration."""

    enable_knowledge_assistant: bool = Field(
        True, description="Enable knowledge assistant for multi-agent orchestration"
    )
    system_prompt_tasks: Optional[List[SystemPromptTaskRequest]] = Field(
        None, description="System prompt tasks for the assistant"
    )


class CreateSessionRequest(BaseModel):
    """Request model for creating a new conversation session with new structure."""

    name: Optional[str] = Field(
        None, max_length=100, description="Conversation name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    system_prompt: Optional[SystemPromptRequest] = Field(
        None, description="Embedded system prompt (deprecated - use assistant_config for Assistant mode)"
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
        None, description="Complex nested configuration for Assistant mode (RAG=null, Assistant=object)"
    )


def _serialize_conversation_to_response(session: 'ConversationSession') -> dict:
    """Serialize ConversationSession to API response format (new nested structure)."""
    response = {
        "id": session._id,
        "name": session.name or f"Session {session._id[:8]}",
        "description": session.description,
        "created_at": session.created_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "message_count": session.message_count,
        "tags": session.tags or [],
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
            "provider": (
                {
                    "id": session.answer_generation.provider.id,
                    "model_name": session.answer_generation.provider.model_name,
                }
                if session.answer_generation.provider
                else None
            )
        }

    # Assistant configuration (complex nested structure)
    if session.assistant_config:
        response["assistant_config"] = {
            "enable_knowledge_assistant": session.assistant_config.enable_knowledge_assistant,
        }
        if session.assistant_config.system_prompt_tasks:
            response["assistant_config"]["system_prompt_tasks"] = [
                {
                    "id": task.id,
                    "title": task.name,  # SystemPromptTask uses 'name', map to 'title' for API
                    "content": task.system_prompt,  # SystemPromptTask uses 'system_prompt', map to 'content' for API
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "is_active": task.is_active,
                }
                for task in session.assistant_config.system_prompt_tasks
            ]
        else:
            response["assistant_config"]["system_prompt_tasks"] = None

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

    name: Optional[str] = Field(
        None, max_length=100, description="Conversation name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Conversation description"
    )
    system_prompt: Optional[SystemPromptRequest] = Field(
        None, description="Embedded system prompt (deprecated - use assistant_config for Assistant mode)"
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
        None, description="Complex nested configuration for Assistant mode (RAG=null, Assistant=object)"
    )


class SystemPromptTaskResponse(BaseModel):
    """Response model for a system prompt task in assistant_config."""

    id: str = Field(..., description="System prompt task ID")
    title: str = Field(..., description="System prompt task title")
    content: str = Field(..., description="System prompt task content")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether this prompt is active")


class AssistantConfigResponse(BaseModel):
    """Response model for complex nested Assistant mode configuration."""

    enable_knowledge_assistant: bool = Field(
        ..., description="Enable knowledge assistant for multi-agent orchestration"
    )
    system_prompt_tasks: Optional[List[SystemPromptTaskResponse]] = Field(
        None, description="System prompt tasks for the assistant"
    )


# ============================================================================
# SYSTEM PROMPT MANAGEMENT MODELS (Phase 1 - Core CRUD)
# ============================================================================


class SystemPromptTaskManagementResponse(BaseModel):
    """Response model for a system prompt task (for management endpoints)."""

    id: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    tags: List[str]
    is_active: bool
    usage_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: int


class CreateSystemPromptRequest(BaseModel):
    """Request to create a new system prompt."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the system prompt"
    )
    system_prompt: str = Field(
        ...,
        min_length=10,
        description="The actual system prompt content (e.g., instructions for code review, summarization, etc.)",
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Description of what this prompt does"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags for organization (e.g., ['code-review', 'python'])"
    )


class UpdateSystemPromptRequest(BaseModel):
    """Request to update a system prompt."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Updated name"
    )
    system_prompt: Optional[str] = Field(
        None, min_length=10, description="Updated prompt content"
    )
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    is_active: Optional[bool] = Field(None, description="Updated active status")


class SelectSystemPromptRequest(BaseModel):
    """Request to select a system prompt for a conversation."""

    prompt_id: Optional[str] = Field(
        None, description="System prompt ID to select (None to deselect)"
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
        "enable_knowledge_assistant": boolean,
        "system_prompt_tasks": [...] (optional)
      },
      "tags": ["string"]
    }
    """
    try:
        # Convert request models to service dataclasses
        # Note: system_prompt is now part of assistant_config.system_prompt_tasks
        # (if provided in the request at all)

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
            answer_generation = AnswerGenerationConfig(provider=provider)

        # Build assistant_config if provided
        assistant_config = None
        if create_request.assistant_config:
            system_prompt_tasks = None
            if create_request.assistant_config.system_prompt_tasks:
                system_prompt_tasks = [
                    SystemPromptTask(
                        id="",  # Will be generated in __post_init__
                        user_id=current_user.id,
                        conversation_id="",  # Will be set after conversation creation
                        name=task.title,  # API uses 'title', SystemPromptTask uses 'name'
                        system_prompt=task.content,  # API uses 'content', SystemPromptTask uses 'system_prompt'
                        is_active=task.is_active,
                    )
                    for task in create_request.assistant_config.system_prompt_tasks
                ]
            assistant_config = AssistantConfig(
                enable_knowledge_assistant=create_request.assistant_config.enable_knowledge_assistant,
                system_prompt_tasks=system_prompt_tasks,
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

        # Determine agent type from assistant_config or legacy enable_knowledge_assistant
        if assistant_config:
            agent_type = "supervisor" if assistant_config.enable_knowledge_assistant else "rag"
        else:
            agent_type = "supervisor" if create_request.enable_knowledge_assistant else "rag"
        return {
            "success": True,
            "id": session_id,
            "name": create_request.name or f"Session {session_id[:8]}",
            "agent_type": agent_type,
            "enhancement_strategy": (
                create_request.enhancement.strategy if create_request.enhancement else None
            ),
            "message": "Conversation session created successfully",
        }

    except Exception as e:
        logger.error(f"Error creating conversation session: {e}", exc_info=True)
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
            update_doc["answer_generation"] = {"provider": provider}

        # Assistant configuration (complex nested structure)
        if config_request.assistant_config is not None:
            assistant_config_dict = {
                "enable_knowledge_assistant": config_request.assistant_config.enable_knowledge_assistant,
            }
            if config_request.assistant_config.system_prompt_tasks:
                assistant_config_dict["system_prompt_tasks"] = [
                    {
                        "title": task.title,
                        "content": task.content,
                        "is_active": task.is_active,
                    }
                    for task in config_request.assistant_config.system_prompt_tasks
                ]
            else:
                assistant_config_dict["system_prompt_tasks"] = None
            update_doc["assistant_config"] = assistant_config_dict

        if not update_doc:
            raise HTTPException(
                status_code=400, detail="No fields to update"
            )

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


# ============================================================================
# SYSTEM PROMPT TASKS MANAGEMENT ENDPOINTS (Phase 1 - Core CRUD)
# ============================================================================


@router.post("/{conversation_id}/system-prompts", status_code=status.HTTP_201_CREATED)
async def create_system_prompt(
    conversation_id: str,
    request: CreateSystemPromptRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new system prompt task for a conversation.

    This allows users to define reusable system prompts that can be applied to queries
    to provide custom instructions and context to the LLM.
    """
    try:
        prompt = conversation_history_service.create_system_prompt(
            user_id=current_user.id,
            conversation_id=conversation_id,
            name=request.name,
            system_prompt=request.system_prompt,
            description=request.description,
            tags=request.tags,
        )

        if not prompt:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or failed to create system prompt",
            )

        return {
            "success": True,
            "data": {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "system_prompt": prompt.system_prompt,
                "tags": prompt.tags,
                "is_active": prompt.is_active,
                "usage_count": prompt.usage_count,
                "version": prompt.version,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/system-prompts")
async def list_system_prompts(
    conversation_id: str,
    active_only: bool = Query(False, description="Return only active prompts"),
    current_user: User = Depends(get_current_user),
):
    """
    List all system prompts for a conversation.

    Returns a list of all available system prompts, optionally filtered to active only.
    """
    try:
        prompts = conversation_history_service.list_system_prompts(
            conversation_id=conversation_id,
            user_id=current_user.id,
            active_only=active_only,
        )

        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "tags": p.tags,
                    "is_active": p.is_active,
                    "usage_count": p.usage_count,
                    "version": p.version,
                }
                for p in prompts
            ],
            "total": len(prompts),
        }

    except Exception as e:
        logger.error(f"Error listing system prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/system-prompts/{prompt_id}")
async def get_system_prompt(
    conversation_id: str,
    prompt_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific system prompt by ID."""
    try:
        prompt = conversation_history_service.get_system_prompt(
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            user_id=current_user.id,
        )

        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")

        return {
            "success": True,
            "data": {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "system_prompt": prompt.system_prompt,
                "tags": prompt.tags,
                "is_active": prompt.is_active,
                "usage_count": prompt.usage_count,
                "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
                "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
                "version": prompt.version,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/system-prompts/{prompt_id}")
async def update_system_prompt(
    conversation_id: str,
    prompt_id: str,
    request: UpdateSystemPromptRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update a system prompt.

    Allows updating the prompt name, content, description, tags, and active status.
    """
    try:
        success = conversation_history_service.update_system_prompt(
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            user_id=current_user.id,
            name=request.name,
            system_prompt=request.system_prompt,
            description=request.description,
            tags=request.tags,
            is_active=request.is_active,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="System prompt not found or update failed",
            )

        # Fetch and return the updated prompt
        prompt = conversation_history_service.get_system_prompt(
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            user_id=current_user.id,
        )

        return {
            "success": True,
            "data": {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "system_prompt": prompt.system_prompt,
                "tags": prompt.tags,
                "is_active": prompt.is_active,
                "usage_count": prompt.usage_count,
                "version": prompt.version,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/system-prompts/{prompt_id}")
async def delete_system_prompt(
    conversation_id: str,
    prompt_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a system prompt."""
    try:
        success = conversation_history_service.delete_system_prompt(
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="System prompt not found")

        return {"success": True, "message": "System prompt deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}/system-prompts/{prompt_id}/select")
async def select_system_prompt(
    conversation_id: str,
    prompt_id: str,
    request: SelectSystemPromptRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Select (or deselect) a system prompt for the conversation.

    This sets the active system prompt that will be used for subsequent queries.
    Pass prompt_id as None in the request to deselect the current prompt.
    """
    try:
        success = conversation_history_service.select_system_prompt(
            conversation_id=conversation_id,
            prompt_id=request.prompt_id,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "message": f"System prompt {'selected' if request.prompt_id else 'deselected'} successfully",
            "selected_prompt_id": request.prompt_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
