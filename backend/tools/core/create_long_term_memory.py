"""
Long-term Memory Creation Tool for SkillPilot RAG System

This module provides a CLI tool for creating and testing long-term memory
in the SkillPilot RAG (Retrieval-Augmented Generation) system using Weaviate as the vector store.

The tool processes knowledge sources (such as MuleSoft documentation)
and creates searchable vector embeddings in Weaviate with graph-enhanced capabilities.
It includes memory optimization features and comprehensive monitoring capabilities.

Key Features:
- Weaviate vector store with graph-enhanced search capabilities
- Memory usage monitoring and optimization
- Configurable batch processing
- LLM enrichment with model instance balancing
- Comprehensive logging and error handling
- Duplicate detection and prevention

Usage Examples:
    # Basic usage with default settings
    python -m tools.core.create_long_term_memory

    # Process with custom batch size and workers
    python -m tools.core.create_long_term_memory --batch-size 200 --llm-workers 30

    # Memory-optimized processing (recommended for large datasets)
    python -m tools.core.create_long_term_memory --batch-size 5 --llm-workers 1 --disable-llm-enrichment

    # Clear existing data and reprocess
    python -m tools.core.create_long_term_memory --clear-first

    # Enable duplicate checking
    python -m tools.core.create_long_term_memory --check-duplicates

    # Custom output folder
    python -m tools.core.create_long_term_memory --output-folder ./my_output

    # Use MongoDB instead of Weaviate
    python -m tools.core.create_long_term_memory --vector-store mongo

    # Custom metadata file
    python -m tools.core.create_long_term_memory --metadata-file ./custom_metadata.json

Author: SkillPilot Team
Version: 2.0.0
"""

import warnings
import gc
import os
import sys
from pathlib import Path
from typing import Optional
import psutil

import click
from loguru import logger

from application import LongTermMemoryCreator
from config import settings
from domain.knowledge_factory import KnowledgeFactory

# Suppress SQLite ResourceWarnings from Playwright and other libraries
warnings.filterwarnings("ignore", category=ResourceWarning, module="sqlite3")
warnings.filterwarnings("ignore", category=ResourceWarning, module="inspect")
warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")


def log_memory_usage(stage: str) -> None:
    """
    Log current memory usage for monitoring and debugging purposes.
    
    This function captures the current memory consumption of the process and logs
    it with a descriptive stage identifier. Useful for identifying memory leaks
    or optimizing memory-intensive operations.
    
    Args:
        stage (str): Descriptive identifier for the current processing stage
                    (e.g., "start", "after loading knowledge sources", "final cleanup")
    
    Example:
        >>> log_memory_usage("after LLM enrichment")
        INFO: Memory usage at after LLM enrichment: 1024.5 MB
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    logger.info(f"Memory usage at {stage}: {memory_mb:.1f} MB")


def force_garbage_collection() -> None:
    """
    Force garbage collection to free memory and prevent memory leaks.
    
    This function triggers Python's garbage collector to clean up unused objects
    and free memory. It's particularly useful during long-running processes
    where memory accumulation could become an issue.
    
    Returns:
        None
    
    Example:
        >>> force_garbage_collection()
        DEBUG: Garbage collection freed 1500 objects
    """
    collected = gc.collect()
    logger.debug(f"Garbage collection freed {collected} objects")


@click.command()
@click.option(
    "--metadata-file",
    type=click.Path(exists=True, path_type=Path),
    default=settings.EXTRACTION_METADATA_FILE_PATH,
    help="Path to the candidates extraction metadata JSON file.",
)
@click.option(
    "--vector-store",
    type=click.Choice(["mongo", "weaviate"]),
    default=settings.VECTOR_STORE_TYPE.value,
    help="Vector store to use for long-term memory.",
)

@click.option(
    "--clear-first",
    is_flag=True,
    default=False,
    help="Clear existing data before ingestion.",
)
@click.option(
    "--batch-size",
    type=int,
    default=20,
    help="Batch size for processing. Smaller batches use less memory but are slower.",
)
@click.option(
    "--llm-workers",
    type=int,
    default=2,
    help="Number of LLM enrichment workers. Fewer workers use less memory and prevent server overload.",
)
@click.option(
    "--output-folder",
    type=click.Path(path_type=Path),
    default=Path("crawl_output"),
    help="Output folder for enriched documents.",
)
@click.option(
    "--disable-llm-enrichment",
    is_flag=True,
    default=False,
    help="Disable LLM enrichment to reduce memory usage.",
)
@click.option(
    "--memory-monitoring",
    is_flag=True,
    default=True,
    help="Enable memory usage monitoring.",
)
@click.option(
    "--write-files",
    is_flag=True,
    default=True,
    help="Write enriched documents to files.",
)
@click.option(
    "--check-duplicates",
    is_flag=True,
    default=True,
    help="Check for duplicate documents before processing.",
)

def main(
    metadata_file: Path,
    vector_store: str,
    clear_first: bool,
    batch_size: int,
    llm_workers: int,
    disable_llm_enrichment: bool,
    memory_monitoring: bool,
    write_files: bool,
    output_folder: Path,
    check_duplicates: bool,
) -> None:
    """Create long-term memory for the SkillPilot RAG system.
    
    Processes knowledge sources and creates searchable vector embeddings in Weaviate.
    
    Args:
        metadata_file: Path to extraction metadata JSON file (default from settings)
        vector_store: Vector store type ("mongo" or "weaviate", default from settings)
        clear_first: Clear existing data before ingestion (default: False)
        batch_size: Batch size for processing (default: 20, max: 1000)
        llm_workers: Number of LLM enrichment workers (default: 2, max: 50)
        disable_llm_enrichment: Disable LLM enrichment for faster processing (default: False)
        memory_monitoring: Enable memory usage monitoring (default: True)
        write_files: Write enriched documents to files (default: True)
        output_folder: Output folder for enriched documents (default: crawl_output)
        check_duplicates: Check for duplicate documents before processing (default: True)
    
    Examples:
        python -m tools.core.create_long_term_memory
        python -m tools.core.create_long_term_memory --batch-size 5 --llm-workers 1
        python -m tools.core.create_long_term_memory --clear-first
        python -m tools.core.create_long_term_memory --disable-llm-enrichment
        python -m tools.core.create_long_term_memory --vector-store mongo
        python -m tools.core.create_long_term_memory --output-folder ./my_output
    """
    # Validate input parameters
    if llm_workers > 50:
        logger.error(f"LLM workers ({llm_workers}) exceeds maximum allowed value of 50")
        logger.error("Please use a value between 1 and 50")
        sys.exit(1)
    
    if batch_size > 1000:
        logger.error(f"Batch size ({batch_size}) exceeds maximum recommended value of 1000")
        logger.error("Please use a smaller batch size to prevent memory issues")
        sys.exit(1)
    
    # Initialize memory monitoring if enabled
    if memory_monitoring:
        log_memory_usage("start")
    
    # Update vector store type based on user preference
    settings.VECTOR_STORE_TYPE = vector_store
    llm_enrichment = not disable_llm_enrichment
    logger.info(f"Using vector store: {vector_store} | batch_size: {batch_size} | llm_workers: {llm_workers} | check_duplicates: {check_duplicates} | llm_enrichment: {llm_enrichment} | max_workers: {llm_workers}")

    # Load knowledge sources from the configured metadata file
    # This replaces the previous approach of loading from extraction metadata
    knowledge_sources_factory = KnowledgeFactory(settings.KNOWLEDGE_METADATA_FILE_NAME)
    knowledge_sources = knowledge_sources_factory.get_all(enabled_only=True)
    logger.info(f"Loaded {len(knowledge_sources)} knowledge sources from {settings.KNOWLEDGE_METADATA_FILE_NAME}")

    if memory_monitoring:
        log_memory_usage("after loading knowledge sources")

    # Create long-term memory creator (Weaviate-only mode)
    long_term_memory_creator = LongTermMemoryCreator.build_from_settings()
    if memory_monitoring:
        log_memory_usage("after creating memory creator")

    # Process knowledge sources with memory-optimized settings
    try:
        # Process knowledge sources with configured settings
        # This is the main processing step that creates the long-term memory
        long_term_memory_creator(
            knowledge_sources, 
            clear_first, 
            batch_size=batch_size, 
            write_to_file=write_files, 
            output_folder=output_folder, 
            llm_enrichment=not disable_llm_enrichment,
            max_workers=int(llm_workers) if llm_workers is not None and llm_workers > 0 else 2,
            check_duplicates=check_duplicates
        )

        if memory_monitoring:
            log_memory_usage("after processing knowledge sources")
            force_garbage_collection()
            log_memory_usage("after garbage collection")

        logger.info("Successfully created long-term memory")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise
    finally:
        # Final cleanup and memory monitoring
        if memory_monitoring:
            force_garbage_collection()
            log_memory_usage("final cleanup")


if __name__ == "__main__":
    main()
