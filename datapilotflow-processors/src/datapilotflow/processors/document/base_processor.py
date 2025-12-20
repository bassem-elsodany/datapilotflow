"""
Base document processor module that provides core document processing functionality.
This module serves as the foundation for both web crawling and file processing.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Any, Generator, List, Optional

from langchain_core.documents import Document
from loguru import logger

from datapilotflow.processors.storage.duplicate_detector import DuplicateDetector
from datapilotflow.processors.storage.file_writer import write_enriched_documents_to_file
from datapilotflow.processors.utils import process_chunks_with_cross_reference
from datapilotflow.domain.config import settings


class BaseDocumentProcessor:
    """Base class for document processing that can be extended by web crawlers and file processors."""

    def __init__(self):
        self.processor_type = "base"

    async def process_documents_with_batch_callback(
        self,
        documents_generator,  # Async generator that yields Document batches
        client: Optional[Any] = None,
        batch_callback=None,
        output_file: Optional[Path] = None,
        knowledge_job: Optional[
            Any
        ] = None,  # Optional knowledge job for job-specific processing
        knowledge_source_config: Optional[
            Any
        ] = None,  # Optional knowledge source config
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        """Process documents using the core document processing pipeline.

        This is the core processing logic that both web crawling and file processing use.

        Args:
            documents_generator: Async generator that yields batches of Documents
            client: Optional client object for batch callback
            batch_callback: Optional callback function for batch processing
            output_file: Optional output file path
            knowledge_job: Optional knowledge job for job-specific processing (contains save_to_file and check_duplicates_before_insert settings)
            knowledge_source_config: Optional knowledge source configuration
        """
        logger.info(
            f"Processing documents for knowledge source: {knowledge_source_config.name} using {self.processor_type} processor"
        )

        check_duplicates = (
            knowledge_job.check_duplicates_before_insert if knowledge_job else False
        )
        if check_duplicates:
            logger.info("Duplicate detection enabled - will skip existing documents")
        else:
            logger.info("Duplicate detection disabled - will process all documents")

        # Set up output file path
        write_to_file = knowledge_job.save_to_file if knowledge_job else True
        if write_to_file and output_file is None:
            # Create job-specific directory structure: output_dir/job_id/
            output_dir = (
                Path(settings.RAG_INGESTION_JOBS_OUTPUT_DATA_DIR) / knowledge_job.id
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            # Add timestamp suffix to filename
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                output_dir
                / f"crawl_documents_{knowledge_source_config.id}_{timestamp}.json"
            )

        # Note: Duplicate detector is now created in the document processor (web/file)
        # and passed to the document generator, so we don't need to create it here
        duplicate_detector = None

        try:
            batch_number = 0
            total_processed = 0
            # MEMORY OPTIMIZATION: Only accumulate if writing consolidated file
            all_enriched_docs = [] if knowledge_job.write_consolidated_file else None

            # Initialize incremental consolidated file if requested
            if knowledge_job.write_consolidated_file and output_file:
                # Create empty consolidated file or clear existing one
                if output_file.exists():
                    logger.info(f"Clearing existing consolidated file: {output_file}")
                    output_file.unlink()
                logger.info(
                    f"Initializing incremental consolidated file: {output_file}"
                )

            try:
                # Process documents from the generator
                while True:
                    batch = await documents_generator.__anext__()
                    batch_number += 1
                    total_processed += len(batch)

                    logger.info(
                        f"Processing batch {batch_number} with {len(batch)} documents. Total processed: {total_processed}"
                    )

                    # Filter out existing documents if duplicate detection is enabled
                    if check_duplicates and duplicate_detector:
                        original_batch_size = len(batch)
                        logger.info(
                            f"🔍 DUPLICATE CHECK: Batch {batch_number} - Checking {original_batch_size} documents"
                        )
                        batch = duplicate_detector.filter_new_documents(
                            batch,
                            (
                                knowledge_job.id
                                if knowledge_job
                                else knowledge_source_config.id
                            ),
                        )
                        filtered_count = original_batch_size - len(batch)
                        if filtered_count > 0:
                            logger.warning(
                                f"⚠️  DUPLICATES SKIPPED: Batch {batch_number} - "
                                f"Filtered out {filtered_count} existing documents "
                                f"({len(batch)} new documents will be processed)"
                            )
                        else:
                            logger.info(
                                f"✅ NO DUPLICATES: Batch {batch_number} - All {original_batch_size} documents are new"
                            )

                        if not batch:
                            logger.warning(
                                f"⏭️  SKIPPING BATCH: Batch {batch_number} - All documents already exist in collection"
                            )
                            continue

                    # Process each document: Split → LLM Enrichment → Cross-reference
                    processed_batch = []
                    for doc in batch:
                        # DEBUG: Check document content before chunking
                        logger.debug(
                            f"CHUNKING DEBUG - Document length: {len(doc.page_content)} chars"
                        )

                        # Skip documents with empty or invalid content
                        if (
                            not doc.page_content
                            or not doc.page_content.strip()
                            or len(doc.page_content.strip()) == 0
                        ):
                            logger.warning(
                                f"Skipping document with empty content: {doc.metadata.get('source_url', 'unknown')}"
                            )
                            continue

                        # Step 1: Split document into chunks
                        import re

                        from datapilotflow.processors.splitters import create_splitter
                        from datapilotflow.services.knowledge.document_splitter_service import (
                            get_document_splitter_service,
                        )

                        # Get splitter configuration from job
                        if knowledge_job and knowledge_job.splitter_id:
                            # Use the splitter configuration from the job
                            splitter_service = get_document_splitter_service()
                            splitter_config = splitter_service.get_splitter_for_job(
                                knowledge_job.splitter_id
                            )

                            # Apply job overrides if provided
                            if knowledge_job.custom_chunk_size:
                                splitter_config.chunk_size = (
                                    knowledge_job.custom_chunk_size
                                )
                            if knowledge_job.custom_chunk_overlap:
                                splitter_config.chunk_overlap = (
                                    knowledge_job.custom_chunk_overlap
                                )

                            # Create splitter using the new modular system
                            splitter = create_splitter(splitter_config)
                            chunks = splitter.split(doc.page_content)

                            logger.debug(
                                f"Using splitter '{splitter_config.name}' (type: {splitter_config.splitter_type})"
                            )
                        else:
                            # Fallback to default text splitter
                            logger.debug(
                                "No splitter configuration found, using default text splitter"
                            )
                            from datapilotflow.domain.knowledge.document_splitter import (
                                SplitterType,
                            )
                            from datapilotflow.processors.splitters import create_splitter_by_type

                            # Use provided chunk_size and chunk_overlap or defaults
                            if chunk_size is None:
                                chunk_size = 256
                            if chunk_overlap is None:
                                chunk_overlap = 32

                            splitter = create_splitter_by_type(
                                splitter_type=SplitterType.TEXT,
                                chunk_size=chunk_size,
                                chunk_overlap=chunk_overlap,
                                name="Default Text Splitter",
                            )
                            chunks = splitter.split(doc.page_content)

                        logger.debug(f"CHUNKING DEBUG - Created {len(chunks)} chunks")

                        # Debug each chunk size using token-based comparison
                        for i, chunk in enumerate(chunks):
                            chunk_length = len(chunk.page_content)

                            # Convert chunk to tokens for accurate comparison
                            try:
                                import tiktoken

                                encoding = tiktoken.get_encoding("cl100k_base")
                                chunk_tokens = len(encoding.encode(chunk.page_content))
                                percentage = (
                                    (chunk_tokens / chunk_size) * 100
                                    if chunk_size and chunk_size > 0
                                    else 0
                                )
                                logger.debug(
                                    f"CHUNK {i+1}: {chunk_length} chars ({chunk_tokens} tokens, {percentage:.1f}% of target {chunk_size or 'N/A'} tokens)"
                                )

                                # Show preview of small chunks (only if chunk_size is defined)
                                if chunk_size and chunk_tokens < chunk_size * 0.5:  # Less than 50% of target
                                    logger.warning(
                                        f"SMALL CHUNK {i+1}: {chunk_tokens} tokens (target: {chunk_size} tokens)"
                                    )
                                    logger.debug(
                                        f"Small chunk preview: {chunk.page_content[:100]}..."
                                    )
                                elif chunk_size and chunk_tokens > chunk_size * 1.5:  # More than 150% of target
                                    logger.warning(
                                        f"LARGE CHUNK {i+1}: {chunk_tokens} tokens (target: {chunk_size} tokens)"
                                    )
                                    logger.debug(
                                        f"Large chunk preview: {chunk.page_content[:100]}..."
                                    )
                            except Exception as e:
                                # Fallback to character-based comparison if tiktoken fails
                                logger.warning(
                                    f"Could not calculate tokens for chunk {i+1}: {e}"
                                )
                                percentage = (
                                    (chunk_length / chunk_size) * 100
                                    if chunk_size and chunk_size > 0
                                    else 0
                                )
                                logger.debug(
                                    f"CHUNK {i+1}: {chunk_length} chars ({percentage:.1f}% of target {chunk_size or 'N/A'} - FALLBACK TO CHARS)"
                                )

                        # Step 2: Add cross-reference metadata to chunks
                        chunks_with_cross_ref = process_chunks_with_cross_reference(
                            doc, chunks
                        )
                        processed_batch.extend(chunks_with_cross_ref)

                    # Write files per batch if requested (memory-efficient approach)
                    if write_to_file and processed_batch:
                        # Write all batches to the same consolidated file
                        if batch_number == 1:
                            # First batch: create or clear the file
                            logger.info(f"Creating consolidated file: {output_file}")
                            write_enriched_documents_to_file(
                                processed_batch, output_file
                            )
                        else:
                            # Subsequent batches: append to the same file
                            logger.info(
                                f"Appending {len(processed_batch)} enriched chunks to consolidated file (batch {batch_number})"
                            )
                            write_enriched_documents_to_file(
                                processed_batch, output_file, append=True
                            )

                    # Accumulate for consolidated file if requested
                    if (
                        knowledge_job.write_consolidated_file
                        and all_enriched_docs is not None
                    ):
                        all_enriched_docs.extend(processed_batch)

                    # Write incremental consolidated file if requested
                    if knowledge_job.write_consolidated_file and processed_batch:
                        logger.info(
                            f"Appending {len(processed_batch)} chunks to incremental consolidated file (batch {batch_number})"
                        )
                        write_enriched_documents_to_file(
                            processed_batch, output_file, append=True
                        )

                    # Call the callback function if provided
                    if batch_callback:
                        logger.info(f"Calling batch callback for batch {batch_number}")
                        batch_callback(
                            client, processed_batch, batch_number, total_processed
                        )
                    else:
                        # Default behavior: just log the batch
                        logger.info(
                            f"Batch {batch_number}: {len(processed_batch)} chunks"
                        )
                        for doc in processed_batch:
                            logger.debug(
                                f"  - {doc.metadata.get('source_url', 'Unknown source')} (Chunk ID: {doc.metadata.get('chunk_id', 'No ID')})"
                            )

                    # MEMORY OPTIMIZATION: Clear processed batch to free memory
                    del processed_batch
                    import gc

                    gc.collect()

            except StopAsyncIteration:
                logger.info(
                    f"Completed processing all batches. Total processed: {total_processed}"
                )

                # Write consolidated file if requested
                if (
                    knowledge_job.write_consolidated_file
                    and all_enriched_docs
                    and len(all_enriched_docs) > 0
                ):
                    logger.info(
                        f"Writing {len(all_enriched_docs)} enriched chunks to consolidated file"
                    )
                    write_enriched_documents_to_file(all_enriched_docs, output_file)

                # Log final statistics if duplicate detection was used
                if check_duplicates and duplicate_detector:
                    stats = duplicate_detector.get_processing_stats(
                        total_processed,
                        len(all_enriched_docs) if all_enriched_docs else 0,
                    )
                    logger.info(f"Final processing statistics: {stats}")

        except Exception as e:
            logger.error(
                f"Error processing documents for knowledge source: {knowledge_source_config.name} | Error: {e}"
            )
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            # Clean up duplicate detector
            if duplicate_detector:
                try:
                    duplicate_detector.close()
                    logger.debug("Duplicate detector closed")
                except Exception as e:
                    logger.warning(f"Error closing duplicate detector: {e}")

    def extract_documents(
        self,
        knowledge_source_config: Any = None,
        knowledge_job: Any = None,
        output_file: Optional[Path] = None,
    ) -> list[Document]:
        """Extract documents using the core processing pipeline.

        This method should be implemented by subclasses to provide the document generator.

        Args:
            knowledge_job: Knowledge job object
            knowledge_source_config: Knowledge source configuration object
            output_file: Output file path
        Returns:
            list[Document]: List of processed documents
        """
        raise NotImplementedError("Subclasses must implement extract_documents")
