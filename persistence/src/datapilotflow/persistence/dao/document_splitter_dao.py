"""
Document Splitter Data Access Object.

This module handles all MongoDB operations for document splitter configurations.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from src.domain.knowledge.document_splitter import (
    DocumentSplitter,
    DocumentSplitterCreate,
    DocumentSplitterUpdate,
    SplitterType,
)
from src.infrastructure.mongo.client import MongoClientWrapper


class DocumentSplitterDAO(MongoClientWrapper[DocumentSplitter]):
    """DAO for managing document splitter configurations in MongoDB"""

    def __init__(self):
        super().__init__(
            model=DocumentSplitter, collection_name="knowledge_jobs_document_splitters"
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for document splitter configurations"""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])

            # Index for splitter type filtering
            self.collection.create_index([("splitter_type", 1)])

            # Compound index for user and splitter type
            self.collection.create_index([("user_id", 1), ("splitter_type", 1)])

            logger.info("Document splitter configuration indexes ensured")
        except Exception as e:
            logger.error(f"Error creating document splitter configuration indexes: {e}")

    def create_splitter(
        self, splitter_data: DocumentSplitterCreate, user_id: str
    ) -> Optional[str]:
        """Create a new document splitter configuration"""
        try:
            now = datetime.utcnow()

            # Create document without id field - MongoDB will create _id
            splitter_dict = {
                "user_id": user_id,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": now,
                "updated_at": now,
                **splitter_data.dict(),
            }

            result = self.collection.insert_one(splitter_dict)

            if result.inserted_id:
                splitter_id = str(result.inserted_id)
                logger.info(
                    f"Created document splitter {splitter_id} for user {user_id}"
                )
                return splitter_id
            return None

        except Exception as e:
            logger.error(f"Error creating document splitter: {e}")
            return None

    def get_splitter(
        self, splitter_id: str, user_id: str = None
    ) -> Optional[DocumentSplitter]:
        """Get a document splitter by ID"""
        try:
            query = {"_id": ObjectId(splitter_id)}
            if user_id:
                # Allow access only to user's own splitters
                query = {
                    "_id": ObjectId(splitter_id),
                    "user_id": user_id
                }

            result = self.collection.find_one(query)

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error getting document splitter {splitter_id}: {e}")
            return None

    def list_splitters(
        self,
        user_id: str,
        include_defaults: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentSplitter]:
        """List document splitters for a user"""
        try:
            query = {}
            if include_defaults:
                query = {"$or": [{"user_id": user_id}, {"is_default": True}]}
            else:
                query = {"user_id": user_id}

            results = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )
            return [self._parse_single_document(doc) for doc in results]

        except Exception as e:
            logger.error(f"Error listing document splitters for user {user_id}: {e}")
            return []

    def list_by_type(
        self, splitter_type: SplitterType, user_id: str = None
    ) -> List[DocumentSplitter]:
        """List splitters by type, optionally filtered by user"""
        try:
            query = {"splitter_type": splitter_type}
            if user_id:
                query = {
                    "splitter_type": splitter_type,
                    "$or": [{"user_id": user_id}, {"is_default": True}],
                }

            results = self.collection.find(query).sort("created_at", -1)
            return [self._parse_single_document(doc) for doc in results]

        except Exception as e:
            logger.error(
                f"Error listing document splitters by type {splitter_type}: {e}"
            )
            return []

    def list_defaults(self) -> List[DocumentSplitter]:
        """List all default document splitters"""
        try:
            results = self.collection.find({"is_default": True}).sort("created_at", -1)
            return [self._parse_single_document(doc) for doc in results]

        except Exception as e:
            logger.error(f"Error listing default document splitters: {e}")
            return []

    def list_most_used(self, limit: int = 10) -> List[DocumentSplitter]:
        """Get the most frequently used splitter configurations"""
        try:
            results = self.collection.find().sort("usage_count", -1).limit(limit)
            return [self._parse_single_document(doc) for doc in results]

        except Exception as e:
            logger.error(f"Error listing most used document splitters: {e}")
            return []

    def update_splitter(
        self, splitter_id: str, splitter_update: DocumentSplitterUpdate, user_id: str
    ) -> bool:
        """Update a document splitter configuration"""
        try:
            # Build update document with only non-None fields
            update_doc = {"updated_at": datetime.utcnow(), "updated_by": user_id}

            for field, value in splitter_update.dict(exclude_unset=True).items():
                if value is not None:
                    update_doc[field] = value

            result = self.collection.update_one(
                {"_id": ObjectId(splitter_id), "user_id": user_id}, {"$set": update_doc}
            )

            if result.modified_count > 0:
                logger.info(f"Updated document splitter {splitter_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating document splitter {splitter_id}: {e}")
            return False

    def delete_splitter(self, splitter_id: str, user_id: str) -> bool:
        """Delete a document splitter configuration"""
        try:
            # Check if this splitter is being used by any jobs
            from src.infrastructure.mongo.client import get_mongo_db

            db = get_mongo_db()
            jobs_using_splitter = db["knowledge_jobs"].count_documents(
                {"splitter_id": splitter_id}
            )

            if jobs_using_splitter > 0:
                logger.error(
                    f"Cannot delete splitter {splitter_id}: in use by {jobs_using_splitter} job(s)"
                )
                return False

            result = self.collection.delete_one(
                {
                    "_id": ObjectId(splitter_id),
                    "user_id": user_id,
                    "is_default": {
                        "$ne": True
                    },  # Prevent deletion of default splitters
                }
            )

            if result.deleted_count > 0:
                logger.info(f"Deleted document splitter {splitter_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting document splitter {splitter_id}: {e}")
            return False

    def increment_usage_count(self, splitter_id: str) -> bool:
        """Increment the usage count for a splitter configuration"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(splitter_id)}, {"$inc": {"usage_count": 1}}
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(
                f"Error incrementing usage count for splitter {splitter_id}: {e}"
            )
            return False

    def count_jobs_using_splitter(self, splitter_id: str) -> int:
        """Count how many jobs are using this splitter"""
        try:
            from src.infrastructure.mongo.client import get_mongo_db

            db = get_mongo_db()
            return db["knowledge_jobs"].count_documents({"splitter_id": splitter_id})

        except Exception as e:
            logger.error(f"Error counting jobs using splitter {splitter_id}: {e}")
            return 0
