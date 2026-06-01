# datapilotflow-processors

**Document processing pipeline — extraction, chunking, embedding, and vector storage.**

This package implements the full knowledge ingestion pipeline. It is invoked by event listeners and executes all the steps needed to turn raw source content into searchable vector embeddings stored in Milvus.

---

## Responsibility

- Extract text from files (PDF, Markdown, plain text) and web pages
- Crawl websites (single page, multiple pages, full website)
- Extract and convert Confluence spaces and pages
- Split documents into chunks using configurable strategies
- Generate vector embeddings for each chunk
- Store embeddings in Milvus and metadata in MongoDB
- Track job progress through a pipeline step system

---

## Package Structure

```
src/datapilotflow/processors/
├── knowledge_job/
│   ├── knowledge_job_processor.py             # Main entry point for job processing
│   ├── knowledge_job_event_processor.py        # Event-triggered processor wrapper
│   ├── refactored_knowledge_job_event_processor.py
│   ├── container.py                            # Dependency injection container
│   ├── feature_flags.py                        # Feature flag definitions
│   ├── orchestration/
│   │   ├── job_orchestrator.py                 # Orchestrates the full pipeline
│   │   ├── job_context.py                      # Shared job execution context
│   │   └── cancellation_manager.py             # Job cancellation handling
│   ├── pipeline/
│   │   ├── pipeline.py                         # Pipeline runner
│   │   ├── pipeline_factory.py                 # Builds pipeline from source type
│   │   ├── base.py                             # Base pipeline step interface
│   │   └── steps/
│   │       ├── extraction_step.py              # Source content extraction
│   │       ├── file_extraction_step.py         # File-specific extraction
│   │       ├── chunking_step.py                # Document splitting
│   │       ├── embedding_step.py               # Vector embedding generation
│   │       ├── storage_step.py                 # Milvus + MongoDB storage
│   │       └── timeline_step.py                # Job timeline update
│   └── services/
│       ├── document_extraction_service.py      # Extraction coordination
│       ├── embedding_service.py                # Embedding model calls
│       └── vector_storage_service.py           # Milvus write operations
├── document/
│   ├── base_processor.py                       # Abstract document processor
│   ├── file_processor.py                       # Local file processor (PDF, MD, TXT)
│   └── web_document_processor.py               # Web page processor
├── crawler/
│   ├── crawler_processor.py                    # Web crawling orchestration
│   └── crawler_config.py                       # Crawl4AI configuration
├── confluence/
│   ├── confluence_api_client.py                # Confluence REST API client
│   ├── confluence_document_extractor.py        # Space/page content extraction
│   └── confluence_markdown_converter.py        # HTML to Markdown conversion
├── splitters/
│   ├── factory.py                              # Splitter selection by content type
│   ├── base.py                                 # Abstract splitter interface
│   ├── markdown_splitter.py                    # Markdown-aware splitting
│   ├── html_splitter.py                        # HTML-aware splitting
│   ├── text_splitter.py                        # Plain text splitting
│   ├── splitters.py                            # Splitter registry
│   └── token_counter.py                        # Token counting utilities
├── file_upload/
│   └── file_upload_processor.py               # Direct file upload processing
├── notifications/
│   └── notification_processor.py              # Notification delivery processing
├── storage/
│   ├── duplicate_detector.py                  # Detects already-indexed chunks
│   └── file_writer.py                         # Output file writing
└── utils/
    ├── chunk_manager.py                        # Chunk batching and management
    ├── json_utils.py                           # JSON serialization helpers
    ├── resource_manager.py                     # Resource lifecycle management
    └── url_loader.py                           # URL content loading
```

---

## Pipeline Steps

Each ingestion job passes through these steps in sequence:

| Step | Description |
|------|-------------|
| Extraction | Fetch raw content from file, URL, or Confluence |
| Chunking | Split content into overlapping chunks |
| Embedding | Generate vector embeddings via configured model |
| Storage | Write vectors to Milvus, metadata to MongoDB |
| Timeline | Record step completion on the job timeline |

The `PipelineFactory` selects the correct pipeline variant based on the source type (`LOCAL_FILES`, `WEB_SCRAPING`, `CONFLUENCE`).

---

## Supported Source Types

| Type | Extractor | Notes |
|------|-----------|-------|
| Local files | `FileProcessor` | PDF (via marker-pdf), Markdown, plain text |
| Web scraping | `CrawlerProcessor` | Single page, multiple pages, full website via crawl4ai |
| Confluence | `ConfluenceDocumentExtractor` | Space pages converted to Markdown |

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
datapilotflow-infrastructure >= 1.0.0
langchain-core >= 1.0.0
langchain-community >= 0.3.0
marker-pdf[full]
crawl4ai >= 0.6.3
html2text >= 2025.4.15
huggingface-hub >= 0.34.0, < 1.0
tabulate >= 0.9.0
loguru >= 0.7.3
```

---

## Installation

```bash
cd datapilotflow-processors
uv pip install -e ../datapilotflow-domain -e ../datapilotflow-infrastructure -e .
```
