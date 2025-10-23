#!/usr/bin/env python3
"""
Test script to check if the LLM server is responsive.
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.data.llm.llm_enrichment import extract_entities_relationships_tags_sync


def test_llm_server():
    """Test if the LLM server is responsive."""
    logger.info("🧪 Testing LLM Server Responsiveness")
    logger.info("=" * 40)
    
    # Test content
    test_content = """
    MuleSoft Anypoint Platform is a complete integration platform for APIs, applications, and data.
    It includes API Manager for managing APIs, DataWeave for data transformation, and various connectors.
    """
    
    test_cases = [
        {
            "name": "Simple test",
            "content": test_content,
            "title": "Test Document",
            "url": "https://example.com/test"
        },
        {
            "name": "Empty content test",
            "content": "",
            "title": "Empty Document",
            "url": "https://example.com/empty"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{i}️⃣ Testing: {test_case['name']}")
        logger.info("-" * 30)
        
        try:
            start_time = time.time()
            
            result = extract_entities_relationships_tags_sync(
                content=test_case['content'],
                title=test_case['title'],
                url=test_case['url'],
                allowed_nodes=["Platform", "API", "Component"],
                allowed_relationships=["INCLUDES", "USES", "MANAGES"]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"✅ Test completed in {duration:.2f} seconds")
            logger.info(f"Entities found: {len(result.get('entities', []))}")
            logger.info(f"Relationships found: {len(result.get('relationships', []))}")
            logger.info(f"Tags found: {len(result.get('tags', []))}")
            
            if result.get('entities'):
                logger.info(f"Sample entities: {result['entities'][:2]}")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            logger.error(f"Traceback: {e}")
        
        # Small delay between tests
        time.sleep(2)
    
    logger.info("\n🎉 LLM server testing completed!")


def main():
    """Main function."""
    logger.info("🚀 Starting LLM Server Test")
    test_llm_server()


if __name__ == "__main__":
    main() 