"""
Roles Service.

This module provides business logic for user role and permission management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from loguru import logger
import uuid

from datapilotflow.persistence.dao.roles_dao import RolesDAO
from datapilotflow.domain.user.role_model import Role, RoleType

class RolesService:
    """
    Service for managing user roles and permissions.
    """

    def __init__(self):
        """Initialize the roles service."""
        self.roles_dao = RolesDAO()

    def get_all_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Get all available roles with pagination.

        Args:
            skip: Number of roles to skip
            limit: Maximum number of roles to return

        Returns:
            List of Role objects
        """
        try:
            return self.roles_dao.get_all_roles(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Error getting all roles: {e}")
            return []

    def get_roles_count(self) -> int:
        """
        Get total number of roles.

        Returns:
            Total number of roles
        """
        try:
            return self.roles_dao.get_roles_count()
        except Exception as e:
            logger.error(f"Error getting roles count: {e}")
            return 0

    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """
        Get role by name.

        Args:
            role_name: Name of the role

        Returns:
            Role object if found, None otherwise
        """
        try:
            return self.roles_dao.get_role_by_name(role_name)
        except Exception as e:
            logger.error(f"Error getting role by name {role_name}: {e}")
            return None

    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """
        Get role by ID.

        Args:
            role_id: ID of the role

        Returns:
            Role object if found, None otherwise
        """
        try:
            return self.roles_dao.get_role_by_id(role_id)
        except Exception as e:
            logger.error(f"Error getting role by ID {role_id}: {e}")
            return None

    def role_exists(self, role_name: str) -> bool:
        """
        Check if role exists.

        Args:
            role_name: Name of the role

        Returns:
            True if role exists, False otherwise
        """
        try:
            return self.roles_dao.role_exists(role_name)
        except Exception as e:
            logger.error(f"Error checking if role exists {role_name}: {e}")
            return False

    def create_role(self, name: str, description: Optional[str] = None, permissions: Optional[List[str]] = None, created_by: str = None) -> Optional[Role]:
        """
        Create a new role.

        Args:
            name: Role name
            description: Role description
            permissions: List of permissions for the role
            created_by: User ID who created this role

        Returns:
            Created Role object if successful, None otherwise
        """
        try:
            # Validate role name
            if not name or len(name.strip()) == 0:
                logger.error("Role name is required")
                return None

            # Check if role already exists
            if self.role_exists(name):
                logger.error(f"Role {name} already exists")
                return None

            # Create role object
            role = Role(
                name=name.strip(),
                display_name=name.strip().title(),
                description=description,
                permissions=permissions or [],
                role_type=RoleType.CUSTOM,
                is_system_role=False,
                created_by=created_by
            )

            # Save to database
            created_role = self.roles_dao.create_role(role)
            if created_role:
                logger.info(f"Role {name} created successfully")
                return created_role
            else:
                logger.error(f"Failed to create role {name}")
                return None

        except Exception as e:
            logger.error(f"Error creating role {name}: {e}")
            return None

    def update_role(self, role_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a role.

        Args:
            role_id: ID of the role to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if role exists
            role = self.get_role_by_id(role_id)
            if not role:
                logger.error(f"Role {role_id} not found")
                return False

            # Prevent updating system roles
            if role.is_system_role:
                logger.error(f"Cannot update system role {role.name}")
                return False

            # Update role
            success = self.roles_dao.update_role(role_id, updates)
            if success:
                logger.info(f"Role {role_id} updated successfully")
            return success

        except Exception as e:
            logger.error(f"Error updating role {role_id}: {e}")
            return False

    def delete_role(self, role_id: str) -> bool:
        """
        Delete a role.

        Args:
            role_id: ID of the role to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if role exists
            role = self.get_role_by_id(role_id)
            if not role:
                logger.error(f"Role {role_id} not found")
                return False

            # Prevent deleting system roles
            if role.is_system_role:
                logger.error(f"Cannot delete system role {role.name}")
                return False

            # Delete role
            success = self.roles_dao.delete_role(role_id)
            if success:
                logger.info(f"Role {role_id} deleted successfully")
            return success

        except Exception as e:
            logger.error(f"Error deleting role {role_id}: {e}")
            return False

    def get_all_permissions(self) -> List[Dict[str, str]]:
        """
        Get all available permissions.

        Returns:
            List of permission dictionaries
        """
        try:
            # Define available permissions
            permissions = [
                {"name": "user:manage", "description": "Manage users", "category": "user_management"},
                {"name": "user:read", "description": "Read user information", "category": "user_management"},
                {"name": "interview:manage", "description": "Manage interviews", "category": "interview_management"},
                {"name": "interview:read", "description": "Read interview information", "category": "interview_management"},
                {"name": "knowledge:manage", "description": "Manage knowledge base", "category": "knowledge_management"},
                {"name": "knowledge:read", "description": "Read knowledge base", "category": "knowledge_management"},
                {"name": "analytics:manage", "description": "Manage analytics", "category": "analytics"},
                {"name": "analytics:read", "description": "Read analytics", "category": "analytics"},
                {"name": "system:manage", "description": "Manage system settings", "category": "system"},
                {"name": "system:read", "description": "Read system information", "category": "system"}
            ]
            return permissions
        except Exception as e:
            logger.error(f"Error getting all permissions: {e}")
            return []

    def get_all_permission_names(self) -> List[str]:
        """
        Get all available permission names.

        Returns:
            List of permission names
        """
        try:
            permissions = self.get_all_permissions()
            return [perm["name"] for perm in permissions]
        except Exception as e:
            logger.error(f"Error getting permission names: {e}")
            return []

    def get_permissions_by_category(self, category: str) -> List[Dict[str, str]]:
        """
        Get permissions by category.

        Args:
            category: Permission category

        Returns:
            List of permission dictionaries for the category
        """
        try:
            all_permissions = self.get_all_permissions()
            return [perm for perm in all_permissions if perm["category"] == category]
        except Exception as e:
            logger.error(f"Error getting permissions by category {category}: {e}")
            return []

    def get_system_roles(self) -> List[Role]:
        """
        Get all system roles.

        Returns:
            List of system Role objects
        """
        try:
            return self.roles_dao.get_system_roles()
        except Exception as e:
            logger.error(f"Error getting system roles: {e}")
            return []

    def get_custom_roles(self) -> List[Role]:
        """
        Get all custom roles.

        Returns:
            List of custom Role objects
        """
        try:
            return self.roles_dao.get_custom_roles()
        except Exception as e:
            logger.error(f"Error getting custom roles: {e}")
            return []

    def get_active_roles(self) -> List[Role]:
        """
        Get all active roles.

        Returns:
            List of active Role objects
        """
        try:
            return self.roles_dao.get_active_roles()
        except Exception as e:
            logger.error(f"Error getting active roles: {e}")
            return []

    def initialize_system_roles(self) -> bool:
        """
        Initialize system roles if they don't exist.

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.roles_dao.initialize_system_roles()
        except Exception as e:
            logger.error(f"Error initializing system roles: {e}")
            return False
