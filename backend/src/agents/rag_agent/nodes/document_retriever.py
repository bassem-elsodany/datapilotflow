"""
Document retriever node for DataPilotFlow LangGraph implementation.

This node retrieves relevant documents using the retriever tool.
Supports both single-query and Reciprocal Rank Fusion (RRF) strategies.
"""

import traceback

import opik
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

        # Get retrieval configuration
        retrieval_config = config.get("retrieval_config", {})

        # Collect all query variants
        query_variants = []
        enhanced_query = state.get("enhanced_query")

        # Check for augmented queries first (original + enhanced variants)
        augmented_queries = state.get("augmented_queries")
        if augmented_queries and isinstance(augmented_queries, list):
            query_variants = augmented_queries
            logger.info(f"🔍 Found {len(query_variants)} augmented query variants")

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

        logger.info("")
        logger.info("🔥" * 50)
        logger.info("📋 QUERY VARIANTS COLLECTED")
        logger.info("🔥" * 50)
        logger.info(f"📊 TOTAL QUERY VARIANTS: {len(query_variants)}")
        logger.info("-" * 100)
        for idx, variant in enumerate(query_variants, 1):
            logger.info(f"   🔍 VARIANT [{idx}/{len(query_variants)}]: '{variant}'")
        logger.info("🔥" * 50)
        logger.info("")

        # Get the retriever
        from ..tools.retriever_tool import MilvusRetriever

        retriever = MilvusRetriever(
            collection_name=collection_name,
            user_id=user_id,
            top_k=top_k,
        )

        # Decide: Single query or RRF?
        # Smart default: Auto-enable RRF when multiple variants exist (unless explicitly disabled)
        retrieval_strategy = retrieval_config.get("retrieval_strategy")

        logger.info("=" * 100)
        logger.info("⚙️  RETRIEVAL STRATEGY DECISION")
        logger.info("=" * 100)
        logger.info(f"📊 Number of query variants: {len(query_variants)}")
        logger.info(f"📊 Configured retrieval_strategy: {retrieval_strategy}")

        # If not explicitly set, use smart default
        if retrieval_strategy is None:
            retrieval_strategy = (
                "reciprocal_rank_fusion" if len(query_variants) > 1 else "single_query"
            )
            logger.info(f"📊 Auto-selected strategy: {retrieval_strategy}")
            if len(query_variants) > 1:
                logger.info(
                    f"✅ Auto-enabling RRF because we have {len(query_variants)} query variants"
                )

        logger.info(f"🎯 FINAL DECISION: Using '{retrieval_strategy}' strategy")
        logger.info("=" * 100)
        logger.info("")

        if len(query_variants) > 1 and retrieval_strategy == "reciprocal_rank_fusion":
            # === RECIPROCAL RANK FUSION (RRF) ===
            top_k_per_query = retrieval_config.get("top_k_per_query", 5)
            rrf_k = retrieval_config.get("rrf_k", 60)

            logger.info("")
            logger.info("🚨" * 50)
            logger.info("🚨 USING RECIPROCAL RANK FUSION (RRF) STRATEGY 🚨")
            logger.info("🚨" * 50)
            logger.info(f"📊 Number of query variants: {len(query_variants)}")
            logger.info(f"📊 User requested top_k: {top_k}")
            logger.info(f"📊 Documents per query variant: {top_k_per_query}")
            logger.info(f"📊 Total docs retrieved before fusion: {len(query_variants)} × {top_k_per_query} = {len(query_variants) * top_k_per_query}")
            logger.info(f"📊 RRF constant k: {rrf_k}")
            logger.info(f"📊 Final top_k after RRF fusion: {top_k}")
            logger.info("🚨" * 50)
            logger.info("")

            # Execute parallel retrieval
            logger.info("🚀 STEP 1: Execute parallel retrieval for all variants...")
            results_list = await parallel_retrieval(
                queries=query_variants,
                retriever=retriever,
                top_k_per_query=top_k_per_query,
            )
            logger.info(
                f"✅ Parallel retrieval returned {len(results_list)} result sets"
            )

            # Apply RRF fusion
            logger.info("")
            logger.info("🚀 STEP 2: Apply RRF to fuse results from all variants...")
            fused_docs = reciprocal_rank_fusion(
                results_list=results_list, k=rrf_k, final_top_k=top_k
            )

            # Format results for state
            retrieved_docs = fused_docs
            scores = [doc.get("rrf_score", 0.0) for doc in fused_docs]

            logger.info("")
            logger.info("=" * 100)
            logger.info("✅✅✅ RRF STRATEGY COMPLETE! ✅✅✅")
            logger.info(
                f"✅ Retrieved {len(fused_docs)} fused documents from {len(query_variants)} variants"
            )
            logger.info("=" * 100)
            logger.info("")

        else:
            # === SINGLE QUERY (DEFAULT/LEGACY BEHAVIOR) ===
            search_query = query_variants[0]
            logger.info(f"🔍 Using single query strategy: '{search_query[:100]}...'")

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

            logger.info(f"✅ Single Query: Retrieved {len(retrieved_docs)} documents")

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
