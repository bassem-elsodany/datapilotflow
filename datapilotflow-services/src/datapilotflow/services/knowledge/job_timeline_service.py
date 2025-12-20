"""
Job Timeline Service.

This service handles business logic for job timeline entries,
allowing tracking of multiple job executions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from datapilotflow.domain.knowledge.job_timeline import JobTimeline, JobTimelineCreate, JobTimelineUpdate
from datapilotflow.domain.knowledge.knowledge_job import JobStatus
from datapilotflow.persistence.dao.job_timeline_dao import JobTimelineDAO


class JobTimelineService:
    """Service for managing job timeline entries."""
    
    def __init__(self):
        self.job_timeline_dao = JobTimelineDAO()
    
    def create_timeline_entry(
        self, 
        timeline_data: JobTimelineCreate, 
        user_id: str
    ) -> Optional[JobTimeline]:
        """Create a new job timeline entry."""
        try:
            timeline_id = self.job_timeline_dao.create_timeline_entry(timeline_data, user_id)
            if not timeline_id:
                raise ValueError("Failed to create job timeline entry")
            
            # Get and return the created timeline entry
            timeline_entry = self.job_timeline_dao.get_timeline_entry(timeline_id, user_id)
            if not timeline_entry:
                raise ValueError("Failed to retrieve created job timeline entry")
            
            return timeline_entry
            
        except Exception as e:
            logger.error(f"Error creating job timeline entry: {e}")
            raise
    
    def get_timeline_entry(
        self, 
        timeline_id: str, 
        user_id: str
    ) -> Optional[JobTimeline]:
        """Get a job timeline entry by ID."""
        return self.job_timeline_dao.get_timeline_entry(timeline_id, user_id)
    
    def list_timeline_entries(
        self, 
        job_id: str,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[JobTimeline]:
        """List timeline entries for a specific job."""
        return self.job_timeline_dao.list_timeline_entries(job_id, user_id, status, limit, skip)
    
    def update_timeline_entry(
        self, 
        timeline_id: str, 
        user_id: str, 
        update_data: JobTimelineUpdate
    ) -> Optional[JobTimeline]:
        """Update a job timeline entry."""
        return self.job_timeline_dao.update_timeline_entry(timeline_id, user_id, update_data)
    
    def get_latest_timeline_entry(
        self, 
        job_id: str, 
        user_id: str
    ) -> Optional[JobTimeline]:
        """Get the latest timeline entry for a job."""
        return self.job_timeline_dao.get_latest_timeline_entry(job_id, user_id)
    
    def get_timeline_statistics(
        self, 
        job_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Get statistics for all timeline entries of a job."""
        return self.job_timeline_dao.get_timeline_statistics(job_id, user_id)
    
    def start_job_execution(
        self, 
        job_id: str, 
        user_id: str,
        execution_context: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> Optional[JobTimeline]:
        """Start a new job execution and create a timeline entry."""
        try:
            timeline_data = JobTimelineCreate(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow(),
                execution_context=execution_context,
                triggered_by=triggered_by
            )
            
            return self.create_timeline_entry(timeline_data, user_id)
            
        except Exception as e:
            logger.error(f"Error starting job execution for job {job_id}: {e}")
            raise
    
    def complete_job_execution(
        self, 
        timeline_id: str, 
        user_id: str,
        documents_processed: int = 0,
        chunks_created: int = 0,
        processing_time_seconds: float = 0.0
    ) -> Optional[JobTimeline]:
        """Complete a job execution and update the timeline entry."""
        try:
            update_data = JobTimelineUpdate(
                status=JobStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                documents_processed=documents_processed,
                chunks_created=chunks_created,
                processing_time_seconds=processing_time_seconds
            )
            
            return self.update_timeline_entry(timeline_id, user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error completing job execution {timeline_id}: {e}")
            raise
    
    def fail_job_execution(
        self, 
        timeline_id: str, 
        user_id: str,
        error_message: str,
        error_traceback: Optional[str] = None,
        processing_time_seconds: float = 0.0
    ) -> Optional[JobTimeline]:
        """Fail a job execution and update the timeline entry."""
        try:
            update_data = JobTimelineUpdate(
                status=JobStatus.FAILED,
                completed_at=datetime.utcnow(),
                error_message=error_message,
                error_traceback=error_traceback,
                processing_time_seconds=processing_time_seconds
            )
            
            return self.update_timeline_entry(timeline_id, user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error failing job execution {timeline_id}: {e}")
            raise


# Global service instance
_job_timeline_service: Optional[JobTimelineService] = None


def get_job_timeline_service() -> JobTimelineService:
    """Get the global job timeline service instance."""
    global _job_timeline_service
    if _job_timeline_service is None:
        _job_timeline_service = JobTimelineService()
    return _job_timeline_service
