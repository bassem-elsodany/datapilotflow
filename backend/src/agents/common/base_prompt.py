"""
Base prompt class for all agents.

This module defines the base Prompt class used by all prompt modules
with Langfuse versioning and management support.
"""

import json
from typing import Any, Dict, List, Literal, Optional

from langfuse import Langfuse
from loguru import logger

from src.config import settings
from src.infrastructure.langfuse_utils import get_langfuse_client


def _sanitize_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitize config to ensure it's JSON serializable for Langfuse.

    Args:
        config: Raw config dictionary that may contain complex types

    Returns:
        Sanitized config with all values converted to JSON-serializable types
    """
    if not config:
        return {}

    sanitized = {}
    for key, value in config.items():
        try:
            # Try to JSON serialize the value to test if it's serializable
            json.dumps({key: value})
            sanitized[key] = value
        except (TypeError, ValueError):
            # If not serializable, convert to string representation
            try:
                sanitized[key] = str(value)
            except Exception as e:
                logger.debug(f"Failed to sanitize config key '{key}': {e}")
                sanitized[key] = f"<unserializable: {type(value).__name__}>"

    return sanitized


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
        prompt_id: Langfuse prompt ID for versioning
        langfuse: Langfuse client instance
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
        self.config = _sanitize_config(config)
        self.prompt_id: Optional[str] = None
        self.langfuse: Optional[Langfuse] = None
        self._langfuse_prompt: Any = None

        # Check if agent tracing is enabled in configuration
        if settings.AGENT_TRACING_ENABLED:
            logger.debug(
                f"Agent tracing enabled: Prompt '{name}' versioned with Langfuse"
            )
            try:
                # Use singleton Langfuse client (initialized at app startup)
                self.langfuse = get_langfuse_client()
                if self.langfuse:
                    try:
                        # Create the prompt in Langfuse
                        self._langfuse_prompt = self.langfuse.create_prompt(
                            name=name,
                            prompt=prompt,
                            type=self.prompt_type,
                            labels=self.labels,
                            config=self.config,
                        )
                        logger.debug(
                            f"Prompt '{name}' created in Langfuse successfully"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to create prompt '{name}' in Langfuse: {e}. "
                            f"Falling back to local prompt."
                        )
                else:
                    logger.warning(
                        f"Langfuse not configured for prompt '{name}'. Falling back to local prompt."
                    )
            except Exception as e:
                logger.warning(
                    f"Can't use Langfuse to manage the prompt '{name}' (probably due to missing or invalid credentials). "
                    f"Falling back to local prompt. The prompt is not versioned, but it's still usable. Error: {e}"
                )
                self.langfuse = None
        else:
            logger.debug(f"Prompt '{name}' initialized without Langfuse tracking")

    @property
    def prompt(self) -> str:
        """Get the prompt text content."""
        return self.prompt_text

    def update_prompt(
        self,
        new_prompt: str,
        labels: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update the prompt content and optionally labels/config.

        Args:
            new_prompt: New prompt text content
            labels: Optional new labels list
            config: Optional new configuration dictionary

        Returns:
            bool: True if update successful, False otherwise
        """
        if self.langfuse and settings.AGENT_TRACING_ENABLED and self._langfuse_prompt:
            try:
                # Create a new prompt version
                prompt_type: Literal["text"] = "text"
                sanitized_config = _sanitize_config(config or self.config)
                new_langfuse_prompt = self.langfuse.create_prompt(
                    name=self.name,
                    prompt=new_prompt,
                    type=prompt_type,
                    labels=labels or self.labels,
                    config=sanitized_config,
                )
                self._langfuse_prompt = new_langfuse_prompt
                self.prompt_text = new_prompt
                if labels:
                    self.labels = labels
                if config:
                    self.config = _sanitize_config(config)
                logger.debug(f"Prompt '{self.name}' updated successfully in Langfuse")
                return True
            except Exception as e:
                logger.error(f"Failed to update prompt '{self.name}' in Langfuse: {e}")
                return False
        else:
            # Local update only
            self.prompt_text = new_prompt
            if labels:
                self.labels = labels
            if config:
                self.config = config
            logger.debug(f"Prompt '{self.name}' updated locally")
            return True

    def promote_to_production(self) -> bool:
        """
        Promote the prompt to production by adding the 'production' label.

        Returns:
            bool: True if promotion successful, False otherwise
        """
        if self.langfuse and settings.AGENT_TRACING_ENABLED and self._langfuse_prompt:
            try:
                # Update labels to include production
                if "production" not in self.labels:
                    self.labels.append("production")
                    # Create a new version with production label
                    prompt_type: Literal["text"] = "text"
                    new_langfuse_prompt = self.langfuse.create_prompt(
                        name=self.name,
                        prompt=self.prompt_text,
                        type=prompt_type,
                        labels=self.labels,
                        config=self.config,
                    )
                    self._langfuse_prompt = new_langfuse_prompt
                    logger.debug(f"Prompt '{self.name}' promoted to production")
                    return True
            except Exception as e:
                logger.error(
                    f"Failed to promote prompt '{self.name}' to production: {e}"
                )
                return False
        return False

    def track_usage(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Track prompt usage with additional metadata.

        Args:
            metadata: Optional additional metadata to track

        Note:
            This method logs usage information. For actual Langfuse tracing,
            use Langfuse's trace/span decorators on the calling function.
        """
        if self.langfuse and settings.AGENT_TRACING_ENABLED:
            usage_info = {
                "prompt_name": self.name,
                "prompt_length": len(self.prompt_text),
                "prompt_type": self.prompt_type,
                "labels": self.labels,
                **(metadata if metadata else {}),
            }
            logger.debug(f"Prompt usage tracked: {usage_info}")
        else:
            logger.debug(f"Prompt '{self.name}' used (tracing disabled)")

    def get_version_info(self) -> Dict[str, Any]:
        """
        Get prompt version information.

        Returns:
            Dict containing prompt version details
        """
        return {
            "name": self.name,
            "prompt_id": self.prompt_id,
            "type": self.prompt_type,
            "labels": self.labels,
            "config": self.config,
            "langfuse_enabled": self.langfuse is not None,
            "length": len(self.prompt_text),
        }

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return f"Prompt(name='{self.name}', id='{self.prompt_id}', type='{self.prompt_type}', langfuse_enabled={self.langfuse is not None})"
