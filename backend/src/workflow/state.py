"""
Enhanced state management for the DataPilotFlow AI Agent workflow.

This module defines the state structure and management utilities
for the enhanced LangGraph workflow with DataPilotFlow intelligence.
Combines workflow state with RAG pipeline state for comprehensive processing.
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated, Literal
from datetime import datetime
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
    
    # === Query Processing ===
    rewritten_query: Optional[str]
    expanded_terms: Optional[List[str]]
    
    # === Search and retrieval ===
    # === Input ===
    query: str
    top_k: int
    
    # === Query Processing ===
    rewritten_query: Optional[str]
    expanded_terms: Optional[List[str]]
    
    
    # === Search and retrieval ===
    retrieved_documents: Optional[List[Dict[str, Any]]]
    document_scores: Optional[List[float]]
    
    # === Document Judging ===
    judged_documents: Optional[List[Dict[str, Any]]]
    relevance_labels: Optional[List[int]]
    
 # Answer Generation
    context: Optional[str]
    final_answer: Optional[str]
    
    # Metadata
    processing_steps: List[str]
    errors: List[str]
    
    # Configuration
    config: Optional[Dict[str, Any]]


def create_initial_state(query: str, top_k: int = 5, config: Optional[Dict[str, Any]] = None) -> WorkflowState:
    """
    Create initial state for the RAG pipeline.
    
    Args:
        query: User's input query
        top_k: Number of documents to retrieve
        config: Optional configuration dictionary
        
    Returns:
        Initial workflow state
    """
    return WorkflowState(
        query=query,
        top_k=top_k,
        rewritten_query=None,
        expanded_terms=None,
        retrieved_documents=None,
        document_scores=None,
        judged_documents=None,
        relevance_labels=None,
        context=None,
        final_answer=None,
        processing_steps=[],
        errors=[],
        config=config or {}
    )