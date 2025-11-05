"""
Task Execution Chain for Task Agent.

LCEL chain for executing any task using LLM with optional RAG context injection.
"""

from typing import Optional

from langchain_community.chat_models import ChatLiteLLM
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.agents.task_agent.prompts.task_prompts import (
    TASK_SYSTEM_PROMPT,
    TASK_USER_PROMPT,
    TASK_WITH_RAG_SYSTEM_PROMPT,
    TASK_WITH_RAG_USER_PROMPT,
)


def get_task_execution_chain(llm_client: ChatLiteLLM, use_rag_context: bool = False):
    """
    Create LCEL chain for task execution.

    Args:
        llm_client: ChatLiteLLM client
        use_rag_context: Whether RAG context is available for knowledge injection

    Returns:
        LCEL chain for task execution
    """
    logger.debug(f"Creating task execution chain (use_rag_context={use_rag_context})")

    # Select appropriate prompts based on RAG context availability
    if use_rag_context:
        system_prompt = str(TASK_WITH_RAG_SYSTEM_PROMPT)
        user_prompt = str(TASK_WITH_RAG_USER_PROMPT)
        logger.info("🎯 [TASK CHAIN] Using RAG-enhanced prompts with knowledge base context")
    else:
        system_prompt = str(TASK_SYSTEM_PROMPT)
        user_prompt = str(TASK_USER_PROMPT)
        logger.info("🎯 [TASK CHAIN] Using standard prompts WITHOUT knowledge base")

    logger.debug(f"🎯 [TASK CHAIN] User prompt template: {user_prompt[:200]}...")

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    # Create chain: prompt | llm
    chain = prompt | llm_client

    return chain
