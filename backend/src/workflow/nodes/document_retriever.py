"""
Document retriever node for DataPilotFlow LangGraph implementation.

This node retrieves relevant documents using the retriever tool.
"""

import traceback

import opik
from loguru import logger

from src.workflow.state import WorkflowState


def document_retriever(state: WorkflowState) -> WorkflowState:
    """
    Retrieve relevant documents using semantic search.

    Args:
        state: Current workflow state containing the enhanced query

    Returns:
        Updated state with retrieved documents and scores
    """
    logger.info("🚀 [NODE START] document_retriever")
    try:
        # Add processing step
        state["processing_steps"].append("document_retrieval")

        # Get configuration from state
        config = state.get("config", {})
        collection_name = config.get("collection_name", "LongTermMemory")
        user_id = config.get("user_id")
        top_k = config.get("top_k", 5)

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

        for i, doc in enumerate(documents, 1):
            page_content = doc.page_content

            # Log document content for debugging
            logger.debug(
                f"📄 Doc {i}: page_content length = {len(page_content) if page_content else 0}"
            )
            if page_content:
                logger.debug(f"📄 Doc {i}: preview = {page_content[:200]}...")
            else:
                logger.warning(f"⚠️ Doc {i}: page_content is empty or None!")

            retrieved_docs.append(
                {
                    "text": page_content,
                    "metadata": {
                        k: v
                        for k, v in doc.metadata.items()
                        if k not in ["id", "distance"]
                    },
                    "id": doc.metadata.get("id"),
                    "source_url": doc.metadata.get("source_url"),
                    "correlation_id": doc.metadata.get("correlation_id"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                }
            )
            scores.append(doc.metadata.get("distance", 0.0))

        # Update state
        state["retrieved_documents"] = retrieved_docs
        state["document_scores"] = scores

        logger.info(
            f"✅ Retrieved {len(retrieved_docs)} documents from {collection_name}"
        )
        logger.info("✅ [NODE FINISH] document_retriever")

    except Exception as e:
        error_msg = f"Document retrieval failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ [NODE FINISH] document_retriever (with error)")

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(error_msg)

        # Set empty results
        state["retrieved_documents"] = []
        state["document_scores"] = []

    return state
