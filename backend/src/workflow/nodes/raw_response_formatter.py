"""
Raw response formatter node for DataPilotFlow LangGraph implementation.

This node formats retrieved documents as raw results without LLM generation.
Useful for power users who want to see exact source material.
"""

import opik
from loguru import logger

from src.workflow.state import WorkflowState


def raw_response_formatter(state: WorkflowState) -> WorkflowState:
    """
    Format retrieved documents as raw response without LLM generation.

    Args:
        state: Current workflow state containing judged/retrieved documents

    Returns:
        Updated state with formatted raw response
    """
    logger.info("🚀 [NODE START] raw_response_formatter")
    try:
        # Add processing step
        state["processing_steps"].append("raw_response_formatting")

        # Get documents - use judged_documents if available, otherwise use retrieved_documents
        judged_docs = state.get("judged_documents")

        if judged_docs:
            # Reranking was enabled - filter relevant documents (label = 1)
            relevant_docs = [
                doc for doc in judged_docs if doc.get("relevance_label", 0) == 1
            ]

            if not relevant_docs:
                logger.warning(
                    "⚠️ No relevant documents found after judging, using all judged documents"
                )
                relevant_docs = judged_docs
        else:
            # Reranking was disabled - use all retrieved documents
            logger.info("ℹ️ Using retrieved documents (reranking disabled)")
            relevant_docs = state.get("retrieved_documents", [])

        if not relevant_docs:
            logger.warning("⚠️ No documents to format")
            state["final_answer"] = (
                "No relevant documents found for your query. "
                "Please try rephrasing your question or check if the knowledge base contains relevant information."
            )
            state["context"] = ""
            logger.info("✅ [NODE FINISH] raw_response_formatter (no documents)")
            return state

        # Build structured raw response
        response_parts = []
        response_parts.append(f"**Found {len(relevant_docs)} relevant document(s):**\n")

        for i, doc in enumerate(relevant_docs, 1):
            # Handle both dict and string document formats
            if isinstance(doc, dict):
                doc_text = doc.get("text", "")
            elif isinstance(doc, str):
                doc_text = doc
            else:
                doc_text = str(doc)

            # Format document section
            response_parts.append(f"\n---\n\n### Document {i}\n")

            # Add document content directly (metadata is shown in UI separately)
            response_parts.append(doc_text)

        # Join all parts
        raw_response = "\n".join(response_parts)

        # Add disclaimer at the top
        disclaimer = (
            "**Raw Results Mode** - Showing unmodified documents from knowledge base.\n"
            "These are the exact chunks retrieved without AI summarization or modification.\n"
        )
        raw_response = disclaimer + "\n" + raw_response

        # Build context (same as documents, for compatibility)
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            # Handle both dict and string document formats
            if isinstance(doc, dict):
                doc_text = doc.get("text", "")
            elif isinstance(doc, str):
                doc_text = doc
            else:
                doc_text = str(doc)

            if doc_text:
                context_parts.append(f"{i}. {doc_text}")

        context = "\n".join(context_parts)

        # Update state
        state["context"] = context
        state["final_answer"] = raw_response

        # Add query info (for consistency with answer_generator)
        original_query = state["query"]
        enhanced_query_data = state.get("enhanced_query", {})

        query_info = {
            "original_query": original_query,
            "enhanced_query": None,
            "enhanced_queries": None,  # Array of all enhanced queries
            "strategy_used": None,
        }

        if enhanced_query_data:
            # Get all enhanced queries that were actually used for search
            if enhanced_query_data.get("augmented_queries"):
                # For augmented strategy, show all variants (including original)
                augmented = enhanced_query_data["augmented_queries"]
                query_info["enhanced_queries"] = augmented
                # For backward compatibility, keep single enhanced_query (first variant after original)
                query_info["enhanced_query"] = (
                    augmented[1] if len(augmented) > 1 else augmented[0]
                )
                query_info["strategy_used"] = "Augmented"
                logger.info(
                    f"📝 Raw Response Formatter: Extracted {len(augmented)} augmented queries for query_info"
                )
                logger.info(f"📝 Augmented queries: {augmented}")
            elif enhanced_query_data.get("multi_query_variants"):
                variants = enhanced_query_data["multi_query_variants"]
                query_info["enhanced_queries"] = variants
                query_info["enhanced_query"] = variants[0]
                query_info["strategy_used"] = "Multi-Query"
            elif enhanced_query_data.get("fusion_perspectives"):
                perspectives = enhanced_query_data["fusion_perspectives"]
                query_info["enhanced_queries"] = perspectives
                query_info["enhanced_query"] = perspectives[0]
                query_info["strategy_used"] = "Query Fusion"
            elif enhanced_query_data.get("sub_queries"):
                sub_queries = enhanced_query_data["sub_queries"]
                query_info["enhanced_queries"] = sub_queries
                query_info["enhanced_query"] = sub_queries[0] if sub_queries else None
                query_info["strategy_used"] = "Decomposition"
            elif enhanced_query_data.get("step_back_query"):
                step_back = enhanced_query_data["step_back_query"]
                query_info["enhanced_queries"] = [step_back]
                query_info["enhanced_query"] = step_back
                query_info["strategy_used"] = "Step-Back"
            elif enhanced_query_data.get("hypothetical_answer"):
                hyde = enhanced_query_data["hypothetical_answer"]
                query_info["enhanced_queries"] = [hyde]
                query_info["enhanced_query"] = hyde
                query_info["strategy_used"] = "HyDE"

        state["query_info"] = query_info

        logger.info(f"✅ Formatted {len(relevant_docs)} documents as raw response")
        logger.info("✅ [NODE FINISH] raw_response_formatter")

    except Exception as e:
        error_msg = f"Raw response formatting failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
        logger.error("❌ [NODE FINISH] raw_response_formatter (with error)")

        # Set fallback response
        state["context"] = ""
        state["final_answer"] = (
            "I apologize, but I encountered an error while formatting the raw results. Please try again."
        )

    return state
