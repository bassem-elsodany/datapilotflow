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
    logger.info("")
    logger.info("=" * 100)
    logger.info("🔥🔥🔥 RECIPROCAL RANK FUSION (RRF) - STARTING NOW! 🔥🔥🔥")
    logger.info("=" * 100)

    if not results_list:
        logger.warning("⚠️ RRF: No result sets provided")
        return []

    logger.info(f"📊 RRF INPUT:")
    logger.info(f"   - Number of result sets (query variants): {len(results_list)}")
    logger.info(f"   - RRF constant k: {k}")
    logger.info(f"   - Final top_k to return: {final_top_k}")

    total_input_docs = sum(len(r) for r in results_list)
    logger.info(f"   - Total input documents: {total_input_docs}")
    logger.info("")

    for idx, results in enumerate(results_list, 1):
        logger.info(f"   Result Set [{idx}]: {len(results)} documents")

    # Track scores for each document by ID
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, Dict[str, Any]] = {}
    doc_appearances: Dict[str, int] = (
        {}
    )  # Count how many result sets each doc appears in

    logger.info("")
    logger.info("🔄 PROCESSING EACH RESULT SET AND CALCULATING RRF SCORES...")
    logger.info("-" * 100)

    # Process each result set
    for result_set_idx, results in enumerate(results_list):
        if not results:
            logger.info(f"⏭️  Result set [{result_set_idx + 1}]: EMPTY, skipping")
            continue

        query_variant = (
            results[0].get("query_variant", "unknown") if results else "unknown"
        )
        logger.info("")
        logger.info(
            f"📊 PROCESSING RESULT SET [{result_set_idx + 1}/{len(results_list)}]"
        )
        logger.info(f"   Query Variant: '{query_variant}'")
        logger.info(f"   Documents in this set: {len(results)}")
        logger.info("   " + "-" * 80)

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
            is_new_doc = doc_id not in doc_scores
            if is_new_doc:
                doc_scores[doc_id] = 0.0
                doc_data[doc_id] = doc
                doc_appearances[doc_id] = 0

            old_score = doc_scores[doc_id]
            doc_scores[doc_id] += rrf_score
            doc_appearances[doc_id] += 1
            new_score = doc_scores[doc_id]

            logger.info(
                f"   📄 Doc (rank={rank}): source_url={doc.get('source_url', 'N/A')[:100]},  RRF formula: 1/(k+rank) = 1/({k}+{rank}) = {rrf_score:.6f}, Score update: {old_score:.6f} + {rrf_score:.6f} = {new_score:.6f}, Appeared in {doc_appearances[doc_id]} result set(s) so far"
            )
    if not doc_scores:
        logger.warning("⚠️ RRF: No documents found in any result set")
        return []

    logger.info("")
    logger.info("=" * 100)
    logger.info("🎯 SORTING DOCUMENTS BY RRF SCORE (HIGHEST FIRST)...")
    logger.info("=" * 100)

    # Sort documents by RRF score (highest first)
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    logger.info(f"📊 Total unique documents after fusion: {len(sorted_docs)}")
    logger.info(f"📊 Returning top {final_top_k} documents")
    logger.info("")

    # Return top_k documents with their RRF scores
    fused_results = []
    for doc_id, score in sorted_docs[:final_top_k]:
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = round(score, 4)
        doc["fusion_rank"] = len(fused_results) + 1
        doc["appeared_in_n_results"] = doc_appearances[doc_id]
        fused_results.append(doc)
        text_preview = doc.get("text", "")[:150] if doc.get("text") else "NO TEXT"
        logger.info(
            f"🏆 FUSED RANK #{doc['fusion_rank']}: chunk_id: {doc_id} RRF score: {score:.6f} Appeared in: {doc_appearances[doc_id]} result set(s) Source: {doc.get('source_url', 'N/A')} Preview: '{text_preview}...'"
        )
        logger.info("")

    logger.info("=" * 100)
    logger.info("✅✅✅ RRF FUSION COMPLETE! ✅✅✅")
    logger.info(
        f"✅ INPUT: {len(results_list)} result sets with {total_input_docs} total documents"
    )
    logger.info(
        f"✅ OUTPUT: {len(fused_results)} fused documents (ranked by RRF score)"
    )
    logger.info("=" * 100)
    logger.info("")

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
    logger.info("=" * 100)
    logger.info("🚨 PARALLEL RETRIEVAL PROOF - STARTING 🚨")
    logger.info("=" * 100)
    logger.info(f"📋 TOTAL QUERY VARIANTS TO SEARCH: {len(queries)}")
    logger.info(f"📊 DOCUMENTS PER QUERY: {top_k_per_query}")
    logger.info("-" * 100)
    logger.info("📝 ALL QUERY VARIANTS THAT WILL BE SEARCHED:")
    for idx, q in enumerate(queries, 1):
        logger.info(f"   🔍 VARIANT [{idx}/{len(queries)}]: '{q}'")
    logger.info("=" * 100)

    async def retrieve_single(query: str, query_idx: int) -> List[Dict[str, Any]]:
        """Retrieve documents for a single query."""
        try:
            logger.info("")
            logger.info("⚡" * 40)
            logger.info(
                f"🚀 VECTOR SEARCH [{query_idx + 1}/{len(queries)}] - STARTING NOW!, Query Variant: '{query}'"
            )
            logger.info("⚡" * 40)

            # Use async retriever (calls _aget_relevant_documents)
            logger.info(f"⚙️  Calling Milvus retriever.ainvoke() (async)...")
            docs = await retriever.ainvoke(query)
            logger.info(f"✅ Milvus returned {len(docs)} documents")

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

            logger.info("")
            logger.info(
                f"✅✅✅ VARIANT [{query_idx + 1}/{len(queries)}] SEARCH COMPLETE! ✅✅✅"
            )
            logger.info(f"📊 QUERY: '{query[:100]}...'")
            logger.info(f"📊 RETRIEVED: {len(results)} documents")
            logger.info("-" * 80)
            logger.info("📄 RETRIEVED DOCUMENTS FOR THIS VARIANT:")
            for idx, res in enumerate(results, 1):
                chunk_id = res.get("chunk_id", "N/A")
                distance = res.get("distance", 0.0)
                source = res.get("source_url", "N/A")
                text_preview = (
                    res.get("text", "")[:100] if res.get("text") else "NO TEXT"
                )
                logger.info(
                    f"   Doc [{idx}]: source_url={source}, distance={distance:.4f}"
                )
            logger.info("-" * 80)
            return results

        except Exception as e:
            logger.error(
                f"❌❌❌ VARIANT [{query_idx + 1}/{len(queries)}] SEARCH FAILED: {e}"
            )
            import traceback

            logger.error(traceback.format_exc())
            return []

    # Execute all queries in parallel
    logger.info("")
    logger.info("⚡" * 40)
    logger.info(f"⚡ EXECUTING {len(queries)} PARALLEL VECTOR SEARCHES...")
    logger.info("⚡" * 40)

    tasks = [retrieve_single(query, idx) for idx, query in enumerate(queries)]
    results_list = await asyncio.gather(*tasks)

    # Log summary
    logger.info("")
    logger.info("=" * 100)
    logger.info("🎯 PARALLEL RETRIEVAL COMPLETE - SUMMARY 🎯")
    logger.info("=" * 100)

    total_retrieved = sum(len(results) for results in results_list)
    successful_queries = sum(1 for results in results_list if results)

    logger.info(f"✅ SUCCESSFUL SEARCHES: {successful_queries}/{len(queries)}")
    logger.info(f"✅ TOTAL DOCUMENTS RETRIEVED: {total_retrieved}")
    logger.info("")
    logger.info("📊 DOCUMENTS PER VARIANT:")
    for idx, results in enumerate(results_list, 1):
        logger.info(f"   Variant [{idx}]: {len(results)} documents")
    logger.info("=" * 100)

    return results_list
