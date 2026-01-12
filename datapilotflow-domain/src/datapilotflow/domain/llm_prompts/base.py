"""
Base Prompt Class

This module defines the base Prompt class used by all prompt modules
in the LLM prompts subpackage.
"""

from typing import Any, Dict, List, Optional


class Prompt:
    """
    Simple wrapper class for managing prompts.

    This class provides a unified interface for prompt management.

    Attributes:
        name: Name identifier for the prompt
        prompt: The actual prompt text content
        labels: Optional labels for categorization
        config: Optional configuration dictionary
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        agent_tracing_enabled: bool = False,
        labels: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a Prompt instance.

        Args:
            name: Name identifier for the prompt
            prompt: The actual prompt text content
            agent_tracing_enabled: Deprecated parameter, kept for backward compatibility
            labels: Optional labels for categorization
            config: Optional configuration dictionary
        """
        self.name = name
        self._prompt = prompt
        self.labels = labels or []
        self.config = config or {}
        # agent_tracing_enabled is ignored - kept for backward compatibility

    @property
    def prompt(self) -> str:
        """Get the prompt text content."""
        return self._prompt

    def __str__(self) -> str:
        """Return string representation of the prompt."""
        return self.prompt

    def __repr__(self) -> str:
        """Return representation of the prompt."""
        return f"Prompt(name='{self.name}')"
