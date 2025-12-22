"""
Model Provider API router module.
"""

from .litellm_router import router as litellm_router
from .model_provider_router import router

__all__ = ["router", "litellm_router"]
