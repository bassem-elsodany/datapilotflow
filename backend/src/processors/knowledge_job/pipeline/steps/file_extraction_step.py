"""
File Extraction Step.

This step extracts documents from local files based on file type.
Different file types require different processing strategies:
- MD files: Read directly (already markdown)
- PDF/DOCX/TXT: Use FileProcessor to extract markdown
- HTML files: Use crawler with file:// URL
"""

import time
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from langchain_core.documents import Document
from loguru import logger

from src.domain.knowledge.knowledge_source_config import (
    ContentSourceType,
    ScrapingMode,
)
from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult


class FileExtractionStep(PipelineStep):
    """
    Pipeline step for extracting documents from local files.

    Handles different file types with appropriate extraction strategies:
    - Markdown files: Direct read (no conversion needed)
    - PDF/DOCX/TXT files: Extract using FileProcessor
    - HTML files: Process using crawler with file:// URL
    """

    def __init__(self, batch_size: Optional[int] = None):
        """
        Initialize the file extraction step.

        Args:
            batch_size: Number of documents to process per batch (if None, uses job's batch_size)
        """
        super().__init__(name="FileExtraction")
        self.batch_size = batch_size

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have a local files configuration."""
        if not context.knowledge_source_config:
            logger.error("No knowledge source configuration provided")
            return False

        # Check if this is a local files source
        if context.knowledge_source_config.content_source_type != ContentSourceType.LOCAL_FILES:
            logger.error(
                f"Invalid content source type: {context.knowledge_source_config.content_source_type}. "
                f"Expected {ContentSourceType.LOCAL_FILES}"
            )
            return False

        # Check if local_files is configured
        if not context.knowledge_source_config.local_files:
            logger.error("No local files configured in knowledge source")
            return False

        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Extract documents from local files.

        Args:
            context: Job execution context

        Returns:
            StepResult with extracted document count
        """
        try:
            # Use job's batch_size if not set in constructor
            batch_size = self.batch_size if self.batch_size is not None else context.job.batch_size

            logger.info(
                f"Starting file extraction from {len(context.knowledge_source_config.local_files)} files "
                f"with batch_size={batch_size} (job: {context.get_job_id()})"
            )

            start_time = time.time()
            total_documents = 0
            batch_count = 0

            # Extract documents based on scraping mode
            async for batch in self._extract_files(context, batch_size):
                # Store documents in context
                context.documents.extend(batch)
                total_documents += len(batch)
                batch_count += 1

                # Emit progress
                context.emit_status(
                    f"Extracted batch {batch_count}: {len(batch)} documents "
                    f"(total: {total_documents})"
                )

                logger.debug(
                    f"Extraction batch {batch_count}: {len(batch)} documents "
                    f"(total: {total_documents})"
                )

            execution_time = time.time() - start_time

            # Update context stats
            context.update_stats(
                total_documents=total_documents,
                extraction_time_seconds=execution_time,
                extraction_batches=batch_count,
            )

            logger.info(
                f"File extraction completed: {total_documents} documents "
                f"in {execution_time:.2f}s (job: {context.get_job_id()})"
            )

            return StepResult.success_result(
                data={
                    "documents_extracted": total_documents,
                    "batches_processed": batch_count,
                    "extraction_time_seconds": execution_time,
                }
            )

        except Exception as e:
            logger.error(f"File extraction failed: {e}")
            context.add_error(f"Extraction error: {e}")
            return StepResult.failure_result(
                error=f"File extraction failed: {e}"
            )

    async def _extract_files(
        self, context: JobContext, batch_size: int
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract documents from files based on file type.

        Args:
            context: Job execution context
            batch_size: Number of files to process per batch

        Yields:
            List[Document]: Batches of extracted documents
        """
        scraping_mode = context.knowledge_source_config.scraping_mode
        local_files = context.knowledge_source_config.local_files

        logger.info(
            f"Processing {len(local_files)} files with mode: {scraping_mode}, batch_size: {batch_size}"
        )

        # Determine extraction strategy based on scraping mode
        if scraping_mode == ScrapingMode.MARKDOWN_FILES:
            async for batch in self._extract_markdown_files(context, local_files, batch_size):
                yield batch

        elif scraping_mode in [
            ScrapingMode.PDF_FILES,
            ScrapingMode.DOCX_FILES,
            ScrapingMode.TXT_FILES,
        ]:
            async for batch in self._extract_with_file_processor(context, local_files, batch_size):
                yield batch

        elif scraping_mode == ScrapingMode.HTML_FILES:
            async for batch in self._extract_html_files(context, local_files, batch_size):
                yield batch

        else:
            logger.error(f"Unsupported scraping mode: {scraping_mode}")
            raise ValueError(f"Unsupported scraping mode: {scraping_mode}")

    async def _extract_markdown_files(
        self, context: JobContext, local_files: List[dict], batch_size: int
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract markdown files by reading them directly.

        Args:
            context: Job execution context
            local_files: List of file metadata dicts
            batch_size: Number of files to process per batch

        Yields:
            List[Document]: Batches of documents
        """
        documents = []

        for file_info in local_files:
            file_path_str = file_info.get("file_path")
            if not file_path_str:
                logger.warning(f"Skipping file with no file_path: {file_info}")
                continue

            file_path = Path(file_path_str)

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            try:
                logger.debug(f"Reading markdown file: {file_path}")

                # Read markdown content directly
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    logger.warning(f"Empty content in file: {file_path}")
                    continue

                # Create document with metadata
                metadata = {
                    "source_url": str(file_path),
                    "knowledge_source": context.knowledge_source_config.id,
                    "title": file_info.get("original_filename", file_path.name),
                    "file_type": "markdown",
                    "original_filename": file_info.get("original_filename", file_path.name),
                    "extraction_method": "direct_read",
                    "user_id": context.knowledge_source_config.user_id,
                }

                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

                # Yield batch when we reach batch_size
                if len(documents) >= batch_size:
                    yield documents
                    documents = []

            except Exception as e:
                logger.error(f"Error reading markdown file {file_path}: {e}")
                continue

        # Yield remaining documents
        if documents:
            yield documents

    async def _extract_with_file_processor(
        self, context: JobContext, local_files: List[dict], batch_size: int
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract PDF/DOCX/TXT files using FileProcessor.

        Args:
            context: Job execution context
            local_files: List of file metadata dicts
            batch_size: Number of files to process per batch

        Yields:
            List[Document]: Batches of documents
        """
        from src.processors.document.file_processor import FileProcessor

        processor = FileProcessor()
        documents = []

        for file_info in local_files:
            file_path_str = file_info.get("file_path")
            if not file_path_str:
                logger.warning(f"Skipping file with no file_path: {file_info}")
                continue

            file_path = Path(file_path_str)

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            try:
                logger.debug(f"Extracting markdown from file: {file_path}")

                # Extract markdown using FileProcessor
                markdown_content = processor.extract_markdown(file_path)

                if not markdown_content.strip():
                    logger.warning(f"No content extracted from file: {file_path}")
                    continue

                # Detect file type
                file_type = file_path.suffix.lower().lstrip(".")

                # Create document with metadata
                metadata = {
                    "source_url": str(file_path),
                    "knowledge_source": context.knowledge_source_config.id,
                    "title": file_info.get("original_filename", file_path.name),
                    "file_type": file_type,
                    "original_filename": file_info.get("original_filename", file_path.name),
                    "extraction_method": "file_processor",
                    "user_id": context.knowledge_source_config.user_id,
                }

                doc = Document(page_content=markdown_content, metadata=metadata)
                documents.append(doc)

                # Yield batch when we reach batch_size
                if len(documents) >= batch_size:
                    yield documents
                    documents = []

            except Exception as e:
                logger.error(f"Error extracting file {file_path}: {e}")
                continue

        # Yield remaining documents
        if documents:
            yield documents

    async def _extract_html_files(
        self, context: JobContext, local_files: List[dict], batch_size: int
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract HTML files using crawler with file:// URLs.

        Args:
            context: Job execution context
            local_files: List of file metadata dicts
            batch_size: Number of files to process per batch

        Yields:
            List[Document]: Batches of documents
        """
        from crawl4ai import AsyncWebCrawler

        from src.processors.crawler.crawler_config import get_crawler_config

        # Get crawler configuration
        crawler_config = get_crawler_config(
            knowledge_source_config=context.knowledge_source_config,
            max_depth=0,  # No link following for local files
            allowed_domains=[],
            blocked_domains=[],
            url_patterns=[],
            target_elements=context.knowledge_source_config.target_elements or [],
            content_filter_threshold=context.knowledge_source_config.content_filter_threshold,
            scraping_mode=context.knowledge_source_config.scraping_mode,
            output_format=context.knowledge_source_config.output_format,
        )

        documents = []

        async with AsyncWebCrawler(verbose=False) as crawler:
            for file_info in local_files:
                file_path_str = file_info.get("file_path")
                if not file_path_str:
                    logger.warning(f"Skipping file with no file_path: {file_info}")
                    continue

                file_path = Path(file_path_str)

                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                try:
                    logger.debug(f"Crawling HTML file: {file_path}")

                    # Create file:// URL
                    file_url = f"file://{file_path.absolute()}"

                    # Crawl the local HTML file
                    result = await crawler.arun(url=file_url, config=crawler_config)

                    if not result.markdown or not result.markdown.strip():
                        logger.warning(f"No content extracted from HTML file: {file_path}")
                        continue

                    # Create document with metadata
                    metadata = {
                        "source_url": str(file_path),
                        "knowledge_source": context.knowledge_source_config.id,
                        "title": file_info.get("original_filename", file_path.name),
                        "file_type": "html",
                        "original_filename": file_info.get("original_filename", file_path.name),
                        "extraction_method": "crawler",
                        "user_id": context.knowledge_source_config.user_id,
                    }

                    doc = Document(page_content=result.markdown, metadata=metadata)
                    documents.append(doc)

                    # Yield batch when we reach batch_size
                    if len(documents) >= batch_size:
                        yield documents
                        documents = []

                except Exception as e:
                    logger.error(f"Error crawling HTML file {file_path}: {e}")
                    continue

        # Yield remaining documents
        if documents:
            yield documents
