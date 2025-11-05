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

            # Debug: Log what RAG context we received
            if rag_context:
                logger.info(f"🎯 [TASK AGENT] RAG Context found:")
                logger.info(f"   - Retrieved count: {rag_context.retrieved_count}")
                logger.info(f"   - Relevant count: {rag_context.relevant_count}")
                logger.info(f"   - Judged docs count: {len(rag_context.judged_documents) if rag_context.judged_documents else 0}")
                if rag_context.judged_documents and len(rag_context.judged_documents) > 0:
                    logger.info(f"   - First doc keys: {list(rag_context.judged_documents[0].keys())}")
                    logger.info(f"   - First doc sample: {str(rag_context.judged_documents[0])[:200]}...")
            else:
                logger.warning("⚠️  [TASK AGENT] NO RAG Context received!")

            # Format RAG knowledge for injection
            rag_knowledge_str = None
            if rag_context:
                rag_knowledge_str = self._format_rag_knowledge(rag_context)
                logger.info(f"📚 [TASK AGENT] Formatted RAG knowledge length: {len(rag_knowledge_str)} chars")
                logger.info(f"📚 [TASK AGENT] RAG knowledge preview: {rag_knowledge_str[:300]}...")

            # Extract conversation description from state (passed from supervisor)
            conversation_description = state.get("conversation_description")
            if conversation_description:
                logger.info(f"📝 [TASK AGENT] Conversation description: {conversation_description[:100]}...")

            task_state = create_initial_state(
                user_request=user_request,
                rag_knowledge=rag_knowledge_str,
                conversation_description=conversation_description,
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

        logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] Processing {len(judged_docs)} judged documents")
        logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] Type of judged_docs: {type(judged_docs)}")

        if judged_docs and len(judged_docs) > 0:
            logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] First doc type: {type(judged_docs[0])}")
            logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] First doc: {str(judged_docs[0])[:500]}")

        # Filter for relevant documents (label = 1)
        relevant_docs = [doc for doc in judged_docs if doc.get('relevance_label', 0) == 1]
        logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] Found {len(relevant_docs)} relevant documents (label=1)")

        # Use relevant docs, fallback to all if none marked as relevant
        docs_to_use = relevant_docs if relevant_docs else judged_docs
        logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] Using {len(docs_to_use)} documents for formatting")

        # Format top 10 documents for context
        docs_text_parts = []
        for i, doc in enumerate(docs_to_use[:10]):
            # Log document structure
            if i == 0:
                logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] First doc keys: {list(doc.keys())}")
                logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] First doc: {str(doc)[:300]}")

            # Try to get title - use chunk_id or source_url as fallback
            title = doc.get('title') or doc.get('source_url') or doc.get('chunk_id', 'Untitled')
            relevance_score = doc.get('relevance_score', doc.get('distance', 0))
            text_content = doc.get('text', '')[:500]

            logger.critical(f"🔴 [FORMAT_RAG_KNOWLEDGE] Doc {i+1}: title={title}, relevance={relevance_score}, text_len={len(text_content)}")

            doc_text = f"\n[Document {i+1}] {title}\nRelevance: {relevance_score:.2f}\nContent: {text_content}..."
            docs_text_parts.append(doc_text)

        docs_text = "\n".join(docs_text_parts)

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
