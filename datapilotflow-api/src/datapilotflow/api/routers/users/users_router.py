"""
User Management Router.

This module contains endpoints for user management operations
including user profile management, user CRUD operations, and user administration.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, EmailStr

from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.domain.config import settings
from datapilotflow.domain.user import User
from datapilotflow.services.auth.auth_service import AuthService
from datapilotflow.services.model_provider.model_provider_initialization_service import (
    ModelProviderInitializationService,
)
from datapilotflow.services.users.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])
auth_service = AuthService()
user_service = UserService()
model_provider_init_service = ModelProviderInitializationService()


class UserProfile(BaseModel):
    id: Optional[str]
    username: str
    email: str
    name: str
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool

    @classmethod
    def from_user(cls, user: User):
        """Create UserProfile from User object."""
        # Get user roles through the role system
        role_names = user_service.get_user_role_names(user.id)

        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            roles=role_names,  # Use role names from the role system
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
        )


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    role_ids: Optional[List[str]] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    users: List[UserProfile]
    total_count: int


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile information.
    """
    return UserProfile.from_user(current_user)


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    profile_update: UpdateProfileRequest, current_user: User = Depends(get_current_user)
):
    """
    Update current user profile information.
    """
    try:
        updates = {}
        if profile_update.name is not None:
            updates["name"] = profile_update.name
        if profile_update.email is not None:
            # Check if email is already taken by another user
            existing_user = auth_service.get_user_by_email(profile_update.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(status_code=400, detail="Email already exists")
            updates["email"] = profile_update.email

        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        success = auth_service.update_user_profile(current_user.id, updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        # Get updated user
        updated_user = auth_service.get_user_by_username(current_user.username)
        if not updated_user:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve updated profile"
            )

        return UserProfile.from_user(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Change current user password.
    """
    try:
        # Verify current password
        user = auth_service.authenticate_user(
            current_user.username, password_change.current_password
        )
        if not user:
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Change password
        success = auth_service.change_user_password(
            current_user.id, password_change.new_password
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to change password")

        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(current_user: User = Depends(get_current_user)):
    """
    Delete current user account.
    """
    try:
        success = auth_service.delete_user(current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account")

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Admin-only endpoints
@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)
):
    """
    List all users (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        users = auth_service.get_all_users(skip=skip, limit=limit)
        user_profiles = [UserProfile.from_user(user) for user in users]

        total_count = auth_service.get_users_count()

        return UserListResponse(users=user_profiles, total_count=total_count)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest, current_user: User = Depends(get_current_user)
):
    """
    Create a new user (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Check if username already exists
        if auth_service.check_username_exists(user_data.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        # Check if email already exists
        if auth_service.check_email_exists(user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user with role IDs
        user = auth_service.auth_dao.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            role_ids=user_data.role_ids or [],
        )
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")

        # Initialize predefined model providers for the new user
        logger.info(
            f"Initializing model providers for new user: {user.username} (ID: {user.id})"
        )
        try:
            provider_init_success = (
                await model_provider_init_service.initialize_predefined_model_providers(
                    user.id
                )
            )
            if provider_init_success:
                logger.info(
                    f"✅ Model providers initialized successfully for user: {user.username}"
                )
            else:
                logger.warning(
                    f"⚠️ Failed to initialize model providers for user: {user.username}"
                )
        except Exception as e:
            logger.error(
                f"❌ Error initializing model providers for user {user.username}: {e}"
            )
            # Don't fail user creation if provider initialization fails

        return UserProfile.from_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Get user by ID (admin only).
    """
    try:
        # Check if user has admin permissions or is requesting their own profile
        if (
            not user_service.user_can_manage_users(current_user.id)
            and current_user.id != user_id
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserProfile.from_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str,
    user_update: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update user by ID (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Check if user exists
        existing_user = auth_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prepare updates
        updates = {}
        if user_update.name is not None:
            updates["name"] = user_update.name
        if user_update.email is not None:
            # Check if email is already taken by another user
            email_user = auth_service.get_user_by_email(user_update.email)
            if email_user and email_user.id != user_id:
                raise HTTPException(status_code=400, detail="Email already exists")
            updates["email"] = user_update.email
        if user_update.is_active is not None:
            updates["is_active"] = user_update.is_active
        if user_update.role_ids is not None:
            # Validate role IDs
            for role_id in user_update.role_ids:
                role = user_service.roles_dao.get_role_by_id(role_id)
                if not role:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid role ID: {role_id}"
                    )
            updates["role_ids"] = user_update.role_ids

        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # Update user
        success = auth_service.update_user_profile(user_id, updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user")

        # Get updated user
        updated_user = auth_service.get_user_by_id(user_id)
        if not updated_user:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve updated user"
            )

        return UserProfile.from_user(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete user by ID (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Prevent self-deletion
        if current_user.id == user_id:
            raise HTTPException(
                status_code=400, detail="Cannot delete your own account"
            )

        # Check if user exists
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete user
        success = auth_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete user")

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
