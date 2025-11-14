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

    strategy: str  # "native", "multi_query", "augmented", "hyde", "decomposition"
    provider: Optional[ProviderConfig] = (
        None  # Provider for enhancement (e.g., embedding model)
    )


@dataclass
class VectorDatabaseConfig:
    """Vector database configuration."""

    collection_name: str = "LongTermMemory"
    top_k: int = 5  # Number of documents to retrieve


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
    provider: Optional[ProviderConfig] = None  # LLM provider for answer generation


# NOTE: AssistantTool and SystemPromptTask classes have been removed.
# Tools are now managed as standalone entities in src/domain/tool and referenced by ID in AssistantConfig.


@dataclass
class AssistantConfig:
    """Configuration for Assistant mode (supervisor agent with tools)."""

    enabled: bool  # Whether Assistant mode is enabled (true) or RAG mode (false)
    tools: Optional[List[str]] = None  # List of tool IDs bound to this conversation agent
    tool_instructions: Optional[str] = None  # User's custom instructions for how tools should work together


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    search_query: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    source_urls: Optional[List[str]] = None
    chunk_ids: Optional[List[str]] = None
    # Enhancement metadata
    enhancement_strategy_used: Optional[str] = None
    enhanced_queries: Optional[List[str]] = None
    # Performance metrics
    processing_time_ms: Optional[int] = None
    document_count: Optional[int] = None


@dataclass
class ConversationSession:
    """Represents a conversation session with history."""

    _id: str  # MongoDB _id as primary identifier
    user_id: str
    created_at: datetime
    last_updated: datetime
    messages: List[ConversationMessage]
    name: Optional[str] = None
    description: Optional[str] = None
    # Nested configuration structures
    enhancement: Optional[EnhancementConfig] = None  # Query enhancement configuration
    vector_database: Optional[VectorDatabaseConfig] = (
        None  # Vector database configuration
    )
    reranker: Optional[RerankerConfig] = None  # Document reranker configuration
    answer_generation: Optional[AnswerGenerationConfig] = (
        None  # Answer generation configuration
    )
    # Tags for organization
    tags: Optional[List[str]] = None
    # Assistant mode configuration (complex nested structure)
    # Contains enable_knowledge_assistant boolean and system_prompt_tasks list
    # This is the ONLY place mode is stored - no redundant flat fields
    assistant_config: Optional[AssistantConfig] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        # Generate default name if none provided
        if self.name is None:
            self.name = f"Session {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def message_count(self) -> int:
        """Get the number of messages in this session."""
        return len(self.messages)

    @property
    def agent_type(self) -> str:
        """Get agent type based on assistant_config.enabled flag."""
        return (
            "supervisor"
            if (self.assistant_config and self.assistant_config.enabled)
            else "rag"
        )

    @property
    def has_answer_generation(self) -> bool:
        """Check if answer generation is configured."""
        return (
            self.answer_generation is not None
            and self.answer_generation.provider is not None
        )

    @property
    def has_enhancement(self) -> bool:
        """Check if enhancement configuration is set."""
        return self.enhancement is not None and self.enhancement.strategy != "native"

    @property
    def current_strategy(self) -> str:
        """Get current enhancement strategy."""
        if self.enhancement:
            return self.enhancement.strategy
        return "native"

    @property
    def has_system_prompt(self) -> bool:
        """Check if system prompt is configured."""
        if not self.assistant_config or not self.assistant_config.system_prompt_tasks:
            return False
        # Check if any system prompt task is active
        return any(
            task.is_active and not task.is_empty
            for task in self.assistant_config.system_prompt_tasks
        )

    @property
    def has_reranker(self) -> bool:
        """Check if reranker is configured."""
        return self.reranker is not None and self.reranker.provider is not None
