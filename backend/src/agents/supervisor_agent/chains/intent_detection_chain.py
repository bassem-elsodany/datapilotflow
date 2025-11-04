"""
Intent Detection Chain for Supervisor Agent.

This chain classifies user intent for routing to appropriate agents.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..prompts import INTENT_DETECTION_PROMPT


def get_intent_detection_chain(
    llm_client: Any, config: Optional[Dict[str, Any]] = None
):
    """
    Create an intent detection chain.

    This chain classifies user intent to route between RAG and Task agents.

    Args:
        llm_client: LLM client for intent detection (already configured with temperature, max_tokens, etc.)
        config: Optional configuration for the chain (not used currently, for future extensibility)

    Returns:
        A runnable chain (prompt | model)
    """
    logger.debug("🔗 Creating Intent Detection Chain")

    # Create the prompt (using Python f-string format, not Jinja2)
    prompt = ChatPromptTemplate.from_template(INTENT_DETECTION_PROMPT.prompt)

    # Return the chain
    # Note: llm_client is already configured with temperature, max_tokens, etc. from conversation settings
    return prompt | llm_client
