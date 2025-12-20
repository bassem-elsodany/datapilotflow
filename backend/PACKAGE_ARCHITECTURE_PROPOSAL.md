# DataPilotFlow Package Architecture Refactoring Proposal

## Executive Summary

Your current backend is a well-architected monolith with clear layering (Domain → Services → Infrastructure → API). The analysis identified **8 candidate packages** that can be extracted with minimal coupling. The proposed refactoring will create a modular, reusable package structure while maintaining a cohesive main application.

**Recommendation**: Implement a **phased approach** starting with core infrastructure packages (Domain, VectorDB, Persistence), then move to specialized packages (Knowledge, Agents, Events).

---

## Current State Analysis

### Architecture Overview
```
┌─────────────────────────────────────────┐
│          API Layer (15+ routers)        │
│  Agents | Knowledge | Conversation etc. │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│        Services Layer (20+ services)    │
│  Knowledge | Agent | Conversation etc.  │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Infrastructure Layer                 │
│  MongoDB | Milvus | RabbitMQ | DAOs     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Domain Layer (Pure Models)         │
│  Pydantic models, no framework deps     │
└─────────────────────────────────────────┘
```

### Key Metrics
- **271 Python files** across 172 directories
- **60+ external dependencies** in one monolith
- **9 entry points** (1 API + 8 event listeners/services)
- **Clean layered architecture** with minimal cross-layer violations
- **Event-driven** with RabbitMQ message broker

---

## Proposed Package Structure

### Package Hierarchy (8 Packages)

```
datapilotflow/                          (Meta package/orchestrator)
├── datapilotflow-domain/               (Shared models)
├── datapilotflow-persistence/          (MongoDB DAOs)
├── datapilotflow-vectordb/             (Milvus vector DB)
├── datapilotflow-processors/           (Document processing)
├── datapilotflow-knowledge/            (Ingestion & retrieval)
├── datapilotflow-agents/               (LangGraph agents)
├── datapilotflow-events/               (RabbitMQ event system)
└── datapilotflow-api/                  (REST/WebSocket API)
```

### Package Details

#### 1. **datapilotflow-domain** (Foundation - No Dependencies)
**Purpose**: Shared data models and interfaces

**Contents**:
```
domain/
├── agent/                   # Agent configurations
├── conversation/            # Message & conversation models
├── knowledge/              # Document, chunk, timeline models
├── embedding/              # Embedding models
├── generative/             # LLM configurations
├── model_provider/         # Provider abstractions
├── rag/                    # RAG-specific models
├── vectordb/               # Vector DB collection models
├── user/                   # User, roles, permissions
├── tool/                   # Tool definitions
├── notification/           # Notification models
├── events/                 # Event definitions
├── llm_prompts/            # Prompt templates
└── core/                   # Exceptions, base classes
```

**Dependencies**:
- `pydantic` (data validation)
- `python-dateutil` (date handling)

**Status**: ✅ Ready to extract immediately
**Benefits**:
- Can be reused in frontend, CLI, data pipelines
- Separate versioning from implementation
- Clear contract between services

---

#### 2. **datapilotflow-persistence** (Data Layer)
**Purpose**: MongoDB abstraction and data access objects

**Contents**:
```
persistence/
├── mongo/
│   ├── client.py           # MongoClientWrapper[T] generic wrapper
│   └── indexes.py          # Index definitions
├── dao/
│   ├── base.py             # Base DAO class
│   ├── conversation_dao.py
│   ├── knowledge_dao.py
│   ├── job_dao.py
│   ├── user_dao.py
│   └── ... (all other DAOs)
├── utils/
│   └── query_builders.py
└── migrations/
    └── (schema migrations, indexes)
```

**Dependencies**:
- `datapilotflow-domain`
- `pymongo>=4.9.2`
- `pydantic>=2.10.6`

**Status**: ✅ Ready to extract (minimal external coupling)
**Benefits**:
- Easy to swap MongoDB with PostgreSQL/other DB
- Generic `MongoClientWrapper[T]` is reusable
- Clear data access layer

---

#### 3. **datapilotflow-vectordb** (Vector Storage Layer)
**Purpose**: Milvus vector database abstraction

**Contents**:
```
vectordb/
├── milvus/
│   ├── client.py           # MilvusClientWrapper[T]
│   ├── utils.py            # Milvus utilities
│   └── examples.py         # Example usage
├── processor/
│   └── milvus_processor.py # Milvus-specific processing
├── schemas/
│   └── collection_schemas.py
└── utils/
    └── embedding_utils.py
```

**Dependencies**:
- `datapilotflow-domain`
- `pymilvus>=2.4.0`
- `sentence-transformers>=4.1.0` (for embeddings)

**Status**: ✅ Ready to extract
**Benefits**:
- Generic `MilvusClientWrapper[T]` for any embedding use case
- Easy to add other vector DBs (Weaviate, Pinecone, etc.)
- Independent of knowledge ingestion logic

---

#### 4. **datapilotflow-processors** (Document Processing)
**Purpose**: File/document processing and text splitting

**Contents**:
```
processors/
├── document/
│   ├── base_processor.py
│   ├── file_processor.py
│   ├── web_document_processor.py
│   └── processor_factory.py
├── splitters/
│   ├── factory.py
│   ├── base.py
│   ├── text_splitter.py
│   ├── markdown_splitter.py
│   ├── html_splitter.py
│   └── token_counter.py
├── crawler/
│   ├── crawler_processor.py
│   └── crawler_config.py
├── extractors/
│   ├── pdf_extractor.py
│   ├── text_extractor.py
│   └── html_extractor.py
└── utils/
    └── text_utils.py
```

**Dependencies**:
- `datapilotflow-domain`
- `langchain-core>=1.0.0`
- `langchain-community>=0.3.0`
- `marker-pdf[full]`
- `crawl4ai>=0.6.3`
- `html2text>=2025.4.15`

**Status**: ✅ Ready to extract (no services, no infrastructure coupling)
**Benefits**:
- Can be used standalone for document processing
- Clear processor abstraction
- Easy to add new document types

---

#### 5. **datapilotflow-knowledge** (Knowledge Management)
**Purpose**: Knowledge ingestion, retrieval, and job orchestration

**Contents**:
```
knowledge/
├── ingestion/
│   └── knowledge_ingestion_service.py
├── retrieval/
│   ├── knowledge_retrieval_service.py
│   └── retrieval_strategies.py
├── jobs/
│   ├── knowledge_job_service.py
│   ├── knowledge_job_processor.py
│   ├── knowledge_job_event_processor.py
│   ├── container.py         # DI container
│   ├── feature_flags.py
│   ├── orchestration/       # Job orchestration
│   │   ├── job_orchestrator.py
│   │   ├── job_context.py
│   │   └── cancellation_manager.py
│   └── pipeline/            # Pipeline orchestration
│       ├── pipeline.py
│       ├── pipeline_factory.py
│       └── steps/
│           ├── file_extraction_step.py
│           ├── extraction_step.py
│           ├── chunking_step.py
│           ├── embedding_step.py
│           ├── storage_step.py
│           └── timeline_step.py
├── sources/
│   └── knowledge_source_service.py
├── collections/
│   └── vectordb_collection_service.py
├── services/
│   ├── document_extraction_service.py
│   ├── embedding_service.py
│   └── vector_storage_service.py
└── dao/
    ├── knowledge_dao.py
    ├── job_dao.py
    └── ... (knowledge-related DAOs)
```

**Dependencies**:
- `datapilotflow-domain`
- `datapilotflow-persistence`
- `datapilotflow-vectordb`
- `datapilotflow-processors`
- `datapilotflow-events` (publishes job events)
- `langchain-core>=1.0.0`
- `sentence-transformers>=4.1.0`

**Status**: ⚠️ Moderate complexity (orchestrates multiple services)
**Benefits**:
- Encapsulates all knowledge ingestion logic
- Event-driven job processing
- Reusable in different API contexts

---

#### 6. **datapilotflow-agents** (AI Agents)
**Purpose**: LangGraph-based AI agents (RAG and Supervisor)

**Contents**:
```
agents/
├── common/
│   ├── agent_interface.py
│   ├── agent_state.py
│   ├── base_prompt.py
│   └── prompts/
├── rag/
│   ├── agent.py             # RAGAgentService
│   ├── graph.py             # LangGraph workflow
│   ├── state.py
│   ├── chains/              # RAG chains
│   ├── nodes/               # Graph nodes
│   ├── prompts/
│   ├── retrieval/           # Retrieval strategies
│   ├── tools/
│   ├── services/
│   └── mcp/                 # MCP integration
│       ├── server.py
│       └── tools.py
└── assistant/
    ├── factory.py           # DeepAgents factory
    ├── response_handler.py
    └── __init__.py
```

**Dependencies**:
- `datapilotflow-domain`
- `datapilotflow-knowledge`
- `langgraph>=1.0.2`
- `langchain-core>=1.0.0`
- `langchain-mcp-adapters>=0.1.0`
- `deepagents>=0.1.0`
- `litellm>=1.79.0`

**Status**: ⚠️ Moderate complexity (LangGraph integration)
**Benefits**:
- Encapsulates AI logic
- Can be tested independently
- Support for multiple agent strategies

---

#### 7. **datapilotflow-events** (Event System)
**Purpose**: RabbitMQ-based event publishing and listening

**Contents**:
```
events/
├── broker/
│   ├── rabbit_mq_broker.py  # RabbitMQ config
│   ├── event_serializer.py
│   └── connection_pool.py
├── publishers/
│   ├── base_publisher.py
│   ├── job_event_publisher.py
│   ├── file_upload_publisher.py
│   └── notification_publisher.py
├── listeners/
│   ├── base_listener.py
│   ├── job_event_listener.py
│   ├── file_upload_listener.py
│   └── notification_listener.py
├── schemas/
│   └── event_schemas.py
└── utils/
    └── event_utils.py
```

**Dependencies**:
- `datapilotflow-domain`
- `aio-pika>=9.5.5`
- `pydantic>=2.10.6`

**Status**: ✅ Ready to extract (minimal dependencies)
**Benefits**:
- Clear event abstraction
- Easy to swap RabbitMQ with other brokers
- Decouples services via events

---

#### 8. **datapilotflow-api** (REST/WebSocket API)
**Purpose**: FastAPI routers and HTTP/WebSocket endpoints

**Contents**:
```
api/
├── app.py                   # FastAPI setup
├── constants.py
├── routers/
│   ├── agent/
│   │   ├── agent_router.py
│   │   ├── assistant_websocket_router.py
│   │   └── rag_websocket_router.py
│   ├── knowledge/           # Knowledge endpoints
│   ├── conversation/        # Conversation endpoints
│   ├── auth/               # Auth endpoints
│   ├── model_provider/     # Model provider endpoints
│   ├── users/              # User endpoints
│   ├── tools/              # Tools endpoints
│   ├── notifications/      # Notification endpoints
│   ├── vectordb/           # Vector DB endpoints
│   └── health/             # Health check endpoints
├── middleware/
│   ├── auth.py
│   ├── error_handling.py
│   └── logging.py
├── dependencies/
│   ├── auth.py
│   └── services.py         # Service injection
└── utils/
    └── response_models.py
```

**Dependencies**:
- All previous packages
- `fastapi[standard]>=0.115.8`
- `uvicorn`

**Status**: ⚠️ Core orchestration (depends on all packages)
**Benefits**:
- Clean separation of HTTP concerns
- Easy to add new endpoints
- Decoupled from business logic

---

## Dependency Graph

```
datapilotflow-domain
    ↑
    ├─── datapilotflow-persistence
    ├─── datapilotflow-vectordb
    ├─── datapilotflow-processors
    ├─── datapilotflow-events
    │
    ├─── datapilotflow-knowledge
    │        ├─ persistence
    │        ├─ vectordb
    │        ├─ processors
    │        └─ events
    │
    ├─── datapilotflow-agents
    │        ├─ knowledge
    │        └─ (other services)
    │
    └─── datapilotflow-api (orchestrator)
             ├─ knowledge
             ├─ agents
             ├─ events
             └─ (all services)
```

**Dependency Flow Direction**: Lower layers ← Upper layers (Acyclic)

---

## Migration Strategy

### Phase 1: Foundation Packages (Week 1-2)
Extract minimal-dependency packages first:

1. **datapilotflow-domain** ✅
   - Pure Pydantic models
   - No external dependencies beyond pydantic
   - Publish to PyPI (or private registry)

2. **datapilotflow-persistence** ✅
   - Depends only on domain + pymongo
   - MongoDB DAOs & MongoClientWrapper
   - Tests with test database

3. **datapilotflow-vectordb** ✅
   - Depends only on domain + pymilvus
   - MilvusClientWrapper[T]
   - Tests with test Milvus instance

### Phase 2: Utility Packages (Week 2-3)
Extract specialized utilities:

4. **datapilotflow-processors** ✅
   - Document processing
   - Text splitting
   - No service dependencies

5. **datapilotflow-events** ✅
   - RabbitMQ abstraction
   - Event schemas & interfaces
   - Tests with RabbitMQ container

### Phase 3: Business Logic Packages (Week 3-4)
Extract complex services:

6. **datapilotflow-knowledge** ⚠️
   - Knowledge ingestion & retrieval
   - Job orchestration
   - Pipeline execution
   - Coordinate with phases 1-2

7. **datapilotflow-agents** ⚠️
   - RAG & Assistant agents
   - LangGraph workflows
   - Coordinate with knowledge package

### Phase 4: Integration (Week 4-5)
8. **datapilotflow-api** ⚠️
   - REST/WebSocket routers
   - Orchestrates all packages
   - Runs as main application

---

## Implementation Roadmap

### Step 1: Create Repository Structure
```bash
# Create new package repositories (or monorepo with subdirectories)
datapilotflow-domain/
  ├── src/datapilotflow/domain/
  ├── tests/
  ├── pyproject.toml
  └── README.md

datapilotflow-persistence/
  ├── src/datapilotflow/persistence/
  ├── tests/
  ├── pyproject.toml
  └── README.md

# ... (repeat for other packages)
```

### Step 2: Extract Each Package
For each package:
1. Create new `pyproject.toml` with explicit dependencies
2. Move source files to package directory
3. Update all imports to use new package namespace
4. Create tests for package
5. Publish package (PyPI or private registry)
6. Update main app to import from package

### Step 3: Update Main Application
Update `datapilotflow-backend`:
```python
# Before
from src.domain.agent import Agent
from src.services.knowledge import KnowledgeService

# After
from datapilotflow.domain import Agent
from datapilotflow.knowledge import KnowledgeService
```

### Step 4: Create Integration Tests
- Test package imports
- Test cross-package communication
- Test event flows
- Test end-to-end workflows

---

## Technical Considerations

### Import Strategy
```python
# Each package should have clean __init__.py exports
# datapilotflow-domain/__init__.py
from .agent import Agent
from .conversation import Conversation
from .knowledge import Document, Chunk
```

### Version Management
```
datapilotflow-domain: 1.0.0
datapilotflow-persistence: 1.0.0 (depends on datapilotflow-domain==1.0.0)
datapilotflow-api: 1.0.0 (depends on all others)
```

### Shared Configuration
- Move common config to `src/config.py` (shared across packages)
- Environment variables for service endpoints (Mongo URL, Milvus URL, RabbitMQ URL)
- Logging configuration (shared via datapilotflow-domain?)

### Testing Strategy
- Unit tests for each package (mock dependencies)
- Integration tests for cross-package communication
- End-to-end tests in main API package

---

## Benefits of This Architecture

### Immediate Benefits
1. **Reusability**: Domain models and utilities in other projects
2. **Clear Separation**: Each team can own a package
3. **Independent Versioning**: Update packages independently
4. **Dependency Clarity**: Explicit imports show what each package needs
5. **Testing**: Easier to test in isolation

### Long-term Benefits
1. **Microservices Ready**: Deploy packages independently if needed
2. **Scalability**: Easy to scale specific services
3. **Flexibility**: Swap implementations (MongoDB → PostgreSQL, Milvus → Weaviate)
4. **Maintainability**: Smaller, focused packages are easier to understand
5. **Onboarding**: New developers learn packages incrementally

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| **Circular dependencies** | Clear dependency graph enforced via imports |
| **Shared config drift** | Centralized config management, shared env vars |
| **Breaking changes** | Semantic versioning, deprecation warnings |
| **Integration complexity** | Comprehensive integration tests |
| **Package discovery** | Well-documented README in each package |

---

## Alternative Architectures Considered

### Option A: Monorepo with Workspaces (Current Recommendation)
```
datapilotflow/
├── packages/
│   ├── domain/
│   ├── persistence/
│   ├── vectordb/
│   ├── knowledge/
│   ├── agents/
│   ├── events/
│   ├── api/
│   └── processors/
└── workspace config (pnpm, npm, poetry)
```
**Pros**: Single repo, coordinated development
**Cons**: Need workspace tooling

### Option B: Multiple Repositories
Separate GitHub repos for each package
**Pros**: Clear separation
**Cons**: Harder to coordinate changes

### Option C: Hybrid (Recommended for Now)
Keep monorepo for development, extract to separate repos for distribution
**Pros**: Best of both worlds
**Cons**: Need CI/CD for packaging

---

## Next Steps

### For User Approval:
1. ✅ Review this proposal
2. ✅ Confirm package boundaries
3. ✅ Decide on deployment strategy (monorepo vs. multi-repo)
4. ✅ Define version management strategy
5. ✅ Set timeline for migration

### Once Approved:
1. Create feature branch `feat/package-refactoring`
2. Create new package structure
3. Extract Phase 1 packages
4. Create tests for each package
5. Update main app imports
6. Integrate and test end-to-end

---

## Questions for You

1. **Monorepo vs. Multi-Repo**: Prefer keeping packages in one repo or separate?
2. **Package Publishing**: PyPI, private registry (GitHub Packages, Artifactory), or internal only?
3. **Timeline**: Priority on extracting which packages first?
4. **Shared Services**: Should config, logging, auth be in domain or separate?
5. **API Routes**: Keep all routers in main API package or split by domain?
