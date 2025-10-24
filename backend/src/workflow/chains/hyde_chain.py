"""
HyDE Chain for Query Enhancement.

This chain generates hypothetical answers for better embedding-based retrieval.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from src.workflow.prompts import HYDE_SYSTEM_PROMPT, HYDE_USER_PROMPT


def get_hyde_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a HyDE (Hypothetical Document Embeddings) chain.

    This chain uses Opik tracking (via the Prompt class) to provide full
    traceability of the HyDE generation process.

    Args:
        llm_client (Any): LLM client for generation
        config (Dict[str, Any], optional): Chain configuration

    Returns:
        Runnable chain (prompt | model)

    Example:
        >>> chain = get_hyde_chain(llm_client)
        >>> result = await chain.ainvoke({"query": "How to configure database pooling?"})
        >>> print(result.content[:100])
        "Database connection pooling is configured through application.properties..."
    """
    config = config or {}
    config.setdefault("temperature", 0.7)
    config.setdefault("max_tokens", 500)
    config.setdefault("style", "documentation")

    logger.debug(f"🔗 Creating HyDE Chain with config: {config}")

    # Get prompts (Opik tracking happens in Prompt class if enabled)
    system_prompt = HYDE_SYSTEM_PROMPT.prompt
    user_prompt_template = HYDE_USER_PROMPT.prompt

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt_template),
        ]
    )

    # Return the chain (prompt | model)
    return prompt | llm_client
