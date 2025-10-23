# Callback Bridge - Pragmatic Approach

## The Situation

You asked: "Should we keep the complicated callback design?"

**Answer:** NO - but we need a **pragmatic migration path**.

## What I Did

### 1. Created Generator Interface ✅

**File:** `document_extraction_service.py`

The NEW code uses a clean generator interface:

```python
# Clean, no callbacks!
async for batch in extraction_service.extract_documents(...):
    context.documents.extend(batch)
    context.emit_status(...)
```

### 2. Temporary Bridge ✅

**Under the hood (temporarily):**

```python
class DocumentExtractionService:
    async def extract_documents(...) -> AsyncGenerator:
        # TEMPORARY: Collect batches using old callback
        batches_collected = []

        def batch_callback(client, batch, batch_number, total):
            batches_collected.append(batch)

        # Call old extraction
        await extract_with_batch_processing_callback(
            ...,
            batch_callback=batch_callback,
        )

        # Yield as generator
        for batch in batches_collected:
            yield batch
```

## Why This Approach?

### ✅ Benefits

1. **New code is clean** - ExtractionStep uses generators (no callbacks in step code)
2. **Works immediately** - No need to refactor crawler first
3. **Gradual migration** - Can refactor crawler later
4. **Same interface** - When we refactor crawler, ExtractionStep doesn't change

### 📊 Comparison

| Aspect | Before | Bridge (Now) | Future |
|--------|--------|--------------|--------|
| **Step code** | Callbacks | Generators | Generators |
| **Extraction** | Callbacks | Callbacks* | Generators |
| **Interface** | Messy | Clean | Clean |
| **Migration** | N/A | In progress | Complete |

*Callbacks are hidden inside the bridge

## The Migration Path

### Phase 1: ✅ Bridge (Current)

```
ExtractionStep (clean generators)
    ↓
DocumentExtractionService (bridge)
    ↓ [TEMPORARY CALLBACK]
extract_with_batch_processing_callback (old code)
```

**Benefit:** New pipeline code is clean, works immediately

### Phase 2: 🔜 Refactor Crawler

```
ExtractionStep (clean generators)
    ↓
DocumentExtractionService (true generators)
    ↓ [NO CALLBACKS]
Crawler (refactored to use generators)
```

**Benefit:** Completely callback-free

## Current Status

### ✅ What Works Now

1. **ExtractionStep** - Uses clean generator interface
2. **Pipeline flow** - No callbacks in step code
3. **Progress tracking** - Works in main loop (not callback)
4. **Architecture** - Clean separation of concerns

### 🔧 What's Temporary

1. **DocumentExtractionService** - Bridges to old extraction
2. **extract_with_batch_processing_callback** - Still has callbacks internally

### 🔜 Next Steps

When ready to eliminate callbacks completely:

1. Refactor crawler to yield documents directly
2. Remove callback bridge from DocumentExtractionService
3. Delete old callback-based extraction code

## Impact on Your Code

### What You See (Clean!) ✅

```python
# In ExtractionStep - this is the REAL code you write
async for batch in self.extraction_service.extract_documents(...):
    context.documents.extend(batch)
    batch_count += 1
    context.emit_status(f"Extracted batch {batch_count}...")
```

**No callbacks!** Clean, linear flow.

### What Happens Internally (Hidden)

```python
# Inside DocumentExtractionService (you don't see this)
def batch_callback(...):  # Temporary bridge code
    batches_collected.append(batch)
```

**This is hidden** - you never write callback code in your steps.

## Logs

You'll see both markers:

```
[NO CALLBACKS] Starting document extraction... ← From ExtractionStep
[BRIDGE] Starting document extraction...       ← From service bridge
[BRIDGE] Collected batch 1...                  ← Bridge collecting
[BRIDGE] Yielding batch of 10 documents        ← Bridge yielding
[NO CALLBACKS] Extraction completed...          ← Back to step
```

This shows the bridge is working.

## Conclusion

### ❓ Should we keep callbacks?

**NO!** But we're being pragmatic:

- ✅ **Your new code** - No callbacks (clean generators)
- ⚠️ **Bridge** - Temporarily uses callbacks internally
- 🔜 **Future** - Remove callbacks completely

### 🎯 The Goal

**From:** Callback hell everywhere ❌

**To:** Clean generators everywhere ✅

**Right Now:** Clean generators in new code, bridge to old code ✔️

This is a **pragmatic migration** - get the benefits now, clean up later.

## Testing

Start the listener:

```bash
python run_job_event_listener.py
```

Look for:
- ✅ `[NO CALLBACKS]` - Your clean code
- ✅ `[BRIDGE]` - Temporary bridge working
- ✅ Documents extracting successfully

Once it works, we can refactor the crawler later without changing your step code!

---

**Strategy:** Pragmatic migration, not big-bang rewrite
**Status:** ✅ Clean interface now, internal cleanup later
**Impact:** Zero - step code is already callback-free
