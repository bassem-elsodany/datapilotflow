# Local Files Pipeline - Quick Reference

## File Type → Processing Strategy

| File Type | Processing Method | Skip Crawling? |
|-----------|------------------|----------------|
| `.md` | Direct read | ✅ Yes - already markdown |
| `.pdf` | `FileProcessor.extract_markdown()` | ✅ Yes - convert to markdown |
| `.docx` | `FileProcessor.extract_markdown()` | ✅ Yes - convert to markdown |
| `.txt` | `FileProcessor.extract_markdown()` | ✅ Yes - convert to markdown |
| `.html` | `crawler.arun(url=file://)` | ❌ No - crawl local file |

## Pipeline Steps

### Local Files Pipeline
```
FileExtractionStep → Chunking → Embedding → Storage → Timeline
```

### Web Scraping Pipeline
```
DocumentExtractionStep → Chunking → Embedding → Storage → Timeline
```

## How It Works

### 1. Configuration Determines Pipeline

```python
# Local files → FileExtractionStep
config = KnowledgeSourceConfig(
    content_source_type=ContentSourceType.LOCAL_FILES,
    scraping_mode=ScrapingMode.PDF_FILES,
    local_files=[...]
)

# Web scraping → DocumentExtractionStep
config = KnowledgeSourceConfig(
    content_source_type=ContentSourceType.WEB_SCRAPING,
    scraping_mode=ScrapingMode.SINGLE_PAGE,
    url="https://..."
)
```

### 2. Factory Creates Pipeline

```python
# In container.py
steps = create_pipeline_steps_for_config(knowledge_source_config)
```

### 3. Orchestrator Executes

```python
# In refactored_knowledge_job_event_processor.py
orchestrator = create_job_orchestrator(
    knowledge_source_config=knowledge_source_config
)
```

## Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `FileExtractionStep` | `pipeline/steps/file_extraction_step.py` | Extracts documents from local files |
| `PipelineFactory` | `pipeline/pipeline_factory.py` | Creates pipelines based on config |
| `JobProcessingContainer` | `container.py` | Dependency injection container |

## ScrapingMode Enum

### Local Files Modes
- `ScrapingMode.MARKDOWN_FILES`
- `ScrapingMode.PDF_FILES`
- `ScrapingMode.DOCX_FILES`
- `ScrapingMode.TXT_FILES`
- `ScrapingMode.HTML_FILES`

### Web Scraping Modes
- `ScrapingMode.SINGLE_PAGE`
- `ScrapingMode.MULTIPLE_PAGES`
- `ScrapingMode.WEBSITE`

## Testing

```bash
# Test pipeline factory
source .venv/bin/activate
python -c "
from src.domain.knowledge.knowledge_source_config import *
from src.processors.knowledge_job.pipeline.pipeline_factory import *

config = KnowledgeSourceConfig(
    id='test',
    user_id='test',
    name='Test',
    content_source_type=ContentSourceType.LOCAL_FILES,
    scraping_mode=ScrapingMode.PDF_FILES,
    local_files=[],
    created_by='test',
    updated_by='test'
)

step = PipelineFactory.create_extraction_step(config)
print(f'{step.name} ({type(step).__name__})')
# Output: FileExtraction (FileExtractionStep)
"
```

## Common Operations

### Add New File Type

1. Add to `ScrapingMode` enum in `knowledge_source_config.py`
2. Add case in `FileExtractionStep._extract_files()`
3. Implement extraction method (e.g., `_extract_xyz_files()`)

### Debug Pipeline Selection

Check logs for:
```
Creating FileExtractionStep for local files (mode: ...)
Creating DocumentExtractionStep for web scraping (mode: ...)
```

### Verify Extraction Method

Check document metadata after extraction:
```python
doc.metadata["extraction_method"]
# Returns: "direct_read", "file_processor", "crawler", etc.
```

## Architecture Flow

```
Job Event
    ↓
RefactoredKnowledgeJobEventProcessor
    ↓
create_job_orchestrator(knowledge_source_config)
    ↓
PipelineFactory.create_pipeline_steps(knowledge_source_config)
    ↓
PipelineFactory.create_extraction_step(knowledge_source_config)
    ↓
FileExtractionStep OR DocumentExtractionStep
```

## File Locations

```
backend/
├── src/processors/knowledge_job/
│   ├── pipeline/
│   │   ├── steps/
│   │   │   ├── file_extraction_step.py     ← NEW
│   │   │   ├── extraction_step.py          (existing)
│   │   ├── pipeline_factory.py             ← NEW
│   ├── container.py                         (modified)
│   ├── refactored_knowledge_job_event_processor.py  (modified)
```

## Quick Debug Commands

```bash
# Check file syntax
python -m py_compile src/processors/knowledge_job/pipeline/steps/file_extraction_step.py

# Test imports
python -c "from src.processors.knowledge_job.pipeline.steps.file_extraction_step import FileExtractionStep"

# Test factory
python -c "from src.processors.knowledge_job.pipeline.pipeline_factory import PipelineFactory"
```
