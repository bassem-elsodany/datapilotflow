"""
Step-Back Strategy Node for Query Enhancement.

This node generates broader, more conceptual questions to retrieve foundational knowledge.
It uses the step-back chain which includes Opik tracing for observability.
"""

import time

import opik
from loguru import logger

from src.workflow.chains import get_step_back_chain
from src.workflow.state import WorkflowState


async def step_back_strategy_node(state: WorkflowState) -> WorkflowState:
    """
    Execute Step-Back Prompting strategy.

    Generates broader, more conceptual questions to retrieve foundational knowledge.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        WorkflowState: Updated state with step-back query
    """
    logger.info("🚀 [NODE START] step_back_strategy_node")
    start_time = time.time()
    logger.info("🔄 Executing Step-Back Strategy Node")

    try:
        query = state["query"]
        conversation_description = state.get("conversation_description")
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Get configuration
        config = state.get("enhancement_config", {}).get("step_back", {})
        config.setdefault("temperature", 0.3)
        config.setdefault("max_tokens", 100)

        logger.debug(f"Generating step-back question for: '{query[:50]}...'")
        if conversation_description:
            logger.debug(
                f"📝 Using conversation description for context: '{conversation_description[:50]}...'"
            )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_step_back_chain(llm_client=llm_client, config=config)

        # Invoke with query and optional description
        chain_input = {"query": query}
        if conversation_description:
            chain_input["conversation_description"] = conversation_description

        response = await chain.ainvoke(chain_input)

        step_back_query = response.content.strip()

        if not step_back_query:
            raise ValueError("LLM returned empty step-back question")

        logger.info(f"✅ Step-Back: '{query[:50]}...' → '{step_back_query[:50]}...'")

        # Update state
        state["enhanced_query"] = {"step_back_query": step_back_query}
        state["enhancement_strategies_applied"] = ["step_back"]

        logger.info("✅ [NODE FINISH] step_back_strategy_node")
        return state

    except Exception as e:
        logger.error(f"❌ Step-Back node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("❌ [NODE FINISH] step_back_strategy_node (with error)")

        # Fallback
        state["enhanced_query"] = {}
        state["enhancement_strategies_applied"] = []
        return state
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Step-Back node completed in {elapsed:.2f}ms")
