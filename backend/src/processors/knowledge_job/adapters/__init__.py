"""
Infrastructure Adapters Package.

This package contains adapters that connect domain services
to specific infrastructure implementations (LiteLLM, Milvus, etc.).
"""

from .litellm_adapter import EmbeddingAdapter, LiteLLMEmbeddingAdapter

__all__ = [
    "EmbeddingAdapter",
    "LiteLLMEmbeddingAdapter",
]
