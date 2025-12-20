"""
User Roles Router.

This module contains endpoints for user role management operations
including role assignment, role creation, and role permissions management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from loguru import logger

from datapilotflow.services.auth.auth_service import AuthService
from datapilotflow.services.users.roles_service import RolesService
from datapilotflow.services.users.user_service import UserService
from datapilotflow.domain.user import User
from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.config import settings

router = APIRouter(prefix="/roles", tags=["User Roles Management"])
auth_service = AuthService()
roles_service = RolesService()
user_service = UserService()

class RoleSchema(BaseModel):
    id: Optional[str]
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str]
    role_type: str
    is_system_role: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CreateRoleRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str]

class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str

class RemoveRoleRequest(BaseModel):
    user_id: str
    role_id: str

class UserRolesResponse(BaseModel):
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]

class RoleListResponse(BaseModel):
    roles: List[RoleSchema]
    total_count: int

class PermissionSchema(BaseModel):
    name: str
    description: str
    category: str

class PermissionsResponse(BaseModel):
    permissions: List[PermissionSchema]
    total_count: int

@router.get("", response_model=RoleListResponse)
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    List all available roles (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        roles = roles_service.get_all_roles(skip=skip, limit=limit)
        role_schemas = []
        
        for role in roles:
            role_schema = RoleSchema(
                id=role.id,
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                permissions=role.permissions,
                role_type=role.role_type.value,
                is_system_role=role.is_system_role,
                is_active=role.is_active,
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            role_schemas.append(role_schema)
        
        total_count = roles_service.get_roles_count()
        
        return RoleListResponse(roles=role_schemas, total_count=total_count)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List roles error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions", response_model=PermissionsResponse)
async def list_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    List all available permissions (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        permissions = roles_service.get_all_permissions()
        permission_schemas = []
        
        for perm in permissions:
            permission_schema = PermissionSchema(
                name=perm["name"],
                description=perm["description"],
                category=perm["category"]
            )
            permission_schemas.append(permission_schema)
        
        return PermissionsResponse(permissions=permission_schemas, total_count=len(permission_schemas))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List permissions error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: CreateRoleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new role (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Validate role name
        if not role_data.name or len(role_data.name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Role name is required")
        
        # Check if role already exists
        if roles_service.role_exists(role_data.name):
            raise HTTPException(status_code=400, detail="Role already exists")
        
        # Validate permissions
        valid_permissions = roles_service.get_all_permission_names()
        invalid_permissions = [p for p in role_data.permissions if p not in valid_permissions]
        if invalid_permissions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid permissions: {', '.join(invalid_permissions)}"
            )
        
        # Create role
        role = roles_service.create_role(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            created_by=current_user.id
        )
        
        if not role:
            raise HTTPException(status_code=500, detail="Failed to create role")
        
        return RoleSchema(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions,
            role_type=role.role_type.value,
            is_system_role=role.is_system_role,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get role by ID (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        role = roles_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return RoleSchema(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions,
            role_type=role.role_type.value,
            is_system_role=role.is_system_role,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: str,
    role_update: UpdateRoleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update role by ID (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if role exists
        role = roles_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Prepare updates
        updates = {}
        if role_update.name is not None:
            updates["name"] = role_update.name
        if role_update.display_name is not None:
            updates["display_name"] = role_update.display_name
        if role_update.description is not None:
            updates["description"] = role_update.description
        if role_update.permissions is not None:
            # Validate permissions
            valid_permissions = roles_service.get_all_permission_names()
            invalid_permissions = [p for p in role_update.permissions if p not in valid_permissions]
            if invalid_permissions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid permissions: {', '.join(invalid_permissions)}"
                )
            updates["permissions"] = role_update.permissions
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update role
        success = roles_service.update_role(role_id, updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update role")
        
        # Get updated role
        updated_role = roles_service.get_role_by_id(role_id)
        if not updated_role:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated role")
        
        return RoleSchema(
            id=updated_role.id,
            name=updated_role.name,
            display_name=updated_role.display_name,
            description=updated_role.description,
            permissions=updated_role.permissions,
            role_type=updated_role.role_type.value,
            is_system_role=updated_role.is_system_role,
            is_active=updated_role.is_active,
            created_at=updated_role.created_at,
            updated_at=updated_role.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete role by ID (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if role exists
        role = roles_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Delete role
        success = roles_service.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete role")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/assign", response_model=UserRolesResponse)
async def assign_role(
    assign_data: AssignRoleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Assign role to user (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if target user exists
        target_user = auth_service.get_user_by_id(assign_data.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if role exists
        role = roles_service.get_role_by_id(assign_data.role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Assign role
        success = user_service.assign_role_to_user(assign_data.user_id, assign_data.role_id, current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to assign role")
        
        # Get updated user
        updated_user = auth_service.get_user_by_id(assign_data.user_id)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated user")
        
        # Get user roles through the role system
        role_names = user_service.get_user_role_names(updated_user.id)
        permissions = user_service.get_user_permissions(updated_user.id)
        
        return UserRolesResponse(
            user_id=updated_user.id,
            username=updated_user.username,
            roles=role_names,
            permissions=list(permissions)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/remove", response_model=UserRolesResponse)
async def remove_role(
    remove_data: RemoveRoleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Remove role from user (admin only).
    """
    try:
        # Check if user has admin permissions
        if not user_service.user_can_manage_users(current_user.id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if target user exists
        target_user = auth_service.get_user_by_id(remove_data.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if role exists
        role = roles_service.get_role_by_id(remove_data.role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if user has this role
        if not user_service.user_has_role_id(remove_data.user_id, remove_data.role_id):
            raise HTTPException(status_code=400, detail="User does not have this role")
        
        # Prevent removing the last admin role from the last admin user
        if role.name == "admin":
            admin_users = user_service.get_users_with_role("admin")
            if len(admin_users) == 1 and admin_users[0].id == remove_data.user_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot remove the last admin role from the last admin user"
                )
        
        # Remove role
        success = user_service.remove_role_from_user(remove_data.user_id, remove_data.role_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove role")
        
        # Get updated user
        updated_user = auth_service.get_user_by_id(remove_data.user_id)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated user")
        
        # Get user roles through the role system
        role_names = user_service.get_user_role_names(updated_user.id)
        permissions = user_service.get_user_permissions(updated_user.id)
        
        return UserRolesResponse(
            user_id=updated_user.id,
            username=updated_user.username,
            roles=role_names,
            permissions=list(permissions)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove role error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user/{user_id}", response_model=UserRolesResponse)
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get user roles and permissions (admin only).
    """
    try:
        # Check if user has admin permissions or is requesting their own roles
        if not user_service.user_can_manage_users(current_user.id) and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if target user exists
        target_user = auth_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user roles through the role system
        role_names = user_service.get_user_role_names(target_user.id)
        permissions = user_service.get_user_permissions(target_user.id)
        
        return UserRolesResponse(
            user_id=target_user.id,
            username=target_user.username,
            roles=role_names,
            permissions=list(permissions)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user roles error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
