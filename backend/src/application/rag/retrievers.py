import traceback
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from loguru import logger

from src.config import settings
from src.infrastructure.milvus.client import MilvusClientWrapper
from litellm import embedding, completion


@dataclass
class RetrievalMetrics:
    """Metrics for tracking retrieval performance."""
    query_time: float
    weaviate_search_time: float
    llm_response_time: float
    total_results: int
    quality_score: float
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


async def milvus_knowledge_graph_search(
    query: str,
    milvus_client: MilvusClientWrapper,
    entities: List[str] = None,
    relationships: List[str] = None,
    top_k: int = 5,
    alpha: float = 0.7,
) -> str:
    """
    Milvus-based knowledge graph search using enhanced schema.
    
    This replaces the Weaviate search with a Milvus-based approach that leverages
    the enhanced searchable fields and vector similarity search.
    
    Args:
        query: User query string
        milvus_client: Milvus client wrapper
        entities: Optional list of entities to filter by (format: "name:type")
        relationships: Optional list of relationships to filter by (format: "source:relation:target")
        top_k: Number of top results to retrieve
        alpha: Balance between vector and keyword search
        
    Returns:
        LLM response based on retrieved context
    """
    try:
        logger.info(f"Performing Milvus knowledge graph search: {query}")
        
        # Get embedding for the query using LiteLLM
        embedding_response = embedding(
            model=settings.EMBEDDING_MODEL_NAME,
            input=[query]
        )
        query_vector = embedding_response.data[0].embedding
        
        # Build filter expression for entities and relationships if provided
        filter_expr = None
        if entities or relationships:
            filter_parts = []
            if entities:
                # Note: Entity filtering removed as keywords field is no longer available
                pass
            if relationships:
                # Note: Relationship filtering removed as keywords field is no longer available
                pass
            if filter_parts:
                filter_expr = " or ".join(filter_parts)
        
        # Use Milvus vector search
        results = milvus_client.search_with_vector(
            query_vector=query_vector,
            limit=top_k,
            filter_expr=filter_expr,
            return_fields=[
                "page_content", "title", "knowledge_source", "chunk_id",
                "source_url"
            ]
        )
        
        if not results:
            return "I couldn't find any relevant information in the knowledge base."
        
        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            properties = result.get("properties", {})
            content = properties.get("page_content", "")
            title = properties.get("title", "")
            source = properties.get("knowledge_source", "")
            source_url = properties.get("source_url", "")
            
            context_part = f"KNOWLEDGE SOURCE: {source}\n"
            if source_url:
                context_part += f"URL: {source_url}\n"
            if title:
                context_part += f"Title: {title}\n"
            context_part += f"Content: {content}\n"
            
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # Get LLM response using LiteLLM
        prompt = f"""Based on the following context from the knowledge base, please answer the user's question.

Context:
{context}

User Question: {query}

INSTRUCTIONS:
1. Answer the question based ONLY on the information provided in the context
2. CRITICAL: When referencing information, ALWAYS cite the specific knowledge source URL (e.g., 'According to [source_url]...' or 'As mentioned in [source_url]...')
3. Do NOT use generic terms like 'Result1', 'Result2', etc.
4. If the context doesn't contain enough information to answer the question, please say so
5. Use specific details from the context to support your answer
6. Keep your response concise but comprehensive
7. Synthesize and combine information from all relevant context entries to provide a unified answer.
8. If multiple context entries provide related or overlapping information, consolidate them and avoid repetition.
9. Do not simply list the context entries; instead, write a coherent, human-readable answer that integrates the most useful details."""

        response = completion(
            model=settings.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in milvus_knowledge_graph_search: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error occurred while searching: {str(e)}"


async def milvus_entity_search(
    entities: List[str],
    milvus_client: MilvusClientWrapper,
    top_k: int = 5,
) -> str:
    """
    Search for documents containing specific entities.
    
    Args:
        entities: List of entities to search for (format: "name:type" or just "name")
        milvus_client: Milvus client wrapper
        top_k: Number of top results to retrieve
        
    Returns:
        LLM response based on retrieved context
    """
    try:
        logger.info(f"Performing entity search for: {entities}")
        
        # Note: Entity filtering removed as keywords field is no longer available
        filter_expr = None
        
        # Use Milvus to fetch documents by entity filter
        results = milvus_client.fetch_documents(
            limit=top_k,
            filter_expr=filter_expr,
            return_fields=[
                "page_content", "title", "knowledge_source", "chunk_id",
                "source_url"
            ]
        )
        
        if not results:
            return f"I couldn't find any documents containing the entities: {', '.join(entities)}"
        
        # Build context
        context_parts = []
        for i, result in enumerate(results, 1):
            properties = result.get("properties", {})
            content = properties.get("page_content", "")
            title = properties.get("title", "")
            source = properties.get("knowledge_source", "")
            source_url = properties.get("source_url", "")
            
            context_part = f"KNOWLEDGE SOURCE: {source}\n"
            if source_url:
                context_part += f"URL: {source_url}\n"
            if title:
                context_part += f"Title: {title}\n"
            context_part += f"Content: {content}\n"
            
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # Get LLM response using LiteLLM
        prompt = f"""Based on the following documents that contain the entities {', '.join(entities)}, please provide information about these entities.

Context:
{context}

Please provide a comprehensive summary of what you found about these entities."""

        response = completion(
            model=settings.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in milvus_entity_search: {e}")
        return f"Error occurred while searching: {str(e)}"


async def milvus_relationship_search(
    relationships: List[str],
    milvus_client: MilvusClientWrapper,
    top_k: int = 5,
) -> str:
    """
    Search for documents containing specific relationships.
    
    Args:
        relationships: List of relationships to search for (format: "source:relation:target")
        milvus_client: Milvus client wrapper
        top_k: Number of top results to retrieve
        
    Returns:
        LLM response based on retrieved context
    """
    try:
        logger.info(f"Performing relationship search: relationships={relationships}")
        
        # Note: Relationship filtering removed as keywords field is no longer available
        filter_expr = None
        
        # Use Milvus to fetch documents by relationship filter
        results = milvus_client.fetch_documents(
            limit=top_k,
            filter_expr=filter_expr,
            return_fields=[
                "page_content", "title", "knowledge_source", "chunk_id",
                "source_url"
            ]
        )
        
        if not results:
            return "I couldn't find any documents containing the specified relationships."
        
        # Build context
        context_parts = []
        for i, result in enumerate(results, 1):
            properties = result.get("properties", {})
            content = properties.get("page_content", "")
            title = properties.get("title", "")
            source = properties.get("knowledge_source", "")
            source_url = properties.get("source_url", "")
            
            context_part = f"KNOWLEDGE SOURCE: {source}\n"
            if source_url:
                context_part += f"URL: {source_url}\n"
            if title:
                context_part += f"Title: {title}\n"
            context_part += f"Content: {content}\n"
            
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # Get LLM response using LiteLLM
        prompt = f"""Based on the following documents that contain relationships {', '.join(relationships)}, please provide information about these relationships.

Context:
{context}

Please provide a comprehensive summary of what you found about these relationships."""

        response = completion(
            model=settings.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in milvus_relationship_search: {e}")
        return f"Error occurred while searching: {str(e)}"


async def milvus_semantic_search(
    query: str,
    milvus_client: MilvusClientWrapper,
    top_k: int = 5,
    alpha: float = 0.7,
) -> str:
    """
    Perform semantic search using Milvus vector search capabilities.
    
    Args:
        query: User query string
        milvus_client: Milvus client wrapper
        top_k: Number of top results to retrieve
        alpha: Balance between vector and keyword search (not used in Milvus)
        
    Returns:
        LLM response based on retrieved context
    """
    try:
        logger.info(f"Performing semantic search: {query}")
        
        # Get embedding for the query using LiteLLM
        embedding_response = embedding(
            model=settings.EMBEDDING_MODEL_NAME,
            input=[query]
        )
        query_vector = embedding_response.data[0].embedding
        
        # Use Milvus vector search
        results = milvus_client.search_with_vector(
            query_vector=query_vector,
            limit=top_k,
            return_fields=[
                "page_content", "title", "knowledge_source", "chunk_id", "source_url",
            ]
        )
        
        if not results:
            return "I couldn't find any relevant information in the knowledge base."
        
        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            properties = result.get("properties", {})
            content = properties.get("page_content", "")
            title = properties.get("title", "")
            source = properties.get("knowledge_source", "")
            source_url = properties.get("source_url", "")
            
            context_part = f"KNOWLEDGE SOURCE: {source}\n"
            if source_url:
                context_part += f"URL: {source_url}\n"
            if title:
                context_part += f"Title: {title}\n"
            context_part += f"Content: {content}\n"
            
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # Get LLM response using LiteLLM
        prompt = f"""Based on the following context from the knowledge base, please answer the user's question.

Context:
{context}

User Question: {query}

INSTRUCTIONS:
1. Answer the question based ONLY on the information provided in the context
2. CRITICAL: When referencing information, ALWAYS cite the specific knowledge source URL (e.g., 'According to [source_url]...' or 'As mentioned in [source_url]...')
3. Do NOT use generic terms like 'Result1', 'Result2', etc.
4. If the context doesn't contain enough information to answer the question, please say so
5. Use specific details from the context to support your answer
6. Keep your response concise but comprehensive
7. Synthesize and combine information from all relevant context entries to provide a unified answer.
8. If multiple context entries provide related or overlapping information, consolidate them and avoid repetition.
9. Do not simply list the context entries; instead, write a coherent, human-readable answer that integrates the most useful details."""

        response = completion(
            model=settings.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in milvus_semantic_search: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error occurred while searching: {str(e)}"


