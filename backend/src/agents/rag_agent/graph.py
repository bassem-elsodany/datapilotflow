"""
LangGraph Custom ReAct Agent for Salesforce AI.

This module implements a simple ReAct agent following the LangGraph pattern exactly:
1. Agent (call_model) → Tools → Agent (call_model) → ... → End
2. Simple message-based state
3. Built-in tool calling and routing
"""

from functools import lru_cache
from typing import Any, Dict, Optional

from langgraph.graph import (  # pyright: ignore[reportMissingImports]
    END,
    START,
    StateGraph,
)
from langgraph.graph.state import (
    CompiledStateGraph,  # pyright: ignore[reportMissingImports]
)
from loguru import logger

from src.agents.rag_agent.nodes import (
    answer_generator,
    augmented_strategy_node,
    custom_variants_node,
    decomposition_strategy_node,
    document_judger,
    document_retriever,
    hyde_strategy_node,
    multi_query_strategy_node,
    raw_response_formatter,
)
from src.agents.rag_agent.state import RAGWorkflowState as WorkflowState
from src.config import settings


@lru_cache(maxsize=1)
def get_graph() -> CompiledStateGraph:
    """
    Build the LangGraph RAG Agent for independent query processing.

    This implements a stateless RAG pipeline where each user query is processed
    independently without graph-level state persistence:
    1. Query Enhancement (optional based on selected_strategy)
    2. Document Retrieval with vector search
    3. Document Reranking (optional)
    4. Answer Generation (optional) or raw response formatting

    Returns:
        CompiledStateGraph: The compiled RAG pipeline graph
    """
    logger.debug("Building LangGraph RAG Agent for independent queries")

    def route_to_strategy(state: WorkflowState) -> str:
        """
        Route to the appropriate query enhancement strategy based on selected_strategy.

        If no strategy is selected or "native" is selected, goes directly to document_retriever
        for traditional RAG without query enhancement.
        """
        selected = state.get("selected_strategy", "native")

        # Map strategy names to node names
        strategy_map = {
            "augmented": "augmented_strategy_node",
            "custom_variants": "custom_variants_node",
            "hyde": "hyde_strategy_node",
            "decomposition": "decomposition_strategy_node",
            "multi_query": "multi_query_strategy_node",
            "native": "document_retriever",  # Traditional RAG without enhancement
        }

        node_name = strategy_map.get(selected, "document_retriever")
        logger.info(f"Routing to strategy: {selected} to {node_name}")

        return node_name

    def should_continue_after_retriever(state: WorkflowState) -> str:
        """Decide whether to continue after document retrieval."""
        if not state.get("retrieved_documents"):
            return END  # No documents found, end the process

        # Check if reranking is enabled
        config = state.get("config", {})
        enable_reranking = config.get("enable_reranking", True)
        enable_llm_generation = config.get("enable_llm_generation", True)

        logger.info(
            f"Routing decision after retrieval: enable_reranking={enable_reranking}, "
            f"enable_llm_generation={enable_llm_generation}"
        )
        logger.debug(f"Config keys: {list(config.keys())}")

        if enable_reranking:
            logger.info("Routing to document_judger (reranking enabled)")
            return "document_judger"
        elif enable_llm_generation:
            logger.info(
                "Routing to answer_generator (reranking disabled, LLM generation enabled)"
            )
            return "answer_generator"
        else:
            logger.info(
                "Routing to raw_response_formatter (reranking disabled, LLM generation disabled)"
            )
            return "raw_response_formatter"

    def should_continue_after_judger(state: WorkflowState) -> str:
        """Decide whether to continue after document judging."""
        if not state.get("judged_documents"):
            return END  # No documents to judge, end the process

        # Check if LLM answer generation is enabled
        config = state.get("config", {})
        enable_llm_generation = config.get("enable_llm_generation", True)

        if enable_llm_generation:
            logger.info("Routing to answer_generator (LLM generation enabled)")
            return "answer_generator"
        else:
            logger.info("Routing to raw_response_formatter (LLM generation disabled)")
            return "raw_response_formatter"

    # Create the state graph
    graph_builder = StateGraph(WorkflowState)

    # Add strategy nodes (query enhancement)
    graph_builder.add_node("augmented_strategy_node", augmented_strategy_node)
    graph_builder.add_node("custom_variants_node", custom_variants_node)
    graph_builder.add_node("hyde_strategy_node", hyde_strategy_node)
    graph_builder.add_node("decomposition_strategy_node", decomposition_strategy_node)
    graph_builder.add_node("multi_query_strategy_node", multi_query_strategy_node)

    # Add core workflow nodes
    graph_builder.add_node("document_retriever", document_retriever)
    graph_builder.add_node("document_judger", document_judger)
    graph_builder.add_node("answer_generator", answer_generator)
    graph_builder.add_node("raw_response_formatter", raw_response_formatter)

    # Define the workflow edges
    # Start with conditional routing to the selected strategy (or native RAG)
    graph_builder.add_conditional_edges(
        START,
        route_to_strategy,
        {
            "augmented_strategy_node": "augmented_strategy_node",
            "custom_variants_node": "custom_variants_node",
            "hyde_strategy_node": "hyde_strategy_node",
            "decomposition_strategy_node": "decomposition_strategy_node",
            "multi_query_strategy_node": "multi_query_strategy_node",
            "document_retriever": "document_retriever",  # Native RAG (no enhancement)
        },
    )

    # All strategy nodes → document_retriever
    graph_builder.add_edge("augmented_strategy_node", "document_retriever")
    graph_builder.add_edge("custom_variants_node", "document_retriever")
    graph_builder.add_edge("hyde_strategy_node", "document_retriever")
    graph_builder.add_edge("decomposition_strategy_node", "document_retriever")
    graph_builder.add_edge("multi_query_strategy_node", "document_retriever")

    graph_builder.add_conditional_edges(
        "document_retriever",
        should_continue_after_retriever,
        {
            "document_judger": "document_judger",
            "answer_generator": "answer_generator",  # Skip judger if reranking disabled
            "raw_response_formatter": "raw_response_formatter",  # Skip judger + LLM generation
            END: END,
        },
    )

    graph_builder.add_conditional_edges(
        "document_judger",
        should_continue_after_judger,
        {
            "answer_generator": "answer_generator",
            "raw_response_formatter": "raw_response_formatter",  # Skip LLM generation
            END: END,
        },
    )

    graph_builder.add_edge("answer_generator", END)
    graph_builder.add_edge("raw_response_formatter", END)

    logger.debug("RAG Agent with independent query processing created successfully")

    # Compile the graph (stateless - no checkpointer needed)
    return graph_builder.compile()


# Initialize the RAG graph for independent query processing
graph_dev = get_graph()
