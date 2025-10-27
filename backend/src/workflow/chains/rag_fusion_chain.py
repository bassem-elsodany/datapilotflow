"""
RAG-Fusion Chain for Query Enhancement.

This chain generates multiple query perspectives for fusion-based retrieval.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from src.workflow.prompts import RAG_FUSION_SYSTEM_PROMPT, RAG_FUSION_USER_PROMPT


def get_rag_fusion_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a RAG-Fusion chain for generating query perspectives.

    This chain uses Opik tracking (via the Prompt class) to provide full
    traceability of the RAG-Fusion generation process.

    Args:
        llm_client (Any): LLM client for generation (already configured with temperature, max_tokens, etc.)
        config (Dict[str, Any], optional): Chain configuration (not used currently, for future extensibility)

    Returns:
        Runnable chain (prompt | model)

    Example:
        >>> chain = get_rag_fusion_chain(llm_client)
        >>> result = await chain.ainvoke({"query": "How to optimize database queries?"})
        >>> print(result.content)
        "1. What are SQL optimization techniques?\\n2. How to improve indexes?..."
    """
    logger.debug(f"🔗 Creating RAG-Fusion Chain")

    # Get prompts (Opik tracking happens in Prompt class if enabled)
    system_prompt = RAG_FUSION_SYSTEM_PROMPT.prompt
    user_prompt_template = RAG_FUSION_USER_PROMPT.prompt

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
