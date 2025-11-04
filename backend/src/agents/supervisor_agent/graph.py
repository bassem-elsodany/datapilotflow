"""
Supervisor Agent LangGraph definition.

Defines the orchestration workflow for routing between RAG and Task agents.
"""

from functools import lru_cache
from typing import Any

from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from src.agents.supervisor_agent.nodes import intent_router_node
from src.agents.supervisor_agent.state import SupervisorAgentState
from src.config import settings


@lru_cache(maxsize=1)
def get_graph(llm_client: ChatLiteLLM) -> CompiledStateGraph:
    """
    Build the LangGraph for Supervisor Agent.

    Handles intent detection and routing decisions.

    Args:
        llm_client: ChatLiteLLM client for intent detection

    Returns:
        CompiledStateGraph: The compiled supervisor graph
    """
    logger.debug("Building LangGraph for Supervisor Agent")

    # Create the state graph
    graph_builder = StateGraph(SupervisorAgentState)

    # Add intent router node
    graph_builder.add_node(
        "intent_router", lambda state: intent_router_node(state, llm_client)
    )

    # Define workflow edges
    graph_builder.add_edge(START, "intent_router")
    graph_builder.add_edge("intent_router", END)

    logger.debug("Supervisor Agent graph created successfully")

    # Compile the graph
    return graph_builder.compile()


# Initialize graph (will be called with llm_client)
graph_dev = None
