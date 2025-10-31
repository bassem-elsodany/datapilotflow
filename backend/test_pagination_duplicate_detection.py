"""
Test script to verify pagination-based duplicate detection works correctly.

This script:
1. Creates a test collection with 15,000+ chunks (simulating your MuleSoft scenario)
2. Tests that duplicate detector fetches ALL URLs using pagination
3. Verifies that the old limit=10000 bug is fixed
"""

import sys
sys.path.insert(0, 'src')

from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.application.data.storage.duplicate_detector import DuplicateDetector
from src.config import settings

def test_pagination_duplicate_detection():
    """Test that pagination fetches all URLs regardless of collection size."""

    # Test configuration
    test_collection_name = "test_pagination_collection"
    vector_dimension = 1536  # OpenAI embedding dimension

    print("=" * 80)
    print("PAGINATION DUPLICATE DETECTION TEST")
    print("=" * 80)

    # Create test Milvus client
    print("\n1. Creating Milvus client...")
    client = MilvusClientWrapper(
        model=KnowledgeChunk,
        collection_name=test_collection_name,
        vector_dimension=vector_dimension,
    )
    print(f"✅ Connected to Milvus collection: {test_collection_name}")

    # Clear collection
    print("\n2. Clearing test collection...")
    client.clear_collection()
    count_after_clear = client.get_collection_count()
    print(f"✅ Collection cleared. Count: {count_after_clear}")

    # Create test data simulating your MuleSoft scenario
    # 500 URLs, each with 30 chunks = 15,000 total chunks
    print("\n3. Creating test data (15,000 chunks to exceed old 10,000 limit)...")

    num_urls = 500
    chunks_per_url = 30
    total_chunks = num_urls * chunks_per_url

    print(f"   - {num_urls} unique URLs")
    print(f"   - {chunks_per_url} chunks per URL")
    print(f"   - Total: {total_chunks} chunks")

    # Generate chunks in batches
    batch_size = 1000
    total_inserted = 0

    for batch_idx in range(0, total_chunks, batch_size):
        chunks = []
        vectors = []

        for i in range(batch_idx, min(batch_idx + batch_size, total_chunks)):
            url_idx = i // chunks_per_url
            chunk_idx = i % chunks_per_url
            url = f"https://docs.example.com/page-{url_idx}"

            chunk = KnowledgeChunk(
                page_content=f"Content for page {url_idx}, chunk {chunk_idx}",
                source_url=url,
                job_id="test-job-1",
                title=f"Page {url_idx}",
                chunk_id=f"chunk-{i}",
                chunk_index=chunk_idx,
                total_chunks=chunks_per_url,
            )
            chunks.append(chunk)
            vectors.append([0.0] * vector_dimension)  # Dummy vectors

        # Upsert batch
        client.ingest_documents(chunks, vectors)
        total_inserted += len(chunks)
        print(f"   Inserted batch {batch_idx // batch_size + 1}: {total_inserted}/{total_chunks} chunks")

    collection_count = client.get_collection_count()
    print(f"\n✅ Inserted {collection_count} chunks into collection")

    # TEST: Duplicate detector should fetch ALL URLs using pagination
    print("\n4. Testing duplicate detector with pagination...")
    print("   (This previously failed with limit=10000 when collection > 10,000 chunks)")

    duplicate_detector = DuplicateDetector(milvus_client=client)
    existing_urls = duplicate_detector.get_existing_urls()

    print(f"\n5. RESULTS")
    print("=" * 80)
    print(f"Collection count: {collection_count} chunks")
    print(f"Expected URLs: {num_urls} unique URLs")
    print(f"Fetched URLs: {len(existing_urls)} unique URLs")

    # Check if all URLs were fetched
    if len(existing_urls) == num_urls:
        print(f"\n✅ SUCCESS: All {num_urls} URLs fetched correctly!")
        print(f"   - Collection has {collection_count} chunks (> 10,000)")
        print(f"   - Pagination fetched all {len(existing_urls)} unique URLs")
        print(f"   - OLD BUG (limit=10000) would have missed {num_urls - (10000 // chunks_per_url)} URLs")
        success = True
    else:
        print(f"\n❌ FAILURE: Missing URLs!")
        print(f"   - Expected: {num_urls} URLs")
        print(f"   - Got: {len(existing_urls)} URLs")
        print(f"   - Missing: {num_urls - len(existing_urls)} URLs")
        success = False

    # Test specific URL from the "missed" range
    test_url_idx = 400  # This would be in chunks 12,000+ (missed by old limit=10000)
    test_url = f"https://docs.example.com/page-{test_url_idx}"

    print(f"\n6. SPECIFIC URL TEST")
    print("=" * 80)
    print(f"Testing URL: {test_url}")
    print(f"   (This URL is in chunk range {test_url_idx * chunks_per_url} - {(test_url_idx + 1) * chunks_per_url})")
    print(f"   (Would be MISSED by old limit=10000)")

    if test_url in existing_urls:
        print(f"✅ URL found in existing_urls (pagination works!)")
    else:
        print(f"❌ URL NOT found (pagination failed!)")
        success = False

    # Cleanup
    print(f"\n7. CLEANUP")
    print("=" * 80)
    print("Cleaning up test collection...")
    client.clear_collection()
    client.close()
    print("✅ Test collection cleared and connection closed")

    print("\n" + "=" * 80)
    if success:
        print("TEST PASSED ✅")
        print(f"\nPagination successfully fetched all {num_urls} URLs from {collection_count} chunks")
        print("The old limit=10000 bug is FIXED!")
    else:
        print("TEST FAILED ❌")
        print("Pagination did not fetch all URLs")
    print("=" * 80)

    return success


if __name__ == "__main__":
    try:
        success = test_pagination_duplicate_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
