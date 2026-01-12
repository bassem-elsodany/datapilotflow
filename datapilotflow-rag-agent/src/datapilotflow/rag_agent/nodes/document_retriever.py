"""
Document retriever node for DataPilotFlow LangGraph implementation.

This node retrieves relevant documents using the retriever tool.
Supports both single-query and Reciprocal Rank Fusion (RRF) strategies.
"""

import asyncio
import traceback

from loguru import logger

from ..retrieval import parallel_retrieval, reciprocal_rank_fusion
from ..state import RAGWorkflowState as WorkflowState


async def document_retriever(state: WorkflowState) -> WorkflowState:
    """
    Retrieve relevant documents using semantic search.

    Args:
        state: Current workflow state containing the enhanced query

    Returns:
        Updated state with retrieved documents and scores
    """
    logger.debug("Node starting: document_retriever")
    try:
        # Get configuration from state
        config = state.get("config", {})
        collection_name = config.get("collection_name", "LongTermMemory")
        user_id = config.get("user_id")
        top_k = config.get("top_k", 5)
        # Embedding configuration from collection
        embedding_provider_id = config.get("embedding_provider_id")
        embedding_model_name = config.get("embedding_model_name")
        vector_dimension = config.get("vector_dimension", 1536)

        if not user_id:
            raise ValueError("user_id is required in config")

        logger.debug(f"Collection: {collection_name}, top_k={top_k}, embedding_provider={embedding_provider_id}, model={embedding_model_name}, dimension={vector_dimension}")

        # Get retrieval configuration
        retrieval_config = config.get("retrieval_config", {})

        # Collect all query variants
        query_variants = []
        enhanced_query = state.get("enhanced_query")

        # Check for augmented queries first (original + enhanced variants)
        augmented_queries = state.get("augmented_queries")
        if augmented_queries and isinstance(augmented_queries, list):
            query_variants = augmented_queries

        elif enhanced_query and isinstance(enhanced_query, dict):
            # Try to get enhanced query variants in order of preference
            # 1. Multi-query variants
            if enhanced_query.get("multi_query_variants"):
                query_variants = enhanced_query.get("multi_query_variants")
            # 2. Sub-queries from decomposition
            elif enhanced_query.get("sub_queries"):
                query_variants = enhanced_query.get("sub_queries")
            # 3. For single-value enhancements (hyde), create list
            elif enhanced_query.get("hypothetical_answer"):
                query_variants = [enhanced_query.get("hypothetical_answer")]

        # Fallback to original query if no variants found
        if not query_variants:
            query_variants = [state["query"]]

        logger.debug(f"Query variants collected: {len(query_variants)} total")

        # Get the retriever
        from ..tools.retriever_tool import MilvusRetriever

        retriever = MilvusRetriever(
            collection_name=collection_name,
            user_id=user_id,
            top_k=top_k,
            embedding_provider_id=embedding_provider_id,
            embedding_model_name=embedding_model_name,
            vector_dimension=vector_dimension,
        )

        # Decide: Single query or RRF?
        # Smart default: Auto-enable RRF when multiple variants exist (unless explicitly disabled)
        retrieval_strategy = retrieval_config.get("retrieval_strategy")

        # If not explicitly set, use smart default
        if retrieval_strategy is None:
            retrieval_strategy = (
                "reciprocal_rank_fusion" if len(query_variants) > 1 else "single_query"
            )

        logger.debug(f"Retrieval strategy selected: {retrieval_strategy} (variants={len(query_variants)})")

        if len(query_variants) > 1 and retrieval_strategy == "reciprocal_rank_fusion":
            # === RECIPROCAL RANK FUSION (RRF) ===
            top_k_per_query = retrieval_config.get("top_k_per_query", 5)
            rrf_k = retrieval_config.get("rrf_k", 60)

            logger.debug(f"RRF strategy: {len(query_variants)} variants, {top_k_per_query} docs/variant, final_top_k={top_k}, rrf_k={rrf_k}")

            # Execute parallel retrieval
            results_list = await parallel_retrieval(
                queries=query_variants,
                retriever=retriever,
                top_k_per_query=top_k_per_query,
            )
            logger.debug(f"Parallel retrieval returned {len(results_list)} result sets")

            # Apply RRF fusion
            fused_docs = reciprocal_rank_fusion(
                results_list=results_list, k=rrf_k, final_top_k=top_k
            )

            # Format results for state
            retrieved_docs = fused_docs
            scores = [doc.get("rrf_score", 0.0) for doc in fused_docs]

            logger.debug(f"RRF fusion complete: retrieved {len(fused_docs)} fused documents")

        else:
            # === SINGLE QUERY (DEFAULT/LEGACY BEHAVIOR) ===
            search_query = query_variants[0]
            logger.debug(f"Single query strategy: '{search_query[:100]}...'")

            # Use async retriever (calls _aget_relevant_documents)
            documents = await retriever.ainvoke(search_query)

            # Format results
            retrieved_docs = []
            scores = []

            for i, doc in enumerate(documents, 1):
                page_content = doc.page_content

                # Log document content for debugging
                if not page_content:
                    logger.warning(f"Document {i}: page_content is empty or None")

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

            logger.debug(f"Single query strategy complete: retrieved {len(retrieved_docs)} documents")

        # Update state
        state["retrieved_documents"] = retrieved_docs
        state["document_scores"] = scores

        logger.debug(f"Retrieved {len(retrieved_docs)} documents from {collection_name}")
        logger.debug("Node finished: document_retriever")

    except Exception as e:
        error_msg = f"Document retrieval failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("Node finished: document_retriever (with error)")

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(error_msg)

        # Set empty results
        state["retrieved_documents"] = []
        state["document_scores"] = []

    return state
