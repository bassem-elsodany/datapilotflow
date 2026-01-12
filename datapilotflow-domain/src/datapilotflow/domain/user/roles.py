"""
User roles and permissions for DataPilotFlow.

This module defines the role-based access control system for users
in the DataPilotFlow system.
"""

from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    """User roles in the DataPilotFlow system."""
    
    # Core roles
    ADMIN = "admin"
    USER = "user"
    
    # Feature-specific roles
    INTERVIEWER = "interviewer"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    ANALYST = "analyst"
    
    # System roles
    SYSTEM = "system"
    GUEST = "guest"


class UserRoles:
    """Helper class for managing user roles and permissions."""
    
    # Role hierarchies and permissions
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            "permissions": [
                "user:manage",
                "user:read",
                "interview:manage",
                "interview:read",
                "knowledge:manage",
                "knowledge:read",
                "analytics:manage",
                "analytics:read",
                "system:manage",
                "system:read"
            ],
            "description": "Full system access"
        },
        UserRole.HR_MANAGER: {
            "permissions": [
                "user:read",
                "interview:manage",
                "interview:read",
                "knowledge:read",
                "analytics:read"
            ],
            "description": "HR management access"
        },
        UserRole.INTERVIEWER: {
            "permissions": [
                "interview:manage",
                "interview:read",
                "knowledge:read"
            ],
            "description": "Interview management access"
        },
        UserRole.RECRUITER: {
            "permissions": [
                "interview:read",
                "knowledge:read",
                "analytics:read"
            ],
            "description": "Recruitment access"
        },
        UserRole.ANALYST: {
            "permissions": [
                "interview:read",
                "knowledge:read",
                "analytics:manage",
                "analytics:read"
            ],
            "description": "Analytics access"
        },
        UserRole.USER: {
            "permissions": [
                "interview:read",
                "knowledge:read"
            ],
            "description": "Basic user access"
        },
        UserRole.GUEST: {
            "permissions": [
                "knowledge:read"
            ],
            "description": "Read-only access"
        }
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
        user_permissions = cls.get_permissions(roles)
        return permission in user_permissions
    
    @classmethod
    def get_role_description(cls, role: UserRole) -> str:
        """Get description for a role."""
        return cls.ROLE_PERMISSIONS.get(role, {}).get("description", "Unknown role")
    
    @classmethod
    def get_default_roles(cls) -> List[UserRole]:
        """Get default roles for new users."""
        return [UserRole.USER]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Check if a role string is valid."""
        try:
            UserRole(role)
            return True
        except ValueError:
            return False
