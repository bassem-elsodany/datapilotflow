"""
Unified Model Provider Initialization Service.

This service handles the initialization of predefined model providers during system startup.
These providers support both embedding and generative models with a single API key.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.domain.model_provider.model_provider import ModelProviderCreate, ModelType
from src.services.model_provider.model_provider_service import ModelProviderService


class ModelProviderInitializationService:
    """Service for initializing predefined unified model providers."""

    def __init__(self):
        self.model_provider_service = ModelProviderService()

    def get_predefined_model_providers(self) -> List[Dict[str, Any]]:
        """Get the list of predefined unified model providers."""
        return [
            {
                "name": "OpenAI",
                "provider_type": "openai",
                "endpoint": "https://api.openai.com/v1",
                "api_key": None,
                "api_key_env_var": "OPENAI_API_KEY",
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
            {
                "name": "Anthropic",
                "provider_type": "anthropic",
                "endpoint": "https://api.anthropic.com/v1",
                "api_key": None,
                "api_key_env_var": "ANTHROPIC_API_KEY",
                "description": "Anthropic's unified provider for both embedding and generative models",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": [
                        "claude-3-5-sonnet-embedding",
                        "claude-3-opus-embedding",
                        "claude-3-sonnet-embedding",
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8192,
                        "batch_size": 50,
                    },
                },
                "generative": {
                    "models": [
                        "claude-opus-4-1-20250805",
                        "claude-4-sonnet-20250514",
                        "claude-4-opus-20250514",
                        "claude-4-haiku-20250514",
                        "claude-sonnet-4-20250514",
                        "claude-haiku-4-5-20241119",
                        "claude-sonnet-4-20250514",
                        "claude-3-5-sonnet-20241022",
                        "claude-3-5-haiku-20241022",
                        "claude-3-opus-20240229",
                        "claude-3-sonnet-20240229",
                        "claude-3-haiku-20240307",
                        "claude-2.1",
                        "claude-2",
                        "claude-instant-1.2",
                    ],
                    "config": {
                        "endpoint_suffix": "/messages",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": None,  # Anthropic can be used for reranking but not primary role
            },
            {
                "name": "Google",
                "provider_type": "google",
                "endpoint": "https://generativelanguage.googleapis.com/v1beta",
                "api_key": None,
                "api_key_env_var": "GOOGLE_API_KEY",
                "description": "Google's unified provider for both embedding and generative models",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": ["text-embedding-004", "text-multilingual-embedding-002"],
                    "config": {
                        "endpoint_suffix": "/models",
                        "max_input_tokens": 2048,
                        "batch_size": 100,
                    },
                },
                "generative": {
                    "models": [
                        "gemini-2-5-pro",
                        "gemini-2-5-flash",
                        "gemini-2-5-flash-lite",
                        "gemini-2.0-flash",
                        "gemini-2.0-flash-exp",
                        "gemini-1.5-pro",
                        "gemini-1.5-pro-002",
                        "gemini-1.5-flash",
                        "gemini-1.5-flash-002",
                        "gemini-1.0-pro",
                        "gemini-1.0-pro-vision",
                    ],
                    "config": {
                        "endpoint_suffix": "/models",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": None,  # Google can be used for reranking but not primary role
            },
            {
                "name": "Ollama",
                "provider_type": "ollama",
                "endpoint": "http://localhost:11434/api",
                "api_key": None,
                "api_key_env_var": None,
                "description": "Ollama's unified provider for local embedding and generative models",
                "is_active": False,
                "timeout": 120,  # Longer timeout for local models
                "embedding": {
                    "models": [
                        "nomic-embed-text",
                        "mxbai-embed-large",
                        "all-minilm",
                        "bge-large-en",
                        "bge-base-en",
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8192,
                        "batch_size": 10,  # Smaller batch for local models
                    },
                },
                "generative": {
                    "models": [
                        "llama3.3:70b",
                        "llama3.2:90b",
                        "llama3.2:11b",
                        "llama3.2:3b",
                        "llama3.2-vision:90b",
                        "llama3.2-vision:11b",
                        "llama3.1:405b",
                        "llama3.1:70b",
                        "llama3.1:8b",
                        "llama3:70b",
                        "llama3:8b",
                        "mistral:7b",
                        "mistral-large:latest",
                        "mixtral:8x7b",
                        "codellama:34b",
                        "codellama:13b",
                        "codellama:7b",
                        "phi3:3.8b",
                        "phi3:14b",
                        "phi4:14b",
                        "neural-chat:7b",
                        "deepseek-coder:33b",
                        "deepseek-coder:6.7b",
                    ],
                    "config": {
                        "endpoint_suffix": "/generate",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": None,  # Ollama doesn't support reranking
            },
            {
                "name": "Hugging Face",
                "provider_type": "huggingface",
                "endpoint": "https://api-inference.huggingface.co/models",
                "api_key": None,
                "api_key_env_var": "HUGGINGFACE_API_KEY",
                "description": "Hugging Face's unified provider for both embedding and generative models",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": [
                        "sentence-transformers/all-MiniLM-L6-v2",
                        "sentence-transformers/all-mpnet-base-v2",
                        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        "sentence-transformers/distilbert-base-nli-mean-tokens",
                    ],
                    "config": {
                        "endpoint_suffix": "/",
                        "max_input_tokens": 512,
                        "batch_size": 50,
                    },
                },
                "generative": {
                    "models": [
                        "meta-llama/Llama-3.3-70B-Instruct",
                        "meta-llama/Llama-3.1-70B-Instruct",
                        "meta-llama/Llama-3.1-8B-Instruct",
                        "meta-llama/Llama-2-70b-chat-hf",
                        "meta-llama/Llama-2-13b-chat-hf",
                        "meta-llama/Llama-2-7b-chat-hf",
                        "mistralai/Mistral-Large-Instruct-2411",
                        "mistralai/Mistral-7B-Instruct-v0.3",
                        "mistralai/Mistral-7B-Instruct-v0.2",
                        "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
                        "NousResearch/Nous-Hermes-2-7b-DPO",
                        "google/flan-t5-xxl",
                        "google/flan-t5-large",
                        "google/flan-t5-base",
                        "deepseek-ai/deepseek-coder-33b-instruct",
                        "deepseek-ai/deepseek-coder-7b-instruct",
                        "Qwen/Qwen2.5-72B-Instruct",
                        "Qwen/Qwen2.5-32B-Instruct",
                        "Qwen/Qwen2.5-7B-Instruct",
                        "stabilityai/stablelm-2-zephyr-1.6b",
                    ],
                    "config": {
                        "endpoint_suffix": "/",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": None,  # Hugging Face can be used for reranking but not primary role
            },
            {
                "name": "Groq",
                "provider_type": "groq",
                "endpoint": "https://api.groq.com/openai/v1",
                "api_key": None,
                "api_key_env_var": "GROQ_API_KEY",
                "description": "Groq's high-performance generative model provider",
                "is_active": False,
                "timeout": 30,  # Fast inference
                "embedding": None,  # Groq doesn't support embeddings
                "generative": {
                    "models": [
                        "llama-4-8b",
                        "llama-4-70b",
                        "llama-4-405b",
                        "llama-3-3-70b-versatile",
                        "llama-3-3-70b-specdec",
                        "llama-3-1-70b-versatile",
                        "llama-3-1-8b-instant",
                        "llama-3-2-90b-vision-preview",
                        "llama-3-2-11b-vision-preview",
                        "llama-3-2-1b-preview",
                        "mixtral-8x7b-32768",
                        "gemma-7b-it",
                        "gemma-2-9b-it",
                        "deepseek-r1-distill-qwen-32b",
                        "qwen-qwq-32b",
                        "qwen-2-5-coder-32b",
                        "qwen-2-5-32b",
                        "mistral-saba-24b",
                    ],
                    "config": {
                        "endpoint_suffix": "/chat/completions",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": None,  # Groq doesn't support reranking
            },
            {
                "name": "Cohere",
                "provider_type": "cohere",
                "endpoint": "https://api.cohere.ai/v1",
                "api_key": None,
                "api_key_env_var": "COHERE_API_KEY",
                "description": "Cohere's unified provider for embeddings, generative AI, and reranking",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": [
                        "embed-english-v3.0",
                        "embed-english-light-v3.0",
                        "embed-multilingual-v3.0",
                        "embed-multilingual-light-v3.0",
                    ],
                    "config": {
                        "endpoint_suffix": "/embed",
                        "max_input_tokens": 512,
                        "batch_size": 96,
                    },
                },
                "generative": {
                    "models": [
                        "command-a-03-2025",
                        "command-a-reasoning-03-2025",
                        "command-a-translate-03-2025",
                        "command-r-plus-08-2024",
                        "command-r-plus",
                        "command-r-08-2024",
                        "command-r",
                        "command-nightly",
                        "command",
                        "command-light",
                        "command-light-nightly",
                    ],
                    "config": {
                        "endpoint_suffix": "/generate",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                    },
                },
                "reranker": {
                    "models": [
                        "rerank-english-v3.0",
                        "rerank-multilingual-v3.0",
                        "rerank-english-v2.0",
                        "rerank-multilingual-v2.0",
                    ],
                    "config": {
                        "endpoint_suffix": "/rerank",
                        "max_documents": 1000,
                        "top_n": 10,
                    },
                },
            },
            {
                "name": "Voyage AI",
                "provider_type": "voyage",
                "endpoint": "https://api.voyageai.com/v1",
                "api_key": None,
                "api_key_env_var": "VOYAGE_API_KEY",
                "description": "Voyage AI's provider for embeddings and reranking",
                "is_active": False,
                "timeout": 60,
                "embedding": {
                    "models": [
                        "voyage-large-2",
                        "voyage-code-2",
                        "voyage-2",
                        "voyage-lite-02-instruct",
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8000,
                        "batch_size": 128,
                    },
                },
                "generative": None,  # Voyage AI doesn't support generative models
                "reranker": {
                    "models": ["rerank-lite-1", "rerank-1"],
                    "config": {
                        "endpoint_suffix": "/rerank",
                        "max_documents": 1000,
                        "top_n": 10,
                    },
                },
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

                    # Create provider
                    provider_create = ModelProviderCreate(**provider_data)
                    created_provider = (
                        self.model_provider_service.create_model_provider(
                            provider_create, admin_user_id
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
                        "api_key_env_var": provider["api_key_env_var"],
                        "api_key_required": provider["api_key_env_var"] is not None,
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
                    "api_key_required": provider["api_key_env_var"] is not None,
                    "api_key_env_var": provider["api_key_env_var"],
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

    def get_providers_by_api_key_requirement(
        self, requires_api_key: bool
    ) -> List[Dict[str, Any]]:
        """Get providers filtered by API key requirement status."""
        predefined_providers = self.get_predefined_model_providers()

        filtered_providers = []
        for provider in predefined_providers:
            provider_requires_api_key = provider["api_key_env_var"] is not None

            if provider_requires_api_key == requires_api_key:
                filtered_providers.append(
                    {
                        "name": provider["name"],
                        "provider_type": provider["provider_type"],
                        "endpoint": provider["endpoint"],
                        "api_key_required": provider_requires_api_key,
                        "api_key_env_var": provider["api_key_env_var"],
                        "supports_embedding": provider.get("embedding") is not None,
                        "supports_generative": provider.get("generative") is not None,
                        "supports_reranker": provider.get("reranker") is not None,
                        "timeout": provider["timeout"],
                        "description": provider["description"],
                    }
                )

        return filtered_providers
