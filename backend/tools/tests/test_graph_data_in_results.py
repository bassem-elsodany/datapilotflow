#!/usr/bin/env python3
"""
Test script to demonstrate how graph data is included in extraction results.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from application.data import extract_with_graph_data
from domain.knowledge_factory import KnowledgeFactory
from loguru import logger

def test_graph_data_in_results():
    """Test that graph data is included in extraction results."""
    
    # Load knowledge sources
    knowledge_factory = KnowledgeFactory()
    knowledge_sources = knowledge_factory.get_all(enabled_only=True)
    
    if not knowledge_sources:
        logger.error("No knowledge sources found")
        return
    
    # Use the first enabled knowledge source
    knowledge = next((ks for ks in knowledge_sources if ks.enabled), knowledge_sources[0])
    logger.info(f"Testing with knowledge source: {knowledge.name}")
    
    # Extract documents with graph data
    logger.info("Extracting documents with graph data...")
    documents, graph_data = extract_with_graph_data(knowledge)
    
    logger.info(f"Extracted {len(documents)} documents")
    logger.info(f"Graph data contains {len(graph_data['pages'])} pages, {len(graph_data['links'])} links, {len(graph_data['hierarchies'])} hierarchies")
    
    # Check that graph data is included in document metadata
    for i, doc in enumerate(documents):
        logger.info(f"\nDocument {i+1}: {doc.metadata.get('title', 'Unknown title')}")
        logger.info(f"  Source: {doc.metadata.get('source', 'Unknown source')}")
        
        # Check for graph data in metadata
        graph_data_in_metadata = doc.metadata.get('graph_data', {})
        if graph_data_in_metadata:
            logger.info(f"  Graph data included:")
            logger.info(f"    - Headers: {len(graph_data_in_metadata.get('headers', []))}")
            logger.info(f"    - Internal links: {len(graph_data_in_metadata.get('internal_links', []))}")
            logger.info(f"    - Code blocks: {len(graph_data_in_metadata.get('code_blocks', []))}")
            logger.info(f"    - Breadcrumbs: {len(graph_data_in_metadata.get('breadcrumbs', []))}")
        else:
            logger.warning(f"  No graph data found in metadata")
    
    # Show complete graph data structure
    logger.info(f"\n=== COMPLETE GRAPH DATA STRUCTURE ===")
    logger.info(f"Pages: {list(graph_data['pages'].keys())}")
    
    if graph_data['links']:
        logger.info(f"Sample links:")
        for link in graph_data['links'][:3]:
            logger.info(f"  {link['from_url']} -> {link['to_url']}")
    
    if graph_data['hierarchies']:
        logger.info(f"Sample hierarchy:")
        hierarchy = graph_data['hierarchies'][0]
        logger.info(f"  URL: {hierarchy['url']}")
        logger.info(f"  Title: {hierarchy['title']}")
        logger.info(f"  Structure depth: {hierarchy['depth']}")
        logger.info(f"  Headers: {len(hierarchy['structure'])}")

if __name__ == "__main__":
    test_graph_data_in_results() 