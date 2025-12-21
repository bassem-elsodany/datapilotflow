"""
Milvus Vector Database Collections Inspection Script.

This script connects to Milvus and displays all collections, their schemas,
and sample data for inspection and debugging.
"""

import json
from typing import Dict, List, Any
from pymilvus import connections, Collection, utility
from loguru import logger

logger.remove()  # Remove default handler
logger.add(lambda msg: print(msg.rstrip()), format="{message}")


class MilvusInspector:
    """Inspector for Milvus vector database collections."""

    def __init__(self, host: str = "localhost", port: int = 19530):
        """Initialize Milvus connection."""
        self.host = host
        self.port = port
        self.connected = False
        self.connect()

    def connect(self) -> bool:
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                pool_size=10,
            )
            self.connected = True
            logger.info(f"✓ Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to Milvus: {e}")
            return False

    def disconnect(self):
        """Disconnect from Milvus."""
        try:
            connections.disconnect(alias="default")
            self.connected = False
            logger.info("✓ Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def list_collections(self) -> List[str]:
        """List all collections in Milvus."""
        try:
            collections = utility.list_collections()
            logger.info(f"\n{'='*70}")
            logger.info(f"MILVUS COLLECTIONS ({len(collections)} total)")
            logger.info(f"{'='*70}")

            if not collections:
                logger.warning("No collections found in Milvus")
                return []

            for i, col_name in enumerate(collections, 1):
                logger.info(f"{i}. {col_name}")

            return collections
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    def get_collection_schema(self, collection_name: str) -> Dict[str, Any]:
        """Get schema of a collection."""
        try:
            collection = Collection(collection_name)
            schema = collection.schema

            schema_info = {
                "collection_name": collection_name,
                "description": schema.description if hasattr(schema, 'description') else "N/A",
                "fields": [],
            }

            for field in schema.fields:
                field_info = {
                    "name": field.name,
                    "dtype": str(field.dtype),
                }

                # Add dtype-specific info
                if hasattr(field, "max_length"):
                    field_info["max_length"] = field.max_length
                if hasattr(field, "dim"):
                    field_info["dimension"] = field.dim

                schema_info["fields"].append(field_info)

            return schema_info
        except Exception as e:
            logger.error(f"Error getting schema for {collection_name}: {e}")
            return {}

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collection = Collection(collection_name)

            # Load collection to get entity count
            try:
                collection.load()
                stats = {
                    "collection_name": collection_name,
                    "row_count": collection.num_entities,
                }
            except Exception as load_err:
                logger.warning(f"Could not load {collection_name}: {load_err}")
                stats = {
                    "collection_name": collection_name,
                    "row_count": "unknown (load error)",
                }

            return stats
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {"collection_name": collection_name, "error": str(e)}

    def get_sample_data(
        self, collection_name: str, limit: int = 5
    ) -> Dict[str, Any]:
        """Get sample data from a collection."""
        try:
            collection = Collection(collection_name)

            # Try to load collection first
            try:
                collection.load()
            except Exception as load_err:
                logger.warning(f"Could not load {collection_name}: {load_err}")

            # Query sample data
            expr = ""  # Empty expression returns all
            output_fields = ["*"]

            try:
                results = collection.query(expr, output_fields=output_fields, limit=limit)

                sample_data = {
                    "collection_name": collection_name,
                    "sample_count": len(results),
                    "data": results,
                }
            except Exception as query_err:
                sample_data = {
                    "collection_name": collection_name,
                    "error": str(query_err),
                    "data": [],
                }

            return sample_data
        except Exception as e:
            logger.error(f"Error getting sample data from {collection_name}: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
                "data": [],
            }

    def print_collection_details(self, collection_name: str):
        """Print detailed information about a collection."""
        logger.info(f"\n{'-'*70}")
        logger.info(f"COLLECTION: {collection_name}")
        logger.info(f"{'-'*70}")

        # Schema
        logger.info("\n[SCHEMA]")
        schema = self.get_collection_schema(collection_name)
        if schema and schema.get("fields"):
            logger.info(f"  Description: {schema.get('description', 'N/A')}")
            logger.info("  Fields:")
            for field in schema.get("fields", []):
                dim_str = f" (dim={field.get('dimension', 'N/A')})" if 'dimension' in field else ""
                logger.info(f"    - {field['name']}: {field['dtype']}{dim_str}")
        else:
            logger.warning(f"  Could not retrieve schema")

        # Statistics
        logger.info("\n[STATISTICS]")
        stats = self.get_collection_stats(collection_name)
        logger.info(f"  Row Count: {stats.get('row_count', 'N/A')}")
        if "error" in stats:
            logger.warning(f"  Error: {stats['error']}")

        # Sample Data
        logger.info("\n[SAMPLE DATA]")
        sample_data = self.get_sample_data(collection_name, limit=3)
        if sample_data.get("data"):
            logger.info(f"  {len(sample_data.get('data', []))} records retrieved:")
            for idx, record in enumerate(sample_data["data"], 1):
                logger.info(f"  Record {idx}:")
                for key, value in record.items():
                    # Truncate long values
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:97] + "..."
                    logger.info(f"    {key}: {val_str}")
        else:
            error_msg = sample_data.get('error', 'No data found')
            logger.warning(f"  No sample data: {error_msg}")

    def inspect_all_collections(self):
        """Inspect all collections and display detailed information."""
        if not self.connected:
            logger.error("Not connected to Milvus")
            return

        collections = self.list_collections()

        for collection_name in collections:
            self.print_collection_details(collection_name)

        logger.info(f"\n{'='*70}")
        logger.info(f"INSPECTION COMPLETE ({len(collections)} collections)")
        logger.info(f"{'='*70}\n")

    def get_collection_summary(self) -> Dict[str, Any]:
        """Get a summary of all collections."""
        summary = {
            "total_collections": 0,
            "collections": [],
        }

        try:
            collections = utility.list_collections()
            summary["total_collections"] = len(collections)

            for col_name in collections:
                stats = self.get_collection_stats(col_name)
                schema = self.get_collection_schema(col_name)

                col_summary = {
                    "name": col_name,
                    "row_count": stats.get('row_count', 'N/A'),
                    "field_count": len(schema.get('fields', [])),
                    "fields": [f.get('name') for f in schema.get('fields', [])],
                }
                summary["collections"].append(col_summary)

            return summary
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return summary


def test_list_milvus_collections():
    """Test: List all Milvus collections."""
    inspector = MilvusInspector()

    try:
        collections = inspector.list_collections()
        assert isinstance(collections, list), "Expected list of collections"
    finally:
        inspector.disconnect()


def test_inspect_collections():
    """Test: Inspect all collections with detailed info."""
    inspector = MilvusInspector()

    try:
        inspector.inspect_all_collections()
    finally:
        inspector.disconnect()


def test_collection_summary():
    """Test: Get summary of all collections."""
    inspector = MilvusInspector()

    try:
        summary = inspector.get_collection_summary()
        logger.info("\n" + "="*70)
        logger.info("COLLECTION SUMMARY (JSON)")
        logger.info("="*70)
        logger.info(json.dumps(summary, indent=2, default=str))
    finally:
        inspector.disconnect()


if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("MILVUS VECTOR DATABASE INSPECTOR")
    logger.info("="*70)

    inspector = MilvusInspector()

    if inspector.connected:
        logger.info("\n[MODE 1] Listing Collections")
        inspector.list_collections()

        logger.info("\n[MODE 2] Inspecting All Collections")
        inspector.inspect_all_collections()

        logger.info("\n[MODE 3] Collection Summary (JSON)")
        summary = inspector.get_collection_summary()
        logger.info(json.dumps(summary, indent=2, default=str))
    else:
        logger.error(
            "Could not connect to Milvus at localhost:19530\n"
            "Make sure Milvus server is running:\n"
            "  docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest"
        )

    inspector.disconnect()
