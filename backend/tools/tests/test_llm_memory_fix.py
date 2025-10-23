#!/usr/bin/env python3
"""
Test script to verify LLM memory fixes.
"""

import sys
import gc
import psutil
import os
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.data.llm.llm_enrichment import enrich_documents_batch_with_llm
from langchain_core.documents import Document


def create_test_documents(count: int = 10) -> list[Document]:
    """Create test documents for LLM enrichment."""
    docs = []
    for i in range(count):
        doc = Document(
            page_content=f"This is test document {i} with some content about MuleSoft and DataWeave. It contains information about APIs and integration patterns.",
            metadata={
                "title": f"Test Document {i}",
                "source_url": f"https://example.com/doc{i}",
                "chunk_id": f"chunk_{i}"
            }
        )
        docs.append(doc)
    return docs


def log_memory_usage(stage: str):
    """Log current memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    logger.info(f"Memory usage at {stage}: {memory_mb:.1f} MB")


def test_llm_memory_fix():
    """Test the LLM memory fixes."""
    logger.info("🧪 Testing LLM Memory Fixes")
    logger.info("=" * 40)
    
    # Test configurations
    test_configs = [
        {"name": "Small batch, few workers", "batch_size": 5, "workers": 2},
        {"name": "Medium batch, medium workers", "batch_size": 10, "workers": 4},
        {"name": "Large batch, many workers", "batch_size": 20, "workers": 8},
    ]
    
    for config in test_configs:
        logger.info(f"\n📋 Testing: {config['name']}")
        logger.info("-" * 30)
        
        try:
            # Create test documents
            docs = create_test_documents(config['batch_size'])
            log_memory_usage(f"after creating {config['batch_size']} test docs")
            
            # Test LLM enrichment
            import asyncio
            enriched_docs = asyncio.run(
                enrich_documents_batch_with_llm(
                docs=docs,
                max_workers=config['workers'],
                allowed_nodes=["API", "Integration", "DataWeave"],
                allowed_relationships=["uses", "implements", "contains"]
                )
            )
            
            log_memory_usage(f"after LLM enrichment with {config['workers']} workers")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            log_memory_usage(f"after GC for {config['name']}")
            
            logger.success(f"✅ {config['name']} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ {config['name']} failed: {e}")
            logger.error(f"Traceback: {e}")
        
        # Clear variables
        if 'docs' in locals():
            del docs
        if 'enriched_docs' in locals():
            del enriched_docs
        gc.collect()
        
        # Small delay between tests
        import time
        time.sleep(1)
    
    logger.info("\n🎉 LLM memory fix testing completed!")


def main():
    """Main function."""
    logger.info("🚀 Starting LLM Memory Fix Test")
    
    # Check if psutil is available
    try:
        import psutil
        logger.info("✅ psutil available for memory monitoring")
    except ImportError:
        logger.warning("⚠️ psutil not available. Install with: pip install psutil")
        logger.info("Continuing without memory monitoring...")
    
    test_llm_memory_fix()


if __name__ == "__main__":
    main() 