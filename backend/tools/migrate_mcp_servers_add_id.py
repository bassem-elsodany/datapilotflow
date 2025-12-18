"""
Migration Script: Add 'id' field to existing MCP servers.

This script fixes the E11000 duplicate key error by adding UUID 'id' field
to all existing mcp_servers documents that have id: null.

Usage:
    python tools/migrate_mcp_servers_add_id.py
"""

import sys
import uuid
from datetime import datetime

import click
from loguru import logger

from src.config import settings
from src.infrastructure.mongo.client import get_database


@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be updated without making changes")
def migrate_mcp_servers(dry_run: bool):
    """Migrate MCP servers to include 'id' field."""
    
    logger.info("=" * 80)
    logger.info("MCP Servers Migration: Add 'id' field")
    logger.info("=" * 80)
    
    try:
        # Get MongoDB collection
        db = get_database()
        collection = db["mcp_servers"]
        
        # Find all documents without 'id' field or with id: null
        query = {"$or": [{"id": {"$exists": False}}, {"id": None}]}
        documents_to_update = list(collection.find(query))
        
        logger.info(f"Found {len(documents_to_update)} documents to update")
        
        if len(documents_to_update) == 0:
            logger.success("✅ No documents need migration")
            return
        
        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            for doc in documents_to_update:
                logger.info(f"  Would update: _id={doc['_id']}, name={doc.get('name', 'N/A')}")
            return
        
        # Update each document
        updated_count = 0
        for doc in documents_to_update:
            new_id = str(uuid.uuid4())
            result = collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "id": new_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                logger.info(f"✅ Updated: _id={doc['_id']}, name={doc.get('name', 'N/A')}, new id={new_id}")
            else:
                logger.warning(f"⚠️ Failed to update: _id={doc['_id']}")
        
        logger.success(f"✅ Migration completed: {updated_count}/{len(documents_to_update)} documents updated")
        
        # Verify no null ids remain
        remaining_nulls = collection.count_documents({"$or": [{"id": {"$exists": False}}, {"id": None}]})
        if remaining_nulls > 0:
            logger.error(f"❌ Still have {remaining_nulls} documents with null/missing id")
            sys.exit(1)
        else:
            logger.success("✅ All documents now have valid 'id' field")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    migrate_mcp_servers()

