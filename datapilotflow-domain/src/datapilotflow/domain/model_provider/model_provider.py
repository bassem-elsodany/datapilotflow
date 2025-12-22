"""
Unified Model Provider domain models.

This module defines the Pydantic models for unified model provider configurations
that support both embedding and generative models from the same provider.
"""

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class ModelType(str, Enum):
    """Enumeration of supported model types."""

    EMBEDDING = "embedding"
    GENERATIVE = "generative"
    RERANKER = "reranker"


class ModelTypeConfig(BaseModel):
    """Configuration for a specific model type."""

    models: List[str] = Field(description="List of supported model names for this type")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration specific to this model type"
    )
    endpoint: Optional[str] = Field(
        default=None,
        description=(
            "Endpoint path for this model type "
            "(e.g., '/v1/embeddings', '/v1/chat/completions')"
        ),
    )

    model_config = ConfigDict(extra="ignore")


class ModelProvider(BaseModel):
    """Model representing a unified model provider configuration."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the model provider")
    name: str = Field(
        description="Name of the model provider (e.g., 'OpenAI', 'Anthropic')"
    )
    provider_type: str = Field(
        description=(
            "Provider type / LiteLLM provider key used for routing; must match the "
            "value selected in the dashboard 'Provider Type' dropdown "
            "(e.g. 'openai', 'azure', 'azure_ai', 'anthropic', 'vertex_ai', "
            "'google_ai_studio', 'groq', 'cohere', 'deepseek', etc.)."
        )
    )
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (can be None for providers like Ollama)",
    )
    api_key_field_name: str = Field(
        default="api_key",
        description=(
            "HTTP header name for the API key (e.g., 'api_key', 'Api-Key', 'X-API-Key', 'Authorization'). "
            "Defaults to 'api_key'. LiteLLM will use this as the header name when making requests."
        ),
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(default=True, description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds for all model types",
        ge=1,
        le=300,
    )

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )

    # Metadata
    created_at: datetime = Field(description="Timestamp when the provider was created")
    updated_at: datetime = Field(
        description="Timestamp when the provider was last updated"
    )
    created_by: str = Field(description="User ID who created the provider")
    updated_by: str = Field(description="User ID who last updated the provider")

    @property
    def supported_model_types(self) -> List[ModelType]:
        """Get list of supported model types based on available configurations."""
        types = []
        if self.embedding is not None:
            types.append(ModelType.EMBEDDING)
        if self.generative is not None:
            types.append(ModelType.GENERATIVE)
        if self.reranker is not None:
            types.append(ModelType.RERANKER)
        return types

    @property
    def embedding_models(self) -> List[str]:
        """Get list of embedding models."""
        return self.embedding.models if self.embedding else []

    @property
    def generative_models(self) -> List[str]:
        """Get list of generative models."""
        return self.generative.models if self.generative else []

    @property
    def reranker_models(self) -> List[str]:
        """Get list of reranker models."""
        return self.reranker.models if self.reranker else []

    @property
    def is_user_managed(self) -> bool:
        """All providers are user-manageable (no system/custom distinction)."""
        return True


class ModelProviderCreate(BaseModel):
    """Model for creating a new model provider configuration."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Name of the model provider")
    provider_type: str = Field(description="Type of provider")
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (can be None for providers like Ollama)",
    )
    api_key_field_name: str = Field(
        default="api_key",
        description=(
            "HTTP header name for the API key (e.g., 'api_key', 'Api-Key', 'X-API-Key', 'Authorization'). "
            "Defaults to 'api_key'. LiteLLM will use this as the header name when making requests."
        ),
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(default=True, description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds for all model types",
        ge=1,
        le=300,
    )

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )


# Use the same model for both create and update
ModelProviderUpdate = ModelProviderCreate


class ModelProviderResponse(BaseModel):
    """Response model for model provider that excludes sensitive information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the model provider")
    name: str = Field(description="Name of the model provider")
    provider_type: str = Field(description="Type of provider")
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (full key, UI will mask it for display)",
    )
    api_key_field_name: str = Field(
        default="api_key",
        description=(
            "HTTP header name for the API key (e.g., 'api_key', 'Api-Key', 'X-API-Key', 'Authorization'). "
            "Defaults to 'api_key'."
        ),
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(description="Request timeout in seconds for all model types")

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )

    # Metadata
    created_at: datetime = Field(description="Timestamp when the provider was created")
    updated_at: datetime = Field(
        description="Timestamp when the provider was last updated"
    )
    created_by: str = Field(description="User ID who created the provider")
    updated_by: str = Field(description="User ID who last updated the provider")

    @computed_field(return_type=List[ModelType])
    def supported_model_types(self) -> List[ModelType]:
        """Get list of supported model types based on available configurations."""
        types = []
        if self.embedding is not None:
            types.append(ModelType.EMBEDDING)
        if self.generative is not None:
            types.append(ModelType.GENERATIVE)
        if self.reranker is not None:
            types.append(ModelType.RERANKER)
        return types

    @computed_field(return_type=List[str])
    def embedding_models(self) -> List[str]:
        """Get list of embedding models."""
        return self.embedding.models if self.embedding else []

    @computed_field(return_type=List[str])
    def generative_models(self) -> List[str]:
        """Get list of generative models."""
        return self.generative.models if self.generative else []

    @computed_field(return_type=List[str])
    def reranker_models(self) -> List[str]:
        """Get list of reranker models."""
        return self.reranker.models if self.reranker else []

    @computed_field(return_type=Dict[str, Any])
    def provider_config(self) -> Dict[str, Any]:
        """Get provider-level config from first available model type."""
        if self.embedding and self.embedding.config:
            return self.embedding.config
        if self.generative and self.generative.config:
            return self.generative.config
        if self.reranker and self.reranker.config:
            return self.reranker.config
        return {}

    @property
    def is_user_managed(self) -> bool:
        """All providers are user-manageable (no system/custom distinction)."""
        return True
