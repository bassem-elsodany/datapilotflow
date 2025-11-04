#!/usr/bin/env python
"""
Script to update model providers in the database with latest models.

This script reads the predefined model providers from the initialization service
and updates the corresponding providers in the database with the new model lists.

Usage:
    python scripts/update_model_providers.py
"""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.model_provider.model_provider_initialization_service import (
    ModelProviderInitializationService,
)
from src.services.model_provider.model_provider_service import ModelProviderService
from src.domain.model_provider.model_provider import ModelTypeConfig


def update_model_providers():
    """Update model providers in the database with latest models."""
    logger.info("=" * 100)
    logger.info("🚀 STARTING MODEL PROVIDER UPDATE SCRIPT")
    logger.info("=" * 100)

    try:
        # Initialize services
        init_service = ModelProviderInitializationService()
        provider_service = ModelProviderService()

        # Get predefined providers with latest models
        predefined_providers = init_service.get_predefined_model_providers()

        logger.info(f"📋 Found {len(predefined_providers)} predefined providers to update")

        # Get admin user (first admin user, or use 'admin' as fallback)
        # In production, you may need to get the actual admin user ID
        admin_user_id = "admin"

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for provider_config in predefined_providers:
            provider_name = provider_config.get("name")
            logger.info("")
            logger.info("=" * 100)
            logger.info(f"📦 UPDATING PROVIDER: {provider_name}")
            logger.info("=" * 100)

            try:
                # Try to find existing provider
                existing_provider = provider_service.get_provider_by_name(
                    admin_user_id, provider_name
                )

                if not existing_provider:
                    logger.warning(
                        f"⏭️  Provider '{provider_name}' not found in database, skipping"
                    )
                    skipped_count += 1
                    continue

                logger.info(f"✅ Found existing provider: {existing_provider.id}")

                # Build updated models dict
                updates = {
                    "updated_at": datetime.utcnow(),
                    "updated_by": admin_user_id,
                }

                # Update embedding models if available
                if provider_config.get("embedding"):
                    embedding_config = provider_config["embedding"]
                    updates["embedding"] = ModelTypeConfig(
                        models=embedding_config.get("models", []),
                        config=embedding_config.get("config", {}),
                    )
                    logger.info(
                        f"   📊 Embedding: {len(embedding_config.get('models', []))} models"
                    )

                # Update generative models if available
                if provider_config.get("generative"):
                    generative_config = provider_config["generative"]
                    updates["generative"] = ModelTypeConfig(
                        models=generative_config.get("models", []),
                        config=generative_config.get("config", {}),
                    )
                    logger.info(
                        f"   🧠 Generative: {len(generative_config.get('models', []))} models"
                    )

                # Update reranker models if available
                if provider_config.get("reranker"):
                    reranker_config = provider_config["reranker"]
                    updates["reranker"] = ModelTypeConfig(
                        models=reranker_config.get("models", []),
                        config=reranker_config.get("config", {}),
                    )
                    logger.info(
                        f"   🔍 Reranker: {len(reranker_config.get('models', []))} models"
                    )

                # Update the provider in database
                updated_provider = provider_service.update_model_provider(
                    existing_provider.id, updates, admin_user_id
                )

                if updated_provider:
                    logger.info(f"✅✅✅ SUCCESSFULLY UPDATED: {provider_name}")
                    logger.info(f"   ID: {updated_provider.id}")
                    logger.info(f"   Updated at: {updated_provider.updated_at}")

                    # Log model counts
                    if updated_provider.embedding:
                        logger.info(
                            f"   📊 Embedding models: {len(updated_provider.embedding.models)}"
                        )
                    if updated_provider.generative:
                        logger.info(
                            f"   🧠 Generative models: {len(updated_provider.generative.models)}"
                        )
                    if updated_provider.reranker:
                        logger.info(
                            f"   🔍 Reranker models: {len(updated_provider.reranker.models)}"
                        )

                    updated_count += 1
                else:
                    logger.error(f"❌ Failed to update provider: {provider_name}")
                    error_count += 1

            except Exception as e:
                logger.error(f"❌ Error updating provider '{provider_name}': {e}")
                logger.error(f"   Traceback: {str(e)}")
                error_count += 1
                continue

        # Summary
        logger.info("")
        logger.info("=" * 100)
        logger.info("📊 UPDATE SUMMARY")
        logger.info("=" * 100)
        logger.info(f"✅ Successfully updated: {updated_count} providers")
        logger.info(f"⏭️  Skipped: {skipped_count} providers")
        logger.info(f"❌ Errors: {error_count} providers")
        logger.info("=" * 100)

        if error_count == 0 and updated_count > 0:
            logger.info("🎉 ALL PROVIDERS UPDATED SUCCESSFULLY!")
            return True
        elif updated_count > 0:
            logger.warning(f"⚠️  {error_count} providers had errors, but some were updated")
            return True
        else:
            logger.error("❌ NO PROVIDERS WERE UPDATED")
            return False

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        logger.error(f"Traceback: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = update_model_providers()
    sys.exit(0 if success else 1)
