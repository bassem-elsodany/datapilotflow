"""
Milvus processor for document ingestion and storage.
"""

import traceback
from typing import List, Dict, Any, Optional
from loguru import logger

from src.infrastructure.milvus.client import MilvusClientWrapper


class MilvusProcessor:
    """Milvus processor for document ingestion and storage."""
    
    def __init__(
        self,
        milvus_client: MilvusClientWrapper,
    ):
        """Initialize Milvus processor.
        
        Args:
            milvus_client: Milvus client for vector storage.
        """
        self.milvus_client = milvus_client
        
        logger.info(f"Milvus processor initialized")
    
    def process_documents(
        self, 
        documents: List[Any], 
        vectors: List[List[float]]
    ) -> Dict[str, Any]:
        """Process documents and store them in Milvus.
        
        Args:
            documents: List of documents to process.
            vectors: List of vector embeddings corresponding to each document.
            
        Returns:
            Dictionary containing processing statistics.
        """
        logger.debug(f"Processing {len(documents)} documents with Milvus processor")
        
        try:
            # Process documents in batches
            batch_stats = self._process_batch(documents, vectors)
            
            logger.debug(f"Document processing completed: {batch_stats}")
            return batch_stats
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _process_batch(self, documents: List[Any], vectors: List[List[float]]) -> Dict[str, Any]:
        """Process a batch of documents.
        
        Args:
            documents: List of documents to process.
            vectors: List of vector embeddings corresponding to each document.
            
        Returns:
            Dictionary containing batch processing statistics.
        """
        logger.debug(f"Processing batch of {len(documents)} documents")
        
        batch_stats = {
            "total_documents": len(documents),
            "milvus_processed": 0,
            "milvus_errors": [],
            "processing_time": 0
        }
        
        try:
            # Ingest documents into Milvus
            self.milvus_client.ingest_documents(documents, vectors)
            batch_stats["milvus_processed"] = len(documents)
            
            logger.debug(f"Successfully processed {len(documents)} documents in Milvus")
            
        except Exception as e:
            error_msg = f"Error processing documents in Milvus: {e}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            batch_stats["milvus_errors"].append(error_msg)
        
        return batch_stats
    
    def clear_all(self) -> None:
        """Clear Milvus collection."""
        logger.debug("Clearing Milvus collection")
        
        try:
            self.milvus_client.clear_collection()
            logger.debug("Milvus collection cleared")
                
        except Exception as e:
            logger.error(f"Error clearing Milvus collection: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from Milvus.
        
        Returns:
            Dictionary containing statistics from Milvus.
        """
        stats = {
            "milvus": {},
        }
        
        try:
            stats["milvus"] = {
                "collection_count": self.milvus_client.get_collection_count()
            }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            stats["error"] = str(e)
        
        return stats


def create_milvus_processor(
    milvus_model,
    milvus_collection_name: str,
    vector_dimension: int,
    **kwargs
) -> MilvusProcessor:
    """Factory function to create a Milvus processor.
    
    Args:
        milvus_model: Model class for Milvus.
        milvus_collection_name: Milvus collection name.
        vector_dimension: Dimension of the vector field.
        **kwargs: Additional arguments for Milvus client.
        
    Returns:
        Configured Milvus processor.
    """
    # Create Milvus client
    milvus_client = MilvusClientWrapper(
        model=milvus_model,
        collection_name=milvus_collection_name,
        vector_dimension=vector_dimension,
        **kwargs
    )
    
    return MilvusProcessor(
        milvus_client=milvus_client,
    )
