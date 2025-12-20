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

from datapilotflow.domain.config import settings

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
        index_type: str = "HNSW",
        index_params: Optional[Dict[str, Any]] = None,
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
            index_type (str, optional): Type of index to use. Defaults to "HNSW".
            index_params (Dict[str, Any], optional): Custom index parameters.

        Raises:
            Exception: If connection to Milvus fails.
        """
        self.model = model
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension
        self.index_type = index_type
        self.index_params = index_params or self._get_default_index_params(index_type)

        # Generate unique connection alias if none provided
        if connection_alias is None:
            connection_alias = f"milvus_{id(self)}"
        self.connection_alias = connection_alias

        # Retry connection with exponential backoff for long-running jobs
        max_retries = 5
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.warning(
                        f"Milvus connection attempt {attempt + 1}/{max_retries} after {retry_delay}s delay"
                    )
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff: 5s, 10s, 20s, 40s

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

                # Success - break retry loop
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Milvus connection failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    continue
                else:
                    # Final attempt failed
                    logger.error(f"Failed to initialize MilvusClientWrapper after {max_retries} attempts: {e}")
                    logger.error("Make sure Milvus is running and accessible")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

    def _get_default_index_params(self, index_type: str) -> Dict[str, Any]:
        """
        Get default index parameters based on index type and vector dimension.

        Args:
            index_type: Type of index (HNSW, IVF_FLAT, IVF_PQ, FLAT, etc.)

        Returns:
            Dictionary of optimal index parameters
        """
        if index_type == "HNSW":
            # HNSW: Best for production RAG (high recall, fast search)
            # M: connections per layer (8-64, higher = better recall + more memory)
            # efConstruction: build quality (100-500, higher = better index + slower build)
            return {
                "M": 16,  # Balanced for most use cases
                "efConstruction": 256,  # Good quality/speed tradeoff
            }
        elif index_type == "IVF_FLAT":
            # IVF_FLAT: Good for medium datasets (< 1M vectors)
            # nlist: number of clusters (recommend 4 * sqrt(n))
            # For typical RAG: 128-2048
            return {"nlist": 1024}  # Increased from 128 for better recall
        elif index_type == "IVF_PQ":
            # IVF_PQ: Memory efficient for large datasets (> 1M vectors)
            return {
                "nlist": 2048,
                "m": 8,  # Number of subvectors (must divide dimension evenly)
                "nbits": 8,  # Bits per subvector
            }
        elif index_type == "FLAT":
            # FLAT: Exact search (100% recall, slow for large datasets)
            return {}
        else:
            logger.warning(f"Unknown index type '{index_type}', using HNSW defaults")
            return {"M": 16, "efConstruction": 256}

    def _calculate_search_params(self, limit: int, filter_expr: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate adaptive search parameters based on collection size and query requirements.

        Args:
            limit: Number of results requested
            filter_expr: Optional filter expression (affects search strategy)

        Returns:
            Optimized search parameters for the index type
        """
        try:
            # Get collection size for adaptive parameter calculation
            self.collection.load()
            collection_size = self.collection.num_entities
        except Exception as e:
            logger.warning(f"Could not get collection size: {e}, using default params")
            collection_size = 10000  # Fallback estimate

        if self.index_type == "HNSW":
            # ef: search quality parameter (higher = better recall, slower search)
            # Should be >= top_k, ideally 2-4x top_k for good recall
            # Range: top_k to 512
            ef = max(limit * 3, 64)  # 3x multiplier for high recall
            ef = min(ef, 512)  # Cap at 512 for performance

            logger.debug(f"HNSW search params: ef={ef} (limit={limit}, collection_size={collection_size})")

            return {
                "metric_type": "COSINE",
                "params": {"ef": ef}
            }

        elif self.index_type == "IVF_FLAT":
            # nprobe: number of clusters to search
            # Should be 5-20% of nlist for good recall/performance balance
            nlist = self.index_params.get("nlist", 1024)
            nprobe = max(int(nlist * 0.1), 20)  # 10% of clusters, minimum 20
            nprobe = min(nprobe, nlist)  # Cannot exceed nlist

            logger.debug(f"IVF_FLAT search params: nprobe={nprobe} (nlist={nlist}, limit={limit})")

            return {
                "metric_type": "COSINE",
                "params": {"nprobe": nprobe}
            }

        elif self.index_type == "IVF_PQ":
            # Similar to IVF_FLAT
            nlist = self.index_params.get("nlist", 2048)
            nprobe = max(int(nlist * 0.1), 32)
            nprobe = min(nprobe, nlist)

            return {
                "metric_type": "COSINE",
                "params": {"nprobe": nprobe}
            }

        elif self.index_type == "FLAT":
            # FLAT index doesn't need search params (exact search)
            return {"metric_type": "COSINE"}

        else:
            # Default to COSINE with basic params
            return {"metric_type": "COSINE"}

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
            # Define collection schema with correlation_id as primary key
            # CRITICAL: correlation_id = {source_url}_{chunk_index}_{content_hash}
            # This ensures automatic deduplication via upsert operations
            fields = [
                # Primary key: correlation_id for chunk-level deduplication
                FieldSchema(
                    name="correlation_id", dtype=DataType.VARCHAR, is_primary=True, max_length=512
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
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100),  # Keep for backward compatibility
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="total_chunks", dtype=DataType.INT64),
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

            # Create index for vector field with optimized parameters
            vector_index_params = {
                "metric_type": "COSINE",
                "index_type": self.index_type,
                "params": self.index_params,
            }
            self.collection.create_index(field_name="vector", index_params=vector_index_params)
            logger.info(f"Created {self.index_type} vector index with params: {self.index_params}")

            # Create scalar indexes for efficient filtering
            # STL_SORT for numeric fields
            numeric_index_fields = ["chunk_index"]
            for field_name in numeric_index_fields:
                try:
                    scalar_index_params = {
                        "index_type": "STL_SORT",  # Sorted index for fast range queries
                    }
                    self.collection.create_index(
                        field_name=field_name, index_params=scalar_index_params
                    )
                    logger.info(f"Created STL_SORT index on '{field_name}' for fast filtering")
                except Exception as idx_error:
                    logger.warning(
                        f"Could not create scalar index on {field_name}: {idx_error}"
                    )

            # INVERTED index for VARCHAR fields
            varchar_index_fields = ["job_id"]
            for field_name in varchar_index_fields:
                try:
                    scalar_index_params = {
                        "index_type": "INVERTED",  # Inverted index for VARCHAR fields
                    }
                    self.collection.create_index(
                        field_name=field_name, index_params=scalar_index_params
                    )
                    logger.info(f"Created INVERTED index on '{field_name}' for fast filtering")
                except Exception as idx_error:
                    logger.warning(
                        f"Could not create inverted index on {field_name}: {idx_error}"
                    )

            # Create full-text index for source_url field
            try:
                source_url_index_params = {
                    "index_type": "INVERTED",  # Inverted index for text search
                }
                self.collection.create_index(
                    field_name="source_url", index_params=source_url_index_params
                )
                logger.info(
                    f"Created INVERTED index on 'source_url' for full-text search"
                )
            except Exception as idx_error:
                logger.warning(
                    f"Could not create inverted index on source_url: {idx_error}. "
                    "Full-text search may not be available."
                )

            logger.info(
                f"Created collection '{self.collection_name}' with {self.index_type} vector index "
                f"and scalar indexes for filtering"
            )

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
        """Upsert documents into the Milvus collection using correlation_id as primary key.

        This method uses UPSERT operation which:
        - Inserts new chunks if correlation_id doesn't exist
        - Updates existing chunks if correlation_id already exists

        This ensures automatic deduplication at the chunk level.

        Args:
            documents: List of Pydantic model instances to upsert.
            vectors: List of vector embeddings corresponding to each document.

        Raises:
            ValueError: If documents is empty or vectors don't match documents.
            Exception: If the upsert operation fails.
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

            # Prepare data for upsert
            data = []
            for i, (doc, vector) in enumerate(zip(documents, vectors)):
                doc_dict = doc.model_dump()

                # Generate correlation_id for unique chunk identification (PRIMARY KEY)
                source_url = doc_dict.get("source_url", "")
                chunk_index = doc_dict.get("chunk_index", 0)
                page_content = doc_dict.get("page_content", "")
                content_hash = hashlib.md5(page_content.encode()).hexdigest()
                correlation_id = f"{source_url}_{chunk_index}_{content_hash}"

                data.append(
                    {
                        "correlation_id": correlation_id,  # PRIMARY KEY - must be first
                        "vector": vector,
                        "page_content": page_content,
                        "source_url": source_url,
                        "job_id": doc_dict.get("job_id", ""),
                        "title": doc_dict.get("title", ""),
                        "id": str(uuid.uuid4()),  # Keep for backward compatibility
                        "chunk_id": doc_dict.get("chunk_id", ""),
                        "chunk_index": chunk_index,
                        "total_chunks": doc_dict.get("total_chunks", 1),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )

            # Use UPSERT instead of INSERT for automatic deduplication
            # If correlation_id exists: UPDATE the chunk
            # If correlation_id is new: INSERT the chunk
            self.collection.upsert(data)
            self.collection.flush()

            logger.info(f"Upserted {len(documents)} documents into Milvus (automatic deduplication enabled)")

        except Exception as e:
            logger.error(f"Error upserting documents into Milvus: {e}")
            logger.error(
                f"Connection status: {connections.has_connection(self.connection_alias)}"
            )
            logger.error(f"Collection status: {self.collection is not None}")
            raise

    def search_with_vector(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_expr: Optional[str] = None,
        return_fields: Optional[List[str]] = None,
        distance_threshold: Optional[float] = None,
        use_adaptive_params: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search for documents using a vector query with optimized parameters.

        Args:
            query_vector (List[float]): The vector to search for similar documents.
            limit (int): Maximum number of results to return. Defaults to 5.
            filter_expr (Optional[str]): Filter expression for the search.
            return_fields (Optional[List[str]]): Fields to return in results.
            distance_threshold (Optional[float]): Maximum distance for results (COSINE: 0-2, lower=better).
                Recommended: 0.3-0.5 for high quality, 0.5-0.7 for medium quality.
            use_adaptive_params (bool): Use adaptive search parameters based on collection size.
                Defaults to True.

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

            # Calculate adaptive search parameters
            if use_adaptive_params:
                search_params = self._calculate_search_params(limit, filter_expr)
            else:
                # Fallback to basic params
                search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # Retrieve more candidates if distance threshold is set
            search_limit = limit * 2 if distance_threshold else limit

            # Perform search
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=search_limit,
                expr=filter_expr,
                output_fields=return_fields,
            )

            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    # Apply distance threshold filtering
                    if distance_threshold and hit.distance > distance_threshold:
                        continue

                    # hit.id returns the primary key (now correlation_id)
                    result = {
                        "id": hit.id,  # This is correlation_id now
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

                    # Stop if we have enough results after filtering
                    if len(formatted_results) >= limit:
                        break

            logger.info(
                f"Vector search completed | Index: {self.index_type} | "
                f"Vector dim: {len(query_vector)} | "
                f"Results: {len(formatted_results)}/{search_limit} | "
                f"Distance threshold: {distance_threshold or 'None'}"
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
            # Note: correlation_id is now the primary key
            results = self.collection.query(
                expr=filter_expr or "correlation_id != ''",  # Default filter to get all documents
                output_fields=return_fields,
                limit=limit,
            )

            # Format results
            formatted_results = []
            for result in results:
                # Use correlation_id as the id (it's the primary key now)
                formatted_result = {"id": result.get("correlation_id"), "properties": {}}

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
