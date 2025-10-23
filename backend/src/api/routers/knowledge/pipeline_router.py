"""
Pipeline API Router.

This router provides REST endpoints for managing visual data processing pipelines.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.api.routers.auth.auth_router import get_current_user
from src.domain.knowledge.pipeline import (
    Pipeline,
    PipelineCreate,
    PipelineExecutionRequest,
    PipelineExecutionStatus,
    PipelineUpdate,
)
from src.domain.user import User
from src.services.knowledge.pipeline_service import PipelineService

router = APIRouter()


def get_pipeline_service() -> PipelineService:
    """Dependency injection for PipelineService."""
    return PipelineService()


@router.post("/", response_model=Pipeline, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    pipeline_data: PipelineCreate,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """
    Create a new pipeline template.

    This saves the visual pipeline configuration (nodes and edges) for later editing and execution.
    """
    try:
        pipeline = service.create_pipeline(pipeline_data, current_user.id)
        return pipeline
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=List[Pipeline])
def list_pipelines(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """List all pipelines for the current user."""
    try:
        pipelines = service.list_pipelines(current_user.id, skip, limit)
        return pipelines
    except Exception as e:
        logger.error(f"Error listing pipelines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{pipeline_id}", response_model=Pipeline)
def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """Get a specific pipeline by ID."""
    try:
        pipeline = service.get_pipeline(pipeline_id, current_user.id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        return pipeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{pipeline_id}", response_model=Pipeline)
def update_pipeline(
    pipeline_id: str,
    update_data: PipelineUpdate,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """Update a pipeline template."""
    try:
        pipeline = service.update_pipeline(pipeline_id, current_user.id, update_data)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        return pipeline
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """Delete a pipeline."""
    try:
        success = service.delete_pipeline(pipeline_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{pipeline_id}/execute", status_code=status.HTTP_202_ACCEPTED)
def execute_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """
    Execute a pipeline.

    This converts the visual pipeline into actual knowledge source + job execution:
    1. Creates knowledge source configuration from data source nodes
    2. Creates document splitter from splitter nodes
    3. Creates/uses vector DB collection from storage nodes
    4. Creates and executes a KnowledgeJob

    Returns execution details including job_id for tracking.
    """
    try:
        request = PipelineExecutionRequest(pipeline_id=pipeline_id)
        result = service.execute_pipeline(request, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing pipeline {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{pipeline_id}/status", response_model=PipelineExecutionStatus)
def get_pipeline_status(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    service: PipelineService = Depends(get_pipeline_service),
):
    """Get the execution status of a pipeline."""
    try:
        status_info = service.get_execution_status(pipeline_id, current_user.id)
        return status_info
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting pipeline status {pipeline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
