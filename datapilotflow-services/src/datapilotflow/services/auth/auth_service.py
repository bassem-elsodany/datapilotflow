"""
Authentication Service.

This module provides business logic for authentication operations
including login, registration, token management, and user session handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from loguru import logger

from datapilotflow.config import settings
from datapilotflow.domain.user import User
from datapilotflow.services.auth.dao.auth_dao import AuthDAO


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.auth_dao = AuthDAO()
        self.secret_key = getattr(settings, "JWT_SECRET_KEY", "supersecret")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24 * 7  # 1 week

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: User's username
            password: User's password

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            user = self.auth_dao.verify_user_credentials(username, password)
            if user:
                logger.info(f"User {username} authenticated successfully")
                return user
            else:
                logger.warning(f"Authentication failed for user {username}")
                return None
        except Exception as e:
            logger.error(f"Error during authentication for {username}: {e}")
            return None

    def register_user(
        self, username: str, email: str, password: str, name: str, roles: list = None
    ) -> Optional[User]:
        """
        Register a new user account.

        Args:
            username: User's username
            email: User's email
            password: User's password
            name: User's full name
            roles: List of user roles

        Returns:
            User object if registration successful, None otherwise
        """
        try:
            # Validate input
            if not username or not email or not password or not name:
                logger.error("Missing required fields for user registration")
                return None

            # Create user
            user = self.auth_dao.create_user(username, email, password, name, roles)
            if user:
                logger.info(f"User {username} registered successfully")
                return user
            else:
                logger.error(f"Failed to register user {username}")
                return None
        except Exception as e:
            logger.error(f"Error during user registration for {username}: {e}")
            return None

    def create_access_token(
        self, user: User, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token for user.

        Args:
            user: User object
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        try:
            # Get user roles through the role system
            from datapilotflow.services.users.user_service import UserService

            user_service = UserService()

            # Get role names for the user
            role_names = user_service.get_user_role_names(user.id)

            to_encode = {
                "sub": user.username,
                "user_id": user.id,
                "roles": role_names,  # Use role names from the role system
            }

            expire = datetime.now(timezone.utc) + (
                expires_delta or timedelta(minutes=self.access_token_expire_minutes)
            )
            to_encode.update({"exp": expire})

            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Access token created for user {user.username}")
            return token
        except Exception as e:
            logger.error(f"Error creating access token for user {user.username}: {e}")
            raise

    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate JWT access token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.PyJWTError as e:
            logger.error(f"Invalid token format: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {e}")
            return None

    def validate_token_and_get_user(self, token: str) -> Optional[User]:
        """
        Validate JWT token and return the associated user.

        Args:
            token: JWT token string

        Returns:
            User object if token valid, None otherwise
        """
        try:
            payload = self.decode_access_token(token)
            if not payload:
                logger.error("Token decode failed - no payload returned")
                return None

            username = payload.get("sub")
            if not username:
                logger.error("No username in token payload")
                return None

            user = self.auth_dao.get_user_by_username(username)
            if not user:
                logger.error(f"User not found for username: {username}")
                return None

            return user
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: User's username

        Returns:
            User object if found, None otherwise
        """
        try:
            return self.auth_dao.get_user_by_username(username)
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User's email

        Returns:
            User object if found, None otherwise
        """
        try:
            return self.auth_dao.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user profile information.

        Args:
            user_id: User's ID
            updates: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            success = self.auth_dao.update_user_profile(user_id, updates)
            if success:
                logger.info(f"User profile updated successfully for user {user_id}")
            else:
                logger.warning(f"Failed to update user profile for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return False

    def change_user_password(self, user_id: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User's ID
            new_password: New password

        Returns:
            True if password change successful, False otherwise
        """
        try:
            success = self.auth_dao.change_password(user_id, new_password)
            if success:
                logger.info(f"Password changed successfully for user {user_id}")
            else:
                logger.warning(f"Failed to change password for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user account.

        Args:
            user_id: User's ID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            success = self.auth_dao.delete_user(user_id)
            if success:
                logger.info(f"User account deleted successfully for user {user_id}")
            else:
                logger.warning(f"Failed to delete user account for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def check_username_exists(self, username: str) -> bool:
        """
        Check if username already exists.

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        try:
            user = self.auth_dao.get_user_by_username(username)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking username existence for {username}: {e}")
            return False

    def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if email exists, False otherwise
        """
        try:
            user = self.auth_dao.get_user_by_email(email)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking email existence for {email}: {e}")
            return False

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User's ID

        Returns:
            User object if found, None otherwise
        """
        try:
            return self.auth_dao.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of User objects
        """
        try:
            return self.auth_dao.get_all_users(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def get_users_count(self) -> int:
        """
        Get total number of users.

        Returns:
            Total number of users
        """
        try:
            return self.auth_dao.get_users_count()
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0

    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a JWT token (add to blacklist).

        Args:
            token: JWT token to invalidate

        Returns:
            True if token invalidated successfully, False otherwise
        """
        try:
            # TODO: Implement token blacklist mechanism
            # For now, just log the invalidation
            logger.info(f"Token invalidated: {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"Error invalidating token: {e}")
            return False

    def create_password_reset_token(self, user: User) -> Optional[str]:
        """
        Create a password reset token for user.

        Args:
            user: User object

        Returns:
            Reset token if created successfully, None otherwise
        """
        try:
            # TODO: Implement password reset token creation
            # For now, return a placeholder
            logger.info(f"Password reset token created for user {user.username}")
            return "reset_token_placeholder"
        except Exception as e:
            logger.error(
                f"Error creating password reset token for user {user.username}: {e}"
            )
            return None

    def validate_password_reset_token(self, token: str) -> Optional[User]:
        """
        Validate a password reset token and return associated user.

        Args:
            token: Password reset token

        Returns:
            User object if token is valid, None otherwise
        """
        try:
            # TODO: Implement password reset token validation
            # For now, return None
            logger.warning(
                f"Password reset token validation not implemented: {token[:20]}..."
            )
            return None
        except Exception as e:
            logger.error(f"Error validating password reset token: {e}")
            return None

    def invalidate_password_reset_token(self, token: str) -> bool:
        """
        Invalidate a password reset token.

        Args:
            token: Password reset token to invalidate

        Returns:
            True if token invalidated successfully, False otherwise
        """
        try:
            # TODO: Implement password reset token invalidation
            logger.info(f"Password reset token invalidated: {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"Error invalidating password reset token: {e}")
            return False
