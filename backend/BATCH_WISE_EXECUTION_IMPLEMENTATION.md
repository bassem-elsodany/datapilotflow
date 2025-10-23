# Batch-Wise Execution Implementation

## Problem Statement

The original pipeline architecture processed ALL data through each step sequentially:
```
Extract ALL files → Accumulate in memory
Chunk ALL documents → Accumulate in memory
Embed ALL chunks → Accumulate in memory
Store ALL vectors
```

This caused memory issues with large file sets and didn't respect the job's `batch_size` configuration properly.

## Solution

Implemented **batch-wise execution** for local files where each batch goes through ALL pipeline steps before processing the next batch:

```
Batch 1: Extract → Chunk → Embed → Store
Batch 2: Extract → Chunk → Embed → Store
Batch 3: Extract → Chunk → Embed → Store
...
```

## Implementation Details

### 1. JobOrchestrator - Dual Execution Modes

Modified [job_orchestrator.py](src/processors/knowledge_job/orchestration/job_orchestrator.py) to support two execution modes:

**Traditional Mode** (for web scraping):
- Extracts all documents
- Processes all through each step sequentially
- Used when `content_source_type != LOCAL_FILES`

**Batch-Wise Mode** (for local files):
- Extracts files in batches
- Each batch goes through all steps before next batch
- Used when `content_source_type == LOCAL_FILES`

### 2. Key Changes

**`execute_job()` method** - Routes to appropriate execution mode:
```python
async def execute_job(...):
    if knowledge_source_config.content_source_type == ContentSourceType.LOCAL_FILES:
        return await self._execute_job_batch_wise(...)
    else:
        return await self._execute_job_traditional(...)
```

**`_execute_job_batch_wise()` method** - New batch processing loop:
```python
async def _execute_job_batch_wise(...):
    # Get pipeline steps
    extraction_step = self.pipeline.steps[0]  # FileExtractionStep
    chunking_step = self.pipeline.steps[1]
    embedding_step = self.pipeline.steps[2]
    storage_step = self.pipeline.steps[3]
    timeline_step = self.pipeline.steps[4]

    # Process batches
    async for doc_batch in extraction_step._extract_files(context, batch_size):
        # Create fresh context for this batch
        batch_context = JobContext(...)
        batch_context.documents = doc_batch

        # Run all steps for this batch
        await chunking_step.execute(batch_context)
        await embedding_step.execute(batch_context)
        await storage_step.execute(batch_context)

        # Accumulate stats
        total_documents += len(doc_batch)
        total_chunks += len(batch_context.chunks)
```

## Flow Comparison

### Before (Traditional - All Files in Memory)
```
┌─────────────────────────────────────────┐
│ FileExtractionStep                      │
│  ├─ Read file 1                         │
│  ├─ Read file 2                         │
│  ├─ ...                                 │
│  └─ Read file 177                       │
│      ↓ context.documents = [all 177]    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ DocumentChunkingStep                    │
│  └─ Chunk all 177 documents at once     │
│      ↓ context.chunks = [all 1455]      │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ EmbeddingGenerationStep                 │
│  └─ Embed all 1455 chunks at once      │
│      ↓ FAILS: Token limit exceeded      │
└─────────────────────────────────────────┘
```

### After (Batch-Wise - Process in Chunks)
```
BATCH 1 (50 files):
┌─────────────────────────────────────────┐
│ Extract 50 files                        │
│  ↓ batch_context.documents = [50]       │
├─────────────────────────────────────────┤
│ Chunk 50 documents                      │
│  ↓ batch_context.chunks = [~410]        │
├─────────────────────────────────────────┤
│ Embed ~410 chunks                       │
│  ↓ batch_context.vectors = [~410]       │
├─────────────────────────────────────────┤
│ Store ~410 vectors                      │
└─────────────────────────────────────────┘

BATCH 2 (50 files):
┌─────────────────────────────────────────┐
│ Extract 50 files                        │
│ Chunk → Embed → Store                   │
└─────────────────────────────────────────┘

BATCH 3 (50 files):
┌─────────────────────────────────────────┐
│ Extract 50 files                        │
│ Chunk → Embed → Store                   │
└─────────────────────────────────────────┘

BATCH 4 (27 files):
┌─────────────────────────────────────────┐
│ Extract 27 files                        │
│ Chunk → Embed → Store                   │
└─────────────────────────────────────────┘
```

## Benefits

### 1. Memory Efficiency
- Only one batch in memory at a time
- Context is cleared between batches
- No accumulation of all documents

### 2. Respects batch_size Configuration
- Uses `knowledge_job.batch_size` from job config
- Processes exactly that many files per batch

### 3. Better Progress Tracking
- Progress updates after each batch
- Can see "Batch 1 of 4 completed"
- More granular status reporting

### 4. Avoids API Limits
- Each batch has fewer chunks to embed
- Won't hit token limits on embedding API
- Distributes load across multiple API calls

### 5. Faster Failure Recovery
- If batch 3 fails, batches 1-2 are already stored
- Can resume from failed batch
- Less data loss on errors

## Example Log Output

### Before (All at Once)
```
Starting file extraction from 177 files
Extracted batch 18: 7 documents (total: 177)
File extraction completed: 177 documents in 0.02s
Starting document chunking for 177 documents
Document chunking completed: 1455 chunks in 0.19s
Starting embedding generation for 1455 chunks
ERROR: Requested 312774 tokens, max 300000 tokens per request
```

### After (Batch-Wise)
```
Using batch-wise execution for local files job 68f99717314c9857778304c7
Starting batch-wise pipeline orchestration
Processing batch 1: 50 documents
Batch 1 completed: 50 docs, 410 chunks, 410 vectors
Processing batch 2: 50 documents
Batch 2 completed: 50 docs, 412 chunks, 412 vectors
Processing batch 3: 50 documents
Batch 3 completed: 50 docs, 408 chunks, 408 vectors
Processing batch 4: 27 documents
Batch 4 completed: 27 docs, 225 chunks, 225 vectors
Batch-wise job completed successfully: 177 docs, 1455 chunks across 4 batches
```

## Configuration

The batch size is controlled by the job configuration:

```python
knowledge_job = KnowledgeJob(
    batch_size=50,  # Process 50 files per batch
    ...
)
```

## Backward Compatibility

- **Web scraping jobs**: Use traditional pipeline (unchanged behavior)
- **Local file jobs**: Use batch-wise execution (new behavior)
- Automatic routing based on `content_source_type`

## Technical Details

### Context Management

Each batch gets a **fresh context**:
```python
batch_context = JobContext(
    job=knowledge_job,
    knowledge_source_config=knowledge_source_config,
    user_id=user_id,
    status_callback=status_callback,
)
batch_context.documents = doc_batch  # Only this batch's documents
```

After processing:
- `batch_context.documents` = current batch's documents
- `batch_context.chunks` = current batch's chunks
- `batch_context.vectors` = current batch's vectors

Context is discarded after storage, freeing memory.

### Stats Accumulation

Stats are accumulated across batches:
```python
total_documents += len(doc_batch)
total_chunks += len(batch_context.chunks)
total_vectors += len(batch_context.vectors)
```

### Timeline Management

- Timeline started once at beginning
- Updated after each batch
- Marked complete/failed at end

## Files Modified

1. **[job_orchestrator.py](src/processors/knowledge_job/orchestration/job_orchestrator.py)**
   - Added `_execute_job_batch_wise()` method
   - Renamed existing `execute_job()` to `_execute_job_traditional()`
   - New `execute_job()` routes to appropriate mode

2. **[file_extraction_step.py](src/processors/knowledge_job/pipeline/steps/file_extraction_step.py)**
   - Already had `_extract_files()` as async generator
   - Compatible with batch-wise execution
   - No changes needed!

3. **[pipeline_factory.py](src/processors/knowledge_job/pipeline/pipeline_factory.py)**
   - Updated to pass `batch_size=None` to use job's config

4. **[container.py](src/processors/knowledge_job/container.py)**
   - Updated to pass `extraction_batch_size=None`

## Testing

To test batch-wise execution:

1. Create a local files job with `batch_size=10`
2. Upload 25 files
3. Execute the job
4. Check logs for:
   - "Using batch-wise execution"
   - "Processing batch 1: 10 documents"
   - "Processing batch 2: 10 documents"
   - "Processing batch 3: 5 documents"
   - "Batch-wise job completed: 25 docs across 3 batches"

## Future Enhancements

1. **Parallel Batch Processing**: Process multiple batches concurrently
2. **Checkpoint/Resume**: Save progress after each batch for resumability
3. **Dynamic Batch Sizing**: Adjust batch size based on memory usage
4. **Batch Retry Logic**: Retry failed batches independently

## Summary

The batch-wise execution implementation ensures that:
- ✅ Each batch respects the job's `batch_size` configuration
- ✅ Memory usage is bounded (only one batch in memory)
- ✅ API limits are respected (smaller embedding requests)
- ✅ Progress is tracked per batch
- ✅ Web scraping jobs continue to work as before
- ✅ Local file jobs now process efficiently in batches
