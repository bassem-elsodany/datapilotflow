"""
Confluence Pages Cache Data Access Object.

Handles caching of Confluence pages metadata for quick UI access and searching.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field

from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class ConfluencePage(BaseModel):
    """Domain model for cached Confluence page."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Cache entry ID")
    credential_id: str = Field(description="ID of the credential this page belongs to")
    user_id: str = Field(description="ID of the user")
    space_key: str = Field(description="Confluence space key")
    page_id: str = Field(description="Confluence page ID")
    page_title: str = Field(description="Page title")
    page_version: int = Field(default=1, description="Page version")
    last_modified: datetime = Field(description="When page was last modified")
    labels: List[str] = Field(default_factory=list, description="Page labels")
    last_synced: datetime = Field(
        description="When this cache entry was last updated"
    )

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConfluencePageDAO(MongoClientWrapper[ConfluencePage]):
    """Data Access Object for cached Confluence pages."""

    def __init__(self):
        super().__init__(
            model=ConfluencePage,
            collection_name="confluence_pages_cache",
        )

    async def create(self, page: ConfluencePage) -> ConfluencePage:
        """
        Create a cached page entry.

        Args:
            page: ConfluencePage to cache

        Returns:
            ConfluencePage: The created entry
        """
        try:
            logger.debug(
                f"Caching page: {page.page_id} in space: {page.space_key}"
            )

            page_dict = page.model_dump()
            self.collection.insert_one(page_dict)

            return page

        except Exception as e:
            logger.error(f"Error caching page: {e}")
            raise

    async def get_by_space_key(
        self,
        credential_id: str,
        space_key: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ConfluencePage]:
        """
        Get cached pages for a specific space.

        Args:
            credential_id: ID of the credential
            space_key: Space key
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List[ConfluencePage]: Cached pages in the space
        """
        try:
            documents = self.collection.find(
                {"credential_id": credential_id, "space_key": space_key}
            ).limit(limit).skip(skip)

            pages = [ConfluencePage(**doc) for doc in documents]

            return pages

        except Exception as e:
            logger.error(
                f"Error getting pages for space {space_key}: {e}"
            )
            return []

    async def get_by_labels(
        self,
        credential_id: str,
        labels: List[str],
        limit: int = 100,
    ) -> List[ConfluencePage]:
        """
        Get cached pages matching any of the given labels.

        Args:
            credential_id: ID of the credential
            labels: List of labels to search for
            limit: Maximum number of results

        Returns:
            List[ConfluencePage]: Pages matching the labels
        """
        try:
            documents = self.collection.find(
                {
                    "credential_id": credential_id,
                    "labels": {"$in": labels},
                }
            ).limit(limit)

            pages = [ConfluencePage(**doc) for doc in documents]

            return pages

        except Exception as e:
            logger.error(f"Error searching pages by labels: {e}")
            return []

    async def delete_by_credential_id(self, credential_id: str) -> bool:
        """
        Delete all cached pages for a credential.

        Args:
            credential_id: ID of the credential

        Returns:
            bool: True if deletion was successful
        """
        try:
            logger.debug(f"Clearing page cache for credential: {credential_id}")

            result = self.collection.delete_many(
                {"credential_id": credential_id}
            )
            logger.debug(
                f"Deleted {result.deleted_count} cached pages for credential: {credential_id}"
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(
                f"Error deleting pages for credential {credential_id}: {e}"
            )
            return False

    async def update_page(self, page: ConfluencePage) -> Optional[ConfluencePage]:
        """
        Update a cached page entry.

        Args:
            page: ConfluencePage with updated values

        Returns:
            ConfluencePage: The updated page, or None if not found
        """
        try:
            logger.debug(f"Updating cached page: {page.page_id}")

            page_dict = page.model_dump()
            result = self.collection.update_one(
                {
                    "credential_id": page.credential_id,
                    "page_id": page.page_id,
                },
                {"$set": page_dict},
            )

            if result.matched_count > 0:
                logger.debug(f"Updated cached page: {page.page_id}")
                return page
            else:
                logger.warning(f"Page not found: {page.page_id}")
                return None

        except Exception as e:
            logger.error(f"Error updating page {page.page_id}: {e}")
            return None

    async def bulk_upsert(self, pages: List[ConfluencePage]) -> int:
        """
        Upsert multiple pages efficiently.

        Args:
            pages: List of pages to upsert

        Returns:
            int: Number of pages processed
        """
        try:
            if not pages:
                return 0

            logger.debug(f"Bulk upserting {len(pages)} pages")

            operations = []
            for page in pages:
                operations.append(
                    {
                        "replace_one": {
                            "filter": {
                                "credential_id": page.credential_id,
                                "page_id": page.page_id,
                            },
                            "replacement": page.model_dump(),
                            "upsert": True,
                        }
                    }
                )

            if operations:
                result = self.collection.bulk_write(operations)
                logger.debug(
                    f"Bulk upsert completed: {result.modified_count} modified, "
                    f"{result.upserted_ids} upserted"
                )
                return len(pages)

            return 0

        except Exception as e:
            logger.error(f"Error bulk upserting pages: {e}")
            return 0


# Singleton instance
_confluence_page_dao: Optional[ConfluencePageDAO] = None


def get_confluence_page_dao() -> ConfluencePageDAO:
    """Get the singleton Confluence page DAO instance."""
    global _confluence_page_dao

    if _confluence_page_dao is None:
        _confluence_page_dao = ConfluencePageDAO()

    return _confluence_page_dao
