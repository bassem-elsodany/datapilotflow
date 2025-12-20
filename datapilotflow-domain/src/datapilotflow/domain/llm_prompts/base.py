"""
Base Prompt Class

This module defines the base Prompt class used by all prompt modules
in the LLM prompts subpackage.
"""

import opik
from loguru import logger

# Note: settings removed from domain - it's only for local prompt fallback


class Prompt:
    """
    Wrapper class for managing prompts with Opik versioning.

    This class provides a unified interface for prompt management, supporting
    both Opik versioned prompts and local fallback prompts.

    Attributes:
        name: Name identifier for the prompt
        prompt: The actual prompt text content
    """

    def __init__(self, name: str, prompt: str, agent_tracing_enabled: bool = False) -> None:
        self.name = name

        try:
            if agent_tracing_enabled:
                import opik

                self.__prompt = opik.Prompt(name=name, prompt=prompt)
            else:
                self.__prompt = prompt
        except Exception:
            logger.warning(
                "Can't use Opik to version the prompt (probably due to missing or invalid credentials). Falling back to local prompt. The prompt is not versioned, but it's still usable."
            )

            self.__prompt = prompt
        else:
            self.__prompt = prompt

    @property
    def prompt(self) -> str:
        if (
            hasattr(opik, "Prompt")
            and isinstance(self.__prompt, opik.Prompt)
        ):
            return self.__prompt.prompt
        else:
            return str(self.__prompt)

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()
