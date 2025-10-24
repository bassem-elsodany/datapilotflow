"""
Decomposition Strategy Node for Query Enhancement.

This node breaks complex queries into simpler sub-questions.
It uses the decomposition chain which includes Opik tracing for observability.
"""

import re
import time
from typing import Any, Dict, List

import opik
from loguru import logger

from ..chains import get_decomposition_chain
from ..state import WorkflowState


@opik.track(
    name="decomposition_strategy_node", tags=["query_enhancement", "decomposition"]
)
async def decomposition_strategy_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Execute Query Decomposition strategy.

    Breaks complex queries into simpler sub-questions.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        Dict[str, Any]: Updated state with sub-queries
    """
    start_time = time.time()
    logger.info("🔄 Executing Decomposition Strategy Node")

    try:
        query = state["query"]
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("decomposition", {})
        config.setdefault("temperature", 0.2)
        config.setdefault("max_tokens", 300)
        config.setdefault("max_sub_queries", 5)
        config.setdefault("min_sub_queries", 2)

        logger.debug(f"Analyzing query complexity: '{query[:50]}...'")

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_decomposition_chain(llm_client=llm_client, config=config)
        response = await chain.ainvoke({"query": query})

        # Parse response
        response_text = response.content.strip()
        is_complex, sub_queries = _parse_decomposition_response(response_text, config)

        if is_complex and sub_queries:
            logger.info(f"✅ Decomposition: Generated {len(sub_queries)} sub-queries")

            return {
                "enhanced_query": {
                    "sub_queries": sub_queries,
                },
                "enhancement_strategies_applied": ["decomposition"],
            }
        else:
            logger.info("ℹ️  Query is simple, no decomposition needed")
            return {
                "enhanced_query": {},
                "enhancement_strategies_applied": [],
            }

    except Exception as e:
        logger.error(f"❌ Decomposition node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "enhanced_query": {},
            "enhancement_strategies_applied": [],
        }
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Decomposition node completed in {elapsed:.2f}ms")


def _parse_decomposition_response(
    response: str, config: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Parse LLM response to extract complexity and sub-questions.

    Expected formats:
    - Complex: "COMPLEX\\n1. Question 1\\n2. Question 2..."
    - Simple: "SIMPLE" or "This question is simple..."

    Args:
        response (str): LLM response text
        config (Dict[str, Any]): Configuration with min/max sub_queries

    Returns:
        tuple[bool, List[str]]: (is_complex, sub_questions)
    """
    response = response.strip()

    # Check if simple
    if response.upper().startswith("SIMPLE"):
        return False, []

    # Check if complex
    if response.upper().startswith("COMPLEX"):
        # Extract numbered sub-questions
        lines = response.split("\n")[1:]  # Skip "COMPLEX" line

        sub_queries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering (1. 2. etc.)
            cleaned = re.sub(r"^\d+\.\s*", "", line)
            cleaned = cleaned.strip()

            if cleaned:
                sub_queries.append(cleaned)

        # Validate and limit
        if len(sub_queries) < config.get("min_sub_queries", 2):
            logger.warning(
                f"Too few sub-queries ({len(sub_queries)}), treating as simple"
            )
            return False, []

        if len(sub_queries) > config.get("max_sub_queries", 5):
            logger.warning(f"Too many sub-queries ({len(sub_queries)}), truncating")
            sub_queries = sub_queries[: config["max_sub_queries"]]

        return True, sub_queries

    # Fallback: try to extract numbered questions anyway
    numbered_pattern = r"^\d+\.\s*(.+)$"
    lines = response.split("\n")
    potential_queries = []

    for line in lines:
        match = re.match(numbered_pattern, line.strip())
        if match:
            potential_queries.append(match.group(1).strip())

    if len(potential_queries) >= config.get("min_sub_queries", 2):
        return True, potential_queries[: config["max_sub_queries"]]

    # Default to simple
    return False, []
