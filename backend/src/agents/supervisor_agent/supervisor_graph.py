"""
Supervisor Graph using Official LangGraph Supervisor Library.

This module implements the supervisor agent orchestration using the official
langgraph-supervisor library's create_supervisor() function for proper
tool-based handoff mechanism with minimal boilerplate.

Reference: https://github.com/langchain-ai/langgraph-supervisor-py
"""

from typing import Any, Optional
from langgraph_supervisor import create_supervisor
from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from src.agents.common.agent_state import AgentState
from src.agents.rag_agent import RAGAgentService
from src.agents.task_agent import TaskAgentService


def create_supervisor_graph_with_agents(
    llm_client: ChatLiteLLM,
    rag_agent: RAGAgentService,
    task_agent: TaskAgentService,
) -> CompiledStateGraph:
    """
    Create a supervisor graph using langgraph-supervisor library.

    The library's create_supervisor() function automatically:
    1. Wraps each agent as a callable tool
    2. Creates tool-based handoff mechanism
    3. Implements LLM-driven routing
    4. Manages message history and context injection

    Args:
        llm_client: ChatLiteLLM client for supervisor reasoning
        rag_agent: RAGAgentService instance (must have rag_graph attribute)
        task_agent: TaskAgentService instance

    Returns:
        Compiled StateGraph with tool-based supervisor routing
    """
    logger.info("🏭 Building Supervisor Graph using langgraph-supervisor library")

    # Extract compiled graphs from agents
    # The library expects Pregel/CompiledStateGraph objects
    agents = [rag_agent.rag_graph, task_agent.task_graph]

    # System prompt for supervisor LLM
    # Instructs the supervisor on how to route between agents
    supervisor_prompt = """
You are an intelligent supervisor orchestrating multiple specialist agents.

You have access to:
1. **RAG Agent** - For retrieving and ranking documents from the knowledge base
   - Use this when the user needs information from documents
   - Use this to gather knowledge before executing tasks

2. **Task Agent** - For executing tasks, generating code, and analysis
   - Use this for task execution, planning, and creative work
   - This agent has access to RAG context if you retrieve documents first

Your routing strategy:
- For questions about documents: Use RAG Agent → delegate to RAG Agent
- For tasks requiring knowledge: Use RAG Agent first → then Task Agent
- For pure tasks: Use Task Agent directly
- Always provide the full context to the agent you delegate to

Be decisive about routing. Do not over-explain your choices.
"""

    logger.info("🔧 Creating supervisor with tool-based handoff mechanism")

    # Create supervisor using the library
    # This automatically:
    # - Creates tool nodes for each agent
    # - Sets up conditional routing
    # - Configures message handling
    supervisor_graph = create_supervisor(
        agents=agents,  # List of compiled agent graphs
        model=llm_client,  # LLM for supervisor reasoning
        prompt=supervisor_prompt,  # Routing instructions
        output_mode="last_message",  # Only include final agent response
        add_handoff_messages=True,  # Track agent delegations
        handoff_tool_prefix="delegate_to_",  # Tool naming convention
    )

    logger.info("✅ Supervisor Graph created successfully using langgraph-supervisor")

    return supervisor_graph
