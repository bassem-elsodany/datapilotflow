"""
Knowledge Job API Router.

This router provides REST endpoints for managing knowledge processing jobs.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from loguru import logger

from src.api.routers.auth.auth_router import get_current_user
from src.domain.events.job_events import JobActionRequested
from src.domain.knowledge.job_timeline import JobTimeline, JobTimelineUpdate
from src.domain.knowledge.knowledge_job import (
    JobStatus,
    KnowledgeJob,
    KnowledgeJobCreate,
    KnowledgeJobExpanded,
    KnowledgeJobUpdate,
)
from src.domain.user import User
from src.services.events_publisher import get_job_event_publisher
from src.services.knowledge.job_timeline_service import get_job_timeline_service
from src.services.knowledge.knowledge_job_service import (
    KnowledgeJobService,
    get_knowledge_job_service,
)

router = APIRouter()


@router.get("/", response_model=List[KnowledgeJob])
def list_all_knowledge_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """List all knowledge processing jobs for the current user."""
    try:
        jobs = service.list_knowledge_jobs(current_user.id, None, skip, limit)
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{job_id}", response_model=KnowledgeJobExpanded)
def get_knowledge_job(
    job_id: str,
    expand: Optional[str] = Query(
        None,
        description="Comma-separated list of related data to expand (timeline,document_splitter,vectordb_collection,knowledge_source_config,execution_stats)",
    ),
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Get a knowledge processing job by ID with optional expanded related data."""
    try:
        # Parse expand parameter
        expand_list = []
        if expand:
            expand_list = [item.strip() for item in expand.split(",") if item.strip()]

        job = service.get_knowledge_job_expanded(job_id, current_user.id, expand_list)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge processing job not found",
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{job_id}", response_model=KnowledgeJob)
def update_knowledge_job(
    job_id: str,
    update_data: KnowledgeJobUpdate,
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Update a knowledge processing job."""
    try:
        job = service.update_knowledge_job(job_id, current_user.id, update_data)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge processing job not found",
            )
        return job
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Delete a knowledge processing job."""
    try:
        deleted = service.delete_knowledge_job(job_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge processing job not found",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{job_id}/execute")
async def execute_knowledge_job(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Request execution of a knowledge processing job via event-driven architecture."""
    try:
        logger.debug(f"Executing job {job_id} by user {current_user.id}")
        # First, verify the job exists and belongs to the user
        job = service.get_knowledge_job(job_id, current_user.id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge processing job not found",
            )

        # Check if job is in a valid state for execution by looking at the latest timeline entry
        from src.services.knowledge.dao.job_timeline_dao import JobTimelineDAO

        timeline_dao = JobTimelineDAO()
        latest_timeline = timeline_dao.get_latest_timeline_entry(
            job_id, current_user.id
        )

        # If no timeline entries exist, allow execution (job was just created)
        if latest_timeline:
            if latest_timeline.status == JobStatus.RUNNING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Job is already running. Current status: {latest_timeline.status}",
                )
            # Allow execution of cancelled jobs - they can be restarted

        # Create and dispatch the job execution event
        event = JobActionRequested(
            job_id=job_id,
            user_id=current_user.id,
            requested_at=datetime.utcnow().isoformat(),
            execution_context={
                "source": "api",
                "endpoint": f"/api/v1/knowledge-jobs/{job_id}/execute",
            },
        )

        # Publish the event to RabbitMQ for async processing
        job_event_publisher = get_job_event_publisher()
        await job_event_publisher.publish_job_action_requested(event)

        logger.info(
            f"Job execution requested for job {job_id} by user {current_user.id}"
        )

        return {
            "message": "Job execution requested successfully",
            "job_id": job_id,
            "status": "execution_requested",
            "event_id": str(event.event_id),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting job execution for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{job_id}/cancel")
async def cancel_knowledge_job(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Cancel a running knowledge processing job."""
    try:
        logger.debug(f"Cancelling job {job_id} by user {current_user.id}")

        # First, verify the job exists and belongs to the user
        job = service.get_knowledge_job(job_id, current_user.id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge processing job not found",
            )

        # Check if job is in a valid state for cancellation
        from src.services.knowledge.dao.job_timeline_dao import JobTimelineDAO

        timeline_dao = JobTimelineDAO()
        latest_timeline = timeline_dao.get_latest_timeline_entry(
            job_id, current_user.id
        )

        if not latest_timeline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job has no execution history",
            )

        if latest_timeline.status != JobStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not running. Current status: {latest_timeline.status}",
            )

        # Create and dispatch the job cancellation event using same event type
        from src.services.events_publisher import get_job_event_publisher

        event = JobActionRequested(
            job_id=job_id,
            user_id=current_user.id,
            requested_at=datetime.utcnow().isoformat(),
            execution_context={
                "action": "cancel",  # This indicates it's a cancellation request
                "source": "api",
                "endpoint": f"/api/v1/knowledge-jobs/{job_id}/cancel",
                "cancellation_reason": "User requested cancellation",
            },
        )

        # Publish the event to RabbitMQ for async processing
        job_event_publisher = get_job_event_publisher()
        await job_event_publisher.publish_job_action_requested(event)

        logger.info(
            f"Job cancellation event published for job {job_id} by user {current_user.id}"
        )

        return {
            "message": "Job cancellation requested successfully",
            "job_id": job_id,
            "status": "cancellation_requested",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Job Timeline Endpoints


@router.get("/{job_id}/timelines", response_model=List[JobTimeline])
async def list_job_timeline_entries(
    job_id: str,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of entries to return"
    ),
    skip: int = Query(0, ge=0, description="Number of entries to skip"),
    latest: bool = Query(False, description="Get only the latest timeline entry"),
    current_user: User = Depends(get_current_user),
):
    """List timeline entries for a specific job."""
    try:
        timeline_service = get_job_timeline_service()

        if latest:
            # Get only the latest timeline entry
            timeline_entry = timeline_service.get_latest_timeline_entry(
                job_id, current_user.id
            )
            if not timeline_entry:
                return []  # Return empty array instead of 404
            return [timeline_entry]
        else:
            # Get all timeline entries
            timeline_entries = timeline_service.list_timeline_entries(
                job_id=job_id,
                user_id=current_user.id,
                status=status,
                limit=limit,
                skip=skip,
            )
            logger.info(
                f"Retrieved {len(timeline_entries)} timeline entries for job {job_id}"
            )
            return timeline_entries

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing timeline entries for job {job_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve timeline entries"
        )


# Removed /latest endpoint - use query parameter ?latest=true instead


@router.get("/{job_id}/timelines/statistics")
async def get_job_timeline_statistics(
    job_id: str, current_user: User = Depends(get_current_user)
):
    """Get statistics for all timeline entries of a job."""
    try:
        timeline_service = get_job_timeline_service()
        statistics = timeline_service.get_timeline_statistics(job_id, current_user.id)

        return {"job_id": job_id, "statistics": statistics}

    except Exception as e:
        logger.error(f"Error getting timeline statistics for job {job_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve timeline statistics"
        )


@router.put("/timelines/{timeline_id}", response_model=JobTimeline)
async def update_timeline_entry(
    timeline_id: str,
    update_data: JobTimelineUpdate,
    current_user: User = Depends(get_current_user),
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
