"""
Model Provider API Router.

This router handles HTTP requests for unified model provider configurations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel

from src.api.routers.auth.auth_router import get_current_user
from src.domain.model_provider.model_provider import (
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
    ModelType,
)
from src.domain.user.user import User
from src.services.model_provider.model_provider_service import (
    ModelProviderService,
    get_model_provider_service,
)

router = APIRouter(prefix="/model-providers", tags=["Model Providers"])


@router.post(
    "/",
    response_model=ModelProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model provider",
    description="Create a new custom model provider configuration. Users can only create CUSTOM providers. SYSTEM providers are managed by the system.",
)
def create_model_provider(
    provider_data: ModelProviderCreate,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Create a new model provider configuration.

    All providers are user-created; provider types must be OpenAI-compatible.
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


@router.get(
    "/active/list",
    response_model=List[ModelProviderResponse],
    summary="List active model providers",
    description="List all active model provider configurations for the current user",
)
def list_active_model_providers(
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """List all active model provider configurations."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info(f"Listing active model providers for user: {current_user.id}")

        providers = service.list_model_providers(current_user.id, is_active=True)
        return providers

    except Exception as e:
        logger.error(f"Error listing active model providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/by-type/{model_type}",
    response_model=List[ModelProviderResponse],
    summary="Get providers by model type",
    description="Get model providers that support a specific model type (embedding or generative)",
)
def get_providers_by_type(
    model_type: ModelType,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Get model providers that support a specific model type."""
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info(
            f"Getting providers for model type: {model_type} for user: {current_user.id}"
        )

        providers = service.get_providers_by_type(current_user.id, model_type)

        # Convert to response models using service method (includes all fields)
        response_providers = []
        for provider in providers:
            response = service.get_model_provider_response(provider.id, current_user.id)
            if response:
                response_providers.append(response)

        return response_providers

    except Exception as e:
        logger.error(f"Error getting providers by type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


class ModelProviderTestRequest(BaseModel):
    """Request payload for testing model providers without saving them."""

    provider: ModelProviderCreate
    test_type: ModelType
    model: str


@router.post(
    "/test",
    summary="Test model provider before saving",
    description="Perform a live test call against a provider (embedding/generative/reranker) before saving the configuration.",
)
async def test_model_provider(
    request: ModelProviderTestRequest,
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """Run a quick live check against the provided model configuration."""
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


@router.get(
    "/{provider_id}/models",
    response_model=List[str],
    summary="Get supported models for a provider",
    description="Get list of supported models for a specific provider. Filters by model type if provided.",
)
def get_provider_models(
    provider_id: str,
    model_type: Optional[ModelType] = Query(None, description="Filter by model type (embedding, generative, reranker)"),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Get supported models for a specific provider.

    If model_type is provided, returns only models of that type.
    If model_type is not provided, returns all models.
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        provider = service.get_model_provider(provider_id, current_user.id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model provider '{provider_id}' not found",
            )

        models = []

        if model_type is None or model_type == ModelType.EMBEDDING:
            if provider.embedding:
                models.extend(provider.embedding.models)

        if model_type is None or model_type == ModelType.GENERATIVE:
            if provider.generative:
                models.extend(provider.generative.models)

        if model_type is None or model_type == ModelType.RERANKER:
            if provider.reranker:
                models.extend(provider.reranker.models)

        return models

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching provider models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/available-models/{provider_type}",
    response_model=List[str],
    summary="Get available models for a provider type",
    description="Get list of ALL available models from LiteLLM SDK for a specific provider type. This queries the LiteLLM database of supported models.",
)
def get_available_models(
    provider_type: str,
    model_type: Optional[ModelType] = Query(None, description="Filter by model type (embedding, generative, reranker)"),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Get available models for a provider type from LiteLLM SDK.

    This endpoint queries the LiteLLM SDK to get all supported models for a given
    provider type. This is useful for the UI to show users what models are available
    for a provider before they configure it.

    Args:
        provider_type: The provider type (e.g., 'openai', 'anthropic', 'groq')
        model_type: Optional filter for model type

    Returns:
        List of available model names for the provider
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info(f"Fetching available models for provider type: {provider_type}")

        available_models = service.get_available_models_for_provider(provider_type, model_type)

        logger.info(f"Returning {len(available_models)} available models for {provider_type}")
        return available_models

    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available models: {str(e)}",
        )
