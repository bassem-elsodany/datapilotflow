"""Supervisor Agent Tools Package."""

# NOTE: default_tools.py is deprecated (tools are now managed as standalone entities)

from src.agents.supervisor_agent.tools.rag_knowledge_tool import (
    create_rag_knowledge_tool,
)
from src.agents.supervisor_agent.tools.tool_factory import (
    ToolFactory,
    get_dynamic_task_tools,
)

__version__ = "1.0.0"

__all__ = [
    "create_rag_knowledge_tool",
    "ToolFactory",
    "get_dynamic_task_tools",
    # "get_default_tools",  # Deprecated
    # "create_default_tool_config_for_conversation",  # Deprecated
]
