"""
Knowledge ingestion service for SkillPilot.

This module provides the KnowledgeIngestionService class for managing
document ingestion into the knowledge base using Weaviate storage.
"""

import base64
import io
import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger
from pathlib import Path

from datapilotflow.services.file_management.file_upload_service import handle_file_upload
from datapilotflow.processors.document.file_processor import FileProcessor
from datapilotflow.persistence.vectordb.processor import MilvusProcessor, create_milvus_processor
from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
from datapilotflow.domain.config import settings


# REMOVE all await websocket.send_json calls
# REMOVE process_file_with_progress function

# ... existing code ... 

class KnowledgeIngestionService:
    """Service for ingesting knowledge documents into the system."""
    
    def __init__(self):
        """Initialize the knowledge ingestion service."""
        self.milvus_processor = create_milvus_processor(
            milvus_model=KnowledgeChunk,
            milvus_collection_name="LongTermMemory"
        )
        logger.info("Knowledge ingestion service initialized with Milvus processor")
    
    def ingest_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest documents into the knowledge base.
        
        Args:
            documents: List of documents to ingest
            
        Returns:
            Dictionary containing ingestion statistics
        """
        try:
            logger.info(f"Ingesting {len(documents)} documents")
            
            # Process documents using Milvus processor
            stats = self.milvus_processor.process_documents(documents)
            
            logger.info(f"Document ingestion completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            raise
    
    def clear_knowledge_base(self) -> None:
        """Clear the entire knowledge base."""
        try:
            logger.info("Clearing knowledge base")
            self.milvus_processor.clear_all()
            logger.info("Knowledge base cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Dictionary containing knowledge base statistics
        """
        try:
            stats = self.milvus_processor.get_statistics()
            logger.info(f"Knowledge base statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise 