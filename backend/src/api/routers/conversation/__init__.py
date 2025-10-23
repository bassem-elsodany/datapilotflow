"""
Conversation Router Package

This package contains conversation-related endpoints including
REST endpoints for chat and memory management, and WebSocket endpoints
for real-time communication and knowledge search.
"""

from .conversation_router import router as conversation_router
from .conversation_websocket_router import router as conversation_websocket_router

__all__ = [
    "conversation_router",
    "conversation_websocket_router"
]
