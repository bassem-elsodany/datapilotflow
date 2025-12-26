"""
Unit tests for Confluence API Client.

Tests cover all extraction modes, error handling, and pagination.
"""

import pytest
from datetime import datetime
from typing import List
from unittest.mock import Mock, patch, MagicMock
import base64

from datapilotflow.processors.confluence.confluence_api_client import (
    ConfluenceApiClient,
    ConfluencePage,
    ConfluenceAuthenticationError,
    ConfluenceRateLimitError,
    ConfluenceServerError,
    ConfluencePageNotFoundError,
)


@pytest.fixture
def confluence_config():
    """Fixture for test Confluence configuration."""
    return {
        "cloud_url": "https://test.atlassian.net/wiki",
        "username_or_email": "test@example.com",
        "api_token": "test-token-123",
    }


@pytest.fixture
def api_client(confluence_config):
    """Fixture for ConfluenceApiClient instance."""
    return ConfluenceApiClient(**confluence_config)


class TestConfluenceApiClientInitialization:
    """Tests for API client initialization."""

    def test_client_initialization(self, confluence_config):
        """Test that client initializes with correct configuration."""
        client = ConfluenceApiClient(**confluence_config)
        assert client.cloud_url == "https://test.atlassian.net/wiki"
        assert client.username_or_email == "test@example.com"
        assert client.api_token == "test-token-123"

    def test_base_url_construction(self, api_client):
        """Test that base URL is correctly constructed."""
        expected_url = "https://test.atlassian.net/wiki/rest/api/content"
        assert api_client.base_url == expected_url

    def test_auth_header_construction(self, api_client):
        """Test that Basic Auth header is correctly constructed."""
        header = api_client._get_auth_header()
        # Verify it contains Bearer token
        assert "Authorization" in header
        assert header["Authorization"].startswith("Bearer ")


class TestVerifyCredentials:
    """Tests for credential verification."""

    @patch("requests.get")
    def test_verify_credentials_success(self, mock_get, api_client):
        """Test successful credential verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user": {"accountId": "123"}}
        mock_get.return_value = mock_response

        result = api_client.verify_credentials()
        assert result is True

    @patch("requests.get")
    def test_verify_credentials_invalid(self, mock_get, api_client):
        """Test credential verification with invalid credentials."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        with pytest.raises(ConfluenceAuthenticationError):
            api_client.verify_credentials()

    @patch("requests.get")
    def test_verify_credentials_server_error(self, mock_get, api_client):
        """Test credential verification with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with pytest.raises(ConfluenceServerError):
            api_client.verify_credentials()


class TestGetSpacePages:
    """Tests for fetching pages from a space."""

    @patch("requests.get")
    def test_get_space_pages_success(self, mock_get, api_client):
        """Test successful space pages retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=123"},
                    "metadata": {"labels": {"results": []}},
                }
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_space_pages("TEST")
        assert len(pages) == 1
        assert pages[0].page_id == "123"
        assert pages[0].page_title == "Test Page"
        assert pages[0].space_key == "TEST"

    @patch("requests.get")
    def test_get_space_pages_with_limit(self, mock_get, api_client):
        """Test space pages retrieval with max_pages limit."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": str(i),
                    "title": f"Page {i}",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": f"/pages/viewpage.action?pageId={i}"},
                    "metadata": {"labels": {"results": []}},
                }
                for i in range(5)
            ],
            "start": 0,
            "limit": 25,
            "size": 5,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_space_pages("TEST", max_pages=3)
        assert len(pages) == 3

    @patch("requests.get")
    def test_get_space_pages_pagination(self, mock_get, api_client):
        """Test space pages retrieval handles pagination."""
        # First call
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = {
            "results": [
                {
                    "id": "1",
                    "title": "Page 1",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=1"},
                    "metadata": {"labels": {"results": []}},
                }
            ],
            "start": 0,
            "limit": 1,
            "size": 1,
            "isLast": False,
        }

        # Second call
        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = {
            "results": [
                {
                    "id": "2",
                    "title": "Page 2",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=2"},
                    "metadata": {"labels": {"results": []}},
                }
            ],
            "start": 1,
            "limit": 1,
            "size": 1,
            "isLast": True,
        }

        mock_get.side_effect = [response1, response2]

        pages = api_client.get_space_pages("TEST")
        assert len(pages) == 2
        assert pages[0].page_id == "1"
        assert pages[1].page_id == "2"

    @patch("requests.get")
    def test_get_space_pages_not_found(self, mock_get, api_client):
        """Test space pages retrieval when space doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Space not found"
        mock_get.return_value = mock_response

        with pytest.raises(ConfluencePageNotFoundError):
            api_client.get_space_pages("NONEXISTENT")


class TestGetPageById:
    """Tests for fetching a specific page by ID."""

    @patch("requests.get")
    def test_get_page_by_id_success(self, mock_get, api_client):
        """Test successful page retrieval by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
            "body": {"storage": {"value": "<p>Content</p>"}},
            "links": {"webui": "/pages/viewpage.action?pageId=123"},
            "metadata": {"labels": {"results": []}},
        }
        mock_get.return_value = mock_response

        page = api_client.get_page_by_id("123")
        assert page.page_id == "123"
        assert page.page_title == "Test Page"

    @patch("requests.get")
    def test_get_page_by_id_not_found(self, mock_get, api_client):
        """Test page retrieval when page doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Page not found"
        mock_get.return_value = mock_response

        with pytest.raises(ConfluencePageNotFoundError):
            api_client.get_page_by_id("999")


class TestGetPagesByLabel:
    """Tests for fetching pages by label."""

    @patch("requests.get")
    def test_get_pages_by_label_success(self, mock_get, api_client):
        """Test successful pages retrieval by label."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=123"},
                    "metadata": {"labels": {"results": [{"name": "api-docs"}]}},
                }
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_pages_by_label(["api-docs"])
        assert len(pages) == 1
        assert pages[0].page_id == "123"
        assert "api-docs" in pages[0].labels

    @patch("requests.get")
    def test_get_pages_by_multiple_labels(self, mock_get, api_client):
        """Test pages retrieval with multiple labels."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=123"},
                    "metadata": {
                        "labels": {
                            "results": [{"name": "api-docs"}, {"name": "important"}]
                        }
                    },
                }
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_pages_by_label(["api-docs", "important"])
        assert len(pages) == 1
        assert len(pages[0].labels) == 2


class TestGetRecentlyModifiedPages:
    """Tests for fetching recently modified pages."""

    @patch("requests.get")
    def test_get_recently_modified_pages_success(self, mock_get, api_client):
        """Test successful recently modified pages retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": "/pages/viewpage.action?pageId=123"},
                    "metadata": {"labels": {"results": []}},
                }
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_recently_modified_pages()
        assert len(pages) == 1
        assert pages[0].page_id == "123"

    @patch("requests.get")
    def test_get_recently_modified_pages_with_limit(self, mock_get, api_client):
        """Test recently modified pages with custom limit."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": str(i),
                    "title": f"Page {i}",
                    "space": {"key": "TEST"},
                    "version": {"number": 1, "when": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "links": {"webui": f"/pages/viewpage.action?pageId={i}"},
                    "metadata": {"labels": {"results": []}},
                }
                for i in range(10)
            ],
            "start": 0,
            "limit": 10,
            "size": 10,
            "isLast": True,
        }
        mock_get.return_value = mock_response

        pages = api_client.get_recently_modified_pages(limit=5)
        assert len(pages) == 5


class TestRateLimiting:
    """Tests for rate limiting handling."""

    @patch("requests.get")
    def test_rate_limit_error_handling(self, mock_get, api_client):
        """Test that 429 responses raise rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too many requests"
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        with pytest.raises(ConfluenceRateLimitError):
            api_client.verify_credentials()


class TestStorageFormatConversion:
    """Tests for XHTML to Markdown conversion."""

    def test_convert_basic_xhtml_to_markdown(self):
        """Test conversion of basic XHTML to markdown."""
        xhtml = "<p>Hello <strong>world</strong></p>"
        markdown = ConfluenceApiClient._convert_storage_to_markdown(xhtml)
        assert "Hello" in markdown
        assert "world" in markdown

    def test_convert_xhtml_with_links(self):
        """Test conversion of XHTML with links."""
        xhtml = '<p><a href="https://example.com">link</a></p>'
        markdown = ConfluenceApiClient._convert_storage_to_markdown(xhtml)
        assert "link" in markdown
        assert "example.com" in markdown

    def test_convert_xhtml_with_lists(self):
        """Test conversion of XHTML with lists."""
        xhtml = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        markdown = ConfluenceApiClient._convert_storage_to_markdown(xhtml)
        assert "Item 1" in markdown
        assert "Item 2" in markdown

    def test_convert_xhtml_with_code(self):
        """Test conversion of XHTML with code blocks."""
        xhtml = '<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[print("hello")]]></ac:plain-text-body></ac:structured-macro>'
        markdown = ConfluenceApiClient._convert_storage_to_markdown(xhtml)
        assert "print" in markdown


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @patch("requests.get")
    def test_connection_error_handling(self, mock_get, api_client):
        """Test handling of connection errors."""
        mock_get.side_effect = ConnectionError("Network error")

        with pytest.raises(ConfluenceServerError):
            api_client.verify_credentials()

    @patch("requests.get")
    def test_timeout_error_handling(self, mock_get, api_client):
        """Test handling of timeout errors."""
        mock_get.side_effect = TimeoutError("Request timeout")

        with pytest.raises(ConfluenceServerError):
            api_client.verify_credentials()

    @patch("requests.get")
    def test_malformed_response_handling(self, mock_get, api_client):
        """Test handling of malformed API responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with pytest.raises(ConfluenceServerError):
            api_client.verify_credentials()
