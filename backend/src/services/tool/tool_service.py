"""
Tool Service.

This module provides business logic for tool management operations
including CRUD operations and MCP tool discovery.
"""

import traceback
from typing import List, Optional

from loguru import logger

from src.domain.tool import PromptBasedToolConfig, Tool, ToolType
from src.services.tool.dao.tool_dao import ToolDAO


class ToolService:
    """
    Service for managing user tools (prompt-based and MCP remote).

    This service provides business logic for tool management,
    including CRUD operations and MCP server discovery.
    """

    def __init__(self):
        """Initialize the tool service."""
        self.tool_dao = ToolDAO()

    # Tool Management Methods

    def create_tool(self, tool: Tool) -> Tool:
        """
        Create a new tool.

        Args:
            tool: Tool object to create

        Returns:
            Created tool object

        Raises:
            Exception: If creation fails
        """
        try:
            self.tool_dao.create_tool(tool)
            logger.info(
                f"Created tool '{tool.name}' (ID: {tool.id}) for user {tool.user_id}"
            )
            return tool
        except Exception as e:
            logger.error(f"Error creating tool: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_tool_by_id(self, tool_id: str, user_id: str) -> Optional[Tool]:
        """
        Get tool by ID (with user ownership check).

        Args:
            tool_id: Tool ID
            user_id: User ID for ownership verification

        Returns:
            Tool object if found and owned by user, None otherwise
        """
        return self.tool_dao.get_tool_by_id(tool_id, user_id)

    def get_user_tools(
        self, user_id: str, is_active: Optional[bool] = None
    ) -> List[Tool]:
        """
        Get all tools for a user.

        Args:
            user_id: User ID
            is_active: Optional filter by active status

        Returns:
            List of tools owned by user
        """
        tools = self.tool_dao.get_user_tools(user_id, is_active=is_active)
        logger.info(f"Retrieved {len(tools)} tools for user {user_id}")
        return tools

    def update_tool(self, tool_id: str, user_id: str, updates: dict) -> bool:
        """
        Update an existing tool.

        Args:
            tool_id: Tool ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            success = self.tool_dao.update_tool(tool_id, user_id, updates)
            if success:
                logger.info(f"User {user_id} updated tool {tool_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating tool {tool_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def delete_tool(self, tool_id: str, user_id: str) -> bool:
        """
        Delete a tool.

        Args:
            tool_id: Tool ID
            user_id: User ID for ownership verification

        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            success = self.tool_dao.delete_tool(tool_id, user_id)
            if success:
                logger.info(f"User {user_id} deleted tool {tool_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting tool {tool_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    # MCP Discovery

    async def discover_mcp_tools(
        self,
        server_url: str,
        auth_type: Optional[str] = None,
        auth_credentials: Optional[dict] = None,
    ) -> List[dict]:
        """
        Discover available tools from an MCP server using langchain-mcp-adapters.

        Args:
            server_url: MCP server URL
            auth_type: Authentication type (none, bearer, basic, api_key)
            auth_credentials: Authentication credentials dictionary

        Returns:
            List of discovered tool metadata

        Raises:
            Exception: If discovery fails
        """
        try:
            from src.agents.supervisor_agent.tools.tool_factory import ToolFactory
            from src.domain.tool import MCPServerConfig

            logger.info(f"Discovering MCP tools from {server_url}")

            # Create temporary MCPServerConfig for discovery
            temp_server = MCPServerConfig(
                id="",  # Temporary ID for discovery
                name="temp_discovery",
                server_url=server_url,
                auth_type=auth_type,
                auth_credentials=auth_credentials or {},
                user_id="",
            )

            # Use ToolFactory to discover tools (uses langchain-mcp-adapters)
            discovered_tools_raw = await ToolFactory.discover_mcp_tools(temp_server)

            # Add display_name for UI
            discovered_tools = []
            for tool_data in discovered_tools_raw:
                tool_data_with_display = {
                    **tool_data,
                    "display_name": tool_data["name"].replace("_", " ").title(),
                }
                discovered_tools.append(tool_data_with_display)

            logger.info(
                f"Successfully discovered {len(discovered_tools)} tools from {server_url}"
            )

            return discovered_tools

        except ImportError as e:
            logger.error(f"Required MCP libraries not installed: {e}")
            raise Exception(
                "MCP libraries required. Please install: pip install langchain-mcp-adapters"
            )
        except Exception as e:
            logger.error(f"Error discovering MCP tools from {server_url}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


# Singleton instance
_tool_service = None


def get_tool_service() -> ToolService:
    """
    Get or create the singleton ToolService instance.

    Returns:
        ToolService instance
    """
    global _tool_service
    if _tool_service is None:
        _tool_service = ToolService()
    return _tool_service
