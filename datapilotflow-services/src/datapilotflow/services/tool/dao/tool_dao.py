"""
Tool DAO - Data Access Object for Tool management.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger
from pymongo import ASCENDING

from datapilotflow.domain.tool import Tool, ToolType
from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class ToolDAO(MongoClientWrapper[Tool]):
    """Data Access Object for tool management."""

    def __init__(self):
        super().__init__(model=Tool, collection_name="mcp_tools")

        # Create indexes for efficient querying (using MongoDB's native _id)
        self.collection.create_index([("user_id", ASCENDING)])
        self.collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
        self.collection.create_index([("user_id", ASCENDING), ("tool_type", ASCENDING)])
        
        # Drop the old 'id' index if it exists (cleanup from old schema)
        try:
            self.collection.drop_index("id_1")
            logger.info("Dropped old 'id_1' index (now using native _id)")
        except Exception:
            pass  # Index doesn't exist, that's fine

        logger.info("ToolDAO initialized with MongoDB collection 'mcp_tools'")

    def create_tool(self, tool: Tool) -> str:
        """
        Create a new tool.

        Args:
            tool: Tool object to create

        Returns:
            str: The created tool's _id (MongoDB ObjectId as string)
        """
        # Convert model to dict (MongoDB generates _id automatically)
        tool_dict = {
            "name": tool.name,
            "display_name": tool.display_name,
            "description": tool.description,
            "tool_type": tool.tool_type.value,
            "user_id": tool.user_id,
            "is_active": tool.is_active,
            "tags": tool.tags,
            "created_at": tool.created_at or datetime.utcnow(),
            "updated_at": tool.updated_at or datetime.utcnow(),
        }

        # Add type-specific configuration
        if tool.prompt_config:
            tool_dict["prompt_config"] = {
                "system_prompt": tool.prompt_config.system_prompt,
                "llm_provider_id": tool.prompt_config.llm_provider_id,
                "llm_model_name": tool.prompt_config.llm_model_name,
                "temperature": tool.prompt_config.temperature,
                "instructions": tool.prompt_config.instructions,
            }

        # For MCP_REMOTE tools, store server reference and tool name
        if tool.mcp_server_id:
            tool_dict["mcp_server_id"] = tool.mcp_server_id
        if tool.mcp_tool_name:
            tool_dict["mcp_tool_name"] = tool.mcp_tool_name

        result = self.collection.insert_one(tool_dict)
        tool_id = str(result.inserted_id)
        logger.info(f"Created tool '{tool.name}' with _id: {tool_id}")
        return tool_id

    def get_tool_by_id(self, tool_id: str, user_id: str) -> Optional[tuple[str, Tool]]:
        """
        Get a tool by its _id.

        Args:
            tool_id: MongoDB _id as string
            user_id: User ID (for ownership validation)

        Returns:
            Tuple of (_id, Tool) or None if not found
        """
        tool_dict = self.collection.find_one({"_id": ObjectId(tool_id), "user_id": user_id})
        if not tool_dict:
            return None

        _id = str(tool_dict["_id"])
        tool = self._dict_to_tool(tool_dict)
        return (_id, tool)

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
        query = {"user_id": user_id}
        if is_active is not None:
            query["is_active"] = is_active

        tools = []
        for tool_dict in self.collection.find(query):
            _id = str(tool_dict["_id"])
            tool = self._dict_to_tool(tool_dict)
            tools.append((_id, tool))

        logger.info(f"Retrieved {len(tools)} tools for user {user_id}")
        return tools

    def update_tool(self, tool_id: str, user_id: str, updates: dict) -> bool:
        """
        Update a tool.

        Args:
            tool_id: MongoDB _id as string
            user_id: User ID (for ownership validation)
            updates: Dictionary of fields to update

        Returns:
            bool: True if updated successfully
        """
        updates["updated_at"] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": ObjectId(tool_id), "user_id": user_id}, {"$set": updates}
        )

        if result.modified_count > 0:
            logger.info(f"Updated tool {tool_id}")
            return True
        else:
            logger.warning(f"Tool {tool_id} not found or no changes made")
            return False

    def delete_tool(self, tool_id: str, user_id: str) -> bool:
        """
        Delete a tool.

        Args:
            tool_id: MongoDB _id as string
            user_id: User ID (for ownership validation)

        Returns:
            bool: True if deleted successfully
        """
        result = self.collection.delete_one({"_id": ObjectId(tool_id), "user_id": user_id})

        if result.deleted_count > 0:
            logger.info(f"Deleted tool {tool_id}")
            return True
        else:
            logger.warning(f"Tool {tool_id} not found")
            return False

    def _dict_to_tool(self, tool_dict: dict) -> Tool:
        """Convert database dictionary to Tool object (without _id)."""
        from datapilotflow.domain.tool import PromptBasedToolConfig, Tool, ToolType

        prompt_config = None
        if tool_dict.get("prompt_config"):
            pc = tool_dict["prompt_config"]
            prompt_config = PromptBasedToolConfig(
                system_prompt=pc.get("system_prompt", ""),
                llm_provider_id=pc.get("llm_provider_id"),
                llm_model_name=pc.get("llm_model_name"),
                temperature=pc.get("temperature", 0.7),
                instructions=pc.get("instructions"),
            )

        return Tool(
            name=tool_dict.get("name", ""),
            display_name=tool_dict.get("display_name", ""),
            description=tool_dict.get("description", ""),
            tool_type=ToolType(tool_dict.get("tool_type", "prompt_based")),
            user_id=tool_dict.get("user_id", ""),
            is_active=tool_dict.get("is_active", True),
            prompt_config=prompt_config,
            mcp_server_id=tool_dict.get("mcp_server_id"),
            mcp_tool_name=tool_dict.get("mcp_tool_name"),
            tags=tool_dict.get("tags", []),
            created_at=tool_dict.get("created_at"),
            updated_at=tool_dict.get("updated_at"),
        )


# Global instance
tool_dao = ToolDAO()
