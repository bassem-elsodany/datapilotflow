"""
Pipeline Data Access Object.

This module handles all MongoDB operations for pipeline configurations.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from src.domain.knowledge.pipeline import Pipeline, PipelineCreate, PipelineUpdate
from src.infrastructure.mongo.client import MongoClientWrapper


class PipelineDAO(MongoClientWrapper[Pipeline]):
    """DAO for managing pipelines in MongoDB."""

    def __init__(self):
        super().__init__(model=Pipeline, collection_name="pipelines")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for pipelines."""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])

            # Index for pipeline status
            self.collection.create_index([("status", 1)])

            # Index for pipeline name search
            self.collection.create_index([("name", "text")])

            logger.info("Pipeline indexes ensured")
        except Exception as e:
            logger.error(f"Error creating pipeline indexes: {e}")

    def create_pipeline(
        self, pipeline_data: PipelineCreate, user_id: str
    ) -> Optional[str]:
        """Create a new pipeline."""
        try:
            now = datetime.utcnow()

            # Create document without id field - MongoDB will create _id
            pipeline_dict = {
                "user_id": user_id,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": now,
                "updated_at": now,
                "status": "draft",  # New pipelines start as draft
                "execution_count": 0,
                "last_executed_at": None,
                **pipeline_data.dict(),
            }

            result = self.collection.insert_one(pipeline_dict)

            if result.inserted_id:
                pipeline_id = str(result.inserted_id)
                logger.info(f"Created pipeline {pipeline_id} for user {user_id}")
                return pipeline_id
            return None

        except Exception as e:
            logger.error(f"Error creating pipeline: {e}")
            return None

    def get_pipeline(self, pipeline_id: str, user_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID."""
        try:
            result = self.collection.find_one(
                {"_id": ObjectId(pipeline_id), "user_id": user_id}
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error getting pipeline {pipeline_id}: {e}")
            return None

    def list_pipelines(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Pipeline]:
        """List pipelines for a user."""
        try:
            cursor = (
                self.collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            pipelines = []
            for doc in cursor:
                pipelines.append(self._parse_single_document(doc))

            return pipelines

        except Exception as e:
            logger.error(f"Error listing pipelines for user {user_id}: {e}")
            return []

    def update_pipeline(
        self, pipeline_id: str, user_id: str, update_data: PipelineUpdate
    ) -> Optional[Pipeline]:
        """Update a pipeline."""
        try:
            # Only include non-None fields in the update
            update_dict = {
                k: v for k, v in update_data.dict().items() if v is not None
            }

            if not update_dict:
                # No fields to update
                return self.get_pipeline(pipeline_id, user_id)

            update_dict["updated_at"] = datetime.utcnow()
            update_dict["updated_by"] = user_id

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(pipeline_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error updating pipeline {pipeline_id}: {e}")
            return None

    def delete_pipeline(self, pipeline_id: str, user_id: str) -> bool:
        """Delete a pipeline."""
        try:
            result = self.collection.delete_one(
                {"_id": ObjectId(pipeline_id), "user_id": user_id}
            )

            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted pipeline {pipeline_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting pipeline {pipeline_id}: {e}")
            return False

    def update_pipeline_status(
        self, pipeline_id: str, user_id: str, status: str
    ) -> Optional[Pipeline]:
        """Update pipeline status."""
        try:
            update_dict = {"status": status, "updated_at": datetime.utcnow()}

            # If status is running, increment execution count and update last_executed_at
            if status == "running":
                update_dict["last_executed_at"] = datetime.utcnow()
                self.collection.update_one(
                    {"_id": ObjectId(pipeline_id), "user_id": user_id},
                    {"$inc": {"execution_count": 1}},
                )

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(pipeline_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error updating pipeline status {pipeline_id}: {e}")
            return None

    def update_node_status(
        self,
        pipeline_id: str,
        user_id: str,
        node_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Pipeline]:
        """Update the status of a specific node in the pipeline."""
        try:
            update_dict = {
                "updated_at": datetime.utcnow(),
            }

            # Find the node and update its status
            pipeline = self.get_pipeline(pipeline_id, user_id)
            if not pipeline:
                return None

            for node in pipeline.nodes:
                if node.id == node_id:
                    node.status = status
                    if status == "running":
                        node.started_at = datetime.utcnow()
                    elif status in ["completed", "failed"]:
                        node.completed_at = datetime.utcnow()
                    if error_message:
                        node.error_message = error_message
                    break

            # Update the entire nodes array
            update_dict["nodes"] = [node.dict() for node in pipeline.nodes]

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(pipeline_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(
                f"Error updating node status for pipeline {pipeline_id}, node {node_id}: {e}"
            )
            return None
