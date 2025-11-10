"""
Decomposition Chain for Query Enhancement.

This chain breaks complex queries into simpler sub-questions.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from ..prompts import DECOMPOSITION_SYSTEM_PROMPT, DECOMPOSITION_USER_PROMPT


def get_decomposition_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a query decomposition chain.

    This chain uses Opik tracking (via the Prompt class) to provide full
    traceability of the decomposition process.

    Args:
        llm_client (Any): LLM client for generation (already configured with temperature, max_tokens, etc.)
        config (Dict[str, Any], optional): Chain configuration (not used currently, for future extensibility)

    Returns:
        Runnable chain (prompt | model)

    Example:
        >>> chain = get_decomposition_chain(llm_client)
        >>> result = await chain.ainvoke({"query": "How to secure and rate-limit REST APIs?"})
        >>> print(result.content)
        "COMPLEX\\n1. How to set up authentication?\\n2. How to configure rate limiting?"
    """
    logger.debug(f"Creating Decomposition Chain")

    # Get prompts (Opik tracking happens in Prompt class if enabled)
    system_prompt = DECOMPOSITION_SYSTEM_PROMPT.prompt
    user_prompt_template = DECOMPOSITION_USER_PROMPT.prompt

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt_template),
        ]
    )

    # Return the chain (prompt | model)
    # Note: llm_client is already configured with temperature, max_tokens, etc. from conversation settings
    return prompt | llm_client
