"""
LangGraph Custom ReAct Agent for Salesforce AI.

This module implements a simple ReAct agent following the LangGraph pattern exactly:
1. Agent (call_model) → Tools → Agent (call_model) → ... → End
2. Simple message-based state
3. Built-in tool calling and routing
"""

from functools import lru_cache
from re import L
from typing import Dict, Any, Optional
from loguru import logger
from langgraph.graph import StateGraph, START, END  # pyright: ignore[reportMissingImports]

from src.workflow.state import WorkflowState
from src.config import settings
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingImports]

from src.workflow.nodes import query_rewriter, answer_generator, document_judger, document_retriever

# Global checkpointer - will be set by the lifespan context manager
_global_checkpointer = None

def set_checkpointer(checkpointer):
    """Set the global checkpointer from the lifespan context manager"""
    global _global_checkpointer
    _global_checkpointer = checkpointer
    logger.debug(f"Global checkpointer set: {checkpointer}")

@lru_cache(maxsize=1)
def get_graph(use_checkpointer: bool = False) -> CompiledStateGraph:
    """
    Build the LangGraph Custom ReAct Agent for Salesforce AI.
    
    This follows the LangGraph custom ReAct agent pattern exactly:
    1. Agent (call_model) → Tools → Agent (call_model) → ... → End
    2. Simple message-based state with messages and remaining_steps
    3. Built-in tool calling and routing
    
    Returns:
        CompiledStateGraph: The compiled ReAct agent graph
    """
    logger.debug("Building LangGraph Custom ReAct Agent for Salesforce AI")
    
    # Get the checkpointer from global variable (only if needed)
    checkpointer = None
    if use_checkpointer:
        global _global_checkpointer
        checkpointer = _global_checkpointer
        logger.debug(f"Global checkpointer: {checkpointer}")
        if checkpointer is None:
            # hard fail with a clear message
            logger.error("No checkpointer found in global variable")
            raise RuntimeError(
                "Checkpointer not configured. "
                "Make sure the lifespan context manager is properly set up."
            )
        logger.debug(f"Checkpointer acquired from global: {checkpointer}")
    else:
        logger.debug("Running without checkpointer for LangGraph dev server")


    def should_continue_after_rewriter(state: WorkflowState) -> str:
        """Decide whether to continue after query rewriting."""
        if state.get("errors") and "query_rewriting" in str(state["errors"]):
            return "document_retriever"  # Continue with original query
        return "document_retriever"
    
    def should_continue_after_retriever(state: WorkflowState) -> str:
        """Decide whether to continue after document retrieval."""
        if not state.get("retrieved_documents"):
            return END  # No documents found, end the process
        return "document_judger"
    
    def should_continue_after_judger(state: WorkflowState) -> str:
        """Decide whether to continue after document judging."""
        if not state.get("judged_documents"):
            return END  # No documents to judge, end the process
        return "answer_generator"


    # Create the state graph
    graph_builder = StateGraph(WorkflowState)
    
    # Add nodes
    graph_builder.add_node("query_rewriter", query_rewriter)
    graph_builder.add_node("document_retriever", document_retriever)
    graph_builder.add_node("document_judger", document_judger)
    graph_builder.add_node("answer_generator", answer_generator)
    
    # Define the workflow edges
    graph_builder.set_entry_point("query_rewriter")
    
    graph_builder.add_conditional_edges(
        "query_rewriter",
        should_continue_after_rewriter,
        {
            "document_retriever": "document_retriever",
        }
    )
    
    graph_builder.add_conditional_edges(
        "document_retriever",
        should_continue_after_retriever,
        {
            "document_judger": "document_judger",
            END: END
        }
    )
    
    graph_builder.add_conditional_edges(
        "document_judger",
        should_continue_after_judger,
        {
            "answer_generator": "answer_generator",
            END: END
        }
    )
    
    graph_builder.add_edge("answer_generator", END)
    
    logger.debug("DataPilotFlow Agent with workflow nodes created successfully")
    
    # Compile with or without checkpointer
    if use_checkpointer and checkpointer:
        return graph_builder.compile(checkpointer=checkpointer)
    else:
        return graph_builder.compile()


graph_dev = get_graph(use_checkpointer=False)