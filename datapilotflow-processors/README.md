# DataPilotFlow Processors

**Document Processing Layer - Text Splitting, Extraction, and Web Crawling**

The `datapilotflow-processors` package provides document processing capabilities including text extraction, chunking, web crawling, and file processing. It processes events from the events layer and orchestrates the knowledge ingestion pipeline.

## 📦 Package Overview

- **Version**: 1.0.0
- **Python**: >=3.11
- **Dependencies**: `datapilotflow-domain` + processing libraries
- **Purpose**: Document processing, text splitting, web crawling, and knowledge ingestion pipeline

## 🏗️ Architecture Position

```
┌─────────────────────────────────────────┐
│     Events Layer (Event Listeners)      │
└────────────────┬────────────────────────┘
                 │ triggers
┌────────────────▼────────────────────────┐
│   datapilotflow-processors             │
│   (Document Processing & Pipeline)      │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-services                │
│   (Business Logic)                       │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-infrastructure          │
│   (Database Access)                      │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│      datapilotflow-domain               │
│      (Foundation)                        │
└─────────────────────────────────────────┘
```

**This package provides**:
- Document extraction (PDF, HTML, web pages)
- Text splitting and chunking
- Web crawling
- Knowledge ingestion pipeline orchestration
- File upload processing

## 📁 Package Structure

```
datapilotflow-processors/
├── src/datapilotflow/processors/
│   ├── __init__.py
│   │
│   ├── knowledge_job/           # Knowledge job processing
│   │   ├── knowledge_job_processor.py
│   │   ├── knowledge_job_event_processor.py
│   │   ├── container.py
│   │   ├── feature_flags.py
│   │   │
│   │   ├── orchestration/        # Job orchestration
│   │   │   ├── job_orchestrator.py
│   │   │   ├── job_context.py
│   │   │   └── cancellation_manager.py
│   │   │
│   │   ├── pipeline/             # Pipeline steps
│   │   │   ├── pipeline.py
│   │   │   ├── pipeline_factory.py
│   │   │   └── steps/
│   │   │       ├── file_extraction_step.py
│   │   │       ├── extraction_step.py
│   │   │       ├── chunking_step.py
│   │   │       ├── embedding_step.py
│   │   │       ├── storage_step.py
│   │   │       └── timeline_step.py
│   │   │
│   │   └── services/             # Processing services
│   │       ├── document_extraction_service.py
│   │       ├── embedding_service.py
│   │       └── vector_storage_service.py
│   │
│   ├── file_upload/              # File upload processing
│   │   └── file_upload_processor.py
│   │
│   ├── document/                 # Document processing
│   │   ├── base_processor.py
│   │   ├── file_processor.py
│   │   └── web_document_processor.py
│   │
│   ├── crawler/                  # Web crawling
│   │   ├── crawler_processor.py
│   │   └── crawler_config.py
│   │
│   ├── splitters/                # Text splitting
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── text_splitter.py
│   │   ├── html_splitter.py
│   │   ├── markdown_splitter.py
│   │   └── token_counter.py
│   │
│   ├── storage/                  # Storage utilities
│   │   ├── file_writer.py
│   │   └── duplicate_detector.py
│   │
│   ├── notifications/             # Notification processing
│   │   └── notification_processor.py
│   │
│   └── utils/                     # Utilities
│       ├── chunk_manager.py
│       ├── json_utils.py
│       ├── resource_manager.py
│       └── url_loader.py
│
├── tests/
├── pyproject.toml
└── README.md
```

## 🔑 Key Components

### 1. Knowledge Job Processor

**KnowledgeJobProcessor**: Main orchestrator for knowledge ingestion jobs

**Pipeline Steps**:
1. **File Extraction**: Extract content from files
2. **Extraction**: Extract text from web pages/URLs
3. **Chunking**: Split documents into chunks
4. **Embedding**: Generate embeddings for chunks
5. **Storage**: Store vectors in Milvus
6. **Timeline**: Update job timeline

**Usage**:
```python
from datapilotflow.processors.knowledge_job import KnowledgeJobProcessor

processor = KnowledgeJobProcessor()

# Process knowledge job
await processor.process_job(
    job_id="job_123",
    source_id="source_456",
    config={...}
)
```

### 2. Document Processors

**FileProcessor**: Processes uploaded files (PDF, DOCX, etc.)
```python
from datapilotflow.processors.document import FileProcessor

processor = FileProcessor()

# Extract text from file
content = await processor.extract(file_path)
```

**WebDocumentProcessor**: Processes web pages
```python
from datapilotflow.processors.document import WebDocumentProcessor

processor = WebDocumentProcessor()

# Extract content from URL
content = await processor.extract(url)
```

### 3. Text Splitters

**TextSplitter**: Splits text into chunks
```python
from datapilotflow.processors.splitters import TextSplitter

splitter = TextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Split text
chunks = splitter.split_text(text)
```

**HTMLSplitter**: Splits HTML content
```python
from datapilotflow.processors.splitters import HTMLSplitter

splitter = HTMLSplitter()
chunks = splitter.split_html(html_content)
```

### 4. Web Crawler

**CrawlerProcessor**: Crawls websites
```python
from datapilotflow.processors.crawler import CrawlerProcessor

crawler = CrawlerProcessor()

# Crawl website
results = await crawler.crawl(
    urls=["https://example.com"],
    max_depth=3,
    config={...}
)
```

### 5. Pipeline Orchestration

**JobOrchestrator**: Orchestrates the knowledge ingestion pipeline
```python
from datapilotflow.processors.knowledge_job.orchestration import JobOrchestrator

orchestrator = JobOrchestrator()

# Execute pipeline
await orchestrator.execute_pipeline(
    job_id=job_id,
    pipeline_config={...}
)
```

## 🔗 How This Package Uses Lower Layers

### Uses Services
```python
from datapilotflow.services.knowledge import (
    KnowledgeJobService,
    KnowledgeIngestionService
)
from datapilotflow.services.events_publisher import JobEventPublisher

# Processors use services for business logic
job_service = KnowledgeJobService()
ingestion_service = KnowledgeIngestionService()
event_publisher = JobEventPublisher()
```

### Uses Infrastructure
```python
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper
from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO

# Processors use infrastructure for data access
vector_client = MilvusClientWrapper()
job_dao = KnowledgeJobDAO()
```

### Uses Domain
```python
from datapilotflow.domain.knowledge import KnowledgeJob, KnowledgeSource
from datapilotflow.domain.config import settings

# Processors work with domain models
job = KnowledgeJob(...)
chunk_size = settings.RAG_TOP_K
```

## 🔗 How Other Packages Use This Package

### Events Layer
```python
from datapilotflow.processors.knowledge_job import KnowledgeJobEventProcessor

# Event listeners trigger processors
processor = KnowledgeJobEventProcessor()

# Process job event
await processor.process_job_created_event(event_data)
```

### Services Layer
```python
from datapilotflow.processors.splitters import TextSplitter

# Services can use processors directly
splitter = TextSplitter()
chunks = splitter.split_text(text)
```

## 📦 Dependencies

### DataPilotFlow Dependencies
- `datapilotflow-domain>=1.0.0` - Domain models

### External Dependencies
- `langchain-core>=1.0.0` - LangChain integration
- `langchain-community>=0.3.0` - LangChain community tools
- `marker-pdf[full]` - PDF extraction
- `crawl4ai>=0.6.3` - Web crawling
- `html2text>=2025.4.15` - HTML to text conversion

## 🚀 Installation

```bash
cd datapilotflow-processors
pip install -e .
```

## 📝 Usage Examples

### Process Knowledge Job
```python
from datapilotflow.processors.knowledge_job import KnowledgeJobProcessor

processor = KnowledgeJobProcessor()

await processor.process_job(
    job_id="job_123",
    source_id="source_456",
    config={
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "top_k": 5
    }
)
```

### Split Text
```python
from datapilotflow.processors.splitters import TextSplitter

splitter = TextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_text(long_text)
```

### Extract from File
```python
from datapilotflow.processors.document import FileProcessor

processor = FileProcessor()
content = await processor.extract("/path/to/file.pdf")
```

## 🧪 Testing

```bash
cd datapilotflow-processors
pytest tests/
```

## 📚 Related Packages

**Depends on**:
- ✅ `datapilotflow-domain` - Uses domain models

**Used by**:
- ✅ `datapilotflow-events` - Triggers processors via events
- ✅ `datapilotflow-services` - Can use processors directly

## 🎯 Design Principles

1. **Event-Driven**: Processes events from event listeners
2. **Pipeline Pattern**: Modular pipeline steps
3. **Orchestration**: Coordinates multiple processing steps
4. **Async Processing**: All operations are async
5. **Error Handling**: Robust error handling and recovery

## 📖 Documentation

For more details:
- Knowledge Job Processing: See `src/datapilotflow/processors/knowledge_job/`
- Document Processing: See `src/datapilotflow/processors/document/`
- Text Splitting: See `src/datapilotflow/processors/splitters/`
- Web Crawling: See `src/datapilotflow/processors/crawler/`
