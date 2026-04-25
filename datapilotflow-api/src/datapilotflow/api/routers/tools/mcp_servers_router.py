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

from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.api.dependencies.permissions import require_permission
from datapilotflow.domain.tool import MCPServerConfig
from datapilotflow.domain.user import User
from datapilotflow.services.tool import get_mcp_server_service, get_tool_service

router = APIRouter()


def extract_root_cause(exc: Exception) -> str:
    """
    Extract a meaningful error message from an exception.

    Handles ExceptionGroup (Python 3.11+) by unwrapping nested exceptions
    to find the actual root cause error message.

    Args:
        exc: The exception to extract the root cause from

    Returns:
        A human-readable error message describing the root cause
    """
    # Handle ExceptionGroup / BaseExceptionGroup
    if isinstance(exc, BaseExceptionGroup):
        # Get all nested exceptions
        exceptions = exc.exceptions
        root_causes = []

        for nested_exc in exceptions:
            # Recursively extract from nested groups
            if isinstance(nested_exc, BaseExceptionGroup):
                root_causes.append(extract_root_cause(nested_exc))
            else:
                # Try to get the most meaningful error message
                error_msg = _get_exception_message(nested_exc)
                if error_msg:
                    root_causes.append(error_msg)

        if root_causes:
            # Return unique root causes
            unique_causes = list(dict.fromkeys(root_causes))
            return "; ".join(unique_causes)

    # For regular exceptions
    return _get_exception_message(exc)


def _get_exception_message(exc: Exception) -> str:
    """
    Get a meaningful error message from a single exception.

    Handles common exception types and extracts user-friendly messages.

    Args:
        exc: The exception to extract the message from

    Returns:
        A human-readable error message
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    # Common connection/network errors - provide user-friendly messages
    if "ConnectError" in exc_type or "ConnectionError" in exc_type:
        if "nodename nor servname provided" in exc_msg or "Name or service not known" in exc_msg:
            return "Cannot resolve server hostname. Please check the URL is correct."
        if "Connection refused" in exc_msg:
            return "Connection refused. The server may be down or the port may be incorrect."
        if "timed out" in exc_msg.lower() or "timeout" in exc_msg.lower():
            return "Connection timed out. The server may be unreachable or slow to respond."
        return f"Connection error: {exc_msg}"

    if "TimeoutError" in exc_type or "timeout" in exc_msg.lower():
        return "Request timed out. The server may be unreachable or slow to respond."

    if "SSLError" in exc_type or "SSL" in exc_msg:
        return f"SSL/TLS error: {exc_msg}. Check if the server uses HTTPS and has valid certificates."

    if "AuthenticationError" in exc_type or "401" in exc_msg or "Unauthorized" in exc_msg:
        return "Authentication failed. Please check your credentials."

    if "PermissionError" in exc_type or "403" in exc_msg or "Forbidden" in exc_msg:
        return "Permission denied. Your credentials may not have access to this server."

    if "404" in exc_msg or "Not Found" in exc_msg:
        return "MCP endpoint not found. Please verify the server URL is correct."

    # For other exceptions, return the type and message
    if exc_msg:
        return f"{exc_type}: {exc_msg}"
    return exc_type


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


def server_to_response(_id: str, server: MCPServerConfig) -> MCPServerResponse:
    """Convert (_id, MCPServerConfig) to API response."""
    return MCPServerResponse(
        id=_id,  # Use MongoDB _id
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
    current_user: User = Depends(require_permission("tools:manage")),
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

        # Create server object (without id - MongoDB will generate _id)
        server = MCPServerConfig(
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
        _id, created_server = mcp_server_service.create_server(server)

        return server_to_response(_id, created_server)

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
    current_user: User = Depends(require_permission("tools:read")),
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

        return [server_to_response(_id, server) for _id, server in servers]

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
    current_user: User = Depends(require_permission("tools:read")),
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
        result = mcp_server_service.get_server_by_id(server_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        _id, server = result
        return server_to_response(_id, server)

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
    current_user: User = Depends(require_permission("tools:manage")),
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
        result = mcp_server_service.get_server_by_id(server_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found after update",
            )

        _id, updated_server = result
        return server_to_response(_id, updated_server)

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
    current_user: User = Depends(require_permission("tools:manage")),
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
        result = mcp_server_service.get_server_by_id(server_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        _id, existing_server = result

        # Check for related tools
        all_tools = tool_service.get_user_tools(user_id)
        related_tools = [
            tool
            for _, tool in all_tools
            if tool.tool_type.value == "mcp_remote" and tool.mcp_server_id == server_id
        ]

        if related_tools:
            tool_names = ", ".join([tool.display_name for tool in related_tools[:5]])
            if len(related_tools) > 5:
                tool_names += f" and {len(related_tools) - 5} more"

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
        logger.info(
            f"User {user_id} deleting MCP server {server_id} ('{existing_server.name}')"
        )
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
    current_user: User = Depends(require_permission("tools:manage")),
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

        # Create temporary server config for discovery (will not be saved)
        temp_server = MCPServerConfig(
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
        # Extract meaningful error message from exception (including ExceptionGroup)
        error_message = extract_root_cause(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover MCP tools: {error_message}",
        )


@router.post("/{server_id}/discover", response_model=List[dict])
async def discover_from_existing_server(
    server_id: str,
    current_user: User = Depends(require_permission("tools:manage")),
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
        result = mcp_server_service.get_server_by_id(server_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        _id, server = result
        logger.info(
            f"User {user_id} discovering tools from saved server '{server.name}' ({server_id})"
        )

        # Discover tools from server
        discovered_tools = await mcp_server_service.discover_tools_from_server(server)

        return discovered_tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering tools from MCP server {server_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Extract meaningful error message from exception (including ExceptionGroup)
        error_message = extract_root_cause(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover MCP tools: {error_message}",
        )


@router.get("/{server_id}/tools", response_model=List[dict])
async def get_server_tools(
    server_id: str,
    current_user: User = Depends(require_permission("tools:read")),
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
        result = mcp_server_service.get_server_by_id(server_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with ID {server_id} not found",
            )

        _id, server = result
        # Discover tools from server
        all_tools = await mcp_server_service.discover_tools_from_server(server)

        return all_tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tools from MCP server {server_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Extract meaningful error message from exception (including ExceptionGroup)
        error_message = extract_root_cause(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP server tools: {error_message}",
        )
