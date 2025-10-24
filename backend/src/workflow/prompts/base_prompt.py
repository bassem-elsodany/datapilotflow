"""
Base prompt class for DataPilotFlow workflow prompts.

This module provides a base class for all prompts with optional Opik integration
for prompt versioning and management.
"""

from typing import Any, Dict, List

import opik
from loguru import logger

from src.config import settings


class Prompt:
    def __init__(
        self,
        name: str,
        prompt: str,
        tags: List[str] = [],
        metadata: Dict[str, Any] = {},
    ) -> None:
        self.name = name

        # Check if agent tracing is enabled in configuration
        if settings.AGENT_TRACING_ENABLED:
            logger.debug(f"Agent tracing enabled: Prompt '{name}' versioned with Opik")
            try:
                self.__prompt = opik.Prompt(name=name, prompt=prompt)
                logger.debug(
                    f"Agent tracing enabled: Prompt '{name}' versioned with Opik"
                )
            except Exception as e:
                logger.error(
                    f"Agent tracing enabled but Opik failed for prompt '{name}': {e}. "
                    "Falling back to local prompt."
                )
                self.__prompt = prompt
        else:
            logger.debug(f"agent tracing disabled: Using local prompt '{name}'")
            self.__prompt = prompt

    @property
    def prompt(self) -> str:
        if isinstance(self.__prompt, opik.Prompt):
            return self.__prompt.prompt
        else:
            return self.__prompt

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()
