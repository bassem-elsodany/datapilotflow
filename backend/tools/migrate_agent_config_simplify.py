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
    logger.info(
        "Agent Configuration Migration: Simplify Enhancement & Answer Generation"
    )
    logger.info("=" * 80)

    try:
        # Get MongoDB client and database
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        collection = db["agents"]

        # Find ALL agents (we need to check and clean all of them)
        # Some may have provider: null, some may have provider objects, some may not have the field at all
        documents_to_update = list(collection.find({}))

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

                enhancement = doc.get("enhancement", {})
                answer_generation = doc.get("answer_generation", {})

                if enhancement and "provider" in enhancement:
                    provider_val = enhancement.get("provider")
                    changes.append(
                        f"enhancement.provider ({'null' if provider_val is None else 'object'})"
                    )
                if answer_generation and "provider" in answer_generation:
                    provider_val = answer_generation.get("provider")
                    changes.append(
                        f"answer_generation.provider ({'null' if provider_val is None else 'object'})"
                    )

                if changes:
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

            # Build unset operation to remove provider fields (even if null)
            unset_fields = {}
            enhancement = doc.get("enhancement", {})
            answer_generation = doc.get("answer_generation", {})

            # Remove provider field from enhancement if it exists (even if null)
            if enhancement and "provider" in enhancement:
                unset_fields["enhancement.provider"] = ""

            # Remove provider field from answer_generation if it exists (even if null)
            if answer_generation and "provider" in answer_generation:
                unset_fields["answer_generation.provider"] = ""

            if not unset_fields:
                continue

            # Update document
            result = collection.update_one(
                {"_id": agent_id},
                {
                    "$unset": unset_fields,
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
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

        # Verify no provider fields remain (including null values)
        remaining_with_providers = collection.count_documents(
            {
                "$or": [
                    {"enhancement.provider": {"$exists": True}},
                    {"answer_generation.provider": {"$exists": True}},
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
