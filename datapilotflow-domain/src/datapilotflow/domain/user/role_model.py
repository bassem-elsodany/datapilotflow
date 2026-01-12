"""
Role domain model for DataPilotFlow.

This module defines the Role model used for managing roles
in a separate collection for better scalability and maintainability.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Set
from datetime import datetime
from enum import Enum


class RoleType(str, Enum):
    """Types of roles in the system."""
    SYSTEM = "system"      # Built-in system roles (admin, user, etc.)
    CUSTOM = "custom"      # Custom roles created by admins
    FEATURE = "feature"    # Feature-specific roles (interviewer, hr_manager, etc.)


class Role(BaseModel):
    """
    Model representing a role in the DataPilotFlow system.
    
    This model is stored in a separate 'roles' collection for better
    scalability and maintainability. Roles can be system-defined or
    custom-created by administrators.
    
    Attributes:
        id: Unique identifier for the role
        name: Unique role name (e.g., 'admin', 'interviewer')
        display_name: Human-readable display name
        description: Role description
        permissions: List of permissions granted by this role
        role_type: Type of role (system, custom, feature)
        is_active: Whether the role is active
        is_system_role: Whether this is a system role (cannot be deleted)
        created_at: Timestamp when the role was created
        updated_at: Timestamp when the role was last updated
        created_by: User ID who created this role (for custom roles)
        metadata: Additional role metadata
    """
    id: Optional[str] = Field(alias="_id", default=None)
    name: str = Field(..., description="Unique role name")
    display_name: str = Field(..., description="Human-readable display name")
    description: Optional[str] = Field(default=None, description="Role description")
    permissions: List[str] = Field(default_factory=list, description="List of permissions")
    role_type: RoleType = Field(default=RoleType.CUSTOM, description="Type of role")
    is_active: bool = Field(default=True, description="Whether the role is active")
    is_system_role: bool = Field(default=False, description="Whether this is a system role")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = Field(default=None, description="User ID who created this role")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional role metadata")

    model_config = ConfigDict(
        allow_population_by_field_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def get_permissions_set(self) -> Set[str]:
        """Get permissions as a set."""
        return set(self.permissions)
    
    def can_be_deleted(self) -> bool:
        """Check if role can be deleted (not a system role)."""
        return not self.is_system_role
    
    def can_be_modified(self) -> bool:
        """Check if role can be modified (not a system role or active)."""
        return not self.is_system_role and self.is_active


class UserRoleAssignment(BaseModel):
    """
    Model representing a user's role assignment.
    
    This model is used to track which roles are assigned to users,
    allowing for better audit trails and role management.
    
    Attributes:
        id: Unique identifier for the assignment
        user_id: ID of the user
        role_id: ID of the role
        assigned_at: When the role was assigned
        assigned_by: User ID who assigned this role
        expires_at: When the role assignment expires (optional)
        is_active: Whether the assignment is active
    """
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str = Field(..., description="ID of the user")
    role_id: str = Field(..., description="ID of the role")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[str] = Field(default=None, description="User ID who assigned this role")
    expires_at: Optional[datetime] = Field(default=None, description="When the role assignment expires")
    is_active: bool = Field(default=True, description="Whether the assignment is active")

    model_config = ConfigDict(
        allow_population_by_field_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    def is_expired(self) -> bool:
        """Check if the role assignment has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the role assignment is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
