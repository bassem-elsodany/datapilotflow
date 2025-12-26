"""
Confluence Metadata Service.

Handles fetching and caching Confluence spaces and pages metadata
for use in the UI during job configuration.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import ConfluenceConfig
from datapilotflow.infrastructure.dao.confluence_space_dao import (
    ConfluenceSpace,
    ConfluenceSpaceDAO,
)
from datapilotflow.infrastructure.dao.confluence_page_dao import (
    ConfluencePage,
    ConfluencePageDAO,
)
from datapilotflow.infrastructure.dao.confluence_credential_dao import (
    ConfluenceCredential,
)


class ConfluenceMetadataService:
    """
    Service for managing Confluence spaces and pages metadata.

    Provides methods for:
    - Fetching and caching spaces for a credential
    - Fetching and caching pages for a space
    - Searching pages by labels
    - Updating cached metadata
    """

    CACHE_TTL_MINUTES = 60  # Cache expires after 1 hour

    def __init__(
        self,
        space_dao: Optional[ConfluenceSpaceDAO] = None,
        page_dao: Optional[ConfluencePageDAO] = None,
    ):
        """
        Initialize the metadata service.

        Args:
            space_dao: Optional space DAO instance
            page_dao: Optional page DAO instance
        """
        from datapilotflow.infrastructure.dao import (
            get_confluence_space_dao,
            get_confluence_page_dao,
        )

        self.space_dao = space_dao or get_confluence_space_dao()
        self.page_dao = page_dao or get_confluence_page_dao()

    async def sync_spaces(
        self,
        user_id: str,
        credential: ConfluenceCredential,
        force: bool = False,
    ) -> List[ConfluenceSpace]:
        """
        Fetch and cache spaces from Confluence.

        Args:
            user_id: ID of the user
            credential: The Confluence credential to use
            force: Force refresh even if cache is valid

        Returns:
            List[ConfluenceSpace]: List of spaces

        Raises:
            ValueError: If credential verification fails
        """
        logger.info(f"Syncing Confluence spaces for credential: {credential.id}")

        # Check if we can use cached data
        if not force:
            cached_spaces = await self.space_dao.get_by_credential_id(
                credential.id
            )
            if cached_spaces:
                # Check if cache is still valid
                if cached_spaces and self._is_cache_valid(cached_spaces[0]):
                    logger.debug("Using cached spaces")
                    return cached_spaces

        # Fetch fresh spaces from Confluence
        try:
            from datapilotflow.processors.confluence import ConfluenceApiClient

            config = ConfluenceConfig(
                cloud_url=credential.cloud_url,
                username_or_email=credential.username_or_email,
                api_token=credential.api_token,
                confluence_mode=None,  # Not needed for space listing
            )

            async with ConfluenceApiClient(config) as client:
                # Note: API client would need a get_spaces() method
                # For now, we'll implement basic space discovery
                logger.info(
                    f"Fetching spaces from Confluence: {credential.cloud_url}"
                )

                # Clear old cache for this credential
                await self.space_dao.delete_by_credential_id(credential.id)

                # TODO: Implement actual space fetching from API
                # For now, return empty list as placeholder
                logger.warning(
                    "Space syncing requires additional API client method"
                )
                return []

        except Exception as e:
            logger.error(f"Failed to sync spaces: {e}")
            raise ValueError(f"Failed to sync spaces: {str(e)}")

    async def get_spaces(
        self,
        user_id: str,
        credential_id: str,
        use_cache: bool = True,
    ) -> List[ConfluenceSpace]:
        """
        Get spaces for a credential.

        Args:
            user_id: ID of the user
            credential_id: ID of the credential
            use_cache: Whether to use cached data

        Returns:
            List[ConfluenceSpace]: List of spaces
        """
        logger.debug(f"Getting spaces for credential: {credential_id}")

        spaces = await self.space_dao.get_by_credential_id(credential_id)

        if not spaces and use_cache:
            logger.debug("No cached spaces, returning empty list")

        return spaces or []

    async def get_pages_in_space(
        self,
        user_id: str,
        credential_id: str,
        space_key: str,
        use_cache: bool = True,
        limit: int = 100,
    ) -> List[ConfluencePage]:
        """
        Get pages in a specific space.

        Args:
            user_id: ID of the user
            credential_id: ID of the credential
            space_key: The space key
            use_cache: Whether to use cached data
            limit: Maximum number of pages to return

        Returns:
            List[ConfluencePage]: Pages in the space
        """
        logger.debug(
            f"Getting pages for space: {space_key} (credential: {credential_id})"
        )

        pages = await self.page_dao.get_by_space_key(
            credential_id, space_key, limit=limit
        )

        return pages or []

    async def search_pages_by_labels(
        self,
        user_id: str,
        credential_id: str,
        labels: List[str],
        limit: int = 100,
    ) -> List[ConfluencePage]:
        """
        Search for pages matching specific labels.

        Args:
            user_id: ID of the user
            credential_id: ID of the credential
            labels: List of labels to search for
            limit: Maximum number of results

        Returns:
            List[ConfluencePage]: Pages matching the labels
        """
        logger.debug(
            f"Searching pages by labels: {labels} "
            f"(credential: {credential_id})"
        )

        pages = await self.page_dao.get_by_labels(
            credential_id, labels, limit=limit
        )

        return pages or []

    async def invalidate_cache(self, credential_id: str) -> bool:
        """
        Invalidate cached metadata for a credential.

        Args:
            credential_id: ID of the credential

        Returns:
            bool: True if invalidation was successful
        """
        logger.info(f"Invalidating cache for credential: {credential_id}")

        try:
            await self.space_dao.delete_by_credential_id(credential_id)
            await self.page_dao.delete_by_credential_id(credential_id)
            logger.info(f"Cache invalidated for credential: {credential_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False

    @staticmethod
    def _is_cache_valid(cached_item) -> bool:
        """
        Check if cached item is still valid based on TTL.

        Args:
            cached_item: Cached space or page with last_synced timestamp

        Returns:
            bool: True if cache is still valid
        """
        if not hasattr(cached_item, "last_synced") or cached_item.last_synced is None:
            return False

        age = datetime.utcnow() - cached_item.last_synced
        ttl = timedelta(minutes=ConfluenceMetadataService.CACHE_TTL_MINUTES)

        return age < ttl


# Singleton instance
_confluence_metadata_service: Optional[ConfluenceMetadataService] = None


def get_confluence_metadata_service() -> ConfluenceMetadataService:
    """Get the singleton Confluence metadata service instance."""
    global _confluence_metadata_service

    if _confluence_metadata_service is None:
        _confluence_metadata_service = ConfluenceMetadataService()

    return _confluence_metadata_service
