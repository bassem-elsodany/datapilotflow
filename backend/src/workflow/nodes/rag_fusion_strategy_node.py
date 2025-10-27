"""
RAG-Fusion Strategy Node for Query Enhancement.

This node generates multiple query perspectives for fusion-based retrieval.
It uses the RAG-Fusion chain which includes Opik tracing for observability.
"""

import re
import time
from typing import Any, Dict, List

import opik
from loguru import logger

from src.workflow.chains import get_rag_fusion_chain
from src.workflow.state import WorkflowState


async def rag_fusion_strategy_node(state: WorkflowState) -> WorkflowState:
    """
    Execute RAG-Fusion strategy.

    Generates multiple query perspectives for fusion-based retrieval.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        Dict[str, Any]: Updated state with fusion perspectives
    """
    logger.info("🚀 [NODE START] rag_fusion_strategy_node")
    start_time = time.time()
    logger.info("🔄 Executing RAG-Fusion Strategy Node")

    try:
        query = state["query"]
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("rag_fusion", {})
        config.setdefault("temperature", 0.8)
        config.setdefault("max_tokens", 100)
        config.setdefault("num_perspectives", 3)
        config.setdefault("include_original", True)

        logger.debug(
            f"Generating {config['num_perspectives']} query perspectives "
            f"for: '{query[:50]}...'"
        )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_rag_fusion_chain(llm_client=llm_client, config=config)
        response = await chain.ainvoke({"query": query})

        # Parse perspectives from response
        perspectives = _parse_perspectives(response.content)

        if len(perspectives) < 2:
            raise ValueError(
                f"Expected at least 2 perspectives, got {len(perspectives)}"
            )

        # Optionally include original query
        if config["include_original"] and query not in perspectives:
            perspectives.insert(0, query)

        logger.info(f"✅ RAG-Fusion: Generated {len(perspectives)} perspectives")

        # Update state
        state["enhanced_query"] = {"fusion_perspectives": perspectives}
        state["enhancement_strategies_applied"] = ["rag_fusion"]

        logger.info("✅ [NODE FINISH] rag_fusion_strategy_node")
        return state

    except Exception as e:
        logger.error(f"❌ RAG-Fusion node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ [NODE FINISH] rag_fusion_strategy_node (with error)")

        # Fallback
        state["enhanced_query"] = {}
        state["enhancement_strategies_applied"] = []
        return state
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  RAG-Fusion node completed in {elapsed:.2f}ms")


def _parse_perspectives(llm_response: str) -> List[str]:
    """
    Parse query perspectives from LLM response.

    The LLM is expected to return perspectives as a numbered or bulleted list.

    Args:
        llm_response (str): Raw response from LLM

    Returns:
        List[str]: List of query perspectives
    """
    logger.info("🚀 [NODE START] rag_fusion_strategy_node")
    lines = llm_response.strip().split("\n")
    perspectives = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove numbering and bullets
        cleaned = re.sub(r"^[\d]+[\.\)]\s*|^[\-\*\•]\s*", "", line)
        cleaned = cleaned.strip()

        if cleaned and len(cleaned) > 10:
            perspectives.append(cleaned)

    return perspectives
