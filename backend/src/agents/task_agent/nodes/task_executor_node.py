"""
Task Executor Node for Task Agent.

Executes tasks using LLM with optional RAG context injection.
"""

from typing import Any, Dict

from langchain_core.language_models.base import BaseLanguageModel
from loguru import logger

from src.agents.task_agent.chains import get_task_execution_chain
from src.agents.task_agent.state import TaskAgentState


def task_executor_node(state: TaskAgentState) -> Dict[str, Any]:
    """
    Execute user task using LLM.

    Handles:
    - Code generation
    - Task planning
    - Data analysis
    - Problem solving
    - Any LLM-capable task

    Args:
        state: Current TaskAgentState (llm_client extracted from config)

    Returns:
        Updated state with task_result populated
    """
    logger.info("🔨 Task Executor Node: Starting task execution")

    # Extract llm_client from config (same pattern as RAG Agent)
    config = state.get("config", {}) or {}
    llm_client = config.get("llm_client")

    if not llm_client:
        logger.error("❌ llm_client not found in config")
        return {"task_result": "❌ Error: LLM client not configured"}

    user_request = state.get("user_request", "")
    if not user_request:
        logger.error("❌ No user request in state")
        return {"task_result": "❌ Error: Empty task request"}

    logger.debug(f"📝 Task Executor: Processing request: {user_request[:100]}...")

    # Check if RAG context available
    has_rag_context = state.get("rag_knowledge") is not None
    rag_knowledge_content = state.get("rag_knowledge", "")
    conversation_description = state.get("conversation_description", "")

    logger.info(f"📚 [TASK EXECUTOR] RAG Knowledge Available: {has_rag_context}")
    if has_rag_context:
        logger.info(f"📚 [TASK EXECUTOR] RAG Knowledge length: {len(rag_knowledge_content)} chars")
        logger.info(f"📚 [TASK EXECUTOR] RAG Knowledge preview: {rag_knowledge_content[:200]}...")
    else:
        logger.warning("⚠️  [TASK EXECUTOR] NO RAG Knowledge provided - will use standalone prompts")

    if conversation_description:
        logger.info(f"📝 [TASK EXECUTOR] Conversation Description: {conversation_description[:100]}...")

    # Get task execution chain
    chain = get_task_execution_chain(llm_client, use_rag_context=has_rag_context)

    # Execute chain
    try:
        # Build input with correct variable names matching the prompts
        chain_input = {"task_request": user_request}
        if has_rag_context:
            chain_input["rag_context"] = rag_knowledge_content
            logger.info(f"📚 [TASK EXECUTOR] Injected RAG context into chain input")

        if conversation_description:
            chain_input["conversation_description"] = conversation_description
            logger.info(f"📝 [TASK EXECUTOR] Injected conversation description into chain input")

        result = chain.invoke(chain_input)
        task_result = result.content if hasattr(result, "content") else str(result)

        logger.info(f"✅ Task Executor: Generated result ({len(task_result)} chars)")

        return {
            "task_result": task_result,
            "task_details": {
                "type": "task_execution",
                "used_rag_context": has_rag_context,
                "execution_status": "success",
            },
        }

    except Exception as e:
        logger.error(f"❌ Task Executor Node error: {e}")
        return {
            "task_result": f"❌ Task execution failed: {str(e)}",
            "task_details": {
                "type": "task_execution",
                "execution_status": "failed",
                "error": str(e),
            },
        }
