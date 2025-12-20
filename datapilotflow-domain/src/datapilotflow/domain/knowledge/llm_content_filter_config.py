"""
LLM Content Filter Configuration domain models.

This module defines the domain models for configuring LLM-based content filtering
during web crawling and document extraction.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LLMContentFilterConfig(BaseModel):
    """Configuration for LLM-based content filtering during crawling.

    This model defines how an LLM should filter and clean crawled content
    before it's processed into chunks and embeddings.
    """

    id: str = Field(description="Unique identifier for the LLM content filter config")
    user_id: str = Field(description="ID of the user who created this configuration")

    # Basic Configuration
    name: str = Field(description="Name of the content filter configuration")
    description: Optional[str] = Field(
        default=None, description="Description of what this filter does"
    )

    # LLM Provider Configuration
    enabled: bool = Field(
        default=False, description="Whether LLM content filtering is enabled"
    )
    llm_provider_id: str = Field(
        description="ID of the model provider to use for LLM content filtering"
    )
    llm_model_name: str = Field(
        description="Name of the specific LLM model to use (e.g., 'gpt-4o-mini', 'gemini-1.5-pro')"
    )

    # Filtering Configuration
    instruction: str = Field(
        default="""Extract only the main technical documentation content.
Include:
- Key concepts and explanations
- Important code examples
- Essential technical details
- API references and guides

Exclude:
- Navigation elements
- Headers and footers
- Sidebars
- Advertisements
- Cookie notices
- Social media links

Format the output as clean markdown with proper code blocks and headers.""",
        description="Natural language instruction for the LLM on how to filter content",
    )

    chunk_token_threshold: int = Field(
        default=500,
        description="Token threshold for chunking content before LLM processing",
        ge=100,
        le=4000,
    )

    # Advanced Settings
    temperature: Optional[float] = Field(
        default=0.0,
        description="LLM temperature for content filtering (0.0 = deterministic)",
        ge=0.0,
        le=2.0,
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for LLM API calls",
        ge=1,
        le=10,
    )

    timeout_seconds: int = Field(
        default=30, description="Timeout for LLM API calls in seconds", ge=10, le=300
    )

    verbose: bool = Field(
        default=False, description="Enable verbose logging for LLM filtering"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was last updated",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class LLMContentFilterConfigCreate(BaseModel):
    """Model for creating a new LLM content filter configuration."""

    name: str = Field(description="Name of the content filter configuration")
    description: Optional[str] = Field(
        default=None, description="Description of what this filter does"
    )

    # LLM Provider Configuration
    enabled: bool = Field(
        default=False, description="Whether LLM content filtering is enabled"
    )
    llm_provider_id: str = Field(
        description="ID of the model provider to use for LLM content filtering"
    )
    llm_model_name: str = Field(
        description="Name of the specific LLM model to use (e.g., 'gpt-4o-mini', 'gemini-1.5-pro')"
    )

    # Filtering Configuration
    instruction: str = Field(
        default="""Extract only the main technical documentation content.
Include:
- Key concepts and explanations
- Important code examples
- Essential technical details
- API references and guides

Exclude:
- Navigation elements
- Headers and footers
- Sidebars
- Advertisements
- Cookie notices
- Social media links

Format the output as clean markdown with proper code blocks and headers.""",
        description="Natural language instruction for the LLM",
    )

    chunk_token_threshold: int = Field(
        default=500, description="Token threshold for chunking content", ge=100, le=4000
    )

    # Advanced Settings
    temperature: Optional[float] = Field(
        default=0.0, description="LLM temperature", ge=0.0, le=2.0
    )

    max_retries: int = Field(
        default=3, description="Maximum retries for LLM API calls", ge=1, le=10
    )

    timeout_seconds: int = Field(
        default=30, description="Timeout for LLM API calls in seconds", ge=10, le=300
    )

    verbose: bool = Field(default=False, description="Enable verbose logging")


# Use the same model for both create and update
LLMContentFilterConfigUpdate = LLMContentFilterConfigCreate
