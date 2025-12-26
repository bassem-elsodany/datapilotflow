"""
Confluence Credential Service.

Handles storage, retrieval, and management of Confluence API credentials.
Credentials are encrypted in the database for security.
"""

from datetime import datetime
from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import ConfluenceConfig
from datapilotflow.infrastructure.dao.confluence_credential_dao import (
    ConfluenceCredential,
    ConfluenceCredentialDAO,
)


class ConfluenceCredentialService:
    """
    Service for managing Confluence API credentials.

    Provides methods for:
    - Creating and storing credentials
    - Retrieving credentials by ID
    - Verifying credentials are valid
    - Updating credentials
    - Deleting credentials
    - Listing all credentials for a user
    """

    def __init__(self, credential_dao: Optional[ConfluenceCredentialDAO] = None):
        """
        Initialize the credential service.

        Args:
            credential_dao: Optional DAO instance. If None, a new instance will be created.
        """
        from datapilotflow.infrastructure.dao import get_confluence_credential_dao

        self.dao = credential_dao or get_confluence_credential_dao()

    async def create_credential(
        self,
        user_id: str,
        name: str,
        cloud_url: str,
        username_or_email: str,
        api_token: str,
    ) -> ConfluenceCredential:
        """
        Create and store a new Confluence credential.

        Args:
            user_id: ID of the user creating the credential
            name: Human-readable name for the credential
            cloud_url: Confluence Cloud URL
            username_or_email: Username or email for authentication
            api_token: API token for authentication

        Returns:
            ConfluenceCredential: The created credential

        Raises:
            ValueError: If required fields are missing
        """
        if not all(
            [user_id, name, cloud_url, username_or_email, api_token]
        ):
            raise ValueError("All credential fields are required")

        logger.info(f"Creating Confluence credential for user: {user_id}")

        credential = ConfluenceCredential(
            user_id=user_id,
            name=name,
            cloud_url=cloud_url.rstrip("/"),
            username_or_email=username_or_email,
            api_token=api_token,  # DAO will encrypt before storing
            created_at=datetime.utcnow(),
            last_verified=None,
            is_active=True,
        )

        saved_credential = await self.dao.create(credential)
        logger.info(
            f"Created Confluence credential: {saved_credential.id} for user: {user_id}"
        )
        return saved_credential

    async def get_credential(
        self, credential_id: str, user_id: str
    ) -> Optional[ConfluenceCredential]:
        """
        Retrieve a credential by ID (with user verification).

        Args:
            credential_id: ID of the credential
            user_id: ID of the user requesting the credential (for access control)

        Returns:
            ConfluenceCredential: The requested credential, or None if not found

        Raises:
            PermissionError: If user does not own the credential
        """
        logger.debug(f"Retrieving credential: {credential_id} for user: {user_id}")

        credential = await self.dao.get_by_id(credential_id)

        if credential is None:
            logger.warning(f"Credential not found: {credential_id}")
            return None

        if credential.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access credential {credential_id} "
                f"owned by {credential.user_id}"
            )
            raise PermissionError(
                "You do not have permission to access this credential"
            )

        return credential

    async def list_credentials(self, user_id: str) -> List[ConfluenceCredential]:
        """
        List all Confluence credentials for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[ConfluenceCredential]: All credentials owned by the user
        """
        logger.info(f"Listing Confluence credentials for user: {user_id}")

        credentials = await self.dao.get_by_user_id(user_id)
        logger.debug(f"Found {len(credentials)} credentials for user: {user_id}")
        return credentials

    async def update_credential(
        self,
        credential_id: str,
        user_id: str,
        name: Optional[str] = None,
        cloud_url: Optional[str] = None,
        username_or_email: Optional[str] = None,
        api_token: Optional[str] = None,
    ) -> ConfluenceCredential:
        """
        Update a Confluence credential.

        Args:
            credential_id: ID of the credential to update
            user_id: ID of the user making the update
            name: New name (optional)
            cloud_url: New cloud URL (optional)
            username_or_email: New username/email (optional)
            api_token: New API token (optional)

        Returns:
            ConfluenceCredential: The updated credential

        Raises:
            PermissionError: If user does not own the credential
            ValueError: If credential not found
        """
        credential = await self.get_credential(credential_id, user_id)
        if credential is None:
            raise ValueError(f"Credential not found: {credential_id}")

        logger.info(f"Updating credential: {credential_id}")

        # Update fields if provided
        if name is not None:
            credential.name = name
        if cloud_url is not None:
            credential.cloud_url = cloud_url.rstrip("/")
        if username_or_email is not None:
            credential.username_or_email = username_or_email
        if api_token is not None:
            credential.api_token = api_token

        updated_credential = await self.dao.update(credential)
        logger.info(f"Updated credential: {credential_id}")
        return updated_credential

    async def delete_credential(self, credential_id: str, user_id: str) -> bool:
        """
        Delete a Confluence credential.

        Args:
            credential_id: ID of the credential to delete
            user_id: ID of the user making the deletion

        Returns:
            bool: True if deletion was successful

        Raises:
            PermissionError: If user does not own the credential
            ValueError: If credential not found
        """
        credential = await self.get_credential(credential_id, user_id)
        if credential is None:
            raise ValueError(f"Credential not found: {credential_id}")

        logger.info(f"Deleting credential: {credential_id} for user: {user_id}")

        success = await self.dao.delete(credential_id)
        if success:
            logger.info(f"Successfully deleted credential: {credential_id}")
        else:
            logger.warning(f"Failed to delete credential: {credential_id}")

        return success

    async def verify_raw_credentials(
        self, cloud_url: str, username_or_email: str, api_token: str
    ) -> bool:
        """
        Verify raw Confluence credentials without requiring a stored credential.

        Used for testing credentials before saving them.

        Args:
            cloud_url: Confluence Cloud URL
            username_or_email: Username or email
            api_token: API token

        Returns:
            bool: True if credentials are valid

        Raises:
            ValueError: If verification fails
        """
        logger.info(f"Testing Confluence credentials for URL: {cloud_url}")

        try:
            from datapilotflow.processors.confluence import ConfluenceApiClient

            config = ConfluenceConfig(
                cloud_url=cloud_url,
                username_or_email=username_or_email,
                api_token=api_token,
                confluence_mode=None,  # Not needed for verification
            )

            async with ConfluenceApiClient(config) as client:
                is_valid = await client.verify_credentials()

            if is_valid:
                logger.info(f"Credentials verified for URL: {cloud_url}")
                return True

        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            raise ValueError(f"Credential verification failed: {str(e)}")

    async def verify_credential(self, credential_id: str, user_id: str) -> bool:
        """
        Verify that a credential is valid by testing the connection to Confluence.

        Args:
            credential_id: ID of the credential to verify
            user_id: ID of the user making the verification

        Returns:
            bool: True if credential is valid

        Raises:
            PermissionError: If user does not own the credential
            ValueError: If credential not found or verification fails
        """
        credential = await self.get_credential(credential_id, user_id)
        if credential is None:
            raise ValueError(f"Credential not found: {credential_id}")

        logger.info(f"Verifying credential: {credential_id}")

        try:
            from datapilotflow.processors.confluence import ConfluenceApiClient

            config = ConfluenceConfig(
                cloud_url=credential.cloud_url,
                username_or_email=credential.username_or_email,
                api_token=credential.api_token,
                confluence_mode=None,  # Not needed for verification
            )

            async with ConfluenceApiClient(config) as client:
                is_valid = await client.verify_credentials()

            if is_valid:
                # Update last_verified timestamp
                credential.last_verified = datetime.utcnow()
                await self.dao.update(credential)
                logger.info(f"Credential verified: {credential_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to verify credential {credential_id}: {e}")
            raise ValueError(f"Credential verification failed: {str(e)}")

    async def deactivate_credential(self, credential_id: str, user_id: str) -> bool:
        """
        Deactivate a credential (mark as inactive without deleting).

        Args:
            credential_id: ID of the credential to deactivate
            user_id: ID of the user making the request

        Returns:
            bool: True if deactivation was successful

        Raises:
            PermissionError: If user does not own the credential
        """
        credential = await self.get_credential(credential_id, user_id)
        if credential is None:
            raise ValueError(f"Credential not found: {credential_id}")

        logger.info(f"Deactivating credential: {credential_id}")

        credential.is_active = False
        await self.dao.update(credential)
        logger.info(f"Deactivated credential: {credential_id}")
        return True

    async def activate_credential(self, credential_id: str, user_id: str) -> bool:
        """
        Activate a previously deactivated credential.

        Args:
            credential_id: ID of the credential to activate
            user_id: ID of the user making the request

        Returns:
            bool: True if activation was successful

        Raises:
            PermissionError: If user does not own the credential
        """
        credential = await self.get_credential(credential_id, user_id)
        if credential is None:
            raise ValueError(f"Credential not found: {credential_id}")

        logger.info(f"Activating credential: {credential_id}")

        credential.is_active = True
        await self.dao.update(credential)
        logger.info(f"Activated credential: {credential_id}")
        return True


# Singleton instance
_confluence_credential_service: Optional[ConfluenceCredentialService] = None


def get_confluence_credential_service() -> ConfluenceCredentialService:
    """Get the singleton Confluence credential service instance."""
    global _confluence_credential_service

    if _confluence_credential_service is None:
        _confluence_credential_service = ConfluenceCredentialService()

    return _confluence_credential_service
