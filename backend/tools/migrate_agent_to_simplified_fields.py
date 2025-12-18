"""
Migration Script: Migrate Agent to Simplified Fields

This script migrates existing agent configurations from the old format:
- enhancement: {strategy: "..."} -> enhancement_strategy: "..."
- answer_generation: {enabled: true/false} -> is_llm_generation_enabled: true/false

Usage:
    python tools/migrate_agent_to_simplified_fields.py
    python tools/migrate_agent_to_simplified_fields.py --dry-run
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
def migrate_agent_fields(dry_run: bool):
    """Migrate agent configurations to simplified field format."""

    logger.info("=" * 80)
    logger.info(
        "Agent Configuration Migration: Simplify to enhancement_strategy and is_llm_generation_enabled"
    )
    logger.info("=" * 80)

    try:
        # Get MongoDB client and database
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        collection = db["agents"]

        # Find all agents that need migration
        # Agents with old format: enhancement object or answer_generation object
        # Agents with new format: enhancement_strategy string or is_llm_generation_enabled boolean
        query = {
            "$or": [
                {"enhancement": {"$exists": True, "$ne": None}},  # Has old enhancement object
                {"answer_generation": {"$exists": True, "$ne": None}},  # Has old answer_generation object
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

                # Check enhancement migration
                if doc.get("enhancement") and not doc.get("enhancement_strategy"):
                    old_strategy = doc["enhancement"].get("strategy", "")
                    changes.append(
                        f"enhancement -> enhancement_strategy: '{old_strategy}'"
                    )

                # Check answer_generation migration
                if doc.get("answer_generation") and "is_llm_generation_enabled" not in doc:
                    old_enabled = doc["answer_generation"].get("enabled", False)
                    changes.append(
                        f"answer_generation.enabled -> is_llm_generation_enabled: {old_enabled}"
                    )

                if changes:
                    logger.info(
                        f"  Would update: _id={agent_id}, name={agent_name}, "
                        f"changes: {', '.join(changes)}"
                    )
            return

        # Update each document
        updated_count = 0
        for doc in documents_to_update:
            agent_id = doc["_id"]
            agent_name = doc.get("name", "N/A")

            # Build update operation
            update_data = {"$set": {"updated_at": datetime.now(timezone.utc)}}
            unset_data = {}

            # Migrate enhancement object to enhancement_strategy string
            if doc.get("enhancement") and not doc.get("enhancement_strategy"):
                strategy = doc["enhancement"].get("strategy", "")
                update_data["$set"]["enhancement_strategy"] = strategy
                unset_data["enhancement"] = ""  # Remove old field

            # Migrate answer_generation object to is_llm_generation_enabled boolean
            if doc.get("answer_generation") and "is_llm_generation_enabled" not in doc:
                enabled = doc["answer_generation"].get("enabled", False)
                update_data["$set"]["is_llm_generation_enabled"] = enabled
                unset_data["answer_generation"] = ""  # Remove old field

            if not update_data.get("$set", {}).get("enhancement_strategy") and not update_data.get("$set", {}).get("is_llm_generation_enabled"):
                # Skip if no actual changes needed
                continue

            # Build final update operation
            final_update = {"$set": update_data["$set"]}
            if unset_data:
                final_update["$unset"] = unset_data

            # Update document
            result = collection.update_one({"_id": agent_id}, final_update)

            if result.modified_count > 0:
                updated_count += 1
                changes = []
                if "enhancement_strategy" in update_data["$set"]:
                    changes.append(f"enhancement_strategy={update_data['$set']['enhancement_strategy']}")
                if "is_llm_generation_enabled" in update_data["$set"]:
                    changes.append(f"is_llm_generation_enabled={update_data['$set']['is_llm_generation_enabled']}")
                logger.info(
                    f"✅ Updated: _id={agent_id}, name={agent_name}, "
                    f"changes: {', '.join(changes)}"
                )
            else:
                logger.warning(f"⚠️ Failed to update: _id={agent_id}, name={agent_name}")

        logger.success(
            f"✅ Migration completed: {updated_count}/{len(documents_to_update)} agents updated"
        )

        # Verify no old format fields remain
        remaining_old_format = collection.count_documents(
            {
                "$or": [
                    {"enhancement": {"$exists": True, "$ne": None}},
                    {"answer_generation": {"$exists": True, "$ne": None}},
                ]
            }
        )
        if remaining_old_format > 0:
            logger.warning(
                f"⚠️ Still have {remaining_old_format} agents with old format fields"
            )
        else:
            logger.success("✅ All agents now use simplified field format")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    migrate_agent_fields()

