"""
Unified Model Provider Service.

This service handles business logic for unified model provider configurations
that support both embedding and generative models.
"""

import inspect
import json
import time
from typing import Any, Dict, List, Optional

from litellm import acompletion, aembedding, rerank
from loguru import logger

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
        self,
        provider_data: ModelProviderCreate,
        user_id: str,
        allow_system: bool = False,
    ) -> Optional[ModelProvider]:
        """
        Create a new model provider configuration.

        Users can only create CUSTOM providers. SYSTEM providers are created
        during system initialization.

        Args:
            provider_data: Provider data to create
            user_id: User ID creating the provider
            allow_system: If True, allows creating SYSTEM providers (for initialization only)
        """
        provider_id = self.model_provider_dao.create_model_provider(
            provider_data, user_id
        )
        if not provider_id:
            raise ValueError("Failed to create model provider configuration")

        # Get and return the created provider
        provider = self.model_provider_dao.get_model_provider(provider_id, user_id)
        if not provider:
            raise ValueError("Failed to retrieve created model provider")

        logger.info(
            f"Created provider '{provider.name}' (id: {provider_id}) for user {user_id}"
        )
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
            api_key=provider.api_key,  # Include full API key, UI will mask it
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

        # Convert to response models (including API key for editing)
        return [
            ModelProviderResponse(
                id=provider.id,
                name=provider.name,
                provider_type=provider.provider_type,
                endpoint=provider.endpoint,
                api_key=provider.api_key,  # Include full API key, UI will mask it
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
        """
        Update an existing model provider configuration.

        System providers can be updated but category cannot be changed.
        Custom providers can be fully updated by their owner.
        """
        # Check if provider exists and get current state
        existing_provider = self.model_provider_dao.get_model_provider(
            provider_id, user_id
        )
        if not existing_provider:
            raise ValueError("Model provider not found")

        success = self.model_provider_dao.update_model_provider(
            provider_id, user_id, update_data
        )
        if not success:
            raise ValueError("Failed to update model provider configuration")

        # Get and return the updated provider
        provider = self.model_provider_dao.get_model_provider(provider_id, user_id)
        if not provider:
            raise ValueError("Failed to retrieve updated model provider")

        logger.info(
            f"Updated provider '{provider.name}' (id: {provider_id}) by user {user_id}"
        )
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

    async def test_model_provider(
        self,
        provider_data: ModelProviderCreate,
        user_id: str,
        test_type: ModelType,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Perform a lightweight live call to validate a provider configuration before saving.

        Returns a dict with success flag, status_code, duration_ms, and a response preview.
        """
        start = time.perf_counter()

        api_key = provider_data.api_key
        base_endpoint = provider_data.endpoint.rstrip("/")

        # LiteLLM expects model identifiers in the form "provider/model_name"
        # so we compose this from provider_type + model_name when available.
        model_identifier = (
            f"{provider_data.provider_type}/{model_name}"
            if provider_data.provider_type
            else model_name
        )

        def common_params() -> Dict[str, Any]:
            params: Dict[str, Any] = {
                "model": model_identifier,
                "api_key": api_key or "",
                "api_base": base_endpoint,
                "timeout": provider_data.timeout or 60,
            }
            return params

        def wrap_result(
            raw: Any, success: bool, message: str = "OK", status_code: int = 200
        ) -> Dict[str, Any]:
            duration_ms = int((time.perf_counter() - start) * 1000)
            body = ""
            try:
                to_dump = raw
                if hasattr(raw, "model_dump"):
                    to_dump = raw.model_dump()
                body = json.dumps(to_dump, default=str, indent=2)[:800]
            except Exception:
                body = str(raw)[:800]
            return {
                "success": success,
                "duration_ms": duration_ms,
                "body": body,
                "message": message,
                "status_code": status_code,
            }

        # Determine URL and payload per test type
        if test_type == ModelType.EMBEDDING:
            if not provider_data.embedding or not provider_data.embedding.models:
                return wrap_result({}, False, "No embedding models configured", 400)
            params = common_params()
            params.update(provider_data.embedding.config or {})
            # Remove client-only fields that LiteLLM does not accept
            params.pop("endpoint_suffix", None)
            params["input"] = ["Health check embedding ping"]
            params["dimensions"] = params.get(
                "dimensions", provider_data.embedding.config.get("dimensions")
            )

            try:
                resp = await aembedding(**params)
                return wrap_result(resp, True, "OK", 200)
            except Exception as e:
                logger.error(f"Embedding test failed: {e}")
                return wrap_result({}, False, str(e), 500)

        if test_type == ModelType.GENERATIVE:
            if not provider_data.generative or not provider_data.generative.models:
                return wrap_result({}, False, "No generative models configured", 400)
            params = common_params()
            params.update(provider_data.generative.config or {})
            # Remove client-only fields that LiteLLM does not accept
            params.pop("endpoint_suffix", None)
            params.pop("max_input_tokens", None)
            params.pop("batch_size", None)

            messages = [{"role": "user", "content": "Hello! Quick connectivity check."}]

            params["messages"] = messages
            params["max_tokens"] = params.get("max_tokens", 50)

            try:
                resp = await acompletion(**params)
                return wrap_result(resp, True, "OK", 200)
            except Exception as e:
                logger.error(f"Generative test failed: {e}")
                return wrap_result({}, False, str(e), 500)

        if test_type == ModelType.RERANKER:
            if not provider_data.reranker or not provider_data.reranker.models:
                return wrap_result({}, False, "No reranker models configured", 400)

            params = common_params()
            params.update(provider_data.reranker.config or {})
            # Remove client-only fields that LiteLLM does not accept
            params.pop("endpoint_suffix", None)
            params["documents"] = [
                "Doc A about AI safety.",
                "Doc B about embedding models.",
                "Doc C about LLM latency.",
            ]
            params["query"] = "Test ranking query"
            params["top_n"] = params.get("top_n", 3)

            try:
                result = rerank(**params)
                if inspect.iscoroutine(result):
                    result = await result
                return wrap_result(result, True, "OK", 200)
            except Exception as e:
                logger.error(f"Reranker test failed: {e}")
                return wrap_result({}, False, str(e), 500)

        return wrap_result({}, False, f"Unsupported test type: {test_type}", 400)

    def get_available_models_for_provider(
        self, provider_type: str, model_type: Optional[ModelType] = None
    ) -> List[str]:
        """
        Get available models for a provider type using LiteLLM SDK.

        This queries the LiteLLM SDK to get all supported models for a given provider.

        Args:
            provider_type: The provider type (e.g., 'openai', 'anthropic', 'groq')
            model_type: Optional filter for model type (embedding, generative, reranker)

        Returns:
            List of available model names for the provider
        """
        try:
            # Import litellm's get_available_models function
            from litellm import get_available_models

            logger.info(f"Fetching available models for provider: {provider_type}")

            # Get all models for this provider from LiteLLM
            available_models = get_available_models(provider=provider_type)

            if not available_models:
                logger.warning(f"No models found for provider: {provider_type}")
                return []

            logger.info(f"Found {len(available_models)} models for provider {provider_type}")
            return available_models

        except Exception as e:
            logger.error(f"Error fetching available models for {provider_type}: {e}")
            # Return empty list on error instead of raising
            return []


# Global service instance
_model_provider_service: Optional[ModelProviderService] = None


def get_model_provider_service() -> ModelProviderService:
    """Get the global model provider service instance."""
    global _model_provider_service
    if _model_provider_service is None:
        _model_provider_service = ModelProviderService()
    return _model_provider_service
