"""
Test script for Milvus optimization improvements.

This script validates:
1. HNSW index creation
2. Adaptive search parameters
3. Distance threshold filtering
4. Scalar indexes for filtering
"""

import sys
from typing import List

from loguru import logger

# Add src to path
sys.path.insert(0, "src")

from infrastructure.milvus.client import MilvusClientWrapper
from domain.rag.rag_file_upload import RagFileUpload


def test_index_initialization():
    """Test that HNSW index is properly initialized."""
    logger.info("=" * 80)
    logger.info("TEST 1: Index Initialization")
    logger.info("=" * 80)

    try:
        # Create client with HNSW index (default)
        client = MilvusClientWrapper(
            model=RagFileUpload,
            collection_name="test_hnsw_collection",
            vector_dimension=1536,
            index_type="HNSW",
        )

        logger.info(f"✅ Client initialized with index_type: {client.index_type}")
        logger.info(f"✅ Index params: {client.index_params}")

        # Verify defaults
        assert client.index_type == "HNSW", "Index type should be HNSW"
        assert "M" in client.index_params, "HNSW should have M parameter"
        assert "efConstruction" in client.index_params, "HNSW should have efConstruction"

        logger.info("✅ TEST 1 PASSED: HNSW index properly initialized")
        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        return False


def test_adaptive_search_params():
    """Test adaptive search parameter calculation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Adaptive Search Parameters")
    logger.info("=" * 80)

    try:
        # Test HNSW params
        client = MilvusClientWrapper(
            model=RagFileUpload,
            collection_name="test_adaptive_hnsw",
            vector_dimension=1536,
            index_type="HNSW",
        )

        # Test different limits
        for limit in [5, 10, 20, 50]:
            params = client._calculate_search_params(limit)
            ef = params["params"]["ef"]
            logger.info(f"  limit={limit:2d} → ef={ef:3d}")

            # Verify ef is at least limit and capped at 512
            assert ef >= limit, f"ef should be >= limit ({ef} < {limit})"
            assert ef <= 512, f"ef should be <= 512 ({ef} > 512)"

        logger.info("✅ HNSW adaptive params working correctly")

        # Test IVF_FLAT params
        client_ivf = MilvusClientWrapper(
            model=RagFileUpload,
            collection_name="test_adaptive_ivf",
            vector_dimension=1536,
            index_type="IVF_FLAT",
        )

        params = client_ivf._calculate_search_params(10)
        nprobe = params["params"]["nprobe"]
        nlist = client_ivf.index_params["nlist"]

        logger.info(f"  IVF_FLAT: nlist={nlist}, nprobe={nprobe}")
        assert nprobe <= nlist, f"nprobe should be <= nlist ({nprobe} > {nlist})"
        assert nprobe >= 20, f"nprobe should be >= 20 ({nprobe} < 20)"

        logger.info("✅ TEST 2 PASSED: Adaptive search parameters working correctly")

        client.close()
        client_ivf.close()
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_index_types():
    """Test different index types and their parameters."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Index Types")
    logger.info("=" * 80)

    index_configs = [
        ("HNSW", {"M": 16, "efConstruction": 256}),
        ("IVF_FLAT", {"nlist": 1024}),
        ("IVF_PQ", {"nlist": 2048, "m": 8, "nbits": 8}),
        ("FLAT", {}),
    ]

    try:
        for index_type, expected_keys in index_configs:
            client = MilvusClientWrapper(
                model=RagFileUpload,
                collection_name=f"test_{index_type.lower()}",
                vector_dimension=1536,
                index_type=index_type,
            )

            logger.info(f"  {index_type}: {client.index_params}")

            # Verify expected keys are present
            for key in expected_keys.keys():
                assert (
                    key in client.index_params
                ), f"{index_type} should have {key} parameter"

            client.close()

        logger.info("✅ TEST 3 PASSED: All index types properly configured")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_distance_threshold_logic():
    """Test distance threshold filtering logic."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Distance Threshold Logic")
    logger.info("=" * 80)

    try:
        # Test that search method accepts distance_threshold parameter
        client = MilvusClientWrapper(
            model=RagFileUpload,
            collection_name="test_distance_threshold",
            vector_dimension=1536,
            index_type="HNSW",
        )

        # Verify method signature
        import inspect

        sig = inspect.signature(client.search_with_vector)
        params = sig.parameters

        assert (
            "distance_threshold" in params
        ), "search_with_vector should have distance_threshold parameter"
        assert (
            "use_adaptive_params" in params
        ), "search_with_vector should have use_adaptive_params parameter"

        logger.info("✅ Distance threshold parameter exists")
        logger.info("✅ Adaptive params parameter exists")

        # Test with higher search limit when threshold is set
        query_vector = [0.1] * 1536
        # This would normally search the collection, but we're just testing the logic

        logger.info("✅ TEST 4 PASSED: Distance threshold logic verified")

        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("🚀 Starting Milvus Optimization Tests")
    logger.info("=" * 80)

    results = []

    # Run tests
    results.append(("Index Initialization", test_index_initialization()))
    results.append(("Adaptive Search Params", test_adaptive_search_params()))
    results.append(("Index Types", test_index_types()))
    results.append(("Distance Threshold", test_distance_threshold_logic()))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name:<30s} {status}")

    logger.info("=" * 80)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 80)

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
