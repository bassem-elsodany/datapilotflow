"""Raw response formatter node for DataPilotFlow LangGraph implementation.

This node formats retrieved documents as raw results without LLM generation.
Useful for power users who want to see exact source material.
"""

from loguru import logger

from ..state import RAGWorkflowState as WorkflowState


def raw_response_formatter(state: WorkflowState) -> WorkflowState:
    """Format retrieved documents as raw response without LLM generation.

    Args:
        state: Current workflow state containing judged/retrieved documents

    Returns:
        Updated state with formatted raw response
    """
    logger.debug("Node starting: [NODE START] raw_response_formatter")

    try:
        # Get documents - use judged_documents if available, otherwise use retrieved_documents
        judged_docs = state.get("judged_documents")

        if judged_docs:
            # Reranking was enabled - filter relevant documents (label = 1)
            relevant_docs = [
                doc for doc in judged_docs if doc.get("relevance_label", 0) == 1
            ]

            if not relevant_docs:
                logger.warning(
                    " No relevant documents found after judging, using all judged documents"
                )
                relevant_docs = judged_docs

        else:
            # Reranking was disabled - use all retrieved documents
            logger.debug(f"Using retrieved documents (reranking disabled)")
            relevant_docs = state.get("retrieved_documents", [])

        if not relevant_docs:
            logger.warning(f"No documents to format")
            state["final_answer"] = (
                "No relevant documents found for your query. "
                "Please try rephrasing your question or check if the knowledge base contains relevant information."
            )
            state["context"] = ""
            logger.debug("[NODE FINISH] raw_response_formatter (no documents)")
            return state

        # Build structured raw response with rich Markdown formatting
        response_parts = []

        # Add header with disclaimer
        disclaimer = (
            "# Raw Results Mode\n"
            "> Showing unmodified documents from knowledge base.\n"
            "> These are the exact chunks retrieved without AI summarization or modification.\n"
        )
        response_parts.append(disclaimer)

        # Add summary
        response_parts.append(f"\n**Found {len(relevant_docs)} relevant document(s):**\n")

        # Store structured documents for task tools
        structured_docs = []

        for i, doc in enumerate(relevant_docs, 1):
            # Handle both dict and string document formats
            if isinstance(doc, dict):
                doc_text = doc.get("text", "")
                doc_source = doc.get("source_url", "")
                doc_chunk_id = doc.get("chunk_id", "")
                doc_metadata = doc.get("metadata", {})
                relevance_score = doc.get("relevance_score")
                relevance_label = doc.get("relevance_label")

            elif isinstance(doc, str):
                doc_text = doc
                doc_source = ""
                doc_chunk_id = ""
                doc_metadata = {}
                relevance_score = None
                relevance_label = None

            else:
                doc_text = str(doc)
                doc_source = ""
                doc_chunk_id = ""
                doc_metadata = {}
                relevance_score = None
                relevance_label = None

            # Store structured document for task tools
            structured_doc = {
                "index": i,
                "content": doc_text,
                "source": doc_source,
                "chunk_id": doc_chunk_id,
                "metadata": doc_metadata,
                "relevance_score": relevance_score,
                "relevance_label": relevance_label,
            }
            structured_docs.append(structured_doc)

            # Format document header with metadata
            doc_header = f"\n---\n## Document {i}"
            if doc_chunk_id:
                doc_header += f" | `{doc_chunk_id}`"
            doc_header += "\n"
            response_parts.append(doc_header)

            # Add metadata section if available
            metadata_parts = []
            if doc_source:
                metadata_parts.append(f"**Source:** `{doc_source}`")
            if relevance_score is not None:
                relevance_pct = (
                    int(relevance_score * 100)
                    if isinstance(relevance_score, float)
                    else relevance_score
                )
                metadata_parts.append(f"**Relevance Score:** {relevance_pct}%")
            if relevance_label is not None:
                relevance_status = (
                    "✓ Relevant" if relevance_label == 1 else "✗ Not Relevant"
                )
                metadata_parts.append(f"**Label:** {relevance_status}")

            if metadata_parts:
                response_parts.append("\n".join(metadata_parts))
                response_parts.append("\n\n")

            # Add document content (preserve newlines in content)
            response_parts.append(doc_text)
            if doc_text and not doc_text.endswith("\n"):
                response_parts.append("\n")

        # Join all parts
        raw_response = "".join(response_parts)

        # Store structured documents in state for task tools to access
        state["structured_documents"] = structured_docs
        logger.info(
            f" Created {len(structured_docs)} structured documents for task tools"
        )

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
                # Use LLM variants directly (nodes no longer prepend original query)
                augmented = enhanced_query_data["augmented_queries"]
                query_info["enhanced_queries"] = augmented
                query_info["enhanced_query"] = augmented[0] if augmented else None
                query_info["strategy_used"] = "Augmented"
                logger.info(
                    f" Raw Response Formatter: Extracted {len(augmented)} enhanced queries from LLM"
                )
                logger.debug(f"Enhanced queries: {augmented}")

            elif enhanced_query_data.get("multi_query_variants"):
                # Use LLM variants directly (nodes no longer prepend original query)
                variants = enhanced_query_data["multi_query_variants"]
                query_info["enhanced_queries"] = variants
                query_info["enhanced_query"] = variants[0] if variants else None
                query_info["strategy_used"] = "Multi-Query"
                logger.info(
                    f" Raw Response Formatter: Extracted {len(variants)} enhanced queries from LLM"
                )

            elif enhanced_query_data.get("sub_queries"):
                sub_queries = enhanced_query_data["sub_queries"]
                query_info["enhanced_queries"] = sub_queries
                query_info["enhanced_query"] = sub_queries[0] if sub_queries else None
                query_info["strategy_used"] = "Decomposition"

            elif enhanced_query_data.get("hypothetical_answer"):
                hyde = enhanced_query_data["hypothetical_answer"]
                query_info["enhanced_queries"] = [hyde]
                query_info["enhanced_query"] = hyde
                query_info["strategy_used"] = "HyDE"

        state["query_info"] = query_info

        logger.debug(f"Formatted {len(relevant_docs)} documents as raw response")
        logger.debug("[NODE FINISH] raw_response_formatter")

    except Exception as e:
        error_msg = f"Raw response formatting failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"{error_msg}")
        logger.error(f"[NODE FINISH] raw_response_formatter (with error)")

        # Set fallback response with actual error details
        state["context"] = ""
        state["final_answer"] = (
            f"I apologize, but I encountered an error while formatting the raw results: {str(e)}"
        )

    return state
