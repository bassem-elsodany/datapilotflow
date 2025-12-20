"""
Knowledge Job Data Access Object.

This module handles all MongoDB operations for knowledge processing jobs.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from src.domain.knowledge.knowledge_job import (
    JobStatus,
    KnowledgeJob,
    KnowledgeJobCreate,
    KnowledgeJobUpdate,
)
from src.infrastructure.mongo.client import MongoClientWrapper


class KnowledgeJobDAO(MongoClientWrapper[KnowledgeJob]):
    """DAO for managing knowledge processing jobs in MongoDB"""

    def __init__(self):
        super().__init__(model=KnowledgeJob, collection_name="knowledge_jobs")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure proper indexes exist for knowledge processing jobs"""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])

            # Index for knowledge_source_config_id for config-related queries
            self.collection.create_index([("knowledge_source_config_id", 1)])

            # Index for status for filtering
            self.collection.create_index([("status", 1)])

            # Compound index for user and status
            self.collection.create_index([("user_id", 1), ("status", 1)])

            logger.info("Knowledge processing job indexes ensured")
        except Exception as e:
            logger.error(f"Error creating knowledge processing job indexes: {e}")

    def create_job(
        self,
        job_data: KnowledgeJobCreate,
        config_id: str,
        user_id: str,
        vectordb_collection_id: str = None,
    ) -> Optional[str]:
        """Create a new knowledge processing job"""
        try:
            now = datetime.utcnow()

            # Extract only the job-specific fields from job_data
            job_dict = {
                "knowledge_source_config_id": config_id,
                "vectordb_collection_id": vectordb_collection_id,
                "user_id": user_id,
                "created_by": user_id,
                "created_at": now,
                "status": "created",  # Explicitly set initial status
                "name": job_data.name,
                "description": job_data.description,
                "batch_size": job_data.batch_size,
                "save_to_file": job_data.save_to_file,
                "write_consolidated_file": job_data.write_consolidated_file,
                "clear_collection_before_start": job_data.clear_collection_before_start,
                "check_duplicates_before_insert": job_data.check_duplicates_before_insert,
            }

            # Document splitter reference - ONLY save splitter_id
            # The actual splitter config is stored in document_splitters collection
            if job_data.splitter_id:
                job_dict["splitter_id"] = job_data.splitter_id
                # Save custom overrides if provided
                if job_data.custom_chunk_size is not None:
                    job_dict["custom_chunk_size"] = job_data.custom_chunk_size
                if job_data.custom_chunk_overlap is not None:
                    job_dict["custom_chunk_overlap"] = job_data.custom_chunk_overlap

            result = self.collection.insert_one(job_dict)

            if result.inserted_id:
                job_id = str(result.inserted_id)
                logger.info(
                    f"Created knowledge processing job {job_id} for user {user_id}"
                )
                return job_id
            return None

        except Exception as e:
            logger.error(f"Error creating knowledge processing job: {e}")
            return None

    def get_job(self, job_id: str, user_id: str) -> Optional[KnowledgeJob]:
        """Get a knowledge processing job by ID"""
        try:
            result = self.collection.find_one(
                {"_id": ObjectId(job_id), "user_id": user_id}
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error getting knowledge processing job {job_id}: {e}")
            return None

    def list_jobs(
        self,
        user_id: str,
        config_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[KnowledgeJob]:
        """List knowledge processing jobs for a user"""
        try:
            query = {"user_id": user_id}

            if config_id:
                query["knowledge_source_config_id"] = config_id

            # Note: status filtering is no longer supported as status is tracked in timeline entries

            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            jobs = []
            for doc in cursor:
                jobs.append(self._parse_single_document(doc))

            return jobs

        except Exception as e:
            logger.error(
                f"Error listing knowledge processing jobs for user {user_id}: {e}"
            )
            return []

    def update_job_status(
        self,
        job_id: str,
        user_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> Optional[KnowledgeJob]:
        """Update the status of a knowledge processing job"""
        try:
            update_dict = {"status": status.value, "updated_at": datetime.utcnow()}

            if status == JobStatus.RUNNING and "started_at" not in kwargs:
                update_dict["started_at"] = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_dict["completed_at"] = datetime.utcnow()

            if error_message:
                update_dict["error_message"] = error_message

            # Add any additional fields
            update_dict.update(kwargs)

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(job_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error updating job status for job {job_id}: {e}")
            return None

    def update_job(
        self, job_id: str, user_id: str, update_data: "KnowledgeJobUpdate"
    ) -> Optional[KnowledgeJob]:
        """Update a knowledge processing job"""
        try:
            update_dict = {"updated_at": datetime.utcnow()}

            # Add non-None fields from update_data
            for field, value in update_data.model_dump(exclude_unset=True).items():
                if value is not None:
                    update_dict[field] = value

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(job_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True,
            )

            if result:
                return self._parse_single_document(result)
            return None

        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return None

    def delete_job(self, job_id: str, user_id: str) -> bool:
        """Delete a knowledge processing job and all related records"""
        try:
            # First, get the job to know which collection and splitter to check
            job = self.get_job(job_id, user_id)
            if not job:
                logger.warning(f"Job {job_id} not found for deletion")
                return False

            vectordb_collection_id = job.vectordb_collection_id
            splitter_id = getattr(job, "splitter_id", None)

            # Delete the job itself
            result = self.collection.delete_one(
                {"_id": ObjectId(job_id), "user_id": user_id}
            )

            if result.deleted_count == 0:
                return False

            logger.info(f"Deleted knowledge processing job {job_id}")

            # Delete all related timeline entries
            try:
                timeline_result = self.db["knowledge_jobs_timelines"].delete_many(
                    {"job_id": job_id, "user_id": user_id}
                )
                logger.info(
                    f"Deleted {timeline_result.deleted_count} timeline entries for job {job_id}"
                )
            except Exception as e:
                logger.error(f"Error deleting timeline entries for job {job_id}: {e}")

            # Check if vectordb collection is used by other jobs before deleting
            if vectordb_collection_id:
                try:
                    other_jobs_count = self.collection.count_documents(
                        {
                            "vectordb_collection_id": vectordb_collection_id,
                            "user_id": user_id,
                        }
                    )
                    if other_jobs_count == 0:
                        # No other jobs use this collection, safe to delete
                        collection_result = self.db[
                            "knowledge_jobs_vectordb_collections"
                        ].delete_one(
                            {
                                "_id": ObjectId(vectordb_collection_id),
                                "created_by": user_id,
                            }
                        )
                        if collection_result.deleted_count > 0:
                            logger.info(
                                f"Deleted vectordb collection {vectordb_collection_id} (no longer used)"
                            )
                    else:
                        logger.info(
                            f"Vectordb collection {vectordb_collection_id} still used by {other_jobs_count} other job(s)"
                        )
                except Exception as e:
                    logger.error(
                        f"Error checking/deleting vectordb collection {vectordb_collection_id}: {e}"
                    )

            # Check if document splitter is used by other jobs before deleting
            if splitter_id:
                try:
                    other_jobs_count = self.collection.count_documents(
                        {"splitter_id": splitter_id, "user_id": user_id}
                    )
                    if other_jobs_count == 0:
                        # No other jobs use this splitter, safe to delete
                        splitter_result = self.db[
                            "knowledge_jobs_document_splitters"
                        ].delete_one({"_id": ObjectId(splitter_id), "user_id": user_id})
                        if splitter_result.deleted_count > 0:
                            logger.info(
                                f"Deleted document splitter {splitter_id} (no longer used)"
                            )
                    else:
                        logger.info(
                            f"Document splitter {splitter_id} still used by {other_jobs_count} other job(s)"
                        )
                except Exception as e:
                    logger.error(
                        f"Error checking/deleting document splitter {splitter_id}: {e}"
                    )

            return True

        except Exception as e:
            logger.error(f"Error deleting knowledge processing job {job_id}: {e}")
            return False
