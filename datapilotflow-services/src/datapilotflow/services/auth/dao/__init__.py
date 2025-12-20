"""
Authentication Data Access Objects (DAOs).

This subpackage contains all MongoDB services for authentication-related data access
including user authentication, session management, and auth-specific operations.
"""

from .auth_dao import AuthDAO

__all__ = [
    # Auth DAO
    "AuthDAO"
]
