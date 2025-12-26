"""
Integration tests for Confluence DAOs.

Tests cover credential storage, caching, and metadata management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from datapilotflow.infrastructure.dao.confluence.confluence_credential_dao import (
    ConfluenceCredentialDAO,
    ConfluenceCredential,
    get_confluence_credential_dao,
)
from datapilotflow.infrastructure.dao.confluence.confluence_space_dao import (
    ConfluenceSpaceDAO,
    ConfluenceSpace,
    get_confluence_space_dao,
)
from datapilotflow.infrastructure.dao.confluence.confluence_page_dao import (
    ConfluencePageDAO,
    ConfluencePage,
    get_confluence_page_dao,
)


@pytest.fixture
def user_id():
    """Fixture for test user ID."""
    return str(uuid4())


@pytest.fixture
def credential_id():
    """Fixture for credential ID."""
    return str(uuid4())


@pytest.fixture
def confluence_credential(user_id, credential_id):
    """Fixture for a test Confluence credential."""
    return ConfluenceCredential(
        id=credential_id,
        user_id=user_id,
        name="Test Confluence",
        cloud_url="https://test.atlassian.net/wiki",
        username_or_email="test@example.com",
        api_token="test-token-123",
        created_at=datetime.now(),
        is_active=True,
    )


@pytest.fixture
def confluence_space(user_id, credential_id):
    """Fixture for a test Confluence space."""
    return ConfluenceSpace(
        id=str(uuid4()),
        credential_id=credential_id,
        user_id=user_id,
        space_key="TEST",
        space_name="Test Space",
        total_pages=10,
        last_synced=datetime.now(),
    )


@pytest.fixture
def confluence_page(user_id, credential_id):
    """Fixture for a test Confluence page."""
    return ConfluencePage(
        id=str(uuid4()),
        credential_id=credential_id,
        user_id=user_id,
        space_key="TEST",
        page_id="123",
        page_title="Test Page",
        page_version=1,
        last_modified=datetime.now(),
        labels=["test", "api"],
        last_synced=datetime.now(),
    )


@pytest.mark.asyncio
class TestConfluenceCredentialDAO:
    """Tests for Confluence credential DAO."""

    async def test_create_credential(self, confluence_credential):
        """Test credential creation."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.insert_one.return_value = Mock(inserted_id="test-id")

            result = await dao.create(confluence_credential)

            assert result.id == confluence_credential.id
            mock_collection.insert_one.assert_called_once()

    async def test_get_credential_by_id(self, confluence_credential):
        """Test retrieving credential by ID."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            credential_dict = confluence_credential.model_dump()
            credential_dict["api_token"] = f"encrypted:{credential_dict['api_token']}"
            mock_collection.find_one.return_value = credential_dict

            result = await dao.get_by_id(confluence_credential.id)

            assert result is not None
            assert result.id == confluence_credential.id
            mock_collection.find_one.assert_called_once_with(
                {"id": confluence_credential.id}
            )

    async def test_get_credential_not_found(self):
        """Test retrieving non-existent credential."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.find_one.return_value = None

            result = await dao.get_by_id("nonexistent-id")

            assert result is None

    async def test_get_credentials_by_user_id(self, user_id, confluence_credential):
        """Test retrieving all credentials for a user."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            credential_dict = confluence_credential.model_dump()
            credential_dict["api_token"] = f"encrypted:{credential_dict['api_token']}"
            mock_collection.find.return_value = [credential_dict]

            result = await dao.get_by_user_id(user_id)

            assert len(result) == 1
            assert result[0].user_id == user_id
            mock_collection.find.assert_called_once_with({"user_id": user_id})

    async def test_update_credential(self, confluence_credential):
        """Test updating a credential."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.update_one.return_value = Mock(matched_count=1)

            result = await dao.update(confluence_credential)

            assert result.id == confluence_credential.id
            mock_collection.update_one.assert_called_once()

    async def test_delete_credential(self, confluence_credential):
        """Test deleting a credential."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.delete_one.return_value = Mock(deleted_count=1)

            result = await dao.delete(confluence_credential.id)

            assert result is True
            mock_collection.delete_one.assert_called_once_with(
                {"id": confluence_credential.id}
            )

    async def test_token_encryption_decryption(self):
        """Test token encryption and decryption."""
        token = "my-secret-token"

        encrypted = ConfluenceCredentialDAO._encrypt_token(token)
        assert encrypted.startswith("encrypted:")
        assert encrypted != token

        decrypted = ConfluenceCredentialDAO._decrypt_token(encrypted)
        assert decrypted == token

    async def test_singleton_instance(self):
        """Test that DAO returns singleton instance."""
        dao1 = get_confluence_credential_dao()
        dao2 = get_confluence_credential_dao()

        assert dao1 is dao2


@pytest.mark.asyncio
class TestConfluenceSpaceDAO:
    """Tests for Confluence space DAO."""

    async def test_create_space(self, confluence_space):
        """Test space creation."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.insert_one.return_value = Mock(inserted_id="test-id")

            result = await dao.create(confluence_space)

            assert result.space_key == confluence_space.space_key
            mock_collection.insert_one.assert_called_once()

    async def test_get_spaces_by_credential_id(self, credential_id, confluence_space):
        """Test retrieving spaces by credential ID."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            space_dict = confluence_space.model_dump()
            mock_collection.find.return_value = [space_dict]

            result = await dao.get_by_credential_id(credential_id)

            assert len(result) == 1
            assert result[0].space_key == "TEST"
            mock_collection.find.assert_called_once_with(
                {"credential_id": credential_id}
            )

    async def test_get_spaces_empty(self, credential_id):
        """Test retrieving spaces when none exist."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.find.return_value = []

            result = await dao.get_by_credential_id(credential_id)

            assert len(result) == 0

    async def test_update_space(self, confluence_space):
        """Test updating a space."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.update_one.return_value = Mock(matched_count=1)

            result = await dao.update_space(confluence_space)

            assert result is not None
            assert result.space_key == confluence_space.space_key

    async def test_delete_spaces_by_credential_id(self, credential_id):
        """Test deleting all spaces for a credential."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.delete_many.return_value = Mock(deleted_count=5)

            result = await dao.delete_by_credential_id(credential_id)

            assert result is True

    async def test_singleton_instance(self):
        """Test that space DAO returns singleton instance."""
        dao1 = get_confluence_space_dao()
        dao2 = get_confluence_space_dao()

        assert dao1 is dao2


@pytest.mark.asyncio
class TestConfluencePageDAO:
    """Tests for Confluence page DAO."""

    async def test_create_page(self, confluence_page):
        """Test page creation."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.insert_one.return_value = Mock(inserted_id="test-id")

            result = await dao.create(confluence_page)

            assert result.page_id == confluence_page.page_id
            mock_collection.insert_one.assert_called_once()

    async def test_get_pages_by_space_key(self, credential_id, confluence_page):
        """Test retrieving pages by space key."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            page_dict = confluence_page.model_dump()
            mock_collection.find.return_value = [page_dict]
            mock_collection.find.return_value.limit.return_value = mock_collection.find.return_value
            mock_collection.find.return_value.skip.return_value = [page_dict]

            result = await dao.get_by_space_key(credential_id, "TEST")

            assert len(result) == 1
            assert result[0].page_id == "123"

    async def test_get_pages_by_space_with_pagination(self, credential_id, confluence_page):
        """Test page retrieval with pagination."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            page_dict = confluence_page.model_dump()
            mock_find = Mock()
            mock_find.limit.return_value.skip.return_value = [page_dict]
            mock_collection.find.return_value = mock_find

            result = await dao.get_by_space_key(
                credential_id, "TEST", limit=10, skip=5
            )

            assert len(result) == 1

    async def test_get_pages_by_labels(self, credential_id, confluence_page):
        """Test retrieving pages by labels."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            page_dict = confluence_page.model_dump()
            mock_find = Mock()
            mock_find.limit.return_value = [page_dict]
            mock_collection.find.return_value = mock_find

            result = await dao.get_by_labels(credential_id, ["test", "api"])

            assert len(result) == 1
            assert "test" in result[0].labels

    async def test_update_page(self, confluence_page):
        """Test updating a page."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.update_one.return_value = Mock(matched_count=1)

            result = await dao.update_page(confluence_page)

            assert result is not None
            assert result.page_id == confluence_page.page_id

    async def test_bulk_upsert_pages(self, confluence_page):
        """Test bulk upserting pages."""
        dao = ConfluencePageDAO()
        pages = [confluence_page] * 3

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.bulk_write.return_value = Mock(
                modified_count=2, upserted_ids=["1"]
            )

            result = await dao.bulk_upsert(pages)

            assert result == 3
            mock_collection.bulk_write.assert_called_once()

    async def test_delete_pages_by_credential_id(self, credential_id):
        """Test deleting all pages for a credential."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.delete_many.return_value = Mock(deleted_count=15)

            result = await dao.delete_by_credential_id(credential_id)

            assert result is True

    async def test_singleton_instance(self):
        """Test that page DAO returns singleton instance."""
        dao1 = get_confluence_page_dao()
        dao2 = get_confluence_page_dao()

        assert dao1 is dao2


@pytest.mark.asyncio
class TestDAOErrorHandling:
    """Tests for DAO error handling."""

    async def test_credential_dao_create_error(self, confluence_credential):
        """Test error handling during credential creation."""
        dao = ConfluenceCredentialDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.insert_one.side_effect = Exception("Database error")

            with pytest.raises(Exception):
                await dao.create(confluence_credential)

    async def test_space_dao_query_error(self, credential_id):
        """Test error handling during space queries."""
        dao = ConfluenceSpaceDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.find.side_effect = Exception("Query error")

            result = await dao.get_by_credential_id(credential_id)

            # Should return empty list on error
            assert result == []

    async def test_page_dao_bulk_operation_error(self):
        """Test error handling during bulk page operations."""
        dao = ConfluencePageDAO()

        with patch.object(dao, "collection") as mock_collection:
            mock_collection.bulk_write.side_effect = Exception("Bulk operation error")

            result = await dao.bulk_upsert([])

            assert result == 0
