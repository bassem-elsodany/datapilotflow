"""
Knowledge Source Data Access Object.

This module handles all MongoDB operations for knowledge source configurations.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger
from pymongo import ReturnDocument

from datapilotflow.domain.knowledge.knowledge_source_config import (
    KnowledgeSourceConfig,
    KnowledgeSourceConfigCreate,
    KnowledgeSourceConfigUpdate,
)
from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class KnowledgeSourceDAO(MongoClientWrapper[KnowledgeSourceConfig]):
    """DAO for managing knowledge source configurations in MongoDB"""

    def __init__(self):
        super().__init__(
            model=KnowledgeSourceConfig, collection_name="knowledge_sources"
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for knowledge source configurations"""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])

            # Index for scraping_mode for filtering
            self.collection.create_index([("scraping_mode", 1)])

            # Index for url_source_id for URL source lookups
            self.collection.create_index([("url_source_id", 1)])

            logger.info("Knowledge source configuration indexes ensured")
        except Exception as e:
            logger.error(f"Error creating knowledge source configuration indexes: {e}")

    def create_config(
        self, config_data: KnowledgeSourceConfigCreate, user_id: str
    ) -> Optional[str]:
        """Create a new knowledge source configuration"""
        try:
            now = datetime.utcnow()

            # Create document without id field - MongoDB will create _id
            config_dict = {
                "user_id": user_id,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": now,
                "updated_at": now,
                **config_data.dict(),
            }

            # Remove url_source from config_dict if present (will be handled separately)
            if "url_source" in config_dict:
                del config_dict["url_source"]

            result = self.collection.insert_one(config_dict)

            if result.inserted_id:
                config_id = str(result.inserted_id)
                logger.info(
                    f"Created knowledge source configuration {config_id} for user {user_id}"
                )
                return config_id
            return None

        except Exception as e:
            logger.error(f"Error creating knowledge source configuration: {e}")
            return None

    def get_config(
        self, config_id: str, user_id: str
    ) -> Optional[KnowledgeSourceConfig]:
        """Get a knowledge source configuration by ID"""
        try:
            result = self.collection.find_one(
                {"_id": ObjectId(config_id), "user_id": user_id}
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(
                f"Error getting knowledge source configuration {config_id}: {e}"
            )
            return None

    def list_configs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        content_source_type: Optional[str] = None,
    ) -> List[KnowledgeSourceConfig]:
        """List knowledge source configurations for a user"""
        try:
            query = {"user_id": user_id}
            if content_source_type:
                query["content_source_type"] = content_source_type

            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            configs = []
            for doc in cursor:
                configs.append(self._parse_single_document(doc))

            return configs

        except Exception as e:
            logger.error(
                f"Error listing knowledge source configurations for user {user_id}: {e}"
            )
            return []

    def update_config(
        self, config_id: str, user_id: str, update_data: KnowledgeSourceConfigUpdate
    ) -> Optional[KnowledgeSourceConfig]:
        """Update a knowledge source configuration"""
        try:
            # Only include non-None fields in the update
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

            if not update_dict:
                # No fields to update
                return self.get_config(config_id, user_id)

            update_dict["updated_at"] = datetime.utcnow()
            update_dict["updated_by"] = user_id

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(config_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(
                f"Error updating knowledge source configuration {config_id}: {e}"
            )
            return None

    def delete_config(self, config_id: str, user_id: str) -> bool:
        """Delete a knowledge source configuration and all related records"""
        try:
            # First, get the config to know which related records to delete
            config = self.get_config(config_id, user_id)
            if not config:
                logger.warning(f"Config {config_id} not found for deletion")
                return False

            url_source_id = config.url_source_id
            llm_content_filter_id = config.llm_content_filter_id

            # Delete the config itself
            result = self.collection.delete_one(
                {"_id": ObjectId(config_id), "user_id": user_id}
            )

            if result.deleted_count == 0:
                return False

            logger.info(f"Deleted knowledge source configuration {config_id}")

            # Delete related URL source if it exists
            if url_source_id:
                try:
                    url_source_result = self.db[
                        "knowledge_sources_url_sources"
                    ].delete_one({"_id": ObjectId(url_source_id)})
                    if url_source_result.deleted_count > 0:
                        logger.info(
                            f"Deleted URL source {url_source_id} for config {config_id}"
                        )
                except Exception as e:
                    logger.error(f"Error deleting URL source {url_source_id}: {e}")

            # Delete related LLM content filter if it exists
            if llm_content_filter_id:
                try:
                    filter_result = self.db[
                        "knowledge_sources_llm_content_filters"
                    ].delete_one(
                        {"_id": ObjectId(llm_content_filter_id), "user_id": user_id}
                    )
                    if filter_result.deleted_count > 0:
                        logger.info(
                            f"Deleted LLM content filter {llm_content_filter_id} for config {config_id}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error deleting LLM content filter {llm_content_filter_id}: {e}"
                    )

            return True

        except Exception as e:
            logger.error(
                f"Error deleting knowledge source configuration {config_id}: {e}"
            )
            return False

    def update_job_count(
        self,
        config_id: str,
        user_id: str,
        increment: int = 1,
        last_job_at: Optional[datetime] = None,
    ) -> bool:
        """Update job count and last job timestamp for a configuration"""
        try:
            update_dict = {"$inc": {"job_count": increment}}
            if last_job_at:
                update_dict["$set"] = {"last_job_at": last_job_at}

            result = self.collection.update_one(
                {"_id": ObjectId(config_id), "user_id": user_id}, update_dict
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Updated job count for configuration {config_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating job count for configuration {config_id}: {e}")
            return False
