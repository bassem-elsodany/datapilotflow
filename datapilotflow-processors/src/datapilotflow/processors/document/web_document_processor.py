"""
Document processing module for handling document extraction and batch processing.
This is the main orchestration module that coordinates between different specialized modules.
"""

import asyncio
import mimetypes
import time
import traceback
from pathlib import Path
from typing import Any, Generator, List, Optional

from langchain_core.documents import Document
from loguru import logger
from tqdm import tqdm

from datapilotflow.application.data.storage.duplicate_detector import DuplicateDetector
from datapilotflow.application.data.storage.file_writer import write_enriched_documents_to_file
from datapilotflow.application.data.utils import process_chunks_with_cross_reference
from datapilotflow.config import settings
from datapilotflow.domain.knowledge import KnowledgeSourceConfig
from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob
from datapilotflow.processors.crawler import (
    CrawlerKnowledgeConfig,
    get_knowledge_source_documents,
)

from .base_processor import BaseDocumentProcessor


class WebDocumentProcessor(BaseDocumentProcessor):
    """Web/HTML document processor that extends the base document processor."""

    def __init__(self):
        super().__init__()
        self.processor_type = "web"

    def get_web_documents(
        self,
        knowledge_source_config: KnowledgeSourceConfig,
        knowledge_job: Optional[KnowledgeJob] = None,
    ):
        # Resolve LLM content filter configuration if present
        llm_content_filter_config = None
        if knowledge_source_config.llm_content_filter_id:
            try:
                from datapilotflow.services.knowledge.llm_content_filter_service import (
                    get_llm_content_filter_service,
                )

                llm_filter_service = get_llm_content_filter_service()
                llm_filter = llm_filter_service.get_config(
                    knowledge_source_config.llm_content_filter_id,
                    knowledge_source_config.user_id,
                )
                if llm_filter:
                    # Resolve provider name from provider ID
                    provider = (
                        llm_filter_service.model_provider_service.get_model_provider(
                            llm_filter.llm_provider_id, knowledge_source_config.user_id
                        )
                    )
                    provider_name = provider.name if provider else "openai"

                    llm_content_filter_config = {
                        "provider_name": provider_name,
                        "llm_model_name": llm_filter.llm_model_name,
                        "api_token": provider.api_key,
                        "base_url": provider.endpoint,
                        "temperature": llm_filter.temperature,
                        "max_retries": llm_filter.max_retries,
                        "timeout_seconds": llm_filter.timeout_seconds,
                        "instruction": llm_filter.instruction,
                        "chunk_token_threshold": llm_filter.chunk_token_threshold,
                        "verbose": llm_filter.verbose,
                    }
            except Exception as e:
                logger.error(
                    f"Failed to resolve LLM content filter {knowledge_source_config.llm_content_filter_id}: {e}"
                )

        # Use the existing get_knowledge_source_documents function
        return get_knowledge_source_documents(
            knowledge_source_config=knowledge_source_config,
            crawler_config=CrawlerKnowledgeConfig(
                max_depth=knowledge_source_config.crawl_depth,
                allowed_domains=knowledge_source_config.allowed_subdomains,
                blocked_domains=knowledge_source_config.blocked_subdomains,
                url_patterns=knowledge_source_config.url_patterns,
                target_elements=knowledge_source_config.target_elements,
                content_filter_threshold=knowledge_source_config.content_filter_threshold,
                scraping_mode=knowledge_source_config.scraping_mode,
                output_format=knowledge_source_config.output_format,
                llm_content_filter_config=llm_content_filter_config,
            ),
            knowledge_job=knowledge_job,
        )

    async def process_knowledge_source_with_batch_callback(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        client: Optional[Any] = None,
        batch_callback=None,
        output_file: Optional[Path] = None,
        check_duplicates: bool = True,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        """Process a web/HTML knowledge source using the batch processing pipeline."""
        logger.debug(
            f"[WebDocumentProcessor] FUNCTION CALLED: process_knowledge_source_with_batch_callback"
        )
        logger.debug(
            f"[WebDocumentProcessor] Processing knowledge source: {knowledge_source_config.name} | URL: {knowledge_source_config.url} | check_duplicates: {check_duplicates}"
        )
        logger.debug(
            f"[WebDocumentProcessor] LLM content filter ID: {getattr(knowledge_source_config, 'llm_content_filter_id', 'NOT_FOUND')}"
        )

        # Note: Duplicate detection is now handled inside get_knowledge_source_documents
        # based on knowledge_job.check_duplicates_before_insert

        documents_generator = self.get_web_documents(
            knowledge_source_config=knowledge_source_config,
            knowledge_job=knowledge_job,
        )
        await self.process_documents_with_batch_callback(
            documents_generator=documents_generator,
            client=client,
            batch_callback=batch_callback,
            output_file=output_file,
            knowledge_job=knowledge_job,  # Pass knowledge_job for job-specific processing
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            knowledge_source_config=knowledge_source_config,  # Pass knowledge_source_config
        )
        logger.debug(
            f"[WebDocumentProcessor] Completed processing knowledge source: {knowledge_source_config.name}"
        )


# Instantiate a single processor instance for reuse
_web_processor = WebDocumentProcessor()


async def extract_with_batch_processing_callback(
    knowledge_job: KnowledgeJob,
    knowledge_source_config: KnowledgeSourceConfig,
    client: Optional[Any] = None,
    batch_callback=None,
    output_file: Optional[Path] = None,
    check_duplicates: bool = True,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> None:
    """Extract documents for a single knowledge source with batch processing callback.
    (Refactored: Uses WebDocumentProcessor internally for safety and extensibility.)
    """
    logger.debug(
        f"extract_with_batch_processing_callback for job {knowledge_job.id} Using WebDocumentProcessor... | knowledge: {knowledge_source_config.id} | check_duplicates: {check_duplicates}"
    )
    try:
        await _web_processor.process_knowledge_source_with_batch_callback(
            knowledge_job=knowledge_job,
            knowledge_source_config=knowledge_source_config,
            client=client,
            batch_callback=batch_callback,
            output_file=output_file,
            check_duplicates=check_duplicates,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except Exception as e:
        logger.error(f"Error in process_knowledge_source_with_batch_callback: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def get_file_type(file_path: Path) -> str:
    """Get the file type from file extension.

    Args:
        file_path: Path to the file

    Returns:
        str: File type (pdf, doc, docx, xml, txt, etc.)
    """
    return file_path.suffix.lower().lstrip(".")


def create_file_knowledge_source(
    file_path: Path, user_id: str, original_filename: str, file_type: str = None
) -> KnowledgeSourceConfig:
    """Create a Knowledge source for an uploaded file.

    This function creates a Knowledge object that can be processed by the existing
    document processing pipeline using Crawl4AI's file processing capabilities.

    Args:
        file_path: Path to the uploaded file
        user_id: ID of the user who uploaded the file
        original_filename: Original filename from the upload
        file_type: File type (if None, will be detected from extension)

    Returns:
        Knowledge: Knowledge object configured for file processing
    """
    if file_type is None:
        file_type = get_file_type(file_path)

    # Generate unique knowledge ID
    timestamp = int(time.time())
    knowledge_id = f"file_{user_id}_{file_path.stem}_{timestamp}"

    # Create file URL (Crawl4AI can handle file:// URLs)
    file_url = f"file://{file_path.absolute()}"

    return KnowledgeSourceConfig(
        id=knowledge_id,
        name=f"Uploaded {file_type.upper()}: {original_filename}",
        description=f"User uploaded {file_type} file: {original_filename}",
        url=file_url,  # Crawl4AI will process this file URL
        enabled=True,
        scraping_mode="single_page",  # Single file processing
        allowed_subdomains=[],  # Not applicable for files
        blocked_subdomains=[],  # Not applicable for files
        url_patterns=[],  # Not applicable for files
        crawl_depth=0,  # Single file
        css_selector="",  # Not applicable for files
        content_filter_threshold=0.6,
    )


def process_uploaded_file(
    knowledge_job: KnowledgeJob,
    file_path: Path,
    user_id: str,
    original_filename: str,
    client: Optional[Any] = None,
    batch_callback=None,
    write_to_file: bool = True,
    output_file: Optional[Path] = None,
    check_duplicates: bool = False,
) -> None:
    """Process uploaded file using existing document processor infrastructure.

    This function leverages the existing document processing pipeline to handle
    uploaded files (PDF, DOC, DOCX, XML, etc.) using Crawl4AI's file processing.

    Args:
        file_path: Path to the uploaded file
        user_id: ID of the user who uploaded the file
        original_filename: Original filename from the upload
        client: Optional client object for batch callback
        batch_callback: Optional callback function for batch processing
        write_to_file: Whether to write results to file
        output_file: Output file path (if None, uses default)
        check_duplicates: Whether to check for duplicates (usually False for files)
    """
    logger.debug(f"Processing uploaded file: {original_filename} for user: {user_id}")

    # Step 1: Create knowledge source for the file
    knowledge = create_file_knowledge_source(
        file_path=file_path, user_id=user_id, original_filename=original_filename
    )

    logger.debug(f"Created knowledge source: {knowledge.id} for file: {file_path}")

    # Step 2: Use existing processing pipeline
    extract_with_batch_processing_callback(
        knowledge_job=knowledge_job,
        knowledge_source_config=knowledge,
        client=client,
        batch_callback=batch_callback,
        output_file=output_file,
        check_duplicates=check_duplicates,
    )

    logger.info(f"Completed processing file: {original_filename}")


def process_uploaded_files_batch(
    files: List[
        tuple[Path, str, str]
    ],  # List of (file_path, user_id, original_filename)
    client: Optional[Any] = None,
    batch_callback=None,
    write_to_file: bool = True,
    check_duplicates: bool = False,
) -> None:
    """Process multiple uploaded files in batch.

    Args:
        files: List of tuples containing (file_path, user_id, original_filename)
        client: Optional client object for batch callback
        batch_callback: Optional callback function for batch processing
        write_to_file: Whether to write results to file
        check_duplicates: Whether to check for duplicates
    """
    logger.info(f"Processing batch of {len(files)} uploaded files")

    for i, (file_path, user_id, original_filename) in enumerate(files, 1):
        logger.info(f"Processing file {i}/{len(files)}: {original_filename}")

        try:
            process_uploaded_file(
                file_path=file_path,
                user_id=user_id,
                original_filename=original_filename,
                client=client,
                batch_callback=batch_callback,
                write_to_file=write_to_file,
                check_duplicates=check_duplicates,
            )
        except Exception as e:
            logger.error(f"Failed to process file {original_filename}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue with next file
            continue

    logger.info(f"Completed processing batch of {len(files)} files")


def get_extraction_generator(
    knowledge_source_configs: list[KnowledgeSourceConfig],
    check_duplicates: bool = True,
    knowledge_job: Optional[KnowledgeJob] = None,
) -> Generator[tuple[KnowledgeSourceConfig, list[Document]], None, None]:
    """Extract documents for a list of knowledge sources, yielding one at a time.

    Args:
        knowledge_source_configs: A list of KnowledgeSourceConfig objects containing knowledge source information.
        check_duplicates: Whether to check for existing documents before processing them.

    Yields:
        tuple[KnowledgeSourceConfig, list[Document]]: A tuple containing the knowledge source object and a list of
            documents extracted for that knowledge source.
    """
    logger.info(
        f"Extracting documents for {len(knowledge_source_configs)} knowledge sources | check_duplicates: {check_duplicates}"
    )
    progress_bar = tqdm(
        knowledge_source_configs,
        desc="Extracting docs",
        unit="knowledge source",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
        ncols=100,
        position=0,
        leave=True,
    )

    for knowledge_source_config in progress_bar:
        logger.info(
            f"Knowledge source: {knowledge_source_config.name} | URL: {knowledge_source_config.url}"
        )
        if not knowledge_source_config.enabled:
            logger.info(
                f"Skipping disabled knowledge source: {knowledge_source_config.name}"
            )
            continue
        progress_bar.set_postfix_str(
            f"Knowledge source: {knowledge_source_config.name}"
        )

        # Initialize duplicate detector for this knowledge source if needed
        duplicate_detector = None
        if check_duplicates:
            try:
                duplicate_detector = DuplicateDetector()
                duplicate_detector.initialize_clients()
                logger.info(
                    f"Duplicate detector initialized for {knowledge_source_config.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize duplicate detector for {knowledge_source_config.name}: {e}"
                )
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise e

        # MEMORY OPTIMIZATION: Process documents in smaller batches to avoid memory buildup
        batch_size = knowledge_source_config.batch_size
        if batch_size is None:
            batch_size = 20

        chunk_size = knowledge_source_config.chunk_size
        if chunk_size is None:
            chunk_size = 1024

        chunk_overlap = knowledge_source_config.chunk_overlap
        if chunk_overlap is None:
            chunk_overlap = 128

        all_docs = []
        loop = asyncio.get_event_loop()

        # Note: LLM content filter resolution is now handled in get_web_documents method
        async_gen = get_knowledge_source_documents(
            knowledge_source_config=knowledge_source_config,
            crawler_config=CrawlerKnowledgeConfig(
                max_depth=knowledge_source_config.crawl_depth,
                allowed_domains=knowledge_source_config.allowed_subdomains,
                blocked_domains=knowledge_source_config.blocked_subdomains,
                url_patterns=knowledge_source_config.url_patterns,
                target_elements=knowledge_source_config.target_elements,
                content_filter_threshold=knowledge_source_config.content_filter_threshold,
                scraping_mode=knowledge_source_config.scraping_mode,
                output_format=knowledge_source_config.output_format,
            ),
            knowledge_job=knowledge_job,
        )

        try:
            while True:
                batch = loop.run_until_complete(async_gen.__anext__())
                all_docs.extend(batch)
                logger.info(
                    f"Processed batch of {len(batch)} documents. Total so far: {len(all_docs)}"
                )

                # MEMORY OPTIMIZATION: Process in smaller chunks to avoid memory buildup
                if (
                    len(all_docs) >= batch_size * 2
                ):  # Process when we have enough documents
                    logger.info(
                        f"Processing intermediate batch of {len(all_docs)} documents"
                    )

                    # Process each document: Split → LLM Enrichment → Cross-reference
                    all_chunks = []
                    for doc in all_docs:
                        # Step 1: Split document into chunks
                        from datapilotflow.domain.knowledge.document_splitter import SplitterType
                        from datapilotflow.processors.splitters import (
                            create_splitter,
                            create_splitter_by_type,
                        )
                        from datapilotflow.services.knowledge.document_splitter_service import (
                            get_document_splitter_service,
                        )

                        # Use job's splitter configuration if available
                        if knowledge_job and knowledge_job.splitter_id:
                            # Use the splitter configuration from the job
                            splitter_service = get_document_splitter_service()
                            splitter_config = splitter_service.get_splitter_for_job(
                                knowledge_job.splitter_id
                            )

                            # Create splitter using the new modular system
                            splitter = create_splitter(splitter_config)
                            logger.debug(
                                f"Using job splitter '{splitter_config.name}' (type: {splitter_config.splitter_type})"
                            )
                        else:
                            logger.error(
                                f"No splitter configuration found for job {knowledge_job.id}"
                            )
                            raise ValueError(
                                f"No splitter configuration found for job {knowledge_job.id}"
                            )

                        chunks = splitter.split(doc.page_content)

                        # Step 2: Add cross-reference metadata to chunks
                        chunks_with_cross_ref = process_chunks_with_cross_reference(
                            doc, chunks
                        )

                        # Step 3: Use chunks without LLM enrichment (simplified pipeline)
                        logger.info(
                            f"Using {len(chunks_with_cross_ref)} chunks for {knowledge_source_config.name} without LLM enrichment"
                        )
                        all_chunks.extend(chunks_with_cross_ref)

                    # Yield the processed chunks and clear memory
                    yield (knowledge_source_config, all_chunks)

                    # MEMORY OPTIMIZATION: Clear processed documents to free memory
                    del all_docs
                    del all_chunks
                    all_docs = []
                    import gc

                    gc.collect()

        except StopAsyncIteration:
            pass  # All batches processed

        # Process remaining documents
        if all_docs:
            logger.info(f"Processing final batch of {len(all_docs)} documents")

            # Process each document: Split → LLM Enrichment → Cross-reference
            all_chunks = []
            for doc in all_docs:
                # Step 1: Split document into chunks
                from datapilotflow.domain.knowledge.document_splitter import SplitterType
                from datapilotflow.processors.splitters import (
                    create_splitter,
                    create_splitter_by_type,
                )
                from datapilotflow.services.knowledge.document_splitter_service import (
                    get_document_splitter_service,
                )

                # Use job's splitter configuration if available
                if knowledge_job and knowledge_job.splitter_id:
                    # Use the splitter configuration from the job
                    splitter_service = get_document_splitter_service()
                    splitter_config = splitter_service.get_splitter_for_job(
                        knowledge_job.splitter_id
                    )

                    # Create splitter using the new modular system
                    splitter = create_splitter(splitter_config)
                    logger.debug(
                        f"Using job splitter '{splitter_config.name}' (type: {splitter_config.splitter_type})"
                    )
                else:
                    # Fallback to default text splitter with provided parameters
                    splitter = create_splitter_by_type(
                        splitter_type=SplitterType.TEXT,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        name="Web Document Processor Splitter",
                    )
                    logger.debug("Using default text splitter (no job configuration)")

                chunks = splitter.split(doc.page_content)

                # Step 2: Add cross-reference metadata to chunks
                chunks_with_cross_ref = process_chunks_with_cross_reference(doc, chunks)

                # Step 3: Use chunks without LLM enrichment (simplified pipeline)
                logger.info(
                    f"Using {len(chunks_with_cross_ref)} chunks for {knowledge_source_config.name} without LLM enrichment"
                )
                all_chunks.extend(chunks_with_cross_ref)

            # Yield the final processed chunks
            yield (knowledge_source_config, all_chunks)

            # MEMORY OPTIMIZATION: Clear final batch to free memory
            del all_docs
            del all_chunks
            import gc

            gc.collect()

        # Clean up duplicate detector for this knowledge source
        if duplicate_detector:
            try:
                duplicate_detector.close()
                logger.debug(
                    f"Duplicate detector closed for {knowledge_source_config.name}"
                )
            except Exception as e:
                logger.warning(
                    f"Error closing duplicate detector for {knowledge_source_config.name}: {e}"
                )


def extract(
    knowledge_job: KnowledgeJob,
    knowledge_source_config: KnowledgeSourceConfig,
    write_to_file: bool = True,
    output_file: Optional[Path] = None,
    check_duplicates: bool = True,
) -> list[Document]:
    """Extract documents for a single knowledge source from all sources and deduplicate them.
    (Refactored: Uses WebDocumentProcessor internally for safety and extensibility.)
    """
    logger.info("[extract] Using WebDocumentProcessor...")
    # Use the batch callback version to process and collect all documents
    all_docs = []

    def collect_batch(client, batch, batch_number, total_processed):
        all_docs.extend(batch)

    extract_with_batch_processing_callback(
        knowledge_job=knowledge_job,
        knowledge_source_config=knowledge_source_config,
        client=None,
        batch_callback=collect_batch,
        output_file=output_file,
        check_duplicates=check_duplicates,
    )
    return all_docs
