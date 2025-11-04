"""
Task Agent chains package.

Contains LangChain Expression Language (LCEL) chains for task execution.
"""

from .task_execution_chain import get_task_execution_chain

__version__ = "1.0.0"

__all__ = ["get_task_execution_chain"]
