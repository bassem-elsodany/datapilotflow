"""
Document judging chain for relevance assessment.

This chain judges whether a retrieved document is relevant to the user's query.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.workflow.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT


def get_judger_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a document judging chain.

    This chain judges the relevance of a document to a query, returning 0 or 1.

    Args:
        llm_client: LLM client for judging (already configured with temperature, max_tokens, etc.)
        config: Optional configuration for the chain (not used currently, for future extensibility)

    Returns:
        A runnable chain (prompt | model)
    """
    logger.debug(f"🔗 Creating Judger Chain")

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", JUDGE_SYSTEM_PROMPT.prompt),
            ("human", JUDGE_USER_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    # Return the chain
    # Note: llm_client is already configured with temperature, max_tokens, etc. from conversation settings
    return prompt | llm_client
