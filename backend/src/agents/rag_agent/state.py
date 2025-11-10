"""
RAG Agent specific state management.

This is a copy of the original workflow/state.py, now owned by the RAG Agent package.
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, Union

from langchain_core.documents import Document
from loguru import logger


class RAGWorkflowState(TypedDict):
    """
    State specific to the RAG Agent workflow.
    Handles document retrieval, judging, and ranking.
    """

    # === Input ===
    query: Union[str, List[str]]  # Accept both single query and list of variants
    top_k: int
    conversation_description: Optional[str]

    # === Query Enhancement ===
    enhanced_query: Optional[Dict[str, Any]]
    enhancement_strategies_applied: Optional[List[str]]
    selected_strategy: Optional[str]

    # Enhanced query components
    augmented_queries: Optional[List[str]]
    multi_query_variants: Optional[List[str]]
    hypothetical_answer: Optional[str]
    sub_queries: Optional[List[str]]
    custom_variants: Optional[List[str]]  # For custom_variants strategy

    # === Search and retrieval ===
    retrieved_documents: Optional[List[Dict[str, Any]]]
    document_scores: Optional[List[float]]

    # === Document Judging ===
    judged_documents: Optional[List[Dict[str, Any]]]
    relevance_labels: Optional[List[int]]
    relevance_scores: Optional[List[float]]

    # Answer Generation
    context: Optional[str]
    final_answer: Optional[str]
    query_info: Optional[Dict[str, Any]]

    # Metadata
    errors: Optional[List[str]]

    # Configuration
    config: Optional[Dict[str, Any]]


def create_initial_state(
    query: Union[str, List[str]],
    top_k: int = 5,
    config: Optional[Dict[str, Any]] = None,
    selected_strategy: Optional[str] = None,
    conversation_description: Optional[str] = None,
    custom_variants: Optional[List[str]] = None,
) -> RAGWorkflowState:
    """
    Create initial state for the RAG pipeline.

    Args:
        query: User's input query (string or list of query variants)
        top_k: Number of documents to retrieve
        config: Optional configuration dictionary
        selected_strategy: Target strategy to use
        conversation_description: Domain/topic description for query enhancement
        custom_variants: Optional additional custom query variants

    Returns:
        Initial RAG workflow state
    """
    return RAGWorkflowState(
        query=query,
        top_k=top_k,
        conversation_description=conversation_description,
        enhanced_query=None,
        enhancement_strategies_applied=None,
        selected_strategy=selected_strategy,
        augmented_queries=None,
        multi_query_variants=None,
        hypothetical_answer=None,
        sub_queries=None,
        custom_variants=custom_variants,
        retrieved_documents=None,
        document_scores=None,
        judged_documents=None,
        relevance_labels=None,
        relevance_scores=None,
        context=None,
        final_answer=None,
        query_info=None,
        errors=[],
        config=config or {},
    )
