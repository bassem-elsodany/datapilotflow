"""
Confluence Document Extractor Service.

This service provides a clean async generator interface for extracting documents
from Confluence using the API, following the same pattern as web scraping extraction.
"""

from typing import AsyncGenerator, List, Optional

from langchain_core.documents import Document
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob
from datapilotflow.domain.knowledge.knowledge_source_config import (
    ConfluenceConfig,
    ScrapingMode,
    KnowledgeSourceConfig,
)

from .confluence_api_client import (
    ConfluenceApiClient,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    ConfluenceRateLimitError,
    ConfluenceServerError,
)
from .confluence_markdown_converter import convert_confluence_xhtml_to_markdown


class ConfluenceDocumentExtractor:
    """
    Service for extracting documents from Confluence using the API.

    Provides a clean async generator interface that yields batches of documents
    without any chunking or embedding processing, matching the interface of
    web document extraction.
    """

    async def extract_documents(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        batch_size: int = 100,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract documents from Confluence as an async generator.

        Routes to the appropriate extraction method based on confluence_mode:
        - SPECIFIC_PAGES: Fetch specific page IDs
        - SPACE_PAGES: Fetch all pages in specific spaces
        - PAGES_WITH_LABEL: Fetch pages matching labels
        - RECENTLY_MODIFIED: Fetch recently modified pages

        Args:
            knowledge_job: The job configuration
            knowledge_source_config: The knowledge source configuration
            batch_size: Target batch size for yielding

        Yields:
            List[Document]: Batches of extracted documents

        Raises:
            ValueError: If configuration is invalid
            ConfluenceAuthenticationError: If authentication fails
            ConfluenceServerError: If server errors occur
        """
        if not knowledge_source_config.confluence_config:
            raise ValueError(
                "confluence_config is required for Confluence extraction"
            )

        config = knowledge_source_config.confluence_config
        scraping_mode = knowledge_source_config.scraping_mode
        logger.info(
            f"[GENERATOR] Starting Confluence document extraction "
            f"(job: {knowledge_job.id}, mode: {scraping_mode}, "
            f"url: {config.cloud_url})"
        )

        # Create API client and verify credentials
        async with ConfluenceApiClient(config) as client:
            try:
                await client.verify_credentials()
            except ConfluenceAuthenticationError as e:
                logger.error(f"Confluence authentication failed: {e}")
                raise

            # Route based on extraction mode
            if scraping_mode == ScrapingMode.SPECIFIC_PAGES:
                async for batch in self._extract_specific_pages(
                    client, config, batch_size
                ):
                    yield batch

            elif scraping_mode == ScrapingMode.SPACE_PAGES:
                async for batch in self._extract_space_pages(
                    client, config, batch_size
                ):
                    yield batch

            elif scraping_mode == ScrapingMode.PAGES_WITH_LABEL:
                async for batch in self._extract_pages_with_label(
                    client, config, batch_size
                ):
                    yield batch

            elif scraping_mode == ScrapingMode.RECENTLY_MODIFIED:
                async for batch in self._extract_recently_modified(
                    client, config, batch_size
                ):
                    yield batch

            else:
                raise ValueError(
                    f"Unknown Confluence mode: {scraping_mode}"
                )

        logger.info(
            f"[GENERATOR] Completed Confluence document extraction "
            f"for job: {knowledge_job.id}"
        )

    async def _extract_specific_pages(
        self,
        client: ConfluenceApiClient,
        config: ConfluenceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract specific pages by ID.

        Args:
            client: Confluence API client
            config: Confluence configuration
            batch_size: Batch size for yielding

        Yields:
            List[Document]: Batches of documents
        """
        if not config.page_ids:
            logger.warning("No page IDs specified for specific_pages mode")
            return

        logger.info(
            f"Extracting {len(config.page_ids)} specific pages from Confluence"
        )

        batch = []
        for page_id in config.page_ids:
            try:
                page = await client.get_page_by_id(
                    page_id,
                    expand_children=config.expand_child_pages,
                )
                doc = self._confluence_page_to_document(page, config, ScrapingMode.SPECIFIC_PAGES)
                batch.append(doc)

                if len(batch) >= batch_size:
                    logger.debug(f"Yielding batch of {len(batch)} documents")
                    yield batch
                    batch = []

            except ConfluencePageNotFoundError:
                logger.warning(f"Page not found: {page_id}")
            except ConfluenceRateLimitError:
                logger.warning(
                    "Rate limit exceeded, waiting before retrying..."
                )
                # Could add exponential backoff here
                raise

        # Yield remaining documents
        if batch:
            logger.debug(f"Yielding final batch of {len(batch)} documents")
            yield batch

    async def _extract_space_pages(
        self,
        client: ConfluenceApiClient,
        config: ConfluenceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract all pages from specific spaces.

        Args:
            client: Confluence API client
            config: Confluence configuration
            batch_size: Batch size for yielding

        Yields:
            List[Document]: Batches of documents
        """
        if not config.space_keys:
            logger.warning("No space keys specified for space_pages mode")
            return

        logger.info(
            f"Extracting pages from {len(config.space_keys)} spaces"
        )

        batch = []
        for space_key in config.space_keys:
            try:
                pages = await client.get_space_pages(
                    space_key,
                    max_pages=config.max_pages_per_space,
                )
                logger.info(
                    f"Fetched {len(pages)} pages from space: {space_key}"
                )

                for page in pages:
                    doc = self._confluence_page_to_document(page, config, ScrapingMode.SPACE_PAGES)
                    batch.append(doc)

                    if len(batch) >= batch_size:
                        logger.debug(
                            f"Yielding batch of {len(batch)} documents"
                        )
                        yield batch
                        batch = []

            except ConfluencePageNotFoundError:
                logger.warning(f"Space not found: {space_key}")
            except ConfluenceRateLimitError:
                logger.warning(
                    "Rate limit exceeded, waiting before retrying..."
                )
                raise

        # Yield remaining documents
        if batch:
            logger.debug(f"Yielding final batch of {len(batch)} documents")
            yield batch

    async def _extract_pages_with_label(
        self,
        client: ConfluenceApiClient,
        config: ConfluenceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract pages matching specific labels.

        Args:
            client: Confluence API client
            config: Confluence configuration
            batch_size: Batch size for yielding

        Yields:
            List[Document]: Batches of documents
        """
        if not config.labels:
            logger.warning("No labels specified for pages_with_label mode")
            return

        logger.info(f"Searching for pages with labels: {config.labels}")

        try:
            pages = await client.get_pages_by_label(config.labels)
            logger.info(f"Found {len(pages)} pages matching labels")

            batch = []
            for page in pages:
                doc = self._confluence_page_to_document(page, config, ScrapingMode.PAGES_WITH_LABEL)
                batch.append(doc)

                if len(batch) >= batch_size:
                    logger.debug(
                        f"Yielding batch of {len(batch)} documents"
                    )
                    yield batch
                    batch = []

            # Yield remaining documents
            if batch:
                logger.debug(
                    f"Yielding final batch of {len(batch)} documents"
                )
                yield batch

        except ConfluenceRateLimitError:
            logger.warning("Rate limit exceeded while searching labels")
            raise

    async def _extract_recently_modified(
        self,
        client: ConfluenceApiClient,
        config: ConfluenceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract recently modified pages.

        Args:
            client: Confluence API client
            config: Confluence configuration
            batch_size: Batch size for yielding

        Yields:
            List[Document]: Batches of documents
        """
        logger.info("Fetching recently modified pages from Confluence")

        try:
            pages = await client.get_recently_modified_pages(limit=250)
            logger.info(f"Found {len(pages)} recently modified pages")

            batch = []
            for page in pages:
                doc = self._confluence_page_to_document(page, config, ScrapingMode.RECENTLY_MODIFIED)
                batch.append(doc)

                if len(batch) >= batch_size:
                    logger.debug(
                        f"Yielding batch of {len(batch)} documents"
                    )
                    yield batch
                    batch = []

            # Yield remaining documents
            if batch:
                logger.debug(
                    f"Yielding final batch of {len(batch)} documents"
                )
                yield batch

        except ConfluenceRateLimitError:
            logger.warning(
                "Rate limit exceeded while fetching recently modified pages"
            )
            raise

    @staticmethod
    def _confluence_page_to_document(
        page, config: ConfluenceConfig, scraping_mode: Optional[ScrapingMode] = None
    ) -> Document:
        """
        Convert a ConfluencePage to a LangChain Document.

        Args:
            page: ConfluencePage object
            config: Confluence configuration
            scraping_mode: The scraping mode used for extraction

        Returns:
            Document: LangChain Document with metadata
        """
        # Convert content to markdown if requested
        page_content = page.content
        output_format = config.output_format if hasattr(config, 'output_format') else 'html'
        markdown_generation = config.markdown_generation if hasattr(config, 'markdown_generation') else None

        if output_format == 'markdown' or markdown_generation:
            try:
                page_content = convert_confluence_xhtml_to_markdown(page.content)
                logger.debug(
                    f"Converted page {page.page_id} to markdown "
                    f"({len(page.content)} -> {len(page_content)} chars)"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to convert page {page.page_id} to markdown, using HTML: {e}"
                )
                # Keep original HTML content if conversion fails

        metadata = {
            "source_url": page.url,
            "title": page.title,
            "page_id": page.page_id,
            "space_key": page.space_key,
            "labels": page.labels,
            "version": page.version,
            "last_modified": page.last_modified,
            "confluence_mode": scraping_mode.value if scraping_mode else "unknown",
            "knowledge_source": config.cloud_url,
            "extraction_method": "confluence_api",
            "output_format": output_format,
            "content_type": "markdown" if page_content != page.content and output_format == 'markdown' else "html",
        }

        return Document(
            page_content=page_content,
            metadata=metadata,
        )
