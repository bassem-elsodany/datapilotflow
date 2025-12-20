"""
Unified Model Provider Initialization Service.

This service handles the initialization of predefined model providers during system startup.
These providers support both embedding and generative models with a single API key.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from datapilotflow.domain.model_provider.model_provider import ModelProviderCreate, ModelType
from datapilotflow.services.model_provider.model_provider_service import ModelProviderService


class ModelProviderInitializationService:
    """Service for initializing predefined unified model providers."""

    def __init__(self):
        self.model_provider_service = ModelProviderService()

    def get_predefined_model_providers(self) -> List[Dict[str, Any]]:
        """Get the list of predefined unified model providers.

        Note:
            We currently initialize only the OpenAI provider for each user.
            Additional providers can be (re)introduced here in the future if needed.
        """
        return [
            {
                "name": "OpenAI",
                "provider_type": "openai",
                "endpoint": "https://api.openai.com/v1",
                "api_key": None,
                "description": "OpenAI's unified provider for both embedding and generative models",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": [
                        "text-embedding-3-small",
                        "text-embedding-3-large",
                        "text-embedding-ada-002",
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8191,
                        "batch_size": 100,
                    },
                },
                "generative": {
                    "models": [
                        "gpt-5",
                        "gpt-5-mini",
                        "gpt-5-nano",
                        "gpt-5-chat-latest",
                        "gpt-4o",
                        "gpt-4o-2024-11-20",
                        "gpt-4o-2024-08-06",
                        "gpt-4o-mini",
                        "gpt-4o-mini-2024-07-18",
                        "gpt-4-turbo",
                        "gpt-4-turbo-2024-04-09",
                        "gpt-4",
                        "gpt-4-32k",
                        "gpt-3.5-turbo",
                        "gpt-3.5-turbo-16k",
                    ],
                    "config": {
                        "endpoint_suffix": "/chat/completions",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0,
                    },
                },
                "reranker": None,  # OpenAI can be used for reranking but not primary role
            },
        ]

    async def initialize_predefined_model_providers(self, admin_user_id: str) -> bool:
        """Initialize predefined model providers in the database."""
        try:
            logger.info("Starting initialization of predefined model providers")

            predefined_providers = self.get_predefined_model_providers()

            for provider_data in predefined_providers:
                try:
                    # Check if provider already exists
                    existing_provider = (
                        self.model_provider_service.get_provider_by_name(
                            admin_user_id, provider_data["name"]
                        )
                    )

                    if existing_provider:
                        logger.info(
                            f"Model provider '{provider_data['name']}' already exists, skipping"
                        )
                        continue

                    provider_create = ModelProviderCreate(**provider_data)
                    created_provider = (
                        self.model_provider_service.create_model_provider(
                            provider_create, admin_user_id, allow_system=True
                        )
                    )

                    if created_provider:
                        logger.info(
                            f"Successfully initialized model provider: {created_provider.name}"
                        )
                    else:
                        logger.warning(
                            f"Failed to initialize model provider: {provider_data['name']}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error initializing model provider '{provider_data['name']}': {e}"
                    )
                    continue

            logger.info("Completed initialization of predefined model providers")
            return True

        except Exception as e:
            logger.error(f"Error during model provider initialization: {e}")
            return False

    def get_provider_config_for_model_type(
        self, provider_name: str, model_type: ModelType
    ) -> Optional[Dict[str, Any]]:
        """Get provider configuration for a specific model type."""
        predefined_providers = self.get_predefined_model_providers()

        for provider in predefined_providers:
            if provider["name"] == provider_name:
                # Check if the provider supports the requested model type
                has_embedding = provider.get("embedding") is not None
                has_generative = provider.get("generative") is not None
                has_reranker = provider.get("reranker") is not None

                if (
                    (model_type == ModelType.EMBEDDING and has_embedding)
                    or (model_type == ModelType.GENERATIVE and has_generative)
                    or (model_type == ModelType.RERANKER and has_reranker)
                ):

                    config = {
                        "name": provider["name"],
                        "provider_type": provider["provider_type"],
                        "endpoint": provider["endpoint"],
                        "timeout": provider["timeout"],
                    }

                    # Add model-specific configuration
                    if model_type == ModelType.EMBEDDING and provider.get("embedding"):
                        config.update(provider["embedding"])
                    elif model_type == ModelType.GENERATIVE and provider.get(
                        "generative"
                    ):
                        config.update(provider["generative"])
                    elif model_type == ModelType.RERANKER and provider.get("reranker"):
                        config.update(provider["reranker"])

                    return config

        return None

    def get_provider_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all predefined providers with API key requirements."""
        predefined_providers = self.get_predefined_model_providers()

        summary = []
        for provider in predefined_providers:
            summary.append(
                {
                    "name": provider["name"],
                    "provider_type": provider["provider_type"],
                    "endpoint": provider["endpoint"],
                    "supports_embedding": provider.get("embedding") is not None,
                    "supports_generative": provider.get("generative") is not None,
                    "supports_reranker": provider.get("reranker") is not None,
                    "embedding_models_count": len(
                        provider.get("embedding", {}).get("models", [])
                    ),
                    "generative_models_count": len(
                        provider.get("generative", {}).get("models", [])
                    ),
                    "reranker_models_count": len(
                        provider.get("reranker", {}).get("models", [])
                    ),
                    "timeout": provider["timeout"],
                    "description": provider["description"],
                }
            )

        return summary
