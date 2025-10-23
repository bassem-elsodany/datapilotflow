"""
Admin User Initialization Service.

This service handles the initialization of admin users and system roles
during application startup. It ensures that essential system users and
roles are created if they don't exist.
"""

import uuid
import bcrypt
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from src.services.auth.dao.auth_dao import AuthDAO
from src.services.users.roles_service import RolesService


class AdminInitializationService:
    """Service for initializing admin users and system roles."""
    
    def __init__(self):
        self.auth_dao = AuthDAO()
        self.roles_service = RolesService()
    
    async def initialize_admin_user_if_needed(self) -> bool:
        """Initialize admin user if it doesn't exist."""
        try:
            logger.info("🔧 Initializing admin user...")
            # Check if admin user already exists
            existing_admin = self.auth_dao.get_user_by_username("admin")
            if existing_admin:
                logger.info(f"✅ Admin user already exists: {existing_admin.username}")
                return True
            
            # Create admin user if it doesn't exist
            logger.info("🔧 Creating default admin user...")
            
            # Create admin user data
            admin_data = {
                "_id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@datapilotflow.com",
                "name": "System Administrator",
                "hashed_password": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "roles": ["admin"],
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "is_active": True,
                "profile_data": {
                    "description": "Default system administrator",
                    "created_by": "system"
                }
            }
            
            # Insert the admin user
            result = self.auth_dao.collection.insert_one(admin_data)
            
            if result.inserted_id:
                logger.info("✅ Admin user created successfully!")
                logger.debug("   Username: admin")
                logger.debug("   Password: admin123")
                logger.debug("   Email: admin@datapilotflow.com")
                logger.warning("⚠️  IMPORTANT: Change the default password after first login!")
                return True
            else:
                logger.error("❌ Failed to create admin user")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing admin user: {e}")
            return False
    
    async def initialize_system_roles_if_needed(self) -> bool:
        """Initialize system roles if they don't exist."""
        try:
            logger.info("🔧 Initializing system roles...")
            # Check if system roles exist
            system_roles = self.roles_service.get_system_roles()
            if system_roles:
                logger.info(f"✅ System roles already exist: {len(system_roles)} roles found")
                return True
            
            # Initialize system roles
            logger.info("🔧 Initializing system roles...")
            success = self.roles_service.initialize_system_roles()
            
            if success:
                logger.info("✅ System roles initialized successfully!")
                return True
            else:
                logger.error("❌ Failed to initialize system roles")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing system roles: {e}")
            return False
    
    async def initialize_system_if_needed(self) -> bool:
        """Initialize the complete system (admin user and roles) if needed."""
        try:
            logger.info("🚀 Starting system initialization...")
            
            # Initialize system roles first
            roles_success = await self.initialize_system_roles_if_needed()
            
            # Initialize admin user
            admin_success = await self.initialize_admin_user_if_needed()
            
            if roles_success and admin_success:
                logger.info("✅ System initialization completed successfully!")
                return True
            else:
                logger.error("❌ System initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during system initialization: {e}")
            return False


# Global service instance
_admin_initialization_service: Optional[AdminInitializationService] = None


def get_admin_initialization_service() -> AdminInitializationService:
    """Get the global admin initialization service instance."""
    global _admin_initialization_service
    
    if _admin_initialization_service is None:
        _admin_initialization_service = AdminInitializationService()
    
    return _admin_initialization_service
