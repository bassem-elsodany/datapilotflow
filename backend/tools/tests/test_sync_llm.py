#!/usr/bin/env python3
"""
Test script to verify the synchronous LLM approach works.
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.data.llm.llm_enrichment import enrich_documents_batch_with_llm
from langchain_core.documents import Document


def create_test_documents(count: int = 3) -> list[Document]:
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


def test_sync_llm():
    """Test the synchronous LLM approach."""
    logger.info("🧪 Testing Synchronous LLM Approach")
    logger.info("=" * 40)
    
    # Test configurations
    test_configs = [
        {"name": "Sequential processing (1 worker)", "workers": 1},
        {"name": "Threaded processing (2 workers)", "workers": 2},
    ]
    
    for config in test_configs:
        logger.info(f"\n📋 Testing: {config['name']}")
        logger.info("-" * 30)
        
        try:
            # Create test documents
            docs = create_test_documents(3)
            logger.info(f"Created {len(docs)} test documents")
            
            # Test LLM enrichment
            start_time = time.time()
            import asyncio
            enriched_docs = asyncio.run(
                enrich_documents_batch_with_llm(
                docs=docs,
                max_workers=config['workers'],
                allowed_nodes=["API", "Integration", "DataWeave"],
                allowed_relationships=["uses", "implements", "contains"]
                )
            )
            end_time = time.time()
            
            duration = end_time - start_time
            logger.info(f"✅ {config['name']} completed in {duration:.2f} seconds")
            logger.info(f"Enriched {len(enriched_docs)} documents")
            
            # Check if documents were enriched
            enriched_count = 0
            for doc in enriched_docs:
                if doc.metadata.get('graph_data', {}).get('entities'):
                    enriched_count += 1
            
            logger.info(f"Documents with entities: {enriched_count}/{len(enriched_docs)}")
            
        except Exception as e:
            logger.error(f"❌ {config['name']} failed: {e}")
            logger.error(f"Traceback: {e}")
        
        # Clear variables
        if 'docs' in locals():
            del docs
        if 'enriched_docs' in locals():
            del enriched_docs
        
        # Small delay between tests
        time.sleep(2)
    
    logger.info("\n🎉 Synchronous LLM testing completed!")


def main():
    """Main function."""
    logger.info("🚀 Starting Synchronous LLM Test")
    test_sync_llm()


if __name__ == "__main__":
    main() 