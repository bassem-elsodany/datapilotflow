"""
Reinitialize Model Providers with Reranker Support

This script deletes all existing model providers and recreates them with the updated schema
that includes reranker support for Cohere and Voyage AI.

Usage:
    python tools/reinitialize_providers.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from pymongo import MongoClient

from src.config import settings
from src.services.auth.admin_initialization_service import AdminInitializationService
from src.services.model_provider.model_provider_initialization_service import (
    ModelProviderInitializationService,
)


async def main():
    """Reinitialize all model providers with reranker support."""
    try:
        logger.info("=" * 80)
        logger.info("Starting Model Provider Reinitialization")
        logger.info("=" * 80)

        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {settings.MONGO_HOST}:{settings.MONGO_PORT}")
        client = MongoClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASS,
        )
        db = client[settings.MONGO_DB_NAME]

        # Get admin user
        logger.info("Finding admin user...")
        from src.services.auth.dao.auth_dao import AuthDAO
        
        auth_dao = AuthDAO()
        admin_user = auth_dao.get_user_by_username("admin")

        if not admin_user:
            logger.error("Admin user not found. Please run admin initialization first.")
            return False

        logger.info(f"Admin user found: {admin_user.username} (ID: {admin_user.id})")

        # Delete all existing model providers
        logger.info("\n" + "=" * 80)
        logger.info("Deleting existing model providers...")
        logger.info("=" * 80)

        model_providers_collection = db["model_providers"]
        result = model_providers_collection.delete_many({"created_by": admin_user.id})
        logger.info(f"Deleted {result.deleted_count} existing model providers")

        # Reinitialize providers with reranker support
        logger.info("\n" + "=" * 80)
        logger.info("Reinitializing model providers with reranker support...")
        logger.info("=" * 80)

        provider_service = ModelProviderInitializationService()
        success = await provider_service.initialize_predefined_model_providers(
            admin_user.id
        )

        if success:
            logger.info("\n" + "=" * 80)
            logger.info("✅ Model providers reinitialized successfully!")
            logger.info("=" * 80)

            # Show summary
            providers = list(
                model_providers_collection.find({"created_by": admin_user.id})
            )
            logger.info(f"\nTotal providers: {len(providers)}")

            for provider in providers:
                capabilities = []
                if provider.get("embedding"):
                    capabilities.append(
                        f"Embedding ({len(provider['embedding'].get('models', []))} models)"
                    )
                if provider.get("generative"):
                    capabilities.append(
                        f"Generative ({len(provider['generative'].get('models', []))} models)"
                    )
                if provider.get("reranker"):
                    capabilities.append(
                        f"Reranker ({len(provider['reranker'].get('models', []))} models)"
                    )

                logger.info(
                    f"  • {provider['name']} ({provider['provider_type']}): {', '.join(capabilities)}"
                )

            # Highlight reranker providers
            reranker_providers = [p for p in providers if p.get("reranker")]
            if reranker_providers:
                logger.info(
                    f"\n🎯 Providers with Reranker Support: {len(reranker_providers)}"
                )
                for provider in reranker_providers:
                    logger.info(
                        f"  • {provider['name']}: {', '.join(provider['reranker'].get('models', []))}"
                    )

            return True
        else:
            logger.error("Failed to reinitialize model providers")
            return False

    except Exception as e:
        logger.error(f"Error during reinitialization: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False
    finally:
        if "client" in locals():
            client.close()
            logger.info("\nMongoDB connection closed")


if __name__ == "__main__":
    logger.info("Model Provider Reinitialization Script")
    logger.info("This will delete and recreate all model providers")
    logger.info("=" * 80)

    result = asyncio.run(main())

    if result:
        logger.info("\n✅ Reinitialization completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Reinitialization failed!")
        sys.exit(1)

