"""
Conversation Domain Models

This module contains all domain models for conversation management including:
- ConversationSession: Main conversation with history
- ConversationMessage: Individual messages in conversation
- Configuration models: Nested configuration for conversations (RAG, Assistant, Answer Gen)

Note: Tools are now managed as standalone entities (see src/domain/tool)
and referenced by ID in AssistantConfig.tools
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class QueryEnhancementStrategy(str, Enum):
    """Available query enhancement strategies."""

    NONE = "none"
    AUGMENTED = "augmented"
    CUSTOM_VARIANTS = "custom_variants"
    MULTI_QUERY = "multi_query"
    HYDE = "hyde"
    DECOMPOSITION = "decomposition"
    QUERY_FUSION = "query_fusion"


class RetrievalStrategy(str, Enum):
    """Available multi-query retrieval strategies."""

    SINGLE_QUERY = "single_query"  # Use only first query variant (fast, less coverage)
    RECIPROCAL_RANK_FUSION = (
        "reciprocal_rank_fusion"  # Use all variants with RRF (slower, better quality)
    )


@dataclass
class ProviderConfig:
    """Provider and model configuration."""

    id: str  # Provider ID
    model_name: str  # Model name


@dataclass
class EnhancementConfig:
    """Query enhancement configuration for a conversation."""

    strategy: str  # "native", "multi_query", "augmented", "hyde", "decomposition", "custom_variants"
    # Note: Enhancement uses the agent's primary llm_provider, no separate provider needed


@dataclass
class VectorDatabaseConfig:
    """Vector database configuration.

    The embedding provider configured here MUST match the vector database collection's
    embedding provider. This ensures query embeddings are compatible with stored document embeddings.
    """

    collection_name: str = "LongTermMemory"
    top_k: int = 5  # Number of documents to retrieve

    # Embedding provider - denormalized from collection config for consistency and clarity
    # This MUST be the same provider used to embed the collection's documents
    embedding_provider: Optional[ProviderConfig] = None  # Provider for query vectorization

    # Vector dimension - denormalized from collection config for validation
    vector_dimension: int = 1536  # Must match the dimension of embeddings in collection


@dataclass
class RerankerConfig:
    """Document reranker configuration."""

    enabled: bool = False  # Whether reranking is enabled
    provider: Optional[ProviderConfig] = None  # Reranker provider
    relevance_threshold: float = 0.5  # Relevance score threshold (0-1)


@dataclass
class AnswerGenerationConfig:
    """Answer generation configuration."""

    enabled: bool = False  # Whether answer generation is enabled
    # Note: Answer generation uses the agent's primary llm_provider, no separate provider needed


# NOTE: AssistantTool and SystemPromptTask classes have been removed.
# Tools are now managed as standalone entities in src/domain/tool and referenced by ID in AssistantConfig.


@dataclass
class AssistantConfig:
    """Configuration for Assistant mode (supervisor agent with tools)."""

    enabled: bool  # Whether Assistant mode is enabled (true) or RAG mode (false)
    tools: Optional[List[str]] = (
        None  # List of tool IDs bound to this conversation agent
    )
    instructions: Optional[str] = (
        None  # User's custom instructions for how the assistant should behave and respond
    )


@dataclass
class ConversationMessage:
    """
    Represents a single message in a conversation.

    NEW ARCHITECTURE: Stored in separate 'messages' collection.
    """

    _id: str  # MongoDB _id
    conversation_id: str  # Foreign key to ConversationSession
    user_id: str  # Denormalized for faster queries
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    message_index: int = 0  # Preserves order within conversation
    source_links: Optional[List[Dict[str, str]]] = (
        None  # List of dicts with 'url', 'title', 'chunk_id', 'query_variant_index', 'query_variant'
    )
    # Enhancement metadata
    enhancement_strategy_used: Optional[str] = None
    enhanced_queries: Optional[List[str]] = None
    # Performance metrics
    processing_time_ms: Optional[int] = None
    document_count: Optional[int] = None


@dataclass
class ConversationSession:
    """
    Represents a conversation session (thread).

    NEW ARCHITECTURE:
    - agent_id links to reusable agent configuration
    - messages are stored in separate 'messages' collection
    - NO configuration fields here (all in agent)
    """

    _id: str  # MongoDB _id as primary identifier (conversation_id/thread_id)
    user_id: str
    agent_id: str  # Foreign key to Agent collection (REQUIRED)
    created_at: datetime
    last_updated: datetime
    name: Optional[str] = None
    description: Optional[str] = None
    last_message_at: Optional[datetime] = None
    is_archived: bool = False
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        # Generate default name if none provided
        if self.name is None:
            self.name = f"Conversation {self.created_at.strftime('%Y-%m-%d %H:%M')}"
