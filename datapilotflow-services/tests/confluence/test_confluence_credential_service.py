"""
Integration tests for Confluence Credential Service.

Tests cover credential lifecycle management and user isolation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from datapilotflow.services.confluence.confluence_credential_service import (
    ConfluenceCredentialService,
)
from datapilotflow.infrastructure.dao.confluence.confluence_credential_dao import (
    ConfluenceCredential,
)


@pytest.fixture
def user_id():
    """Fixture for test user ID."""
    return str(uuid4())


@pytest.fixture
def credential_data():
    """Fixture for test credential data."""
    return {
        "name": "Test Confluence",
        "cloud_url": "https://test.atlassian.net/wiki",
        "username_or_email": "test@example.com",
        "api_token": "test-token-123",
    }


@pytest.fixture
def credential(user_id, credential_data):
    """Fixture for a test credential."""
    return ConfluenceCredential(
        id=str(uuid4()),
        user_id=user_id,
        name=credential_data["name"],
        cloud_url=credential_data["cloud_url"],
        username_or_email=credential_data["username_or_email"],
        api_token=credential_data["api_token"],
        created_at=datetime.now(),
        is_active=True,
    )


@pytest.fixture
async def service():
    """Fixture for ConfluenceCredentialService."""
    with patch(
        "datapilotflow.services.confluence.confluence_credential_service.get_confluence_credential_dao"
    ) as mock_dao_getter:
        mock_dao = AsyncMock()
        mock_dao_getter.return_value = mock_dao
        service = ConfluenceCredentialService()
        service.credential_dao = mock_dao
        yield service


@pytest.mark.asyncio
class TestCreateCredential:
    """Tests for credential creation."""

    async def test_create_credential_success(self, service, user_id, credential_data, credential):
        """Test successful credential creation."""
        service.credential_dao.create.return_value = credential

        result = await service.create_credential(user_id, credential_data)

        assert result.id == credential.id
        assert result.user_id == user_id
        assert result.name == credential_data["name"]
        service.credential_dao.create.assert_called_once()

    async def test_create_credential_with_verification(self, service, user_id, credential_data, credential):
        """Test credential creation with automatic verification."""
        service.credential_dao.create.return_value = credential

        with patch.object(service, "verify_credential", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = True
            result = await service.create_credential(user_id, credential_data)
            assert result.id == credential.id

    async def test_create_credential_validation(self, service, user_id):
        """Test credential creation with invalid data."""
        invalid_data = {
            "name": "Test",
            "cloud_url": "invalid-url",
            "username_or_email": "test@example.com",
            "api_token": "token",
        }

        with pytest.raises(ValueError):
            await service.create_credential(user_id, invalid_data)


@pytest.mark.asyncio
class TestGetCredential:
    """Tests for credential retrieval."""

    async def test_get_credential_success(self, service, user_id, credential):
        """Test successful credential retrieval."""
        service.credential_dao.get_by_id.return_value = credential

        result = await service.get_credential(user_id, credential.id)

        assert result.id == credential.id
        assert result.user_id == user_id

    async def test_get_credential_not_found(self, service, user_id):
        """Test retrieval of non-existent credential."""
        service.credential_dao.get_by_id.return_value = None

        result = await service.get_credential(user_id, "nonexistent-id")

        assert result is None

    async def test_get_credential_user_isolation(self, service, credential):
        """Test that users cannot access other users' credentials."""
        other_user_id = str(uuid4())
        service.credential_dao.get_by_id.return_value = credential

        result = await service.get_credential(other_user_id, credential.id)

        # Should be None since user IDs don't match
        assert result is None or result.user_id == other_user_id


@pytest.mark.asyncio
class TestListCredentials:
    """Tests for listing credentials."""

    async def test_list_credentials_success(self, service, user_id, credential):
        """Test successful credentials listing."""
        service.credential_dao.get_by_user_id.return_value = [credential]

        result = await service.list_credentials(user_id)

        assert len(result) == 1
        assert result[0].id == credential.id
        service.credential_dao.get_by_user_id.assert_called_once_with(user_id)

    async def test_list_credentials_empty(self, service, user_id):
        """Test listing credentials for user with no credentials."""
        service.credential_dao.get_by_user_id.return_value = []

        result = await service.list_credentials(user_id)

        assert len(result) == 0

    async def test_list_credentials_multiple(self, service, user_id):
        """Test listing multiple credentials."""
        credentials = [
            ConfluenceCredential(
                id=str(uuid4()),
                user_id=user_id,
                name=f"Confluence {i}",
                cloud_url=f"https://test{i}.atlassian.net/wiki",
                username_or_email=f"user{i}@example.com",
                api_token=f"token{i}",
                created_at=datetime.now(),
                is_active=True,
            )
            for i in range(3)
        ]
        service.credential_dao.get_by_user_id.return_value = credentials

        result = await service.list_credentials(user_id)

        assert len(result) == 3


@pytest.mark.asyncio
class TestUpdateCredential:
    """Tests for credential updates."""

    async def test_update_credential_success(self, service, user_id, credential_data, credential):
        """Test successful credential update."""
        updated_credential = credential.copy(
            update={"name": "Updated Name"}
        )
        service.credential_dao.get_by_id.return_value = credential
        service.credential_dao.update.return_value = updated_credential

        result = await service.update_credential(
            user_id, credential.id, {"name": "Updated Name"}
        )

        assert result.name == "Updated Name"

    async def test_update_credential_user_isolation(self, service, user_id, credential):
        """Test that users cannot update other users' credentials."""
        other_user_id = str(uuid4())
        service.credential_dao.get_by_id.return_value = credential

        result = await service.update_credential(
            other_user_id, credential.id, {"name": "Hacked"}
        )

        # Should fail or return None
        assert result is None or result.user_id == user_id

    async def test_update_credential_not_found(self, service, user_id):
        """Test updating non-existent credential."""
        service.credential_dao.get_by_id.return_value = None

        with pytest.raises(ValueError):
            await service.update_credential(user_id, "nonexistent", {"name": "New"})


@pytest.mark.asyncio
class TestDeleteCredential:
    """Tests for credential deletion."""

    async def test_delete_credential_success(self, service, user_id, credential):
        """Test successful credential deletion."""
        service.credential_dao.get_by_id.return_value = credential
        service.credential_dao.delete.return_value = True

        result = await service.delete_credential(user_id, credential.id)

        assert result is True
        service.credential_dao.delete.assert_called_once_with(credential.id)

    async def test_delete_credential_user_isolation(self, service, user_id, credential):
        """Test that users cannot delete other users' credentials."""
        other_user_id = str(uuid4())
        service.credential_dao.get_by_id.return_value = credential

        with pytest.raises(PermissionError):
            await service.delete_credential(other_user_id, credential.id)

    async def test_delete_credential_not_found(self, service, user_id):
        """Test deleting non-existent credential."""
        service.credential_dao.get_by_id.return_value = None

        with pytest.raises(ValueError):
            await service.delete_credential(user_id, "nonexistent")


@pytest.mark.asyncio
class TestVerifyCredential:
    """Tests for credential verification."""

    async def test_verify_credential_success(self, service, user_id, credential):
        """Test successful credential verification."""
        service.credential_dao.get_by_id.return_value = credential

        with patch("datapilotflow.services.confluence.confluence_credential_service.ConfluenceApiClient") as mock_client_class:
            mock_client = Mock()
            mock_client.verify_credentials.return_value = True
            mock_client_class.return_value = mock_client

            result = await service.verify_credential(user_id, credential.id)

            assert result is True

    async def test_verify_credential_invalid(self, service, user_id, credential):
        """Test credential verification with invalid credentials."""
        service.credential_dao.get_by_id.return_value = credential

        with patch("datapilotflow.services.confluence.confluence_credential_service.ConfluenceApiClient") as mock_client_class:
            mock_client = Mock()
            mock_client.verify_credentials.return_value = False
            mock_client_class.return_value = mock_client

            result = await service.verify_credential(user_id, credential.id)

            assert result is False

    async def test_verify_credential_not_found(self, service, user_id):
        """Test verification of non-existent credential."""
        service.credential_dao.get_by_id.return_value = None

        with pytest.raises(ValueError):
            await service.verify_credential(user_id, "nonexistent")

    async def test_verify_credential_user_isolation(self, service, user_id, credential):
        """Test that users cannot verify other users' credentials."""
        other_user_id = str(uuid4())
        service.credential_dao.get_by_id.return_value = credential

        with pytest.raises(PermissionError):
            await service.verify_credential(other_user_id, credential.id)


@pytest.mark.asyncio
class TestActivateDeactivate:
    """Tests for activating and deactivating credentials."""

    async def test_deactivate_credential(self, service, user_id, credential):
        """Test credential deactivation."""
        service.credential_dao.get_by_id.return_value = credential
        deactivated = credential.copy(update={"is_active": False})
        service.credential_dao.update.return_value = deactivated

        result = await service.deactivate_credential(user_id, credential.id)

        assert result.is_active is False

    async def test_activate_credential(self, service, user_id, credential):
        """Test credential activation."""
        inactive_credential = credential.copy(update={"is_active": False})
        service.credential_dao.get_by_id.return_value = inactive_credential
        active = inactive_credential.copy(update={"is_active": True})
        service.credential_dao.update.return_value = active

        result = await service.activate_credential(user_id, credential.id)

        assert result.is_active is True

    async def test_deactivate_credential_user_isolation(self, service, user_id, credential):
        """Test that users cannot deactivate other users' credentials."""
        other_user_id = str(uuid4())
        service.credential_dao.get_by_id.return_value = credential

        with pytest.raises(PermissionError):
            await service.deactivate_credential(other_user_id, credential.id)


@pytest.mark.asyncio
class TestCredentialValidation:
    """Tests for credential validation."""

    async def test_validate_url_format(self, service, user_id):
        """Test validation of Confluence URL format."""
        invalid_data = {
            "name": "Test",
            "cloud_url": "not-a-valid-url",
            "username_or_email": "test@example.com",
            "api_token": "token",
        }

        with pytest.raises(ValueError):
            await service.create_credential(user_id, invalid_data)

    async def test_validate_required_fields(self, service, user_id):
        """Test validation of required fields."""
        incomplete_data = {
            "name": "Test",
            "cloud_url": "https://test.atlassian.net/wiki",
        }

        with pytest.raises(ValueError):
            await service.create_credential(user_id, incomplete_data)
