"""
HyDE Strategy Node for Query Enhancement.

This node generates hypothetical answers for better embedding-based retrieval.
It uses the HyDE chain which includes Opik tracing for observability.
"""

import time

import opik
from loguru import logger

from src.workflow.chains import get_hyde_chain
from src.workflow.state import WorkflowState


async def hyde_strategy_node(state: WorkflowState) -> WorkflowState:
    """
    Execute HyDE (Hypothetical Document Embeddings) strategy.

    Generates hypothetical answers for better embedding-based retrieval.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        WorkflowState: Updated state with hypothetical answer
    """
    logger.info("🚀 [NODE START] hyde_strategy_node")
    start_time = time.time()
    logger.info("🔄 Executing HyDE Strategy Node")

    try:
        query = state["query"]
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("hyde", {})
        config.setdefault("temperature", 0.7)
        config.setdefault("max_tokens", 500)
        config.setdefault("style", "documentation")

        logger.debug(
            f"Generating hypothetical answer ({config['style']} style) "
            f"for: '{query[:50]}...'"
        )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_hyde_chain(llm_client=llm_client, config=config)
        response = await chain.ainvoke({"query": query})

        hypothetical_answer = response.content.strip()

        if not hypothetical_answer:
            raise ValueError("LLM returned empty hypothetical answer")

        logger.info(
            f"✅ HyDE: Generated {len(hypothetical_answer.split())} word answer"
        )

        # Update state
        state["enhanced_query"] = {"hypothetical_answer": hypothetical_answer}
        state["enhancement_strategies_applied"] = ["hyde"]

        logger.info("✅ [NODE FINISH] hyde_strategy_node")
        return state

    except Exception as e:
        logger.error(f"❌ HyDE node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ [NODE FINISH] hyde_strategy_node (with error)")

        # Fallback
        state["enhanced_query"] = {}
        state["enhancement_strategies_applied"] = []
        return state
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  HyDE node completed in {elapsed:.2f}ms")
