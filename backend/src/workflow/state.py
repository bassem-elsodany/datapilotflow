"""
Enhanced state management for the DataPilotFlow AI Agent workflow.

This module defines the state structure and management utilities
for the enhanced LangGraph workflow with DataPilotFlow intelligence.
Combines workflow state with RAG pipeline state for comprehensive processing.
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.documents import Document
from loguru import logger


class WorkflowState(TypedDict):
    """
    Extended workflow state for the DataPilotFlow LangGraph workflow.
    Combines workflow functionality with RAG pipeline state for comprehensive processing.
    """

    # === Input ===
    query: str
    top_k: int

    # === Query Enhancement ===
    enhanced_query: Optional[Dict[str, Any]]  # EnhancedQuery object as dict
    enhancement_strategies_applied: Optional[List[str]]

    # Strategy selection (runtime control)
    # If selected_strategy is set → use ONLY that strategy
    # If None → use default config behavior (all enabled strategies)
    selected_strategy: Optional[
        str
    ]  # Target strategy (e.g., "multi_query", "hyde", "step_back")

    # Enhanced query components
    augmented_queries: Optional[List[str]]  # Original + enhanced variants
    multi_query_variants: Optional[List[str]]
    step_back_query: Optional[str]
    hypothetical_answer: Optional[str]
    sub_queries: Optional[List[str]]
    fusion_perspectives: Optional[List[str]]

    # === Search and retrieval ===
    retrieved_documents: Optional[List[Dict[str, Any]]]
    document_scores: Optional[List[float]]

    # === Document Judging ===
    judged_documents: Optional[List[Dict[str, Any]]]
    relevance_labels: Optional[List[int]]

    # Answer Generation
    context: Optional[str]
    final_answer: Optional[str]
    query_info: Optional[Dict[str, Any]]  # Original vs Enhanced query comparison

    # Metadata
    processing_steps: List[str]
    errors: List[str]

    # Configuration
    config: Optional[Dict[str, Any]]


def create_initial_state(
    query: str,
    top_k: int = 5,
    config: Optional[Dict[str, Any]] = None,
    selected_strategy: Optional[str] = None,
) -> WorkflowState:
    """
    Create initial state for the RAG pipeline.

    Args:
        query: User's input query
        top_k: Number of documents to retrieve
        config: Optional configuration dictionary
        selected_strategy: Target strategy to use (e.g., "multi_query", "hyde", "step_back")
                          If None, uses default config behavior

    Returns:
        Initial workflow state

    Strategy Selection Logic:
        - If selected_strategy is provided → Use ONLY that strategy
        - If selected_strategy is None → Use all enabled strategies from config (default)

    Examples:
        # Use only multi-query strategy
        >>> state = create_initial_state(
        ...     query="How to configure SSL?",
        ...     selected_strategy="multi_query"
        ... )

        # Use HyDE strategy
        >>> state = create_initial_state(
        ...     query="Explain microservices architecture",
        ...     selected_strategy="hyde"
        ... )

        # Use default config (no strategy specified)
        >>> state = create_initial_state(
        ...     query="What is X?"
        ... )
        # Uses all enabled strategies from config
    """
    return WorkflowState(
        query=query,
        top_k=top_k,
        enhanced_query=None,
        enhancement_strategies_applied=None,
        selected_strategy=selected_strategy,
        augmented_queries=None,
        multi_query_variants=None,
        step_back_query=None,
        hypothetical_answer=None,
        sub_queries=None,
        fusion_perspectives=None,
        retrieved_documents=None,
        document_scores=None,
        judged_documents=None,
        relevance_labels=None,
        context=None,
        final_answer=None,
        query_info=None,
        processing_steps=[],
        errors=[],
        config=config or {},
    )
