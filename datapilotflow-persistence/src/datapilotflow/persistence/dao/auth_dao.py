"""
Authentication Data Access Object.

This module provides database operations specifically for authentication
including user verification, session management, and auth-related queries.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pymongo import ASCENDING
from bson import ObjectId
from passlib.hash import bcrypt
from loguru import logger

from datapilotflow.domain.user import User
from datapilotflow.persistence.mongo.client import MongoClientWrapper
from datapilotflow.domain.config import settings


class AuthDAO(MongoClientWrapper[User]):
    """Data Access Object for authentication operations."""
    
    def __init__(self):
        super().__init__(
            model=User,
            collection_name=getattr(settings, "MONGO_USERS_COLLECTION", "users")
        )
        # Ensure indexes for auth operations
        self.collection.create_index([("username", ASCENDING)], unique=True)
        self.collection.create_index([("email", ASCENDING)], unique=True)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username for authentication."""
        try:
            doc = self.collection.find_one({"username": username})
            if doc:
                return self._convert_doc_to_user(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email for authentication."""
        try:
            doc = self.collection.find_one({"email": email})
            if doc:
                return self._convert_doc_to_user(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def verify_user_credentials(self, username: str, password: str) -> Optional[User]:
        """Verify user credentials and return user if valid."""
        try:
            # Truncate password if it's too long (bcrypt limit is 72 bytes)
            if len(password.encode('utf-8')) > 72:
                password = password[:72]
                logger.warning(f"Password truncated to 72 bytes for user {username}")
            
            user = self.get_user_by_username(username)
            if user and bcrypt.verify(password, user.hashed_password):
                # Update last login
                self._update_last_login(user.id)
                return user
            return None
        except Exception as e:
            logger.error(f"Error verifying credentials for {username}: {e}")
            return None
    
    def create_user(self, username: str, email: str, password: str, name: str, role_ids: list = None) -> Optional[User]:
        """Create a new user account."""
        try:
            # Check if user already exists
            if self.get_user_by_username(username):
                logger.warning(f"Username {username} already exists")
                return None
            
            if self.get_user_by_email(email):
                logger.warning(f"Email {email} already exists")
                return None
            
            # Hash password (truncate if too long)
            if len(password.encode('utf-8')) > 72:
                password = password[:72]
                logger.warning(f"Password truncated to 72 bytes for new user {username}")
            hashed_password = bcrypt.hash(password)
            
            # Create user document
            user_data = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "name": name,
                "role_ids": role_ids or [],
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "is_active": True,
                "profile_data": {}
            }
            
            # Insert into database
            result = self.collection.insert_one(user_data)
            
            if result.inserted_id:
                # Return the created user
                user_data["_id"] = str(result.inserted_id)
                return User.model_validate(user_data)
            
            return None
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return None
    
    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            result = self.collection.update_one(
                {"_id": user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            # Prevent updating sensitive fields
            sensitive_fields = ["hashed_password", "username", "email"]
            for field in sensitive_fields:
                updates.pop(field, None)
            
            result = self.collection.update_one(
                {"_id": user_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return False
    
    def change_password(self, user_id: str, new_password: str) -> bool:
        """Change user password."""
        try:
            hashed_password = bcrypt.hash(new_password)
            result = self.collection.update_one(
                {"_id": user_id},
                {"$set": {"hashed_password": hashed_password}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user account."""
        try:
            result = self.collection.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def _convert_doc_to_user(self, doc: Dict[str, Any]) -> User:
        """Convert MongoDB document to User model."""
        try:
            # Convert ObjectId to string
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc[key] = str(value)
            
            # Handle _id field - keep it as _id for the model alias
            if "_id" in doc:
                # The model expects _id due to the alias
                pass
            
            return User.model_validate(doc)
        except Exception as e:
            logger.error(f"Error converting document to User: {e}")
            raise
    
    def _update_last_login(self, user_id: str) -> None:
        """Internal method to update last login."""
        try:
            self.collection.update_one(
                {"_id": user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            doc = self.collection.find_one({"_id": user_id})
            if doc:
                return self._convert_doc_to_user(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        try:
            docs = self.collection.find().skip(skip).limit(limit)
            users = []
            for doc in docs:
                user = self._convert_doc_to_user(doc)
                if user:
                    users.append(user)
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def get_users_count(self) -> int:
        """Get total number of users."""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
