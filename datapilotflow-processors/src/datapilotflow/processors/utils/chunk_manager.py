"""
Chunk Manager for handling chunk ID generation and cross-referencing between Weaviate and Neo4j.
"""

import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from langchain_core.documents import Document


class ChunkManager:
    """Manages chunk IDs and cross-referencing between vector and graph databases."""
    
    def __init__(self):
        """Initialize the chunk manager."""
        self.chunk_counter = 0
        self.document_chunks = {}  # Track chunks per document
    
    def generate_chunk_id(self, document_url: str, chunk_content: str, chunk_index: int = None) -> str:
        """Generate a unique chunk ID based on document URL and content.
        
        Args:
            document_url: The source URL of the document.
            chunk_content: The content of the chunk.
            chunk_index: Optional index of the chunk within the document.
            
        Returns:
            Unique chunk ID string.
        """
        # Create a deterministic hash of the document URL and chunk content
        # This ensures the same content always generates the same chunk ID
        content_hash = hashlib.md5(f"{document_url}:{chunk_content}".encode()).hexdigest()[:12]
        
        # Include chunk index if provided for uniqueness within the document
        index_suffix = f"_{chunk_index}" if chunk_index is not None else ""
        
        # Remove timestamp to make chunk IDs deterministic
        chunk_id = f"chunk_{content_hash}{index_suffix}"
        
        logger.debug(f"Generated chunk ID: {chunk_id} for document: {document_url}")
        return chunk_id
    
    def process_document_chunks(
        self, 
        document: Document, 
        chunks: List[Document]
    ) -> List[Document]:
        """Process document chunks and add cross-reference metadata.
        
        Args:
            document: Original document before splitting.
            chunks: List of chunks created from the document.
            
        Returns:
            List of chunks with cross-reference metadata added.
        """
        document_url = document.metadata.get('source_url', '')
        document_id = document.metadata.get('document_id', str(uuid.uuid4()))
        
        # Track chunks for this document
        self.document_chunks[document_id] = {
            'url': document_url,
            'total_chunks': len(chunks),
            'chunk_ids': []
        }
        
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Generate unique chunk ID
            chunk_id = self.generate_chunk_id(document_url, chunk.page_content, i)
            
            # Add cross-reference metadata
            chunk.metadata.update({
                'chunk_id': chunk_id,
                'document_id': document_id,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source_url': document_url,
                'cross_reference_metadata': {
                    'weaviate_chunk_id': chunk_id,
                    'neo4j_chunk_id': chunk_id,
                    'document_id': document_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'created_at': datetime.now().isoformat()
                }
            })
            
            # Track chunk ID
            self.document_chunks[document_id]['chunk_ids'].append(chunk_id)
            
            processed_chunks.append(chunk)
            
            logger.debug(f"Processed chunk {i+1}/{len(chunks)} with ID: {chunk_id}")
        
        logger.info(f"Processed {len(processed_chunks)} chunks for document: {document_url}")
        return processed_chunks
    
    def get_chunk_cross_reference(self, chunk_id: str) -> Dict[str, Any]:
        """Get cross-reference information for a chunk.
        
        Args:
            chunk_id: The chunk ID to look up.
            
        Returns:
            Dictionary containing cross-reference information.
        """
        for doc_id, doc_info in self.document_chunks.items():
            if chunk_id in doc_info['chunk_ids']:
                chunk_index = doc_info['chunk_ids'].index(chunk_id)
                return {
                    'chunk_id': chunk_id,
                    'document_id': doc_id,
                    'document_url': doc_info['url'],
                    'chunk_index': chunk_index,
                    'total_chunks': doc_info['total_chunks'],
                    'related_chunks': doc_info['chunk_ids']
                }
        
        return {}
    
    def get_document_chunks(self, document_id: str) -> List[str]:
        """Get all chunk IDs for a document.
        
        Args:
            document_id: The document ID to look up.
            
        Returns:
            List of chunk IDs for the document.
        """
        return self.document_chunks.get(document_id, {}).get('chunk_ids', [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get chunk manager statistics.
        
        Returns:
            Dictionary containing chunk manager statistics.
        """
        total_documents = len(self.document_chunks)
        total_chunks = sum(len(doc_info['chunk_ids']) for doc_info in self.document_chunks.values())
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'average_chunks_per_document': total_chunks / total_documents if total_documents > 0 else 0,
            'document_chunks': self.document_chunks
        }


# Global chunk manager instance
_chunk_manager = ChunkManager()


def get_chunk_manager() -> ChunkManager:
    """Get the global chunk manager instance.
    
    Returns:
        Global chunk manager instance.
    """
    return _chunk_manager


def process_chunks_with_cross_reference(
    document: Document, 
    chunks: List[Document]
) -> List[Document]:
    """Process document chunks and add cross-reference metadata.
    
    Args:
        document: Original document before splitting.
        chunks: List of chunks created from the document.
        
    Returns:
        List of chunks with cross-reference metadata added.
    """
    return _chunk_manager.process_document_chunks(document, chunks)


def get_chunk_cross_reference(chunk_id: str) -> Dict[str, Any]:
    """Get cross-reference information for a chunk.
    
    Args:
        chunk_id: The chunk ID to look up.
        
    Returns:
        Dictionary containing cross-reference information.
    """
    return _chunk_manager.get_chunk_cross_reference(chunk_id) 