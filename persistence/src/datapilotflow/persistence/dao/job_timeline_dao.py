"""
Job Timeline Data Access Object.

This module provides database operations for job timeline entries,
allowing tracking of multiple job executions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from loguru import logger

from src.infrastructure.mongo.client import MongoClientWrapper
from src.domain.knowledge.job_timeline import JobTimeline, JobTimelineCreate, JobTimelineUpdate
from src.domain.knowledge.knowledge_job import JobStatus


class JobTimelineDAO(MongoClientWrapper[JobTimeline]):
    """Data Access Object for job timeline entries."""
    
    def __init__(self):
        super().__init__(
            model=JobTimeline,
            collection_name="knowledge_jobs_timelines"
        )
    
    def create_timeline_entry(
        self, 
        timeline_data: JobTimelineCreate, 
        user_id: str
    ) -> str:
        """Create a new job timeline entry."""
        try:
            timeline_dict = {
                "job_id": timeline_data.job_id,
                "user_id": user_id,
                "status": timeline_data.status.value,
                "started_at": timeline_data.started_at,
                "completed_at": None,
                "documents_processed": timeline_data.documents_processed,
                "chunks_created": timeline_data.chunks_created,
                "processing_time_seconds": timeline_data.processing_time_seconds,
                "error_message": timeline_data.error_message,
                "error_traceback": timeline_data.error_traceback,
                "execution_context": timeline_data.execution_context,
                "triggered_by": timeline_data.triggered_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.collection.insert_one(timeline_dict)
            return str(result.inserted_id) if result.inserted_id else None
            
        except Exception as e:
            logger.error(f"Error creating job timeline entry: {e}")
            raise
    
    def get_timeline_entry(
        self, 
        timeline_id: str, 
        user_id: str
    ) -> Optional[JobTimeline]:
        """Get a job timeline entry by ID."""
        try:
            document = self.collection.find_one({
                "_id": ObjectId(timeline_id),
                "user_id": user_id
            })
            
            if document:
                return self._parse_single_document(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting job timeline entry {timeline_id}: {e}")
            return None
    
    def list_timeline_entries(
        self, 
        job_id: str,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[JobTimeline]:
        """List timeline entries for a specific job."""
        try:
            query = {
                "job_id": job_id,
                "user_id": user_id
            }
            
            if status:
                query["status"] = status.value
            
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            timeline_entries = []
            for document in cursor:
                timeline_entry = self._parse_single_document(document)
                if timeline_entry:
                    timeline_entries.append(timeline_entry)
            
            return timeline_entries
            
        except Exception as e:
            logger.error(f"Error listing timeline entries for job {job_id}: {e}")
            return []
    
    def update_timeline_entry(
        self, 
        timeline_id: str, 
        user_id: str, 
        update_data: JobTimelineUpdate
    ) -> Optional[JobTimeline]:
        """Update a job timeline entry."""
        try:
            update_dict = {
                "updated_at": datetime.utcnow()
            }
            
            # Add non-None fields from update_data
            for field, value in update_data.model_dump(exclude_unset=True).items():
                if value is not None:
                    if field == "status":
                        update_dict[field] = value.value
                    else:
                        update_dict[field] = value
            
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(timeline_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                return self._parse_single_document(result)
            return None
            
        except Exception as e:
            logger.error(f"Error updating job timeline entry {timeline_id}: {e}")
            return None
    
    def get_latest_timeline_entry(
        self, 
        job_id: str, 
        user_id: str
    ) -> Optional[JobTimeline]:
        """Get the latest timeline entry for a job."""
        try:
            document = self.collection.find_one(
                {
                    "job_id": job_id,
                    "user_id": user_id
                },
                sort=[("created_at", -1)]
            )
            
            if document:
                return self._parse_single_document(document)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest timeline entry for job {job_id}: {e}")
            return None
    
    def get_timeline_statistics(
        self, 
        job_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Get statistics for all timeline entries of a job."""
        try:
            pipeline = [
                {
                    "$match": {
                        "job_id": job_id,
                        "user_id": user_id
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_executions": {"$sum": 1},
                        "successful_executions": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "completed"]}, 1, 0]
                            }
                        },
                        "failed_executions": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "failed"]}, 1, 0]
                            }
                        },
                        "total_documents_processed": {"$sum": "$documents_processed"},
                        "total_chunks_created": {"$sum": "$chunks_created"},
                        "total_processing_time": {"$sum": "$processing_time_seconds"},
                        "last_execution": {"$max": "$created_at"}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            if result:
                return result[0]
            
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_documents_processed": 0,
                "total_chunks_created": 0,
                "total_processing_time": 0,
                "last_execution": None
            }
            
        except Exception as e:
            logger.error(f"Error getting timeline statistics for job {job_id}: {e}")
            return {}
