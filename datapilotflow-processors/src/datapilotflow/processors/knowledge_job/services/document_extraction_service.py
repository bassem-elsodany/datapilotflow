"""
Document Extraction Service - Clean async generator interface (NO CALLBACKS).

This service provides a clean async generator interface for extracting documents
from knowledge sources (both web scraping and local files), eliminating the callback-based approach.

This service routes to the appropriate extraction method based on content_source_type:
- LOCAL_FILES: Uses FileExtractionStep logic
- WEB_SCRAPING: Uses web crawler
"""

import time
from typing import AsyncGenerator, List, Optional

from langchain_core.documents import Document
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob
from datapilotflow.domain.knowledge.knowledge_source_config import (
    ContentSourceType,
    KnowledgeSourceConfig,
)
from datapilotflow.processors.crawler import (
    CrawlerKnowledgeConfig,
    get_knowledge_source_documents,
)
from datapilotflow.processors.knowledge_job.orchestration.job_context import JobContext


class DocumentExtractionService:
    """
    Service for extracting documents using clean async generators (NO CALLBACKS).

    This service provides a direct async generator interface that yields batches
    of raw documents without any chunking or embedding processing.
    """

    async def extract_documents(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        batch_size: int = 100,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract documents as an async generator (NO CALLBACKS).

        Routes to the appropriate extraction method based on content_source_type:
        - LOCAL_FILES: Delegates to FileExtractionStep logic
        - WEB_SCRAPING: Uses web crawler

        Args:
            knowledge_job: The job configuration
            knowledge_source_config: The knowledge source configuration
            batch_size: Target batch size for yielding

        Yields:
            List[Document]: Batches of extracted documents
        """
        logger.info(
            f"[GENERATOR] Starting document extraction for {knowledge_source_config.name} "
            f"(job: {knowledge_job.id}, source_type: {knowledge_source_config.content_source_type}, "
            f"scraping_mode: {knowledge_source_config.scraping_mode})"
        )

        # Route based on content source type
        if knowledge_source_config.content_source_type == ContentSourceType.LOCAL_FILES:
            # Extract from local files using FileExtractionStep logic
            async for batch in self._extract_from_local_files(
                knowledge_job, knowledge_source_config, batch_size
            ):
                yield batch
        elif (
            knowledge_source_config.content_source_type
            == ContentSourceType.WEB_SCRAPING
        ):
            # Extract from web using crawler
            async for batch in self._extract_from_web(
                knowledge_job, knowledge_source_config, batch_size
            ):
                yield batch
        else:
            raise ValueError(
                f"Unsupported content_source_type: {knowledge_source_config.content_source_type}"
            )

    async def _extract_from_local_files(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract documents from local files.

        Delegates to FileExtractionStep's extraction logic.

        Args:
            knowledge_job: The job configuration
            knowledge_source_config: The knowledge source configuration (LOCAL_FILES)
            batch_size: Target batch size for yielding

        Yields:
            List[Document]: Batches of extracted documents
        """
        logger.info(
            f"[LOCAL FILES] Extracting from local files with mode: {knowledge_source_config.scraping_mode}"
        )

        # Create a context for FileExtractionStep
        from datapilotflow.processors.knowledge_job.pipeline.steps.file_extraction_step import (
            FileExtractionStep,
        )

        # Create FileExtractionStep instance
        file_extraction_step = FileExtractionStep(batch_size=batch_size)

        # Create a minimal context for extraction
        context = JobContext(
            job=knowledge_job,
            knowledge_source_config=knowledge_source_config,
            user_id=knowledge_source_config.user_id,
        )

        # Delegate to FileExtractionStep's _extract_files method
        async for batch in file_extraction_step._extract_files(context, batch_size):
            yield batch

    async def _extract_from_web(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        batch_size: int,
    ) -> AsyncGenerator[List[Document], None]:
        """
        Extract documents from web sources using the crawler.

        Args:
            knowledge_job: The job configuration
            knowledge_source_config: The knowledge source configuration (WEB_SCRAPING)
            batch_size: Target batch size for yielding

        Yields:
            List[Document]: Batches of extracted documents
        """
        logger.info(
            f"[WEB SCRAPING] Using web crawler for mode: {knowledge_source_config.scraping_mode}"
        )

        start_time = time.time()
        total_documents = 0
        batch_count = 0

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
                    logger.debug(
                        f"[GENERATOR] Configured LLM content filter: {llm_filter.llm_model_name}"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to resolve LLM content filter {knowledge_source_config.llm_content_filter_id}: {e}"
                )

        # Get documents from crawler as async generator
        documents_generator = get_knowledge_source_documents(
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

        # Yield batches directly from crawler with timeout protection
        try:
            import asyncio

            # Timeout for receiving batches from crawler
            # This timeout applies to receiving ANY batch (including empty heartbeat batches)
            # If crawler yields empty batches as heartbeat, timeout is reset
            batch_timeout = 1800  # 30 minutes - crawler should yield heartbeat if skipping many URLs (long pages need time)

            logger.info(
                f"[GENERATOR] Starting batch extraction with {batch_timeout}s timeout per batch"
            )

            # Create the generator iterator once
            generator_iter = documents_generator.__aiter__()

            # Iterate with timeout protection
            while True:
                try:
                    # Wait for next batch with timeout
                    batch = await asyncio.wait_for(
                        generator_iter.__anext__(), timeout=batch_timeout
                    )

                    # Empty batch = heartbeat signal from crawler (e.g., skipping duplicates)
                    # This resets the timeout counter, distinguishing between:
                    # - Real timeout: Crawler hung, no batches (including empty) for 600s
                    # - Normal operation: Crawler actively skipping, yields empty batches periodically
                    if not batch:
                        logger.debug(
                            "[GENERATOR] Received heartbeat batch (empty) - crawler is alive, "
                            "likely skipping duplicate URLs. Continuing..."
                        )
                        continue

                    # Filter out documents with empty content
                    valid_documents = [
                        doc
                        for doc in batch
                        if doc.page_content and doc.page_content.strip()
                    ]

                    if not valid_documents:
                        logger.warning(
                            f"[GENERATOR] Batch {batch_count + 1}: All documents had empty content, skipping"
                        )
                        continue

                    batch_count += 1
                    total_documents += len(valid_documents)

                    logger.info(
                        f"[GENERATOR] Yielding batch {batch_count}: {len(valid_documents)} documents "
                        f"(total: {total_documents})"
                    )

                    # Yield the batch directly
                    yield valid_documents

                except StopAsyncIteration:
                    # Generator exhausted normally
                    logger.info(
                        f"[GENERATOR] Extraction complete: {batch_count} batches, {total_documents} documents"
                    )
                    break

                except asyncio.TimeoutError:
                    # Timeout waiting for next batch - crawler is hung
                    # This is a REAL ERROR (not a heartbeat), so we need to raise it
                    # to let the orchestrator know the job failed
                    logger.error(
                        f"[GENERATOR] TIMEOUT: No batch received for {batch_timeout}s. "
                        f"Crawler appears hung or no heartbeat received. "
                        f"Successfully yielded: {batch_count} batches, {total_documents} documents before timeout."
                    )
                    # Re-raise to propagate error to orchestrator
                    raise

        except Exception as e:
            logger.error(f"[GENERATOR] Error during document extraction: {e}")
            raise

        execution_time = time.time() - start_time
        logger.info(
            f"[GENERATOR] Document extraction completed: {total_documents} documents "
            f"in {batch_count} batches ({execution_time:.2f}s)"
        )


# Singleton instance
_document_extraction_service: Optional[DocumentExtractionService] = None


def get_document_extraction_service() -> DocumentExtractionService:
    """Get the singleton document extraction service instance."""
    global _document_extraction_service

    if _document_extraction_service is None:
        _document_extraction_service = DocumentExtractionService()

    return _document_extraction_service
