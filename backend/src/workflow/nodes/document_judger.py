"""
Document judger node for DataPilotFlow LangGraph implementation.

This node judges the relevance of retrieved documents to the user's question.
"""

import opik
from loguru import logger

from src.workflow.chains import get_judger_chain
from src.workflow.state import WorkflowState


def document_judger(state: WorkflowState) -> WorkflowState:
    """
    Judge the relevance of retrieved documents.

    Args:
        state: Current workflow state containing retrieved documents

    Returns:
        Updated state with judged documents and relevance labels
    """
    logger.info("🚀 [NODE START] document_judger")
    try:
        # Add processing step
        state["processing_steps"].append("document_judging")

        # Get LLM client from config
        config = state.get("config", {})
        llm_client = config.get("llm_client")

        if not llm_client:
            raise ValueError("llm_client not found in config")

        logger.info(f"🔍 Judging documents using LLM client")

        retrieved_docs = state.get("retrieved_documents", [])
        if not retrieved_docs:
            logger.warning("⚠️ No documents to judge")
            state["judged_documents"] = []
            state["relevance_labels"] = []
            logger.info("✅ [NODE FINISH] document_judger (no documents)")
            return state

        # Get the judger chain
        chain = get_judger_chain(llm_client=llm_client, config=config)

        judged_docs = []
        relevance_scores = []

        # Get reranking config
        reranking_config = config.get("reranking_config", {})
        relevance_threshold = reranking_config.get("relevance_threshold", 0.5)
        use_score_based = reranking_config.get("use_score_based", True)

        # Judge each document
        for i, doc in enumerate(retrieved_docs):
            try:
                # Invoke the chain
                response = chain.invoke(
                    {"query": state["query"], "document": doc["text"]}
                )

                # Extract content from response
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Parse judgment result - extract last number from response
                try:
                    # Try to find the last number in the response (the score)
                    import re

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
                        f"⚠️ Failed to parse score from: {response_text[:100]}"
                    )
                    score = 0.0  # Default to not relevant if parsing fails

                # Add judgment to document
                judged_doc = doc.copy()
                judged_doc["relevance_score"] = round(score, 2)
                judged_doc["relevance_label"] = 1 if score >= relevance_threshold else 0
                judged_doc["original_rank"] = i
                judged_docs.append(judged_doc)
                relevance_scores.append(score)

                logger.debug(f"   Doc {i+1}: Score = {score:.2f}")

            except Exception as e:
                logger.warning(f"⚠️ Failed to judge document: {e}")
                # Default to not relevant
                judged_doc = doc.copy()
                judged_doc["relevance_score"] = 0.0
                judged_doc["relevance_label"] = 0
                judged_doc["original_rank"] = i
                judged_docs.append(judged_doc)
                relevance_scores.append(0.0)

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

        logger.info(
            f"✅ Judged {len(judged_docs)} documents: "
            f"{relevant_count} relevant (threshold: {relevance_threshold}), "
            f"avg score: {avg_score:.2f}"
        )
        logger.info("✅ [NODE FINISH] document_judger")

    except Exception as e:
        error_msg = f"Document judging failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
        logger.error("❌ [NODE FINISH] document_judger (with error)")

        # Set empty results
        state["judged_documents"] = []
        state["relevance_labels"] = []

    return state
