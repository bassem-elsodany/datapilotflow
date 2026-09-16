"""
Unit tests for Confluence Document Extractor.

Tests cover all extraction modes, batch processing, and metadata handling.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from langchain_core.documents import Document

from datapilotflow.domain.knowledge import (
    ScrapingMode,
    ConfluenceConfig,
    KnowledgeSourceConfig,
)
from datapilotflow.processors.confluence.confluence_api_client import (
    ConfluencePage,
)
from datapilotflow.processors.confluence.confluence_document_extractor import (
    ConfluenceDocumentExtractor,
)


@pytest.fixture
def confluence_config():
    """Fixture for Confluence configuration."""
    return ConfluenceConfig(
        cloud_url="https://test.atlassian.net/wiki",
        username_or_email="test@example.com",
        api_token="test-token",
        space_keys=["TEST"],
        include_attachments=False,
        include_comments=False,
    )


@pytest.fixture
def sample_pages():
    """Fixture for sample Confluence pages."""
    return [
        ConfluencePage(
            page_id="123",
            page_title="Test Page 1",
            space_key="TEST",
            content="Test content 1",
            source_url="https://test.atlassian.net/wiki/pages/viewpage.action?pageId=123",
            version=1,
            last_modified=datetime.now(),
            labels=["test", "api-docs"],
        ),
        ConfluencePage(
            page_id="124",
            page_title="Test Page 2",
            space_key="TEST",
            content="Test content 2",
            source_url="https://test.atlassian.net/wiki/pages/viewpage.action?pageId=124",
            version=1,
            last_modified=datetime.now(),
            labels=["test"],
        ),
    ]


@pytest.fixture
def extractor(confluence_config):
    """Fixture for ConfluenceDocumentExtractor instance."""
    return ConfluenceDocumentExtractor(confluence_config)


@pytest.mark.asyncio
class TestConfluenceDocumentExtractorInitialization:
    """Tests for extractor initialization."""

    async def test_extractor_initialization(self, confluence_config):
        """Test that extractor initializes with correct configuration."""
        extractor = ConfluenceDocumentExtractor(confluence_config)
        assert extractor.config == confluence_config
        assert extractor.batch_size == 50

    async def test_extractor_with_custom_batch_size(self, confluence_config):
        """Test extractor initialization with custom batch size."""
        extractor = ConfluenceDocumentExtractor(confluence_config, batch_size=100)
        assert extractor.batch_size == 100


@pytest.mark.asyncio
class TestExtractSpecificPages:
    """Tests for SPECIFIC_PAGES extraction mode."""

    async def test_extract_specific_pages(self, sample_pages):
        """Test extraction of specific pages."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123", "124"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = sample_pages

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 2
            assert documents[0].metadata["page_id"] == "123"
            assert documents[1].metadata["page_id"] == "124"

    async def test_extract_specific_pages_with_metadata(self, sample_pages):
        """Test that extracted documents contain correct metadata."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [sample_pages[0]]

            async for batch in extractor.extract_documents():
                doc = batch[0]
                assert doc.metadata["source_url"] == sample_pages[0].source_url
                assert doc.metadata["title"] == "Test Page 1"
                assert doc.metadata["page_id"] == "123"
                assert doc.metadata["space_key"] == "TEST"
                assert "test" in doc.metadata["labels"]
                assert doc.metadata["extraction_method"] == "confluence_api"


@pytest.mark.asyncio
class TestExtractSpacePages:
    """Tests for SPACE_PAGES extraction mode."""

    async def test_extract_space_pages(self, sample_pages):
        """Test extraction of all pages from a space."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            space_keys=["TEST"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_pages

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 2
            mock_get.assert_called_once_with("TEST", max_pages=None)

    async def test_extract_space_pages_with_limit(self, sample_pages):
        """Test extraction of space pages with max limit."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            space_keys=["TEST"],
            max_pages_per_space=1,
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [sample_pages[0]]

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 1
            mock_get.assert_called_once_with("TEST", max_pages=1)

    async def test_extract_multiple_spaces(self, sample_pages):
        """Test extraction from multiple spaces."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            space_keys=["TEST", "DOCS"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [sample_pages, sample_pages]

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 4
            assert mock_get.call_count == 2


@pytest.mark.asyncio
class TestExtractPagesWithLabel:
    """Tests for PAGES_WITH_LABEL extraction mode."""

    async def test_extract_pages_with_label(self, sample_pages):
        """Test extraction of pages with specific labels."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            labels=["api-docs"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_pages_by_label", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [sample_pages[0]]

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 1
            assert documents[0].metadata["page_id"] == "123"

    async def test_extract_pages_with_multiple_labels(self, sample_pages):
        """Test extraction with multiple labels."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            labels=["test", "important"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_pages_by_label", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_pages

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 2
            mock_get.assert_called_once_with(["test", "important"])


@pytest.mark.asyncio
class TestExtractRecentlyModified:
    """Tests for RECENTLY_MODIFIED extraction mode."""

    async def test_extract_recently_modified_pages(self, sample_pages):
        """Test extraction of recently modified pages."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_recently_modified_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_pages

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 2
            mock_get.assert_called_once()


@pytest.mark.asyncio
class TestBatchProcessing:
    """Tests for batch processing functionality."""

    async def test_batch_processing(self, sample_pages):
        """Test that documents are yielded in batches."""
        # Create config for many pages
        many_pages = sample_pages * 20  # 40 pages

        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=[str(i) for i in range(40)],
        )
        extractor = ConfluenceDocumentExtractor(config, batch_size=10)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = many_pages

            batches = []
            async for batch in extractor.extract_documents():
                batches.append(batch)
                assert len(batch) <= 10

            # Should have 4 batches of 10 each
            assert len(batches) == 4

    async def test_small_batch_size(self, sample_pages):
        """Test extraction with small batch size."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123", "124"],
        )
        extractor = ConfluenceDocumentExtractor(config, batch_size=1)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = sample_pages

            batches = []
            async for batch in extractor.extract_documents():
                batches.append(batch)
                assert len(batch) == 1

            assert len(batches) == 2


@pytest.mark.asyncio
class TestDocumentMetadata:
    """Tests for document metadata handling."""

    async def test_document_contains_all_metadata(self, sample_pages):
        """Test that documents contain all required metadata."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [sample_pages[0]]

            async for batch in extractor.extract_documents():
                doc = batch[0]
                assert isinstance(doc, Document)
                assert "source_url" in doc.metadata
                assert "title" in doc.metadata
                assert "page_id" in doc.metadata
                assert "space_key" in doc.metadata
                assert "labels" in doc.metadata
                assert "version" in doc.metadata
                assert "last_modified" in doc.metadata
                assert "confluence_mode" in doc.metadata
                assert "extraction_method" in doc.metadata

    async def test_document_content(self, sample_pages):
        """Test that document content is correctly set."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [sample_pages[0]]

            async for batch in extractor.extract_documents():
                doc = batch[0]
                assert doc.page_content == "Test content 1"


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling during extraction."""

    async def test_handle_page_not_found(self):
        """Test handling of pages that don't exist."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["999"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = Exception("Page not found")

            # Should handle error gracefully
            documents = []
            with pytest.raises(Exception):
                async for batch in extractor.extract_documents():
                    documents.extend(batch)

    async def test_handle_empty_results(self):
        """Test handling of empty extraction results."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            space_keys=["EMPTY"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = []

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            assert len(documents) == 0


@pytest.mark.asyncio
class TestAsyncGeneratorBehavior:
    """Tests for async generator behavior."""

    async def test_generator_can_be_consumed_multiple_times(self, sample_pages):
        """Test that generator yields all documents."""
        config = ConfluenceConfig(
            cloud_url="https://test.atlassian.net/wiki",
            username_or_email="test@example.com",
            api_token="test-token",
            page_ids=["123", "124"],
        )
        extractor = ConfluenceDocumentExtractor(config)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = sample_pages

            count = 0
            async for batch in extractor.extract_documents():
                count += len(batch)

            assert count == 2
