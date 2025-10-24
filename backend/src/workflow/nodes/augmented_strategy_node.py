"""
Augmented query enhancement strategy node.

This node generates enhanced query variants while preserving the original query,
ensuring no context is lost while benefiting from query improvements.
"""

import json
from typing import Any, Dict

import opik
from loguru import logger

from src.workflow.chains import get_augmented_chain
from src.workflow.state import WorkflowState


@opik.track(name="augmented_strategy_node", tags=["query_enhancement", "augmented"])
async def augmented_strategy_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Apply the Augmented query enhancement strategy.

    This strategy generates 2-3 enhanced query variants that complement the original query.
    The original query is ALWAYS preserved and used alongside the enhanced variants.

    Args:
        state: Current workflow state

    Returns:
        Updated state with augmented queries
    """
    query = state["query"]
    config = state.get("config", {})

    llm_config = config.get("llm_config", {})
    llm_provider_id = llm_config.get("provider_id")
    llm_model_name = llm_config.get("model_name")

    logger.info(f"🔄 Augmented Strategy: Enhancing query '{query[:50]}...'")

    try:
        # Get LLM client from config
        llm_client = config.get("llm_client")
        if not llm_client:
            raise ValueError("llm_client not found in config")

        # Get the chain
        chain = get_augmented_chain(llm_client=llm_client, config=config)

        # Invoke the chain
        response = await chain.ainvoke({"query": query})

        # Parse the response
        enhanced_variants = []
        try:
            # Try to parse as JSON
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            enhanced_variants = json.loads(content)

            if not isinstance(enhanced_variants, list):
                logger.warning(
                    f"⚠️ Augmented Strategy: Expected list, got {type(enhanced_variants)}"
                )
                enhanced_variants = [content]

        except json.JSONDecodeError:
            logger.warning(
                "⚠️ Augmented Strategy: Failed to parse JSON, using raw response"
            )
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            # Split by newlines and filter empty lines
            enhanced_variants = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.strip().startswith(("[", "]", "{", "}"))
            ]

        # Ensure we have at least one variant
        if not enhanced_variants:
            logger.warning(
                "⚠️ Augmented Strategy: No variants generated, using original query"
            )
            enhanced_variants = [query]

        # Combine original query with enhanced variants
        # Original query ALWAYS comes first to preserve context
        augmented_queries = [query] + enhanced_variants

        logger.info(
            f"✅ Augmented Strategy: Generated {len(enhanced_variants)} variants + original query"
        )
        logger.debug(f"   Original: {query}")
        for i, variant in enumerate(enhanced_variants, 1):
            logger.debug(f"   Variant {i}: {variant}")

        # Update state
        return {
            "enhanced_query": query,  # Keep original as primary
            "augmented_queries": augmented_queries,  # Original + variants
            "enhancement_strategies_applied": ["augmented"],
        }

    except Exception as e:
        logger.error(f"❌ Augmented Strategy failed: {e}")
        logger.exception(e)

        # Fallback: use original query only
        return {
            "enhanced_query": query,
            "augmented_queries": [query],
            "enhancement_strategies_applied": ["augmented_fallback"],
        }
