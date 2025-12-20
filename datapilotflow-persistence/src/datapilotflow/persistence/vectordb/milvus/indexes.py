"""
Milvus Index Management Utilities.

This module provides utilities for creating and managing indexes in Milvus collections.
"""

from typing import Dict, Any, Optional
from loguru import logger
from pymilvus import Collection, MilvusException

from .client import MilvusClientWrapper


class MilvusIndex:
    """Utility class for managing Milvus indexes."""

    def __init__(self, milvus_client: MilvusClientWrapper) -> None:
        """Initialize with a Milvus client wrapper.

        Args:
            milvus_client (MilvusClientWrapper): The Milvus client wrapper instance.
        """
        self.milvus_client = milvus_client
        self.collection = milvus_client.collection

    def create_vector_index(
        self,
        field_name: str = "vector",
        index_type: str = "IVF_FLAT",
        metric_type: str = "COSINE",
        nlist: int = 128,
        nbits: int = 8
    ) -> None:
        """Create a vector index for similarity search.

        Args:
            field_name (str): Name of the vector field to index.
            index_type (str): Type of index to create.
                Options: 'IVF_FLAT', 'IVF_SQ8', 'IVF_PQ', 'HNSW', 'ANNOY'
            metric_type (str): Distance metric for similarity calculation.
                Options: 'L2', 'IP', 'COSINE', 'HAMMING', 'JACCARD'
            nlist (int): Number of clusters for IVF indexes.
            nbits (int): Number of bits for PQ indexes.

        Raises:
            MilvusException: If index creation fails.
        """
        try:
            # Define index parameters based on index type
            if index_type == "IVF_FLAT":
                params = {"nlist": nlist}
            elif index_type == "IVF_SQ8":
                params = {"nlist": nlist}
            elif index_type == "IVF_PQ":
                params = {"nlist": nlist, "m": 8, "nbits": nbits}
            elif index_type == "HNSW":
                params = {"M": 16, "efConstruction": 200}
            elif index_type == "ANNOY":
                params = {"n_trees": 8}
            else:
                raise ValueError(f"Unsupported index type: {index_type}")

            index_params = {
                "metric_type": metric_type,
                "index_type": index_type,
                "params": params
            }

            self.collection.create_index(
                field_name=field_name,
                index_params=index_params
            )

            logger.info(
                f"Created {index_type} index on field '{field_name}' "
                f"with metric '{metric_type}' and params: {params}"
            )

        except MilvusException as e:
            logger.error(f"Failed to create vector index: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating vector index: {e}")
            raise

    def create_scalar_index(
        self,
        field_name: str,
        index_type: str = "STL_SORT"
    ) -> None:
        """Create a scalar index for filtering operations.

        Args:
            field_name (str): Name of the scalar field to index.
            index_type (str): Type of scalar index to create.
                Options: 'STL_SORT', 'Trie'

        Raises:
            MilvusException: If index creation fails.
        """
        try:
            index_params = {
                "index_type": index_type
            }

            self.collection.create_index(
                field_name=field_name,
                index_params=index_params
            )

            logger.info(f"Created {index_type} index on scalar field '{field_name}'")

        except MilvusException as e:
            logger.error(f"Failed to create scalar index: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating scalar index: {e}")
            raise

    def create_hybrid_index(
        self,
        vector_field: str = "vector",
        scalar_fields: Optional[list] = None,
        vector_index_type: str = "IVF_FLAT",
        vector_metric_type: str = "COSINE",
        scalar_index_type: str = "STL_SORT"
    ) -> None:
        """Create both vector and scalar indexes for hybrid search.

        Args:
            vector_field (str): Name of the vector field.
            scalar_fields (Optional[list]): List of scalar fields to index.
            vector_index_type (str): Type of vector index.
            vector_metric_type (str): Metric type for vector similarity.
            scalar_index_type (str): Type of scalar index.

        Raises:
            MilvusException: If index creation fails.
        """
        try:
            # Create vector index
            self.create_vector_index(
                field_name=vector_field,
                index_type=vector_index_type,
                metric_type=vector_metric_type
            )

            # Create scalar indexes
            if scalar_fields:
                for field in scalar_fields:
                    self.create_scalar_index(
                        field_name=field,
                        index_type=scalar_index_type
                    )

            logger.info(
                f"Created hybrid indexes: vector index on '{vector_field}' "
                f"and scalar indexes on {scalar_fields or 'no scalar fields'}"
            )

        except Exception as e:
            logger.error(f"Failed to create hybrid indexes: {e}")
            raise

    def drop_index(self, field_name: str) -> None:
        """Drop an index from the specified field.

        Args:
            field_name (str): Name of the field to drop index from.

        Raises:
            MilvusException: If index drop fails.
        """
        try:
            self.collection.drop_index(field_name=field_name)
            logger.info(f"Dropped index from field '{field_name}'")

        except MilvusException as e:
            logger.error(f"Failed to drop index: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error dropping index: {e}")
            raise

    def list_indexes(self) -> Dict[str, Any]:
        """List all indexes in the collection.

        Returns:
            Dict[str, Any]: Dictionary containing index information.

        Raises:
            MilvusException: If listing indexes fails.
        """
        try:
            indexes = self.collection.indexes
            index_info = {}

            for index in indexes:
                field_name = index.field_name
                index_info[field_name] = {
                    "index_type": index.params.get("index_type"),
                    "metric_type": index.params.get("metric_type"),
                    "params": index.params.get("params", {})
                }

            logger.debug(f"Listed {len(index_info)} indexes")
            return index_info

        except MilvusException as e:
            logger.error(f"Failed to list indexes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing indexes: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about indexes in the collection.

        Returns:
            Dict[str, Any]: Dictionary containing index statistics.

        Raises:
            MilvusException: If getting index stats fails.
        """
        try:
            indexes = self.collection.indexes
            stats = {
                "total_indexes": len(indexes),
                "indexes": []
            }

            for index in indexes:
                index_stat = {
                    "field_name": index.field_name,
                    "index_type": index.params.get("index_type"),
                    "metric_type": index.params.get("metric_type"),
                    "params": index.params.get("params", {})
                }
                stats["indexes"].append(index_stat)

            logger.debug(f"Retrieved stats for {stats['total_indexes']} indexes")
            return stats

        except MilvusException as e:
            logger.error(f"Failed to get index stats: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting index stats: {e}")
            raise
