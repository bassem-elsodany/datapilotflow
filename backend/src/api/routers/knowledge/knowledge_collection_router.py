"""
Knowledge VectorDB Collection API Router.

This router provides REST endpoints for managing knowledge vector database collection configurations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.api.routers.auth.auth_router import get_current_user
from src.domain.knowledge.vectordb_collection import (
    VectorDBCollection,
    VectorDBCollectionCreate,
    VectorDBCollectionUpdate,
)
from src.domain.user import User
from src.services.knowledge.vectordb_collection_service import (
    VectorDBCollectionService,
    get_vectordb_collection_service,
)

knowledge_collection_router = APIRouter()


@knowledge_collection_router.get("/")
def list_vectordb_collections(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """List all vector DB collection configurations or check if a specific name exists."""
    try:
        if name:
            # Check if collection name exists
            existing_collection = service.get_collection_by_name(name)
            return {
                "collection_name": name,
                "exists": existing_collection is not None,
                "message": (
                    f"Collection name '{name}' already exists"
                    if existing_collection
                    else f"Collection name '{name}' is available"
                ),
            }
        else:
            # List all collections
            collections = service.list_collections(current_user.id, 0, 1000)
            return collections

    except Exception as e:
        logger.error(f"Error listing/checking vector DB collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@knowledge_collection_router.get("/{collection_id}", response_model=VectorDBCollection)
def get_vectordb_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """Get a specific vector DB collection configuration."""
    try:
        collection = service.get_collection(collection_id, current_user.id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector DB collection not found",
            )
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vector DB collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@knowledge_collection_router.post("/", response_model=VectorDBCollection)
def create_vectordb_collection(
    collection_data: VectorDBCollectionCreate,
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """Create a new vector DB collection configuration."""
    try:
        collection = service.create_collection(collection_data, current_user.id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create vector DB collection",
            )
        return collection
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vector DB collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@knowledge_collection_router.put("/{collection_id}", response_model=VectorDBCollection)
def update_vectordb_collection(
    collection_id: str,
    update_data: VectorDBCollectionUpdate,
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """Update a vector DB collection configuration."""
    try:
        collection = service.update_collection(
            collection_id, current_user.id, update_data
        )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector DB collection not found",
            )
        return collection
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vector DB collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@knowledge_collection_router.delete(
    "/{collection_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_vectordb_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """Delete a vector DB collection configuration."""
    try:
        deleted = service.delete_collection(collection_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector DB collection not found",
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vector DB collection {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
