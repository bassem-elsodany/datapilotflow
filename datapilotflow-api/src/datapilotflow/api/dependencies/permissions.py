"""
Permission-based FastAPI dependencies for RBAC enforcement.

Usage:
    from datapilotflow.api.dependencies.permissions import require_permission

    @router.post("/sources")
    def create_source(current_user = Depends(require_permission("knowledge:manage"))):
        ...
"""

from fastapi import Depends, HTTPException, status

from datapilotflow.api.routers.auth.auth_router import get_current_user
from datapilotflow.domain.user import User
from datapilotflow.services.users.user_service import UserService

_user_service = UserService()


def require_permission(permission: str):
    """
    Returns a FastAPI dependency that enforces a single permission.
    Raises HTTP 403 if the authenticated user does not hold that permission.
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if not _user_service.user_has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    # Give the inner function a unique name so FastAPI can distinguish
    # multiple require_permission() calls on the same router.
    _check.__name__ = f"require_{permission.replace(':', '_')}"
    return _check
