"""
Reciprocal Rank Fusion (RRF) for multi-query retrieval.

RRF combines results from multiple query variants to improve ranking quality.
Documents appearing in multiple result sets rank higher, promoting consensus results.

Reference: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
(Cormack, Clarke, & Buettcher, 2009)
"""

import asyncio
from typing import Any, Dict, List

from loguru import logger


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]], k: int = 60, final_top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Apply Reciprocal Rank Fusion to merge multiple retrieval result sets.

    RRF Formula: score(doc) = Σ(1 / (k + rank_i))
    where rank_i is the rank of the document in result set i

    Args:
        results_list: List of result lists from different queries
        k: RRF constant (default: 60, from original paper)
        final_top_k: Number of final results to return

    Returns:
        Fused results sorted by RRF score (highest first)

    Example:
        >>> results_1 = [{"id": "doc1", "text": "..."}, {"id": "doc2", "text": "..."}]
        >>> results_2 = [{"id": "doc2", "text": "..."}, {"id": "doc3", "text": "..."}]
        >>> fused = reciprocal_rank_fusion([results_1, results_2], k=60, final_top_k=3)
        >>> # doc2 appears in both result sets, so it gets highest score
    """
    if not results_list:
        logger.warning("⚠️ RRF: No result sets provided")
        return []

    # Track scores for each document by ID
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, Dict[str, Any]] = {}
    doc_appearances: Dict[str, int] = {}  # Count how many result sets each doc appears in

    # Process each result set
    for result_set_idx, results in enumerate(results_list):
        if not results:
            logger.debug(f"⏭️ Result set {result_set_idx + 1}: empty, skipping")
            continue

        logger.debug(
            f"📊 Processing result set {result_set_idx + 1}: {len(results)} documents"
        )

        for rank, doc in enumerate(results, start=1):
            # Generate unique doc ID
            doc_id = (
                doc.get("id")
                or doc.get("chunk_id")
                or doc.get("correlation_id")
                or f"doc_{result_set_idx}_{rank}"
            )

            # Calculate RRF score for this document in this result set
            rrf_score = 1.0 / (k + rank)

            # Accumulate scores across result sets
            if doc_id not in doc_scores:
                doc_scores[doc_id] = 0.0
                doc_data[doc_id] = doc
                doc_appearances[doc_id] = 0

            doc_scores[doc_id] += rrf_score
            doc_appearances[doc_id] += 1

            logger.debug(
                f"  Doc {doc_id[:30]}... in set {result_set_idx + 1}: "
                f"rank={rank}, rrf_contribution={rrf_score:.4f}, "
                f"total_score={doc_scores[doc_id]:.4f}"
            )

    if not doc_scores:
        logger.warning("⚠️ RRF: No documents found in any result set")
        return []

    # Sort documents by RRF score (highest first)
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # Return top_k documents with their RRF scores
    fused_results = []
    for doc_id, score in sorted_docs[:final_top_k]:
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = round(score, 4)
        doc["fusion_rank"] = len(fused_results) + 1
        doc["appeared_in_n_results"] = doc_appearances[doc_id]
        fused_results.append(doc)

        logger.debug(
            f"✅ Fused rank {doc['fusion_rank']}: "
            f"doc_id={doc_id[:30]}..., "
            f"rrf_score={score:.4f}, "
            f"appeared_in={doc_appearances[doc_id]} result sets"
        )

    total_docs = sum(len(r) for r in results_list)
    logger.info(
        f"✅ RRF Fusion Complete: Combined {len(results_list)} result sets "
        f"({total_docs} total docs) → {len(fused_results)} fused results"
    )

    return fused_results


async def parallel_retrieval(
    queries: List[str], retriever, top_k_per_query: int = 5
) -> List[List[Dict[str, Any]]]:
    """
    Execute multiple retrieval queries in parallel for faster processing.

    Args:
        queries: List of query strings
        retriever: MilvusRetriever instance
        top_k_per_query: Number of documents to retrieve per query

    Returns:
        List of result lists, one per query

    Example:
        >>> queries = ["SSL configuration", "secure socket layer setup", "TLS config"]
        >>> results = await parallel_retrieval(queries, retriever, top_k_per_query=5)
        >>> # results[0] contains top 5 docs for "SSL configuration"
        >>> # results[1] contains top 5 docs for "secure socket layer setup"
        >>> # results[2] contains top 5 docs for "TLS config"
    """
    logger.info(f"🔄 Starting parallel retrieval for {len(queries)} queries")

    async def retrieve_single(query: str, query_idx: int) -> List[Dict[str, Any]]:
        """Retrieve documents for a single query."""
        try:
            logger.debug(f"Query {query_idx + 1}/{len(queries)}: '{query[:60]}...'")

            # Use synchronous retriever in async context
            docs = await asyncio.to_thread(retriever.get_relevant_documents, query)

            # Format results
            results = []
            for doc in docs[:top_k_per_query]:
                results.append(
                    {
                        "text": doc.page_content,
                        "metadata": {
                            k: v
                            for k, v in doc.metadata.items()
                            if k not in ["id", "distance"]
                        },
                        "id": doc.metadata.get("id"),
                        "source_url": doc.metadata.get("source_url"),
                        "correlation_id": doc.metadata.get("correlation_id"),
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "distance": doc.metadata.get("distance", 0.0),
                        "query_variant_index": query_idx + 1,
                        "query_variant": query,
                    }
                )

            logger.debug(
                f"✅ Query {query_idx + 1}/{len(queries)}: Retrieved {len(results)} documents"
            )
            return results

        except Exception as e:
            logger.error(f"❌ Query {query_idx + 1}/{len(queries)} failed: {e}")
            return []

    # Execute all queries in parallel
    tasks = [retrieve_single(query, idx) for idx, query in enumerate(queries)]
    results_list = await asyncio.gather(*tasks)

    # Log summary
    total_retrieved = sum(len(results) for results in results_list)
    successful_queries = sum(1 for results in results_list if results)

    logger.info(
        f"✅ Parallel retrieval complete: "
        f"{successful_queries}/{len(queries)} queries successful, "
        f"{total_retrieved} total documents retrieved"
    )

    return results_list
