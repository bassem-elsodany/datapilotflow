"""
LiteLLM Provider Types Router.

This router handles endpoints for querying LiteLLM SDK metadata.
"""

from typing import List, Optional

from datapilotflow.domain.model_provider.model_provider import ModelType
from datapilotflow.domain.user.user import User
from datapilotflow.services.model_provider.model_provider_service import (
    ModelProviderService,
    get_model_provider_service,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from datapilotflow.api.routers.auth.auth_router import get_current_user

router = APIRouter(prefix="/litellm-providers", tags=["LiteLLM Metadata"])


@router.get(
    "/",
    response_model=List[str],
    summary="Get all available provider names",
    description="Get list of ALL available provider names from LiteLLM SDK. Returns provider names sorted alphabetically.",
)
def get_available_provider_names(
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Get all available provider names from LiteLLM SDK.

    This endpoint queries the LiteLLM SDK to get all supported provider names.
    This is useful for the UI to dynamically populate the provider name dropdown.

    Returns:
        List of available provider names, sorted alphabetically
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    try:
        logger.info("Fetching all available provider names")

        provider_names = service.get_available_provider_types()

        logger.info(f"Returning {len(provider_names)} provider names")
        logger.debug(f"Provider list: {sorted(provider_names)}")
        logger.debug(f"EPAM-DIAL in response: {'epam-dial' in provider_names}")
        return provider_names

    except Exception as e:
        logger.error(f"Error fetching available provider names: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available provider names: {str(e)}",
        )


@router.get(
    "/{provider_name}/models",
    response_model=List[str],
    summary="Get available models for a provider",
    description="Get list of ALL available models from LiteLLM SDK for a specific provider. This queries the LiteLLM database of supported models.",
)
def get_available_models(
    provider_name: str,
    model_type: Optional[ModelType] = Query(
        None, description="Filter by model type (embedding, generative, reranker)"
    ),
    current_user: User = Depends(get_current_user),
    service: ModelProviderService = Depends(get_model_provider_service),
):
    """
    Get available models for a provider from LiteLLM SDK.

    This endpoint queries the LiteLLM SDK to get all supported models for a given
    provider. This is useful for the UI to show users what models are available
    for a provider before they configure it.

    Args:
        provider_name: The provider name (e.g., 'openai', 'anthropic', 'groq')
        model_type: Optional filter for model type

    Returns:
        List of available model names for the provider
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID is required"
        )

    # Validate provider_name is not empty
    if not provider_name or not provider_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider name is required and cannot be empty",
        )

    try:
        logger.info(f"Fetching available models for provider: {provider_name}")

        available_models = service.get_available_models_for_provider(
            provider_name, model_type
        )

        logger.info(
            f"Returning {len(available_models)} available models for {provider_name}"
        )
        return available_models

    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available models: {str(e)}",
        )
