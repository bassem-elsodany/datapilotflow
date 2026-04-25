"""
Admin User Initialization Service.

This service handles the initialization of the admin user and system roles during
application startup.  It always upserts the admin user so profile details and role
assignments stay in sync with the code-defined defaults even after a MongoDB wipe
or manual edit.

Default admin credentials
--------------------------
  username : admin
  password : admin123          ← change this on first login!
  email    : admin@datapilotflow.com
  role     : admin  (display: "Platform Admin") — full access to everything
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from datapilotflow.infrastructure.dao.auth import AuthDAO
from loguru import logger

from datapilotflow.services.users.roles_service import RolesService

# ---------------------------------------------------------------------------
# Canonical admin user defaults — update here if you need to change them.
# ---------------------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@datapilotflow.com"
ADMIN_NAME = "System Administrator"
ADMIN_DEFAULT_PASSWORD = "admin123"
ADMIN_ROLE_NAME = "admin"          # matches roles_dao.initialize_system_roles


class AdminInitializationService:
    """Service for initializing admin users and system roles."""

    def __init__(self):
        self.auth_dao = AuthDAO()
        self.roles_service = RolesService()

    async def initialize_admin_user_if_needed(self) -> bool:
        """
        Upsert the default admin user.

        - If the user does not exist it is created with the defaults above.
        - If the user already exists, their name / email / is_active status are
          brought back to the canonical defaults (password is NOT reset).
        - The Platform Admin role is always re-assigned in both cases.
        """
        try:
            logger.info("🔧 Initializing admin user…")

            # Resolve the Platform Admin role first — must exist before we touch the user.
            admin_role = self.roles_service.get_role_by_name(ADMIN_ROLE_NAME)
            if not admin_role or not admin_role.id:
                logger.error(
                    "❌ Admin role '%s' not found. "
                    "Run initialize_system_roles first.",
                    ADMIN_ROLE_NAME,
                )
                return False

            existing_admin = self.auth_dao.get_user_by_username(ADMIN_USERNAME)

            if existing_admin:
                logger.debug("Admin user already exists — syncing profile & role…")
                # Bring profile fields back to canonical defaults (non-destructive).
                self.auth_dao.collection.update_one(
                    {"username": ADMIN_USERNAME},
                    {
                        "$set": {
                            "email": ADMIN_EMAIL,
                            "name": ADMIN_NAME,
                            "is_active": True,
                        }
                    },
                )
                if existing_admin.id:
                    await self._ensure_admin_role_assigned(existing_admin.id, admin_role.id)
                logger.debug("✅ Admin user profile synced.")
                return True

            # ── First-time creation ──────────────────────────────────────────
            logger.info("🔧 Creating default admin user…")
            admin_data = {
                "_id": str(uuid.uuid4()),
                "username": ADMIN_USERNAME,
                "email": ADMIN_EMAIL,
                "name": ADMIN_NAME,
                "hashed_password": bcrypt.hashpw(
                    ADMIN_DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8"),
                "role_ids": [admin_role.id],
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "is_active": True,
                "profile_data": {
                    "description": "Default system administrator — Platform Admin role",
                    "created_by": "system",
                },
            }

            result = self.auth_dao.collection.insert_one(admin_data)
            if result.inserted_id:
                logger.info("✅ Admin user created.")
                logger.info("   username : %s", ADMIN_USERNAME)
                logger.info("   email    : %s", ADMIN_EMAIL)
                logger.warning(
                    "⚠️  Default password is '%s' — change it after first login!",
                    ADMIN_DEFAULT_PASSWORD,
                )
                return True

            logger.error("❌ Failed to insert admin user document.")
            return False

        except Exception as e:
            logger.error(f"Error initializing admin user: {e}")
            return False

    async def _ensure_admin_role_assigned(
        self, user_id: str, admin_role_id: Optional[str] = None
    ) -> bool:
        """Ensure the admin user holds the Platform Admin role_id."""
        try:
            from datapilotflow.services.users.user_service import UserService

            user_service = UserService()

            if admin_role_id is None:
                admin_role = self.roles_service.get_role_by_name(ADMIN_ROLE_NAME)
                if not admin_role or not admin_role.id:
                    logger.error("❌ Admin role not found or has no ID")
                    return False
                admin_role_id = admin_role.id

            user = user_service.get_user_by_id(user_id)
            if not user:
                logger.error(f"❌ User {user_id} not found")
                return False

            if admin_role_id not in user.role_ids:
                logger.info(f"🔧 Assigning Platform Admin role to user {user_id}")
                success = user_service.assign_role_to_user(user_id, admin_role_id)
                if success:
                    logger.debug(f"✅ Platform Admin role assigned to user {user_id}")
                    return True
                logger.error(f"❌ Failed to assign Platform Admin role to user {user_id}")
                return False

            logger.debug(f"✅ User {user_id} already has Platform Admin role")
            return True

        except Exception as e:
            logger.error(f"Error ensuring admin role assignment: {e}")
            return False

    async def initialize_system_roles_if_needed(self) -> bool:
        """Initialize (upsert) system roles on every startup to keep definitions in sync."""
        try:
            logger.info("🔧 Syncing system roles...")
            success = self.roles_service.initialize_system_roles()

            if success:
                logger.debug("✅ System roles initialized successfully!")
                return True
            else:
                logger.error(f"❌ Failed to initialize system roles")
                return False

        except Exception as e:
            logger.error(f"Error initializing system roles: {e}")
            return False

    async def initialize_system_if_needed(self) -> bool:
        """Initialize the complete system (admin user and roles) if needed."""
        try:
            logger.debug("🚀 Starting system initialization...")

            # Initialize system roles first
            roles_success = await self.initialize_system_roles_if_needed()

            # Initialize admin user
            admin_success = await self.initialize_admin_user_if_needed()

            if roles_success and admin_success:
                logger.debug("✅ System initialization completed successfully!")
                return True
            else:
                logger.error(f"❌ System initialization failed")
                return False

        except Exception as e:
            logger.error(f"Error during system initialization: {e}")
            return False


# Global service instance
_admin_initialization_service: Optional[AdminInitializationService] = None


def get_admin_initialization_service() -> AdminInitializationService:
    """Get the global admin initialization service instance."""
    global _admin_initialization_service
    if _admin_initialization_service is None:
        _admin_initialization_service = AdminInitializationService()
    return _admin_initialization_service
