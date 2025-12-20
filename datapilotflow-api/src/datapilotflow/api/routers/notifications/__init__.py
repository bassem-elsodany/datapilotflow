"""
Notification routers.

This subpackage contains all notification-related routers including
REST endpoints and WebSocket endpoints for real-time notifications.
"""

from .notification_router import router as notification_router
from .notification_websocket_router import router as notification_websocket_router

__all__ = [
    "notification_router",
    "notification_websocket_router"
]
