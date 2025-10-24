"""
HyDE Strategy Node for Query Enhancement.

This node generates hypothetical answers for better embedding-based retrieval.
It uses the HyDE chain which includes Opik tracing for observability.
"""

import time
from typing import Any, Dict

import opik
from loguru import logger

from ..chains import get_hyde_chain
from ..state import WorkflowState


@opik.track(name="hyde_strategy_node", tags=["query_enhancement", "hyde"])
async def hyde_strategy_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Execute HyDE (Hypothetical Document Embeddings) strategy.

    Generates hypothetical answers for better embedding-based retrieval.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        Dict[str, Any]: Updated state with hypothetical answer
    """
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

        return {
            "enhanced_query": {
                "hypothetical_answer": hypothetical_answer,
            },
            "enhancement_strategies_applied": ["hyde"],
        }

    except Exception as e:
        logger.error(f"❌ HyDE node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "enhanced_query": {},
            "enhancement_strategies_applied": [],
        }
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  HyDE node completed in {elapsed:.2f}ms")
