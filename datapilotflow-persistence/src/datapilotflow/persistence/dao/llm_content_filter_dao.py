"""
LLM Content Filter DAO module for MongoDB operations.

This module provides data access operations for LLM Content Filter configurations,
including CRUD operations and queries.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from datapilotflow.domain.knowledge.llm_content_filter_config import (
    LLMContentFilterConfig,
    LLMContentFilterConfigCreate,
    LLMContentFilterConfigUpdate,
)
from datapilotflow.persistence.mongo.client import MongoClientWrapper


class LLMContentFilterDAO(MongoClientWrapper[LLMContentFilterConfig]):
    """Data Access Object for LLM Content Filter configurations."""

    def __init__(self):
        """Initialize the LLM Content Filter DAO."""
        super().__init__(
            model=LLMContentFilterConfig,
            collection_name="knowledge_sources_llm_content_filters",
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create necessary indexes for the collection."""
        try:
            # Index on user_id for filtering by user
            self.collection.create_index("user_id")

            # Index on enabled status
            self.collection.create_index("enabled")

            # Compound index for user queries
            self.collection.create_index([("user_id", 1), ("enabled", 1)])

            logger.debug("LLM Content Filter DAO indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating LLM Content Filter DAO indexes: {e}")

    def create(
        self, config_data: LLMContentFilterConfigCreate, user_id: str
    ) -> Optional[str]:
        """Create a new LLM content filter configuration.

        Args:
            config_data: Configuration data for the new filter
            user_id: ID of the user creating the configuration

        Returns:
            ID of the created configuration, or None if creation failed
        """
        try:
            config_dict = config_data.model_dump()
            config_dict["user_id"] = user_id
            config_dict["created_at"] = datetime.utcnow()
            config_dict["updated_at"] = datetime.utcnow()

            result = self.collection.insert_one(config_dict)

            logger.info(
                f"Created LLM content filter config: {result.inserted_id} for user: {user_id}"
            )
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error creating LLM content filter config: {e}")
            return None

    def get_by_id(
        self, config_id: str, user_id: str
    ) -> Optional[LLMContentFilterConfig]:
        """Get an LLM content filter configuration by ID.

        Args:
            config_id: ID of the configuration to retrieve
            user_id: ID of the user (for access control)

        Returns:
            LLM content filter configuration if found, None otherwise
        """
        try:
            config_dict = self.collection.find_one(
                {"_id": ObjectId(config_id), "user_id": user_id}
            )

            if not config_dict:
                logger.warning(
                    f"LLM content filter config not found: {config_id} for user: {user_id}"
                )
                return None

            # Convert _id to string
            config_dict["id"] = str(config_dict.pop("_id"))

            return LLMContentFilterConfig(**config_dict)

        except Exception as e:
            logger.error(f"Error retrieving LLM content filter config {config_id}: {e}")
            return None

    def get_all(self, user_id: str) -> List[LLMContentFilterConfig]:
        """Get all LLM content filter configurations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of LLM content filter configurations
        """
        try:
            configs = []
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)

            for config_dict in cursor:
                config_dict["id"] = str(config_dict.pop("_id"))
                configs.append(LLMContentFilterConfig(**config_dict))

            logger.debug(
                f"Retrieved {len(configs)} LLM content filter configs for user: {user_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving LLM content filter configs for user {user_id}: {e}"
            )
            return []

    def get_enabled(self, user_id: str) -> List[LLMContentFilterConfig]:
        """Get all enabled LLM content filter configurations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of enabled LLM content filter configurations
        """
        try:
            configs = []
            cursor = self.collection.find({"user_id": user_id, "enabled": True}).sort(
                "created_at", -1
            )

            for config_dict in cursor:
                config_dict["id"] = str(config_dict.pop("_id"))
                configs.append(LLMContentFilterConfig(**config_dict))

            logger.debug(
                f"Retrieved {len(configs)} enabled LLM content filter configs for user: {user_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving enabled LLM content filter configs for user {user_id}: {e}"
            )
            return []

    def update(
        self, config_id: str, user_id: str, update_data: LLMContentFilterConfigUpdate
    ) -> bool:
        """Update an LLM content filter configuration.

        Args:
            config_id: ID of the configuration to update
            user_id: ID of the user (for access control)
            update_data: Updated configuration data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Only update fields that are not None
            update_dict = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }

            if not update_dict:
                logger.warning(
                    f"No fields to update for LLM content filter config: {config_id}"
                )
                return False

            # Always update the updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": ObjectId(config_id), "user_id": user_id},
                {"$set": update_dict},
            )

            if result.matched_count == 0:
                logger.warning(
                    f"LLM content filter config not found for update: {config_id}"
                )
                return False

            logger.info(f"Updated LLM content filter config: {config_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating LLM content filter config {config_id}: {e}")
            return False

    def delete(self, config_id: str, user_id: str) -> bool:
        """Delete an LLM content filter configuration.

        Args:
            config_id: ID of the configuration to delete
            user_id: ID of the user (for access control)

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.delete_one(
                {"_id": ObjectId(config_id), "user_id": user_id}
            )

            if result.deleted_count == 0:
                logger.warning(
                    f"LLM content filter config not found for deletion: {config_id}"
                )
                return False

            logger.info(f"Deleted LLM content filter config: {config_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting LLM content filter config {config_id}: {e}")
            return False

    def exists(self, config_id: str, user_id: str) -> bool:
        """Check if an LLM content filter configuration exists.

        Args:
            config_id: ID of the configuration to check
            user_id: ID of the user (for access control)

        Returns:
            True if configuration exists, False otherwise
        """
        try:
            count = self.collection.count_documents(
                {"_id": ObjectId(config_id), "user_id": user_id}
            )
            return count > 0

        except Exception as e:
            logger.error(
                f"Error checking existence of LLM content filter config {config_id}: {e}"
            )
            return False

    def get_by_provider(
        self, provider_id: str, user_id: str
    ) -> List[LLMContentFilterConfig]:
        """Get all LLM content filter configurations using a specific provider.

        Args:
            provider_id: ID of the model provider
            user_id: ID of the user

        Returns:
            List of LLM content filter configurations using the provider
        """
        try:
            configs = []
            cursor = self.collection.find(
                {"user_id": user_id, "llm_provider_id": provider_id}
            ).sort("created_at", -1)

            for config_dict in cursor:
                config_dict["id"] = str(config_dict.pop("_id"))
                configs.append(LLMContentFilterConfig(**config_dict))

            logger.debug(
                f"Retrieved {len(configs)} LLM content filter configs using provider {provider_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving LLM content filter configs by provider {provider_id}: {e}"
            )
            return []
