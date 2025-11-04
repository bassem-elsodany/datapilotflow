"""
Task Agent prompts package.

Contains prompts for task execution, planning, and analysis.
"""

from src.agents.task_agent.prompts.task_prompts import (
    TASK_SYSTEM_PROMPT,
    TASK_USER_PROMPT,
    TASK_WITH_RAG_SYSTEM_PROMPT,
    TASK_WITH_RAG_USER_PROMPT,
)

__version__ = "1.0.0"

__all__ = [
    "TASK_SYSTEM_PROMPT",
    "TASK_USER_PROMPT",
    "TASK_WITH_RAG_SYSTEM_PROMPT",
    "TASK_WITH_RAG_USER_PROMPT",
]
