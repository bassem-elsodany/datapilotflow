#!/usr/bin/env python3
"""
Test script to verify that markdown and enriched document files are being saved correctly.
"""

import sys
import os
import json
from pathlib import Path
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from application.data.web_document_processor import (
    _write_markdown_to_file, 
    write_enriched_documents_to_file,
    write_enriched_markdown_to_file,
    get_all_model_instances
)
from langchain_core.documents import Document

def test_markdown_file_saving():
    """Test that markdown files are being saved correctly."""
    logger.info("=== Testing Markdown File Saving ===")
    
    # Create test data
    test_metadata = {
        "source_url": "https://example.com/test",
        "knowledge_source": "test_knowledge",
        "title": "Test Document",
        "description": "A test document for file saving",
        "graph_data": {
            "headers": [{"level": 1, "text": "Test Header"}],
            "internal_links": [{"href": "/test", "text": "Test Link"}]
        }
    }
    
    test_content = """
# Test Document

This is a test document to verify markdown file saving.

## Section 1

Some content here.

## Section 2

More content here.
"""
    
    # Test file path
    test_file = Path("crawl_output/test_markdown_content.json")
    
    try:
        # Test the markdown file saving
        import asyncio
        asyncio.run(_write_markdown_to_file(test_file, test_metadata, test_content))
        
        # Verify the file was created and contains the data
        if test_file.exists():
            logger.info(f"✅ Markdown file created: {test_file}")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"✅ File contains {len(data)} entries")
                
                # Check the first entry
                first_entry = data[0]
                if (first_entry.get('source_url') == test_metadata['source_url'] and
                    first_entry.get('title') == test_metadata['title'] and
                    first_entry.get('page_content') == test_content):
                    logger.info("✅ File content matches expected data")
                else:
                    logger.error("❌ File content does not match expected data")
            else:
                logger.error("❌ File does not contain expected array structure")
        else:
            logger.error("❌ Markdown file was not created")
            
    except Exception as e:
        logger.error(f"❌ Error testing markdown file saving: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def test_enriched_documents_file_saving():
    """Test that enriched documents are being saved correctly."""
    logger.info("\n=== Testing Enriched Documents File Saving ===")
    
    # Create test documents
    test_docs = []
    for i in range(3):
        doc = Document(
            page_content=f"Test content {i}",
            metadata={
                "source_url": f"https://example.com/test{i}",
                "knowledge_source": "test_knowledge",
                "title": f"Test Document {i}",
                "description": f"Test description {i}",
                "graph_data": {
                    "entities": [{"name": f"Entity {i}", "type": "Test"}],
                    "relationships": [{"source": f"Entity {i}", "relation": "test", "target": "Test"}],
                    "tags": [f"tag{i}", "test"]
                }
            }
        )
        test_docs.append(doc)
    
    # Test file path
    test_file = Path("crawl_output/test_enriched_documents.json")
    
    try:
        # Test the enriched documents file saving
        write_enriched_documents_to_file(test_docs, test_file)
        
        # Verify the file was created and contains the data
        if test_file.exists():
            logger.info(f"✅ Enriched documents file created: {test_file}")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) == len(test_docs):
                logger.info(f"✅ File contains {len(data)} documents")
                
                # Check each document
                for i, doc_data in enumerate(data):
                    if (doc_data.get('source_url') == test_docs[i].metadata['source_url'] and
                        doc_data.get('title') == test_docs[i].metadata['title'] and
                        doc_data.get('page_content') == test_docs[i].page_content and
                        'graph_data' in doc_data):
                        logger.info(f"✅ Document {i} data matches expected")
                    else:
                        logger.error(f"❌ Document {i} data does not match expected")
            else:
                logger.error("❌ File does not contain expected number of documents")
        else:
            logger.error("❌ Enriched documents file was not created")
            
    except Exception as e:
        logger.error(f"❌ Error testing enriched documents file saving: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def test_enriched_markdown_file_saving():
    """Test that enriched markdown files are being saved correctly."""
    logger.info("\n=== Testing Enriched Markdown File Saving ===")
    
    # Create test documents with LLM-enriched data
    test_docs = []
    for i in range(3):
        doc = Document(
            page_content=f"""# Test Document {i}

This is test content {i} with markdown formatting.

## Section {i}

Some content here.

## Code Example

```python
def test_function_{i}():
    return "test"
```

## Links

- [Test Link {i}](https://example.com/test{i})
- [Another Link](https://example.com/another)
""",
            metadata={
                "source_url": f"https://example.com/test{i}",
                "knowledge_source": "test_knowledge",
                "title": f"Test Document {i}",
                "description": f"Test description {i}",
                "graph_data": {
                    "entities": [
                        {"name": f"Entity {i}", "type": "Test"},
                        {"name": f"Function {i}", "type": "Code"}
                    ],
                    "relationships": [
                        {"source": f"Entity {i}", "relation": "test", "target": "Test"},
                        {"source": f"Function {i}", "relation": "implements", "target": f"Entity {i}"}
                    ],
                    "tags": [f"tag{i}", "test", "markdown", "documentation"],
                    "headers": [
                        {"level": 1, "text": f"Test Document {i}"},
                        {"level": 2, "text": f"Section {i}"},
                        {"level": 2, "text": "Code Example"},
                        {"level": 2, "text": "Links"}
                    ],
                    "internal_links": [
                        {"href": f"https://example.com/test{i}", "text": f"Test Link {i}"},
                        {"href": "https://example.com/another", "text": "Another Link"}
                    ]
                }
            }
        )
        test_docs.append(doc)
    
    # Test file path
    test_file = Path("crawl_output/test_enriched_markdown.json")
    
    try:
        # Test the enriched markdown file saving
        write_enriched_markdown_to_file(test_docs, test_file)
        
        # Verify the file was created and contains the data
        if test_file.exists():
            logger.info(f"✅ Enriched markdown file created: {test_file}")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) == len(test_docs):
                logger.info(f"✅ File contains {len(data)} documents")
                
                # Check each document
                for i, doc_data in enumerate(data):
                    if (doc_data.get('source_url') == test_docs[i].metadata['source_url'] and
                        doc_data.get('title') == test_docs[i].metadata['title'] and
                        doc_data.get('page_content') == test_docs[i].page_content and
                        'graph_data' in doc_data):
                        logger.info(f"✅ Document {i} data matches expected")
                        
                        # Check LLM-enriched data
                        graph_data = doc_data.get('graph_data', {})
                        if (len(graph_data.get('entities', [])) > 0 and
                            len(graph_data.get('relationships', [])) > 0 and
                            len(graph_data.get('tags', [])) > 0):
                            logger.info(f"✅ Document {i} contains LLM-enriched data")
                        else:
                            logger.warning(f"⚠️  Document {i} missing LLM-enriched data")
                    else:
                        logger.error(f"❌ Document {i} data does not match expected")
            else:
                logger.error("❌ File does not contain expected number of documents")
        else:
            logger.error("❌ Enriched markdown file was not created")
            
    except Exception as e:
        logger.error(f"❌ Error testing enriched markdown file saving: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def test_file_structure():
    """Test the structure of saved files."""
    logger.info("\n=== Testing File Structure ===")
    
    # Check if crawl_output directory exists
    crawl_output_dir = Path("crawl_output")
    if crawl_output_dir.exists():
        logger.info(f"✅ Crawl output directory exists: {crawl_output_dir}")
        
        # List all files in the directory
        files = list(crawl_output_dir.glob("*.json"))
        logger.info(f"Found {len(files)} JSON files:")
        
        for file in files:
            logger.info(f"  - {file.name}")
            
            # Try to read and validate each file
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    logger.info(f"    ✅ Valid JSON array with {len(data)} entries")
                    
                    # Check structure of first entry if available
                    if len(data) > 0:
                        first_entry = data[0]
                        required_fields = ['source_url', 'page_content']
                        missing_fields = [field for field in required_fields if field not in first_entry]
                        
                        if missing_fields:
                            logger.warning(f"    ⚠️  Missing required fields: {missing_fields}")
                        else:
                            logger.info(f"    ✅ Contains required fields: {required_fields}")
                else:
                    logger.warning(f"    ⚠️  Not a JSON array: {type(data)}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"    ❌ Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"    ❌ Error reading file: {e}")
    else:
        logger.warning("⚠️  Crawl output directory does not exist")

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")
    
    try:
        # Test markdown file saving
        test_markdown_file_saving()
        
        # Test enriched documents file saving
        test_enriched_documents_file_saving()
        
        # Test enriched markdown file saving
        test_enriched_markdown_file_saving()
        
        # Test existing file structure
        test_file_structure()
        
        logger.info("\n=== All tests completed ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1) 