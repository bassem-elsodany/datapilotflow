"""
Standalone Tools API Router

RESTful API for managing user tools (prompt-based and MCP remote).
Tools are user-level entities, not tied to conversations.
"""

import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.tool import PromptBasedToolConfig, Tool, ToolType
from src.domain.user import User
from src.services.tool import get_tool_service

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PromptConfigRequest(BaseModel):
    """Request model for prompt-based tool configuration."""

    system_prompt: str
    llm_provider_id: Optional[str] = None
    llm_model_name: Optional[str] = None
    temperature: float = 0.7
    instructions: Optional[str] = None


class CreateToolRequest(BaseModel):
    """Request model for creating a tool."""

    name: str = Field(..., description="Internal tool name (used by LLM)")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Tool description for LLM")
    tool_type: str = Field(..., description="'prompt_based' or 'mcp_remote'")
    is_active: bool = True
    # For prompt_based tools
    prompt_config: Optional[PromptConfigRequest] = None
    # For mcp_remote tools
    mcp_server_id: Optional[str] = Field(
        None, description="MCP server ID (for mcp_remote tools)"
    )
    mcp_tool_name: Optional[str] = Field(
        None, description="Tool name on MCP server (for mcp_remote tools)"
    )
    tags: List[str] = Field(default_factory=list)


class UpdateToolRequest(BaseModel):
    """Request model for updating a tool."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    prompt_config: Optional[PromptConfigRequest] = None
    mcp_server_id: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    tags: Optional[List[str]] = None


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: str
    name: str
    display_name: str
    description: str
    tool_type: str
    is_active: bool
    prompt_config: Optional[dict] = None
    mcp_server_id: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    tags: List[str]
    created_at: str
    updated_at: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def tool_to_response(tool: Tool) -> ToolResponse:
    """Convert Tool domain object to API response."""
    response_dict = {
        "id": tool.id,
        "name": tool.name,
        "display_name": tool.display_name,
        "description": tool.description,
        "tool_type": tool.tool_type.value,
        "is_active": tool.is_active,
        "tags": tool.tags,
        "created_at": tool.created_at.isoformat() if tool.created_at else "",
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else "",
    }

    if tool.prompt_config:
        response_dict["prompt_config"] = {
            "system_prompt": tool.prompt_config.system_prompt,
            "llm_provider_id": tool.prompt_config.llm_provider_id,
            "llm_model_name": tool.prompt_config.llm_model_name,
            "temperature": tool.prompt_config.temperature,
            "instructions": tool.prompt_config.instructions,
        }

    if tool.mcp_server_id:
        response_dict["mcp_server_id"] = tool.mcp_server_id
    if tool.mcp_tool_name:
        response_dict["mcp_tool_name"] = tool.mcp_tool_name

    return ToolResponse(**response_dict)


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    request: CreateToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tool.

    Args:
        request: Tool creation data
        user_data: Authenticated user data

    Returns:
        Created tool data

    Raises:
        HTTPException: If validation fails or creation errors occur
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        # Validate tool type
        try:
            tool_type = ToolType(request.tool_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tool_type. Must be 'prompt_based' or 'mcp_remote'",
            )

        # Validate configuration based on type
        prompt_config = None

        if tool_type == ToolType.PROMPT_BASED:
            if not request.prompt_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="prompt_config is required for prompt_based tools",
                )
            prompt_config = PromptBasedToolConfig(
                system_prompt=request.prompt_config.system_prompt,
                llm_provider_id=request.prompt_config.llm_provider_id,
                llm_model_name=request.prompt_config.llm_model_name,
                temperature=request.prompt_config.temperature,
                instructions=request.prompt_config.instructions,
            )

        elif tool_type == ToolType.MCP_REMOTE:
            if not (request.mcp_server_id and request.mcp_tool_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="mcp_server_id and mcp_tool_name are required for mcp_remote tools",
                )

        # Create tool object
        tool = Tool(
            id=str(uuid.uuid4()),
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            tool_type=tool_type,
            user_id=user_id,
            is_active=request.is_active,
            prompt_config=prompt_config,
            mcp_server_id=request.mcp_server_id,
            mcp_tool_name=request.mcp_tool_name,
            tags=request.tags,
        )

        # Save via service
        tool_service = get_tool_service()
        created_tool = tool_service.create_tool(tool)

        return tool_to_response(created_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tool: {str(e)}",
        )


@router.get("", response_model=List[ToolResponse])
async def list_tools(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
):
    """
    List all tools for the authenticated user.

    Args:
        is_active: Optional filter by active status
        user_data: Authenticated user data

    Returns:
        List of tools
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        tools = tool_service.get_user_tools(user_id, is_active=is_active)

        return [tool_to_response(tool) for tool in tools]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}",
        )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific tool by ID.

    Args:
        tool_id: Tool ID
        user_data: Authenticated user data

    Returns:
        Tool data

    Raises:
        HTTPException: If tool not found
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        tool = tool_service.get_tool_by_id(tool_id, user_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

        return tool_to_response(tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}",
        )


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing tool.

    Args:
        tool_id: Tool ID
        request: Tool update data
        user_data: Authenticated user data

    Returns:
        Updated tool data

    Raises:
        HTTPException: If tool not found or update fails
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()

        # Check if tool exists
        existing_tool = tool_service.get_tool_by_id(tool_id, user_id)
        if not existing_tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

        # Build updates dictionary
        updates = {}
        
        # For MCP_REMOTE tools, only allow updating is_active and tags
        if existing_tool.tool_type == ToolType.MCP_REMOTE:
            if request.is_active is not None:
                updates["is_active"] = request.is_active
            if request.tags is not None:
                updates["tags"] = request.tags
            
            logger.info(f"User {user_id} updating MCP remote tool {tool_id} (is_active={request.is_active}, tags={request.tags})")
        
        # For PROMPT_BASED tools, allow full updates
        elif existing_tool.tool_type == ToolType.PROMPT_BASED:
            if request.name is not None:
                updates["name"] = request.name
            if request.display_name is not None:
                updates["display_name"] = request.display_name
            if request.description is not None:
                updates["description"] = request.description
            if request.is_active is not None:
                updates["is_active"] = request.is_active
            if request.tags is not None:
                updates["tags"] = request.tags
            
            if request.prompt_config:
                updates["prompt_config"] = {
                    "system_prompt": request.prompt_config.system_prompt,
                    "llm_provider_id": request.prompt_config.llm_provider_id,
                    "llm_model_name": request.prompt_config.llm_model_name,
                    "temperature": request.prompt_config.temperature,
                    "instructions": request.prompt_config.instructions,
                }

        # Perform update
        success = tool_service.update_tool(tool_id, user_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tool",
            )

        # Fetch updated tool
        updated_tool = tool_service.get_tool_by_id(tool_id, user_id)

        return tool_to_response(updated_tool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tool: {str(e)}",
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a tool.

    Args:
        tool_id: Tool ID
        user_data: Authenticated user data

    Raises:
        HTTPException: If tool not found or deletion fails
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        tool_service = get_tool_service()
        success = tool_service.delete_tool(tool_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with ID {tool_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tool: {str(e)}",
        )


# Note: MCP tool discovery is now handled by the mcp_servers_router
# via the GET /mcp-servers/{server_id}/discover endpoint
