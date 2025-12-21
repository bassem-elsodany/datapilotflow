"""
MCP Server Service.

This module provides business logic for MCP server management operations
including CRUD operations and runtime tool discovery.
"""

import traceback
from typing import List, Optional

from loguru import logger

from datapilotflow.domain.tool import MCPServerConfig
from datapilotflow.infrastructure.dao.tool import MCPServerDAO


class MCPServerService:
    """
    Service for managing MCP servers.

    This service provides business logic for MCP server management,
    including CRUD operations and integration with tool discovery.
    """

    def __init__(self):
        """Initialize the MCP server service."""
        self.mcp_server_dao = MCPServerDAO()

    # Server Management Methods

    def create_server(self, server: MCPServerConfig) -> tuple[str, MCPServerConfig]:
        """
        Create a new MCP server configuration.

        Args:
            server: MCPServerConfig object to create

        Returns:
            Tuple of (_id, MCPServerConfig)

        Raises:
            Exception: If creation fails
        """
        try:
            _id = self.mcp_server_dao.create_server(server)
            logger.info(
                f"Created MCP server '{server.name}' (_id: {_id}) for user {server.user_id}"
            )
            return (_id, server)
        except Exception as e:
            logger.error(f"Error creating MCP server: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_server_by_id(
        self, server_id: str, user_id: str
    ) -> Optional[tuple[str, MCPServerConfig]]:
        """
        Get MCP server by _id (with user ownership check).

        Args:
            server_id: MongoDB _id as string
            user_id: User ID for ownership verification

        Returns:
            Tuple of (_id, MCPServerConfig) if found and owned by user, None otherwise
        """
        return self.mcp_server_dao.get_server_by_id(server_id, user_id)

    def get_user_servers(
        self, user_id: str, is_active: Optional[bool] = None
    ) -> List[tuple[str, MCPServerConfig]]:
        """
        Get all MCP servers for a user.

        Args:
            user_id: User ID
            is_active: Optional filter by active status

        Returns:
            List of tuples: (_id, MCPServerConfig)
        """
        servers = self.mcp_server_dao.get_user_servers(user_id, is_active=is_active)
        logger.info(f"Retrieved {len(servers)} MCP servers for user {user_id}")
        return servers

    def update_server(self, server_id: str, user_id: str, updates: dict) -> bool:
        """
        Update an existing MCP server.

        Args:
            server_id: Server ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            success = self.mcp_server_dao.update_server(server_id, user_id, updates)
            if success:
                logger.info(f"User {user_id} updated MCP server {server_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating MCP server {server_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def delete_server(self, server_id: str, user_id: str) -> bool:
        """
        Delete an MCP server.

        Args:
            server_id: Server ID
            user_id: User ID for ownership verification

        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            success = self.mcp_server_dao.delete_server(server_id, user_id)
            if success:
                logger.info(f"User {user_id} deleted MCP server {server_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting MCP server {server_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    # Tool Discovery

    async def discover_tools_from_server(self, server: MCPServerConfig) -> List[dict]:
        """
        Discover available tools from an MCP server at runtime.

        This fetches LIVE tool metadata (descriptions, schemas) from the MCP server.
        This ensures tool information is always fresh and up-to-date.

        Uses langchain-mcp-adapters for native MCP integration.

        Args:
            server: MCPServerConfig with connection details

        Returns:
            List of discovered tool metadata (name, description, schema)

        Raises:
            Exception: If discovery fails
        """
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            logger.info(
                f"Discovering tools from MCP server '{server.name}' ({server.server_url})"
            )

            # Build auth headers
            headers = {}
            if server.auth_type and server.auth_credentials:
                if server.auth_type == "bearer":
                    token = server.auth_credentials.get(
                        "token"
                    ) or server.auth_credentials.get("bearer_token")
                    if token:
                        headers["Authorization"] = f"Bearer {token.strip()}"
                elif server.auth_type == "api_key":
                    api_key = server.auth_credentials.get("api_key")
                    header_name = server.auth_credentials.get(
                        "header_name", "X-API-Key"
                    )
                    if api_key:
                        headers[header_name] = api_key.strip()

            # Connect to MCP server
            # Use server name as temp ID for discovery
            temp_server_id = f"discovery_{server.name}"
            server_config: dict = {
                temp_server_id: {
                    "transport": "streamable_http",
                    "url": server.server_url,
                }
            }
            if headers:
                server_config[temp_server_id]["headers"] = headers

            # Discover tools
            client = MultiServerMCPClient(server_config)  # type: ignore
            all_tools = await client.get_tools()

            # Convert to tool metadata
            discovered_tools = []
            for tool in all_tools:
                # Extract schema - handle both dict and Pydantic model
                schema = {}
                if hasattr(tool, "args_schema") and tool.args_schema:
                    if isinstance(tool.args_schema, dict):
                        schema = tool.args_schema
                    elif hasattr(tool.args_schema, "schema"):
                        schema = tool.args_schema.schema()

                tool_data = {
                    "name": tool.name,
                    "description": tool.description or "",
                    "display_name": tool.name.replace("_", " ").title(),
                    "schema": schema,
                }
                discovered_tools.append(tool_data)

            logger.info(
                f"Successfully discovered {len(discovered_tools)} tools from server '{server.name}'"
            )

            return discovered_tools

        except ImportError as e:
            logger.error(f"Required MCP libraries not installed: {e}")
            raise Exception(
                "MCP libraries required. Please install: pip install langchain-mcp-adapters"
            )
        except Exception as e:
            logger.error(
                f"Error discovering tools from MCP server '{server.name}': {e}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


# Singleton instance
_mcp_server_service = None


def get_mcp_server_service() -> MCPServerService:
    """
    Get or create the singleton MCPServerService instance.

    Returns:
        MCPServerService instance
    """
    global _mcp_server_service
    if _mcp_server_service is None:
        _mcp_server_service = MCPServerService()
    return _mcp_server_service
