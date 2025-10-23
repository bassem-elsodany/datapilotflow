#!/usr/bin/env python3
"""
Comprehensive Knowledge Extraction and Processing Tool

This module orchestrates the complete knowledge extraction pipeline for the SkillPilot system.
It processes all enabled knowledge sources defined in the configuration, extracts content
from web pages, and builds a comprehensive knowledge graph for semantic search and analysis.

Purpose:
    - Crawl and extract content from configured knowledge sources (websites, documentation)
    - Process documents in batches for memory efficiency
    - Extract entities, relationships, and tags from content
    - Build a knowledge graph with page hierarchies and internal links
    - Prepare data for semantic search and long-term memory storage

Process Flow:
    1. Clear any existing graph data to start fresh
    2. Load all enabled knowledge sources from configuration
    3. For each knowledge source:
       - Configure crawler settings (depth, domains, patterns, etc.)
       - Extract documents in batches to manage memory
       - Process each document for content and metadata
    4. Save extracted graph data for persistence
    5. Display summary statistics of the extraction process

Output:
    - Processed documents with extracted entities, relationships, and tags
    - Knowledge graph data with page hierarchies and internal links
    - Summary statistics of the extraction process
    - Logs of the entire extraction process for debugging

Usage:
    python -m tools.core.run_extraction

Dependencies:
    - Knowledge sources must be configured and enabled
    - Web crawler must have access to target URLs
    - Sufficient disk space for document storage
    - Network connectivity for web crawling

Note: This tool is part of the larger SkillPilot knowledge management system
and should be run as part of the regular knowledge update process.

Author: SkillPilot Team
Version: 2.0.0
"""

import asyncio
import sys
import traceback
from pathlib import Path

from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.data import (
    extract_with_batch_processing_callback,
    get_extraction_generator,
)
from application.data.crawler import CrawlerKnowledgeConfig
from application.data.graph_extractor import (
    clear_graph_data,
    get_graph_data,
    save_graph_data,
)
from application.data.web_document_processor import get_knowledge_source_documents
from domain.knowledge import Knowledge
from domain.knowledge_factory import KnowledgeFactory


async def main():
    """Main extraction function that processes all enabled knowledge sources."""
    # Clear any existing graph data
    clear_graph_data()

    # Initialize knowledge factory
    factory = KnowledgeFactory()

    # Get all available knowledge sources
    knowledge_sources = factory.get_all(enabled_only=True)
    logger.info(f"Found {len(knowledge_sources)} enabled knowledge sources")

    # Process each enabled knowledge source
    for knowledge in knowledge_sources:
        try:
            logger.info(
                f"Starting {knowledge.scraping_mode} for knowledge source: {knowledge.name}"
            )

            # Create crawler config from knowledge settings
            # Note: Using default cache_mode since Knowledge model doesn't have this attribute
            crawler_knowledge_config = CrawlerKnowledgeConfig(
                max_depth=knowledge.crawl_depth,
                allowed_domains=knowledge.allowed_subdomains,
                blocked_domains=knowledge.blocked_subdomains,
                url_patterns=knowledge.url_patterns,
                target_elements=knowledge.target_elements,
                content_filter_threshold=knowledge.content_filter_threshold,
                scraping_mode=knowledge.scraping_mode,
            )

            # Process the knowledge source URL using batch processing
            total_docs = 0
            batch_count = 0

            async for batch in get_knowledge_source_documents(
                knowledge, knowledge.url, crawler_knowledge_config
            ):
                batch_count += 1
                total_docs += len(batch)
                logger.info(
                    f"Batch {batch_count}: {len(batch)} documents. Total so far: {total_docs}"
                )

                # Process each document in the batch
                for doc in batch:
                    source = doc.metadata.get("source", "Unknown")
                    logger.debug(f"  - {source}")

            logger.info(
                f"Completed processing {knowledge.name}. Total documents: {total_docs}"
            )

        except Exception as e:
            logger.error(f"Failed to process knowledge source {knowledge.name}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")

    # Save the extracted graph data
    logger.info("Saving extracted graph data...")
    save_graph_data()

    # Display graph summary
    graph_summary = get_graph_data()
    logger.info("=== GRAPH EXTRACTION SUMMARY ===")
    logger.info(f"Pages processed: {len(graph_summary['pages'])}")
    logger.info(f"Internal links found: {len(graph_summary['links'])}")
    logger.info(f"Hierarchies extracted: {len(graph_summary['hierarchies'])}")

    # Show sample data
    if graph_summary["pages"]:
        sample_page = list(graph_summary["pages"].values())[0]
        logger.info(f"Sample page: {sample_page['title']}")
        logger.info(f"  - Headers: {len(sample_page['headers'])}")
        logger.info(f"  - Internal links: {len(sample_page['internal_links'])}")
        logger.info(f"  - Code blocks: {len(sample_page['code_blocks'])}")


if __name__ == "__main__":
    print("Starting extraction process...")
    # Run the async main function
    asyncio.run(main())
    print("Extraction process completed!")
