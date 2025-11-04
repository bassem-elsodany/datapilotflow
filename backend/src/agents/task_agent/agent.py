"""Task Agent service implementation."""

import logging
from typing import Any, Dict, List, Optional

from langchain_community.chat_models import ChatLiteLLM
from loguru import logger

from src.agents.common.agent_interface import AgentService
from src.agents.common.agent_state import AgentState, RAGContext
from src.agents.task_agent.graph import get_graph
from src.agents.task_agent.state import TaskAgentState, create_initial_state


class TaskAgentService(AgentService):
    """
    Universal Task Agent.

    Responsibilities:
    - Handle any task using LLM: code generation, planning, analysis, etc.
    - Optionally inject RAG knowledge if available
    - Work standalone (no RAG) or with injected knowledge
    - Return task results for display to user

    This agent can perform:
    - Code generation (any language)
    - Task planning and workflow creation
    - Data analysis
    - Problem solving
    - Content writing
    - Explanation and clarification
    - Any other LLM-capable task
    """

    def __init__(self, llm_client: ChatLiteLLM):
        """
        Initialize Task Agent.

        Args:
            llm_client: ChatLiteLLM client for task execution
        """
        self.llm_client = llm_client
        self.task_graph = None
        logger.info("✅ Task Agent initialized")

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the task using LLM.

        If RAG context is available in state, injects it as knowledge.
        Otherwise, uses conversation history and LLM's base knowledge.

        Args:
            state: Current AgentState containing messages and optional RAG context

        Returns:
            Updated AgentState with task_result populated
        """
        try:
            logger.info("🔨 Task Agent: Starting task execution")

            # Extract task/request from messages
            messages = state.get("messages", [])
            if not messages:
                raise ValueError("No messages in state")

            user_message = messages[-1]
            user_request = user_message.get("content", "")

            if not user_request:
                raise ValueError("Empty request in message")

            logger.debug(f"📝 Task Agent: Processing request: {user_request[:100]}...")

            # Create initial task state
            rag_context = state.get("rag_context")
            task_state = create_initial_state(
                user_request=user_request,
                rag_knowledge=(
                    self._format_rag_knowledge(rag_context) if rag_context else None
                ),
            )

            # Add llm_client to config (same pattern as RAG Agent)
            config = state.get("config", {}) or {}
            task_state["config"] = {**config, "llm_client": self.llm_client}

            logger.debug("⚙️  Task Agent: Running task graph")

            # Get the cached task graph (no parameters, cached with @lru_cache)
            task_graph = get_graph()
            result = await task_graph.ainvoke(task_state)

            logger.info(f"✅ Task Agent: Execution complete")

            # Extract results
            task_result = result.get("task_result", "")
            task_details = result.get("task_details", {})

            # Update state with task results
            state["task_result"] = task_result
            state["task_details"] = task_details

            # Add result to message history
            result_message = {
                "role": "assistant",
                "content": task_result,
            }
            state["messages"] = state.get("messages", []) + [result_message]

            logger.info("🎉 Task Agent: Execution complete")
            return state

        except Exception as e:
            logger.error(f"❌ Task Agent error: {e}")
            error_message = {
                "role": "assistant",
                "content": f"❌ Task Agent failed: {str(e)}",
            }
            state["messages"] = state.get("messages", []) + [error_message]
            raise

    def _format_rag_knowledge(self, rag_context: RAGContext) -> str:
        """
        Format RAG results into knowledge injection for task execution.

        Args:
            rag_context: RAGContext from RAG Agent execution

        Returns:
            Formatted knowledge string
        """
        judged_docs = rag_context.judged_documents
        relevant_count = rag_context.relevant_count

        # Format top 10 documents for context
        docs_text = "\n".join(
            [
                f"\n[Document {i+1}] {doc.get('title', 'Untitled')}\n"
                f"Relevance: {doc.get('relevance_score', 0):.2f}\n"
                f"Content: {doc.get('text', '')[:500]}..."
                for i, doc in enumerate(judged_docs[:10])
            ]
        )

        return f"""Additional Context - Knowledge Base Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Documents Analyzed: {rag_context.retrieved_count}
Relevant Documents: {relevant_count} (threshold: {rag_context.relevance_threshold})
Relevance: Documents ranked by relevance score (0.0-1.0)

Top Documents for Your Task:
{docs_text}

IMPORTANT: Use this knowledge base information to:
1. Reference actual documents when relevant
2. Base your solution on real information
3. Provide accurate, grounded responses
4. Mention document sources in your answer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    def get_agent_name(self) -> str:
        """Return agent name."""
        return "Task Agent"

    def get_supported_intents(self) -> List[str]:
        """Return supported intent types."""
        return ["rag_then_task"]

    def get_description(self) -> str:
        """Return agent description."""
        return (
            "Universal task execution agent. Handles code generation, planning, "
            "analysis, problem solving, and any other task. Can work standalone "
            "or with RAG knowledge injection."
        )
