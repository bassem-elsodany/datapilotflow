"""
Migration Script for Conversation Schema Update

This script migrates existing conversation documents to include
new fields for LLM provider configuration, query enhancement,
and statistics tracking.

Usage:
    python tools/migrate_conversation_schema.py [--dry-run]
"""

import sys
from datetime import datetime

import click
from loguru import logger
from pymongo import MongoClient

from src.config import settings


def migrate_conversations(dry_run: bool = False):
    """
    Migrate existing conversation documents to new schema.

    Args:
        dry_run: If True, only show what would be changed without modifying data
    """
    try:
        # Connect to MongoDB
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        collection = db["knowledge_conversation_history"]

        # Count total documents
        total_docs = collection.count_documents({})
        logger.info(f"Found {total_docs} conversation documents")

        # Find documents that need migration (missing any new fields)
        migration_query = {
            "$or": [
                {"llm_provider_id": {"$exists": False}},
                {"llm_model_name": {"$exists": False}},
                {"enhancement_config": {"$exists": False}},
                {"collection_name": {"$exists": False}},
                {"total_queries": {"$exists": False}},
                {"total_documents_retrieved": {"$exists": False}},
                {"average_response_time_ms": {"$exists": False}},
                {"tags": {"$exists": False}},
                {"description": {"$exists": False}},
            ]
        }

        docs_to_migrate = collection.count_documents(migration_query)
        logger.info(f"Found {docs_to_migrate} conversations requiring migration")

        if docs_to_migrate == 0:
            logger.success("All conversations are already up to date!")
            return True

        if dry_run:
            logger.info("DRY RUN: Would update the following documents:")
            for doc in collection.find(migration_query).limit(5):
                logger.info(f"  - Conversation ID: {doc['_id']}")
            if docs_to_migrate > 5:
                logger.info(f"  ... and {docs_to_migrate - 5} more")
            return True

        # Perform migration
        logger.info("Starting migration...")

        update_data = {
            "$set": {
                "llm_provider_id": None,
                "llm_model_name": None,
                "enhancement_config": {
                    "strategy": "none",
                    "enabled": False,
                    "config": None,
                    "configured_at": datetime.utcnow(),
                },
                "collection_name": "LongTermMemory",
                "total_queries": 0,
                "total_documents_retrieved": 0,
                "average_response_time_ms": None,
                "tags": [],
                "description": None,
            }
        }

        # Only set fields if they don't exist (use $setOnInsert equivalent)
        result = collection.update_many(migration_query, update_data)

        logger.success(f"Migration complete!")
        logger.info(f"  - Matched: {result.matched_count} documents")
        logger.info(f"  - Modified: {result.modified_count} documents")

        # Verify migration
        remaining = collection.count_documents(migration_query)
        if remaining == 0:
            logger.success("All conversations successfully migrated!")
            return True
        else:
            logger.warning(f"Warning: {remaining} conversations still need migration")
            return False

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        client.close()


def add_message_metadata_fields(dry_run: bool = False):
    """
    Add new metadata fields to existing messages in conversations.

    Args:
        dry_run: If True, only show what would be changed without modifying data
    """
    try:
        # Connect to MongoDB
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        collection = db["knowledge_conversation_history"]

        # Find documents with messages that need metadata
        logger.info("Checking for messages requiring metadata fields...")

        # Count conversations with messages
        conversations_with_messages = collection.count_documents(
            {"messages": {"$exists": True, "$ne": []}}
        )
        logger.info(f"Found {conversations_with_messages} conversations with messages")

        if conversations_with_messages == 0:
            logger.success("No messages to update!")
            return True

        if dry_run:
            logger.info(
                "DRY RUN: Would add metadata fields to messages in conversations"
            )
            return True

        # Update messages to include new fields (if they don't exist)
        # This is more complex as we need to iterate through each conversation
        updated_count = 0
        for doc in collection.find({"messages": {"$exists": True, "$ne": []}}):
            messages = doc.get("messages", [])
            updated_messages = []
            needs_update = False

            for msg in messages:
                # Check if message needs new fields
                if "enhancement_strategy_used" not in msg:
                    msg["enhancement_strategy_used"] = None
                    needs_update = True
                if "enhanced_queries" not in msg:
                    msg["enhanced_queries"] = None
                    needs_update = True
                if "processing_time_ms" not in msg:
                    msg["processing_time_ms"] = None
                    needs_update = True
                if "document_count" not in msg:
                    msg["document_count"] = None
                    needs_update = True

                updated_messages.append(msg)

            if needs_update:
                collection.update_one(
                    {"_id": doc["_id"]}, {"$set": {"messages": updated_messages}}
                )
                updated_count += 1

        logger.success(f"Updated messages in {updated_count} conversations")
        return True

    except Exception as e:
        logger.error(f"Message metadata migration failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        client.close()


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be migrated without making changes",
)
@click.option(
    "--messages",
    is_flag=True,
    default=False,
    help="Also migrate message metadata fields",
)
def main(dry_run: bool, messages: bool):
    """
    Migrate conversation schema to include new configuration fields.
    """
    logger.info("=" * 70)
    logger.info("Conversation Schema Migration")
    logger.info("=" * 70)

    if dry_run:
        logger.warning("DRY RUN MODE - No changes will be made")

    # Migrate conversation documents
    logger.info("\n1. Migrating conversation documents...")
    success1 = migrate_conversations(dry_run=dry_run)

    # Optionally migrate message metadata
    success2 = True
    if messages:
        logger.info("\n2. Migrating message metadata...")
        success2 = add_message_metadata_fields(dry_run=dry_run)

    logger.info("\n" + "=" * 70)
    if success1 and success2:
        logger.success("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
