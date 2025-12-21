"""
VectorDB Collection Data Access Object.

This module handles all MongoDB operations for vector database collection configurations.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from datapilotflow.domain.knowledge.vectordb_collection import (
    VectorDBCollection,
    VectorDBCollectionCreate,
    VectorDBCollectionUpdate,
)
from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class VectorDBCollectionDAO(MongoClientWrapper[VectorDBCollection]):
    """Data access object for vector database collection configurations."""

    def __init__(self):
        super().__init__(
            model=VectorDBCollection,
            collection_name="knowledge_jobs_vectordb_collections",
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for vector DB collection configurations"""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("created_by", 1), ("created_at", -1)])

            # Index for collection_name for uniqueness checks
            self.collection.create_index([("collection_name", 1)], unique=True)

            # Index for embedding model for filtering
            self.collection.create_index(
                [("embedding_model_provider_id", 1), ("embedding_model_name", 1)]
            )

        except Exception as e:
            logger.error(f"Error creating vector DB collection indexes: {e}")

    def create_collection(
        self, collection_data: VectorDBCollectionCreate, user_id: str
    ) -> Optional[str]:
        """Create a new vector DB collection configuration"""
        try:
            now = datetime.utcnow()

            collection_dict = {
                "created_by": user_id,
                "created_at": now,
                **collection_data.dict(),
            }

            result = self.collection.insert_one(collection_dict)

            if result.inserted_id:
                collection_id = str(result.inserted_id)
                logger.info(
                    f"Created vector DB collection {collection_id} for user {user_id}"
                )
                return collection_id
            return None

        except Exception as e:
            logger.error(f"Error creating vector DB collection: {e}")
            return None

    def get_collection(
        self, collection_id: str, user_id: str
    ) -> Optional[VectorDBCollection]:
        """Get a vector DB collection configuration by ID"""
        try:
            result = self.collection.find_one(
                {"_id": ObjectId(collection_id), "created_by": user_id}
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error getting vector DB collection {collection_id}: {e}")
            return None

    def get_collection_by_name(
        self, collection_name: str
    ) -> Optional[VectorDBCollection]:
        """Get a vector DB collection configuration by collection name"""
        try:
            logger.debug(
                f"[DAO] Querying MongoDB for collection_name='{collection_name}'"
            )
            result = self.collection.find_one({"collection_name": collection_name})
            logger.debug(f"[DAO] MongoDB find_one result: {result is not None}")

            if result:
                parsed = self._parse_single_document(result)
                logger.debug(
                    f"[DAO] Successfully parsed collection config for '{collection_name}'"
                )
                return parsed
            else:
                logger.warning(
                    f"[DAO] ❌ MongoDB returned NO document for collection_name='{collection_name}'"
                )
                return None

        except Exception as e:
            logger.error(
                f"[DAO] ❌❌ EXCEPTION getting vector DB collection by name '{collection_name}': {e}"
            )
            import traceback

            logger.error(f"[DAO] Traceback: {traceback.format_exc()}")
            return None

    def list_collections(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[VectorDBCollection]:
        """List vector DB collection configurations for a user"""
        try:
            cursor = (
                self.collection.find({"created_by": user_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            return [self._parse_single_document(doc) for doc in cursor]

        except Exception as e:
            logger.error(f"Error listing vector DB collections: {e}")
            return []

    def update_collection(
        self, collection_id: str, user_id: str, update_data: VectorDBCollectionUpdate
    ) -> Optional[VectorDBCollection]:
        """Update a vector DB collection configuration"""
        try:
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            logger.debug(
                f"DAO: Updating collection {collection_id} with data: {update_dict}"
            )

            if not update_dict:
                logger.debug(f"DAO: No data to update, returning existing collection")
                return self.get_collection(collection_id, user_id)

            # Check if collection exists and user owns it
            existing_collection = self.get_collection(collection_id, user_id)
            if not existing_collection:
                logger.error(
                    f"DAO: Collection {collection_id} not found or user {user_id} doesn't own it"
                )
                return None

            logger.debug(f"DAO: Collection exists, proceeding with update")

            result = self.collection.update_one(
                {"_id": ObjectId(collection_id), "created_by": user_id},
                {"$set": update_dict},
            )

            logger.debug(
                f"DAO: Update result - matched: {result.matched_count}, modified: {result.modified_count}"
            )

            if result.matched_count == 0:
                logger.error(
                    f"DAO: No collection found with ID {collection_id} owned by user {user_id}"
                )
                return None

            if result.modified_count == 0:
                logger.warning(
                    f"DAO: Collection {collection_id} found but no changes made (data might be identical)"
                )
                # Return the existing collection even if no changes were made
                return self.get_collection(collection_id, user_id)

            logger.debug(f"DAO: Successfully updated collection {collection_id}")
            return self.get_collection(collection_id, user_id)

        except Exception as e:
            logger.error(f"Error updating vector DB collection {collection_id}: {e}")
            return None

    def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """Delete a vector DB collection configuration"""
        try:
            result = self.collection.delete_one(
                {"_id": ObjectId(collection_id), "created_by": user_id}
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting vector DB collection {collection_id}: {e}")
            return False
