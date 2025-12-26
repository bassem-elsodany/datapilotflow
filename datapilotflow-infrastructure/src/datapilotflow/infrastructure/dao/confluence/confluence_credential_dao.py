"""
Confluence Credential Data Access Object.

Handles storage, retrieval, and management of Confluence API credentials.
API tokens are encrypted in the database.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from bson import ObjectId
from loguru import logger
from pydantic import BaseModel, Field

from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class ConfluenceCredential(BaseModel):
    """Domain model for a Confluence credential."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Credential ID")
    user_id: str = Field(description="ID of the user who owns this credential")
    name: str = Field(description="Human-readable name for the credential")
    cloud_url: str = Field(description="Confluence Cloud URL")
    username_or_email: str = Field(description="Username or email for authentication")
    api_token: str = Field(description="API token (encrypted in database)")
    created_at: datetime = Field(description="When the credential was created")
    last_verified: Optional[datetime] = Field(
        default=None, description="When the credential was last verified"
    )
    is_active: bool = Field(
        default=True, description="Whether the credential is active"
    )

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConfluenceCredentialDAO(MongoClientWrapper[ConfluenceCredential]):
    """Data Access Object for Confluence credentials."""

    def __init__(self):
        super().__init__(
            model=ConfluenceCredential,
            collection_name="confluence_credentials",
        )

    async def create(self, credential: ConfluenceCredential) -> ConfluenceCredential:
        """
        Create a new Confluence credential.

        Args:
            credential: ConfluenceCredential to create

        Returns:
            ConfluenceCredential: The created credential

        Raises:
            Exception: If creation fails
        """
        try:
            logger.info(
                f"Creating Confluence credential for user: {credential.user_id}"
            )

            credential_dict = {
                "id": credential.id,
                "user_id": credential.user_id,
                "name": credential.name,
                "cloud_url": credential.cloud_url,
                "username_or_email": credential.username_or_email,
                "api_token": self._encrypt_token(credential.api_token),
                "created_at": credential.created_at,
                "last_verified": credential.last_verified,
                "is_active": credential.is_active,
            }

            result = self.collection.insert_one(credential_dict)
            logger.info(f"Created credential: {credential.id}")
            return credential

        except Exception as e:
            logger.error(f"Error creating credential: {e}")
            raise

    async def get_by_id(self, credential_id: str) -> Optional[ConfluenceCredential]:
        """
        Get a credential by ID.

        Args:
            credential_id: ID of the credential

        Returns:
            ConfluenceCredential: The credential, or None if not found
        """
        try:
            document = self.collection.find_one({"id": credential_id})

            if document:
                # Decrypt token before returning
                document["api_token"] = self._decrypt_token(
                    document.get("api_token", "")
                )
                return ConfluenceCredential(**document)

            return None

        except Exception as e:
            logger.error(f"Error getting credential {credential_id}: {e}")
            return None

    async def get_by_user_id(self, user_id: str) -> List[ConfluenceCredential]:
        """
        Get all credentials for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[ConfluenceCredential]: All credentials for the user
        """
        try:
            documents = self.collection.find({"user_id": user_id})
            credentials = []

            for document in documents:
                # Decrypt token before returning
                document["api_token"] = self._decrypt_token(
                    document.get("api_token", "")
                )
                credentials.append(ConfluenceCredential(**document))

            return credentials

        except Exception as e:
            logger.error(f"Error getting credentials for user {user_id}: {e}")
            return []

    async def update(self, credential: ConfluenceCredential) -> ConfluenceCredential:
        """
        Update an existing credential.

        Args:
            credential: ConfluenceCredential with updated values

        Returns:
            ConfluenceCredential: The updated credential

        Raises:
            Exception: If update fails
        """
        try:
            logger.info(f"Updating credential: {credential.id}")

            update_dict = {
                "name": credential.name,
                "cloud_url": credential.cloud_url,
                "username_or_email": credential.username_or_email,
                "api_token": self._encrypt_token(credential.api_token),
                "last_verified": credential.last_verified,
                "is_active": credential.is_active,
            }

            self.collection.update_one(
                {"id": credential.id},
                {"$set": update_dict},
            )

            logger.info(f"Updated credential: {credential.id}")
            return credential

        except Exception as e:
            logger.error(f"Error updating credential {credential.id}: {e}")
            raise

    async def delete(self, credential_id: str) -> bool:
        """
        Delete a credential.

        Args:
            credential_id: ID of the credential to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            logger.info(f"Deleting credential: {credential_id}")

            result = self.collection.delete_one({"id": credential_id})
            success = result.deleted_count > 0

            if success:
                logger.info(f"Deleted credential: {credential_id}")
            else:
                logger.warning(f"Credential not found: {credential_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting credential {credential_id}: {e}")
            return False

    @staticmethod
    def _encrypt_token(token: str) -> str:
        """
        Encrypt API token before storage.

        Args:
            token: Plain text API token

        Returns:
            str: Encrypted token

        Note:
            This is a placeholder implementation. In production, use proper
            encryption library (e.g., cryptography, fernet).
        """
        # TODO: Implement proper encryption using cryptography library
        # For now, return base64 encoded as placeholder
        import base64
        return f"encrypted:{base64.b64encode(token.encode()).decode()}"

    @staticmethod
    def _decrypt_token(encrypted_token: str) -> str:
        """
        Decrypt API token from storage.

        Args:
            encrypted_token: Encrypted API token

        Returns:
            str: Plain text API token

        Note:
            This is a placeholder implementation. In production, use proper
            decryption library (e.g., cryptography, fernet).
        """
        # TODO: Implement proper decryption using cryptography library
        # For now, handle base64 as placeholder
        if encrypted_token.startswith("encrypted:"):
            import base64
            encoded = encrypted_token[len("encrypted:"):]
            return base64.b64decode(encoded).decode()
        return encrypted_token


# Singleton instance
_confluence_credential_dao: Optional[ConfluenceCredentialDAO] = None


def get_confluence_credential_dao() -> ConfluenceCredentialDAO:
    """Get the singleton Confluence credential DAO instance."""
    global _confluence_credential_dao

    if _confluence_credential_dao is None:
        _confluence_credential_dao = ConfluenceCredentialDAO()

    return _confluence_credential_dao
