"""
Document judger node for DataPilotFlow LangGraph implementation.

This node judges the relevance of retrieved documents to the user's question.
Uses async concurrent processing to judge multiple documents in parallel.
"""

import asyncio
import re

from loguru import logger

from ..chains import get_judger_chain
from ..state import RAGWorkflowState as WorkflowState


async def _judge_single_document_async(
    doc: dict, query: str, chain, relevance_threshold: float, doc_index: int
) -> tuple:
    """
    Judge a single document's relevance asynchronously.

    Args:
        doc: Document to judge
        query: User query
        chain: Judger chain
        relevance_threshold: Threshold for relevance label
        doc_index: Document index for tracking

    Returns:
        Tuple of (judged_doc, score)
    """
    try:
        # Invoke the chain asynchronously
        response = await chain.ainvoke({"query": query, "document": doc["text"]})

        # Extract content from response
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        # Parse judgment result - extract last number from response
        try:
            numbers = re.findall(r"\b[0-1]\.?[0-9]*\b", response_text)

            if numbers:
                # Take the last number found (should be the final score)
                score = float(numbers[-1])
                # Clamp to [0.0, 1.0]
                score = max(0.0, min(1.0, score))
            else:
                # Fallback: try parsing the entire response
                score = float(response_text.strip())
                score = max(0.0, min(1.0, score))

        except (ValueError, AttributeError):
            logger.warning(
                f"Failed to parse score from doc {doc_index + 1}: {response_text[:100]}"
            )
            score = 0.0  # Default to not relevant if parsing fails

        # Add judgment to document
        judged_doc = doc.copy()
        judged_doc["relevance_score"] = round(score, 2)
        judged_doc["relevance_label"] = 1 if score >= relevance_threshold else 0
        judged_doc["original_rank"] = doc_index

        logger.debug(f"   Doc {doc_index + 1}: Score = {score:.2f} (async)")

        return judged_doc, score

    except Exception as e:
        logger.warning(f"Failed to judge document {doc_index + 1}: {e}")
        # Default to not relevant
        judged_doc = doc.copy()
        judged_doc["relevance_score"] = 0.0
        judged_doc["relevance_label"] = 0
        judged_doc["original_rank"] = doc_index

        return judged_doc, 0.0


async def document_judger(state: WorkflowState) -> WorkflowState:
    """
    Judge the relevance of retrieved documents using async parallel processing.

    Args:
        state: Current workflow state containing retrieved documents

    Returns:
        Updated state with judged documents and relevance labels
    """
    logger.debug("Node starting: document_judger")
    try:
        # Get LLM client from config
        # Use reranker_client if available (separate provider), otherwise use primary llm_client
        config = state.get("config", {})
        reranker_client = config.get("reranker_client")
        llm_client = config.get("llm_client")

        # Prefer reranker_client if available, otherwise use primary llm_client
        client_to_use = reranker_client if reranker_client else llm_client

        if not client_to_use:
            raise ValueError(
                "LLM client not found in config (neither reranker_client nor llm_client)"
            )

        if reranker_client:
            logger.debug("Judging documents using separate reranker LLM client (async parallel mode)")
        else:
            logger.debug("Judging documents using primary LLM client (async parallel mode)")

        retrieved_docs = state.get("retrieved_documents", [])
        if not retrieved_docs:
            logger.warning("No documents to judge")
            state["judged_documents"] = []
            state["relevance_labels"] = []
            logger.debug("Node finished: document_judger (no documents)")
            return state

        # Get the judger chain using the appropriate client
        chain = get_judger_chain(llm_client=client_to_use, config=config)

        # Get reranking config
        reranking_config = config.get("reranking_config", {})
        relevance_threshold = reranking_config.get("relevance_threshold", 0.5)

        # Async parallel processing - create tasks for all documents
        logger.info(f"⚙️  Judging {len(retrieved_docs)} documents concurrently (async)")

        tasks = [
            _judge_single_document_async(
                retrieved_docs[i],
                state["query"],
                chain,
                relevance_threshold,
                i,
            )
            for i in range(len(retrieved_docs))
        ]

        # Execute all tasks concurrently with asyncio.gather
        # return_exceptions=True ensures that failed tasks don't stop others
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        judged_docs_dict = {}
        relevance_scores = [0.0] * len(retrieved_docs)
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error judging document {i + 1}: {result}")
                error_count += 1
                # Create fallback document on error
                judged_doc = retrieved_docs[i].copy()
                judged_doc["relevance_score"] = 0.0
                judged_doc["relevance_label"] = 0
                judged_doc["original_rank"] = i
                judged_docs_dict[i] = judged_doc
                relevance_scores[i] = 0.0
            else:
                judged_doc, score = result
                judged_docs_dict[i] = judged_doc
                relevance_scores[i] = score

        # Log error summary if any
        if error_count > 0:
            logger.warning(
                f"{error_count}/{len(retrieved_docs)} documents failed during judging"
            )

        # Reconstruct judged_docs in original order
        judged_docs = [
            judged_docs_dict[i]
            for i in range(len(retrieved_docs))
            if i in judged_docs_dict
        ]

        # Sort documents by relevance score (highest first)
        judged_docs_sorted = sorted(
            judged_docs, key=lambda x: x.get("relevance_score", 0.0), reverse=True
        )

        # Update state
        state["judged_documents"] = judged_docs_sorted
        state["relevance_scores"] = relevance_scores
        state["document_scores"] = [
            doc["relevance_score"] for doc in judged_docs_sorted
        ]

        # Stats
        relevant_count = sum(
            1 for score in relevance_scores if score >= relevance_threshold
        )
        avg_score = (
            sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        )

        logger.debug(
            f"Judged {len(judged_docs)} documents: "
            f"{relevant_count} relevant (threshold: {relevance_threshold}), "
            f"avg score: {avg_score:.2f}"
        )
        logger.debug("Node finished: document_judger")

    except Exception as e:
        error_msg = f"Document judging failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.error("Node finished: document_judger (with error)")

    return state
