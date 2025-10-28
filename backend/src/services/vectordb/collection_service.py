"""
VectorDB Collection Service.

This module provides services for inspecting and retrieving data from
vector database collections without the actual vector embeddings.
"""

import traceback
from typing import Dict, List, Optional

from loguru import logger
from pymilvus import Collection, connections, utility

from src.config import settings
from src.domain.vectordb import (
    CollectionInfo,
    CollectionSchema,
    CollectionStats,
    FieldSchema,
    RecordResponse,
    VectorRecord,
)


class VectorDBCollectionService:
    """Service for interacting with vector database collections."""

    def __init__(self):
        """Initialize the VectorDB collection service."""
        # Use a shared connection alias for collection inspection
        self.connection_alias = "vectordb_inspector"
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensure connection to Milvus is established."""
        try:
            # Check if connection already exists
            if not connections.has_connection(self.connection_alias):
                # Connect with credentials
                connections.connect(
                    alias=self.connection_alias,
                    host=settings.VECTOR_DB_HOST,
                    port=settings.VECTOR_DB_HTTP_PORT,
                    user=settings.VECTOR_DB_USERNAME,
                    password=settings.VECTOR_DB_PASSWORD,
                )
                logger.info(
                    f"Connected to Milvus for collection inspection using alias: {self.connection_alias}"
                )
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _resolve_collection_name(
        self, collection_id: str, user_id: str
    ) -> Optional[str]:
        """
        Resolve MongoDB collection ID to actual Milvus collection name.

        Handles both cases:
        - If collection_id looks like a MongoDB ObjectId (24 hex chars), look it up
        - Otherwise, assume it's already the Milvus collection name

        Args:
            collection_id: Either MongoDB ID or Milvus collection name
            user_id: ID of the user

        Returns:
            Milvus collection name or the original collection_id if not found
        """
        try:
            # Check if this looks like a MongoDB ObjectId (24 hex characters)
            is_mongodb_id = len(collection_id) == 24 and all(
                c in "0123456789abcdefABCDEF" for c in collection_id
            )

            if is_mongodb_id:
                # Try to resolve as MongoDB ID
                from src.services.knowledge.vectordb_collection_service import (
                    get_vectordb_collection_service,
                )

                config_service = get_vectordb_collection_service()
                collection_config = config_service.get_collection(
                    collection_id, user_id
                )

                if collection_config:
                    logger.debug(
                        f"Resolved MongoDB ID {collection_id} to Milvus name: {collection_config.collection_name}"
                    )
                    return collection_config.collection_name
                else:
                    logger.warning(
                        f"MongoDB collection config {collection_id} not found, trying as collection name"
                    )
                    # Fall through to return the original ID

            # Not a MongoDB ID or not found - assume it's already a Milvus collection name
            logger.debug(f"Using {collection_id} as Milvus collection name directly")
            return collection_id

        except Exception as e:
            logger.error(f"Error resolving collection {collection_id}: {e}")
            # On error, return the original ID and let Milvus handle it
            return collection_id

    def list_collections(self, user_id: str) -> List[CollectionInfo]:
        """
        List all vector collections accessible to the user.

        Args:
            user_id: ID of the user requesting collections

        Returns:
            List of collection information
        """
        try:
            self._ensure_connection()

            # Get all collection names
            collection_names = utility.list_collections(using=self.connection_alias)
            logger.info(f"Found {len(collection_names)} collections in Milvus")

            collections_info = []

            for coll_name in collection_names:
                try:
                    collection = Collection(name=coll_name, using=self.connection_alias)

                    # Flush collection to ensure all data is persisted
                    try:
                        collection.flush()
                    except Exception as flush_error:
                        logger.warning(
                            f"Could not flush collection {coll_name}: {flush_error}"
                        )

                    # Load collection to get stats
                    collection.load()

                    # Get collection stats (force refresh)
                    num_entities = collection.num_entities

                    # Get schema to find vector dimension
                    schema = collection.schema
                    vector_dim = None
                    for field in schema.fields:
                        if field.dtype.name.startswith("FLOAT_VECTOR"):
                            vector_dim = field.params.get("dim", 0)
                            break

                    collection_info = CollectionInfo(
                        id=coll_name,
                        name=coll_name,
                        description=schema.description or None,
                        dimension=vector_dim or 0,
                        record_count=num_entities,
                        metric_type=None,  # Can be enhanced later
                        index_type=None,  # Can be enhanced later
                        created_at=None,
                        updated_at=None,
                    )
                    collections_info.append(collection_info)

                except Exception as e:
                    logger.error(f"Error getting info for collection {coll_name}: {e}")
                    continue

            logger.info(f"Retrieved {len(collections_info)} collection(s)")
            return collections_info

        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_collection(
        self, collection_id: str, user_id: str
    ) -> Optional[CollectionInfo]:
        """
        Get detailed information about a specific collection.

        Args:
            collection_id: MongoDB ID or Milvus collection name
            user_id: ID of the user requesting the collection

        Returns:
            Collection information or None if not found
        """
        try:
            # Resolve to Milvus collection name (handles both MongoDB ID and direct name)
            collection_name = self._resolve_collection_name(collection_id, user_id)
            if not collection_name:
                logger.warning(f"Could not resolve collection {collection_id}")
                return None

            # Try to get MongoDB config for additional metadata (optional)
            collection_config = None
            try:
                from src.services.knowledge.vectordb_collection_service import (
                    get_vectordb_collection_service,
                )

                config_service = get_vectordb_collection_service()
                collection_config = config_service.get_collection(
                    collection_id, user_id
                )
            except Exception as e:
                logger.debug(f"Could not get config for {collection_id}: {e}")
                # Continue without config - we'll use Milvus data only

            self._ensure_connection()

            # Check if Milvus collection exists
            if not utility.has_collection(collection_name, using=self.connection_alias):
                logger.warning(f"Milvus collection {collection_name} not found")

                # If we have config, return it even if Milvus collection doesn't exist yet
                if collection_config:
                    return CollectionInfo(
                        id=collection_id,
                        name=collection_name,
                        description=collection_config.description,
                        dimension=collection_config.vector_dimension,
                        record_count=0,
                        metric_type=None,
                        index_type=None,
                        created_at=None,
                        updated_at=None,
                    )
                return None

            # Get Milvus collection info
            collection = Collection(name=collection_name, using=self.connection_alias)
            collection.load()

            schema = collection.schema
            num_entities = collection.num_entities

            # Get vector dimension from schema
            vector_dim = None
            for field in schema.fields:
                if field.dtype.name.startswith("FLOAT_VECTOR"):
                    vector_dim = field.params.get("dim", 0)
                    break

            return CollectionInfo(
                id=collection_id,
                name=collection_name,
                description=(
                    collection_config.description
                    if collection_config
                    else schema.description
                ),
                dimension=vector_dim
                or (collection_config.vector_dimension if collection_config else 0),
                record_count=num_entities,
                metric_type=None,
                index_type=None,
                created_at=None,
                updated_at=None,
            )

        except Exception as e:
            logger.error(f"Error getting collection {collection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_collection_schema(
        self, collection_id: str, user_id: str
    ) -> Optional[CollectionSchema]:
        """
        Get the schema of a collection.

        Args:
            collection_id: MongoDB ID of the VectorDB collection configuration
            user_id: ID of the user requesting the schema

        Returns:
            Collection schema or None if not found
        """
        try:
            # Resolve collection ID to Milvus collection name
            collection_name = self._resolve_collection_name(collection_id, user_id)
            if not collection_name:
                return None

            self._ensure_connection()

            if not utility.has_collection(collection_name, using=self.connection_alias):
                logger.warning(f"Milvus collection {collection_name} not found")
                return None

            collection = Collection(name=collection_name, using=self.connection_alias)
            schema = collection.schema

            fields = []
            for field in schema.fields:
                field_schema = FieldSchema(
                    name=field.name,
                    type=field.dtype.name,
                    is_primary=field.is_primary,
                    auto_id=field.auto_id,
                    dimension=(
                        field.params.get("dim")
                        if field.dtype.name.startswith("FLOAT_VECTOR")
                        else None
                    ),
                    max_length=(
                        field.params.get("max_length")
                        if hasattr(field, "params")
                        else None
                    ),
                    indexed=False,  # Can be enhanced by checking indexes
                )
                fields.append(field_schema)

            return CollectionSchema(collection_id=collection_id, fields=fields)

        except Exception as e:
            logger.error(f"Error getting schema for collection {collection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_collection_stats(
        self, collection_id: str, user_id: str
    ) -> Optional[CollectionStats]:
        """
        Get statistics about a collection.

        Args:
            collection_id: MongoDB ID of the VectorDB collection configuration
            user_id: ID of the user requesting the stats

        Returns:
            Collection statistics or None if not found
        """
        try:
            # Resolve collection ID to Milvus collection name
            collection_name = self._resolve_collection_name(collection_id, user_id)
            if not collection_name:
                return None

            self._ensure_connection()

            if not utility.has_collection(collection_name, using=self.connection_alias):
                logger.warning(f"Milvus collection {collection_name} not found")
                return None

            collection = Collection(name=collection_name, using=self.connection_alias)
            collection.load()

            total_records = collection.num_entities

            # Query to get records by job
            records_by_job: Dict[str, int] = {}

            try:
                # Check if job_id field exists
                schema = collection.schema
                has_job_id = any(field.name == "job_id" for field in schema.fields)

                if has_job_id:
                    # Query all records to count by job_id
                    # Note: This is a simplified approach. For large collections,
                    # consider aggregating this during ingestion
                    results = collection.query(
                        expr="",  # Empty expr to get all
                        output_fields=["job_id"],
                        limit=16384,  # Milvus limit
                    )

                    for record in results:
                        job_id = record.get("job_id", "unknown")
                        records_by_job[job_id] = records_by_job.get(job_id, 0) + 1

            except Exception as e:
                logger.warning(f"Could not aggregate records by job: {e}")

            return CollectionStats(
                collection_id=collection_id,
                total_records=total_records,
                records_by_job=records_by_job,
                date_range=None,  # Can be enhanced
                avg_content_length=None,  # Can be enhanced
                unique_sources=None,  # Can be enhanced
            )

        except Exception as e:
            logger.error(f"Error getting stats for collection {collection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_collection_records(
        self,
        collection_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        job_id: Optional[str] = None,
        source_url: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
    ) -> Optional[RecordResponse]:
        """
        Get records from a collection without vectors.

        Args:
            collection_id: MongoDB ID of the VectorDB collection configuration
            user_id: ID of the user requesting records
            limit: Number of records to return
            offset: Offset for pagination
            job_id: Optional filter by job ID (exact match)
            source_url: Optional filter by source URL (partial/keyword match using TEXT_MATCH)
            search: Optional text search in title/content (not yet implemented)
            sort_by: Optional field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Paginated record response or None if error
        """
        try:
            # Resolve collection ID to Milvus collection name
            collection_name = self._resolve_collection_name(collection_id, user_id)
            if not collection_name:
                return None

            self._ensure_connection()

            if not utility.has_collection(collection_name, using=self.connection_alias):
                logger.warning(f"Milvus collection {collection_name} not found")
                return None

            collection = Collection(name=collection_name, using=self.connection_alias)

            # Flush collection to ensure all data is persisted and counts are accurate
            try:
                collection.flush()
            except Exception as flush_error:
                logger.warning(
                    f"Could not flush collection {collection_name}: {flush_error}"
                )

            collection.load()

            # Get schema to determine available fields
            schema = collection.schema
            output_fields = []
            has_job_id_field = False
            has_source_url_field = False

            for field in schema.fields:
                # Exclude vector fields
                if not field.dtype.name.startswith("FLOAT_VECTOR"):
                    output_fields.append(field.name)
                    if field.name == "job_id":
                        has_job_id_field = True
                    if field.name == "source_url":
                        has_source_url_field = True

            # Build filter expression
            filter_conditions = []

            # Add job_id filter if provided and field exists
            if job_id and has_job_id_field:
                # Escape special characters in job_id
                escaped_job_id = job_id.replace('"', '\\"')
                filter_conditions.append(f'job_id == "{escaped_job_id}"')

            # Add source_url filter if provided and field exists
            if source_url and has_source_url_field:
                # Escape special characters in source_url for exact match
                escaped_url = source_url.replace('"', '\\"')
                # Try different approaches for URL filtering
                # Use exact string matching
                filter_conditions.append(f'source_url == "{escaped_url}"')
                logger.info(f'Applied source_url filter: source_url == "{escaped_url}"')
            elif source_url and not has_source_url_field:
                logger.warning(
                    f"source_url filter requested but field doesn't exist in schema"
                )
            elif source_url:
                logger.warning(
                    f"source_url filter requested but has_source_url_field is {has_source_url_field}"
                )

            # Combine filters with AND
            expr = " && ".join(filter_conditions) if filter_conditions else ""
            logger.info(f"Final filter expression: {expr}")

            # Note: Search parameter is ignored as Milvus doesn't support full-text search
            # For text search, we would need to retrieve all records and filter in Python
            if search:
                logger.warning(
                    f"Text search parameter '{search}' is provided but not supported by Milvus. "
                    "Consider implementing client-side filtering for text search."
                )

            # Query records
            try:
                if expr:
                    logger.info(
                        f"Querying collection {collection_id} with filter: {expr}"
                    )
                    results = collection.query(
                        expr=expr,
                        output_fields=output_fields,
                        limit=limit,
                        offset=offset,
                    )
                else:
                    # Query all records if no filter
                    logger.info(f"Querying collection {collection_id} without filter")
                    results = collection.query(
                        expr="",
                        output_fields=output_fields,
                        limit=limit,
                        offset=offset,
                    )
            except Exception as query_error:
                logger.error(f"Query error: {query_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Fallback: query without expression
                results = collection.query(
                    expr="",
                    output_fields=output_fields,
                    limit=limit,
                    offset=offset,
                )

            # Convert results to VectorRecord objects
            records = []
            logger.info(f"Retrieved {len(results)} records from Milvus")

            # Log first few source_urls for debugging
            for i, record in enumerate(results[:5]):
                source_url = record.get("source_url", "N/A")
                logger.info(f"Record {i+1} source_url: {source_url}")

            # If we have a source_url filter, also log some URLs that contain the search term
            if source_url:
                matching_urls = []
                for record in results:
                    record_url = record.get("source_url", "")
                    if source_url.lower() in record_url.lower():
                        matching_urls.append(record_url)
                        if len(matching_urls) >= 3:  # Show first 3 matches
                            break
                if matching_urls:
                    logger.info(
                        f"Found {len(matching_urls)} URLs containing '{source_url}': {matching_urls}"
                    )
                else:
                    logger.warning(
                        f"No URLs found containing '{source_url}' in the first {len(results)} records"
                    )

            for record in results:
                vector_record = VectorRecord(
                    id=str(record.get("id", record.get("pk", ""))),
                    source_url=record.get("source_url"),
                    job_id=record.get("job_id"),
                    title=record.get("title"),
                    page_content=record.get("page_content"),
                    chunk_index=record.get("chunk_index"),
                    total_chunks=record.get("total_chunks"),
                    created_at=record.get("created_at"),
                    metadata={
                        k: v
                        for k, v in record.items()
                        if k
                        not in [
                            "id",
                            "pk",
                            "source_url",
                            "job_id",
                            "title",
                            "page_content",
                            "chunk_index",
                            "total_chunks",
                            "created_at",
                        ]
                    },
                )
                records.append(vector_record)

            # Calculate total based on whether filters are applied
            if expr:
                # When filters are applied, get the count of filtered records
                count_results = collection.query(
                    expr=expr,
                    output_fields=["id"],
                    limit=16384,  # Max limit to get all matching records
                )
                total = len(count_results)
            else:
                # When no filters, use total collection count
                total = collection.num_entities

            return RecordResponse(
                collection_id=collection_id,
                total=total,
                limit=limit,
                offset=offset,
                records=records,
            )

        except Exception as e:
            logger.error(f"Error getting records for collection {collection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


# Singleton instance
_vectordb_collection_service: Optional[VectorDBCollectionService] = None


def get_vectordb_collection_service() -> VectorDBCollectionService:
    """Get the VectorDB collection service singleton instance."""
    global _vectordb_collection_service

    if _vectordb_collection_service is None:
        _vectordb_collection_service = VectorDBCollectionService()

    return _vectordb_collection_service
