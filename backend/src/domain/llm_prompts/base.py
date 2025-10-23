"""
Base Prompt Class

This module defines the base Prompt class used by all prompt modules
in the LLM prompts subpackage.
"""


from loguru import logger

from src.config import settings


class Prompt:
    """
    Wrapper class for managing prompts with Opik versioning.
    
    This class provides a unified interface for prompt management, supporting
    both Opik versioned prompts and local fallback prompts.
    
    Attributes:
        name: Name identifier for the prompt
        prompt: The actual prompt text content
    """
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name

        try:
            if settings.OBSERVABILITY_ENABLED:
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
        if settings.OBSERVABILITY_ENABLED and hasattr(opik, 'Prompt') and isinstance(self.__prompt, opik.Prompt):
            return self.__prompt.prompt
        else:
            return self.__prompt

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()
