"""
VectorDB Collection Router.

This module provides REST API endpoints for inspecting and retrieving
data from vector database collections.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.api.routers.auth.auth_router import get_current_user
from src.domain.user import User
from src.domain.vectordb import (
    CollectionInfo,
    CollectionSchema,
    CollectionStats,
    RecordResponse,
)
from src.services.vectordb import get_vectordb_collection_service

router = APIRouter()


@router.get("/collections", response_model=List[CollectionInfo])
def list_collections(
    current_user: User = Depends(get_current_user),
    service=Depends(get_vectordb_collection_service),
):
    """
    List all vector collections accessible to the user.

    Returns:
        List of collection information including name, dimension, and record count.
    """
    try:
        collections = service.list_collections(user_id=current_user.id)
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}",
        )


@router.get("/collections/{collection_id}", response_model=CollectionInfo)
def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_vectordb_collection_service),
):
    """
    Get detailed information about a specific collection.

    Args:
        collection_id: ID (name) of the collection

    Returns:
        Collection information

    Raises:
        404: Collection not found
    """
    try:
        collection = service.get_collection(collection_id, current_user.id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found",
            )
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}",
        )


@router.get("/collections/{collection_id}/schema", response_model=CollectionSchema)
def get_collection_schema(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_vectordb_collection_service),
):
    """
    Get the schema of a collection.

    Args:
        collection_id: ID (name) of the collection

    Returns:
        Collection schema with field definitions

    Raises:
        404: Collection not found
    """
    try:
        schema = service.get_collection_schema(collection_id, current_user.id)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found",
            )
        return schema
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema for collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection schema: {str(e)}",
        )


@router.get("/collections/{collection_id}/stats", response_model=CollectionStats)
def get_collection_stats(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_vectordb_collection_service),
):
    """
    Get statistical information about a collection.

    Args:
        collection_id: ID (name) of the collection

    Returns:
        Collection statistics including record counts and distribution

    Raises:
        404: Collection not found
    """
    try:
        stats = service.get_collection_stats(collection_id, current_user.id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found",
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection stats: {str(e)}",
        )


@router.get("/collections/{collection_id}/records", response_model=RecordResponse)
def get_collection_records(
    collection_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    source_url: Optional[str] = Query(None, description="Filter by source URL"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
    current_user: User = Depends(get_current_user),
    service=Depends(get_vectordb_collection_service),
):
    """
    Get records from a collection without the vector embeddings.

    This endpoint retrieves metadata and text content from the collection,
    excluding the high-dimensional vector embeddings for performance.

    Args:
        collection_id: ID (name) of the collection
        limit: Number of records to return (max 1000)
        offset: Offset for pagination
        job_id: Optional filter by job ID
        source_url: Optional filter by source URL (partial match)
        search: Optional text search in title and content
        sort_by: Optional field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        Paginated response with records

    Raises:
        404: Collection not found
    """
    try:
        response = service.get_collection_records(
            collection_id=collection_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            job_id=job_id,
            source_url=source_url,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting records for collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection records: {str(e)}",
        )
