"""
Augmented query enhancement chain.

This chain generates enhanced query variants while preserving the original query.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..prompts import AUGMENTED_SYSTEM_PROMPT, AUGMENTED_USER_PROMPT


def get_augmented_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create an augmented query enhancement chain.

    This chain generates 2-3 enhanced query variants that complement the original query,
    ensuring no context is lost while benefiting from query improvements.

    Args:
        llm_client: LLM client for generation (already configured with temperature, max_tokens, etc.)
        config: Optional configuration for the chain (not used currently, for future extensibility)

    Returns:
        A runnable chain (prompt | model)
    """
    logger.debug(f"Creating Augmented Chain")

    # Create the prompt (using Python f-string format, not Jinja2)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", AUGMENTED_SYSTEM_PROMPT.prompt),
            ("human", AUGMENTED_USER_PROMPT.prompt),
        ]
    )

    # Return the chain
    # Note: llm_client is already configured with temperature, max_tokens, etc. from conversation settings
    return prompt | llm_client
