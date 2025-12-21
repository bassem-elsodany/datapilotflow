"""
User Service.

This module provides business logic for user management operations
including role-based access control and user profile management.
"""

from typing import Optional, List, Set, Dict, Any
from datetime import datetime, timezone
from loguru import logger

from datapilotflow.infrastructure.dao.auth import AuthDAO
from datapilotflow.infrastructure.dao.auth import RolesDAO
from datapilotflow.domain.user import User
from datapilotflow.domain.user.role_model import Role, UserRoleAssignment


class UserService:
    """
    Service for managing users and their role assignments.

    This service provides business logic for user management,
    role assignments, and permission checking.
    """

    def __init__(self):
        """Initialize the user service."""
        self.auth_dao = AuthDAO()
        self.roles_dao = RolesDAO()

    # User Management Methods

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.auth_dao.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.auth_dao.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.auth_dao.get_user_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.auth_dao.get_all_users(skip, limit)

    def get_users_count(self) -> int:
        """Get total number of users."""
        return self.auth_dao.get_users_count()

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile information."""
        return self.auth_dao.update_user_profile(user_id, updates)

    def change_user_password(self, user_id: str, new_password: str) -> bool:
        """Change user password."""
        return self.auth_dao.change_password(user_id, new_password)

    def delete_user(self, user_id: str) -> bool:
        """Delete user account."""
        return self.auth_dao.delete_user(user_id)

    # Role Management Methods

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all roles assigned to a user."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return []

            roles = []
            for role_id in user.role_ids:
                role = self.roles_dao.get_role_by_id(role_id)
                if role and role.is_active:
                    roles.append(role)

            return roles
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            return []

    def get_user_role_names(self, user_id: str) -> List[str]:
        """Get role names assigned to a user."""
        roles = self.get_user_roles(user_id)
        return [role.name for role in roles]

    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str = None) -> bool:
        """Assign a role to a user."""
        try:
            # Verify user exists
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Verify role exists and is active
            role = self.roles_dao.get_role_by_id(role_id)
            if not role or not role.is_active:
                logger.error(f"Role {role_id} not found or inactive")
                return False

            # Check if role is already assigned
            if role_id in user.role_ids:
                logger.warning(f"Role {role_id} already assigned to user {user_id}")
                return True  # Already assigned, consider it successful

            # Add role to user
            user.add_role_id(role_id)

            # Update user in database
            success = self.auth_dao.update_user_profile(
                user_id,
                {"role_ids": user.role_ids}
            )

            if success:
                logger.info(f"Role {role_id} assigned to user {user_id}")
                return True
            else:
                logger.error(f"Failed to update user {user_id} with new role")
                return False

        except Exception as e:
            logger.error(f"Error assigning role {role_id} to user {user_id}: {e}")
            return False

    def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a user."""
        try:
            # Verify user exists
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Check if role is assigned
            if role_id not in user.role_ids:
                logger.warning(f"Role {role_id} not assigned to user {user_id}")
                return True  # Not assigned, consider it successful

            # Remove role from user
            user.remove_role_id(role_id)

            # Update user in database
            success = self.auth_dao.update_user_profile(
                user_id,
                {"role_ids": user.role_ids}
            )

            if success:
                logger.info(f"Role {role_id} removed from user {user_id}")
                return True
            else:
                logger.error(f"Failed to update user {user_id} after role removal")
                return False

        except Exception as e:
            logger.error(f"Error removing role {role_id} from user {user_id}: {e}")
            return False

    def set_user_roles(self, user_id: str, role_ids: List[str]) -> bool:
        """Set all roles for a user (replaces existing roles)."""
        try:
            # Verify user exists
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Verify all roles exist and are active
            for role_id in role_ids:
                role = self.roles_dao.get_role_by_id(role_id)
                if not role or not role.is_active:
                    logger.error(f"Role {role_id} not found or inactive")
                    return False

            # Update user roles
            success = self.auth_dao.update_user_profile(
                user_id,
                {"role_ids": role_ids}
            )

            if success:
                logger.info(f"Roles {role_ids} set for user {user_id}")
                return True
            else:
                logger.error(f"Failed to update user {user_id} with new roles")
                return False

        except Exception as e:
            logger.error(f"Error setting roles for user {user_id}: {e}")
            return False

    # Permission Checking Methods

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        try:
            roles = self.get_user_roles(user_id)
            permissions = set()

            for role in roles:
                permissions.update(role.permissions)

            return permissions
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {e}")
            return set()

    def user_has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission."""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def user_has_role(self, user_id: str, role_name: str) -> bool:
        """Check if user has a specific role by name."""
        try:
            roles = self.get_user_roles(user_id)
            return any(role.name == role_name for role in roles)
        except Exception as e:
            logger.error(f"Error checking role {role_name} for user {user_id}: {e}")
            return False

    def user_has_role_id(self, user_id: str, role_id: str) -> bool:
        """Check if user has a specific role by ID."""
        try:
            user = self.get_user_by_id(user_id)
            return user and role_id in user.role_ids
        except Exception as e:
            logger.error(f"Error checking role ID {role_id} for user {user_id}: {e}")
            return False

    # Convenience Methods for Common Permission Checks

    def user_can_manage_users(self, user_id: str) -> bool:
        """Check if user can manage other users."""
        return self.user_has_permission(user_id, "user:manage")

    def user_can_read_users(self, user_id: str) -> bool:
        """Check if user can read user information."""
        return self.user_has_permission(user_id, "user:read")

    def user_can_manage_interviews(self, user_id: str) -> bool:
        """Check if user can manage interviews."""
        return self.user_has_permission(user_id, "interview:manage")

    def user_can_read_interviews(self, user_id: str) -> bool:
        """Check if user can read interviews."""
        return self.user_has_permission(user_id, "interview:read")

    def user_can_manage_knowledge(self, user_id: str) -> bool:
        """Check if user can manage knowledge base."""
        return self.user_has_permission(user_id, "knowledge:manage")

    def user_can_read_knowledge(self, user_id: str) -> bool:
        """Check if user can read knowledge base."""
        return self.user_has_permission(user_id, "knowledge:read")

    def user_is_admin(self, user_id: str) -> bool:
        """Check if user is an admin."""
        return self.user_has_role(user_id, "admin")

    def user_is_interviewer(self, user_id: str) -> bool:
        """Check if user is an interviewer."""
        return self.user_has_role(user_id, "interviewer")

    def get_users_with_role(self, role_name: str) -> List[User]:
        """Get all users with a specific role by name."""
        try:
            # Get all users
            all_users = self.auth_dao.get_all_users()
            users_with_role = []

            for user in all_users:
                if self.user_has_role(user.id, role_name):
                    users_with_role.append(user)

            return users_with_role
        except Exception as e:
            logger.error(f"Error getting users with role {role_name}: {e}")
            return []
