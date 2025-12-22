"""
Model Provider API Router.

This router handles HTTP requests for unified model provider configurations.
"""

from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from datapilotflow.domain.model_provider.model_provider import (
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
    ModelType,
)
from datapilotflow.domain.user.user import User
from datapilotflow.services.model_provider.model_provider_service import (
    ModelProviderService,
    get_model_provider_service,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel

from datapilotflow.api.routers.auth.auth_router import get_current_user

router = APIRouter(prefix="/providers", tags=["Model Providers"])


@router.post(
    "/",
    response_model=ModelProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model provider",
    description="Create a new model provider configuration.",
)
def create_model_provider(
    provider_data: ModelProviderCreate,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Create a new model provider configuration.
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info(
            f"Creating model provider: {provider_data.name} for user: {current_user.id}"
        )

        created_provider = service.create_model_provider(provider_data, current_user.id)
        if not created_provider:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create model provider",
            )

        # Return response
        return service.get_model_provider_response(created_provider.id, current_user.id)

    except ValueError as e:
        logger.error(f"Validation error creating model provider: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating model provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",
    response_model=List[ModelProviderResponse],
    summary="List model providers",
    description="List all model provider configurations for the current user",
)
def list_model_providers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    supported_model_type: Optional[ModelType] = Query(
        None, description="Filter by supported model type"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """List model provider configurations for the current user."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info(f"Listing model providers for user: {current_user.id}")

        providers = service.list_model_providers(
            current_user.id,
            is_active=is_active,
            provider_type=provider_type,
            supported_model_type=supported_model_type,
            skip=skip,
            limit=limit,
        )

        return providers

    except Exception as e:
        logger.error(f"Error listing model providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


class ModelProviderTestRequest(BaseModel):
    """Request payload for testing model providers."""

    test_type: ModelType
    model: str


class ModelProviderTestBeforeCreateRequest(BaseModel):
    """Request payload for testing model providers before creation."""

    provider: ModelProviderCreate
    test_type: ModelType
    model: str


@router.post(
    "/test",
    summary="Test model provider before creation",
    description="Perform a live test call against a provider configuration before saving it (embedding/generative/reranker).",
)
async def test_model_provider_before_create(
    request: ModelProviderTestBeforeCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Run a quick live check against a provider configuration before saving."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        result = await service.test_model_provider(
            provider_data=request.provider,
            user_id=current_user.id,
            test_type=request.test_type,
            model_name=request.model,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Provider test failed"),
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{provider_id}/test",
    summary="Test model provider",
    description="Perform a live test call against an existing provider (embedding/generative/reranker).",
)
async def test_model_provider(
    provider_id: str,
    request: ModelProviderTestRequest,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Run a quick live check against an existing provider configuration."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    # Validate that provider_id is a valid MongoDB ObjectId
    try:
        ObjectId(provider_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
        )

    try:
        # Get the provider configuration
        provider = service.get_model_provider(provider_id, current_user.id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
            )

        # Convert provider to ModelProviderCreate for testing
        from datapilotflow.domain.model_provider.model_provider import (
            ModelProviderCreate,
        )

        provider_data = ModelProviderCreate(
            name=provider.name,
            provider_type=provider.provider_type,
            endpoint=provider.endpoint,
            api_key=provider.api_key,
            api_key_field_name=provider.api_key_field_name or "api_key",
            description=provider.description,
            is_active=provider.is_active,
            timeout=provider.timeout,
            embedding=provider.embedding,
            generative=provider.generative,
            reranker=provider.reranker,
        )

        result = await service.test_model_provider(
            provider_data=provider_data,
            user_id=current_user.id,
            test_type=request.test_type,
            model_name=request.model,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Provider test failed"),
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{provider_id}/models",
    response_model=List[str],
    summary="Get available models for a provider",
    description="Get list of ALL available models from LiteLLM SDK for the provider's type. Filters by model type if provided.",
)
def get_provider_models(
    provider_id: str,
    model_type: Optional[ModelType] = Query(
        None, description="Filter by model type (embedding, generative, reranker)"
    ),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Get available models for a specific provider from LiteLLM SDK.

    This endpoint retrieves the provider configuration to get the provider_type,
    then queries LiteLLM SDK to get all available models for that provider type.

    If model_type is provided, returns only models of that type.
    If model_type is not provided, returns all models.
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    # Validate that provider_id is a valid MongoDB ObjectId
    try:
        ObjectId(provider_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model provider '{provider_id}' not found",
        )

    try:
        # Get provider to retrieve provider_type
        provider = service.get_model_provider(provider_id, current_user.id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model provider '{provider_id}' not found",
            )

        # Get available models from LiteLLM SDK for this provider type
        available_models = service.get_available_models_for_provider(
            provider.provider_type, model_type
        )

        logger.info(
            f"Returning {len(available_models)} available models for provider {provider_id} (type: {provider.provider_type})"
        )
        return available_models

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching provider models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{provider_id}",
    response_model=ModelProviderResponse,
    summary="Get model provider by ID",
    description="Get a specific model provider configuration by ID",
)
def get_model_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Get a model provider configuration by ID."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    # Validate that provider_id is a valid MongoDB ObjectId
    # This prevents routes like "/available-models" from being matched
    try:
        ObjectId(provider_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
        )

    try:
        logger.info(
            f"Getting model provider: {provider_id} for user: {current_user.id}"
        )

        provider = service.get_model_provider_response(provider_id, current_user.id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
            )

        return provider

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put(
    "/{provider_id}",
    response_model=ModelProviderResponse,
    summary="Update model provider",
    description="Update an existing model provider configuration",
)
def update_model_provider(
    provider_id: str,
    update_data: ModelProviderUpdate,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Update a model provider configuration."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    # Validate that provider_id is a valid MongoDB ObjectId
    try:
        ObjectId(provider_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
        )

    try:
        logger.info(
            f"Updating model provider: {provider_id} for user: {current_user.id}"
        )

        updated_provider = service.update_model_provider(
            provider_id, current_user.id, update_data
        )
        if not updated_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model provider not found"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
