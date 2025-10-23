"""
User domain model for SkillPilot.

This module defines the User model used for managing user accounts,
authentication, and role-based access control in the SkillPilot system.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Set
from datetime import datetime

# Note: We no longer import UserRole enum directly since roles are now managed separately
# from .roles import UserRole, UserRoles


class User(BaseModel):
    """
    Model representing a user in the SkillPilot system.
    
    This model handles user authentication and profile information.
    Role-based access control is now handled through separate role assignments
    for better scalability and maintainability.
    
    Attributes:
        id: Unique identifier for the user
        username: Unique username for login
        email: Unique email address
        hashed_password: Securely hashed password using bcrypt
        name: Full name of the user
        role_ids: List of role IDs (references to roles collection)
        created_at: Timestamp when the account was created
        last_login: Timestamp of the last login
        is_active: Whether the user account is active
        profile_data: Additional profile information
    """
    id: Optional[str] = Field(alias="_id", default=None)
    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    hashed_password: str = Field(..., description="Hashed password (bcrypt)")
    name: str = Field(..., description="Full name")
    role_ids: List[str] = Field(
        default_factory=list,
        description="List of role IDs (references to roles collection)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True, description="Whether the user account is active")
    profile_data: Optional[dict] = Field(default_factory=dict, description="Additional profile information")

    model_config = ConfigDict(
        allow_population_by_field_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    def has_role_id(self, role_id: str) -> bool:
        """Check if user has a specific role ID."""
        return role_id in self.role_ids
    
    def add_role_id(self, role_id: str) -> None:
        """Add a role ID to the user."""
        if role_id not in self.role_ids:
            self.role_ids.append(role_id)
    
    def remove_role_id(self, role_id: str) -> None:
        """Remove a role ID from the user."""
        if role_id in self.role_ids:
            self.role_ids.remove(role_id)
    
    def get_role_ids(self) -> List[str]:
        """Get all role IDs for this user."""
        return self.role_ids.copy()
    
    def clear_roles(self) -> None:
        """Clear all role assignments."""
        self.role_ids.clear()
    
    # Note: Permission checking methods now require role service injection
    # These methods will be implemented in the UserService class
    
    def is_active_user(self) -> bool:
        """Check if user account is active."""
        return self.is_active
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def get_profile_value(self, key: str, default=None):
        """Get a value from profile_data."""
        return self.profile_data.get(key, default) if self.profile_data else default
    
    def set_profile_value(self, key: str, value) -> None:
        """Set a value in profile_data."""
        if self.profile_data is None:
            self.profile_data = {}
        self.profile_data[key] = value
