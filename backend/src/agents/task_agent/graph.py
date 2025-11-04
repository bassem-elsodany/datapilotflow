"""
Task Agent LangGraph definition.

Defines the task execution workflow for handling any task with optional RAG context.
"""

from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from src.agents.task_agent.nodes import task_executor_node
from src.agents.task_agent.state import TaskAgentState
from src.config import settings


@lru_cache(maxsize=1)
def get_graph() -> CompiledStateGraph:
    """
    Build the LangGraph for Task Agent.

    Executes any task using LLM with optional RAG context injection.
    The llm_client is passed through state config, not as a parameter.

    Returns:
        CompiledStateGraph: The compiled task execution graph
    """
    logger.debug("Building LangGraph for Task Agent")

    # Create the state graph
    graph_builder = StateGraph(TaskAgentState)

    # Add task executor node (llm_client will be extracted from state config)
    graph_builder.add_node("task_executor", task_executor_node)

    # Define workflow edges
    graph_builder.add_edge(START, "task_executor")
    graph_builder.add_edge("task_executor", END)

    logger.debug("Task Agent graph created successfully")

    # Compile the graph
    return graph_builder.compile()


# Initialize graph at module load time (cached, no parameters)
graph_dev = get_graph()
