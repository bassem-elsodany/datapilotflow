"""
Document retriever node for DataPilotFlow LangGraph implementation.

This node retrieves relevant documents using the retriever tool.
"""

import traceback
from typing import Any, Dict

import opik
from loguru import logger

from src.workflow.state import WorkflowState
from src.workflow.tools import get_retriever_tool


def document_retriever(state: WorkflowState) -> Dict[str, Any]:
    """
    Retrieve relevant documents using semantic search.

    Args:
        state: Current workflow state containing the enhanced query

    Returns:
        Updated state with retrieved documents and scores
    """
    try:
        # Add processing step
        state["processing_steps"].append("document_retrieval")

        # Get configuration from state
        config = state.get("config", {})
        collection_name = config.get("collection_name", "LongTermMemory")
        user_id = config.get("user_id")
        top_k = state.get("top_k", 5)

        if not user_id:
            raise ValueError("user_id is required in config")

        logger.info(f"📦 Using collection '{collection_name}' with top_k={top_k}")

        # Use enhanced query if available, otherwise use original query
        enhanced_query = state.get("enhanced_query")
        search_query = None

        # Check for augmented queries first (original + enhanced variants)
        augmented_queries = state.get("augmented_queries")
        if augmented_queries and isinstance(augmented_queries, list):
            # Use all augmented queries (original + variants) for comprehensive search
            search_query = augmented_queries[0] if augmented_queries else None
            logger.info(
                f"🔍 Using augmented queries for search ({len(augmented_queries)} total)"
            )

        elif enhanced_query and isinstance(enhanced_query, dict):
            # Try to get enhanced query variants in order of preference
            # 1. Multi-query variants
            if enhanced_query.get("multi_query_variants"):
                search_queries = enhanced_query.get("multi_query_variants")
                search_query = search_queries[0] if search_queries else None
            # 2. Fusion perspectives
            elif enhanced_query.get("fusion_perspectives"):
                search_queries = enhanced_query.get("fusion_perspectives")
                search_query = search_queries[0] if search_queries else None
            # 3. Step-back query
            elif enhanced_query.get("step_back_query"):
                search_query = enhanced_query.get("step_back_query")
            # 4. Hypothetical answer
            elif enhanced_query.get("hypothetical_answer"):
                search_query = enhanced_query.get("hypothetical_answer")

        # Fallback to original query if no enhanced query found
        if not search_query:
            search_query = state["query"]

        logger.info(f"🔍 Searching with query: '{search_query[:100]}...'")

        # Get the retriever (not the tool wrapper)
        from src.workflow.tools.retriever_tool import MilvusRetriever

        retriever = MilvusRetriever(
            collection_name=collection_name,
            user_id=user_id,
            top_k=top_k,
        )

        # Use the retriever to get documents
        documents = retriever.get_relevant_documents(search_query)

        # Format results
        retrieved_docs = []
        scores = []

        for doc in documents:
            retrieved_docs.append(
                {
                    "text": doc.page_content,
                    "metadata": {
                        k: v
                        for k, v in doc.metadata.items()
                        if k not in ["id", "distance"]
                    },
                    "id": doc.metadata.get("id"),
                }
            )
            scores.append(doc.metadata.get("distance", 0.0))

        # Update state
        state["retrieved_documents"] = retrieved_docs
        state["document_scores"] = scores

        logger.info(
            f"✅ Retrieved {len(retrieved_docs)} documents from {collection_name}"
        )

    except Exception as e:
        error_msg = f"Document retrieval failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(error_msg)

        # Set empty results
        state["retrieved_documents"] = []
        state["document_scores"] = []

    return state
