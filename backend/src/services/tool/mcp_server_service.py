"""
MCP Server Service.

This module provides business logic for MCP server management operations
including CRUD operations and runtime tool discovery.
"""

import traceback
from typing import List, Optional

from loguru import logger

from src.domain.tool import MCPServerConfig
from src.services.tool.dao.mcp_server_dao import MCPServerDAO


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

    def create_server(self, server: MCPServerConfig) -> MCPServerConfig:
        """
        Create a new MCP server configuration.

        Args:
            server: MCPServerConfig object to create

        Returns:
            Created MCPServerConfig object

        Raises:
            Exception: If creation fails
        """
        try:
            self.mcp_server_dao.create_server(server)
            logger.info(
                f"Created MCP server '{server.name}' (ID: {server.id}) for user {server.user_id}"
            )
            return server
        except Exception as e:
            logger.error(f"Error creating MCP server: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_server_by_id(
        self, server_id: str, user_id: str
    ) -> Optional[MCPServerConfig]:
        """
        Get MCP server by ID (with user ownership check).

        Args:
            server_id: Server ID
            user_id: User ID for ownership verification

        Returns:
            MCPServerConfig object if found and owned by user, None otherwise
        """
        return self.mcp_server_dao.get_server_by_id(server_id, user_id)

    def get_user_servers(
        self, user_id: str, is_active: Optional[bool] = None
    ) -> List[MCPServerConfig]:
        """
        Get all MCP servers for a user.

        Args:
            user_id: User ID
            is_active: Optional filter by active status

        Returns:
            List of MCPServerConfig objects owned by user
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
            from src.agents.supervisor_agent.tools.tool_factory import ToolFactory

            logger.info(
                f"Discovering tools from MCP server '{server.name}' ({server.server_url})"
            )

            # Use ToolFactory to discover tools (uses langchain-mcp-adapters)
            discovered_tools_raw = await ToolFactory.discover_mcp_tools(server)

            # Add display_name for UI
            discovered_tools = []
            for tool_data in discovered_tools_raw:
                tool_data_with_display = {
                    **tool_data,
                    "display_name": tool_data["name"].replace("_", " ").title(),
                }
                discovered_tools.append(tool_data_with_display)

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
