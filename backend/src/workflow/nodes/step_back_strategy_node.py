"""
Step-Back Strategy Node for Query Enhancement.

This node generates broader, more conceptual questions to retrieve foundational knowledge.
It uses the step-back chain which includes Opik tracing for observability.
"""

import time
from typing import Any, Dict

import opik
from loguru import logger

from ..chains import get_step_back_chain
from ..state import WorkflowState


@opik.track(name="step_back_strategy_node", tags=["query_enhancement", "step_back"])
async def step_back_strategy_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Execute Step-Back Prompting strategy.

    Generates broader, more conceptual questions to retrieve foundational knowledge.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        Dict[str, Any]: Updated state with step-back query
    """
    start_time = time.time()
    logger.info("🔄 Executing Step-Back Strategy Node")

    try:
        query = state["query"]
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("step_back", {})
        config.setdefault("temperature", 0.3)
        config.setdefault("max_tokens", 100)

        logger.debug(f"Generating step-back question for: '{query[:50]}...'")

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_step_back_chain(llm_client=llm_client, config=config)
        response = await chain.ainvoke({"query": query})

        step_back_query = response.content.strip()

        if not step_back_query:
            raise ValueError("LLM returned empty step-back question")

        logger.info(f"✅ Step-Back: '{query[:50]}...' → '{step_back_query[:50]}...'")

        return {
            "enhanced_query": {
                "step_back_query": step_back_query,
            },
            "enhancement_strategies_applied": ["step_back"],
        }

    except Exception as e:
        logger.error(f"❌ Step-Back node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "enhanced_query": {},
            "enhancement_strategies_applied": [],
        }
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Step-Back node completed in {elapsed:.2f}ms")
