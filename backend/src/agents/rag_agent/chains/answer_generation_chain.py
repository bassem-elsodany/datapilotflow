"""
Answer generation chain for final response synthesis.

This chain generates the final answer based on context and the user's query.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..prompts import GENERATION_SYSTEM_PROMPT, GENERATION_USER_PROMPT


def get_answer_generation_chain(
    llm_client: Any, config: Optional[Dict[str, Any]] = None
):
    """
    Create an answer generation chain.

    This chain generates the final answer based on retrieved context and the user's query.

    Args:
        llm_client: LLM client for generation (already configured with temperature, max_tokens, etc.)
        config: Optional configuration for the chain (not used currently, for future extensibility)

    Returns:
        A runnable chain (prompt | model)
    """
    logger.debug(f"🔗 Creating Answer Generation Chain")

    # Create the prompt (using Python f-string format, not Jinja2)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GENERATION_SYSTEM_PROMPT.prompt),
            ("human", GENERATION_USER_PROMPT.prompt),
        ]
    )

    # Return the chain
    # Note: llm_client is already configured with temperature, max_tokens, etc. from conversation settings
    return prompt | llm_client
