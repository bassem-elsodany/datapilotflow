"""Tool registry for supervisor agent.

Provides a tool registry pattern for managing RAG tool + task tools.
Tools are indexed by ID and retrieved at runtime.
No semantic search - simple ID-based lookup.
"""

from typing import Dict, List, Optional, Union, Callable
from langchain_core.tools import BaseTool


class ToolRegistry:
    """Registry for managing tools by ID."""

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, Union[BaseTool, Callable]] = {}

    def register(self, tool_id: str, tool: Union[BaseTool, Callable]) -> None:
        """Register a tool by ID.

        Args:
            tool_id: Unique identifier for the tool
            tool: LangChain BaseTool or callable
        """
        self._tools[tool_id] = tool

    def register_many(self, tools: Dict[str, Union[BaseTool, Callable]]) -> None:
        """Register multiple tools.

        Args:
            tools: Dict mapping tool IDs to tools
        """
        self._tools.update(tools)

    def get(self, tool_id: str) -> Optional[Union[BaseTool, Callable]]:
        """Get a tool by ID.

        Args:
            tool_id: Tool identifier

        Returns:
            Tool or None if not found
        """
        return self._tools.get(tool_id)

    def get_by_ids(self, tool_ids: List[str]) -> List[Union[BaseTool, Callable]]:
        """Get multiple tools by IDs.

        Args:
            tool_ids: List of tool identifiers

        Returns:
            List of tools (skips missing IDs)
        """
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def get_all(self) -> List[Union[BaseTool, Callable]]:
        """Get all tools in registry.

        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def list_ids(self) -> List[str]:
        """List all tool IDs.

        Returns:
            List of tool identifiers
        """
        return list(self._tools.keys())

    def __contains__(self, tool_id: str) -> bool:
        """Check if tool exists.

        Args:
            tool_id: Tool identifier

        Returns:
            True if tool exists
        """
        return tool_id in self._tools

    def __len__(self) -> int:
        """Get number of tools.

        Returns:
            Number of tools in registry
        """
        return len(self._tools)

    def __getitem__(self, tool_id: str) -> Union[BaseTool, Callable]:
        """Get tool by ID using bracket notation.

        Args:
            tool_id: Tool identifier

        Returns:
            Tool

        Raises:
            KeyError: If tool not found
        """
        return self._tools[tool_id]
