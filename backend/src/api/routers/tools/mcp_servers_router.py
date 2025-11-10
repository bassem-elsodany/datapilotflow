"""
MCP Servers API Router

RESTful API for managing MCP server configurations.
Each server can provide multiple tools.
"""

import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.tool import MCPServerConfig
from src.domain.user import User
from src.services.tool import get_mcp_server_service, get_tool_service

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CreateMCPServerRequest(BaseModel):
    """Request model for creating an MCP server."""

    name: str = Field(..., description="Human-readable server name")
    server_url: str = Field(..., description="MCP server endpoint URL")
    server_type: str = Field(
        default="http", description="Server type (only 'http' supported)"
    )
    auth_type: Optional[str] = Field(
        None, description="Authentication type: 'none', 'bearer', 'basic', 'api_key'"
    )
    auth_credentials: Optional[dict] = Field(
        None, description="Authentication credentials"
    )
    is_active: bool = Field(default=True, description="Whether server is active")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")


class UpdateMCPServerRequest(BaseModel):
    """Request model for updating an MCP server."""

    name: Optional[str] = None
    server_url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_credentials: Optional[dict] = None
    is_active: Optional[bool] = None
    timeout: Optional[int] = None
    tags: Optional[List[str]] = None


class MCPServerResponse(BaseModel):
    """Response model for MCP server data."""

    id: str
    user_id: str
    name: str
    server_url: str
    server_type: str
    auth_type: Optional[str]
    auth_credentials: Optional[dict]
    is_active: bool
    timeout: int
    tags: List[str]
    created_at: str
    updated_at: str


class DiscoverToolsRequest(BaseModel):
    """Request model for discovering tools from an MCP server."""

    server_url: str
    server_type: str = "http"
    auth_type: Optional[str] = None
    auth_credentials: Optional[dict] = None
    timeout: int = 30


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def server_to_response(server: MCPServerConfig) -> MCPServerResponse:
    """Convert MCPServerConfig domain object to API response."""
    return MCPServerResponse(
        id=server.id,
        user_id=server.user_id,
        name=server.name,
        server_url=server.server_url,
        server_type=server.server_type,
        auth_type=server.auth_type,
        auth_credentials=server.auth_credentials,
        is_active=server.is_active,
        timeout=server.timeout,
        tags=server.tags,
        created_at=server.created_at.isoformat() if server.created_at else "",
        updated_at=server.updated_at.isoformat() if server.updated_at else "",
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    request: CreateMCPServerRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new MCP server configuration.

    Args:
        request: Server creation data
        current_user: Authenticated user

    Returns:
        Created server data
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        # Create server object (id will be assigned by MongoDB)
        server = MCPServerConfig(
            id="",  # Will be set by MongoDB _id
            user_id=user_id,
            name=request.name,
            server_url=request.server_url,
            server_type=request.server_type,
            auth_type=request.auth_type,
            auth_credentials=request.auth_credentials,
            is_active=request.is_active,
            timeout=request.timeout,
            tags=request.tags,
        )

        # Save via service
        mcp_server_service = get_mcp_server_service()
        created_server = mcp_server_service.create_server(server)

        return server_to_response(created_server)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating MCP server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create MCP server: {str(e)}",
        )


@router.get("", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
):
    """
    List all MCP servers for the authenticated user.

    Args:
        is_active: Optional filter by active status
        current_user: Authenticated user

    Returns:
        List of MCP servers
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()
        servers = mcp_server_service.get_user_servers(user_id, is_active=is_active)

        return [server_to_response(server) for server in servers]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP servers: {str(e)}",
        )


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific MCP server by ID.

    Args:
        server_id: Server ID
        current_user: Authenticated user

    Returns:
        Server data
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()
        server = mcp_server_service.get_server_by_id(server_id, user_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        return server_to_response(server)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MCP server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP server: {str(e)}",
        )


@router.put("/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str,
    request: UpdateMCPServerRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing MCP server.

    Args:
        server_id: Server ID
        request: Server update data
        current_user: Authenticated user

    Returns:
        Updated server data
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()

        # Check if server exists
        existing_server = mcp_server_service.get_server_by_id(server_id, user_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        # Build updates dictionary
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.server_url is not None:
            updates["server_url"] = request.server_url
        if request.auth_type is not None:
            updates["auth_type"] = request.auth_type
        if request.auth_credentials is not None:
            updates["auth_credentials"] = request.auth_credentials
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.timeout is not None:
            updates["timeout"] = request.timeout
        if request.tags is not None:
            updates["tags"] = request.tags

        # Perform update
        success = mcp_server_service.update_server(server_id, user_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update MCP server",
            )

        # Fetch updated server
        updated_server = mcp_server_service.get_server_by_id(server_id, user_id)

        return server_to_response(updated_server)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating MCP server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update MCP server: {str(e)}",
        )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete an MCP server.
    
    Cannot delete a server if it has associated tools.
    Delete or reassign the tools first.

    Args:
        server_id: Server ID
        current_user: Authenticated user
        
    Raises:
        HTTPException: 409 if server has related tools
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()
        tool_service = get_tool_service()
        
        # Check if server exists
        existing_server = mcp_server_service.get_server_by_id(server_id, user_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )
        
        # Check for related tools
        all_tools = tool_service.get_all_tools(user_id)
        related_tools = [
            tool for tool in all_tools 
            if tool.tool_type.value == 'mcp_remote' and tool.mcp_server_id == server_id
        ]
        
        if related_tools:
            tool_names = ', '.join([tool.display_name for tool in related_tools[:5]])
            if len(related_tools) > 5:
                tool_names += f' and {len(related_tools) - 5} more'
            
            logger.warning(
                f"User {user_id} attempted to delete MCP server {server_id} "
                f"with {len(related_tools)} related tool(s): {tool_names}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete MCP server '{existing_server.name}'. "
                       f"It has {len(related_tools)} tool(s) associated with it: {tool_names}. "
                       f"Please delete or reassign these tools first.",
            )
        
        # Safe to delete
        logger.info(f"User {user_id} deleting MCP server {server_id} ('{existing_server.name}')")
        success = mcp_server_service.delete_server(server_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MCP server {server_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {str(e)}",
        )


@router.post("/discover", response_model=List[dict])
async def discover_mcp_tools(
    request: DiscoverToolsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Discover available tools from an MCP server (without saving).

    This endpoint allows testing MCP server connectivity and previewing
    available tools before creating a server configuration.

    Args:
        request: MCP server connection details
        current_user: Authenticated user

    Returns:
        List of available tools from the MCP server
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        logger.info(f"User {user_id} requested MCP discovery for {request.server_url}")

        # Create temporary server config for discovery (ID not needed, will not be saved)
        temp_server = MCPServerConfig(
            id="",
            user_id=user_id,
            name="Discovery Test",
            server_url=request.server_url,
            server_type=request.server_type,
            auth_type=request.auth_type,
            auth_credentials=request.auth_credentials,
            timeout=request.timeout,
        )

        # Discover tools
        mcp_server_service = get_mcp_server_service()
        discovered_tools = await mcp_server_service.discover_tools_from_server(
            temp_server
        )

        return discovered_tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering MCP tools from {request.server_url}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover MCP tools: {str(e)}",
        )


@router.post("/{server_id}/discover", response_model=List[dict])
async def discover_from_existing_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Discover tools from an existing saved MCP server.

    This endpoint fetches tools from a server that has already been saved to the database.
    Use this when you want to refresh the tool list from an existing server.

    Args:
        server_id: ID of the saved MCP server
        current_user: Authenticated user

    Returns:
        List of discovered tools from the MCP server
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()

        # Get server config
        server = mcp_server_service.get_server_by_id(server_id, user_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        logger.info(f"User {user_id} discovering tools from saved server '{server.name}' ({server_id})")

        # Discover tools from server
        discovered_tools = await mcp_server_service.discover_tools_from_server(server)

        return discovered_tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering tools from MCP server {server_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover MCP tools: {str(e)}",
        )


@router.get("/{server_id}/tools", response_model=List[dict])
async def get_server_tools(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get live tools from an MCP server.

    Fetches current tool metadata (descriptions, schemas) directly from the
    MCP server at runtime. This ensures tool information is always fresh.

    Args:
        server_id: Server ID
        current_user: Authenticated user

    Returns:
        List of tools with current metadata from MCP server
    """
    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        mcp_server_service = get_mcp_server_service()

        # Get server config
        server = mcp_server_service.get_server_by_id(server_id, user_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        # Discover tools from server
        all_tools = await mcp_server_service.discover_tools_from_server(server)

        return all_tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tools from MCP server {server_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP server tools: {str(e)}",
        )
