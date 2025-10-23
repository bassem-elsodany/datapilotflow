"""
Milvus Client Wrapper for vector database operations.

This module provides a wrapper class for Milvus operations that provides a clean interface
for CRUD operations on vector data and Pydantic models.
"""

import hashlib
import json
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from pydantic import BaseModel
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusException,
    connections,
    utility,
)

from src.config import settings

T = TypeVar("T", bound=BaseModel)


class MilvusClientWrapper(Generic[T]):
    """Service class for Milvus operations, supporting ingestion, querying, and validation.

    This class provides methods to interact with Milvus collections, including document
    ingestion, vector search, and validation operations.

    Args:
        model (Type[T]): The Pydantic model class to use for document serialization.
        collection_name (str): Name of the Milvus collection to use.
        milvus_host (str, optional): Host for connecting to Milvus instance.
        milvus_port (str, optional): Port for connecting to Milvus instance.
        milvus_user (str, optional): Username for Milvus authentication.
        milvus_password (str, optional): Password for Milvus authentication.
        vector_dimension (int, optional): Dimension of the vector field.

    Attributes:
        model (Type[T]): The Pydantic model class used for document serialization.
        collection_name (str): Name of the Milvus collection.
        collection (Collection): Milvus collection instance for database operations.
    """

    def __init__(
        self,
        model: Type[T],
        collection_name: str,
        vector_dimension: int,
        milvus_host: str = settings.VECTOR_DB_HOST,
        milvus_port: str = str(settings.VECTOR_DB_HTTP_PORT),
        milvus_user: str = settings.VECTOR_DB_USERNAME,
        milvus_password: str = settings.VECTOR_DB_PASSWORD,
        connection_alias: Optional[str] = None,
    ) -> None:
        """Initialize a connection to the Milvus instance.

        Args:
            model (Type[T]): The Pydantic model class to use for document serialization.
            collection_name (str): Name of the Milvus collection to use.
            vector_dimension (int): Dimension of the vector field.
            milvus_host (str, optional): Host for connecting to Milvus instance.
            milvus_port (str, optional): Port for connecting to Milvus instance.
            milvus_user (str, optional): Username for Milvus authentication.
            milvus_password (str, optional): Password for Milvus authentication.
            connection_alias (str, optional): Alias for the connection.

        Raises:
            Exception: If connection to Milvus fails.
        """
        self.model = model
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension

        # Generate unique connection alias if none provided
        if connection_alias is None:
            connection_alias = f"milvus_{id(self)}"
        self.connection_alias = connection_alias

        try:
            logger.info(
                f"Connecting to Milvus: host={milvus_host}, port={milvus_port}, alias={connection_alias}"
            )

            # Connect to Milvus
            if milvus_user and milvus_password:
                connections.connect(
                    alias=connection_alias,
                    host=milvus_host,
                    port=milvus_port,
                    user=milvus_user,
                    password=milvus_password,
                )
            else:
                connections.connect(
                    alias=connection_alias, host=milvus_host, port=milvus_port
                )

            # Test connection
            if not connections.has_connection(connection_alias):
                raise Exception("Failed to establish connection to Milvus")

            logger.info(
                f"Successfully connected to Milvus with alias: {connection_alias}"
            )

            # Initialize or get collection
            self._initialize_collection()

            logger.info(
                f"Connected to Milvus instance: Host: {milvus_host}:{milvus_port} | Collection: {collection_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize MilvusClientWrapper: {e}")
            logger.error("Make sure Milvus is running and accessible")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _initialize_collection(self) -> None:
        """Initialize or get the Milvus collection with proper schema."""
        try:
            # Check if collection exists
            if utility.has_collection(
                self.collection_name, using=self.connection_alias
            ):
                self.collection = Collection(
                    self.collection_name, using=self.connection_alias
                )
                logger.debug(f"Using existing collection: {self.collection_name}")
            else:
                # Create collection with schema
                self._create_collection()
                logger.info(f"Created new collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise

    def _create_collection(self) -> None:
        """Create a new Milvus collection with appropriate schema."""
        try:
            # Define collection schema to match Weaviate structure
            fields = [
                FieldSchema(
                    name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100
                ),
                FieldSchema(
                    name="vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.vector_dimension,
                ),
                # Core content fields
                FieldSchema(
                    name="page_content", dtype=DataType.VARCHAR, max_length=65535
                ),
                # Enable full-text search on source_url for partial matching
                FieldSchema(
                    name="source_url",
                    dtype=DataType.VARCHAR,
                    max_length=2048,
                    enable_analyzer=True,  # Enable tokenization for full-text search
                ),
                FieldSchema(name="job_id", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1024),
                # Cross-reference properties
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="total_chunks", dtype=DataType.INT64),
                FieldSchema(
                    name="correlation_id", dtype=DataType.VARCHAR, max_length=512
                ),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
            ]

            schema = CollectionSchema(
                fields=fields,
                description=f"Collection for {self.collection_name}",
                enable_dynamic_field=True,
            )

            # Create collection
            self.collection = Collection(
                name=self.collection_name, schema=schema, using=self.connection_alias
            )

            # Create index for vector field
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self.collection.create_index(field_name="vector", index_params=index_params)

            # Create full-text index for source_url field
            try:
                source_url_index_params = {
                    "index_type": "INVERTED",  # Inverted index for text search
                }
                self.collection.create_index(
                    field_name="source_url", index_params=source_url_index_params
                )
                logger.info(
                    f"Created inverted index on source_url field for full-text search"
                )
            except Exception as idx_error:
                logger.warning(
                    f"Could not create inverted index on source_url: {idx_error}. "
                    "Full-text search may not be available."
                )

            logger.info(f"Created collection {self.collection_name} with vector index")

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def __enter__(self) -> "MilvusClientWrapper":
        """Enable context manager support.

        Returns:
            MilvusClientWrapper: The current instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close Milvus connection when exiting context.

        Args:
            exc_type: Type of exception that occurred, if any.
            exc_val: Exception instance that occurred, if any.
            exc_tb: Traceback of exception that occurred, if any.
        """
        self.close()

    def clear_collection(self) -> None:
        """Remove all objects from the collection.

        This method deletes all objects in the collection to avoid duplicates
        during reingestion.

        Raises:
            Exception: If the deletion operation fails.
        """
        try:
            logger.info(
                f"CLEAR COLLECTION STARTED: Checking collection {self.collection_name}"
            )

            # Check if collection exists
            collection_exists = utility.has_collection(
                self.collection_name, using=self.connection_alias
            )
            logger.info(
                f"Collection {self.collection_name} exists: {collection_exists}"
            )

            if collection_exists:
                # Get count before dropping
                try:
                    count_before = self.collection.num_entities
                    logger.info(
                        f"Collection {self.collection_name} has {count_before} entities BEFORE clearing"
                    )
                except Exception as count_error:
                    logger.warning(
                        f"Could not get entity count before clearing: {count_error}"
                    )

                # Drop the collection
                logger.info(f"DROPPING collection {self.collection_name}...")
                utility.drop_collection(
                    self.collection_name, using=self.connection_alias
                )
                logger.info(f"Collection {self.collection_name} DROPPED successfully")

                # Recreate the collection
                logger.info(f"RECREATING collection {self.collection_name}...")
                self._create_collection()
                logger.info(f"Collection {self.collection_name} RECREATED successfully")

                # Verify it's empty
                try:
                    count_after = self.collection.num_entities
                    logger.info(
                        f"Collection {self.collection_name} has {count_after} entities AFTER clearing (should be 0)"
                    )
                    if count_after > 0:
                        logger.error(
                            f"WARNING: Collection still has {count_after} entities after clearing!"
                        )
                except Exception as verify_error:
                    logger.warning(
                        f"Could not verify entity count after clearing: {verify_error}"
                    )

            else:
                logger.info(
                    f"Collection {self.collection_name} does not exist, nothing to clear"
                )
                # Create the collection if it doesn't exist
                logger.info(f"CREATING new collection {self.collection_name}...")
                self._create_collection()
                logger.info(f"Collection {self.collection_name} CREATED successfully")

            logger.info(f"CLEAR COLLECTION COMPLETED: {self.collection_name}")

        except Exception as e:
            logger.error(
                f"CRITICAL ERROR clearing the collection {self.collection_name}: {e}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def ingest_documents(self, documents: List[T], vectors: List[List[float]]) -> None:
        """Insert multiple documents into the Milvus collection.

        Args:
            documents: List of Pydantic model instances to insert.
            vectors: List of vector embeddings corresponding to each document.

        Raises:
            ValueError: If documents is empty or vectors don't match documents.
            Exception: If the insertion operation fails.
        """
        try:
            if not documents:
                raise ValueError("Documents list cannot be empty.")

            if len(documents) != len(vectors):
                raise ValueError("Number of documents must match number of vectors")

            # Validate vectors
            for i, vector in enumerate(vectors):
                if len(vector) != self.vector_dimension:
                    raise ValueError(
                        f"Vector {i} has dimension {len(vector)}, expected {self.vector_dimension}"
                    )

            # Check connection before proceeding
            if not connections.has_connection(self.connection_alias):
                raise Exception(
                    f"No active connection to Milvus with alias '{self.connection_alias}'"
                )

            # Prepare data for insertion to match Weaviate schema structure
            data = []
            for i, (doc, vector) in enumerate(zip(documents, vectors)):
                doc_dict = doc.model_dump()

                # Generate correlation_id for unique chunk identification
                source_url = doc_dict.get("source_url", "")
                chunk_index = doc_dict.get("chunk_index", 0)
                page_content = doc_dict.get("page_content", "")
                content_hash = hashlib.md5(page_content.encode()).hexdigest()
                correlation_id = f"{source_url}_{chunk_index}_{content_hash}"

                data.append(
                    {
                        "id": str(uuid.uuid4()),  # Use proper UUID for Milvus
                        "vector": vector,
                        "page_content": page_content,
                        "source_url": source_url,
                        "job_id": doc_dict.get("job_id", ""),
                        "title": doc_dict.get("title", ""),
                        "chunk_id": doc_dict.get("chunk_id", ""),
                        "chunk_index": chunk_index,
                        "total_chunks": doc_dict.get("total_chunks", 1),
                        "correlation_id": correlation_id,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )

            # Insert data
            self.collection.insert(data)
            self.collection.flush()

            logger.debug(f"Inserted {len(documents)} documents into Milvus")

        except Exception as e:
            logger.error(f"Error inserting documents into Milvus: {e}")
            logger.error(
                f"Connection status: {connections.has_connection(self.connection_alias)}"
            )
            logger.error(f"Collection status: {self.collection is not None}")
            raise

    def search_with_vector(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_expr: Optional[str] = None,
        return_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for documents using a vector query.

        Args:
            query_vector (List[float]): The vector to search for similar documents.
            limit (int): Maximum number of results to return. Defaults to 10.
            filter_expr (Optional[str]): Filter expression for the search.
            return_fields (Optional[List[str]]): Fields to return in results.

        Returns:
            List[Dict[str, Any]]: List of search results with properties and metadata.

        Raises:
            Exception: If the search operation fails.
        """
        try:
            if len(query_vector) != self.vector_dimension:
                raise ValueError(
                    f"Query vector has dimension {len(query_vector)}, expected {self.vector_dimension}"
                )

            # Load collection into memory
            self.collection.load()

            # Set default return fields to match Weaviate schema
            if return_fields is None:
                return_fields = [
                    "id",
                    "page_content",
                    "source_url",
                    "knowledge_source",
                    "title",
                    "keywords",
                    "author",
                    "chunk_id",
                    "document_id",
                    "chunk_index",
                    "total_chunks",
                    "correlation_id",
                    "created_at",
                ]

            # Build search parameters
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # Perform search
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                expr=filter_expr,
                output_fields=return_fields,
            )

            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "distance": hit.distance,
                        "score": 1
                        - hit.distance,  # Convert distance to similarity score
                        "properties": {},
                    }

                    # Extract properties from entity
                    for field in return_fields:
                        if hasattr(hit.entity, field):
                            value = getattr(hit.entity, field)
                            result["properties"][field] = value

                    formatted_results.append(result)

            logger.info(
                f"Vector search completed | Vector dimension: {len(query_vector)} | Results: {len(formatted_results)}"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def search_with_text(
        self,
        query_text: str,
        limit: int = 10,
        filter_expr: Optional[str] = None,
        return_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for documents using text similarity (requires text embedding).

        Note: This method requires the query text to be converted to a vector first.
        For now, it's a placeholder that would need integration with an embedding service.

        Args:
            query_text (str): The text query to search for similar documents.
            limit (int): Maximum number of results to return. Defaults to 10.
            filter_expr (Optional[str]): Filter expression for the search.
            return_fields (Optional[List[str]]): Fields to return in results.

        Returns:
            List[Dict[str, Any]]: List of search results with properties and metadata.

        Raises:
            Exception: If the search operation fails.
        """
        try:
            # TODO: Integrate with embedding service to convert text to vector
            # For now, this is a placeholder implementation
            logger.warning(
                "Text search requires embedding service integration - not implemented yet"
            )

            # This would require:
            # 1. Convert query_text to vector using embedding service
            # 2. Call search_with_vector with the generated vector

            return []

        except Exception as e:
            logger.error(f"Error in text search: {e}")
            raise

    def fetch_documents(
        self,
        limit: int,
        filter_expr: Optional[str] = None,
        return_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from the Milvus collection based on filters.

        Args:
            limit (int): Maximum number of documents to retrieve.
            filter_expr (Optional[str]): Filter expression to apply.
            return_fields (Optional[List[str]]): Fields to return in results.

        Returns:
            List[Dict[str, Any]]: List of documents matching the criteria.

        Raises:
            Exception: If the query operation fails.
        """
        try:
            # Load collection into memory
            self.collection.load()

            # Set default return fields to match Weaviate schema
            if return_fields is None:
                return_fields = [
                    "id",
                    "page_content",
                    "source_url",
                    "knowledge_source",
                    "title",
                    "keywords",
                    "author",
                    "chunk_id",
                    "document_id",
                    "chunk_index",
                    "total_chunks",
                    "correlation_id",
                    "created_at",
                ]

            # Query documents
            results = self.collection.query(
                expr=filter_expr or "id != ''",  # Default filter to get all documents
                output_fields=return_fields,
                limit=limit,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {"id": result.get("id"), "properties": {}}

                # Extract properties
                for field in return_fields:
                    if field in result:
                        value = result[field]
                        formatted_result["properties"][field] = value

                formatted_results.append(formatted_result)

            logger.debug(f"Fetched {len(formatted_results)} documents")
            return formatted_results

        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_collection_count(self) -> int:
        """Count the total number of objects in the collection.

        Returns:
            int: Total number of objects in the collection.

        Raises:
            Exception: If the count operation fails.
        """
        try:
            self.collection.load()
            return self.collection.num_entities
        except Exception as e:
            logger.error(f"Error counting documents in Milvus: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def create_index(
        self,
        field_name: str = "vector",
        index_type: str = "IVF_FLAT",
        metric_type: str = "COSINE",
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create an index on the specified field.

        Args:
            field_name (str): Name of the field to create index on.
            index_type (str): Type of index to create.
            metric_type (str): Metric type for vector similarity.
            params (Optional[Dict[str, Any]]): Additional parameters for the index.

        Raises:
            Exception: If the index creation fails.
        """
        try:
            if params is None:
                params = {"nlist": 128}

            index_params = {
                "metric_type": metric_type,
                "index_type": index_type,
                "params": params,
            }

            self.collection.create_index(
                field_name=field_name, index_params=index_params
            )

            logger.info(f"Created index on field {field_name} with type {index_type}")

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def drop_index(self, field_name: str = "vector") -> None:
        """Drop an index from the specified field.

        Args:
            field_name (str): Name of the field to drop index from.

        Raises:
            Exception: If the index drop fails.
        """
        try:
            self.collection.drop_index(field_name=field_name)
            logger.info(f"Dropped index from field {field_name}")

        except Exception as e:
            logger.error(f"Error dropping index: {e}")
            raise

    def close(self) -> None:
        """Close the Milvus connection.

        This method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """
        try:
            if connections.has_connection(self.connection_alias):
                connections.disconnect(self.connection_alias)
            logger.debug("Closed Milvus connection.")
        except Exception as e:
            logger.warning(f"Error closing Milvus connection: {e}")
