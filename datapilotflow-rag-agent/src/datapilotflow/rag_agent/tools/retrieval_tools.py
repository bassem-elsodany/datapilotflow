"""
Retrieval tools for DataPilotFlow workflow.

This module contains tools for document retrieval and search operations.
"""

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from loguru import logger

from datapilotflow.domain.config import settings
from datapilotflow.domain.core.exceptions import (
    DocumentRetrievalError,
    EntitySearchError,
    HybridSearchError,
    InvalidSearchParametersError,
    KnowledgeGraphSearchError,
    RelationshipSearchError,
    SemanticSearchError,
    VectorSearchError,
    WeaviateConnectionError,
)
from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper


def _serialize_documents_for_llm(documents: List[Document]) -> str:
    """
    Serialize documents into human-readable format for LLM consumption.

    Args:
        documents: List of Document objects

    Returns:
        Serialized string with source and content information
    """
    if not documents:
        return "No documents found."

    return "\n\n".join(
        f"Source: {doc.metadata.get('title', 'Unknown')} | {doc.metadata.get('knowledge_source', 'Unknown')}\n"
        f"Content: {doc.page_content}"
        for doc in documents
    )


@tool(response_format="content_and_artifact")
def vector_search(query: str, limit: int = 5):
    """
    Search for documents using vector similarity.

    Args:
        query: Search query string
        limit: Maximum number of documents to return

    Returns:
        Tuple of (serialized_content, documents) where:
        - serialized_content: Human-readable string for LLM consumption
        - documents: List of Document objects for further processing

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        VectorSearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(f"Vector search: query='{query}', limit={limit}")

    # Validate parameters
    if not query or not query.strip():
        raise InvalidSearchParametersError(
            "vector_search", "query", query, "Query cannot be empty"
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "vector_search", "limit", limit, "Limit must be positive"
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            # Use vector search
            results = milvus_client.search_with_vector(
                vector=query,  # This will be converted to vector internally
                limit=limit,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Vector search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise VectorSearchError(query, error_msg)


@tool(response_format="content_and_artifact")
def semantic_search(
    query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 5
):
    """
    Perform semantic search for documents.

    Args:
        query: Search query string
        filters: Optional filters to apply
        limit: Maximum number of documents to return

    Returns:
        List of relevant documents

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        SemanticSearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(
        f"Semantic search: query='{query}', filters='{filters}', limit={limit}"
    )

    # Validate parameters
    if not query or not query.strip():
        raise InvalidSearchParametersError(
            "semantic_search", "query", query, "Query cannot be empty"
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "semantic_search", "limit", limit, "Limit must be positive"
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            # Use semantic search (text-based search)
            results = milvus_client.search_with_text(
                query_text=query,
                limit=limit,
                filters=filters,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Semantic search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise SemanticSearchError(query, error_msg)


@tool(response_format="content_and_artifact")
def hybrid_search(query: str, alpha: float = 0.5, limit: int = 5):
    """
    Perform hybrid search combining vector and keyword search.

    Args:
        query: Search query string
        alpha: Weight for vector vs keyword search (0.0 = keyword only, 1.0 = vector only)
        limit: Maximum number of documents to return

    Returns:
        Tuple of (serialized_content, documents) where:
        - serialized_content: Human-readable string for LLM consumption
        - documents: List of Document objects for further processing

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        HybridSearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(f"Hybrid search: query='{query}', alpha={alpha}, limit={limit}")

    # Validate parameters
    if not query or not query.strip():
        raise InvalidSearchParametersError(
            "hybrid_search", "query", query, "Query cannot be empty"
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "hybrid_search", "limit", limit, "Limit must be positive"
        )

    if not 0.0 <= alpha <= 1.0:
        raise InvalidSearchParametersError(
            "hybrid_search", "alpha", alpha, "Alpha must be between 0.0 and 1.0"
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            # Use the same hybrid search as in the WebSocket router
            results = milvus_client.search_hybrid(
                query=query,
                limit=limit,
                alpha=alpha,
                fusion_type="relative_score",
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Hybrid search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise HybridSearchError(query, error_msg)


@tool(response_format="content_and_artifact")
def entity_search(entities: List[str], limit: int = 5):
    """
    Search for documents by entities.

    Args:
        entities: List of entity names to search for
        limit: Maximum number of documents to return

    Returns:
        Tuple of (serialized_content, documents) where:
        - serialized_content: Human-readable string for LLM consumption
        - documents: List of Document objects for further processing

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        EntitySearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(f"Entity search: entities='{entities}', limit={limit}")

    # Validate parameters
    if not entities or not isinstance(entities, list) or len(entities) == 0:
        raise InvalidSearchParametersError(
            "entity_search", "entities", entities, "Entities list cannot be empty"
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "entity_search", "limit", limit, "Limit must be positive"
        )

    # Filter out empty entities
    valid_entities = [
        entity.strip() for entity in entities if entity and entity.strip()
    ]
    if not valid_entities:
        raise InvalidSearchParametersError(
            "entity_search", "entities", entities, "No valid entities provided"
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            results = milvus_client.search_by_entities(
                entities=valid_entities,
                limit=limit,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Entity search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise EntitySearchError(entities, error_msg)


@tool(response_format="content_and_artifact")
def relationship_search(relationships: List[str], limit: int = 5):
    """
    Search for documents by relationships.

    Args:
        relationships: List of relationship types to search for
        limit: Maximum number of documents to return

    Returns:
        Tuple of (serialized_content, documents) where:
        - serialized_content: Human-readable string for LLM consumption
        - documents: List of Document objects for further processing

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        RelationshipSearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(f"Relationship search: relationships='{relationships}', limit={limit}")

    # Validate parameters
    if (
        not relationships
        or not isinstance(relationships, list)
        or len(relationships) == 0
    ):
        raise InvalidSearchParametersError(
            "relationship_search",
            "relationships",
            relationships,
            "Relationships list cannot be empty",
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "relationship_search", "limit", limit, "Limit must be positive"
        )

    # Filter out empty relationships
    valid_relationships = [rel.strip() for rel in relationships if rel and rel.strip()]
    if not valid_relationships:
        raise InvalidSearchParametersError(
            "relationship_search",
            "relationships",
            relationships,
            "No valid relationships provided",
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            results = milvus_client.search_by_relationships(
                relationships=valid_relationships,
                limit=limit,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Relationship search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise RelationshipSearchError(relationships, error_msg)


@tool(response_format="content_and_artifact")
def knowledge_graph_search(
    query: str,
    entities: Optional[List[str]] = None,
    relationships: Optional[List[str]] = None,
    limit: int = 5,
):
    """
    Perform knowledge graph search combining query, entities, and relationships.

    Args:
        query: Search query string
        entities: Optional list of entities to filter by
        relationships: Optional list of relationships to filter by
        limit: Maximum number of documents to return

    Returns:
        Tuple of (serialized_content, documents) where:
        - serialized_content: Human-readable string for LLM consumption
        - documents: List of Document objects for further processing

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        KnowledgeGraphSearchError: If search fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(
        f"Knowledge graph search: query='{query}', entities='{entities}', relationships='{relationships}', limit={limit}"
    )

    # Validate parameters
    if not query or not query.strip():
        raise InvalidSearchParametersError(
            "knowledge_graph_search", "query", query, "Query cannot be empty"
        )

    if limit <= 0:
        raise InvalidSearchParametersError(
            "knowledge_graph_search", "limit", limit, "Limit must be positive"
        )

    # Filter out empty entities and relationships if provided
    valid_entities = None
    if entities:
        valid_entities = [
            entity.strip() for entity in entities if entity and entity.strip()
        ]
        if not valid_entities:
            valid_entities = None

    valid_relationships = None
    if relationships:
        valid_relationships = [
            rel.strip() for rel in relationships if rel and rel.strip()
        ]
        if not valid_relationships:
            valid_relationships = None

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            results = milvus_client.search_knowledge_graph(
                query=query,
                entities=valid_entities,
                relationships=valid_relationships,
                limit=limit,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            # Convert to Document objects
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    documents.append(Document(page_content=content, metadata=metadata))

            # Create serialized content for LLM consumption
            serialized_content = _serialize_documents_for_llm(documents)

            return serialized_content, documents

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Knowledge graph search failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise KnowledgeGraphSearchError(query, error_msg)


@tool(response_format="content_and_artifact")
def get_document_by_id(document_id: str):
    """
    Retrieve a specific document by its ID.

    Args:
        document_id: The ID of the document to retrieve

    Returns:
        Tuple of (serialized_content, document) where:
        - serialized_content: Human-readable string for LLM consumption
        - document: Document object if found, None otherwise

    Raises:
        InvalidSearchParametersError: If parameters are invalid
        DocumentRetrievalError: If retrieval fails
        WeaviateConnectionError: If Weaviate connection fails
    """
    logger.debug(f"Get document by ID: document_id='{document_id}'")

    # Validate parameters
    if not document_id or not document_id.strip():
        raise InvalidSearchParametersError(
            "get_document_by_id",
            "document_id",
            document_id,
            "Document ID cannot be empty",
        )

    try:
        with MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory",
            vector_dimension=1536,
        ) as milvus_client:

            # Use object search to get document by ID
            results = milvus_client.search_with_object(
                object_id=document_id.strip(),
                limit=1,
                return_metadata=[
                    "page_content",
                    "title",
                    "knowledge_source",
                    "chunk_id",
                    "entities",
                    "relationships",
                    "tags",
                    "source_url",
                ],
            )

            if results and len(results) > 0:
                result = results[0]
                if isinstance(result, dict):
                    content = result.get("page_content", "")
                    metadata = result.get("metadata", {})
                    document = Document(page_content=content, metadata=metadata)

                    # Create serialized content for LLM consumption
                    serialized_content = _serialize_documents_for_llm([document])

                    return serialized_content, document

            # No document found
            return "No document found with the specified ID.", None

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Get document by ID failed: {error_msg}")

        # Check if it's a connection error
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise WeaviateConnectionError(error_msg)
        else:
            raise DocumentRetrievalError(document_id, error_msg)
