"""
Job Timeline API Router.

This router provides endpoints for managing job timeline entries,
allowing tracking of multiple job executions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from datapilotflow.domain.knowledge.job_timeline import JobTimeline, JobTimelineCreate, JobTimelineUpdate
from datapilotflow.domain.knowledge.knowledge_job import JobStatus
from datapilotflow.services.knowledge.job_timeline_service import get_job_timeline_service
from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.domain.user import User

router = APIRouter(prefix="/jobs", tags=["job-timelines"])


@router.get("/{job_id}/timelines", response_model=List[JobTimeline])
async def list_job_timeline_entries(
    job_id: str,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of entries to return"),
    skip: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user)
):
    """List timeline entries for a specific job."""
    try:
        timeline_service = get_job_timeline_service()
        timeline_entries = timeline_service.list_timeline_entries(
            job_id=job_id,
            user_id=current_user.id,
            status=status,
            limit=limit,
            skip=skip
        )
        
        logger.info(f"Retrieved {len(timeline_entries)} timeline entries for job {job_id}")
        return timeline_entries
        
    except Exception as e:
        logger.error(f"Error listing timeline entries for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline entries")


@router.get("/timelines/{timeline_id}", response_model=JobTimeline)
async def get_timeline_entry(
    timeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific timeline entry by ID."""
    try:
        timeline_service = get_job_timeline_service()
        timeline_entry = timeline_service.get_timeline_entry(timeline_id, current_user.id)
        
        if not timeline_entry:
            raise HTTPException(status_code=404, detail="Timeline entry not found")
        
        return timeline_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline entry {timeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline entry")


@router.get("/{job_id}/timelines/latest", response_model=JobTimeline)
async def get_latest_timeline_entry(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the latest timeline entry for a job."""
    try:
        timeline_service = get_job_timeline_service()
        timeline_entry = timeline_service.get_latest_timeline_entry(job_id, current_user.id)
        
        if not timeline_entry:
            raise HTTPException(status_code=404, detail="No timeline entries found for this job")
        
        return timeline_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest timeline entry for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest timeline entry")


@router.get("/{job_id}/timelines/statistics")
async def get_job_timeline_statistics(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for all timeline entries of a job."""
    try:
        timeline_service = get_job_timeline_service()
        statistics = timeline_service.get_timeline_statistics(job_id, current_user.id)
        
        return {
            "job_id": job_id,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting timeline statistics for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline statistics")


@router.put("/timelines/{timeline_id}", response_model=JobTimeline)
async def update_timeline_entry(
    timeline_id: str,
    update_data: JobTimelineUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a timeline entry."""
    try:
        timeline_service = get_job_timeline_service()
        updated_timeline = timeline_service.update_timeline_entry(
            timeline_id, current_user.id, update_data
        )
        
        if not updated_timeline:
            raise HTTPException(status_code=404, detail="Timeline entry not found")
        
        logger.info(f"Updated timeline entry {timeline_id}")
        return updated_timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating timeline entry {timeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update timeline entry")
