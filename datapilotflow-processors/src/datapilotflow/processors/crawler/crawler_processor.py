"""
Crawler Processor module for handling web crawling and document extraction.
"""

import asyncio
import re
import traceback
import warnings
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig
from langchain_core.documents import Document
from loguru import logger

from datapilotflow.application.data.utils.url_loader import URLLoader
from datapilotflow.config import settings
from datapilotflow.domain.knowledge import KnowledgeJob, KnowledgeSourceConfig

from .crawler_config import (
    CrawlerKnowledgeConfig,
    get_crawler_config,
    get_deep_crawler_strategy,
)

# Suppress Playwright SQLite ResourceWarnings
warnings.filterwarnings("ignore", category=ResourceWarning, module="sqlite3")
warnings.filterwarnings("ignore", category=ResourceWarning, module="inspect")
warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")
warnings.filterwarnings("ignore", category=ResourceWarning, module="concurrent.futures")
warnings.filterwarnings(
    "ignore", message=".*unclosed database.*", category=ResourceWarning
)
warnings.filterwarnings("ignore", message=".*unclosed file.*", category=ResourceWarning)


async def _process_url_with_crawler(
    crawler: AsyncWebCrawler,
    url: str,
    crawler_config: Any,
    knowledge_source_config: KnowledgeSourceConfig,
    duplicate_detector: Optional[Any],
    existing_urls: set,
    current_batch: List[Document],
    total_processed: int,
    knowledge_job: KnowledgeJob,
) -> AsyncGenerator[tuple[List[Document], int], None]:
    """
    Common function to process a single URL using the crawler with depth-based crawling.

    This function uses async for streaming to handle all crawling scenarios:
    - max_depth=0: Only the exact URL (no link following)
    - max_depth>0: URL + links up to specified depth

    Args:
        crawler: The AsyncWebCrawler instance
        url: The URL to process
        crawler_config: Crawler configuration with deep_crawl_strategy
        knowledge_source_config: Knowledge source configuration
        duplicate_detector: Optional duplicate detector
        existing_urls: Set of already processed URLs
        current_batch: Current batch of documents being collected
        total_processed: Total number of documents processed so far
        knowledge_job: Knowledge job for batch size configuration

    Yields:
        tuple: (batch of documents, updated total_processed count)
    """
    import asyncio
    import time

    try:
        logger.debug(f"Processing URL with depth-based crawling: {url}")

        # Track skipped URLs to yield heartbeat periodically
        # This prevents timeout when all URLs are being skipped (duplicates)
        skipped_count = 0
        heartbeat_interval = 50  # Yield empty batch every 50 skipped URLs

        # Time-based heartbeat tracking
        last_heartbeat_time = time.time()
        heartbeat_time_interval = 600  # Send heartbeat every 10 minutes if no activity (long pages can take time)

        # Create crawler result iterator
        crawler_iter = (await crawler.arun(url, config=crawler_config)).__aiter__()

        # Process results with time-based heartbeat
        while True:
            try:
                # Try to get next result with a timeout
                result = await asyncio.wait_for(crawler_iter.__anext__(), timeout=heartbeat_time_interval)
            except asyncio.TimeoutError:
                # No result received within heartbeat interval - send heartbeat and continue
                current_time = time.time()
                if current_time - last_heartbeat_time >= heartbeat_time_interval:
                    logger.info(
                        f"Knowledge Source: {knowledge_source_config.id} | "
                        f"Heartbeat: Crawler is actively working but no results for {heartbeat_time_interval}s. "
                        f"Total processed so far: {total_processed}"
                    )
                    # Yield empty batch as time-based heartbeat
                    yield ([], total_processed)
                    last_heartbeat_time = current_time
                continue  # Continue waiting for next result
            except StopAsyncIteration:
                # Crawler finished normally
                break

            # Reset heartbeat timer when we receive a result
            last_heartbeat_time = time.time()
            try:
                depth = result.metadata.get("depth", 0)
                parent_url = result.metadata.get("parent_url", url)
                logger.debug(
                    f"Knowledge Source: {knowledge_source_config.id} | Source: {url} | Depth: {depth} | Found: {result.url} | Parent: {parent_url}"
                )

                # Check if URL already exists before processing
                if duplicate_detector and result.url in existing_urls:
                    skipped_count += 1
                    logger.debug(
                        f"Knowledge Source: {knowledge_source_config.id} | Skipping existing URL: {result.url}"
                    )

                    # CRITICAL: Yield empty batch periodically to prevent timeout
                    # When skipping many URLs (all duplicates), we need to signal
                    # "I'm alive and working" to the extraction service
                    if skipped_count % heartbeat_interval == 0:
                        logger.info(
                            f"Knowledge Source: {knowledge_source_config.id} | "
                            f"Heartbeat: Skipped {skipped_count} duplicate URLs so far, continuing..."
                        )
                        # Yield empty batch as heartbeat (total_processed unchanged)
                        yield ([], total_processed)

                    continue

                if hasattr(result, "markdown") and result.markdown is not None:
                    logger.debug(
                        f"Knowledge Source: {knowledge_source_config.id} | Processing markdown for {result.url}"
                    )

                    # Safely get title, fallback to URL if not available
                    metadata_obj = result.metadata
                    title = (
                        metadata_obj.get("title")
                        if isinstance(metadata_obj, dict)
                        else None
                    )

                    metadata = {
                        "source_url": result.url,
                        "job_id": (
                            knowledge_job.id
                            if knowledge_job
                            else knowledge_source_config.id
                        ),
                        "title": title,
                    }

                    # Determine content source based on LLM filter configuration
                    if (
                        knowledge_source_config.llm_content_filter_id
                        and knowledge_source_config.llm_content_filter_id.strip()
                    ):
                        # LLM filter enabled - use markdown directly
                        page_content = str(result.markdown)
                        logger.debug("Using markdown content (LLM filter applied)")
                    else:
                        # No LLM filter - use fit_markdown
                        page_content = str(result.markdown.fit_markdown)
                        logger.debug("Using fit_markdown content (no LLM filter)")

                    doc_kwargs = {
                        "page_content": page_content,
                        "metadata": metadata,
                    }
                    doc = Document(**doc_kwargs)

                    current_batch.append(doc)
                    total_processed += 1

                    # CRITICAL: Add URL to existing_urls to prevent within-job duplicates
                    # If the same URL is discovered again later in this job, it will be skipped
                    if duplicate_detector:
                        existing_urls.add(result.url)
                        logger.debug(
                            f"Added {result.url} to existing_urls (now tracking {len(existing_urls)} URLs)"
                        )

                    # Yield batch when it reaches the batch size
                    if len(current_batch) >= knowledge_job.batch_size:
                        logger.debug(
                            f"Yielding batch of {len(current_batch)} documents. Total processed: {total_processed}"
                        )
                        yield (current_batch, total_processed)
                        current_batch = []  # Reset batch

                else:
                    logger.debug(
                        f"Knowledge Source: {knowledge_source_config.id} | Skipping {result.url} - No markdown content available"
                    )

            except Exception as e:
                # Handle individual page errors without stopping the entire crawl
                logger.warning(
                    f"Knowledge Source: {knowledge_source_config.id} | Error processing {result.url if hasattr(result, 'url') else 'unknown URL'}: {e}"
                )
                logger.debug(f"Traceback: {traceback.format_exc()}")
                continue  # Continue with next page

    except asyncio.TimeoutError:
        logger.error(
            f"Knowledge Source: {knowledge_source_config.id} | Timeout while crawling {url}"
        )
        raise
    except Exception as e:
        logger.error(
            f"Knowledge Source: {knowledge_source_config.id} | Error in crawler for {url}: {e}"
        )
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise


async def get_knowledge_source_documents(
    knowledge_source_config: KnowledgeSourceConfig,
    crawler_config: Optional[CrawlerKnowledgeConfig] = None,
    knowledge_job: Optional[KnowledgeJob] = None,
) -> AsyncGenerator[List[Document], None]:
    """Extract documents using the crawl4ai library with batch processing.

    Args:
        knowledge_source_config: KnowledgeSourceConfig object containing source information.
        crawler_config: Optional crawler configuration. If not provided, uses default configuration.
        knowledge_job: Optional knowledge job for job-specific processing.
    Yields:
        List[Document]: Batches of documents extracted using the crawler.

    Raises:
        ValueError: If URL is invalid
        Exception: For other crawler errors
    """
    # For multiple_pages mode, URL might be empty as URLs are in URL source config
    if knowledge_source_config.scraping_mode == "multiple_pages":
        if not knowledge_source_config.url_source_id:
            raise ValueError("URL source ID is required for multiple_pages mode")
    else:
        if not knowledge_source_config.url:
            raise ValueError("URL cannot be empty")

    if not crawler_config:
        crawler_config = CrawlerKnowledgeConfig(
            output_format=knowledge_source_config.output_format,
        )

    current_batch = []
    total_processed = 0
    output_dir = Path(settings.RAG_FILE_UPLOAD_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    # Initialize the files with empty arrays
    markdown_file = output_dir / "markdown_content.json"

    try:
        # Get crawler configuration
        crawler_config = get_crawler_config(
            crawler_config, get_deep_crawler_strategy(crawler_config)
        )
        browser_config = BrowserConfig(headless=True, java_script_enabled=False)

        logger.info(
            f"Starting {knowledge_source_config.scraping_mode} for URL: {knowledge_source_config.url} "
        )

        # Load existing URLs if duplicate checking is enabled
        existing_urls = set()
        duplicate_detector = None
        if knowledge_job and knowledge_job.check_duplicates_before_insert:
            try:
                from datapilotflow.application.data.storage.duplicate_detector import (
                    DuplicateDetector,
                )
                from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
                from datapilotflow.infrastructure.milvus.client import MilvusClientWrapper
                from datapilotflow.services.knowledge.vectordb_collection_service import (
                    get_vectordb_collection_service,
                )

                # Get collection config to initialize Milvus client for duplicate detection
                vectordb_service = get_vectordb_collection_service()
                collection_config = vectordb_service.get_collection(
                    knowledge_job.vectordb_collection_id, knowledge_job.user_id
                )

                if collection_config:
                    # Initialize Milvus client for duplicate detection
                    milvus_client = MilvusClientWrapper(
                        model=KnowledgeChunk,
                        collection_name=collection_config.collection_name,
                        vector_dimension=collection_config.vector_dimension,
                    )

                    duplicate_detector = DuplicateDetector(milvus_client=milvus_client)
                    existing_urls = duplicate_detector.get_existing_urls()
                    logger.info(
                        f"Loaded {len(existing_urls)} existing URLs for duplicate checking from collection {collection_config.collection_name}"
                    )
                else:
                    logger.warning(
                        f"Collection config not found for job {knowledge_job.id}, skipping duplicate detection"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to initialize duplicate detection: {e}. Continuing without duplicate detection."
                )
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Don't raise - continue without duplicate detection

        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                # Determine which URLs to process based on scraping mode
                urls_to_process = []

                if knowledge_source_config.scraping_mode == "single_page":
                    urls_to_process = [knowledge_source_config.url]
                    logger.info(
                        f"Single page mode: processing 1 URL with max_depth={knowledge_source_config.crawl_depth}"
                    )

                elif knowledge_source_config.scraping_mode == "multiple_pages":
                    # Get URL source configuration through the service
                    from datapilotflow.services.knowledge.knowledge_source_service import (
                        get_knowledge_source_service,
                    )

                    knowledge_source_service = get_knowledge_source_service()

                    logger.debug(
                        f"Multiple pages mode - URL source ID: {knowledge_source_config.url_source_id}"
                    )

                    if knowledge_source_config.url_source_id:
                        logger.debug(
                            f"Getting URL source config for ID: {knowledge_source_config.url_source_id}"
                        )
                        url_source_config = (
                            knowledge_source_service.get_url_source_config(
                                knowledge_source_config.url_source_id,
                                knowledge_source_config.user_id,
                            )
                        )
                        if url_source_config:
                            urls_to_process = URLLoader.load_urls(url_source_config)
                            logger.info(
                                f"Multiple pages mode: processing {len(urls_to_process)} URLs with max_depth={knowledge_source_config.crawl_depth}"
                            )
                        else:
                            logger.error(
                                f"Failed to get URL source configuration for {knowledge_source_config.id}"
                            )
                            urls_to_process = [
                                knowledge_source_config.url
                            ]  # Fallback to single URL
                    else:
                        logger.error(
                            f"No URL source ID found for multiple_pages mode in {knowledge_source_config.id}"
                        )
                        urls_to_process = [
                            knowledge_source_config.url
                        ]  # Fallback to single URL

                elif knowledge_source_config.scraping_mode == "website":
                    urls_to_process = [knowledge_source_config.url]
                    logger.info(
                        f"Website crawl mode: starting from {knowledge_source_config.url} with max_depth={knowledge_source_config.crawl_depth}"
                    )

                # Track URLs processed vs skipped for logging
                urls_processed_count = 0
                urls_skipped_count = 0

                # Process each URL using the unified crawler function
                for current_url in urls_to_process:
                    logger.debug(f"Processing URL: {current_url}")

                    # Skip if URL already processed (for multiple_pages mode)
                    if (
                        duplicate_detector
                        and current_url in existing_urls
                        and knowledge_source_config.scraping_mode == "multiple_pages"
                    ):
                        urls_skipped_count += 1
                        logger.debug(
                            f"Knowledge Source: {knowledge_source_config.id} | Skipping already processed URL: {current_url}"
                        )
                        continue

                    # Use the unified crawler function with depth-based crawling
                    urls_processed_count += 1
                    async for batch, processed_count in _process_url_with_crawler(
                        crawler=crawler,
                        url=current_url,
                        crawler_config=crawler_config,
                        knowledge_source_config=knowledge_source_config,
                        duplicate_detector=duplicate_detector,
                        existing_urls=existing_urls,
                        current_batch=current_batch,
                        total_processed=total_processed,
                        knowledge_job=knowledge_job,
                    ):
                        # Update counters
                        current_batch = []  # Batch was already yielded, reset
                        total_processed = processed_count
                        yield batch

                # Log summary of URL processing
                logger.info(
                    f"Knowledge Source: {knowledge_source_config.id} | "
                    f"URL processing complete: {urls_processed_count} URLs processed, "
                    f"{urls_skipped_count} URLs skipped (already exist)"
                )

                # Yield any remaining documents in the final batch
                if current_batch:
                    logger.debug(
                        f"Yielding final batch of {len(current_batch)} documents. Total processed: {total_processed}"
                    )
                    yield current_batch
                elif total_processed == 0:
                    # No documents were processed - this could be because:
                    # 1. All URLs were skipped (duplicates)
                    # 2. No content was found
                    # Log this explicitly and exit gracefully (generator will raise StopAsyncIteration)
                    logger.info(
                        f"Knowledge Source: {knowledge_source_config.id} | "
                        f"Crawling completed with 0 documents processed. "
                        f"URLs processed: {urls_processed_count}, URLs skipped: {urls_skipped_count}. "
                        f"Job completing successfully."
                    )

            except asyncio.TimeoutError:
                logger.error(
                    f"Knowledge Source: {knowledge_source_config.id} | Timeout while crawling"
                )
                # Yield any remaining documents before raising
                if current_batch:
                    yield current_batch
            except Exception as e:
                logger.error(
                    f"Knowledge Source: {knowledge_source_config.id} | Error in crawler session: {e}"
                )
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Yield any remaining documents before raising
                if current_batch:
                    yield current_batch

    except Exception as e:
        logger.error(
            f"Knowledge Source: {knowledge_source_config.id} | Error crawling {knowledge_source_config.url}: {e}"
        )
        logger.debug(f"Traceback: {traceback.format_exc()}")
        # Yield any remaining documents before raising
        if current_batch:
            yield current_batch
        raise

    logger.debug(
        f"Knowledge Source: {knowledge_source_config.id} | Completed processing {knowledge_source_config.url}"
    )
    logger.debug(f"Total documents extracted: {total_processed}")
