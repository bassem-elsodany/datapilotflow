"""
Agent Router

API endpoints for managing AI agents (reusable agent configurations).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.api.dependencies.permissions import require_permission
from datapilotflow.domain.agent.models import Agent, AgentType, EnhancementStrategy
from datapilotflow.domain.conversation.models import (
    AssistantConfig,
    ProviderConfig,
    RerankerConfig,
    VectorDatabaseConfig,
)
from datapilotflow.domain.user.user import User
from datapilotflow.services.agent.agent_service import get_agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ProviderConfigRequest(BaseModel):
    """Provider configuration request model."""

    id: str
    model_name: str


class VectorDatabaseConfigRequest(BaseModel):
    """Vector database configuration request model."""

    collection_name: str = "LongTermMemory"
    top_k: int = 5
    # Embedding provider - must match the vector database collection's embedding provider
    embedding_provider: Optional[ProviderConfigRequest] = None
    # Vector dimension - must match the collection's vector dimension
    vector_dimension: int = 1536


class RerankerConfigRequest(BaseModel):
    """Reranker configuration request model."""

    enabled: bool = False
    provider: Optional[ProviderConfigRequest] = None
    relevance_threshold: float = 0.5


class AssistantConfigRequest(BaseModel):
    """Assistant configuration request model."""

    enabled: bool
    tools: Optional[List[str]] = None
    instructions: Optional[str] = None


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""

    name: str = Field(..., min_length=1, max_length=100)
    agent_type: str = Field(..., pattern="^(rag|assistant)$")
    description: Optional[str] = Field(None, max_length=500)

    # Primary LLM Provider (used by both RAG and Assistant modes)
    llm_provider: Optional[ProviderConfigRequest] = None

    # RAG-specific configuration
    enhancement_strategy: str = EnhancementStrategy.NATIVE.value  # Query enhancement strategy
    vector_database: Optional[VectorDatabaseConfigRequest] = None
    reranker: Optional[RerankerConfigRequest] = None
    is_llm_generation_enabled: bool = False  # Whether LLM answer generation is enabled

    # Assistant-specific configuration
    assistant_config: Optional[AssistantConfigRequest] = None

    tags: Optional[List[str]] = None


class UpdateAgentRequest(BaseModel):
    """Request model for updating an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    # Primary LLM Provider (used by both RAG and Assistant modes)
    llm_provider: Optional[ProviderConfigRequest] = None

    # RAG-specific configuration
    enhancement_strategy: Optional[str] = None  # Query enhancement strategy
    vector_database: Optional[VectorDatabaseConfigRequest] = None
    reranker: Optional[RerankerConfigRequest] = None
    is_llm_generation_enabled: Optional[bool] = None  # Whether LLM answer generation is enabled

    # Assistant-specific configuration
    assistant_config: Optional[AssistantConfigRequest] = None

    tags: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Response model for a message."""

    id: str
    role: str
    content: str
    timestamp: str
    message_index: int


class ConversationSummary(BaseModel):
    """Summary of a conversation (without messages)."""

    id: str
    name: Optional[str]
    description: Optional[str]
    created_at: str
    last_updated: str
    last_message_at: Optional[str]
    message_count: int


class ConversationDetail(ConversationSummary):
    """Detailed conversation (with messages)."""

    messages: List[MessageResponse] = []


class ExpandedToolResponse(BaseModel):
    """Expanded tool object for assistant agents."""

    id: str
    name: str
    display_name: str
    description: str
    tool_type: str
    is_active: bool
    tags: List[str] = []


class ExpandedProviderResponse(BaseModel):
    """Expanded provider object for RAG agent configs."""

    id: str
    name: Optional[str] = None
    model_name: str
    endpoint: Optional[str] = None


class AgentResponse(BaseModel):
    """Response model for a single agent."""

    id: str
    name: str
    agent_type: str
    description: Optional[str]
    created_at: str
    updated_at: str
    tags: List[str]

    # Primary LLM Provider
    llm_provider: Optional[dict] = None

    # Configuration (type-specific)
    enhancement_strategy: str = ""  # Query enhancement strategy
    vector_database: Optional[dict] = None
    reranker: Optional[dict] = None
    is_llm_generation_enabled: bool = False  # Whether LLM answer generation is enabled
    assistant_config: Optional[dict] = None

    # Expandable: conversations
    conversation_count: Optional[int] = None
    conversations: Optional[List[ConversationSummary]] = None


class AgentListResponse(BaseModel):
    """Response model for listing agents."""

    success: bool
    agents: List[AgentResponse]
    total_count: int


class CreateAgentResponse(BaseModel):
    """Response model for creating an agent."""

    success: bool
    id: str
    message: str


class UpdateAgentResponse(BaseModel):
    """Response model for updating an agent."""

    success: bool
    id: str
    message: str


class DeleteAgentResponse(BaseModel):
    """Response model for deleting an agent."""

    success: bool
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def convert_provider_config(
    provider: Optional[ProviderConfigRequest],
) -> Optional[ProviderConfig]:
    """Convert request provider config to domain model."""
    if not provider:
        return None
    return ProviderConfig(id=provider.id, model_name=provider.model_name)


def _expand_provider(provider_id: str, model_name: str, user_id: str) -> dict:
    """Expand a provider ID to full provider object."""
    try:
        from datapilotflow.services.model_provider.model_provider_service import (
            get_model_provider_service,
        )

        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(provider_id, user_id)
        if provider:
            return {
                "id": provider_id,
                "name": provider.name,
                "model_name": model_name,
                "endpoint": provider.endpoint,
            }
    except Exception as e:
        logger.error(f"Error expanding provider {provider_id}: {e}")

    # Fallback to basic info
    return {"id": provider_id, "model_name": model_name}


def _expand_tools(tool_ids: List[str], user_id: str) -> List[dict]:
    """Expand tool IDs to full tool objects."""
    from datapilotflow.services.tool import get_tool_service

    tool_service = get_tool_service()
    expanded_tools = []

    for tool_id in tool_ids:
        try:
            result = tool_service.get_tool_by_id(tool_id, user_id)
            if result:
                _id, tool = result
                expanded_tools.append(
                    {
                        "id": _id,
                        "name": tool.name,
                        "display_name": tool.display_name,
                        "description": tool.description,
                        "tool_type": tool.tool_type.value,
                        "is_active": tool.is_active,
                        "tags": tool.tags or [],
                    }
                )
            else:
                # Fallback to ID only if not found
                expanded_tools.append(
                    {
                        "id": tool_id,
                        "name": tool_id,
                        "display_name": tool_id,
                        "description": "",
                        "tool_type": "unknown",
                        "is_active": False,
                        "tags": [],
                    }
                )
        except Exception as e:
            logger.error(f"Error expanding tool {tool_id}: {e}")
            expanded_tools.append(
                {
                    "id": tool_id,
                    "name": tool_id,
                    "display_name": tool_id,
                    "description": "",
                    "tool_type": "unknown",
                    "is_active": False,
                    "tags": [],
                }
            )

    return expanded_tools


def serialize_agent(
    agent: Agent,
    expand: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AgentResponse:
    """
    Convert Agent domain model to API response.

    Args:
        agent: Agent domain model
        expand: Comma-separated list of fields to expand (tools, enhancement, reranker, answer_generation, conversations, conversations.messages)
        user_id: User ID for fetching conversations (required if expand is set)
    """
    from dataclasses import asdict

    # Parse expand options
    expand_options = set()
    if expand:
        expand_options = {e.strip().lower() for e in expand.split(",")}

    response_data = {
        "id": agent._id,
        "name": agent.name,
        "agent_type": agent.agent_type.value,
        "description": agent.description,
        "created_at": agent.created_at.isoformat(),
        "updated_at": agent.updated_at.isoformat(),
        "tags": agent.tags or [],
        "llm_provider": asdict(agent.llm_provider) if agent.llm_provider else None,
    }

    # Expand llm_provider if requested
    if "llm_provider" in expand_options and agent.llm_provider and user_id:
        response_data["llm_provider"] = _expand_provider(
            agent.llm_provider.id,
            agent.llm_provider.model_name,
            user_id,
        )

    # Add RAG configuration (for both RAG and ASSISTANT agents with Knowledge Expert)
    # Enhancement strategy (simplified - just a string)
    response_data["enhancement_strategy"] = (
        agent.enhancement_strategy.value
        if isinstance(agent.enhancement_strategy, EnhancementStrategy)
        else agent.enhancement_strategy
    )

    # Vector database config with optional embedding provider expansion
    if agent.vector_database:
        vector_db_data = asdict(agent.vector_database)
        # Convert embedding_provider ProviderConfig to dict
        if agent.vector_database.embedding_provider:
            vector_db_data["embedding_provider"] = asdict(agent.vector_database.embedding_provider)
        response_data["vector_database"] = vector_db_data
    else:
        response_data["vector_database"] = None

    # Reranker config
    if agent.reranker:
        reranker_data = asdict(agent.reranker)
        if "reranker" in expand_options and agent.reranker.provider and user_id:
            reranker_data["provider"] = _expand_provider(
                agent.reranker.provider.id,
                agent.reranker.provider.model_name,
                user_id,
            )
        response_data["reranker"] = reranker_data
    else:
        response_data["reranker"] = None

    # LLM generation enabled flag (simplified - just a boolean)
    response_data["is_llm_generation_enabled"] = agent.is_llm_generation_enabled

    # Add assistant config (for ASSISTANT agents)
    if agent.agent_type == AgentType.ASSISTANT:
        # Assistant config with optional tool expansion
        if agent.assistant_config:
            assistant_config_data = asdict(agent.assistant_config)

            # Expand tools if requested
            if "tools" in expand_options and user_id:
                tool_ids = agent.assistant_config.tools or []
                if tool_ids:
                    assistant_config_data["tools"] = _expand_tools(tool_ids, user_id)
                else:
                    assistant_config_data["tools"] = []

            response_data["assistant_config"] = assistant_config_data
        else:
            response_data["assistant_config"] = None

    # Always get conversation count if user_id is provided
    conversations = []
    conv_history_service = None
    if user_id:
        from datapilotflow.services.conversation.conversation_history_service import (
            conversation_history_service,
        )

        conv_history_service = conversation_history_service

        conversations = conv_history_service.get_user_conversations(
            user_id=user_id, agent_id=agent._id
        )
        response_data["conversation_count"] = len(conversations)

    # Handle expand parameter for conversations
    expand_conversations = (
        "conversations" in expand_options or "conversations.messages" in expand_options
    )
    if expand_conversations and user_id and conversations and conv_history_service:
        include_messages = "conversations.messages" in expand_options
        conv_list = []

        for conv in conversations:
            conv_data = {
                "id": conv._id,
                "name": conv.name,
                "description": conv.description,
                "created_at": conv.created_at.isoformat(),
                "last_updated": conv.last_updated.isoformat(),
                "last_message_at": (
                    conv.last_message_at.isoformat() if conv.last_message_at else None
                ),
                "message_count": conv_history_service.get_message_count(conv._id),
            }

            if include_messages:
                messages = conv_history_service.get_conversation_messages(conv._id)
                conv_data["messages"] = [
                    {
                        "id": msg._id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "message_index": msg.message_index,
                    }
                    for msg in messages
                ]

            conv_list.append(conv_data)

        response_data["conversations"] = conv_list
    else:
        # Just get the count without full conversation details
        from datapilotflow.services.agent.agent_service import get_agent_service

        agent_service = get_agent_service()
        response_data["conversation_count"] = (
            agent_service.count_conversations_using_agent(agent._id)
        )

    return AgentResponse(**response_data)


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("", response_model=CreateAgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    current_user: User = Depends(require_permission("conversation:manage")),
):
    """
    Create a new agent.

    An agent is a reusable configuration that can be used across multiple conversations.
    """
    try:
        logger.info(
            f"Creating agent '{request.name}' of type '{request.agent_type}' for user {current_user.id}"
        )

        agent_service = get_agent_service()

        # Parse agent type
        agent_type = AgentType(request.agent_type)

        # Convert request models to domain models
        vector_database = None
        if request.vector_database:
            vector_database = VectorDatabaseConfig(
                collection_name=request.vector_database.collection_name,
                top_k=request.vector_database.top_k,
                embedding_provider=convert_provider_config(request.vector_database.embedding_provider),
                vector_dimension=request.vector_database.vector_dimension,
            )

        reranker = None
        if request.reranker:
            reranker = RerankerConfig(
                enabled=request.reranker.enabled,
                provider=convert_provider_config(request.reranker.provider),
                relevance_threshold=request.reranker.relevance_threshold,
            )

        assistant_config = None
        if request.assistant_config:
            assistant_config = AssistantConfig(
                enabled=request.assistant_config.enabled,
                tools=request.assistant_config.tools,
                instructions=request.assistant_config.instructions,
            )

        # Convert llm_provider
        llm_provider = convert_provider_config(request.llm_provider)

        # Convert enhancement_strategy string to enum
        enhancement_strategy = EnhancementStrategy.NATIVE
        if request.enhancement_strategy:
            try:
                enhancement_strategy = EnhancementStrategy(request.enhancement_strategy)
            except ValueError:
                raise ValueError(
                    f"Invalid enhancement strategy: {request.enhancement_strategy}. "
                    f"Valid values are: {', '.join([s.value for s in EnhancementStrategy])}"
                )

        # Create agent
        agent_id = agent_service.create_agent(
            user_id=current_user.id,
            name=request.name,
            agent_type=agent_type,
            description=request.description,
            llm_provider=llm_provider,
            enhancement_strategy=enhancement_strategy,
            vector_database=vector_database,
            reranker=reranker,
            is_llm_generation_enabled=request.is_llm_generation_enabled,
            assistant_config=assistant_config,
            tags=request.tags,
        )

        return CreateAgentResponse(
            success=True,
            id=agent_id,
            message=f"Agent '{request.name}' created successfully",
        )

    except ValueError as e:
        logger.error(f"Validation error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.get("", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = Query(None, pattern="^(rag|assistant)$"),
    expand: Optional[str] = Query(
        None,
        description="Comma-separated list of fields to expand: tools, enhancement, reranker, answer_generation, conversations, conversations.messages",
    ),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("conversation:read")),
):
    """
    List all agents for the current user.

    Optional filters:
    - agent_type: Filter by agent type (rag or assistant)
    - expand: Comma-separated list of fields to expand
        - "tools": Expand tool IDs to full tool objects (assistant agents)
        - "enhancement": Return enhancement configuration (uses agent's primary llm_provider)
        - "reranker": Expand reranker provider to full provider object (RAG agents)
        - "answer_generation": Return answer generation configuration (uses agent's primary llm_provider)
        - "conversations": Include conversation summaries for each agent
        - "conversations.messages": Include full conversation details with messages
    - limit: Maximum number of agents to return
    - offset: Number of agents to skip
    """
    try:
        logger.info(
            f"Listing agents for user {current_user.id} (type={agent_type}, expand={expand}, limit={limit}, offset={offset})"
        )

        agent_service = get_agent_service()

        # Parse agent type filter
        agent_type_filter = AgentType(agent_type) if agent_type else None

        # Get agents
        agents = agent_service.get_user_agents(
            user_id=current_user.id,
            agent_type=agent_type_filter,
            limit=limit,
            offset=offset,
        )

        # Serialize agents with optional expansion
        agent_responses = [
            serialize_agent(agent, expand=expand, user_id=current_user.id)
            for agent in agents
        ]

        return AgentListResponse(
            success=True,
            agents=agent_responses,
            total_count=len(agent_responses),
        )

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    expand: Optional[str] = Query(
        None,
        description="Comma-separated list of fields to expand: tools, enhancement, reranker, answer_generation, llm_provider, conversations, conversations.messages",
    ),
    current_user: User = Depends(require_permission("conversation:read")),
):
    """
    Get a specific agent by ID.

    Optional:
    - expand: Comma-separated list of fields to expand
        - "tools": Expand tool IDs to full tool objects
        - "enhancement": Return enhancement configuration (uses agent's primary llm_provider)
        - "reranker": Expand reranker provider to full provider object
        - "answer_generation": Return answer generation configuration (uses agent's primary llm_provider)
        - "llm_provider": Expand LLM provider to full provider object
        - "conversations": Include conversation summaries
        - "conversations.messages": Include full conversation details with messages
    """
    try:
        logger.info(
            f"Fetching agent {agent_id} for user {current_user.id} (expand={expand})"
        )

        agent_service = get_agent_service()
        agent = agent_service.get_agent(agent_id, current_user.id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return serialize_agent(agent, expand=expand, user_id=current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent")


@router.put("/{agent_id}", response_model=UpdateAgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    current_user: User = Depends(require_permission("conversation:manage")),
):
    """Update an agent's configuration."""
    try:
        logger.info(f"Updating agent {agent_id} for user {current_user.id}")

        agent_service = get_agent_service()

        # Check if agent exists
        agent = agent_service.get_agent(agent_id, current_user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Convert request models to domain models
        vector_database = None
        if request.vector_database:
            vector_database = VectorDatabaseConfig(
                collection_name=request.vector_database.collection_name,
                top_k=request.vector_database.top_k,
                embedding_provider=convert_provider_config(request.vector_database.embedding_provider),
                vector_dimension=request.vector_database.vector_dimension,
            )

        reranker = None
        if request.reranker:
            reranker = RerankerConfig(
                enabled=request.reranker.enabled,
                provider=convert_provider_config(request.reranker.provider),
                relevance_threshold=request.reranker.relevance_threshold,
            )

        assistant_config = None
        if request.assistant_config:
            assistant_config = AssistantConfig(
                enabled=request.assistant_config.enabled,
                tools=request.assistant_config.tools,
                instructions=request.assistant_config.instructions,
            )

        # Convert llm_provider
        llm_provider = convert_provider_config(request.llm_provider)

        # Convert enhancement_strategy string to enum
        enhancement_strategy = None
        if request.enhancement_strategy is not None:
            try:
                enhancement_strategy = EnhancementStrategy(request.enhancement_strategy)
            except ValueError:
                raise ValueError(
                    f"Invalid enhancement strategy: {request.enhancement_strategy}. "
                    f"Valid values are: {', '.join([s.value for s in EnhancementStrategy])}"
                )

        # Update agent
        success = agent_service.update_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            llm_provider=llm_provider,
            enhancement_strategy=enhancement_strategy,
            vector_database=vector_database,
            reranker=reranker,
            is_llm_generation_enabled=request.is_llm_generation_enabled,
            assistant_config=assistant_config,
            tags=request.tags,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update agent")

        return UpdateAgentResponse(
            success=True,
            id=agent_id,
            message="Agent updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/{agent_id}", response_model=DeleteAgentResponse)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(require_permission("conversation:manage")),
):
    """
    Delete an agent.

    Note: Cannot delete an agent that is in use by conversations.
    """
    try:
        logger.info(f"Deleting agent {agent_id} for user {current_user.id}")

        agent_service = get_agent_service()

        # Check if agent exists
        agent = agent_service.get_agent(agent_id, current_user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check if agent is in use
        conv_count = agent_service.count_conversations_using_agent(agent_id)
        if conv_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete agent. It is used by {conv_count} conversation(s). Delete the conversations first.",
            )

        # Delete agent
        success = agent_service.delete_agent(agent_id, current_user.id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete agent")

        return DeleteAgentResponse(
            success=True,
            message="Agent deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")


@router.get("/{agent_id}/conversations")
async def get_agent_conversations(
    agent_id: str,
    current_user: User = Depends(require_permission("conversation:read")),
):
    """Get all conversations using this agent."""
    try:
        logger.info(f"Fetching conversations for agent {agent_id}")

        agent_service = get_agent_service()

        # Check if agent exists
        agent = agent_service.get_agent(agent_id, current_user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Import here to avoid circular dependency
        from datapilotflow.services.conversation.conversation_history_service import (
            conversation_history_service,
        )

        # Get conversations using this agent
        conversations = list(
            conversation_history_service.collection.find(
                {"agent_id": agent_id, "user_id": current_user.id}
            ).sort("last_updated", -1)
        )

        # Format response
        conversation_list = []
        for conv in conversations:
            conversation_list.append(
                {
                    "id": str(conv["_id"]),
                    "name": conv.get("name"),
                    "description": conv.get("description"),
                    "created_at": conv["created_at"].isoformat(),
                    "last_updated": conv["last_updated"].isoformat(),
                    "message_count": len(conv.get("messages", [])),
                }
            )

        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "conversations": conversation_list,
            "total_count": len(conversation_list),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversations for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch agent conversations"
        )
