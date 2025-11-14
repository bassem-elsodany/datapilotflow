"""
Conversation Tools Router - Tool Management REST Endpoints.

This module provides endpoints for managing assistant agent tools dynamically.
Users can create, update, delete, and query tools configured for conversations.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.conversation import (
    AssistantTool,
    MCPRemoteToolConfig,
    PromptBasedToolConfig,
    ToolType,
)
from src.domain.user import User
from src.services.conversation.conversation_history_service import (
    conversation_history_service,
)

# Create router
router = APIRouter(prefix="/conversations/tools", tags=["Conversation Tools"])


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# ============================================================================


class PromptBasedToolConfigRequest(BaseModel):
    """Request model for prompt-based tool configuration."""

    system_prompt: str = Field(
        ..., description="System prompt that defines tool behavior"
    )
    llm_provider_id: Optional[str] = Field(
        None, description="Optional specific LLM provider ID"
    )
    llm_model_name: Optional[str] = Field(
        None, description="Optional specific LLM model name"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    instructions: Optional[str] = Field(
        None, description="Additional usage instructions"
    )


class MCPRemoteToolConfigRequest(BaseModel):
    """Request model for MCP remote tool configuration."""

    server_url: str = Field(..., description="MCP server endpoint URL")
    tool_name: str = Field(..., description="Specific tool name on MCP server")
    server_type: str = Field("http", description="Server type: http or stdio")
    auth_type: Optional[str] = Field(
        None, description="Authentication type: bearer, api_key, or basic"
    )
    auth_credentials: Optional[Dict[str, str]] = Field(
        None, description="Authentication credentials"
    )
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    tool_schema: Optional[Dict] = Field(
        None, description="Cached tool schema from MCP server"
    )


class CreateToolRequest(BaseModel):
    """Request model for creating a new tool."""

    conversation_id: str = Field(..., description="Conversation ID to attach tool to")
    name: str = Field(..., description="Tool name (used by LLM to invoke)")
    display_name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Tool description for LLM understanding")
    tool_type: ToolType = Field(
        ..., description="Tool type: prompt_based or mcp_remote"
    )
    is_active: bool = Field(True, description="Whether tool is enabled")
    prompt_config: Optional[PromptBasedToolConfigRequest] = Field(
        None, description="Config for prompt-based tools"
    )
    mcp_config: Optional[MCPRemoteToolConfigRequest] = Field(
        None, description="Config for MCP remote tools"
    )
    tags: Optional[List[str]] = Field(None, description="Tags for organization")


class UpdateToolRequest(BaseModel):
    """Request model for updating an existing tool."""

    name: Optional[str] = Field(None, description="Tool name")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Tool description")
    is_active: Optional[bool] = Field(None, description="Whether tool is enabled")
    prompt_config: Optional[PromptBasedToolConfigRequest] = Field(
        None, description="Prompt config"
    )
    mcp_config: Optional[MCPRemoteToolConfigRequest] = Field(
        None, description="MCP config"
    )
    tags: Optional[List[str]] = Field(None, description="Tags")


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: str
    name: str
    display_name: str
    description: str
    tool_type: str
    is_active: bool
    prompt_config: Optional[Dict] = None
    mcp_config: Optional[Dict] = None
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @staticmethod
    def from_domain(tool: AssistantTool) -> "ToolResponse":
        """Convert domain model to response model."""
        from dataclasses import asdict

        return ToolResponse(
            id=tool.id,
            name=tool.name,
            display_name=tool.display_name,
            description=tool.description,
            tool_type=tool.tool_type.value,
            is_active=tool.is_active,
            prompt_config=asdict(tool.prompt_config) if tool.prompt_config else None,
            mcp_config=asdict(tool.mcp_config) if tool.mcp_config else None,
            tags=tool.tags or [],
            created_at=tool.created_at.isoformat() if tool.created_at else None,
            updated_at=tool.updated_at.isoformat() if tool.updated_at else None,
        )


class MCPDiscoverRequest(BaseModel):
    """Request model for MCP tool discovery."""

    server_url: str = Field(..., description="MCP server URL")
    server_type: str = Field("http", description="Server type: http or stdio")
    auth_type: Optional[str] = Field(None, description="Authentication type")
    auth_credentials: Optional[Dict[str, str]] = Field(
        None, description="Auth credentials"
    )
    timeout: int = Field(30, ge=1, le=300, description="Request timeout")


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get(
    "/",
    response_model=List[ToolResponse],
    status_code=status.HTTP_200_OK,
    summary="List tools for a conversation",
    description="Retrieve all tools configured for a specific conversation",
)
async def list_tools(
    conversation_id: str = Query(..., description="Conversation ID to query tools for"),
    current_user: User = Depends(get_current_user),
):
    """
    List all tools configured for a conversation.

    Args:
        conversation_id: The conversation ID to query tools for
        current_user: Authenticated user

    Returns:
        List of tools configured for the conversation

    Raises:
        404: Conversation not found
        403: User not authorized to access conversation
    """
    try:
        logger.info(
            f"Listing tools for conversation {conversation_id} by user {current_user.id}"
        )

        # Get conversation
        conversation = conversation_history_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Check ownership
        if conversation.user_id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to access conversation {conversation_id} owned by {conversation.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        # Get tools from assistant_config
        tools = []
        if conversation.assistant_config and conversation.assistant_config.tools:
            tools = conversation.assistant_config.tools

        logger.info(f"Found {len(tools)} tools for conversation {conversation_id}")

        return [ToolResponse.from_domain(tool) for tool in tools]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tools for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}",
        )


@router.post(
    "/",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tool",
    description="Create a new tool and attach it to a conversation",
)
async def create_tool(
    tool_request: CreateToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tool for a conversation.

    Args:
        tool_request: Tool configuration
        current_user: Authenticated user

    Returns:
        Created tool data

    Raises:
        404: Conversation not found
        403: User not authorized
        400: Invalid tool configuration
    """
    try:
        logger.info(
            f"Creating tool '{tool_request.name}' for conversation {tool_request.conversation_id} by user {current_user.id}"
        )

        # Get conversation
        conversation = conversation_history_service.get_conversation(
            tool_request.conversation_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {tool_request.conversation_id} not found",
            )

        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this conversation",
            )

        # Validate tool configuration based on type
        if (
            tool_request.tool_type == ToolType.PROMPT_BASED
            and not tool_request.prompt_config
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="prompt_config required for PROMPT_BASED tools",
            )
        if (
            tool_request.tool_type == ToolType.MCP_REMOTE
            and not tool_request.mcp_config
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="mcp_config required for MCP_REMOTE tools",
            )

        # Convert request to domain model
        import uuid
        from datetime import datetime

        prompt_config = None
        if tool_request.prompt_config:
            prompt_config = PromptBasedToolConfig(
                system_prompt=tool_request.prompt_config.system_prompt,
                llm_provider_id=tool_request.prompt_config.llm_provider_id,
                llm_model_name=tool_request.prompt_config.llm_model_name,
                temperature=tool_request.prompt_config.temperature,
                instructions=tool_request.prompt_config.instructions,
            )

        mcp_config = None
        if tool_request.mcp_config:
            mcp_config = MCPRemoteToolConfig(
                server_url=tool_request.mcp_config.server_url,
                tool_name=tool_request.mcp_config.tool_name,
                server_type=tool_request.mcp_config.server_type,
                auth_type=tool_request.mcp_config.auth_type,
                auth_credentials=tool_request.mcp_config.auth_credentials,
                timeout=tool_request.mcp_config.timeout,
                tool_schema=tool_request.mcp_config.tool_schema,
            )

        new_tool = AssistantTool(
            id=str(uuid.uuid4()),
            name=tool_request.name,
            display_name=tool_request.display_name,
            description=tool_request.description,
            tool_type=tool_request.tool_type,
            is_active=tool_request.is_active,
            prompt_config=prompt_config,
            mcp_config=mcp_config,
            tags=tool_request.tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Add tool to conversation's assistant_config
        if not conversation.assistant_config:
            from src.domain.conversation import AssistantConfig

            conversation.assistant_config = AssistantConfig(
                enabled=True, tools=[new_tool]
            )
        else:
            if not conversation.assistant_config.tools:
                conversation.assistant_config.tools = []
            conversation.assistant_config.tools.append(new_tool)

        # Update conversation in database
        assistant_config_dict: Dict[str, Any] = {
            "enabled": conversation.assistant_config.enabled,
        }
        if conversation.assistant_config.tools:
            assistant_config_dict["tools"] = conversation.assistant_config.tools
        if conversation.assistant_config.tool_instructions:
            assistant_config_dict["tool_instructions"] = conversation.assistant_config.tool_instructions

        conversation_history_service.collection.update_one(
            {"_id": conversation._id},
            {"$set": {"assistant_config": assistant_config_dict}},
        )

        logger.info(
            f"Successfully created tool '{new_tool.name}' with ID {new_tool.id}"
        )

        return ToolResponse.from_domain(new_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tool: {str(e)}",
        )


@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific tool",
    description="Retrieve a specific tool by ID",
)
async def get_tool(
    tool_id: str,
    conversation_id: str = Query(..., description="Conversation ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific tool by ID.

    Args:
        tool_id: Tool ID
        conversation_id: Conversation ID
        current_user: Authenticated user

    Returns:
        Tool data

    Raises:
        404: Tool or conversation not found
        403: User not authorized
    """
    try:
        logger.info(f"Getting tool {tool_id} from conversation {conversation_id}")

        # Get conversation
        conversation = conversation_history_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        # Find tool
        tool = None
        if conversation.assistant_config and conversation.assistant_config.tools:
            for t in conversation.assistant_config.tools:
                if t.id == tool_id:
                    tool = t
                    break

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found in conversation",
            )

        return ToolResponse.from_domain(tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}",
        )


@router.put(
    "/{tool_id}",
    response_model=ToolResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tool",
    description="Update an existing tool configuration",
)
async def update_tool(
    tool_id: str,
    conversation_id: str = Query(..., description="Conversation ID"),
    tool_update: UpdateToolRequest = ...,
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing tool.

    Args:
        tool_id: Tool ID to update
        conversation_id: Conversation ID
        tool_update: Fields to update
        current_user: Authenticated user

    Returns:
        Updated tool data

    Raises:
        404: Tool or conversation not found
        403: User not authorized
    """
    try:
        logger.info(f"Updating tool {tool_id} in conversation {conversation_id}")

        # Get conversation
        conversation = conversation_history_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this conversation",
            )

        # Find and update tool
        tool_found = False
        updated_tool = None
        if conversation.assistant_config and conversation.assistant_config.tools:
            for i, tool in enumerate(conversation.assistant_config.tools):
                if tool.id == tool_id:
                    # Update fields if provided
                    if tool_update.name is not None:
                        tool.name = tool_update.name
                    if tool_update.display_name is not None:
                        tool.display_name = tool_update.display_name
                    if tool_update.description is not None:
                        tool.description = tool_update.description
                    if tool_update.is_active is not None:
                        tool.is_active = tool_update.is_active
                    if tool_update.tags is not None:
                        tool.tags = tool_update.tags

                    # Update prompt_config if provided
                    if tool_update.prompt_config is not None:
                        tool.prompt_config = PromptBasedToolConfig(
                            system_prompt=tool_update.prompt_config.system_prompt,
                            llm_provider_id=tool_update.prompt_config.llm_provider_id,
                            llm_model_name=tool_update.prompt_config.llm_model_name,
                            temperature=tool_update.prompt_config.temperature,
                            instructions=tool_update.prompt_config.instructions,
                        )

                    # Update mcp_config if provided
                    if tool_update.mcp_config is not None:
                        tool.mcp_config = MCPRemoteToolConfig(
                            server_url=tool_update.mcp_config.server_url,
                            tool_name=tool_update.mcp_config.tool_name,
                            server_type=tool_update.mcp_config.server_type,
                            auth_type=tool_update.mcp_config.auth_type,
                            auth_credentials=tool_update.mcp_config.auth_credentials,
                            timeout=tool_update.mcp_config.timeout,
                            tool_schema=tool_update.mcp_config.tool_schema,
                        )

                    # Update timestamp
                    from datetime import datetime

                    tool.updated_at = datetime.utcnow()

                    updated_tool = tool
                    tool_found = True
                    break

        if not tool_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found in conversation",
            )

        # Update conversation in database
        if conversation.assistant_config:
            assistant_config_dict: Dict[str, Any] = {
                "enabled": conversation.assistant_config.enabled,
            }
            if conversation.assistant_config.tools:
                assistant_config_dict["tools"] = conversation.assistant_config.tools
            if conversation.assistant_config.tool_instructions:
                assistant_config_dict["tool_instructions"] = conversation.assistant_config.tool_instructions

            conversation_history_service.collection.update_one(
                {"_id": conversation._id},
                {"$set": {"assistant_config": assistant_config_dict}},
            )

        logger.info(f"Successfully updated tool {tool_id}")

        return ToolResponse.from_domain(updated_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tool: {str(e)}",
        )


@router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tool",
    description="Delete a tool from a conversation",
)
async def delete_tool(
    tool_id: str,
    conversation_id: str = Query(..., description="Conversation ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a tool from a conversation.

    Args:
        tool_id: Tool ID to delete
        conversation_id: Conversation ID
        current_user: Authenticated user

    Raises:
        404: Tool or conversation not found
        403: User not authorized
    """
    try:
        logger.info(f"Deleting tool {tool_id} from conversation {conversation_id}")

        # Get conversation
        conversation = conversation_history_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this conversation",
            )

        # Find and remove tool
        tool_found = False
        if conversation.assistant_config and conversation.assistant_config.tools:
            original_count = len(conversation.assistant_config.tools)
            conversation.assistant_config.tools = [
                tool
                for tool in conversation.assistant_config.tools
                if tool.id != tool_id
            ]
            tool_found = len(conversation.assistant_config.tools) < original_count

        if not tool_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found in conversation",
            )

        # Update conversation in database
        if conversation.assistant_config:
            assistant_config_dict: Dict[str, Any] = {
                "enabled": conversation.assistant_config.enabled,
            }
            if conversation.assistant_config.tools:
                assistant_config_dict["tools"] = conversation.assistant_config.tools
            else:
                assistant_config_dict["tools"] = None
            if conversation.assistant_config.tool_instructions:
                assistant_config_dict["tool_instructions"] = conversation.assistant_config.tool_instructions

            conversation_history_service.collection.update_one(
                {"_id": conversation._id},
                {"$set": {"assistant_config": assistant_config_dict}},
            )

        logger.info(f"Successfully deleted tool {tool_id}")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tool: {str(e)}",
        )


@router.post(
    "/mcp/discover",
    response_model=List[Dict],
    status_code=status.HTTP_200_OK,
    summary="Discover MCP tools",
    description="Discover available tools from an MCP server",
)
async def discover_mcp_tools(
    discover_request: MCPDiscoverRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Discover available tools from an MCP server.

    This endpoint allows users to test MCP server connections and see what tools
    are available before adding them to a conversation.

    Args:
        discover_request: MCP server connection details
        current_user: Authenticated user

    Returns:
        List of available tools from the MCP server

    Raises:
        400: Invalid MCP server configuration
        500: Failed to connect to MCP server
    """
    try:
        logger.info(f"Discovering tools from MCP server: {discover_request.server_url}")

        # Create MCP config
        from src.agents.assistant_agent.tools.tool_factory import ToolFactory

        mcp_config = MCPRemoteToolConfig(
            server_url=discover_request.server_url,
            tool_name="",  # Not needed for discovery
            server_type=discover_request.server_type,
            auth_type=discover_request.auth_type,
            auth_credentials=discover_request.auth_credentials,
            timeout=discover_request.timeout,
        )

        # Discover tools
        tools = await ToolFactory.discover_mcp_tools(mcp_config)

        logger.info(f"Discovered {len(tools)} tools from MCP server")

        return tools

    except Exception as e:
        logger.error(f"Error discovering MCP tools: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover MCP tools: {str(e)}",
        )
