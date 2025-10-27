"""
Unified Model Provider Service.

This service handles business logic for unified model provider configurations
that support both embedding and generative models.
"""

from typing import List, Optional

from src.domain.model_provider.model_provider import (
    ModelProvider,
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
    ModelType,
)
from src.services.model_provider.dao import ModelProviderDAO


class ModelProviderService:
    """Service for managing unified model provider configurations."""

    def __init__(self):
        self.model_provider_dao = ModelProviderDAO()

    def create_model_provider(
        self, provider_data: ModelProviderCreate, user_id: str
    ) -> Optional[ModelProvider]:
        """Create a new model provider configuration."""

        provider_id = self.model_provider_dao.create_model_provider(
            provider_data, user_id
        )
        if not provider_id:
            raise ValueError("Failed to create model provider configuration")

        # Get and return the created provider
        provider = self.model_provider_dao.get_model_provider(provider_id, user_id)
        if not provider:
            raise ValueError("Failed to retrieve created model provider")

        return provider

    def get_model_provider(
        self, provider_id: str, user_id: str
    ) -> Optional[ModelProvider]:
        """Get a model provider configuration by ID."""
        return self.model_provider_dao.get_model_provider(provider_id, user_id)

    def get_model_provider_response(
        self, provider_id: str, user_id: str
    ) -> Optional[ModelProviderResponse]:
        """Get a model provider response (without sensitive data) by ID."""
        provider = self.get_model_provider(provider_id, user_id)
        if not provider:
            return None

        return ModelProviderResponse(
            id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type,
            endpoint=provider.endpoint,
            description=provider.description,
            is_active=provider.is_active,
            timeout=provider.timeout,
            embedding=provider.embedding,
            generative=provider.generative,
            reranker=provider.reranker,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
            created_by=provider.created_by,
            updated_by=provider.updated_by,
        )

    def list_model_providers(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        provider_type: Optional[str] = None,
        supported_model_type: Optional[ModelType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelProviderResponse]:
        """List model provider configurations for a user."""
        providers = self.model_provider_dao.list_model_providers(
            user_id, is_active, provider_type, supported_model_type, skip, limit
        )

        # Convert to response models (excluding sensitive data)
        return [
            ModelProviderResponse(
                id=provider.id,
                name=provider.name,
                provider_type=provider.provider_type,
                endpoint=provider.endpoint,
                description=provider.description,
                is_active=provider.is_active,
                timeout=provider.timeout,
                embedding=provider.embedding,
                generative=provider.generative,
                reranker=provider.reranker,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                updated_by=provider.updated_by,
            )
            for provider in providers
        ]

    def update_model_provider(
        self, provider_id: str, user_id: str, update_data: ModelProviderUpdate
    ) -> Optional[ModelProvider]:
        """Update an existing model provider configuration."""

        success = self.model_provider_dao.update_model_provider(
            provider_id, user_id, update_data
        )
        if not success:
            raise ValueError("Failed to update model provider configuration")

        # Get and return the updated provider
        provider = self.model_provider_dao.get_model_provider(provider_id, user_id)
        if not provider:
            raise ValueError("Failed to retrieve updated model provider")

        return provider

    def get_active_model_providers(self, user_id: str) -> List[ModelProvider]:
        """Get all active model providers for a user."""
        return self.model_provider_dao.get_active_model_providers(user_id)

    def get_providers_by_type(
        self, user_id: str, model_type: ModelType
    ) -> List[ModelProvider]:
        """Get model providers that support a specific model type."""
        return self.model_provider_dao.get_providers_by_type(user_id, model_type)

    def get_provider_by_name(
        self, user_id: str, provider_name: str
    ) -> Optional[ModelProvider]:
        """Get a model provider by name."""
        return self.model_provider_dao.get_provider_by_name(user_id, provider_name)


# Global service instance
_model_provider_service: Optional[ModelProviderService] = None


def get_model_provider_service() -> ModelProviderService:
    """Get the global model provider service instance."""
    global _model_provider_service
    if _model_provider_service is None:
        _model_provider_service = ModelProviderService()
    return _model_provider_service
