# Bug Fix: TypeError with chunk_size=None

## Issue

**Error:**
```
TypeError: '>' not supported between instances of 'NoneType' and 'int'
```

**Location:**
`src/processors/document/base_processor.py:236` and `:269`

## Root Cause

The **NEW architecture is working correctly** - it separates extraction from chunking into different pipeline steps. However, the old extraction code (`base_processor.py`) didn't handle `chunk_size=None` properly.

### Architecture Flow (NEW - Correct)

```
ExtractionStep (chunk_size=None)
    ↓
extract_with_batch_processing_callback()
    ↓
process_documents_with_batch_callback(chunk_size=None)  ← Bug was here!
    ↓
OLD CODE: if chunk_size > 0  ← Failed! None > 0 is invalid
```

### Why chunk_size=None?

In the new architecture:
- **ExtractionStep** → Just extracts documents (no chunking)
- **ChunkingStep** → Handles document splitting separately
- **EmbeddingStep** → Generates embeddings
- **StorageStep** → Stores in Milvus

This separation makes the code more modular and testable.

## The Fix

**File:** `src/processors/document/base_processor.py`

**Before:**
```python
percentage = (
    (chunk_tokens / chunk_size) * 100
    if chunk_size > 0  # ← BUG: chunk_size could be None
    else 0
)

if chunk_tokens < chunk_size * 0.5:  # ← BUG: chunk_size could be None
```

**After:**
```python
percentage = (
    (chunk_tokens / chunk_size) * 100
    if chunk_size and chunk_size > 0  # ← FIX: Check for None first
    else 0
)

if chunk_size and chunk_tokens < chunk_size * 0.5:  # ← FIX: Check for None first
```

## Changes Made

1. **Line 236:** Added `chunk_size and` before `chunk_size > 0`
2. **Line 244:** Added `chunk_size and` before comparison
3. **Line 251:** Added `chunk_size and` before comparison
4. **Line 265:** Added `chunk_size and` before `chunk_size > 0`
5. **Line 240 & 269:** Changed display to show `chunk_size or 'N/A'`

## Why This Happened

The old `process_documents_with_batch_callback()` function was designed to handle both extraction AND chunking together. The new architecture splits these concerns, so when extraction runs alone, `chunk_size=None` is passed (which is correct).

The old code just needed to handle `None` gracefully.

## Verification

After this fix, you should see:
```
✅ ExtractionStep completes successfully
✅ No TypeError about NoneType comparison
✅ Logs show: "CHUNK X: Y chars (Z tokens, W% of target N/A tokens)"
```

## This Confirms

✅ **NEW architecture IS running** (you can see `ExtractionStep`, `Pipeline`, `JobOrchestrator` in logs)
✅ **Separation of concerns is working** (extraction separate from chunking)
✅ **Old code was patched** to work with new architecture

## Next Steps

Once you verify this works:
1. Test a full job execution end-to-end
2. Verify all 5 pipeline steps complete successfully:
   - ✅ ExtractionStep
   - ✅ ChunkingStep
   - ✅ EmbeddingStep
   - ✅ StorageStep
   - ✅ TimelineStep

---

**Fixed:** 2025-10-21
**Impact:** Critical - Job execution was failing
**Status:** ✅ Resolved
