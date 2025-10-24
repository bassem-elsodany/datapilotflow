"""
Augmented query enhancement chain.

This chain generates enhanced query variants while preserving the original query.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.workflow.prompts import AUGMENTED_SYSTEM_PROMPT, AUGMENTED_USER_PROMPT


def get_augmented_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create an augmented query enhancement chain.

    This chain generates 2-3 enhanced query variants that complement the original query,
    ensuring no context is lost while benefiting from query improvements.

    Args:
        llm_client: LLM client for generation
        config: Optional configuration for the chain

    Returns:
        A runnable chain (prompt | model)
    """
    config = config or {}
    config.setdefault("temperature", 0.3)
    config.setdefault("max_tokens", 200)

    logger.debug(f"🔗 Creating Augmented Chain with config: {config}")

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", AUGMENTED_SYSTEM_PROMPT.prompt),
            ("human", AUGMENTED_USER_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    # Return the chain
    return prompt | llm_client
