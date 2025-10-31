"""
Answer generator node for DataPilotFlow LangGraph implementation.

This node generates the final answer based on the user's question and relevant documents.
"""

import opik
from loguru import logger

from src.workflow.chains import get_answer_generation_chain
from src.workflow.state import WorkflowState


def answer_generator(state: WorkflowState) -> WorkflowState:
    """
    Generate final answer based on relevant documents.

    Args:
        state: Current workflow state containing judged documents

    Returns:
        Updated state with final answer and context
    """
    logger.info("🚀 [NODE START] answer_generator")
    try:
        # Add processing step
        state["processing_steps"].append("answer_generation")

        # Get LLM client from config
        config = state.get("config", {})
        llm_client = config.get("llm_client")

        if not llm_client:
            raise ValueError("llm_client not found in config")

        logger.info(f"💬 Generating answer using LLM client")

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
            logger.info(f"📄 Retrieved documents count: {len(relevant_docs)}")
            if relevant_docs:
                logger.info(f"📄 First doc keys: {list(relevant_docs[0].keys())}")
                first_doc_text = relevant_docs[0].get("text", "NO TEXT")
                logger.info(f"📄 First doc text type: {type(first_doc_text)}")
                logger.info(
                    f"📄 First doc text length: {len(first_doc_text) if first_doc_text else 0}"
                )
                if first_doc_text:
                    logger.info(f"📄 First doc text preview: {first_doc_text[:200]}...")
                else:
                    logger.error(f"❌ First doc text is empty/None!")
            else:
                logger.error(f"❌ No retrieved documents found in state!")

        # Build context from relevant documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            doc_text = doc.get("text", "")
            if doc_text:
                context_parts.append(f"{i}. {doc_text}")
                logger.debug(f"📄 Added doc {i}: {len(doc_text)} chars")
            else:
                logger.warning(f"⚠️ Doc {i} has no text!")

        context = "\n".join(context_parts)
        logger.info(
            f"📝 Built context with {len(context_parts)} documents, total {len(context)} chars"
        )

        # Check if context is empty
        if not context or not context.strip():
            logger.error("❌ Context is empty! No valid document content found.")
            logger.error(f"❌ relevant_docs count: {len(relevant_docs)}")
            if relevant_docs:
                logger.error(f"❌ First doc sample: {relevant_docs[0]}")

            # Set error message as final answer
            state["final_answer"] = (
                "I apologize, but I couldn't find any relevant information in the knowledge base to answer your question. The documents were retrieved but contained no readable content."
            )
            state["context"] = ""
            logger.error("❌ [NODE FINISH] answer_generator (empty context)")
            return state

        # Pre-check: Verify context relevance to question
        # Quick check if context is semantically related to the query
        logger.debug("🔍 Pre-checking context relevance to query...")

        # Simple heuristic: Check if the context seems completely unrelated
        # We'll let the LLM handle the detailed relevance check via the strict prompt
        # but we can add a basic keyword overlap check here if needed

        # For now, we rely on the strict prompt to handle out-of-domain queries
        # The LLM will respond with "I cannot answer..." if context is irrelevant

        # Get the answer generation chain
        chain = get_answer_generation_chain(llm_client=llm_client, config=config)

        # Invoke the chain
        logger.debug(
            f"🔧 Invoking chain with context length: {len(context)}, question: {state['query'][:50]}..."
        )
        response = chain.invoke({"context": context, "question": state["query"]})

        # Extract content from response
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.info("📝 Answer Generator: Starting query_info extraction")

        # Get query information to show user the difference
        original_query = state["query"]
        enhanced_query_data = state.get("enhanced_query", {})

        logger.info(f"📝 Answer Generator: Got enhanced_query_data from state")

        logger.info(
            f"📝 Answer Generator: enhanced_query_data type: {type(enhanced_query_data)}"
        )
        logger.info(
            f"📝 Answer Generator: enhanced_query_data keys: {list(enhanced_query_data.keys()) if isinstance(enhanced_query_data, dict) else 'Not a dict'}"
        )
        logger.info(f"📝 Answer Generator: enhanced_query_data: {enhanced_query_data}")

        # Build query comparison info
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
                    f"📝 Answer Generator: Extracted {len(augmented)} augmented queries for query_info"
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

        # Update state
        state["context"] = context
        state["final_answer"] = response_text
        state["query_info"] = query_info  # Add query comparison info

        logger.info(
            f"✅ Generated answer using {len(relevant_docs)} relevant documents"
        )
        logger.info("✅ [NODE FINISH] answer_generator")

    except Exception as e:
        error_msg = f"Answer generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
        logger.error("❌ [NODE FINISH] answer_generator (with error)")

        # Set fallback answer
        state["context"] = ""
        state["final_answer"] = (
            "I apologize, but I encountered an error while generating the answer. Please try again."
        )

    return state
