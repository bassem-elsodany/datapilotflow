"""
Token Counter Utility.

This module provides utilities for counting tokens in text using tiktoken,
which is used by OpenAI and other LLM providers for tokenization.
"""

from typing import Optional

import tiktoken
from loguru import logger


class TokenCounter:
    """Token counter for estimating token counts in text."""

    # Default encoding for most embedding models
    DEFAULT_ENCODING = "cl100k_base"  # Used by text-embedding-3-* models

    # Model-specific encodings
    MODEL_ENCODINGS = {
        "text-embedding-ada-002": "cl100k_base",
        "text-embedding-3-small": "cl100k_base",
        "text-embedding-3-large": "cl100k_base",
    }

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the token counter.

        Args:
            model_name: Optional model name to use for model-specific encoding
        """
        self.model_name = model_name
        self._encoding = None
        self._initialize_encoding()

    def _initialize_encoding(self) -> None:
        """Initialize the tiktoken encoding."""
        try:
            # Try to get model-specific encoding
            if self.model_name:
                try:
                    self._encoding = tiktoken.encoding_for_model(self.model_name)
                    logger.debug(
                        f"Initialized tiktoken encoding for model: {self.model_name}"
                    )
                    return
                except KeyError:
                    logger.warning(
                        f"Model {self.model_name} not found in tiktoken, using default encoding"
                    )

            # Fall back to default encoding
            self._encoding = tiktoken.get_encoding(self.DEFAULT_ENCODING)
            logger.debug(f"Initialized default tiktoken encoding: {self.DEFAULT_ENCODING}")

        except Exception as e:
            logger.error(f"Failed to initialize tiktoken encoding: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text.

        Args:
            text: The text to count tokens for

        Returns:
            int: Number of tokens in the text
        """
        if not text:
            return 0

        try:
            tokens = self._encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            # Fallback to approximate token count (1 token ≈ 4 characters)
            return len(text) // 4

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using a simple heuristic (faster than counting).

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated number of tokens
        """
        # Approximate: 1 token ≈ 4 characters for English text
        return len(text) // 4

    @staticmethod
    def get_default_max_tokens(model_name: str) -> int:
        """Get the default max input tokens for a model.

        Args:
            model_name: Name of the embedding model

        Returns:
            int: Maximum input tokens for the model
        """
        # Common embedding model limits
        model_limits = {
            "text-embedding-ada-002": 8191,
            "text-embedding-3-small": 8191,
            "text-embedding-3-large": 8191,
            # Add more models as needed
        }

        return model_limits.get(model_name, 512)  # Conservative default
