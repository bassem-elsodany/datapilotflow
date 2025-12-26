"""
Confluence Spaces Cache Data Access Object.

Handles caching of Confluence spaces metadata for quick UI access.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field

from datapilotflow.infrastructure.mongo.client import MongoClientWrapper


class ConfluenceSpace(BaseModel):
    """Domain model for cached Confluence space."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Cache entry ID")
    credential_id: str = Field(description="ID of the credential this space belongs to")
    user_id: str = Field(description="ID of the user")
    space_key: str = Field(description="Confluence space key")
    space_name: str = Field(description="Human-readable space name")
    total_pages: int = Field(default=0, description="Number of pages in space")
    last_synced: datetime = Field(
        description="When this cache entry was last updated"
    )

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConfluenceSpaceDAO(MongoClientWrapper[ConfluenceSpace]):
    """Data Access Object for cached Confluence spaces."""

    def __init__(self):
        super().__init__(
            model=ConfluenceSpace,
            collection_name="confluence_spaces_cache",
        )

    async def create(self, space: ConfluenceSpace) -> ConfluenceSpace:
        """
        Create a cached space entry.

        Args:
            space: ConfluenceSpace to cache

        Returns:
            ConfluenceSpace: The created entry
        """
        try:
            logger.debug(
                f"Caching space: {space.space_key} for credential: {space.credential_id}"
            )

            space_dict = space.model_dump()
            self.collection.insert_one(space_dict)

            return space

        except Exception as e:
            logger.error(f"Error caching space: {e}")
            raise

    async def get_by_credential_id(
        self, credential_id: str
    ) -> List[ConfluenceSpace]:
        """
        Get all cached spaces for a credential.

        Args:
            credential_id: ID of the credential

        Returns:
            List[ConfluenceSpace]: All cached spaces for the credential
        """
        try:
            documents = self.collection.find({"credential_id": credential_id})
            spaces = [ConfluenceSpace(**doc) for doc in documents]

            return spaces

        except Exception as e:
            logger.error(
                f"Error getting spaces for credential {credential_id}: {e}"
            )
            return []

    async def delete_by_credential_id(self, credential_id: str) -> bool:
        """
        Delete all cached spaces for a credential.

        Args:
            credential_id: ID of the credential

        Returns:
            bool: True if deletion was successful
        """
        try:
            logger.debug(f"Clearing space cache for credential: {credential_id}")

            result = self.collection.delete_many(
                {"credential_id": credential_id}
            )
            logger.debug(
                f"Deleted {result.deleted_count} cached spaces for credential: {credential_id}"
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(
                f"Error deleting spaces for credential {credential_id}: {e}"
            )
            return False

    async def update_space(self, space: ConfluenceSpace) -> Optional[ConfluenceSpace]:
        """
        Update a cached space entry.

        Args:
            space: ConfluenceSpace with updated values

        Returns:
            ConfluenceSpace: The updated space, or None if not found
        """
        try:
            logger.debug(f"Updating cached space: {space.space_key}")

            space_dict = space.model_dump()
            result = self.collection.update_one(
                {
                    "credential_id": space.credential_id,
                    "space_key": space.space_key,
                },
                {"$set": space_dict},
            )

            if result.matched_count > 0:
                logger.debug(f"Updated cached space: {space.space_key}")
                return space
            else:
                logger.warning(f"Space not found: {space.space_key}")
                return None

        except Exception as e:
            logger.error(f"Error updating space {space.space_key}: {e}")
            return None


# Singleton instance
_confluence_space_dao: Optional[ConfluenceSpaceDAO] = None


def get_confluence_space_dao() -> ConfluenceSpaceDAO:
    """Get the singleton Confluence space DAO instance."""
    global _confluence_space_dao

    if _confluence_space_dao is None:
        _confluence_space_dao = ConfluenceSpaceDAO()

    return _confluence_space_dao
