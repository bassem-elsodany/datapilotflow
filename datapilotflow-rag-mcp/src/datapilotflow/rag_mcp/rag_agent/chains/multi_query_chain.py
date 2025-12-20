"""
Multi-Query Chain for Query Enhancement.

This chain generates multiple query variants for improved retrieval coverage.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from ..prompts import MULTI_QUERY_SYSTEM_PROMPT, MULTI_QUERY_USER_PROMPT


def get_multi_query_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a multi-query expansion chain.

    This chain uses Opik tracking (via the Prompt class) to provide full
    traceability of the multi-query expansion process.

    Args:
        llm_client (Any): LLM client for generation (already configured with temperature, max_tokens, etc.)
        config (Dict[str, Any], optional): Chain configuration (not used currently, for future extensibility)

    Returns:
        Runnable chain (prompt | model)

    Example:
        >>> chain = get_multi_query_chain(llm_client)
        >>> result = await chain.ainvoke({"query": "How to deploy microservices?"})
        >>> print(result.content)
        "1. What are microservices deployment strategies?\\n2. How to containerize..."
    """
    logger.debug(f"Creating Multi-Query Chain")

    # Get prompts (Opik tracking happens in Prompt class if enabled)
    system_prompt = MULTI_QUERY_SYSTEM_PROMPT.prompt
    user_prompt_template = MULTI_QUERY_USER_PROMPT.prompt

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
