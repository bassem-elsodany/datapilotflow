"""
Multi-Query Strategy Node for Query Enhancement.

This node generates multiple query variants for improved retrieval coverage.
It uses the multi-query chain which includes Opik tracing for observability.
"""

import re
import time
from typing import Any, Dict, List

import opik
from loguru import logger

from ..chains import get_multi_query_chain
from ..state import WorkflowState


@opik.track(name="multi_query_strategy_node", tags=["query_enhancement", "multi_query"])
async def multi_query_strategy_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Execute Multi-Query Expansion strategy.

    Generates multiple query variants for improved retrieval coverage.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        Dict[str, Any]: Updated state with query variants
    """
    start_time = time.time()
    logger.info("🔄 Executing Multi-Query Strategy Node")

    try:
        query = state["query"]
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("multi_query", {})
        config.setdefault("temperature", 0.7)
        config.setdefault("max_tokens", 300)
        config.setdefault("num_variants", 5)
        config.setdefault("min_variants", 2)
        config.setdefault("include_original", True)

        logger.debug(
            f"Generating {config['num_variants']} query variants "
            f"for: '{query[:50]}...'"
        )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_multi_query_chain(llm_client=llm_client, config=config)
        response = await chain.ainvoke({"query": query})

        # Parse variants from response
        variants = _parse_variants(response.content, config)

        # Validate minimum variants
        if len(variants) < config.get("min_variants", 2):
            logger.warning(
                f"Generated only {len(variants)} variants, "
                f"expected at least {config['min_variants']}"
            )

        # Optionally include original
        if config.get("include_original", True) and query not in variants:
            variants.insert(0, query)

        logger.info(f"✅ Multi-Query: Generated {len(variants)} variants")

        return {
            "enhanced_query": {
                "multi_query_variants": variants,
            },
            "enhancement_strategies_applied": ["multi_query"],
        }

    except Exception as e:
        logger.error(f"❌ Multi-Query node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "enhanced_query": {},
            "enhancement_strategies_applied": [],
        }
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Multi-Query node completed in {elapsed:.2f}ms")


def _parse_variants(llm_response: str, config: Dict[str, Any]) -> List[str]:
    """
    Parse query variants from LLM response.

    Expected format: numbered or bulleted list of variants.

    Args:
        llm_response (str): Raw LLM response
        config (Dict[str, Any]): Configuration with num_variants

    Returns:
        List[str]: Parsed query variants
    """
    lines = llm_response.strip().split("\n")
    variants = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove numbering and bullets
        cleaned = re.sub(r"^[\d]+[\.\)]\s*|^[\-\*\•]\s*", "", line)
        cleaned = cleaned.strip()

        # Filter out too-short lines and meta-commentary
        if (
            cleaned
            and len(cleaned) > 10
            and not cleaned.startswith(("Here", "The", "These"))
        ):
            variants.append(cleaned)

    # Limit to configured number
    max_variants = config.get("num_variants", 5)
    return variants[:max_variants]
