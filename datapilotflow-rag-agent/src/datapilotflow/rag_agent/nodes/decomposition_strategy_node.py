"""Decomposition Strategy Node for Query Enhancement.

This node breaks complex queries into simpler sub-questions.
It uses the decomposition chain which includes Opik tracing for observability.
"""

import json
import re
import time
from typing import Any, Dict, List

from loguru import logger

from ..chains import get_decomposition_chain
from ..state import RAGWorkflowState as WorkflowState


async def decomposition_strategy_node(state: WorkflowState) -> WorkflowState:
    """Execute Query Decomposition strategy.

    Breaks complex queries into simpler sub-questions.

    Args:
        state (WorkflowState): Current workflow state

    Returns:
        WorkflowState: Updated state with sub-queries
    """
    logger.debug("Node starting: [NODE START] decomposition_strategy_node")
    start_time = time.time()
    logger.info("🔄 Executing Decomposition Strategy Node")

    try:
        query = state["query"]
        conversation_description = state.get("conversation_description")
        llm_client = state.get("config", {}).get("llm_client")

        if not llm_client:
            raise ValueError("LLM client not found in state config")

        # Decomposition-specific configuration
        config = {
            "max_sub_queries": 5,
            "min_sub_queries": 2,
        }

        logger.debug(f"Analyzing query complexity: '{query[:50]}...'")
        logger.debug(f"Using provider's temperature and max_tokens from LLM client")

        if conversation_description:
            logger.debug(
                f" Using conversation description for context: '{conversation_description[:50]}...'"
            )

        # Create and execute chain (with Opik tracing if enabled)
        chain = get_decomposition_chain(llm_client=llm_client, config=config)

        # Format conversation description for the prompt (always pass a string)
        description_text = ""
        if conversation_description:
            description_text = f"**Context**: This conversation is about: {conversation_description}\n\nUse this context to break down queries into domain-relevant sub-questions."

        chain_input = {"query": query, "conversation_description": description_text}
        response = await chain.ainvoke(chain_input)

        # Parse response
        response_text = response.content.strip()
        sub_queries = _parse_decomposition_response(response_text, config)

        if sub_queries and len(sub_queries) >= 2:
            logger.debug(f"Decomposition: Generated {len(sub_queries)} sub-queries")
            # Update state
            state["enhanced_query"] = {"sub_queries": sub_queries}
            state["enhancement_strategies_applied"] = ["decomposition"]
            logger.debug("[NODE FINISH] decomposition_strategy_node")
            return state
        else:
            logger.warning(f" Failed to generate sub-queries, using original query only")
            # Fallback: use original query as single sub-query
            state["enhanced_query"] = {"sub_queries": [query]}
            state["enhancement_strategies_applied"] = ["decomposition"]
            logger.debug("[NODE FINISH] decomposition_strategy_node")
            return state

    except Exception as e:
        logger.error(f"Decomposition node error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"[NODE FINISH] decomposition_strategy_node (with error)")
        # Fallback
        state["enhanced_query"] = {}
        state["enhancement_strategies_applied"] = []
        return state
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⏱ Decomposition node completed in {elapsed:.2f}ms")


def _parse_decomposition_response(
    response: str, config: Dict[str, Any]
) -> List[str]:
    """Parse LLM response to extract sub-questions.

    Expected format: JSON array of strings
    ["Question 1", "Question 2", "Question 3"]

    Args:
        response (str): LLM response text (should be JSON array)
        config (Dict[str, Any]): Configuration with min/max sub_queries

    Returns:
        List[str]: List of sub-questions
    """
    response = response.strip()

    # Remove markdown code blocks if present
    if response.startswith("```"):
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"```\s*$", "", response)
        response = response.strip()

    try:
        # Parse JSON array
        sub_queries = json.loads(response)

        if not isinstance(sub_queries, list):
            logger.warning(f"LLM returned non-array JSON: {type(sub_queries)}")
            return []

        # Filter out non-string items and empty strings
        sub_queries = [
            q.strip() for q in sub_queries if isinstance(q, str) and q.strip()
        ]

        # Validate and limit
        if len(sub_queries) > config.get("max_sub_queries", 5):
            logger.warning(
                f"Too many sub-queries ({len(sub_queries)}), truncating to {config['max_sub_queries']}"
            )
            sub_queries = sub_queries[: config["max_sub_queries"]]

        if sub_queries:
            logger.debug(f"Extracted {len(sub_queries)} sub-queries from JSON array")
        else:
            logger.warning(f"No valid sub-queries found in JSON array")

        return sub_queries

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw response: {response[:200]}...")
        return []
