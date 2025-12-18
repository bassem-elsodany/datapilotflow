"""
Migration Script: Add Embedding Provider to Agent Vector Database Config

This script populates the embedding_provider field in agent vector_database configs
from the corresponding vector database collection's embedding provider.

Usage:
    python tools/migrate_agent_add_embedding_provider.py
    python tools/migrate_agent_add_embedding_provider.py --dry-run
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.infrastructure.mongo.client import get_mongo_client


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def migrate_agent_embedding_provider(dry_run: bool):
    """Migrate agents to include embedding provider in vector database config."""

    logger.info("=" * 80)
    logger.info("Agent Vector Database Migration: Add Embedding Provider")
    logger.info("=" * 80)

    try:
        # Get MongoDB client and database
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        agents_collection = db["agents"]
        collections_collection = db["vectordb_collections"]

        # Find all agents with vector_database config but without embedding_provider
        query = {
            "vector_database": {"$exists": True, "$ne": None},
            "vector_database.embedding_provider": {"$exists": False},
        }
        documents_to_update = list(agents_collection.find(query))

        logger.info(f"Found {len(documents_to_update)} agents to update")

        if len(documents_to_update) == 0:
            logger.success("✅ No agents need embedding provider migration")
            return

        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            for doc in documents_to_update:
                agent_name = doc.get("name", "N/A")
                agent_id = str(doc["_id"])
                collection_name = doc.get("vector_database", {}).get("collection_name")

                # Try to find the collection to show what will be added
                collection = collections_collection.find_one(
                    {"collection_name": collection_name}
                )
                if collection:
                    logger.info(
                        f"  Would update: _id={agent_id}, name={agent_name}, "
                        f"collection={collection_name}, "
                        f"embedding_provider={collection.get('embedding_model_provider_id')} / "
                        f"{collection.get('embedding_model_name')}"
                    )
                else:
                    logger.warning(
                        f"  ⚠️ Collection not found for agent {agent_id}: {collection_name}"
                    )
            return

        # Update each agent
        updated_count = 0
        failed_count = 0
        for doc in documents_to_update:
            agent_id = doc["_id"]
            agent_name = doc.get("name", "N/A")
            collection_name = doc.get("vector_database", {}).get("collection_name")

            try:
                # Find the collection to get embedding provider details
                collection = collections_collection.find_one(
                    {"collection_name": collection_name}
                )

                if not collection:
                    logger.warning(
                        f"⚠️ Collection not found for agent {agent_id}: {collection_name}"
                    )
                    failed_count += 1
                    continue

                # Extract embedding provider details from collection
                embedding_provider = {
                    "id": collection.get("embedding_model_provider_id"),
                    "model_name": collection.get("embedding_model_name"),
                }
                vector_dimension = collection.get("vector_dimension", 1536)

                # Update agent with embedding provider
                update_data = {
                    "$set": {
                        "vector_database.embedding_provider": embedding_provider,
                        "vector_database.vector_dimension": vector_dimension,
                        "updated_at": datetime.now(timezone.utc),
                    }
                }

                result = agents_collection.update_one({"_id": agent_id}, update_data)

                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(
                        f"✅ Updated: _id={agent_id}, name={agent_name}, "
                        f"embedding_provider_id={embedding_provider['id']}, "
                        f"embedding_model={embedding_provider['model_name']}, "
                        f"vector_dimension={vector_dimension}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Failed to update: _id={agent_id}, name={agent_name}"
                    )
                    failed_count += 1

            except Exception as e:
                logger.error(f"❌ Error updating agent {agent_id}: {e}")
                failed_count += 1

        logger.success(
            f"✅ Migration completed: {updated_count}/{len(documents_to_update)} agents updated, {failed_count} failed"
        )

        # Verify all agents now have embedding_provider
        remaining_without_embedding = agents_collection.count_documents(
            {
                "vector_database": {"$exists": True, "$ne": None},
                "vector_database.embedding_provider": {"$exists": False},
            }
        )
        if remaining_without_embedding > 0:
            logger.warning(
                f"⚠️ Still have {remaining_without_embedding} agents without embedding_provider"
            )
        else:
            logger.success("✅ All agents now have embedding_provider configured")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    migrate_agent_embedding_provider()
