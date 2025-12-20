"""
Authentication Router.

This module contains endpoints for user authentication operations
including login, registration, logout, password reset, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from typing import Optional
from loguru import logger

from datapilotflow.services.auth.auth_service import AuthService
from datapilotflow.domain.user import User
from datapilotflow.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Initialize auth service
auth_service = AuthService()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = auth_service.access_token_expire_minutes * 60

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

class LogoutRequest(BaseModel):
    token: str

# JWT utilities (now using AuthService)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token using AuthService."""
    try:
        # Get user from username
        username = data.get("sub")
        if not username:
            raise ValueError("No username provided for token creation")
        
        user = auth_service.get_user_by_username(username)
        if not user:
            raise ValueError(f"User not found: {username}")
        
        return auth_service.create_access_token(user, expires_delta)
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise

def decode_access_token(token: str):
    """Decode JWT access token using AuthService."""
    logger.debug(f"decode_access_token called with token: {token[:20] if token else 'None'}...")
    try:
        payload = auth_service.decode_access_token(token)
        if payload:
            logger.debug(f"Token decoded successfully, payload: {payload}")
            return payload
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        raise HTTPException(status_code=401, detail="Token validation failed")

def validate_jwt_token(token: str) -> Optional[User]:
    """
    Validate JWT token and return the associated User object.
    Returns None if token is invalid.
    """
    try:
        return auth_service.validate_token_and_get_user(token)
    except Exception as e:
        logger.error(f"Token validation failed with exception: {e}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    
    if not credentials:
        logger.error(f"No credentials provided in request")
        raise HTTPException(status_code=401, detail="Missing authentication credentials")
        
    try:
        user = auth_service.validate_token_and_get_user(credentials.credentials)
        if not user:
            logger.error(f"Token validation failed")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user
    except HTTPException:
        logger.error(f"HTTPException in get_current_user")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """
    Register a new user account and return access token.
    """
    try:
        # Check if username already exists
        if auth_service.check_username_exists(req.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        if auth_service.check_email_exists(req.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create user
        user = auth_service.register_user(req.username, req.email, req.password, req.name)
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Create access token for the new user
        token = auth_service.create_access_token(user)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest):
    """
    Authenticate user and return access token.
    """
    try:
        user = auth_service.authenticate_user(req.username, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        token = auth_service.create_access_token(user)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(req: LogoutRequest, current_user: User = Depends(get_current_user)):
    """
    Logout user and invalidate token.
    """
    try:
        # Invalidate the token (add to blacklist or similar mechanism)
        success = auth_service.invalidate_token(req.token)
        if not success:
            logger.warning(f"Failed to invalidate token for user {current_user.username}")
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/password/reset", status_code=status.HTTP_200_OK)
async def request_password_reset(req: PasswordResetRequest):
    """
    Request password reset for user account.
    """
    try:
        # Check if email exists
        user = auth_service.get_user_by_email(req.email)
        if not user:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate password reset token
        reset_token = auth_service.create_password_reset_token(user)
        if not reset_token:
            raise HTTPException(status_code=500, detail="Failed to create reset token")
        
        # Send password reset email (implement email service)
        # auth_service.send_password_reset_email(user.email, reset_token)
        
        return {"message": "If the email exists, a password reset link has been sent"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/password/reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(req: PasswordResetConfirmRequest):
    """
    Confirm password reset with token and new password.
    """
    try:
        # Validate reset token and get user
        user = auth_service.validate_password_reset_token(req.token)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Change password
        success = auth_service.change_user_password(user.id, req.new_password)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to change password")
        
        # Invalidate the reset token
        auth_service.invalidate_password_reset_token(req.token)
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh access token for current user.
    """
    try:
        token = auth_service.create_access_token(current_user)
        return TokenResponse(access_token=token)
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 