"""
Notification Data Access Objects (DAOs).

This subpackage contains all MongoDB services for notification-related data access.
"""

from .notification_service import NotificationService

__all__ = [
    # Notification DAO
    "NotificationService"
]
