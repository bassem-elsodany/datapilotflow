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
    SystemPromptTask,
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
        description="Query enhancement strategy (none, multi_query, hyde, decomposition, augmented)",
    )
    collection_name: Optional[str] = Field(
        "LongTermMemory", description="Vector DB collection name"
    )
    enable_reranking: bool = Field(
        True, description="Enable document reranking/judging for better relevance"
    )
    relevance_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Relevance score threshold for filtering documents (0.0-1.0). Documents below this threshold are filtered out.",
    )
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID (Cohere/Voyage AI)"
    )
    reranker_model_name: Optional[str] = Field(None, description="Reranker model name")
    enable_llm_generation: bool = Field(
        False,
        description="Enable LLM answer generation (False = raw results by default, True = generated)",
    )
    top_k: int = Field(
        5,
        ge=5,
        le=30,
        description="Number of documents to retrieve from vector database",
    )
    enable_knowledge_assistant: bool = Field(
        True,
        description="Enable Knowledge Assistant for RAG→Task workflow (True = orchestration, False = RAG only)",
    )
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
    relevance_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Relevance score threshold for filtering documents (0.0-1.0)",
    )
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID"
    )
    reranker_model_name: Optional[str] = Field(None, description="Reranker model name")
    enable_llm_generation: Optional[bool] = Field(
        None, description="Enable LLM answer generation"
    )
    top_k: Optional[int] = Field(
        None,
        ge=5,
        le=30,
        description="Number of documents to retrieve from vector database",
    )
    tags: Optional[List[str]] = Field(None, description="Tags for organizing")
    enable_knowledge_assistant: Optional[bool] = Field(
        None, description="Enable Knowledge Assistant (multi-agent supervisor with intent routing)"
    )


# ============================================================================
# SYSTEM PROMPT MANAGEMENT MODELS (Phase 1 - Core CRUD)
# ============================================================================


class SystemPromptTaskResponse(BaseModel):
    """Response model for a system prompt task."""

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
            relevance_threshold=create_request.relevance_threshold,
            reranker_provider_id=create_request.reranker_provider_id,
            reranker_model_name=create_request.reranker_model_name,
            enable_llm_generation=create_request.enable_llm_generation,
            top_k=create_request.top_k,
            enable_knowledge_assistant=create_request.enable_knowledge_assistant,
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
            "enable_llm_generation": create_request.enable_llm_generation,
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
            "enable_reranking": getattr(session, "enable_reranking", False),
            "reranker_provider_id": getattr(session, "reranker_provider_id", None),
            "reranker_model_name": getattr(session, "reranker_model_name", None),
            "enable_llm_generation": getattr(session, "enable_llm_generation", True),
            "top_k": getattr(session, "top_k", None),
            "enable_knowledge_assistant": getattr(session, "enable_knowledge_assistant", True),
        }

        logger.info(
            f"  session_data['enable_llm_generation']: {session_data['enable_llm_generation']}"
        )
        logger.info(
            f"  session_data['enable_knowledge_assistant']: {session_data['enable_knowledge_assistant']}"
        )

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


@router.put("/{conversation_id}", status_code=status.HTTP_200_OK)
async def update_conversation_session(
    conversation_id: str,
    config_request: UpdateSessionConfigRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update conversation session (RESTful endpoint).
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
            relevance_threshold=config_request.relevance_threshold,
            reranker_provider_id=config_request.reranker_provider_id,
            reranker_model_name=config_request.reranker_model_name,
            enable_llm_generation=config_request.enable_llm_generation,
            top_k=config_request.top_k,
            tags=config_request.tags,
            enable_knowledge_assistant=config_request.enable_knowledge_assistant,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found or no changes made",
            )

        return {
            "success": True,
            "id": conversation_id,
            "message": "Conversation updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
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
