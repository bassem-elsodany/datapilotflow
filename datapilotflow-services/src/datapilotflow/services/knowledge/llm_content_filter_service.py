"""
LLM Content Filter Service module.

This module provides business logic for managing LLM Content Filter configurations,
including validation, CRUD operations, and integration with model providers.
"""

from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.llm_content_filter_config import (
    LLMContentFilterConfig,
    LLMContentFilterConfigCreate,
    LLMContentFilterConfigUpdate,
)
from datapilotflow.infrastructure.dao.knowledge import LLMContentFilterDAO
from datapilotflow.services.model_provider.model_provider_service import ModelProviderService


class LLMContentFilterService:
    """Service for managing LLM Content Filter configurations."""

    def __init__(
        self,
        llm_filter_dao: LLMContentFilterDAO,
        model_provider_service: ModelProviderService,
    ):
        """Initialize the LLM Content Filter Service.

        Args:
            llm_filter_dao: DAO for LLM content filter operations
            model_provider_service: Service for model provider operations
        """
        self.llm_filter_dao = llm_filter_dao
        self.model_provider_service = model_provider_service

    def create_config(
        self, config_data: LLMContentFilterConfigCreate, user_id: str
    ) -> Optional[str]:
        """Create a new LLM content filter configuration.

        Args:
            config_data: Configuration data
            user_id: ID of the user creating the configuration

        Returns:
            ID of the created configuration, or None if creation failed
        """
        try:
            # Validate that the model provider exists and supports generative models
            provider = self.model_provider_service.get_model_provider(
                config_data.llm_provider_id, user_id
            )
            if not provider:
                logger.error(f"Model provider not found: {config_data.llm_provider_id}")
                return None

            # Check if provider has generative models
            if not provider.generative or not provider.generative.models:
                logger.error(
                    f"Provider {provider.name} does not support generative models"
                )
                return None

            # Validate that the model is available in the provider
            if config_data.llm_model_name not in provider.generative.models:
                logger.error(
                    f"Model {config_data.llm_model_name} not found in provider {provider.name}"
                )
                logger.error(f"Available models: {provider.generative.models}")
                return None

            # Create the configuration
            config_id = self.llm_filter_dao.create(config_data, user_id)

            if config_id:
                logger.info(
                    f"Created LLM content filter config {config_id} for user {user_id}"
                )
            else:
                logger.error(f"Failed to create LLM content filter config")

            return config_id

        except Exception as e:
            logger.error(f"Error creating LLM content filter config: {e}")
            return None

    def get_config(
        self, config_id: str, user_id: str
    ) -> Optional[LLMContentFilterConfig]:
        """Get an LLM content filter configuration by ID.

        Args:
            config_id: ID of the configuration
            user_id: ID of the user (for access control)

        Returns:
            LLM content filter configuration if found, None otherwise
        """
        try:
            config = self.llm_filter_dao.get_by_id(config_id, user_id)

            if config:
                logger.debug(f"Retrieved LLM content filter config: {config_id}")
            else:
                logger.warning(f"LLM content filter config not found: {config_id}")

            return config

        except Exception as e:
            logger.error(f"Error retrieving LLM content filter config {config_id}: {e}")
            return None

    def get_all_configs(self, user_id: str) -> List[LLMContentFilterConfig]:
        """Get all LLM content filter configurations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of LLM content filter configurations
        """
        try:
            configs = self.llm_filter_dao.get_all(user_id)
            logger.debug(
                f"Retrieved {len(configs)} LLM content filter configs for user {user_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving LLM content filter configs for user {user_id}: {e}"
            )
            return []

    def get_enabled_configs(self, user_id: str) -> List[LLMContentFilterConfig]:
        """Get all enabled LLM content filter configurations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of enabled LLM content filter configurations
        """
        try:
            configs = self.llm_filter_dao.get_enabled(user_id)
            logger.debug(
                f"Retrieved {len(configs)} enabled LLM content filter configs for user {user_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving enabled LLM content filter configs for user {user_id}: {e}"
            )
            return []

    def update_config(
        self,
        config_id: str,
        user_id: str,
        update_data: LLMContentFilterConfigUpdate,
    ) -> Optional[LLMContentFilterConfig]:
        """Update an LLM content filter configuration.

        Args:
            config_id: ID of the configuration to update
            user_id: ID of the user (for access control)
            update_data: Updated configuration data

        Returns:
            Updated configuration if successful, None otherwise
        """
        try:
            # Validate provider and model if they're being updated
            if update_data.llm_provider_id or update_data.llm_model_name:
                # Get current config to check provider/model
                current_config = self.llm_filter_dao.get_by_id(config_id, user_id)
                if not current_config:
                    logger.error(
                        f"LLM content filter config not found for update: {config_id}"
                    )
                    return None

                # Determine which provider and model to validate
                provider_id = (
                    update_data.llm_provider_id or current_config.llm_provider_id
                )
                model_name = update_data.llm_model_name or current_config.llm_model_name

                # Validate provider
                provider = self.model_provider_service.get_model_provider(
                    provider_id, user_id
                )
                if not provider:
                    logger.error(f"Model provider not found: {provider_id}")
                    return None

                # Check if provider has generative models
                if not provider.generative or not provider.generative.models:
                    logger.error(
                        f"Provider {provider.name} does not support generative models"
                    )
                    return None

                # Validate model
                if model_name not in provider.generative.models:
                    logger.error(
                        f"Model {model_name} not found in provider {provider.name}"
                    )
                    return None

            # Update the configuration
            success = self.llm_filter_dao.update(config_id, user_id, update_data)

            if not success:
                logger.error(f"Failed to update LLM content filter config: {config_id}")
                return None

            # Retrieve and return the updated configuration
            updated_config = self.llm_filter_dao.get_by_id(config_id, user_id)
            logger.info(f"Updated LLM content filter config: {config_id}")
            return updated_config

        except Exception as e:
            logger.error(f"Error updating LLM content filter config {config_id}: {e}")
            return None

    def delete_config(self, config_id: str, user_id: str) -> bool:
        """Delete an LLM content filter configuration.

        Args:
            config_id: ID of the configuration to delete
            user_id: ID of the user (for access control)

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if any jobs are using this filter config
            # This would be done through the job service
            # For now, we'll allow deletion and handle orphaned references

            success = self.llm_filter_dao.delete(config_id, user_id)

            if success:
                logger.info(f"Deleted LLM content filter config: {config_id}")
            else:
                logger.warning(
                    f"Failed to delete LLM content filter config: {config_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error deleting LLM content filter config {config_id}: {e}")
            return False

    def get_configs_by_provider(
        self, provider_id: str, user_id: str
    ) -> List[LLMContentFilterConfig]:
        """Get all LLM content filter configurations using a specific provider.

        Args:
            provider_id: ID of the model provider
            user_id: ID of the user

        Returns:
            List of LLM content filter configurations
        """
        try:
            configs = self.llm_filter_dao.get_by_provider(provider_id, user_id)
            logger.debug(
                f"Retrieved {len(configs)} LLM content filter configs for provider {provider_id}"
            )
            return configs

        except Exception as e:
            logger.error(
                f"Error retrieving LLM content filter configs by provider {provider_id}: {e}"
            )
            return []

    def validate_config(
        self, config: LLMContentFilterConfig, user_id: str
    ) -> tuple[bool, str]:
        """Validate an LLM content filter configuration.

        Args:
            config: Configuration to validate
            user_id: ID of the user (for access control)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if provider exists
            provider = self.model_provider_service.get_model_provider(
                config.llm_provider_id, user_id
            )
            if not provider:
                return False, f"Model provider not found: {config.llm_provider_id}"

            # Check if provider supports generative models
            if not provider.generative or not provider.generative.models:
                return (
                    False,
                    f"Provider {provider.name} does not support generative models",
                )

            # Check if model is available
            if config.llm_model_name not in provider.generative.models:
                return (
                    False,
                    f"Model {config.llm_model_name} not found in provider {provider.name}",
                )

            # Check if provider is active
            if not provider.is_active:
                return False, f"Provider {provider.name} is not active"

            return True, ""

        except Exception as e:
            logger.error(f"Error validating LLM content filter config: {e}")
            return False, str(e)


# Factory function to create service instance
_llm_content_filter_service_instance: Optional[LLMContentFilterService] = None


def get_llm_content_filter_service() -> LLMContentFilterService:
    """Get the LLM Content Filter Service singleton instance.

    Returns:
        LLMContentFilterService instance
    """
    global _llm_content_filter_service_instance

    if _llm_content_filter_service_instance is None:
        from datapilotflow.services.model_provider.model_provider_service import (
            get_model_provider_service,
        )

        llm_filter_dao = LLMContentFilterDAO()
        model_provider_service = get_model_provider_service()

        _llm_content_filter_service_instance = LLMContentFilterService(
            llm_filter_dao, model_provider_service
        )

    return _llm_content_filter_service_instance
