# Refactored Job Event Listener Architecture

## Overview

This directory contains the **new modular, elastic architecture** for the job event listener, replacing the previous monolithic 1,438-line spaghetti code with a clean, testable, maintainable system.

## Architecture Comparison

### Before (Old Architecture) ❌
- **Single 700-line processor** handling everything
- **Tight coupling** to infrastructure (Milvus, LiteLLM, etc.)
- **Scattered timeline logic** across 4 different files
- **100-line nested callback** functions
- **Global singletons** and mutable state
- **Impossible to test** without full infrastructure
- **Mixed sync/async** with code duplication

### After (New Architecture) ✅
- **Modular pipeline** with ~60-line focused steps
- **Dependency injection** - no global singletons
- **Clean separation** of concerns (business logic vs. infrastructure)
- **Easy to test** - every component independently testable
- **Async-first** - consistent async/await throughout
- **Elastic scalability** - each step can scale independently

---

## Directory Structure

```
src/processors/knowledge_job/
├── README.md                                    # This file
├── feature_flags.py                             # Feature flags for gradual migration
├── container.py                                 # DI container
│
├── orchestration/                               # Orchestration layer
│   ├── __init__.py
│   ├── job_orchestrator.py                      # Main orchestrator (~200 lines)
│   ├── job_context.py                           # Shared execution context
│   └── cancellation_manager.py                  # Cancellation handling (~150 lines)
│
├── pipeline/                                    # Pipeline layer
│   ├── __init__.py
│   ├── base.py                                  # Base abstractions
│   ├── pipeline.py                              # Pipeline executor (~220 lines)
│   └── steps/                                   # Individual pipeline steps
│       ├── __init__.py
│       ├── extraction_step.py                   # Document extraction (~110 lines)
│       ├── chunking_step.py                     # Document chunking (~110 lines)
│       ├── embedding_step.py                    # Embedding generation (~120 lines)
│       ├── storage_step.py                      # Vector storage (~120 lines)
│       └── timeline_step.py                     # Timeline recording (~150 lines)
│
├── services/                                    # Domain services
│   ├── __init__.py
│   ├── embedding_service.py                     # Embedding abstraction (~200 lines)
│   └── vector_storage_service.py                # Vector storage abstraction (~150 lines)
│
├── adapters/                                    # Infrastructure adapters
│   ├── __init__.py
│   └── litellm_adapter.py                       # LiteLLM implementation (~120 lines)
│
├── refactored_knowledge_job_event_processor.py  # New event processor (~170 lines)
├── knowledge_job_event_processor.py             # OLD processor with routing (modified)
└── knowledge_job_processor.py                   # OLD processor (deprecated)
```

---

## Core Components

### 1. **JobOrchestrator**
[orchestration/job_orchestrator.py](orchestration/job_orchestrator.py)

The main coordinator that executes jobs through the pipeline.

```python
from src.processors.knowledge_job.container import create_job_orchestrator

# Create orchestrator
orchestrator = create_job_orchestrator()

# Execute job
results = await orchestrator.execute_job(
    knowledge_job=job,
    knowledge_source_config=config,
    status_callback=my_callback
)
```

**Responsibilities:**
- Creates execution context
- Manages pipeline execution
- Handles errors and cancellation
- Records timeline events

---

### 2. **JobPipeline**
[pipeline/pipeline.py](pipeline/pipeline.py)

Executes a sequence of steps, passing shared context through each step.

```python
from src.processors.knowledge_job.pipeline import JobPipeline
from src.processors.knowledge_job.pipeline.steps import *

pipeline = JobPipeline(
    steps=[
        DocumentExtractionStep(),
        DocumentChunkingStep(),
        EmbeddingGenerationStep(),
        VectorStorageStep(),
        TimelineRecordingStep(),
    ],
    cancellation_manager=cancellation_mgr,
    enable_rollback=False  # Optional rollback on failure
)

result = await pipeline.execute(context)
```

**Features:**
- Sequential step execution
- Shared context across steps
- Error handling and recovery
- Optional rollback support
- Cancellation support

---

### 3. **Pipeline Steps**
[pipeline/steps/](pipeline/steps/)

Each step is a focused, testable unit of work:

#### **DocumentExtractionStep**
Extracts documents from knowledge sources.

#### **DocumentChunkingStep**
Splits documents into chunks using configured splitter.

#### **EmbeddingGenerationStep**
Generates embeddings using the configured model provider.

#### **VectorStorageStep**
Stores chunks and embeddings in Milvus (or other vector DB).

#### **TimelineRecordingStep**
Records execution progress in the job timeline.

**All steps implement:**
```python
class PipelineStep(ABC):
    async def execute(self, context: JobContext) -> StepResult:
        """Execute the step"""

    async def validate(self, context: JobContext) -> bool:
        """Validate preconditions"""

    async def rollback(self, context: JobContext) -> None:
        """Rollback on failure (optional)"""
```

---

### 4. **Domain Services**
[services/](services/)

Abstract business logic from infrastructure:

#### **EmbeddingService**
```python
from src.processors.knowledge_job.services import ModelProviderEmbeddingService

embedding_service = ModelProviderEmbeddingService(
    provider_id="provider_123",
    model_name="text-embedding-ada-002",
    user_id="user_456"
)

vectors = await embedding_service.generate_embeddings(chunks)
```

#### **VectorStorageService**
```python
from src.processors.knowledge_job.services import MilvusVectorStorageService

storage_service = MilvusVectorStorageService(
    collection_name="my_collection",
    vector_dimension=1536
)

await storage_service.store_vectors(chunks, vectors)
```

---

### 5. **CancellationManager**
[orchestration/cancellation_manager.py](orchestration/cancellation_manager.py)

Centralized cancellation management:

```python
from src.processors.knowledge_job.orchestration import get_cancellation_manager

cancellation_mgr = get_cancellation_manager()

# Request cancellation
cancellation_mgr.request_cancellation(job_id, reason="User requested")

# Check if cancelled
if cancellation_mgr.is_cancelled(job_id):
    raise JobCancelledException(job_id)
```

**Features:**
- Thread-safe cancellation tracking
- Signal handling (SIGINT/SIGTERM)
- Per-job cancellation state

---

## Feature Flags for Migration

The new architecture includes feature flags for safe, gradual migration from old to new:

### Environment Variables

```bash
# Enable new architecture globally
export JOB_PROCESSING_USE_NEW_ARCHITECTURE=true

# Percentage-based rollout (0-100)
export JOB_PROCESSING_ROLLOUT_PERCENTAGE=10  # 10% of jobs

# Canary testing (specific job IDs)
export JOB_PROCESSING_CANARY_JOBS="job_123,job_456,job_789"

# Shadow mode (run both, compare results)
export JOB_PROCESSING_SHADOW_MODE=false
```

### Migration Strategy

**Phase 1: Canary (Week 1)**
```bash
# Test with specific jobs
export JOB_PROCESSING_CANARY_JOBS="test_job_1,test_job_2"
```

**Phase 2: Gradual Rollout (Week 2-3)**
```bash
# Start with 10%, increase gradually
export JOB_PROCESSING_ROLLOUT_PERCENTAGE=10  # Day 1
export JOB_PROCESSING_ROLLOUT_PERCENTAGE=25  # Day 3
export JOB_PROCESSING_ROLLOUT_PERCENTAGE=50  # Day 5
export JOB_PROCESSING_ROLLOUT_PERCENTAGE=75  # Day 7
```

**Phase 3: Full Migration (Week 4)**
```bash
# Enable for all jobs
export JOB_PROCESSING_USE_NEW_ARCHITECTURE=true
```

**Phase 4: Cleanup**
- Remove old processor code
- Remove feature flags
- Update documentation

---

## Usage Examples

### Basic Usage

```python
from src.processors.knowledge_job.container import create_job_orchestrator

# Create orchestrator
orchestrator = create_job_orchestrator()

# Execute job
results = await orchestrator.execute_job(
    knowledge_job=my_job,
    knowledge_source_config=my_config,
    status_callback=lambda msg, info: print(f"Status: {msg}")
)

print(f"Processed {results['total_documents']} documents")
print(f"Created {results['total_chunks']} chunks")
print(f"Took {results['processing_time_seconds']:.2f} seconds")
```

### Custom Pipeline

```python
from src.processors.knowledge_job.container import get_job_processing_container

container = get_job_processing_container()

# Create custom pipeline (only extraction and chunking)
pipeline = container.create_custom_pipeline([
    "extraction",
    "chunking"
])

result = await pipeline.execute(context)
```

### Testing Individual Steps

```python
from src.processors.knowledge_job.pipeline.steps import EmbeddingGenerationStep
from src.processors.knowledge_job.orchestration import JobContext
from unittest.mock import Mock

# Create mock embedding service
mock_embedding_service = Mock()
mock_embedding_service.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]

# Create step with mocked dependency
step = EmbeddingGenerationStep(embedding_service=mock_embedding_service)

# Create test context
context = JobContext(
    job=test_job,
    knowledge_source_config=test_config,
    user_id="test_user",
    chunks=[test_chunk]
)

# Execute step
result = await step.execute(context)

assert result.success
assert len(context.vectors) == 1
```

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Largest File** | 701 lines | ~220 lines |
| **Testability** | 🔴 Very Hard | 🟢 Easy |
| **Extensibility** | 🔴 Modify core | 🟢 Add steps |
| **Error Tracing** | 🔴 Nested try-catch | 🟢 Clear boundaries |
| **Cancellation** | 🟡 Global state | 🟢 Managed service |
| **Timeline** | 🔴 Scattered | 🟢 Event-driven |
| **Dependencies** | 🔴 Hard-coded | 🟢 Injected |
| **Scalability** | 🔴 Monolithic | 🟢 Elastic steps |

---

## Performance Considerations

### Old Architecture
- All steps run in single process
- Memory grows with job size
- Cannot scale individual components
- Cascading failures

### New Architecture
- Steps can run in separate workers
- Each step has bounded memory
- Scale expensive steps independently (embedding, storage)
- Isolated failures per step

### Deployment Options

**Option 1: Monolithic (Current)**
```yaml
# All steps in one process
job_processor:
  replicas: 3
```

**Option 2: Step-Based Services (Future)**
```yaml
# Each step as a service
extraction_service:
  replicas: 2

chunking_service:
  replicas: 3

embedding_service:
  replicas: 10  # Scale expensive embeddings

storage_service:
  replicas: 5
```

---

## Troubleshooting

### Check which architecture is being used

```python
from src.processors.knowledge_job.feature_flags import get_feature_flags

flags = get_feature_flags()
print(flags.get_config_summary())
```

### Force new architecture for specific job

```bash
export JOB_PROCESSING_CANARY_JOBS="your_job_id"
```

### Compare old vs new results (shadow mode)

```bash
export JOB_PROCESSING_SHADOW_MODE=true
```

This runs both architectures and logs comparison results.

---

## Migration Checklist

- [x] ✅ Implement new architecture
- [x] ✅ Add feature flags
- [x] ✅ Create DI container
- [x] ✅ Integrate with event listener
- [ ] ⏳ Test with canary jobs
- [ ] ⏳ Gradual rollout (10% → 50% → 100%)
- [ ] ⏳ Monitor metrics and errors
- [ ] ⏳ Remove old architecture
- [ ] ⏳ Update deployment scripts
- [ ] ⏳ Archive migration documentation

---

## Contributing

When adding new pipeline steps:

1. Create step in `pipeline/steps/`
2. Extend `PipelineStep` base class
3. Implement `execute()`, `validate()`, and optionally `rollback()`
4. Add to container in `container.py`
5. Add tests in `tests/processors/knowledge_job/`
6. Update this README

---

## Additional Resources

- **Old Architecture Analysis**: See `ANALYSIS_SUMMARY.txt` in project root
- **Migration Plan**: See `PIPELINE_IMPLEMENTATION_STATUS.md`
- **Design Patterns Used**:
  - Pipeline Pattern (Chain of Responsibility)
  - Strategy Pattern (Embedding/Storage services)
  - Dependency Injection
  - Event Sourcing (Timeline)
  - Feature Flags (Gradual migration)

---

## Questions?

For questions or issues with the new architecture:
1. Check the logs for routing decisions (old vs new)
2. Review feature flag configuration
3. Test with canary mode first
4. Open an issue with job_id and error traceback
