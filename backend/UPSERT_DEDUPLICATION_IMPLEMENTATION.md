# Upsert-Based Deduplication Implementation

## Problem Summary

**Issue**: Duplicate chunks appearing in Milvus for the same URL across different job executions, even with `check_duplication=True`.

**Example**: URL `https://docs.mulesoft.com/http-connector/latest/http-documentation` was stored twice with different chunks for the same content.

## Root Cause Analysis

### Why Duplicates Occurred

The system had **TWO** deduplication mechanisms:

#### 1. Application-Level Duplicate Detection (Pre-Storage)
**Location**: [duplicate_detector.py](src/application/data/storage/duplicate_detector.py)

**How it works**:
- Fetches existing URLs from Milvus before storage
- Skips documents if URL already exists
- ✅ **Works when enabled and Milvus is reachable**

**Why it fails**:
- ❌ If Milvus connection times out during duplicate check → returns empty set → all documents proceed to storage
- ❌ If `check_duplication=False` → bypasses detection entirely
- ❌ If duplicate detection throws exception → error handler returns all documents

#### 2. Database-Level Deduplication (Storage Layer) - BROKEN
**Location**: [client.py](src/infrastructure/milvus/client.py)

**OLD CODE (BROKEN)**:
```python
# Primary key was random UUID
FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100)

# Insert operation with NEW random UUID every time
data.append({
    "id": str(uuid.uuid4()),  # <-- GENERATES NEW ID EVERY TIME!
    "correlation_id": f"{source_url}_{chunk_index}_{content_hash}",
    # ... other fields
})

self.collection.insert(data)  # <-- ALWAYS INSERTS, NEVER CHECKS
```

**Why it created duplicates**:
- Primary key = random UUID → **every insert gets a NEW unique ID**
- `.insert()` operation → **always adds new entities**, never checks for existing
- `correlation_id` was just a regular field → **not used for deduplication**

**Result**: When duplicate detection failed/was disabled, the same chunks were re-inserted with different IDs.

---

## Solution: Upsert with correlation_id as Primary Key

### Key Changes

#### 1. Changed Primary Key to correlation_id
**File**: [client.py:289-290](src/infrastructure/milvus/client.py#L289-L290)

```python
# PRIMARY KEY: correlation_id for chunk-level deduplication
FieldSchema(
    name="correlation_id", dtype=DataType.VARCHAR, is_primary=True, max_length=512
),
# id moved to regular field for backward compatibility
FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100),
```

**Benefits**:
- `correlation_id` is deterministic: `{source_url}_{chunk_index}_{content_hash}`
- Same chunk always gets the same `correlation_id`
- Enables automatic deduplication at database level

#### 2. Replaced INSERT with UPSERT
**File**: [client.py:559-563](src/infrastructure/milvus/client.py#L559-L563)

```python
# Use UPSERT instead of INSERT for automatic deduplication
# If correlation_id exists: UPDATE the chunk
# If correlation_id is new: INSERT the chunk
self.collection.upsert(data)
self.collection.flush()

logger.info(f"✅ Upserted {len(documents)} documents into Milvus (automatic deduplication enabled)")
```

**How upsert works** (from Milvus docs):
- Checks if primary key (`correlation_id`) exists
- **If found**: Updates the existing entity (replaces all fields)
- **If not found**: Inserts as new entity

#### 3. Updated Query Operations
**File**: [client.py:775-785](src/infrastructure/milvus/client.py#L775-L785)

```python
# Query documents using correlation_id as primary key
results = self.collection.query(
    expr=filter_expr or "correlation_id != ''",  # Use correlation_id
    output_fields=return_fields,
    limit=limit,
)

# Format results with correlation_id as id
for result in results:
    formatted_result = {"id": result.get("correlation_id"), "properties": {}}
```

---

## How Deduplication Now Works

### Scenario: Same URL processed twice

**Job Execution 1** (First time):
```
1. Extract chunks from URL
2. Generate correlation_ids:
   - Chunk 0: "https://example.com_0_abc123"
   - Chunk 1: "https://example.com_1_def456"
3. Upsert to Milvus:
   - Check if "https://example.com_0_abc123" exists → NO → INSERT ✅
   - Check if "https://example.com_1_def456" exists → NO → INSERT ✅
4. Result: 2 chunks in collection
```

**Job Execution 2** (Same URL, hours later):
```
1. Extract same chunks from same URL
2. Generate SAME correlation_ids:
   - Chunk 0: "https://example.com_0_abc123" (SAME!)
   - Chunk 1: "https://example.com_1_def456" (SAME!)
3. Upsert to Milvus:
   - Check if "https://example.com_0_abc123" exists → YES → UPDATE ✅
   - Check if "https://example.com_1_def456" exists → YES → UPDATE ✅
4. Result: STILL 2 chunks (updated, not duplicated!)
```

### Benefits

✅ **Database-level deduplication**: Works even if application-level duplicate detection fails

✅ **Idempotent operations**: Running same job multiple times doesn't create duplicates

✅ **Automatic updates**: If content changes (different hash), creates new chunk; if content same, updates existing

✅ **No manual duplicate cleanup needed**: Milvus handles it automatically

---

## Testing

### Test Script
**Location**: [test_upsert_deduplication.py](test_upsert_deduplication.py)

**What it tests**:
1. Creates test collection
2. Inserts 2 chunks (Job 1)
3. Re-inserts SAME 2 chunks with different job_id (Job 2)
4. Verifies collection count remains 2 (not 4)
5. Inspects documents to confirm updates, not duplicates

**Run test**:
```bash
python test_upsert_deduplication.py
```

**Expected output**:
```
✅ Job 1 completed. Collection count: 2
✅ Job 2 completed. Collection count: 2
✅ SUCCESS: Upsert deduplication works!
🎉 NO DUPLICATES CREATED!
TEST PASSED ✅
```

---

## Migration Impact

### ⚠️ IMPORTANT: Requires Collection Recreation

**Why**: Milvus does not support changing primary key on existing collections.

**Impact**:
1. Existing collections will continue to work with old schema (random UUID primary key)
2. New collections will use new schema (correlation_id primary key)
3. To fix existing collections with duplicates:
   - Clear and re-ingest data
   - OR migrate data to new collection

### Migration Steps

**Option 1: Clear and Re-ingest** (Simplest)
```python
# In your job configuration, set:
clear_collection_before_ingestion = True
```

**Option 2: Manual Migration** (Preserves data)
```python
# 1. Export all chunks from old collection
old_client = MilvusClientWrapper(collection_name="old_collection", ...)
documents = old_client.fetch_documents(limit=100000)

# 2. Drop old collection
old_client.clear_collection()

# 3. Recreate collection (will use new schema automatically)
new_client = MilvusClientWrapper(collection_name="old_collection", ...)

# 4. Re-ingest with upsert (deduplicates automatically)
new_client.ingest_documents(documents, vectors)
```

---

## Backward Compatibility

✅ **Field `id` still exists**: Moved from primary key to regular field for backward compatibility

✅ **API unchanged**: `ingest_documents()` signature unchanged, just uses upsert internally

✅ **Search results unchanged**: `hit.id` now returns `correlation_id` instead of random UUID

⚠️ **Breaking change**: If your code relies on `id` being a random UUID, you'll need to update it

---

## Files Modified

1. **[src/infrastructure/milvus/client.py](src/infrastructure/milvus/client.py)**
   - Changed primary key from `id` to `correlation_id` (line 289-290)
   - Replaced `.insert()` with `.upsert()` (line 562)
   - Updated query operations to use `correlation_id` (line 775-785)
   - Updated docstrings to reflect upsert behavior

2. **[test_upsert_deduplication.py](test_upsert_deduplication.py)** ✅ NEW FILE
   - Complete test script for verifying upsert deduplication

3. **[UPSERT_DEDUPLICATION_IMPLEMENTATION.md](UPSERT_DEDUPLICATION_IMPLEMENTATION.md)** ✅ THIS FILE
   - Complete documentation of implementation

---

## Verification Checklist

Before deploying to production:

- [ ] Run test script: `python test_upsert_deduplication.py`
- [ ] Verify test passes with "NO DUPLICATES CREATED"
- [ ] Clear existing collections or migrate data
- [ ] Test with real job execution (same URL twice)
- [ ] Check collection count remains stable
- [ ] Verify search results return correct documents
- [ ] Monitor logs for "✅ Upserted N documents" messages

---

## Summary

**Problem**: Random UUID primary key + INSERT operation = duplicates when duplicate detection fails

**Solution**: Deterministic correlation_id primary key + UPSERT operation = automatic deduplication

**Result**: Database-level deduplication that works even when application-level detection fails

**Next Steps**: Test with `test_upsert_deduplication.py` and migrate existing collections
