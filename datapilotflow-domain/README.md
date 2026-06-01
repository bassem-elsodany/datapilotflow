# datapilotflow-domain

**Foundation layer — core domain models, configuration, and shared utilities.**

This package is the base of the entire DataPilotFlow architecture. All other packages depend on it. It has zero dependencies on any other DataPilotFlow package.

---

## Responsibility

- Define all core Pydantic domain models shared across services
- Provide centralized application configuration via Pydantic Settings
- Define domain events used by the event-driven pipeline
- Provide shared logging setup for all services
- Define LLM prompt templates used by agent layers

---

## Package Structure

```
src/datapilotflow/domain/
├── config.py                      # Centralized application configuration
├── logging.py                     # Shared logging setup utility
├── core/
│   └── exceptions.py              # Base exception classes
├── agent/
│   └── models.py                  # Agent configuration and state models
├── conversation/
│   └── models.py                  # Conversation and message models
├── embedding/
│   └── embedding_model.py         # Embedding model definitions
├── generative/
│   └── generative_model.py        # Generative model definitions
├── knowledge/
│   ├── knowledge.py               # Knowledge base entity
│   ├── knowledge_job.py           # Ingestion job model
│   ├── knowledge_source_config.py # Source configuration (web, file, Confluence)
│   ├── job_timeline.py            # Job step timeline tracking
│   ├── document_splitter.py       # Document splitting configuration
│   ├── llm_content_filter_config.py # LLM content filter settings
│   └── vectordb_collection.py     # Vector DB collection model
├── model_provider/
│   └── model_provider.py          # LLM model provider definitions
├── notification/
│   └── notification.py            # Notification models
├── rag/
│   ├── knowledge_chunk.py         # Chunk model for retrieval
│   └── rag_file_upload.py         # File upload tracking model
├── tool/
│   └── models.py                  # Tool and MCP server models
├── user/
│   ├── user.py                    # User model
│   ├── role_model.py              # Role model
│   └── roles.py                   # System role definitions
├── vectordb/
│   └── collection_models.py       # Milvus collection schema models
├── events/
│   ├── base.py                    # Base event class
│   ├── job_events.py              # Job lifecycle events
│   ├── timeline_events.py         # Job timeline events
│   ├── confluence_events.py       # Confluence ingestion events
│   └── constants.py               # Event type constants and routing keys
└── llm_prompts/
    ├── base.py                    # Base prompt utilities
    ├── ai_responses.py            # Response formatting prompts
    ├── conversation.py            # Conversation prompts
    └── knowledge_base.py          # Knowledge retrieval prompts
```

---

## Key Modules

### Configuration (`config.py`)

Centralized settings using `pydantic-settings`. Reads from environment variables or a `.env` file. All services import from here.

```python
from datapilotflow.domain.config import settings

settings.API_SERVER_PORT      # int
settings.MONGO_HOST           # str
settings.VECTOR_DB_HOST       # str
settings.RABBITMQ_HOST        # str
settings.MCP_SERVER_PORT      # int
settings.JWT_SECRET_KEY       # str
settings.RAG_TOP_K            # int
```

### Logging (`logging.py`)

Call `setup_service_logging()` once at the top of each service entry point, before any other imports, to configure loguru for that service.

```python
from datapilotflow.domain.logging import setup_service_logging

setup_service_logging("api")
# Creates logs/api.log with daily rotation, 30-day retention, and zip compression
# Also writes to stderr at INFO level
```

### Domain Models

All models are pure Pydantic (`BaseModel`) with no external side effects.

```python
from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob
from datapilotflow.domain.knowledge.knowledge import Knowledge
from datapilotflow.domain.conversation.models import Conversation
from datapilotflow.domain.user.user import User
from datapilotflow.domain.rag.knowledge_chunk import KnowledgeChunk
from datapilotflow.domain.tool.models import MCPServer, Tool
```

### Events

```python
from datapilotflow.domain.events.job_events import JobCreatedEvent, JobCompletedEvent
from datapilotflow.domain.events.timeline_events import TimelineUpdateEvent
from datapilotflow.domain.events.constants import EventTypes, RoutingKeys
```

---

## Dependencies

```
pydantic >= 2.10.6
pydantic-settings >= 2.0.0
loguru >= 0.7.3
python-dateutil >= 2.8.2
email-validator >= 2.3.0
```

No dependencies on any other `datapilotflow-*` package.

---

## Installation

```bash
cd datapilotflow-domain
uv pip install -e .
```

---

## Dependency Position

All other packages in the stack import from this package. Nothing in this package imports from the rest of the stack.

```
datapilotflow-infrastructure  --|
datapilotflow-services        --|
datapilotflow-api             --|-->  datapilotflow-domain
datapilotflow-events          --|
datapilotflow-processors      --|
datapilotflow-rag-agent       --|
datapilotflow-assistant-agent --|
```
