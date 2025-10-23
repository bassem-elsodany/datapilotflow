#!/usr/bin/env python3
"""
Test script for memory optimization in long-term memory creation.
This script helps test different memory configurations and monitor usage.
"""

import sys
import gc
import psutil
import os
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application import LongTermMemoryCreator
from domain.knowledge_factory import KnowledgeFactory
from config import settings


def log_memory_usage(stage: str):
    """Log current memory usage for monitoring."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    logger.info(f"Memory usage at {stage}: {memory_mb:.1f} MB")


def test_memory_optimization():
    """Test different memory optimization configurations."""
    logger.info("🧪 Testing Memory Optimization Configurations")
    logger.info("=" * 50)
    
    # Load knowledge sources
    knowledge_sources_factory = KnowledgeFactory(settings.KNOWLEDGE_METADATA_FILE_NAME)
    knowledge_sources = knowledge_sources_factory.get_all(enabled_only=True)
    logger.info(f"Loaded {len(knowledge_sources)} knowledge sources")
    
    if not knowledge_sources:
        logger.warning("No knowledge sources found!")
        return
    
    # Test different configurations
    configurations = [
        {
            "name": "Memory Optimized (Small batches, Few workers)",
            "batch_size": 10,
            "llm_workers": 2,
            "enable_llm": True,
            "enable_neo4j": True,
            "enable_weaviate": True
        },
        {
            "name": "Balanced (Medium batches, Medium workers)",
            "batch_size": 20,
            "llm_workers": 5,
            "enable_llm": True,
            "enable_neo4j": True,
            "enable_weaviate": True
        },
        {
            "name": "Performance (Large batches, Many workers)",
            "batch_size": 50,
            "llm_workers": 10,
            "enable_llm": True,
            "enable_neo4j": True,
            "enable_weaviate": True
        },
        {
            "name": "No LLM Enrichment (Memory efficient)",
            "batch_size": 20,
            "llm_workers": 0,
            "enable_llm": False,
            "enable_neo4j": True,
            "enable_weaviate": True
        },
        {
            "name": "Weaviate Only (No Neo4j)",
            "batch_size": 20,
            "llm_workers": 5,
            "enable_llm": True,
            "enable_neo4j": False,
            "enable_weaviate": True
        }
    ]
    
    for i, config in enumerate(configurations, 1):
        logger.info(f"\n{i}️⃣ Testing: {config['name']}")
        logger.info("-" * 30)
        
        try:
            # Log initial memory
            log_memory_usage(f"start of {config['name']}")
            
            # Update settings
            settings.RAG_LLM_ENRICHMENT_ENABLED = config['enable_llm']
            if config['enable_llm']:
                settings.RAG_LLM_ENRICHMENT_MAX_WORKERS = config['llm_workers']
            
            # Create long-term memory processor
            creator = LongTermMemoryCreator.build_from_settings()
            
            log_memory_usage(f"after creating processor for {config['name']}")
            
            # Process with current configuration
            creator(
                knowledge_sources[:1],  # Test with first knowledge source only
                clear_first=False,  # Don't clear for testing
                batch_size=config['batch_size']
            )
            
            log_memory_usage(f"after processing {config['name']}")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            log_memory_usage(f"after GC for {config['name']}")
            
            logger.success(f"✅ {config['name']} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ {config['name']} failed: {e}")
        
        # Small delay between tests
        import time
        time.sleep(2)
    
    logger.info("\n🎉 Memory optimization testing completed!")


def main():
    """Main function."""
    logger.info("🚀 Starting Memory Optimization Test")
    
    # Check if psutil is available
    try:
        import psutil
        logger.info("✅ psutil available for memory monitoring")
    except ImportError:
        logger.warning("⚠️ psutil not available. Install with: pip install psutil")
        logger.info("Continuing without memory monitoring...")
    
    test_memory_optimization()


if __name__ == "__main__":
    main() 