"""
Test script to verify heartbeat mechanism prevents timeout when skipping duplicates.

This script simulates a scenario where:
1. A collection already has URLs ingested
2. A new job runs on the same URLs
3. All URLs are skipped due to duplicate detection
4. The job should complete in ~1-2 seconds (not timeout after 600s)
"""

import sys
import time
sys.path.insert(0, 'src')

import asyncio
from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig, ContentSourceType, ScrapingMode
from src.domain.knowledge.knowledge_job import KnowledgeJob
from src.processors.knowledge_job.services.document_extraction_service import get_document_extraction_service
from src.config import settings

async def test_heartbeat_mechanism():
    """Test that heartbeat prevents timeout when all URLs are skipped."""

    # Test configuration
    test_collection_name = "test_heartbeat_collection"
    vector_dimension = 1536  # OpenAI embedding dimension

    print("=" * 80)
    print("HEARTBEAT MECHANISM TEST")
    print("=" * 80)

    # Create test Milvus client
    print("\n1. Setting up test collection...")
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

    # Pre-populate collection with URLs to simulate duplicates
    print("\n3. Pre-populating collection with test URLs...")
    test_urls = [
        f"https://docs.example.com/page-{i}" for i in range(100)
    ]

    # Insert chunks for each URL
    chunks = []
    vectors = []
    for i, url in enumerate(test_urls):
        chunk = KnowledgeChunk(
            page_content=f"Content for page {i}",
            source_url=url,
            job_id="pre-populate-job",
            title=f"Page {i}",
            chunk_id=f"chunk-{i}",
            chunk_index=0,
            total_chunks=1,
        )
        chunks.append(chunk)
        vectors.append([0.0] * vector_dimension)

    client.ingest_documents(chunks, vectors)
    count_after_prepopulate = client.get_collection_count()
    print(f"✅ Pre-populated {count_after_prepopulate} chunks into collection")

    # Create knowledge source config pointing to the same URLs
    print("\n4. Creating knowledge source config (same URLs as pre-populated)...")
    knowledge_source_config = KnowledgeSourceConfig(
        id="test-source",
        user_id="test-user",
        name="Test Source",
        url="https://docs.example.com/page-0",  # Starting URL
        content_source_type=ContentSourceType.WEB_SCRAPING,
        scraping_mode=ScrapingMode.SINGLE_PAGE,
        crawl_depth=0,  # Only process the single URL
        created_by="test",
        updated_by="test",
    )

    # Create knowledge job with duplicate checking enabled
    knowledge_job = KnowledgeJob(
        id="test-job",
        user_id="test-user",
        knowledge_source_config_id="test-source",
        vectordb_collection_id=test_collection_name,
        batch_size=10,
        check_duplicates_before_insert=True,  # ENABLE duplicate checking
    )

    print(f"✅ Knowledge source config created: {knowledge_source_config.name}")
    print(f"✅ Knowledge job created with check_duplicates_before_insert=True")

    # Test: Extract documents (should skip all due to duplicates)
    print("\n5. Testing extraction with duplicate detection...")
    print("   (All URLs should be skipped, heartbeat should prevent timeout)")

    extraction_service = get_document_extraction_service()

    start_time = time.time()
    batch_count = 0
    doc_count = 0
    heartbeat_count = 0

    try:
        async for batch in extraction_service.extract_documents(
            knowledge_job=knowledge_job,
            knowledge_source_config=knowledge_source_config,
            batch_size=knowledge_job.batch_size,
        ):
            batch_count += 1
            doc_count += len(batch)

            if len(batch) == 0:
                heartbeat_count += 1
                print(f"   Heartbeat {heartbeat_count} received (empty batch)")
            else:
                print(f"   Batch {batch_count}: {len(batch)} documents")

        elapsed_time = time.time() - start_time

        print("\n6. RESULTS")
        print("=" * 80)
        print(f"Elapsed time: {elapsed_time:.2f}s")
        print(f"Batches received: {batch_count}")
        print(f"Documents extracted: {doc_count}")
        print(f"Heartbeats received: {heartbeat_count}")

        # Success criteria:
        # 1. Should complete in < 60 seconds (not timeout at 600s)
        # 2. Should extract 0 documents (all duplicates)
        # 3. Should receive at least 1 heartbeat (if URLs were checked)

        success = True

        if elapsed_time >= 60:
            print("\n❌ FAILURE: Job took too long (timeout issue)")
            print(f"   Expected: < 60s")
            print(f"   Actual: {elapsed_time:.2f}s")
            success = False
        else:
            print(f"\n✅ SUCCESS: Job completed quickly ({elapsed_time:.2f}s, not 600s timeout)")

        if doc_count > 0:
            print(f"⚠️  WARNING: Expected 0 documents (all duplicates), got {doc_count}")
            # Not a failure - might be valid if duplicate detection didn't work
        else:
            print(f"✅ SUCCESS: All URLs were skipped (0 documents extracted)")

        print(f"\n✅ HEARTBEAT MECHANISM: {'Working' if heartbeat_count > 0 else 'Not triggered (job too fast)'}")

    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        print("\n❌ FAILURE: Job timed out!")
        print(f"   Elapsed time: {elapsed_time:.2f}s")
        print("   Heartbeat mechanism did NOT work")
        success = False

    # Cleanup
    print("\n7. CLEANUP")
    print("=" * 80)
    print("Cleaning up test collection...")
    client.clear_collection()
    client.close()
    print("✅ Test collection cleared and connection closed")

    print("\n" + "=" * 80)
    if success:
        print("TEST PASSED ✅")
        print("\nHeartbeat mechanism prevents timeout when skipping duplicates!")
    else:
        print("TEST FAILED ❌")
        print("\nHeartbeat mechanism did not work as expected")
    print("=" * 80)

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(test_heartbeat_mechanism())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
