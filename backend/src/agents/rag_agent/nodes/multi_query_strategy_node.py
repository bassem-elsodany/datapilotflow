"""
Multi-Query Strategy Node for Query Enhancement.

This node generates multiple query variants for improved retrieval coverage.
It uses the multi-query chain which includes Opik tracing for observability.
"""

import re
import time
from typing import Any

import opik
from loguru import logger

from ..chains import get_multi_query_chain
from ..state import RAGWorkflowState as WorkflowState


async def multi_query_strategy_node(state: WorkflowState) -> WorkflowState:
    """
    Execute Multi-Query Expansion strategy.

    Generates multiple query variants for improved retrieval coverage.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        WorkflowState: Updated state with query variants
    """
    logger.info("🚀 [NODE START] multi_query_strategy_node")
    start_time = time.time()
    logger.info("🔄 Executing Multi-Query Strategy Node")

    try:
        query = state["query"]
        conversation_description = state.get("conversation_description")
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = {
            "num_variants": 5,
            "min_variants": 2,
            "include_original": True,
        }

        logger.debug(
            f"Generating {config['num_variants']} query variants "
            f"for: '{query[:50]}...'"
        )
        logger.debug(f"Using provider's temperature and max_tokens from LLM client")
        if conversation_description:
            logger.debug(
                f"📝 Using conversation description for context: '{conversation_description[:50]}...'"
            )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_multi_query_chain(llm_client=llm_client, config=config)

        # Format conversation description for the prompt (always pass a string)
        description_text = ""
        if conversation_description:
            description_text = f"**Context**: This conversation is about: {conversation_description}\n\nUse this context to generate alternative phrasings relevant to this domain."

        chain_input = {"query": query, "conversation_description": description_text}

        response = await chain.ainvoke(chain_input)

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

        # Update state
        state["enhanced_query"] = {"multi_query_variants": variants}
        state["enhancement_strategies_applied"] = ["multi_query"]

        logger.info("✅ [NODE FINISH] multi_query_strategy_node")
        return state

    except Exception as e:
        logger.error(f"❌ Multi-Query node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ [NODE FINISH] multi_query_strategy_node (with error)")

        # Fallback
        state["enhanced_query"] = {}
        state["enhancement_strategies_applied"] = []
        return state
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Multi-Query node completed in {elapsed:.2f}ms")


def _parse_variants(llm_response: str, config: dict[str, Any]) -> list[str]:
    """
    Parse query variants from LLM response.

    Expected format: JSON array of strings
    ["Alternative 1", "Alternative 2", "Alternative 3"]

    Args:
        llm_response (str): Raw LLM response (should be JSON array)
        config (Dict[str, Any]): Configuration with num_variants

    Returns:
        List[str]: Parsed query variants
    """
    import json

    response = llm_response.strip()

    # Remove markdown code blocks if present
    if response.startswith("```"):
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"```\s*$", "", response)
        response = response.strip()

    try:
        # Parse JSON array
        variants = json.loads(response)

        if not isinstance(variants, list):
            logger.warning(f"⚠️  LLM returned non-array JSON: {type(variants)}")
            return []

        # Filter out non-string items and empty strings
        variants = [v.strip() for v in variants if isinstance(v, str) and v.strip()]

        # Limit to configured number
        max_variants = config.get("num_variants", 5)
        if len(variants) > max_variants:
            logger.warning(
                f"Too many variants ({len(variants)}), truncating to {max_variants}"
            )
            variants = variants[:max_variants]

        if variants:
            logger.info(f"📝 Extracted {len(variants)} query variants from JSON array")
        else:
            logger.warning("⚠️  No valid variants found in JSON array")

        return variants

    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"Raw response: {response[:200]}...")
        return []
