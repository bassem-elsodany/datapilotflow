"""
Document judger node for DataPilotFlow LangGraph implementation.

This node judges the relevance of retrieved documents to the user's question.
"""

import opik
from loguru import logger

from src.workflow.chains import get_judger_chain
from src.workflow.state import WorkflowState


@opik.track(name="document_judger", tags=["document_judging", "reranking"])
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
        relevance_labels = []

        # Judge each document
        for doc in retrieved_docs:
            try:
                # Invoke the chain
                response = chain.invoke(
                    {"query": state["query"], "document": doc["text"]}
                )

                # Extract content from response
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Parse judgment result
                try:
                    judgment = int(response_text.strip())
                    if judgment not in [0, 1]:
                        judgment = 0  # Default to not relevant
                except (ValueError, AttributeError):
                    judgment = 0  # Default to not relevant if parsing fails

                # Add judgment to document
                judged_doc = doc.copy()
                judged_doc["relevance_label"] = judgment
                judged_docs.append(judged_doc)
                relevance_labels.append(judgment)

            except Exception as e:
                logger.warning(f"⚠️ Failed to judge document: {e}")
                # Default to not relevant
                judged_doc = doc.copy()
                judged_doc["relevance_label"] = 0
                judged_docs.append(judged_doc)
                relevance_labels.append(0)

        # Update state
        state["judged_documents"] = judged_docs
        state["relevance_labels"] = relevance_labels

        relevant_count = sum(relevance_labels)
        logger.info(
            f"✅ Judged {len(judged_docs)} documents, {relevant_count} relevant"
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
