"""Supervisor Agent.

This module defines a custom reasoning and action agent graph with RAG + task tools.
It invokes tools in a simple loop based on langchain-ai/react-agent.

Key exports:
- graph: The compiled LangGraph StateGraph (requires ToolRegistry initialization)
- SupervisorAgentService: Service layer for conversation execution
- ToolRegistry: Tool registry for ID-based tool management
- Context: Configuration context for the agent
- State: Agent state structure with RAG and tool tracking
"""

from src.agents.supervisor_agent.graph import graph, create_graph
from src.agents.supervisor_agent.service import SupervisorAgentService
from src.agents.supervisor_agent.tools import ToolRegistry
from src.agents.supervisor_agent.context import Context
from src.agents.supervisor_agent.state import State
from src.agents.supervisor_agent.tool_initialization import (
    initialize_tools_from_config,
    initialize_tools_from_config_async,
    create_knowledge_expert_tool,
)
from src.agents.supervisor_agent.tool_factory import SupervisorToolFactory
from src.agents.supervisor_agent.generate_response_supervisor import (
    get_response_stream_supervisor,
)

__all__ = [
    "graph",
    "create_graph",
    "SupervisorAgentService",
    "ToolRegistry",
    "Context",
    "State",
    "initialize_tools_from_config",
    "initialize_tools_from_config_async",
    "create_knowledge_expert_tool",
    "SupervisorToolFactory",
    "get_response_stream_supervisor",
]
