"""
Unified Model Provider Service.

This service handles business logic for unified model provider configurations
that support both embedding and generative models.
"""

import inspect
import json
import time
import traceback
from typing import Any, Dict, List, Optional

from datapilotflow.domain.model_provider.model_provider import (
    ModelProvider,
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
    ModelType,
)
from datapilotflow.infrastructure.dao.model_provider import ModelProviderDAO
from litellm import acompletion, aembedding, rerank
from loguru import logger

# Register JSON-based providers with LiteLLM
from datapilotflow.services.model_provider.json_loader import (
    register_json_providers_with_litellm,
)

register_json_providers_with_litellm()


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
            api_key_field_name=provider.api_key_field_name or "api_key",
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
                api_key_field_name=provider.api_key_field_name or "api_key",
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
        api_key_field_name = provider_data.api_key_field_name or "api_key"
        base_endpoint = provider_data.endpoint.rstrip("/")

        # Determine the endpoint to use for this test type
        # Check if there's a model-type-specific endpoint (e.g., generative.endpoint)
        # If present, concatenate it with the base endpoint
        endpoint_to_use = base_endpoint
        if (
            test_type == ModelType.EMBEDDING
            and provider_data.embedding
            and provider_data.embedding.endpoint
        ):
            # Concatenate base endpoint with model-type-specific endpoint
            specific_endpoint = provider_data.embedding.endpoint.strip()
            if specific_endpoint:
                # Ensure proper concatenation (handle leading/trailing slashes)
                if specific_endpoint.startswith("/"):
                    endpoint_to_use = f"{base_endpoint}{specific_endpoint}"
                else:
                    endpoint_to_use = f"{base_endpoint}/{specific_endpoint}"
        elif (
            test_type == ModelType.GENERATIVE
            and provider_data.generative
            and provider_data.generative.endpoint
        ):
            # Concatenate base endpoint with model-type-specific endpoint
            specific_endpoint = provider_data.generative.endpoint.strip()
            if specific_endpoint:
                # Ensure proper concatenation (handle leading/trailing slashes)
                if specific_endpoint.startswith("/"):
                    endpoint_to_use = f"{base_endpoint}{specific_endpoint}"
                else:
                    endpoint_to_use = f"{base_endpoint}/{specific_endpoint}"
        elif (
            test_type == ModelType.RERANKER
            and provider_data.reranker
            and provider_data.reranker.endpoint
        ):
            # Concatenate base endpoint with model-type-specific endpoint
            specific_endpoint = provider_data.reranker.endpoint.strip()
            if specific_endpoint:
                # Ensure proper concatenation (handle leading/trailing slashes)
                if specific_endpoint.startswith("/"):
                    endpoint_to_use = f"{base_endpoint}{specific_endpoint}"
                else:
                    endpoint_to_use = f"{base_endpoint}/{specific_endpoint}"

        # LiteLLM expects model identifiers in the form "provider/model_name"
        # so we compose this from provider_type + model_name when available.
        model_identifier = (
            f"{provider_data.provider_type}/{model_name}"
            if provider_data.provider_type
            else model_name
        )

        # Log test initiation with key details (masking sensitive data)
        logger.debug(
            f"Starting {test_type.value} test for provider '{provider_data.name}' "
            f"(type: {provider_data.provider_type}, model: {model_identifier}, "
            f"endpoint: {endpoint_to_use}, api_key_field: {api_key_field_name}, "
            f"has_api_key: {bool(api_key)})"
        )

        def common_params() -> Dict[str, Any]:
            params: Dict[str, Any] = {
                "model": model_identifier,
                "api_base": endpoint_to_use,
                "timeout": provider_data.timeout or 60,
            }

            # Handle API key
            if api_key:
                # Always set api_key parameter for LiteLLM compatibility
                params["api_key"] = api_key

                # If custom API key field name is specified (different from "api_key"),
                # also set it in extra_headers. This is needed when:
                # 1. Using a proxy that requires a custom header name
                # 2. Custom providers that don't follow LiteLLM's standard header names
                # The extra_headers will override/add to LiteLLM's default headers
                if api_key_field_name and api_key_field_name != "api_key":
                    if "extra_headers" not in params:
                        params["extra_headers"] = {}
                    params["extra_headers"][api_key_field_name] = api_key

            return params

        def log_params_for_debug(params: Dict[str, Any], test_type: str) -> None:
            """Log parameters being sent to LiteLLM (masking sensitive data)."""
            safe_params = params.copy()
            # Mask API key
            if "api_key" in safe_params:
                safe_params["api_key"] = (
                    f"{safe_params['api_key'][:4]}...{safe_params['api_key'][-4:]}"
                    if len(safe_params["api_key"]) > 8
                    else "***"
                )
            # Mask API key in extra_headers if present
            if "extra_headers" in safe_params:
                safe_headers = safe_params["extra_headers"].copy()
                for key, value in safe_headers.items():
                    if isinstance(value, str) and len(value) > 8:
                        safe_headers[key] = f"{value[:4]}...{value[-4:]}"
                    else:
                        safe_headers[key] = "***"
                safe_params["extra_headers"] = safe_headers

            logger.debug(
                f"LiteLLM {test_type} test parameters: {json.dumps(safe_params, indent=2, default=str)}"
            )

        def extract_error_message(exception: Exception) -> str:
            """Extract a user-friendly error message from an exception."""
            # Try to get message attribute first (common in many exception types)
            message = getattr(exception, "message", None)
            if message:
                return str(message)

            # Try to get status_message (LiteLLM exceptions sometimes have this)
            status_message = getattr(exception, "status_message", None)
            if status_message:
                return str(status_message)

            # For LiteLLM exceptions, try to extract the meaningful part
            error_str = str(exception)

            # If it's a LiteLLM exception with format like:
            # "litellm.BadGatewayError: BadGatewayError: OpenAIException - No route"
            # or "litellm.BadGatewayError: AnthropicException BadGatewayError - No route"
            # Extract the last meaningful part after the last colon or dash
            if "litellm." in error_str or "LiteLLM" in error_str:
                # Split by colon and take the last meaningful part
                parts = error_str.split(":")
                if len(parts) > 1:
                    # Take the last part and clean it up
                    meaningful_part = parts[-1].strip()
                    # Remove redundant prefixes like "AnthropicException", "OpenAIException", "BadGatewayError" if present
                    exception_prefixes = [
                        "AnthropicException",
                        "OpenAIException",
                        "BadGatewayError",
                        "AuthenticationError",
                        "TimeoutError",
                        "RateLimitError",
                    ]
                    for prefix in exception_prefixes:
                        if meaningful_part.startswith(prefix):
                            meaningful_part = meaningful_part.replace(
                                prefix, ""
                            ).strip()
                    # Remove leading dashes and colons
                    meaningful_part = meaningful_part.lstrip("- :").strip()
                    if meaningful_part:
                        return meaningful_part

            # Fall back to the full string representation
            return error_str

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

            log_params_for_debug(params, "embedding")

            try:
                resp = await aembedding(**params)
                logger.debug(f"Embedding test succeeded for model: {model_identifier}")
                return wrap_result(resp, True, "OK", 200)
            except Exception as e:
                error_message = extract_error_message(e)
                logger.error(
                    f"Embedding test failed for model '{model_identifier}': {error_message}"
                )
                logger.error(f"Full exception: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception attributes: {dir(e)}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                # Try to extract status code from exception if available
                status_code = (
                    getattr(e, "status_code", None) or getattr(e, "code", None) or 500
                )
                return wrap_result({}, False, error_message, status_code)

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

            log_params_for_debug(params, "generative")

            try:
                resp = await acompletion(**params)
                logger.debug(f"Generative test succeeded for model: {model_identifier}")
                return wrap_result(resp, True, "OK", 200)
            except Exception as e:
                error_message = extract_error_message(e)
                logger.error(
                    f"Generative test failed for model '{model_identifier}': {error_message}"
                )
                logger.error(f"Full exception: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception attributes: {dir(e)}")
                # Log response/request details if available
                response = getattr(e, "response", None)
                if response:
                    logger.error(f"Exception response: {response}")
                request = getattr(e, "request", None)
                if request:
                    logger.error(f"Exception request: {request}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                # Try to extract status code from exception if available
                status_code = (
                    getattr(e, "status_code", None) or getattr(e, "code", None) or 500
                )
                return wrap_result({}, False, error_message, status_code)

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

            log_params_for_debug(params, "reranker")

            try:
                result = rerank(**params)
                if inspect.iscoroutine(result):
                    result = await result
                logger.debug(f"Reranker test succeeded for model: {model_identifier}")
                return wrap_result(result, True, "OK", 200)
            except Exception as e:
                error_message = extract_error_message(e)
                logger.error(
                    f"Reranker test failed for model '{model_identifier}': {error_message}"
                )
                logger.error(f"Full exception: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception attributes: {dir(e)}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                # Try to extract status code from exception if available
                status_code = (
                    getattr(e, "status_code", None) or getattr(e, "code", None) or 500
                )
                return wrap_result({}, False, error_message, status_code)

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
            # Import litellm's models_by_provider to get available models
            from litellm import models_by_provider

            logger.info(f"Fetching available models for provider: {provider_type}")

            # Get all models for this provider from LiteLLM
            if provider_type not in models_by_provider:
                logger.warning(
                    f"Provider '{provider_type}' not found in LiteLLM models_by_provider"
                )
                return []

            available_models = list(models_by_provider[provider_type])

            if not available_models:
                logger.warning(f"No models found for provider: {provider_type}")
                return []

            # Strip provider prefix if it exists (e.g., "azure_ai/model-name" -> "model-name")
            # This makes the model names cleaner in the UI
            cleaned_models = []
            prefix = f"{provider_type}/"
            for model in available_models:
                if model.startswith(prefix):
                    cleaned_models.append(model[len(prefix) :])
                else:
                    cleaned_models.append(model)

            logger.info(
                f"Found {len(cleaned_models)} models for provider {provider_type}"
            )
            return cleaned_models

        except Exception as e:
            logger.error(f"Error fetching available models for {provider_type}: {e}")
            # Return empty list on error instead of raising
            return []

    def get_available_provider_types(self) -> List[str]:
        """
        Get all available provider types from LiteLLM SDK.

        Returns:
            List of available provider type names, sorted alphabetically
        """
        try:
            # Import litellm's models_by_provider to get all provider types
            from litellm import models_by_provider

            logger.info("Fetching all available provider types from LiteLLM")

            # Get all provider types from LiteLLM
            provider_types = list(models_by_provider.keys())

            # Sort alphabetically
            provider_types.sort()

            logger.info(f"Found {len(provider_types)} provider types")
            return provider_types

        except Exception as e:
            logger.error(f"Error fetching available provider types: {e}")
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
