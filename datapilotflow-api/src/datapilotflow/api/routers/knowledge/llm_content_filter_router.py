"""
LLM Content Filter Router for managing content filter configurations.

This module provides REST API endpoints for CRUD operations on LLM content filter
configurations, which are used to intelligently filter crawled content using LLMs.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.domain.knowledge import (
    LLMContentFilterConfig,
    LLMContentFilterConfigCreate,
    LLMContentFilterConfigUpdate,
)
from datapilotflow.domain.user import User
from datapilotflow.services.knowledge.llm_content_filter_service import (
    get_llm_content_filter_service,
)

router = APIRouter()


@router.get("/", response_model=List[LLMContentFilterConfig])
def get_content_filters(
    enabled: Optional[bool] = Query(
        None, description="Filter by enabled status (true/false)"
    ),
    provider_id: Optional[str] = Query(None, description="Filter by model provider ID"),
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Get all LLM content filter configurations for the current user.

    Query parameters allow filtering by enabled status or model provider.
    """
    try:
        logger.debug(
            f"Getting content filters for user {current_user.id} "
            f"(enabled={enabled}, provider_id={provider_id})"
        )

        # Get filters based on query parameters
        if enabled is not None and enabled:
            # Get only enabled filters
            filters = service.get_enabled_configs(current_user.id)
        elif provider_id:
            # Get filters by provider
            filters = service.get_configs_by_provider(provider_id, current_user.id)
        else:
            # Get all filters
            filters = service.get_all_configs(current_user.id)

        logger.info(
            f"Retrieved {len(filters)} content filter configs for user {current_user.id}"
        )
        return filters

    except Exception as e:
        logger.error(f"Error retrieving content filter configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content filter configurations: {str(e)}",
        )


@router.post(
    "/", response_model=LLMContentFilterConfig, status_code=status.HTTP_201_CREATED
)
def create_content_filter(
    config_data: LLMContentFilterConfigCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Create a new LLM content filter configuration.

    The configuration includes the LLM provider, model, filtering instructions,
    and various processing parameters.
    """
    try:
        logger.info(
            f"Creating content filter config '{config_data.name}' for user {current_user.id}"
        )

        config_id = service.create_config(config_data, current_user.id)

        if not config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create content filter configuration. Check that the provider and model are valid.",
            )

        # Retrieve the created configuration
        config = service.get_config(config_id, current_user.id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuration created but could not be retrieved",
            )

        logger.info(f"Created content filter config: {config_id}")
        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating content filter config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create content filter configuration: {str(e)}",
        )


@router.get("/{filter_id}", response_model=LLMContentFilterConfig)
def get_content_filter(
    filter_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Get a specific LLM content filter configuration by ID."""
    try:
        logger.debug(
            f"Getting content filter config {filter_id} for user {current_user.id}"
        )

        config = service.get_config(filter_id, current_user.id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content filter configuration not found: {filter_id}",
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving content filter config {filter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content filter configuration: {str(e)}",
        )


@router.put("/{filter_id}", response_model=LLMContentFilterConfig)
def update_content_filter(
    filter_id: str,
    update_data: LLMContentFilterConfigUpdate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Update an existing LLM content filter configuration."""
    try:
        logger.info(
            f"Updating content filter config {filter_id} for user {current_user.id}"
        )

        updated_config = service.update_config(filter_id, current_user.id, update_data)

        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content filter configuration not found or update failed: {filter_id}",
            )

        logger.info(f"Updated content filter config: {filter_id}")
        return updated_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content filter config {filter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update content filter configuration: {str(e)}",
        )


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content_filter(
    filter_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Delete an LLM content filter configuration.

    Note: Jobs using this filter will have their filter reference set to null.
    """
    try:
        logger.info(
            f"Deleting content filter config {filter_id} for user {current_user.id}"
        )

        success = service.delete_config(filter_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content filter configuration not found: {filter_id}",
            )

        logger.info(f"Deleted content filter config: {filter_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content filter config {filter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content filter configuration: {str(e)}",
        )


@router.post("/{filter_id}/validate")
def validate_content_filter(
    filter_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_llm_content_filter_service),
):
    """Validate an LLM content filter configuration.

    Checks:
    - Provider exists and is active
    - Provider supports generative models
    - Specified model is available in the provider
    """
    try:
        logger.debug(f"Validating content filter config {filter_id}")

        # Get the configuration
        config = service.get_config(filter_id, current_user.id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content filter configuration not found: {filter_id}",
            )

        # Validate the configuration
        is_valid, error_message = service.validate_config(config, current_user.id)

        return {
            "valid": is_valid,
            "error": error_message if not is_valid else None,
            "filter_id": filter_id,
            "filter_name": config.name,
            "provider_id": config.llm_provider_id,
            "model_name": config.llm_model_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating content filter config {filter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate content filter configuration: {str(e)}",
        )
