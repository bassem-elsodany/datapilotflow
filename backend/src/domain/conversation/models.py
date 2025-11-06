"""
Conversation Domain Models

This module contains all domain models for conversation management including:
- ConversationSession: Main conversation with history
- ConversationMessage: Individual messages in conversation
- Configuration models: Nested configuration for conversations
- SystemPromptTask: Reusable system prompts
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
    provider: Optional[ProviderConfig] = None  # Provider for enhancement (e.g., embedding model)


@dataclass
class VectorDatabaseConfig:
    """Vector database configuration."""

    collection_name: str = "LongTermMemory"
    top_k: int = 5  # Number of documents to retrieve


@dataclass
class RerankerConfig:
    """Document reranker configuration."""

    provider: Optional[ProviderConfig] = None  # Reranker provider
    relevance_threshold: float = 0.5  # Relevance score threshold (0-1)


@dataclass
class AnswerGenerationConfig:
    """Answer generation configuration."""

    provider: Optional[ProviderConfig] = None  # LLM provider for answer generation


@dataclass
class SystemPrompt:
    """Embedded system prompt for a conversation."""

    id: str  # UUID identifier
    title: str  # Prompt title
    content: str  # Actual prompt content


@dataclass
class SystemPromptTask:
    """Represents a reusable system prompt template for a conversation."""

    id: str  # UUID identifier
    user_id: str
    conversation_id: str
    name: str  # e.g., "Code Reviewer", "Document Summarizer", "Technical Writer"
    description: Optional[str] = None  # Description of what this prompt does
    system_prompt: str = ""  # The actual system prompt template
    tags: Optional[List[str]] = None  # Tags for organization and filtering
    is_active: bool = True  # Whether this prompt is active and available for use
    usage_count: int = 0  # Number of times this prompt has been used
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None  # User who created this prompt
    version: int = 1  # Version number for tracking changes

    def __post_init__(self):
        if self.id is None or self.id == "":
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.created_by is None:
            self.created_by = self.user_id

    @property
    def is_empty(self) -> bool:
        """Check if the prompt is empty."""
        return not self.system_prompt or self.system_prompt.strip() == ""


@dataclass
class AssistantConfig:
    """Complex nested structure for Assistant mode configuration."""

    enable_knowledge_assistant: bool  # Enable knowledge assistant for multi-agent orchestration
    system_prompt_tasks: Optional[List[SystemPromptTask]] = None  # System prompt tasks for the assistant

    def get_active_prompt(self) -> Optional[SystemPromptTask]:
        """Get the active system prompt task."""
        if not self.system_prompt_tasks:
            return None
        for task in self.system_prompt_tasks:
            if task.is_active:
                return task
        return None


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
    vector_database: Optional[VectorDatabaseConfig] = None  # Vector database configuration
    reranker: Optional[RerankerConfig] = None  # Document reranker configuration
    answer_generation: Optional[AnswerGenerationConfig] = None  # Answer generation configuration
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
        """Get agent type based on enable_knowledge_assistant flag."""
        return "supervisor" if self.enable_knowledge_assistant else "rag"

    @property
    def has_answer_generation(self) -> bool:
        """Check if answer generation is configured."""
        return self.answer_generation is not None and self.answer_generation.provider is not None

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
        return self.system_prompt is not None and bool(self.system_prompt.content.strip())

    @property
    def has_reranker(self) -> bool:
        """Check if reranker is configured."""
        return self.reranker is not None and self.reranker.provider is not None
