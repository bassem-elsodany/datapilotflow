"""
Model Provider API Router.

This router handles HTTP requests for unified model provider configurations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from loguru import logger

from src.domain.model_provider.model_provider import (
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelProviderResponse,
    ModelType
)
from src.services.model_provider.model_provider_service import ModelProviderService, get_model_provider_service
from src.api.routers.auth.auth_router import get_current_user
from src.domain.user.user import User

router = APIRouter(prefix="/model-providers", tags=["Model Providers"])


@router.post(
    "/",
    response_model=ModelProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model provider",
    description="Create a new unified model provider configuration that supports both embedding and generative models"
)
def create_model_provider(
    provider_data: ModelProviderCreate,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """Create a new model provider configuration."""
    try:
        logger.info(f"Creating model provider: {provider_data.name} for user: {current_user.id}")
        
        created_provider = service.create_model_provider(provider_data, current_user.id)
        if not created_provider:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create model provider"
            )
        
        # Return response without sensitive data
        return service.get_model_provider_response(created_provider.id, current_user.id)
        
    except ValueError as e:
        logger.error(f"Validation error creating model provider: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating model provider: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/",
    response_model=List[ModelProviderResponse],
    summary="List model providers",
    description="List all model provider configurations for the current user"
)
def list_model_providers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    supported_model_type: Optional[ModelType] = Query(None, description="Filter by supported model type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """List model provider configurations for the current user."""
    try:
        logger.info(f"Listing model providers for user: {current_user.id}")
        
        providers = service.list_model_providers(
            current_user.id,
            is_active=is_active,
            provider_type=provider_type,
            supported_model_type=supported_model_type,
            skip=skip,
            limit=limit
        )
        
        return providers
        
    except Exception as e:
        logger.error(f"Error listing model providers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{provider_id}",
    response_model=ModelProviderResponse,
    summary="Get model provider by ID",
    description="Get a specific model provider configuration by ID"
)
def get_model_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """Get a model provider configuration by ID."""
    try:
        logger.info(f"Getting model provider: {provider_id} for user: {current_user.id}")
        
        provider = service.get_model_provider_response(provider_id, current_user.id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model provider not found"
            )
        
        return provider
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model provider: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put(
    "/{provider_id}",
    response_model=ModelProviderResponse,
    summary="Update model provider",
    description="Update an existing model provider configuration"
)
def update_model_provider(
    provider_id: str,
    update_data: ModelProviderUpdate,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """Update a model provider configuration."""
    try:
        logger.info(f"Updating model provider: {provider_id} for user: {current_user.id}")
        
        updated_provider = service.update_model_provider(provider_id, current_user.id, update_data)
        if not updated_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model provider not found"
            )
        
        # Return response without sensitive data
        return service.get_model_provider_response(updated_provider.id, current_user.id)
        
    except ValueError as e:
        logger.error(f"Validation error updating model provider: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model provider: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/active/list",
    response_model=List[ModelProviderResponse],
    summary="List active model providers",
    description="List all active model provider configurations for the current user"
)
def list_active_model_providers(
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """List all active model provider configurations."""
    try:
        logger.info(f"Listing active model providers for user: {current_user.id}")
        
        providers = service.list_model_providers(current_user.id, is_active=True)
        return providers
        
    except Exception as e:
        logger.error(f"Error listing active model providers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/by-type/{model_type}",
    response_model=List[ModelProviderResponse],
    summary="Get providers by model type",
    description="Get model providers that support a specific model type (embedding or generative)"
)
def get_providers_by_type(
    model_type: ModelType,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service)
):
    """Get model providers that support a specific model type."""
    try:
        logger.info(f"Getting providers for model type: {model_type} for user: {current_user.id}")
        
        providers = service.get_providers_by_type(current_user.id, model_type)
        
        # Convert to response models (excluding sensitive data)
        response_providers = []
        for provider in providers:
            response_providers.append(ModelProviderResponse(
                id=provider.id,
                name=provider.name,
                provider_type=provider.provider_type,
                endpoint=provider.endpoint,
                description=provider.description,
                is_active=provider.is_active,
                timeout=provider.timeout,
                embedding=provider.embedding,
                generative=provider.generative,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                updated_by=provider.updated_by
            ))
        
        return response_providers
        
    except Exception as e:
        logger.error(f"Error getting providers by type: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
