"""
MCP Server DAO - Data Access Object for MCP Server management.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger
from pymongo import ASCENDING

from src.domain.tool import MCPServerConfig
from src.infrastructure.mongo.client import MongoClientWrapper


class MCPServerDAO(MongoClientWrapper[MCPServerConfig]):
    """Data Access Object for MCP server management."""

    def __init__(self):
        super().__init__(model=MCPServerConfig, collection_name="mcp_servers")

        # Create indexes for efficient querying (no need for separate 'id' index, using _id)
        self.collection.create_index([("user_id", ASCENDING)])
        self.collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
        self.collection.create_index([("server_url", ASCENDING)])

        logger.info("MCPServerDAO initialized with MongoDB collection 'mcp_servers'")

    def create_server(self, server: MCPServerConfig) -> str:
        """
        Create a new MCP server configuration.

        Args:
            server: MCPServerConfig object to create

        Returns:
            str: The created server's ID (MongoDB _id as string)
        """
        server_dict = {
            "user_id": server.user_id,
            "name": server.name,
            "server_url": server.server_url,
            "server_type": server.server_type,
            "auth_type": server.auth_type,
            "auth_credentials": server.auth_credentials,
            "is_active": server.is_active,
            "timeout": server.timeout,
            "tags": server.tags,
            "created_at": server.created_at or datetime.utcnow(),
            "updated_at": server.updated_at or datetime.utcnow(),
        }

        result = self.collection.insert_one(server_dict)
        server_id = str(result.inserted_id)
        logger.info(f"Created MCP server '{server.name}' with ID: {server_id}")
        return server_id

    def get_server_by_id(
        self, server_id: str, user_id: str
    ) -> Optional[MCPServerConfig]:
        """
        Get an MCP server by its ID.

        Args:
            server_id: Server ID (MongoDB _id as string)
            user_id: User ID (for ownership validation)

        Returns:
            MCPServerConfig object or None if not found
        """
        server_dict = self.collection.find_one({"_id": ObjectId(server_id), "user_id": user_id})
        if not server_dict:
            return None

        return self._dict_to_server(server_dict)

    def get_user_servers(
        self, user_id: str, is_active: Optional[bool] = None
    ) -> List[MCPServerConfig]:
        """
        Get all MCP servers for a user.

        Args:
            user_id: User ID
            is_active: Optional filter by active status

        Returns:
            List of MCPServerConfig objects
        """
        query = {"user_id": user_id}
        if is_active is not None:
            query["is_active"] = is_active

        servers = []
        for server_dict in self.collection.find(query):
            servers.append(self._dict_to_server(server_dict))

        logger.info(f"Retrieved {len(servers)} MCP servers for user {user_id}")
        return servers

    def update_server(self, server_id: str, user_id: str, updates: dict) -> bool:
        """
        Update an MCP server.

        Args:
            server_id: Server ID (MongoDB _id as string)
            user_id: User ID (for ownership validation)
            updates: Dictionary of fields to update

        Returns:
            bool: True if updated successfully
        """
        updates["updated_at"] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": ObjectId(server_id), "user_id": user_id}, {"$set": updates}
        )

        if result.modified_count > 0:
            logger.info(f"Updated MCP server {server_id}")
            return True
        else:
            logger.warning(f"MCP server {server_id} not found or no changes made")
            return False

    def delete_server(self, server_id: str, user_id: str) -> bool:
        """
        Delete an MCP server.

        Args:
            server_id: Server ID (MongoDB _id as string)
            user_id: User ID (for ownership validation)

        Returns:
            bool: True if deleted successfully
        """
        result = self.collection.delete_one({"_id": ObjectId(server_id), "user_id": user_id})

        if result.deleted_count > 0:
            logger.info(f"Deleted MCP server {server_id}")
            return True
        else:
            logger.warning(f"MCP server {server_id} not found")
            return False

    def _dict_to_server(self, server_dict: dict) -> MCPServerConfig:
        """Convert database dictionary to MCPServerConfig object."""
        return MCPServerConfig(
            id=str(server_dict.get("_id", "")),
            user_id=server_dict.get("user_id", ""),
            name=server_dict.get("name", ""),
            server_url=server_dict.get("server_url", ""),
            server_type=server_dict.get("server_type", "http"),
            auth_type=server_dict.get("auth_type"),
            auth_credentials=server_dict.get("auth_credentials"),
            is_active=server_dict.get("is_active", True),
            timeout=server_dict.get("timeout", 30),
            tags=server_dict.get("tags", []),
            created_at=server_dict.get("created_at"),
            updated_at=server_dict.get("updated_at"),
        )


# Global instance
mcp_server_dao = MCPServerDAO()
