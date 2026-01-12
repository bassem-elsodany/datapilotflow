"""
Base prompt class for all agents.

This module defines the base Prompt class used by all prompt modules
with Langfuse versioning and management support.
"""

import json
from typing import Any, Dict, List, Literal, Optional

from loguru import logger

from datapilotflow.domain.config import settings


class Prompt:
    """
    Wrapper class for managing prompts with Langfuse versioning and management.

    This class provides a unified interface for prompt management, supporting
    Langfuse prompt versioning, labels, and configuration management.

    Attributes:
        name: Name identifier for the prompt
        prompt_text: The actual prompt text content
        prompt_type: Type of prompt (default: "text")
        labels: Labels for categorizing the prompt
        config: Configuration dictionary for the prompt
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        prompt_type: Literal["text"] = "text",
        labels: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.prompt_text = prompt
        self.prompt_type: Literal["text"] = prompt_type
        self.labels = labels or ["development"]

        # Check if agent tracing is enabled in configuration
        if settings.AGENT_TRACING_ENABLED:
            logger.debug(f"Agent tracing enabled: Prompt '{name}' versioned with Opik")
            try:
                self.__prompt = opik.Prompt(name=name, prompt=prompt)
                logger.debug(f"Prompt '{name}' created in Opik successfully")
            except Exception as e:
                logger.warning(
                    f"Can't use Opik to manage the prompt '{name}' (probably due to missing or invalid credentials). "
                    f"Falling back to local prompt. The prompt is not versioned, but it's still usable. Error: {e}"
                )
                self.opik = None
        else:
            logger.debug(f"Prompt '{name}' initialized without Langfuse tracking")

    @property
    def prompt(self) -> str:
        """Get the prompt text content."""
        return self.prompt_text

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return f"Prompt(name='{self.name}', type='{self.prompt_type}', opik_enabled={self.opik is not None})"
