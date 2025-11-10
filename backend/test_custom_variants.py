"""
Test script for custom_variants strategy.

This script demonstrates how to test the new custom_variants enhancement strategy
which allows users to provide their own query variants without LLM enhancement.

Usage:
    python test_custom_variants.py
"""

import asyncio

from loguru import logger

from src.agents.rag_agent.graph import get_graph
from src.agents.rag_agent.state import create_initial_state


async def test_custom_variants_with_list():
    """Test custom_variants strategy with query as a list."""
    logger.info("=" * 80)
    logger.info("TEST 1: Query as List (Auto Custom Variants)")
    logger.info("=" * 80)

    # Get the RAG graph
    graph = get_graph()

    # Define custom query variants
    custom_queries = [
        "How to configure SSL certificates in Apache?",
        "Apache HTTPS setup and configuration",
        "Secure socket layer Apache web server",
    ]

    # Create initial state with query as list
    initial_state = create_initial_state(
        query=custom_queries,  # List of variants
        selected_strategy="custom_variants",
        top_k=5,
        config={
            "collection_name": "test_collection",
            "user_id": "test_user",
            "top_k": 5,
            "retrieval_config": {
                "top_k_per_query": 5,
                "rrf_k": 60,
            },
        },
    )

    logger.info(f"Input variants: {len(custom_queries)}")
    for idx, variant in enumerate(custom_queries, 1):
        logger.info(f"  {idx}. {variant}")

    # Note: This will fail without proper Milvus connection
    # For actual testing, ensure Milvus is running and collection exists
    logger.info("Note: Full execution requires Milvus connection")
    logger.info("State created successfully!")


async def test_custom_variants_with_additional():
    """Test custom_variants strategy with base query + additional variants."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("TEST 2: Base Query + Additional Custom Variants")
    logger.info("=" * 80)

    graph = get_graph()

    # Base query + additional variants
    base_query = "MuleSoft API management"
    additional_variants = [
        "Anypoint Platform configuration",
        "Mule runtime deployment guide",
    ]

    initial_state = create_initial_state(
        query=base_query,
        custom_variants=additional_variants,
        selected_strategy="custom_variants",
        top_k=5,
        config={
            "collection_name": "test_collection",
            "user_id": "test_user",
            "top_k": 5,
            "retrieval_config": {
                "top_k_per_query": 5,
                "rrf_k": 60,
            },
        },
    )

    logger.info(f"Base query: {base_query}")
    logger.info(f"Additional variants: {len(additional_variants)}")
    for idx, variant in enumerate(additional_variants, 1):
        logger.info(f"  {idx}. {variant}")

    logger.info("Expected total variants: 3 (1 base + 2 additional)")
    logger.info("State created successfully!")


async def test_custom_variants_multilingual():
    """Test custom_variants strategy with multi-language queries."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("TEST 3: Multi-Language Custom Variants")
    logger.info("=" * 80)

    graph = get_graph()

    # Multi-language variants
    multilingual_queries = [
        "How to reset password?",  # English
        "Comment réinitialiser le mot de passe?",  # French
        "Wie setze ich das Passwort zurück?",  # German
        "¿Cómo restablecer la contraseña?",  # Spanish
    ]

    initial_state = create_initial_state(
        query=multilingual_queries,
        selected_strategy="custom_variants",
        top_k=5,
        config={
            "collection_name": "test_collection",
            "user_id": "test_user",
            "top_k": 5,
            "retrieval_config": {
                "top_k_per_query": 5,
                "rrf_k": 60,
            },
        },
    )

    logger.info(f"Multi-language variants: {len(multilingual_queries)}")
    for idx, variant in enumerate(multilingual_queries, 1):
        logger.info(f"  {idx}. {variant}")

    logger.info("State created successfully!")


async def test_strategy_comparison():
    """Compare native vs custom_variants strategy."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("TEST 4: Strategy Comparison")
    logger.info("=" * 80)

    # Native strategy (single query)
    logger.info("\n📊 Native Strategy:")
    logger.info("  - Input: Single string")
    logger.info("  - Enhancement: None")
    logger.info("  - Retrieval: Single query search")
    logger.info("  - RRF: No (only 1 query)")
    logger.info("  - Speed: Fastest")

    # Custom Variants strategy (multiple queries)
    logger.info("\n📊 Custom Variants Strategy:")
    logger.info("  - Input: List of strings")
    logger.info("  - Enhancement: None (passthrough)")
    logger.info("  - Retrieval: Parallel search (N queries)")
    logger.info("  - RRF: Yes (auto-enabled)")
    logger.info("  - Speed: Fast (parallel execution)")

    logger.info("\n✅ Key Difference:")
    logger.info(
        "  Custom Variants = Native (no LLM) + Parallel Search + RRF Fusion"
    )


async def main():
    """Run all tests."""
    logger.info("🚀 Testing Custom Variants Strategy")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Run all tests
        await test_custom_variants_with_list()
        await test_custom_variants_with_additional()
        await test_custom_variants_multilingual()
        await test_strategy_comparison()

        logger.info("\n")
        logger.info("=" * 80)
        logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📝 Note: These tests validate state creation only.")
        logger.info(
            "📝 For full integration testing, ensure Milvus is running with data."
        )

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())

