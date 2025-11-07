"""Multi-agent orchestrator factory and utilities."""

import logging
from typing import Any, Dict, Optional

from langchain_community.chat_models import ChatLiteLLM

from ..agents.rag_agent import RAGAgentService
from ..agents.supervisor_agent import SupervisorAgentService
from ..agents.task_agent import TaskAgentService
from ..agents.common import AgentState

logger = logging.getLogger(__name__)


def create_multi_agent_orchestrator(
    llm_client: ChatLiteLLM,
    rag_graph: Any,
    conversation_service: Optional[Any] = None,
) -> SupervisorAgentService:
    """
    Factory function to create the complete multi-agent system.

    Creates and wires up:
    - RAG Agent: Handles document retrieval and ranking
    - Task Agent: Handles any task execution
    - Supervisor Agent: Routes between agents and orchestrates workflow

    Args:
        llm_client: LangChain LLM client
        rag_graph: Compiled LangGraph for RAG pipeline
        conversation_service: Optional conversation service

    Returns:
        Configured SupervisorAgentService ready to process user requests
    """
    logger.info("🏭 Creating multi-agent orchestrator...")

    # Create individual agents
    logger.info("📦 Initializing RAG Agent...")
    rag_agent = RAGAgentService(
        llm_client=llm_client,
        rag_graph=rag_graph,
        conversation_service=conversation_service,
    )

    logger.info("📦 Initializing Task Agent...")
    task_agent = TaskAgentService(llm_client=llm_client)

    logger.info("📦 Initializing Supervisor Agent...")
    supervisor = SupervisorAgentService(llm_client=llm_client)

    # Register worker agents with supervisor
    supervisor.set_agents(rag_agent=rag_agent, task_agent=task_agent)

    logger.info("✅ Multi-agent orchestrator created successfully")
    logger.info(
        f"   - Supervisor: {supervisor.get_agent_name()}")
    logger.info(f"   - RAG Agent: {rag_agent.get_agent_name()}")
    logger.info(f"   - Task Agent: {task_agent.get_agent_name()}")

    return supervisor


async def process_user_query(
    supervisor: SupervisorAgentService,
    user_query: str,
    conversation_id: str,
    user_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for processing user requests through the multi-agent system.

    Args:
        supervisor: Configured SupervisorAgentService
        user_query: User's input query
        conversation_id: Conversation identifier
        user_id: User identifier
        config: Optional configuration dict

    Returns:
        Dict with results containing:
        - final_response: Response from agent(s)
        - intent: Detected user intent
        - rag_context: RAG results if RAG was executed
        - task_result: Task results if Task agent was executed
    """
    logger.info(f"🚀 Processing user query: {user_query[:100]}...")

    # Create initial state
    initial_state = AgentState(
        messages=[{"role": "user", "content": user_query}],
        conversation_id=conversation_id,
        user_id=user_id,
        config=config or {},
    )

    try:
        # Execute supervisor (which orchestrates all agents)
        result_state = await supervisor.execute(initial_state)

        # Extract final response
        final_response = result_state.messages[-1].get("content", "")

        return {
            "success": True,
            "final_response": final_response,
            "intent": result_state.intent,
            "rag_context": result_state.rag_context,
            "task_result": result_state.task_result,
            "messages": result_state.messages,
        }

    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        return {
            "success": False,
            "error": str(e),
            "final_response": f"❌ Error: {str(e)}",
        }
