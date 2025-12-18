"""
Migration Script: Simplify Agent Configuration

This script migrates existing agent configurations to the new simplified domain model:
- Removes `provider` field from `enhancement` config (now only uses agent's primary llm_provider)
- Removes `provider` field from `answer_generation` config (now only uses agent's primary llm_provider)

Usage:
    python tools/migrate_agent_config_simplify.py
    python tools/migrate_agent_config_simplify.py --dry-run
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
def migrate_agent_config(dry_run: bool):
    """Migrate agent configurations to simplified domain model."""
    
    logger.info("=" * 80)
    logger.info("Agent Configuration Migration: Simplify Enhancement & Answer Generation")
    logger.info("=" * 80)
    
    try:
        # Get MongoDB client and database
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        collection = db["agents"]
        
        # Find all agents that have enhancement.provider or answer_generation.provider
        query = {
            "$or": [
                {"enhancement.provider": {"$exists": True, "$ne": None}},
                {"answer_generation.provider": {"$exists": True, "$ne": None}},
            ]
        }
        documents_to_update = list(collection.find(query))
        
        logger.info(f"Found {len(documents_to_update)} agents to update")
        
        if len(documents_to_update) == 0:
            logger.success("✅ No agents need migration")
            return
        
        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            for doc in documents_to_update:
                agent_name = doc.get("name", "N/A")
                agent_id = str(doc["_id"])
                changes = []
                
                if doc.get("enhancement", {}).get("provider"):
                    changes.append("enhancement.provider")
                if doc.get("answer_generation", {}).get("provider"):
                    changes.append("answer_generation.provider")
                
                logger.info(
                    f"  Would update: _id={agent_id}, name={agent_name}, "
                    f"remove fields: {', '.join(changes)}"
                )
            return
        
        # Update each document
        updated_count = 0
        for doc in documents_to_update:
            agent_id = doc["_id"]
            agent_name = doc.get("name", "N/A")
            
            # Build unset operation to remove provider fields
            unset_fields = {}
            if doc.get("enhancement", {}).get("provider"):
                unset_fields["enhancement.provider"] = ""
            if doc.get("answer_generation", {}).get("provider"):
                unset_fields["answer_generation.provider"] = ""
            
            if not unset_fields:
                continue
            
            # Update document
            result = collection.update_one(
                {"_id": agent_id},
                {
                    "$unset": unset_fields,
                    "$set": {
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                logger.info(
                    f"✅ Updated: _id={agent_id}, name={agent_name}, "
                    f"removed fields: {', '.join(unset_fields.keys())}"
                )
            else:
                logger.warning(f"⚠️ Failed to update: _id={agent_id}, name={agent_name}")
        
        logger.success(
            f"✅ Migration completed: {updated_count}/{len(documents_to_update)} agents updated"
        )
        
        # Verify no provider fields remain
        remaining_with_providers = collection.count_documents(
            {
                "$or": [
                    {"enhancement.provider": {"$exists": True, "$ne": None}},
                    {"answer_generation.provider": {"$exists": True, "$ne": None}},
                ]
            }
        )
        if remaining_with_providers > 0:
            logger.error(
                f"❌ Still have {remaining_with_providers} agents with provider fields"
            )
            sys.exit(1)
        else:
            logger.success("✅ All agents now follow the simplified domain model")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    migrate_agent_config()

