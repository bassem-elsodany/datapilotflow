"""
Milvus Utility Functions.

This module provides utility functions for common Milvus operations,
data transformations, and helper functions.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pymilvus import CollectionSchema, DataType, FieldSchema


def create_vector_field_schema(
    name: str = "vector",
    dim: int = 1536,
    description: str = "Vector field for similarity search",
) -> FieldSchema:
    """Create a vector field schema for Milvus collections.

    Args:
        name (str): Name of the vector field.
        dim (int): Dimension of the vector.
        description (str): Description of the field.

    Returns:
        FieldSchema: Milvus field schema for vector field.
    """
    return FieldSchema(
        name=name, dtype=DataType.FLOAT_VECTOR, dim=dim, description=description
    )


def create_varchar_field_schema(
    name: str, max_length: int = 100, is_primary: bool = False, description: str = ""
) -> FieldSchema:
    """Create a varchar field schema for Milvus collections.

    Args:
        name (str): Name of the field.
        max_length (int): Maximum length of the varchar field.
        is_primary (bool): Whether this field is the primary key.
        description (str): Description of the field.

    Returns:
        FieldSchema: Milvus field schema for varchar field.
    """
    return FieldSchema(
        name=name,
        dtype=DataType.VARCHAR,
        max_length=max_length,
        is_primary=is_primary,
        description=description,
    )


def create_int_field_schema(name: str, description: str = "") -> FieldSchema:
    """Create an integer field schema for Milvus collections.

    Args:
        name (str): Name of the field.
        description (str): Description of the field.

    Returns:
        FieldSchema: Milvus field schema for integer field.
    """
    return FieldSchema(name=name, dtype=DataType.INT64, description=description)


def create_float_field_schema(name: str, description: str = "") -> FieldSchema:
    """Create a float field schema for Milvus collections.

    Args:
        name (str): Name of the field.
        description (str): Description of the field.

    Returns:
        FieldSchema: Milvus field schema for float field.
    """
    return FieldSchema(name=name, dtype=DataType.FLOAT, description=description)


def create_bool_field_schema(name: str, description: str = "") -> FieldSchema:
    """Create a boolean field schema for Milvus collections.

    Args:
        name (str): Name of the field.
        description (str): Description of the field.

    Returns:
        FieldSchema: Milvus field schema for boolean field.
    """
    return FieldSchema(name=name, dtype=DataType.BOOL, description=description)


def create_document_collection_schema(
    collection_name: str, vector_dim: int = 1536, enable_dynamic_field: bool = True
) -> CollectionSchema:
    """Create a standard document collection schema for Milvus.

    Args:
        collection_name (str): Name of the collection.
        vector_dim (int): Dimension of the vector field.
        enable_dynamic_field (bool): Whether to enable dynamic fields.

    Returns:
        CollectionSchema: Milvus collection schema for document storage.
    """
    fields = [
        create_varchar_field_schema(
            name="id",
            max_length=100,
            is_primary=True,
            description="Unique document identifier",
        ),
        create_vector_field_schema(
            name="vector", dim=vector_dim, description="Document embedding vector"
        ),
        create_varchar_field_schema(
            name="text", max_length=65535, description="Document text content"
        ),
        create_varchar_field_schema(
            name="metadata",
            max_length=65535,
            description="Document metadata as JSON string",
        ),
        create_varchar_field_schema(
            name="source_url", max_length=2048, description="Source URL of the document"
        ),
        create_varchar_field_schema(
            name="title", max_length=1024, description="Document title"
        ),
        create_varchar_field_schema(
            name="chunk_id", max_length=100, description="Chunk identifier"
        ),
        create_int_field_schema(
            name="chunk_index", description="Index of this chunk in the document"
        ),
        create_int_field_schema(
            name="total_chunks", description="Total number of chunks in the document"
        ),
        create_varchar_field_schema(
            name="created_at", max_length=50, description="Creation timestamp"
        ),
    ]

    return CollectionSchema(
        fields=fields,
        description=f"Collection for storing {collection_name} documents with vector search",
        enable_dynamic_field=enable_dynamic_field,
    )


def prepare_document_data(
    document_id: str, vector: List[float], text: str, metadata: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """Prepare document data for insertion into Milvus.

    Args:
        document_id (str): Unique identifier for the document.
        vector (List[float]): Vector embedding of the document.
        text (str): Text content of the document.
        metadata (Dict[str, Any]): Metadata dictionary.
        **kwargs: Additional fields to include.

    Returns:
        Dict[str, Any]: Prepared data dictionary for Milvus insertion.
    """
    # Prepare metadata as JSON string
    metadata_json = json.dumps(metadata, default=str)

    # Base data structure
    data = {
        "id": document_id,
        "vector": vector,
        "text": text,
        "metadata": metadata_json,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Add metadata fields as separate columns for better filtering
    data.update(
        {
            "source_url": metadata.get("source_url", ""),
            "title": metadata.get("title", ""),
            "chunk_id": metadata.get("chunk_id", ""),
            "chunk_index": metadata.get("chunk_index", 0),
            "total_chunks": metadata.get("total_chunks", 1),
        }
    )

    # Add any additional fields
    data.update(kwargs)

    return data


def parse_search_results(
    results: List[Any], include_metadata: bool = True
) -> List[Dict[str, Any]]:
    """Parse Milvus search results into a standardized format.

    Args:
        results (List[Any]): Raw search results from Milvus.
        include_metadata (bool): Whether to parse and include metadata.

    Returns:
        List[Dict[str, Any]]: Parsed search results.
    """
    parsed_results = []

    for result in results:
        parsed_result = {
            "id": result.id,
            "distance": result.distance,
            "score": 1 - result.distance,  # Convert distance to similarity score
            "properties": {},
        }

        # Extract entity properties
        if hasattr(result, "entity"):
            entity = result.entity
            for field_name in entity._field_names:
                value = getattr(entity, field_name)
                parsed_result["properties"][field_name] = value

        # Parse metadata if requested
        if include_metadata and "metadata" in parsed_result["properties"]:
            try:
                metadata = json.loads(parsed_result["properties"]["metadata"])
                parsed_result["properties"].update(metadata)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse metadata: {e}")

        parsed_results.append(parsed_result)

    return parsed_results


def build_filter_expression(
    filters: Dict[str, Any], field_mappings: Optional[Dict[str, str]] = None
) -> str:
    """Build a Milvus filter expression from a dictionary of filters.

    Args:
        filters (Dict[str, Any]): Dictionary of field filters.
        field_mappings (Optional[Dict[str, str]]): Mapping of logical field names to actual field names.

    Returns:
        str: Milvus filter expression string.

    Example:
        filters = {
            "source_url": "https://example.com",
            "chunk_index": {"$gte": 0, "$lt": 10}
        }
        expression = build_filter_expression(filters)
        # Returns: 'source_url == "https://example.com" and chunk_index >= 0 and chunk_index < 10'
    """
    if not filters:
        return ""

    expressions = []
    field_mappings = field_mappings or {}

    for field, value in filters.items():
        # Map field name if mapping exists
        actual_field = field_mappings.get(field, field)

        if isinstance(value, dict):
            # Handle range operators
            for operator, op_value in value.items():
                if operator == "$eq":
                    expressions.append(f'{actual_field} == "{op_value}"')
                elif operator == "$ne":
                    expressions.append(f'{actual_field} != "{op_value}"')
                elif operator == "$gt":
                    expressions.append(f"{actual_field} > {op_value}")
                elif operator == "$gte":
                    expressions.append(f"{actual_field} >= {op_value}")
                elif operator == "$lt":
                    expressions.append(f"{actual_field} < {op_value}")
                elif operator == "$lte":
                    expressions.append(f"{actual_field} <= {op_value}")
                elif operator == "$in":
                    if isinstance(op_value, list):
                        value_list = '", "'.join(str(v) for v in op_value)
                        expressions.append(f'{actual_field} in ["{value_list}"]')
                elif operator == "$nin":
                    if isinstance(op_value, list):
                        value_list = '", "'.join(str(v) for v in op_value)
                        expressions.append(f'{actual_field} not in ["{value_list}"]')
        else:
            # Simple equality
            if isinstance(value, str):
                expressions.append(f'{actual_field} == "{value}"')
            else:
                expressions.append(f"{actual_field} == {value}")

    return " and ".join(expressions)


def validate_vector_dimension(
    vector: List[float], expected_dim: int, field_name: str = "vector"
) -> None:
    """Validate that a vector has the expected dimension.

    Args:
        vector (List[float]): Vector to validate.
        expected_dim (int): Expected dimension.
        field_name (str): Name of the field for error messages.

    Raises:
        ValueError: If vector dimension doesn't match expected dimension.
    """
    if len(vector) != expected_dim:
        raise ValueError(
            f"{field_name} has dimension {len(vector)}, expected {expected_dim}"
        )


def batch_insert_data(
    data: List[Dict[str, Any]], batch_size: int = 1000
) -> List[List[Dict[str, Any]]]:
    """Split data into batches for efficient insertion.

    Args:
        data (List[Dict[str, Any]]): Data to batch.
        batch_size (int): Size of each batch.

    Returns:
        List[List[Dict[str, Any]]]: List of data batches.
    """
    batches = []
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        batches.append(batch)

    logger.debug(
        f"Split {len(data)} records into {len(batches)} batches of max size {batch_size}"
    )
    return batches


def get_optimal_batch_size(
    vector_dim: int, available_memory_gb: float = 4.0, safety_factor: float = 0.8
) -> int:
    """Calculate optimal batch size based on vector dimension and available memory.

    Args:
        vector_dim (int): Dimension of vectors.
        available_memory_gb (float): Available memory in GB.
        safety_factor (float): Safety factor to avoid memory issues.

    Returns:
        int: Optimal batch size.
    """
    # Rough calculation: each float is 4 bytes, plus overhead for other fields
    bytes_per_vector = vector_dim * 4 + 1000  # 1000 bytes overhead for other fields
    available_bytes = available_memory_gb * 1024 * 1024 * 1024 * safety_factor
    optimal_batch_size = int(available_bytes / bytes_per_vector)

    # Cap at reasonable limits
    optimal_batch_size = min(optimal_batch_size, 10000)  # Max 10k records
    optimal_batch_size = max(optimal_batch_size, 100)  # Min 100 records

    logger.debug(
        f"Calculated optimal batch size: {optimal_batch_size} "
        f"(vector_dim: {vector_dim}, memory: {available_memory_gb}GB)"
    )

    return optimal_batch_size
