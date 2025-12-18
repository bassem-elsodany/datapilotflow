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
    expand: Optional[str] = Query(None, description="Comma-separated list of fields to expand. Use 'embedding_provider' to get full provider details."),
    current_user: User = Depends(get_current_user),
    service: VectorDBCollectionService = Depends(get_vectordb_collection_service),
):
    """List all vector DB collection configurations or get a specific collection by name.

    Query Parameters:
    - name: Filter by collection name
    - expand: Comma-separated list of fields to expand (e.g., 'embedding_provider')
    """
    try:
        if name:
            # Get collection by name and return full details for UI display
            existing_collection = service.get_collection_by_name(name)
            if existing_collection:
                # Return full collection config with embedding details for UI
                response = _serialize_collection(existing_collection, expand, current_user.id)
                return response
            else:
                # Collection not found
                return {
                    "collection_name": name,
                    "exists": False,
                    "message": f"Collection name '{name}' is available",
                }
        else:
            # List all collections
            collections = service.list_collections(current_user.id, 0, 1000)
            if expand:
                # Expand requested fields for each collection
                collections = [_serialize_collection(c, expand, current_user.id) for c in collections]
            return collections

    except Exception as e:
        logger.error(f"Error listing/checking vector DB collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def _serialize_collection(collection: VectorDBCollection, expand: Optional[str], user_id: Optional[str]) -> dict:
    """Serialize a collection, optionally expanding provider details.

    Args:
        collection: The collection to serialize
        expand: Comma-separated list of fields to expand
        user_id: User ID for fetching provider details

    Returns:
        Dictionary with collection data and optionally expanded provider details
    """
    response = {
        "id": collection.id,
        "description": collection.description,
        "collection_name": collection.collection_name,
        "embedding_model_provider_id": collection.embedding_model_provider_id,
        "embedding_model_name": collection.embedding_model_name,
        "vector_dimension": collection.vector_dimension,
        "created_at": collection.created_at.isoformat() if hasattr(collection.created_at, 'isoformat') else collection.created_at,
        "created_by": collection.created_by,
    }

    # Expand embedding provider if requested
    if expand and "embedding_provider" in expand:
        response["embedding_provider"] = _expand_embedding_provider(
            collection.embedding_model_provider_id,
            collection.embedding_model_name,
            user_id,
        )

    return response


def _expand_embedding_provider(provider_id: str, model_name: str, user_id: Optional[str]) -> dict:
    """Fetch and return expanded embedding provider details.

    Args:
        provider_id: The provider ID
        model_name: The model name
        user_id: User ID for fetching provider details

    Returns:
        Dictionary with expanded provider information
    """
    try:
        if not user_id:
            # Fallback if user_id is not available
            return {
                "id": provider_id,
                "model_name": model_name,
            }

        from src.services.model_provider.model_provider_service import (
            get_model_provider_service,
        )

        provider_service = get_model_provider_service()
        provider = provider_service.get_model_provider(provider_id, user_id)

        if provider:
            return {
                "id": provider_id,
                "name": provider.name,
                "model_name": model_name,
                "provider_type": provider.provider_type,
                "endpoint": provider.endpoint,
            }
    except Exception as e:
        logger.warning(f"Could not expand embedding provider {provider_id}: {e}")

    # Fallback to basic info
    return {
        "id": provider_id,
        "model_name": model_name,
    }


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
