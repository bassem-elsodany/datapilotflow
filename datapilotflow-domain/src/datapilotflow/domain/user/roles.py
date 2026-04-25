"""
User roles and permissions for DataPilotFlow RAG platform.
"""

from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    """User roles in the DataPilotFlow RAG platform."""

    # Core system roles
    ADMIN = "admin"

    # Platform-specific roles
    RAG_ENGINEER = "rag_engineer"
    KNOWLEDGE_MANAGER = "knowledge_manager"
    AI_USER = "ai_user"
    VIEWER = "viewer"


class UserRoles:
    """Helper class for managing user roles and permissions."""

    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            "permissions": [
                "user:manage", "user:read",
                "knowledge:manage", "knowledge:read",
                "conversation:manage", "conversation:read",
                "tools:manage", "tools:read",
                "models:manage", "models:read",
                "analytics:manage", "analytics:read",
                "system:manage", "system:read",
            ],
            "description": "Full access to all platform features",
        },
        UserRole.RAG_ENGINEER: {
            "permissions": [
                "knowledge:manage", "knowledge:read",
                "tools:manage", "tools:read",
                "models:manage", "models:read",
                "conversation:read",
                "analytics:read",
                "system:read",
            ],
            "description": "Builds and maintains the RAG pipeline",
        },
        UserRole.KNOWLEDGE_MANAGER: {
            "permissions": [
                "knowledge:manage", "knowledge:read",
                "conversation:read",
                "tools:read",
                "analytics:read",
            ],
            "description": "Manages data ingestion and knowledge sources",
        },
        UserRole.AI_USER: {
            "permissions": [
                "knowledge:read",
                "conversation:manage", "conversation:read",
                "tools:read",
            ],
            "description": "Uses AI conversations to query the knowledge base",
        },
        UserRole.VIEWER: {
            "permissions": [
                "knowledge:read",
                "conversation:read",
                "tools:read",
                "models:read",
                "analytics:read",
            ],
            "description": "Read-only access across the platform",
        },
    }

    @classmethod
    def get_permissions(cls, roles: List[UserRole]) -> Set[str]:
        """Get all permissions for a list of roles."""
        permissions = set()
        for role in roles:
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role]["permissions"])
        return permissions

    @classmethod
    def has_permission(cls, roles: List[UserRole], permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in cls.get_permissions(roles)

    @classmethod
    def get_role_description(cls, role: UserRole) -> str:
        """Get description for a role."""
        return cls.ROLE_PERMISSIONS.get(role, {}).get("description", "Unknown role")

    @classmethod
    def get_default_roles(cls) -> List[UserRole]:
        """Get default roles assigned to new users."""
        return [UserRole.AI_USER]

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Check if a role string is valid."""
        try:
            UserRole(role)
            return True
        except ValueError:
            return False
