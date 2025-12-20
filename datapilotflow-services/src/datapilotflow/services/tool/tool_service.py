"""
Tool Service.

This module provides business logic for tool management operations
including CRUD operations and MCP tool discovery.
"""

import traceback
from typing import List, Optional

from loguru import logger

from datapilotflow.domain.tool import PromptBasedToolConfig, Tool, ToolType
from datapilotflow.services.tool.dao.tool_dao import ToolDAO


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

    def create_tool(self, tool: Tool) -> tuple[str, Tool]:
        """
        Create a new tool.

        Args:
            tool: Tool object to create

        Returns:
            Tuple of (_id, Tool)

        Raises:
            Exception: If creation fails
        """
        try:
            _id = self.tool_dao.create_tool(tool)
            logger.info(
                f"Created tool '{tool.name}' (_id: {_id}) for user {tool.user_id}"
            )
            return (_id, tool)
        except Exception as e:
            logger.error(f"Error creating tool: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_tool_by_id(self, tool_id: str, user_id: str) -> Optional[tuple[str, Tool]]:
        """
        Get tool by _id (with user ownership check).

        Args:
            tool_id: MongoDB _id as string
            user_id: User ID for ownership verification

        Returns:
            Tuple of (_id, Tool) if found and owned by user, None otherwise
        """
        return self.tool_dao.get_tool_by_id(tool_id, user_id)

    def get_user_tools(
        self, user_id: str, is_active: Optional[bool] = None
    ) -> List[tuple[str, Tool]]:
        """
        Get all tools for a user.

        Args:
            user_id: User ID
            is_active: Optional filter by active status

        Returns:
            List of tuples: (_id, Tool)
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
            from langchain_mcp_adapters.client import MultiServerMCPClient

            logger.info(f"Discovering MCP tools from {server_url}")

            # Build auth headers
            headers = {}
            if auth_type and auth_credentials:
                if auth_type == "bearer":
                    token = auth_credentials.get("token") or auth_credentials.get(
                        "bearer_token"
                    )
                    if token:
                        headers["Authorization"] = f"Bearer {token.strip()}"
                elif auth_type == "api_key":
                    api_key = auth_credentials.get("api_key")
                    header_name = auth_credentials.get("header_name", "X-API-Key")
                    if api_key:
                        headers[header_name] = api_key.strip()

            # Connect to MCP server
            server_config: dict = {
                "discovery_server": {
                    "transport": "streamable_http",
                    "url": server_url,
                }
            }
            if headers:
                server_config["discovery_server"]["headers"] = headers

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
