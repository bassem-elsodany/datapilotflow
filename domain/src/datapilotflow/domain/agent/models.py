"""
Agent Domain Models

This module defines the Agent entity, which represents a reusable AI agent configuration.
An agent can be either RAG-based or Assistant-based and can be used across multiple conversations.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.domain.conversation.models import (
    AssistantConfig,
    ProviderConfig,
    RerankerConfig,
    VectorDatabaseConfig,
)


class AgentType(str, Enum):
    """Agent types."""

    RAG = "rag"
    ASSISTANT = "assistant"


class EnhancementStrategy(str, Enum):
    """Query enhancement strategies for RAG agents."""

    NATIVE = "native"  # Traditional RAG without enhancement
    AUGMENTED = "augmented"  # Augmented queries
    MULTI_QUERY = "multi_query"  # Multiple query variants
    HYDE = "hyde"  # Hypothetical Document Embeddings
    DECOMPOSITION = "decomposition"  # Query decomposition
    CUSTOM_VARIANTS = "custom_variants"  # Custom query variants


@dataclass
class Agent:
    """
    Represents an AI agent configuration.

    An agent is a reusable configuration that defines how the AI behaves.
    It can be used across multiple conversations (threads).

    Agent Types:
    - RAG: Retrieval-Augmented Generation with vector search
    - ASSISTANT: Supervisor agent with tools and custom instructions

    Attributes:
        _id: Unique identifier (MongoDB ObjectId as string)
        user_id: Owner of the agent
        name: Display name (e.g., "Legal Assistant", "Medical Expert")
        description: Optional description of agent's purpose
        agent_type: Type of agent (RAG or ASSISTANT)
        created_at: Creation timestamp
        updated_at: Last modification timestamp

        RAG Configuration (only if agent_type = RAG):
        - enhancement_strategy: Query enhancement strategy (e.g., "native", "augmented", "custom_variants")
        - vector_database: Vector DB settings
        - reranker: Reranker configuration
        - is_llm_generation_enabled: Whether LLM answer generation is enabled

        Assistant Configuration (only if agent_type = ASSISTANT):
        - assistant_config: Tools, instructions, and LLM settings

        tags: Organizational tags
    """

    _id: str
    user_id: str
    name: str
    agent_type: AgentType
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    # Primary LLM Provider for this agent (used by both RAG and Assistant modes)
    # - RAG: Used for query enhancement, reranking, answer generation
    # - Assistant: Used as the LLM powering the assistant
    llm_provider: Optional[ProviderConfig] = None

    # RAG-specific configuration (only populated if agent_type = RAG)
    enhancement_strategy: EnhancementStrategy = EnhancementStrategy.NATIVE
    vector_database: Optional[VectorDatabaseConfig] = None
    reranker: Optional[RerankerConfig] = None
    is_llm_generation_enabled: bool = False  # Whether LLM answer generation is enabled

    # Assistant-specific configuration (only populated if agent_type = ASSISTANT)
    assistant_config: Optional[AssistantConfig] = None

    # Organizational
    tags: Optional[List[str]] = None

    def __post_init__(self):
        """Validate agent configuration."""
        if self.tags is None:
            self.tags = []

        # Validate that RAG agents have RAG config
        if self.agent_type == AgentType.RAG:
            if not self.vector_database:
                raise ValueError("RAG agents must have vector_database configuration")

        # Validate that ASSISTANT agents have assistant config
        if self.agent_type == AgentType.ASSISTANT:
            if not self.assistant_config:
                raise ValueError("ASSISTANT agents must have assistant_config")

    @property
    def is_rag_agent(self) -> bool:
        """Check if this is a RAG agent."""
        return self.agent_type == AgentType.RAG

    @property
    def is_assistant_agent(self) -> bool:
        """Check if this is an Assistant agent."""
        return self.agent_type == AgentType.ASSISTANT

    @property
    def has_tools(self) -> bool:
        """Check if assistant has tools configured."""
        return (
            self.assistant_config is not None
            and self.assistant_config.tools is not None
            and len(self.assistant_config.tools) > 0
        )
