"""
Step-Back Chain for Query Enhancement.

This chain generates broader, more conceptual questions from specific queries
to help retrieve foundational knowledge.
"""

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.config import settings
from src.workflow.prompts import STEP_BACK_SYSTEM_PROMPT, STEP_BACK_USER_PROMPT


def get_step_back_chain(llm_client: Any, config: Optional[Dict[str, Any]] = None):
    """
    Create a step-back prompting chain.

    This chain uses Opik tracking (via the Prompt class) to provide full
    traceability of the step-back prompting process.

    Args:
        llm_client (Any): LLM client for generation (already configured with temperature, max_tokens, etc.)
        config (Dict[str, Any], optional): Chain configuration (not used currently, for future extensibility)

    Returns:
        Runnable chain (prompt | model)

    Example:
        >>> chain = get_step_back_chain(llm_client)
        >>> result = await chain.ainvoke({"query": "How to configure SSL in Mule 4.5?"})
        >>> print(result.content)
        "What are the fundamental principles of security configuration in MuleSoft?"
    """
    logger.debug(f"🔗 Creating Step-Back Chain")

    # Get prompts (Opik tracking happens in Prompt class if enabled)
    system_prompt = STEP_BACK_SYSTEM_PROMPT.prompt
    user_prompt_template = STEP_BACK_USER_PROMPT.prompt

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
