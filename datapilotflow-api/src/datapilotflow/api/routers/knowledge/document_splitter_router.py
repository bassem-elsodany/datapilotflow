"""
Document Splitter API Router.

This module provides REST endpoints for managing document splitter configurations,
including CRUD operations and default splitter access.
"""

from typing import List, Optional

from datapilotflow.domain.knowledge.document_splitter import (
    DocumentSplitter,
    DocumentSplitterCreate,
    DocumentSplitterUpdate,
    SplitterType,
)
from datapilotflow.domain.user import User
from datapilotflow.services.knowledge import get_document_splitter_service
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from datapilotflow.api.routers.auth.auth_router import get_current_user

router = APIRouter()


@router.get("/", response_model=List[DocumentSplitter])
async def list_document_splitters(
    include_defaults: bool = Query(
        True, description="Include default/system splitters"
    ),
    splitter_type: Optional[SplitterType] = Query(
        None, description="Filter by splitter type"
    ),
    current_user: User = Depends(get_current_user),
):
    """List all document splitters available to the current user.

    Args:
        include_defaults: Whether to include default/system splitters
        splitter_type: Optional filter by splitter type
        current_user: Current authenticated user

    Returns:
        List[DocumentSplitter]: List of available splitter configurations
    """
    try:
        service = get_document_splitter_service()

        if splitter_type:
            splitters = service.get_splitters_by_type(splitter_type, current_user.id)
        else:
            splitters = service.get_user_splitters(current_user.id, include_defaults)

        logger.info(
            f"Listed {len(splitters)} document splitters for user {current_user.id}"
        )
        return splitters

    except Exception as e:
        logger.error(f"Error listing document splitters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults", response_model=List[DocumentSplitter])
async def list_default_splitters():
    """Get all default/system document splitter configurations.

    Returns:
        List[DocumentSplitter]: List of default splitter configurations
    """
    try:
        service = get_document_splitter_service()
        splitters = service.get_default_splitters()

        logger.info(f"Listed {len(splitters)} default document splitters")
        return splitters

    except Exception as e:
        logger.error(f"Error listing default document splitters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/most-used", response_model=List[DocumentSplitter])
async def list_most_used_splitters(
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of splitters to return"
    ),
    current_user: User = Depends(get_current_user),
):
    """Get the most frequently used document splitter configurations.

    Args:
        limit: Maximum number of splitters to return
        current_user: Current authenticated user

    Returns:
        List[DocumentSplitter]: List of most used splitter configurations
    """
    try:
        service = get_document_splitter_service()
        splitters = service.get_most_used_splitters(limit)

        logger.info(f"Listed {len(splitters)} most used document splitters")
        return splitters

    except Exception as e:
        logger.error(f"Error listing most used document splitters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DocumentSplitter, status_code=201)
async def create_document_splitter(
    splitter_data: DocumentSplitterCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new document splitter configuration.

    Args:
        splitter_data: The splitter configuration data
        current_user: Current authenticated user

    Returns:
        DocumentSplitter: The created splitter configuration
    """
    try:
        service = get_document_splitter_service()
        splitter = service.create_splitter(splitter_data, current_user.id)

        logger.info(
            f"Created document splitter '{splitter.name}' ({splitter.id}) for user {current_user.id}"
        )
        return splitter

    except ValueError as e:
        logger.warning(f"Validation error creating document splitter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating document splitter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{splitter_id}", response_model=DocumentSplitter)
async def get_document_splitter(
    splitter_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific document splitter configuration.

    Args:
        splitter_id: The splitter ID
        current_user: Current authenticated user

    Returns:
        DocumentSplitter: The splitter configuration
    """
    try:
        service = get_document_splitter_service()
        splitter = service.get_splitter_by_id(splitter_id)

        if not splitter:
            raise HTTPException(
                status_code=404, detail=f"Document splitter not found: {splitter_id}"
            )

        # Check if user has access to this splitter (owner or default)
        if splitter.user_id != current_user.id and not splitter.is_default:
            raise HTTPException(
                status_code=403, detail="Access denied to this splitter configuration"
            )

        logger.info(
            f"Retrieved document splitter '{splitter.name}' ({splitter_id}) for user {current_user.id}"
        )
        return splitter

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document splitter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{splitter_id}", response_model=DocumentSplitter)
async def update_document_splitter(
    splitter_id: str,
    splitter_update: DocumentSplitterUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a document splitter configuration.

    Args:
        splitter_id: The splitter ID
        splitter_update: The update data
        current_user: Current authenticated user

    Returns:
        DocumentSplitter: The updated splitter configuration
    """
    try:
        service = get_document_splitter_service()
        splitter = service.update_splitter(
            splitter_id, splitter_update, current_user.id
        )

        if not splitter:
            raise HTTPException(
                status_code=404, detail=f"Document splitter not found: {splitter_id}"
            )

        logger.info(
            f"Updated document splitter '{splitter.name}' ({splitter_id}) by user {current_user.id}"
        )
        return splitter

    except ValueError as e:
        logger.warning(f"Validation error updating document splitter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission error updating document splitter: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating document splitter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{splitter_id}", status_code=204)
async def delete_document_splitter(
    splitter_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a document splitter configuration.

    Args:
        splitter_id: The splitter ID
        current_user: Current authenticated user
    """
    try:
        service = get_document_splitter_service()
        deleted = service.delete_splitter(splitter_id, current_user.id)

        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Document splitter not found: {splitter_id}"
            )

        logger.info(
            f"Deleted document splitter ({splitter_id}) by user {current_user.id}"
        )

    except ValueError as e:
        logger.warning(f"Validation error deleting document splitter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission error deleting document splitter: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document splitter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{splitter_id}/usage", response_model=dict)
async def get_splitter_usage(
    splitter_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get usage statistics for a document splitter configuration.

    Args:
        splitter_id: The splitter ID
        current_user: Current authenticated user

    Returns:
        dict: Usage statistics including job count and usage metrics
    """
    try:
        service = get_document_splitter_service()
        splitter = service.get_splitter_by_id(splitter_id)

        if not splitter:
            raise HTTPException(
                status_code=404, detail=f"Document splitter not found: {splitter_id}"
            )

        # Check if user has access to this splitter (owner or default)
        if splitter.user_id != current_user.id and not splitter.is_default:
            raise HTTPException(
                status_code=403, detail="Access denied to this splitter configuration"
            )

        # Get additional usage metrics from the database
        from datapilotflow.persistence.mongo.client import MongoClientWrapper

        mongo_wrapper = MongoClientWrapper()
        db = mongo_wrapper.db

        # Count jobs using this splitter
        jobs_count = db["knowledge_jobs"].count_documents({"splitter_id": splitter_id})

        # Get recent usage (jobs created in last 30 days)
        from datetime import datetime, timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs_count = db["knowledge_jobs"].count_documents(
            {"splitter_id": splitter_id, "created_at": {"$gte": thirty_days_ago}}
        )

        usage_stats = {
            "splitter_id": splitter_id,
            "splitter_name": splitter.name,
            "total_usage_count": splitter.usage_count,
            "jobs_using_splitter": jobs_count,
            "recent_jobs_count": recent_jobs_count,
            "is_default": splitter.is_default,
            "created_at": splitter.created_at.isoformat(),
            "last_updated": splitter.updated_at.isoformat(),
        }

        logger.info(
            f"Retrieved usage statistics for splitter '{splitter.name}' ({splitter_id})"
        )
        return usage_stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving splitter usage statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
