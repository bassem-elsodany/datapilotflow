"""
Unified Model Provider Initialization Service.

This service handles the initialization of predefined model providers during system startup.
These providers support both embedding and generative models with a single API key.
"""

from typing import List, Dict, Any, Optional
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
                        "text-embedding-ada-002"
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8191,
                        "batch_size": 100
                    }
                },
                "generative": {
                    "models": [
                        "gpt-4o",
                        "gpt-4o-mini",
                        "gpt-4-turbo",
                        "gpt-4",
                        "gpt-3.5-turbo"
                    ],
                    "config": {
                        "endpoint_suffix": "/chat/completions",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                }
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
                        "claude-3-sonnet-embedding"
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 200000,
                        "batch_size": 50
                    }
                },
                "generative": {
                    "models": [
                        "claude-3-5-sonnet-20241022",
                        "claude-3-5-haiku-20241022",
                        "claude-3-opus-20240229",
                        "claude-3-sonnet-20240229",
                        "claude-3-haiku-20240307"
                    ],
                    "config": {
                        "endpoint_suffix": "/messages",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
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
                    "models": [
                        "text-embedding-004",
                        "text-multilingual-embedding-002"
                    ],
                    "config": {
                        "endpoint_suffix": "/models",
                        "max_input_tokens": 2048,
                        "batch_size": 100
                    }
                },
                "generative": {
                    "models": [
                        "gemini-1.5-pro",
                        "gemini-1.5-flash",
                        "gemini-1.0-pro"
                    ],
                    "config": {
                        "endpoint_suffix": "/models",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
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
                        "bge-base-en"
                    ],
                    "config": {
                        "endpoint_suffix": "/embeddings",
                        "max_input_tokens": 8192,
                        "batch_size": 10  # Smaller batch for local models
                    }
                },
                "generative": {
                    "models": [
                        "llama3.1:8b",
                        "llama3.1:70b",
                        "mistral:7b",
                        "codellama:7b",
                        "phi3:3.8b"
                    ],
                    "config": {
                        "endpoint_suffix": "/generate",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
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
                        "sentence-transformers/distilbert-base-nli-mean-tokens"
                    ],
                    "config": {
                        "endpoint_suffix": "/",
                        "max_input_tokens": 512,
                        "batch_size": 50
                    }
                },
                "generative": {
                    "models": [
                        "microsoft/DialoGPT-medium",
                        "facebook/blenderbot-400M-distill",
                        "google/flan-t5-base"
                    ],
                    "config": {
                        "endpoint_suffix": "/",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
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
                        "llama-3.1-70b-versatile",
                        "llama-3.1-8b-instant",
                        "mixtral-8x7b-32768",
                        "gemma-7b-it"
                    ],
                    "config": {
                        "endpoint_suffix": "/chat/completions",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
            }
        ]
    
    async def initialize_predefined_model_providers(self, admin_user_id: str) -> bool:
        """Initialize predefined model providers in the database."""
        try:
            logger.info("Starting initialization of predefined model providers")
            
            predefined_providers = self.get_predefined_model_providers()
            
            for provider_data in predefined_providers:
                try:
                    # Check if provider already exists
                    existing_provider = self.model_provider_service.get_provider_by_name(
                        admin_user_id, provider_data["name"]
                    )
                    
                    if existing_provider:
                        logger.info(f"Model provider '{provider_data['name']}' already exists, skipping")
                        continue
                    
                    # Create provider
                    provider_create = ModelProviderCreate(**provider_data)
                    created_provider = self.model_provider_service.create_model_provider(
                        provider_create, admin_user_id
                    )
                    
                    if created_provider:
                        logger.info(f"Successfully initialized model provider: {created_provider.name}")
                    else:
                        logger.warning(f"Failed to initialize model provider: {provider_data['name']}")
                        
                except Exception as e:
                    logger.error(f"Error initializing model provider '{provider_data['name']}': {e}")
                    continue
            
            logger.info("Completed initialization of predefined model providers")
            return True
            
        except Exception as e:
            logger.error(f"Error during model provider initialization: {e}")
            return False
    
    def get_provider_config_for_model_type(
        self, 
        provider_name: str, 
        model_type: ModelType
    ) -> Optional[Dict[str, Any]]:
        """Get provider configuration for a specific model type."""
        predefined_providers = self.get_predefined_model_providers()
        
        for provider in predefined_providers:
            if provider["name"] == provider_name:
                # Check if the provider supports the requested model type
                has_embedding = provider.get("embedding") is not None
                has_generative = provider.get("generative") is not None
                
                if (model_type == ModelType.EMBEDDING and has_embedding) or \
                   (model_type == ModelType.GENERATIVE and has_generative):
                    
                    config = {
                        "name": provider["name"],
                        "provider_type": provider["provider_type"],
                        "endpoint": provider["endpoint"],
                        "api_key_env_var": provider["api_key_env_var"],
                        "api_key_required": provider["api_key_env_var"] is not None,
                        "timeout": provider["timeout"]
                    }
                    
                    # Add model-specific configuration
                    if model_type == ModelType.EMBEDDING and provider.get("embedding"):
                        config.update(provider["embedding"])
                    elif model_type == ModelType.GENERATIVE and provider.get("generative"):
                        config.update(provider["generative"])
                    
                    return config
        
        return None
    
    def get_provider_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all predefined providers with API key requirements."""
        predefined_providers = self.get_predefined_model_providers()
        
        summary = []
        for provider in predefined_providers:
            summary.append({
                "name": provider["name"],
                "provider_type": provider["provider_type"],
                "endpoint": provider["endpoint"],
                "api_key_required": provider["api_key_env_var"] is not None,
                "api_key_env_var": provider["api_key_env_var"],
                "supports_embedding": provider.get("embedding") is not None,
                "supports_generative": provider.get("generative") is not None,
                "embedding_models_count": len(provider.get("embedding", {}).get("models", [])),
                "generative_models_count": len(provider.get("generative", {}).get("models", [])),
                "timeout": provider["timeout"],
                "description": provider["description"]
            })
        
        return summary
    
    def get_providers_by_api_key_requirement(self, requires_api_key: bool) -> List[Dict[str, Any]]:
        """Get providers filtered by API key requirement status."""
        predefined_providers = self.get_predefined_model_providers()
        
        filtered_providers = []
        for provider in predefined_providers:
            provider_requires_api_key = provider["api_key_env_var"] is not None
            
            if provider_requires_api_key == requires_api_key:
                filtered_providers.append({
                    "name": provider["name"],
                    "provider_type": provider["provider_type"],
                    "endpoint": provider["endpoint"],
                    "api_key_required": provider_requires_api_key,
                    "api_key_env_var": provider["api_key_env_var"],
                    "supports_embedding": provider.get("embedding") is not None,
                    "supports_generative": provider.get("generative") is not None,
                    "timeout": provider["timeout"],
                    "description": provider["description"]
                })
        
        return filtered_providers
