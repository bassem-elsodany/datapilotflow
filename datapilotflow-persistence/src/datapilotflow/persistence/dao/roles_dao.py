"""
Roles DAO.

This module provides data access operations for user roles and permissions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from pymongo import MongoClient
from bson import ObjectId

from src.infrastructure.mongo.client import MongoClientWrapper
from src.domain.user.role_model import Role, RoleType
from src.config import settings

class RolesDAO(MongoClientWrapper[Role]):
    """
    Data Access Object for user roles and permissions.
    """
    
    def __init__(self):
        """Initialize the roles DAO."""
        super().__init__(
            model=Role,
            collection_name="roles",
            database_name=settings.MONGO_DB_NAME,
            mongodb_uri=settings.MONGO_CONN_STR
        )
    
    def get_all_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Get all roles with pagination.
        
        Args:
            skip: Number of roles to skip
            limit: Maximum number of roles to return
            
        Returns:
            List of Role objects
        """
        try:
            cursor = self.collection.find().skip(skip).limit(limit)
            roles = []
            for doc in cursor:
                role = self._convert_doc_to_role(doc)
                if role:
                    roles.append(role)
            return roles
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
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error getting roles count: {e}")
            return 0
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """
        Get role by ID.
        
        Args:
            role_id: ID of the role
            
        Returns:
            Role object if found, None otherwise
        """
        try:
            doc = self.collection.find_one({"_id": ObjectId(role_id)})
            if doc:
                return self._convert_doc_to_role(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting role by ID {role_id}: {e}")
            return None
    
    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            role_name: Name of the role
            
        Returns:
            Role object if found, None otherwise
        """
        try:
            doc = self.collection.find_one({"name": role_name})
            if doc:
                return self._convert_doc_to_role(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting role by name {role_name}: {e}")
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
            return self.collection.count_documents({"name": role_name}) > 0
        except Exception as e:
            logger.error(f"Error checking if role exists {role_name}: {e}")
            return False
    
    def create_role(self, role: Role) -> Optional[Role]:
        """
        Create a new role.
        
        Args:
            role: Role object to create
            
        Returns:
            Created Role object if successful, None otherwise
        """
        try:
            # Check if role with same name already exists
            if self.role_exists(role.name):
                logger.warning(f"Role with name {role.name} already exists")
                return None
            
            # Prepare role data for insertion
            role_data = role.model_dump(exclude={"id"})
            role_data["created_at"] = datetime.now(timezone.utc)
            role_data["updated_at"] = datetime.now(timezone.utc)
            
            # Insert into database
            result = self.collection.insert_one(role_data)
            
            if result.inserted_id:
                role.id = str(result.inserted_id)
                logger.info(f"Role {role.name} created successfully")
                return role
            
            return None
        except Exception as e:
            logger.error(f"Error creating role {role.name}: {e}")
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
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = self.collection.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": updates}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Role {role_id} updated successfully")
            else:
                logger.warning(f"No changes made to role {role_id}")
            
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
            # Check if role is a system role
            role = self.get_role_by_id(role_id)
            if role and role.is_system_role:
                logger.error(f"Cannot delete system role {role.name}")
                return False
            
            result = self.collection.delete_one({"_id": ObjectId(role_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Role {role_id} deleted successfully")
            else:
                logger.warning(f"Role {role_id} not found for deletion")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting role {role_id}: {e}")
            return False
    
    def get_active_roles(self) -> List[Role]:
        """
        Get all active roles.
        
        Returns:
            List of active Role objects
        """
        try:
            cursor = self.collection.find({"is_active": True})
            roles = []
            for doc in cursor:
                role = self._convert_doc_to_role(doc)
                if role:
                    roles.append(role)
            return roles
        except Exception as e:
            logger.error(f"Error getting active roles: {e}")
            return []
    
    def get_roles_by_type(self, role_type: RoleType) -> List[Role]:
        """
        Get roles by type.
        
        Args:
            role_type: Type of roles to retrieve
            
        Returns:
            List of Role objects of the specified type
        """
        try:
            cursor = self.collection.find({"role_type": role_type.value})
            roles = []
            for doc in cursor:
                role = self._convert_doc_to_role(doc)
                if role:
                    roles.append(role)
            return roles
        except Exception as e:
            logger.error(f"Error getting roles by type {role_type}: {e}")
            return []
    
    def get_system_roles(self) -> List[Role]:
        """
        Get all system roles.
        
        Returns:
            List of system Role objects
        """
        try:
            cursor = self.collection.find({"is_system_role": True})
            roles = []
            for doc in cursor:
                role = self._convert_doc_to_role(doc)
                if role:
                    roles.append(role)
            return roles
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
            cursor = self.collection.find({"is_system_role": False})
            roles = []
            for doc in cursor:
                role = self._convert_doc_to_role(doc)
                if role:
                    roles.append(role)
            return roles
        except Exception as e:
            logger.error(f"Error getting custom roles: {e}")
            return []
    
    def _convert_doc_to_role(self, doc: Dict[str, Any]) -> Optional[Role]:
        """
        Convert MongoDB document to Role model.
        
        Args:
            doc: MongoDB document
            
        Returns:
            Role object if successful, None otherwise
        """
        try:
            # Convert ObjectId to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            # Convert role_type string to enum
            if "role_type" in doc and isinstance(doc["role_type"], str):
                try:
                    doc["role_type"] = RoleType(doc["role_type"])
                except ValueError:
                    logger.warning(f"Invalid role_type: {doc['role_type']}")
                    doc["role_type"] = RoleType.CUSTOM
            
            return Role.model_validate(doc)
        except Exception as e:
            logger.error(f"Error converting document to Role: {e}")
            return None
    
    def initialize_system_roles(self) -> bool:
        """
        Initialize system roles if they don't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            system_roles = [
                {
                    "name": "admin",
                    "display_name": "Administrator",
                    "description": "Full system access with all permissions",
                    "permissions": [
                        "user:manage", "user:read", "interview:manage", "interview:read",
                        "knowledge:manage", "knowledge:read", "analytics:manage", "analytics:read",
                        "system:manage", "system:read"
                    ],
                    "role_type": RoleType.SYSTEM,
                    "is_system_role": True
                },
                {
                    "name": "user",
                    "display_name": "User",
                    "description": "Basic user access",
                    "permissions": ["interview:read", "knowledge:read"],
                    "role_type": RoleType.SYSTEM,
                    "is_system_role": True
                },
                {
                    "name": "interviewer",
                    "display_name": "Interviewer",
                    "description": "Interview management access",
                    "permissions": ["interview:manage", "interview:read", "knowledge:read"],
                    "role_type": RoleType.FEATURE,
                    "is_system_role": True
                }
            ]
            
            for role_data in system_roles:
                if not self.role_exists(role_data["name"]):
                    role = Role(**role_data)
                    self.create_role(role)
                    logger.info(f"System role {role_data['name']} initialized")
                else:
                    logger.info(f"System role {role_data['name']} already exists")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing system roles: {e}")
            return False
