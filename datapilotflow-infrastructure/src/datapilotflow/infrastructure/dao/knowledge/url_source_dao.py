"""
URL Source Data Access Object.

This module handles all MongoDB operations for URL source configurations.
"""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import (
    UrlSourceConfig,
    UrlSourceConfigCreate,
)
from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class UrlSourceDAO(MongoClientWrapper[UrlSourceConfig]):
    """DAO for managing URL source configurations in MongoDB"""

    def __init__(self):
        super().__init__(
            model=UrlSourceConfig, collection_name="knowledge_sources_url_sources"
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for URL source configurations"""
        try:
            # Index for created_at for sorting
            self.collection.create_index([("created_at", -1)])

            logger.info("URL source configuration indexes ensured")
        except Exception as e:
            logger.error(f"Error creating URL source configuration indexes: {e}")

    def create_url_source(
        self, url_source_data: UrlSourceConfigCreate, user_id: str
    ) -> Optional[str]:
        """Create a new URL source configuration"""
        try:
            now = datetime.utcnow()

            # Create URL source document
            url_source_dict = {
                "created_at": now,
                "updated_at": now,
                **url_source_data.dict(),
            }

            result = self.collection.insert_one(url_source_dict)

            if result.inserted_id:
                url_source_id = str(result.inserted_id)
                logger.info(f"Created URL source configuration {url_source_id}")
                return url_source_id
            return None

        except Exception as e:
            logger.error(f"Error creating URL source configuration: {e}")
            return None

    def get_url_source(self, url_source_id: str) -> Optional[UrlSourceConfig]:
        """Get a URL source configuration by ID"""
        try:
            result = self.collection.find_one({"_id": ObjectId(url_source_id)})

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error getting URL source configuration {url_source_id}: {e}")
            return None

    def update_url_source(
        self, url_source_id: str, url_source_data: "UrlSourceConfigCreate"
    ) -> bool:
        """Update a URL source configuration with new data"""
        try:
            update_dict = {
                "file_name": url_source_data.file_name,
                "urls": url_source_data.urls,
                "updated_at": datetime.utcnow(),
            }

            result = self.collection.update_one(
                {"_id": ObjectId(url_source_id)}, {"$set": update_dict}
            )

            success = result.modified_count > 0
            if success:
                logger.info(
                    f"Updated URL source {url_source_id} with {len(url_source_data.urls)} URLs"
                )

            return success

        except Exception as e:
            logger.error(f"Error updating URL source {url_source_id}: {e}")
            return False

    def delete_url_source(self, url_source_id: str) -> bool:
        """Delete a URL source configuration"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(url_source_id)})

            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted URL source configuration {url_source_id}")

            return success

        except Exception as e:
            logger.error(
                f"Error deleting URL source configuration {url_source_id}: {e}"
            )
            return False
