"""
Test script to verify upsert-based deduplication works correctly.

This script simulates two job executions on the same URL and verifies that:
1. First execution inserts chunks
2. Second execution updates (not duplicates) the same chunks
3. Collection count remains the same after second execution
"""

import sys
sys.path.insert(0, 'src')

from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.config import settings

def test_upsert_deduplication():
    """Test that upsert prevents duplicates."""

    # Test configuration
    test_collection_name = "test_upsert_collection"
    vector_dimension = 1536  # OpenAI embedding dimension

    print("=" * 80)
    print("UPSERT DEDUPLICATION TEST")
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

    # Create test chunks simulating same URL, same content
    test_url = "https://docs.mulesoft.com/http-connector/latest/http-documentation"
    test_content_1 = "This is chunk 0 from the HTTP connector documentation."
    test_content_2 = "This is chunk 1 from the HTTP connector documentation."

    # Job 1: First execution
    print("\n3. JOB EXECUTION 1: Inserting initial chunks...")
    chunks_job1 = [
        KnowledgeChunk(
            page_content=test_content_1,
            source_url=test_url,
            job_id="job-execution-1",
            title="HTTP Connector Documentation",
            chunk_id="chunk-0",
            chunk_index=0,
            total_chunks=2,
        ),
        KnowledgeChunk(
            page_content=test_content_2,
            source_url=test_url,
            job_id="job-execution-1",
            title="HTTP Connector Documentation",
            chunk_id="chunk-1",
            chunk_index=1,
            total_chunks=2,
        ),
    ]

    # Create dummy vectors (all zeros for testing)
    vectors_job1 = [[0.0] * vector_dimension for _ in chunks_job1]

    # Ingest (should use upsert)
    client.ingest_documents(chunks_job1, vectors_job1)
    count_after_job1 = client.get_collection_count()
    print(f"✅ Job 1 completed. Collection count: {count_after_job1}")
    print(f"   Expected: 2 chunks")

    # Job 2: Second execution (SAME URL, SAME CONTENT)
    print("\n4. JOB EXECUTION 2: Re-ingesting same chunks (simulating duplicate scenario)...")
    chunks_job2 = [
        KnowledgeChunk(
            page_content=test_content_1,  # SAME CONTENT
            source_url=test_url,  # SAME URL
            job_id="job-execution-2",  # Different job ID
            title="HTTP Connector Documentation",
            chunk_id="chunk-0",
            chunk_index=0,  # SAME CHUNK INDEX
            total_chunks=2,
        ),
        KnowledgeChunk(
            page_content=test_content_2,  # SAME CONTENT
            source_url=test_url,  # SAME URL
            job_id="job-execution-2",  # Different job ID
            title="HTTP Connector Documentation",
            chunk_id="chunk-1",
            chunk_index=1,  # SAME CHUNK INDEX
            total_chunks=2,
        ),
    ]

    vectors_job2 = [[0.0] * vector_dimension for _ in chunks_job2]

    # Ingest again (should UPDATE, not INSERT)
    client.ingest_documents(chunks_job2, vectors_job2)
    count_after_job2 = client.get_collection_count()
    print(f"✅ Job 2 completed. Collection count: {count_after_job2}")
    print(f"   Expected: 2 chunks (SAME as Job 1, not 4!)")

    # Verify results
    print("\n5. VERIFICATION")
    print("=" * 80)

    if count_after_job2 == count_after_job1 == 2:
        print("✅ SUCCESS: Upsert deduplication works!")
        print(f"   - Job 1: {count_after_job1} chunks inserted")
        print(f"   - Job 2: {count_after_job2} chunks (updated, not duplicated)")
        print(f"   - Difference: {count_after_job2 - count_after_job1} (expected: 0)")
        print("\n🎉 NO DUPLICATES CREATED!")
        success = True
    else:
        print("❌ FAILURE: Duplicates were created!")
        print(f"   - Job 1: {count_after_job1} chunks")
        print(f"   - Job 2: {count_after_job2} chunks")
        print(f"   - Difference: {count_after_job2 - count_after_job1}")
        print(f"   - Expected difference: 0")
        print("\n⚠️  DUPLICATES DETECTED!")
        success = False

    # Fetch documents to inspect
    print("\n6. INSPECTING STORED DOCUMENTS")
    print("=" * 80)
    docs = client.fetch_documents(limit=10, return_fields=["correlation_id", "job_id", "chunk_index", "source_url"])

    for i, doc in enumerate(docs, 1):
        props = doc.get("properties", {})
        print(f"\nDocument {i}:")
        print(f"  correlation_id: {doc.get('id')}")
        print(f"  job_id: {props.get('job_id')}")
        print(f"  chunk_index: {props.get('chunk_index')}")
        print(f"  source_url: {props.get('source_url', '')[:60]}...")

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
    else:
        print("TEST FAILED ❌")
    print("=" * 80)

    return success


if __name__ == "__main__":
    try:
        success = test_upsert_deduplication()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
