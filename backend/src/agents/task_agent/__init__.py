"""
Task Agent Tools Package

Provides custom tools for task execution (code generation, planning, analysis, etc.)
to be used with LangChain's create_agent.

We rely on LangChain's ready-made create_agent for all agent logic.
This package only defines the tools the agent can use.
"""

from src.agents.task_agent.tools import get_task_agent_tools

__all__ = ["get_task_agent_tools"]
