"""This module provides tools for the supervisor agent.

Tools are created dynamically from RAG tool + task tools configuration.
This is a placeholder matching react-agent structure.
"""

from typing import Any, Callable, List

# Tools will be injected at runtime from:
# - RAG tool (knowledge_expert)
# - User-configured task tools

TOOLS: List[Callable[..., Any]] = []
