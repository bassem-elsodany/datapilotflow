# Duplicate Cleanup Guide

## Problem

You have duplicate chunks in your Milvus collections due to the `limit=10000` bug in duplicate detection. Re-running the entire job would be expensive (crawling + embeddings cost money).

## Solution

Use the `cleanup_duplicates.py` script to identify and remove duplicates **without re-running jobs**.

---

## How It Works

### Algorithm

For each document (identified by `source_url`):

1. **Fetch all chunks** using pagination (handles collections of any size)
2. **Calculate correlation_id** for each chunk: `{source_url}_{chunk_index}_{content_hash}`
3. **Group chunks** by correlation_id
4. **Identify duplicates**: correlation_ids with multiple chunks
5. **Keep the newest** chunk (by `created_at` timestamp)
6. **Delete older duplicates** using Milvus `delete()` operation

### Example

```
Document: https://docs.mulesoft.com/http-connector/latest/http-documentation

Current state (DUPLICATES):
├─ Chunk 0 (correlation_id: "...http-documentation_0_abc123")
│  ├─ Primary key: uuid-1, created_at: 2025-01-10 10:00:00, job_id: job-1
│  └─ Primary key: uuid-2, created_at: 2025-01-11 15:00:00, job_id: job-2  ← DUPLICATE (newer)
├─ Chunk 1 (correlation_id: "...http-documentation_1_def456")
│  ├─ Primary key: uuid-3, created_at: 2025-01-10 10:00:05, job_id: job-1
│  └─ Primary key: uuid-4, created_at: 2025-01-11 15:00:05, job_id: job-2  ← DUPLICATE (newer)
└─ Chunk 2 (correlation_id: "...http-documentation_2_ghi789")
   └─ Primary key: uuid-5, created_at: 2025-01-10 10:00:10, job_id: job-1  ← NO DUPLICATE (only one)

After cleanup:
├─ Chunk 0: Keep uuid-2 (newer), DELETE uuid-1
├─ Chunk 1: Keep uuid-4 (newer), DELETE uuid-3
└─ Chunk 2: Keep uuid-5 (only one)

Result: 3 chunks instead of 5 (2 duplicates removed)
```

---

## Usage

### Step 1: List Your Collections

First, find the collection name you want to clean:

```bash
# Check MongoDB for collection names
# Or check your vectordb_collection table in the database
```

Example collection names:
- `user_123_mulesoft_docs`
- `knowledge_base_main`
- `company_documents`

### Step 2: Dry Run (Preview Only)

**ALWAYS run dry-run first** to see what will be deleted:

```bash
python cleanup_duplicates.py \
  --collection-name "your_collection_name" \
  --dry-run
```

**Example**:
```bash
python cleanup_duplicates.py \
  --collection-name "user_123_mulesoft_docs" \
  --dry-run
```

**Output**:
```
Fetching all chunks from collection using pagination...
Batch 1: Fetched 5000 chunks (total: 5000)
Batch 2: Fetched 5000 chunks (total: 10000)
Batch 3: Fetched 5000 chunks (total: 15000)
✅ Fetched 15000 total chunks from collection

Analysis complete:
  Total unique correlation_ids: 7500
  Correlation_ids with duplicates: 3750
  Total duplicate chunks to delete: 7500

================================================================================
DUPLICATE CLEANUP PREVIEW
================================================================================

Found duplicates for 500 URLs:

URL: https://docs.mulesoft.com/http-connector/latest/http-documentation
  Duplicate chunks: 30 chunks

URL: https://docs.mulesoft.com/http-connector/latest/examples
  Duplicate chunks: 25 chunks

...

Top 10 URLs with most duplicates:
================================================================================
1. https://docs.mulesoft.com/http-connector/latest/http-documentation...
   Duplicates: 30 chunks
   Example duplicate primary key: 550e8400-e29b-41d4-a716-446655440000
   Created at: 2025-01-11T15:00:00.000000
   Job ID: job-execution-2

...

================================================================================
SUMMARY
================================================================================
Total chunks currently in collection: 15000
Unique correlation_ids: 7500
Duplicate chunks to DELETE: 7500
Chunks to KEEP: 7500
Collection size after cleanup: 7500

Space savings: 7500 chunks (50.0% reduction)
================================================================================

DRY RUN MODE - No changes made
To perform actual cleanup, run with: --no-dry-run
```

### Step 3: Review the Preview

Check the output carefully:

- ✅ **URLs with duplicates**: Make sure these are expected
- ✅ **Number of duplicates**: Does it match your expectations?
- ✅ **Space savings**: How much will be removed?

### Step 4: Run Actual Cleanup

Once you're confident, run with `--no-dry-run`:

```bash
python cleanup_duplicates.py \
  --collection-name "your_collection_name" \
  --no-dry-run
```

**Confirmation required**:
```
⚠️  WARNING: About to delete duplicate chunks
================================================================================
Are you sure you want to proceed? (type 'yes' to confirm):
```

Type `yes` and press Enter to proceed.

**Output**:
```
Deleting duplicate chunks...
Collected 7500 primary keys to delete
Primary key field: id
Deleted batch 1: 1000 chunks (total: 1000)
Deleted batch 2: 1000 chunks (total: 2000)
...
Deleted batch 8: 500 chunks (total: 7500)
✅ Deleted 7500 duplicate chunks

================================================================================
CLEANUP COMPLETE
================================================================================
Deleted: 7500 duplicate chunks
Final collection size: 7500 chunks
Expected size: 7500 chunks
✅ Cleanup successful - collection size matches expected!
```

---

## Advanced Options

### Custom Vector Dimension

If your collection uses a different embedding dimension:

```bash
python cleanup_duplicates.py \
  --collection-name "your_collection" \
  --vector-dimension 768 \
  --dry-run
```

Common dimensions:
- `1536` - OpenAI text-embedding-ada-002 (default)
- `768` - Sentence Transformers, BERT
- `384` - MiniLM models
- `1024` - OpenAI text-embedding-3-small

---

## Safety Features

### 1. Dry Run by Default
The script **always defaults to dry-run mode** to prevent accidental deletions.

### 2. Keeps Newest Chunks
Always keeps the chunk with the latest `created_at` timestamp, ensuring you retain the most recent data.

### 3. Manual Confirmation
Requires typing `yes` to confirm deletion (prevents accidental Enter key presses).

### 4. Batch Processing
Deletes in batches of 1000 chunks to avoid memory issues and allow progress monitoring.

### 5. Verification
After cleanup, verifies that the final collection size matches the expected size.

---

## What Gets Deleted?

### Deleted (Older Duplicates)
- ❌ Older chunks with same correlation_id
- ❌ Chunks from earlier job executions
- ❌ Outdated content (if URL was updated)

### Kept (Newest Version)
- ✅ Newest chunk for each correlation_id
- ✅ Chunks from most recent job execution
- ✅ Most up-to-date content

### Example Timeline

```
Job 1 (2025-01-10):
- Crawled 500 URLs
- Created 15,000 chunks
- All marked with created_at: 2025-01-10

Job 2 (2025-01-11):
- Re-crawled same 500 URLs (due to duplicate bug)
- Created 15,000 MORE chunks (duplicates!)
- All marked with created_at: 2025-01-11

Cleanup Result:
- KEEP: 15,000 chunks from Job 2 (newer: 2025-01-11) ✅
- DELETE: 15,000 chunks from Job 1 (older: 2025-01-10) ❌
```

---

## Troubleshooting

### Issue: "Could not determine primary key field name"

**Cause**: Script can't find the primary key field in your collection schema.

**Solution**: Check your collection schema and update the script if needed:

```python
# In cleanup_duplicates.py, check the primary key detection logic
schema = self.client.collection.schema
for field in schema.fields:
    if field.is_primary:
        primary_field_name = field.name
        break
```

### Issue: "Size mismatch - expected X, got Y"

**Cause**: Deletion may have failed for some chunks, or collection had additional changes during cleanup.

**Solution**:
1. Check logs for deletion errors
2. Run cleanup script again
3. Verify no other processes are modifying the collection

### Issue: "No chunks found in collection"

**Cause**: Collection is empty or doesn't exist.

**Solution**: Verify collection name is correct:

```bash
# Check collection exists in Milvus
python -c "
from pymilvus import connections, utility
connections.connect(host='localhost', port='19530')
print(utility.list_collections())
"
```

### Issue: Script takes very long time

**Cause**: Large collection (millions of chunks) takes time to fetch and process.

**Solution**: This is normal. The script shows progress:
- Batch fetch progress: "Batch 1: Fetched 5000 chunks"
- Deletion progress: "Deleted batch 1: 1000 chunks"

Approximate timing:
- 10,000 chunks: ~30 seconds
- 100,000 chunks: ~5 minutes
- 1,000,000 chunks: ~30 minutes

---

## After Cleanup

### Verify Collection

Check that duplicates are gone:

```bash
python -c "
import sys
sys.path.insert(0, 'src')

from src.infrastructure.milvus.client import MilvusClientWrapper
from src.domain.rag.knowledge_chunk import KnowledgeChunk

client = MilvusClientWrapper(
    model=KnowledgeChunk,
    collection_name='your_collection_name',
    vector_dimension=1536
)

count = client.get_collection_count()
print(f'Collection count: {count}')
"
```

### Test Search Quality

Verify that search still works correctly:

```bash
# Run a test query through your application
# Search results should be the same or better (no duplicates!)
```

### Update Jobs

Now that duplicates are cleaned:

1. ✅ Deploy the pagination fix (already done)
2. ✅ Deploy the within-job tracking fix (already done)
3. ✅ Future jobs won't create duplicates

---

## Cost Savings

### Without Cleanup Script
```
Re-run job:
├─ Crawling: 500 URLs × 30 seconds = 4+ hours ⏰
├─ LLM embeddings: 15,000 chunks × $0.0001 = $1.50 💰
└─ Total cost: Time + Money

Result: Clean collection
```

### With Cleanup Script
```
Run cleanup:
├─ Fetch chunks: ~1 minute ⚡
├─ Analyze duplicates: ~10 seconds ⚡
├─ Delete duplicates: ~30 seconds ⚡
├─ Total time: ~2 minutes
└─ Total cost: $0.00 (no API calls) 💰

Result: Clean collection
```

**Savings**: Hours of time + API costs!

---

## Summary

✅ **Fast**: Cleans thousands of chunks in minutes

✅ **Safe**: Dry-run by default, keeps newest chunks, requires confirmation

✅ **Cost-effective**: No re-crawling, no re-embedding

✅ **Scalable**: Uses pagination, handles millions of chunks

✅ **Smart**: Groups by correlation_id, preserves latest data

**Next Steps**:
1. Run dry-run to preview: `python cleanup_duplicates.py --collection-name "your_collection" --dry-run`
2. Review the output carefully
3. Run actual cleanup: `python cleanup_duplicates.py --collection-name "your_collection" --no-dry-run`
4. Verify results
