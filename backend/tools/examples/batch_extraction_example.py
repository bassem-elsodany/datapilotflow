#!/usr/bin/env python3
"""
Example script demonstrating batch processing for document extraction.

This script shows different ways to use the batch processing functionality:
1. Using the callback approach for immediate processing
2. Using the generator approach for streaming batches
3. Using the traditional approach (for comparison)
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.data.extract import (
    extract_with_batch_processing_callback,
    get_extraction_generator_with_batch_processing,
    extract
)
from domain.knowledge_factory import KnowledgeFactory
from loguru import logger


def batch_callback_example(client, batch, batch_number, total_processed):
    """Example callback function that processes each batch immediately."""
    logger.info(f"🔄 Processing batch {batch_number} with {len(batch)} documents")
    logger.info(f"📊 Total documents processed so far: {total_processed}")
    
    # Example: Process each document in the batch
    for i, doc in enumerate(batch):
        source = doc.metadata.get('source', 'Unknown')
        content_length = len(doc.page_content)
        logger.info(f"  📄 Document {i+1}: {source} ({content_length} characters)")
    
    # Example: You could save to database, process with AI, etc.
    # if client:
    #     client.add_documents(batch)
    # process_with_ai(batch)
    
    logger.info(f"✅ Completed processing batch {batch_number}")


def generator_example():
    """Example using the generator approach for streaming batches."""
    logger.info("🚀 Starting generator example...")
    
    # Initialize knowledge factory
    factory = KnowledgeFactory()
    knowledge_sources = factory.get_all(enabled_only=True)
    
    if not knowledge_sources:
        logger.warning("No knowledge sources found!")
        return
    
    # Get the first enabled knowledge source
    knowledge = knowledge_sources[0] if knowledge_sources else None
    
    if not knowledge:
        logger.warning("No enabled knowledge sources found!")
        return
    
    logger.info(f"📚 Processing knowledge source: {knowledge.name}")
    
    # Use the generator approach
    batch_generator = get_extraction_generator_with_batch_processing(
        [knowledge], 
        batch_size=100  # Smaller batch size for demonstration
    )
    
    total_batches = 0
    total_documents = 0
    
    for knowledge_source, batch in batch_generator:
        total_batches += 1
        total_documents += len(batch)
        
        logger.info(f"📦 Received batch {total_batches} with {len(batch)} documents")
        logger.info(f"📊 Total documents so far: {total_documents}")
        
        # Process the batch immediately
        for doc in batch:
            source = doc.metadata.get('source', 'Unknown')
            logger.info(f"  📄 {source}")
        
        # You can process each batch as it comes in
        # This is much more memory efficient than collecting all documents first
    
    logger.info(f"🎉 Completed! Processed {total_batches} batches with {total_documents} total documents")


def callback_example():
    """Example using the callback approach."""
    logger.info("🚀 Starting callback example...")
    
    # Initialize knowledge factory
    factory = KnowledgeFactory()
    knowledge_sources = factory.get_all(enabled_only=True)
    
    if not knowledge_sources:
        logger.warning("No knowledge sources found!")
        return
    
    # Get the first enabled knowledge source
    knowledge = knowledge_sources[0] if knowledge_sources else None
    
    if not knowledge:
        logger.warning("No enabled knowledge sources found!")
        return
    
    logger.info(f"📚 Processing knowledge source: {knowledge.name}")
    
    # Use the callback approach
    extract_with_batch_processing_callback(
        knowledge=knowledge,
        client=None,  # Pass your Weaviate client here if needed
        batch_callback=batch_callback_example,
        batch_size=100  # Smaller batch size for demonstration
    )
    
    logger.info("🎉 Completed callback example!")


def traditional_example():
    """Example using the traditional approach (for comparison)."""
    logger.info("🚀 Starting traditional example...")
    
    # Initialize knowledge factory
    factory = KnowledgeFactory()
    knowledge_sources = factory.get_all(enabled_only=True)
    
    if not knowledge_sources:
        logger.warning("No knowledge sources found!")
        return
    
    # Get the first enabled knowledge source
    knowledge = knowledge_sources[0] if knowledge_sources else None
    
    if not knowledge:
        logger.warning("No enabled knowledge sources found!")
        return
    
    logger.info(f"📚 Processing knowledge source: {knowledge.name}")
    
    # Use the traditional approach (collects all documents in memory)
    try:
        all_documents = extract(knowledge)
        logger.info(f"📊 Total documents extracted: {len(all_documents)}")
        
        for i, doc in enumerate(all_documents[:5]):  # Show first 5 documents
            source = doc.metadata.get('source', 'Unknown')
            content_length = len(doc.page_content)
            logger.info(f"  📄 Document {i+1}: {source} ({content_length} characters)")
        
        if len(all_documents) > 5:
            logger.info(f"  ... and {len(all_documents) - 5} more documents")
            
    except Exception as e:
        logger.error(f"Error in traditional approach: {e}")
    
    logger.info("🎉 Completed traditional example!")


def main():
    """Main function to run examples."""
    logger.info("🔧 Document Extraction Batch Processing Examples")
    logger.info("=" * 50)
    
    # Example 1: Callback approach
    logger.info("\n1️⃣ Callback Approach (Recommended for large datasets)")
    logger.info("   - Processes batches immediately as they're ready")
    logger.info("   - Memory efficient - doesn't keep all documents in memory")
    logger.info("   - Good for real-time processing")
    try:
        callback_example()
    except Exception as e:
        logger.error(f"Callback example failed: {e}")
    
    # Example 2: Generator approach
    logger.info("\n2️⃣ Generator Approach")
    logger.info("   - Yields batches as they're processed")
    logger.info("   - Memory efficient - streams batches")
    logger.info("   - Good for pipeline processing")
    try:
        generator_example()
    except Exception as e:
        logger.error(f"Generator example failed: {e}")
    
    # Example 3: Traditional approach
    logger.info("\n3️⃣ Traditional Approach (For comparison)")
    logger.info("   - Collects all documents in memory")
    logger.info("   - Can cause memory issues with large datasets")
    logger.info("   - Good for small datasets")
    try:
        traditional_example()
    except Exception as e:
        logger.error(f"Traditional example failed: {e}")
    
    logger.info("\n✅ All examples completed!")


if __name__ == "__main__":
    main() 