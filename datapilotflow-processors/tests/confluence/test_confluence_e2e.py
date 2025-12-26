"""
End-to-end tests for Confluence integration pipeline.

Tests complete workflow from job creation through document extraction.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

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
from datapilotflow.processors.knowledge_job.services.document_extraction_service import (
    DocumentExtractionService,
)


@pytest.fixture
def job_id():
    """Fixture for job ID."""
    return str(uuid4())


@pytest.fixture
def confluence_config():
    """Fixture for Confluence configuration."""
    return ConfluenceConfig(
        cloud_url="https://test.atlassian.net/wiki",
        username_or_email="test@example.com",
        api_token="test-token",
        space_keys=["TECH", "DOCS"],
        include_attachments=False,
        include_comments=False,
    )


@pytest.fixture
def sample_pages():
    """Fixture for sample pages from different spaces."""
    pages = []
    for space in ["TECH", "DOCS"]:
        for i in range(3):
            pages.append(
                ConfluencePage(
                    page_id=f"{space}-{i}",
                    page_title=f"{space} Page {i}",
                    space_key=space,
                    content=f"Content for {space} page {i}",
                    source_url=f"https://test.atlassian.net/wiki/pages/viewpage.action?pageId={space}-{i}",
                    version=1,
                    last_modified=datetime.now(),
                    labels=[space.lower(), "documentation"],
                )
            )
    return pages


@pytest.mark.asyncio
class TestConfluencePipelineE2E:
    """End-to-end tests for complete Confluence pipeline."""

    async def test_complete_extraction_workflow(
        self, job_id, confluence_config, sample_pages
    ):
        """Test complete extraction workflow from config to documents."""
        extractor = ConfluenceDocumentExtractor(confluence_config, batch_size=25)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            # Return different pages for each space
            mock_get.side_effect = [sample_pages[:3], sample_pages[3:]]

            all_documents = []
            batch_count = 0

            async for batch in extractor.extract_documents():
                batch_count += 1
                all_documents.extend(batch)

                # Verify batch structure
                assert len(batch) <= extractor.batch_size
                for doc in batch:
                    assert doc.page_content is not None
                    assert doc.metadata["space_key"] in ["TECH", "DOCS"]

            # Verify we got all documents
            assert len(all_documents) == 6
            assert batch_count == 1  # All fit in one batch

    async def test_multi_space_extraction(self, confluence_config, sample_pages):
        """Test extraction from multiple spaces."""
        extractor = ConfluenceDocumentExtractor(confluence_config, batch_size=50)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [sample_pages[:3], sample_pages[3:]]

            documents = []
            async for batch in extractor.extract_documents():
                documents.extend(batch)

            # Verify documents from both spaces
            space_keys = {doc.metadata["space_key"] for doc in documents}
            assert space_keys == {"TECH", "DOCS"}

            # Verify space page counts
            tech_pages = [d for d in documents if d.metadata["space_key"] == "TECH"]
            docs_pages = [d for d in documents if d.metadata["space_key"] == "DOCS"]
            assert len(tech_pages) == 3
            assert len(docs_pages) == 3

    async def test_large_batch_processing(self, confluence_config):
        """Test processing of large number of pages."""
        # Create 250 pages
        large_pages = [
            ConfluencePage(
                page_id=f"page-{i}",
                page_title=f"Page {i}",
                space_key="LARGE",
                content=f"Content {i}",
                source_url=f"https://test.atlassian.net/wiki/pages/viewpage.action?pageId=page-{i}",
                version=1,
                last_modified=datetime.now(),
                labels=["large-test"],
            )
            for i in range(250)
        ]

        config = confluence_config.copy(
            update={"space_keys": ["LARGE"]}
        )
        extractor = ConfluenceDocumentExtractor(config, batch_size=50)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = large_pages

            all_documents = []
            batch_sizes = []

            async for batch in extractor.extract_documents():
                all_documents.extend(batch)
                batch_sizes.append(len(batch))

            # Verify all documents processed
            assert len(all_documents) == 250

            # Verify batch size constraints
            assert all(size <= 50 for size in batch_sizes)
            assert len(batch_sizes) == 5  # 250 / 50 = 5 batches

    async def test_metadata_consistency_across_batches(
        self, confluence_config, sample_pages
    ):
        """Test that metadata is consistent across batches."""
        config = confluence_config.copy(
            update={"confluence_mode": ScrapingMode.SPECIFIC_PAGES, "page_ids": [p.page_id for p in sample_pages]}
        )
        extractor = ConfluenceDocumentExtractor(config, batch_size=1)

        with patch.object(
            extractor.api_client, "get_page_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = sample_pages

            async for batch in extractor.extract_documents():
                for doc in batch:
                    # Verify required metadata fields
                    required_fields = [
                        "source_url",
                        "title",
                        "page_id",
                        "space_key",
                        "labels",
                        "version",
                        "last_modified",
                        "confluence_mode",
                        "extraction_method",
                    ]
                    for field in required_fields:
                        assert field in doc.metadata
                        assert doc.metadata[field] is not None

    async def test_mode_specific_metadata(self, sample_pages):
        """Test that extraction mode is correctly recorded in metadata."""
        modes = [
            (
                ScrapingMode.SPECIFIC_PAGES,
                {"page_ids": ["page-1"]},
            ),
            (
                ScrapingMode.SPACE_PAGES,
                {"space_keys": ["TEST"]},
            ),
            (
                ScrapingMode.PAGES_WITH_LABEL,
                {"labels": ["test"]},
            ),
            (
                ScrapingMode.RECENTLY_MODIFIED,
                {},
            ),
        ]

        for mode, extra_config in modes:
            config = ConfluenceConfig(
                cloud_url="https://test.atlassian.net/wiki",
                username_or_email="test@example.com",
                api_token="test-token",
                confluence_mode=mode,
                **extra_config
            )
            extractor = ConfluenceDocumentExtractor(config)

            # Mock different API methods based on mode
            if mode == ScrapingMode.SPECIFIC_PAGES:
                with patch.object(
                    extractor.api_client, "get_page_by_id", new_callable=AsyncMock
                ) as mock_get:
                    mock_get.return_value = sample_pages[0]
                    async for batch in extractor.extract_documents():
                        doc = batch[0]
                        assert doc.metadata["confluence_mode"] == mode.value
            elif mode == ScrapingMode.SPACE_PAGES:
                with patch.object(
                    extractor.api_client, "get_space_pages", new_callable=AsyncMock
                ) as mock_get:
                    mock_get.return_value = [sample_pages[0]]
                    async for batch in extractor.extract_documents():
                        doc = batch[0]
                        assert doc.metadata["confluence_mode"] == mode.value
            elif mode == ScrapingMode.PAGES_WITH_LABEL:
                with patch.object(
                    extractor.api_client, "get_pages_by_label", new_callable=AsyncMock
                ) as mock_get:
                    mock_get.return_value = [sample_pages[0]]
                    async for batch in extractor.extract_documents():
                        doc = batch[0]
                        assert doc.metadata["confluence_mode"] == mode.value
            elif mode == ScrapingMode.RECENTLY_MODIFIED:
                with patch.object(
                    extractor.api_client,
                    "get_recently_modified_pages",
                    new_callable=AsyncMock,
                ) as mock_get:
                    mock_get.return_value = [sample_pages[0]]
                    async for batch in extractor.extract_documents():
                        doc = batch[0]
                        assert doc.metadata["confluence_mode"] == mode.value


@pytest.mark.asyncio
class TestPipelineErrorRecovery:
    """Tests for error handling and recovery in pipeline."""

    async def test_partial_page_failure_recovery(self, confluence_config, sample_pages):
        """Test pipeline continues when some pages fail."""
        extractor = ConfluenceDocumentExtractor(confluence_config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [
                sample_pages[:3],
                Exception("Space access denied"),
            ]

            documents = []
            with pytest.raises(Exception):
                async for batch in extractor.extract_documents():
                    documents.extend(batch)

            # Should have extracted first batch before error
            assert len(documents) == 3

    async def test_timeout_handling(self, confluence_config):
        """Test handling of timeout during extraction."""
        extractor = ConfluenceDocumentExtractor(confluence_config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = TimeoutError("Request timed out")

            with pytest.raises(TimeoutError):
                async for batch in extractor.extract_documents():
                    pass

    async def test_empty_space_handling(self, confluence_config):
        """Test handling of spaces with no pages."""
        config = confluence_config.copy(
            update={"space_keys": ["EMPTY"]}
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
class TestPipelinePerformance:
    """Tests for pipeline performance characteristics."""

    async def test_memory_efficiency_with_batching(self, confluence_config):
        """Test that memory usage stays reasonable with large datasets."""
        # Create 1000 pages
        large_pages = [
            ConfluencePage(
                page_id=f"page-{i}",
                page_title=f"Page {i}",
                space_key="PERF",
                content=f"Content {i}" * 100,  # Larger content
                source_url=f"https://test.atlassian.net/wiki/pages/viewpage.action?pageId=page-{i}",
                version=1,
                last_modified=datetime.now(),
                labels=["performance-test"],
            )
            for i in range(1000)
        ]

        config = confluence_config.copy(
            update={"space_keys": ["PERF"]}
        )
        extractor = ConfluenceDocumentExtractor(config, batch_size=100)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = large_pages

            total_documents = 0
            batch_count = 0

            async for batch in extractor.extract_documents():
                batch_count += 1
                total_documents += len(batch)

            assert total_documents == 1000
            assert batch_count == 10  # 1000 / 100 = 10 batches

    async def test_api_call_efficiency(self, confluence_config):
        """Test that API is called efficiently (not redundantly)."""
        extractor = ConfluenceDocumentExtractor(confluence_config)

        with patch.object(
            extractor.api_client, "get_space_pages", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = []

            async for batch in extractor.extract_documents():
                pass

            # Should be called once per space
            assert mock_get.call_count == 2  # TECH and DOCS spaces


@pytest.mark.asyncio
class TestDocumentExtractionService:
    """Tests for document extraction service routing."""

    async def test_confluence_routing(self, confluence_config):
        """Test that service routes Confluence sources correctly."""
        service = DocumentExtractionService()

        with patch(
            "datapilotflow.processors.knowledge_job.services.document_extraction_service.ConfluenceDocumentExtractor"
        ) as mock_extractor_class:
            mock_extractor = AsyncMock()
            mock_extractor.extract_documents = AsyncMock()
            mock_extractor_class.return_value = mock_extractor

            # Mock the async generator
            async def mock_generator():
                yield []

            mock_extractor.extract_documents.return_value = mock_generator()

            # Call service with Confluence config
            async for batch in service._extract_from_confluence(
                confluence_config
            ):
                pass

            mock_extractor_class.assert_called_once()
