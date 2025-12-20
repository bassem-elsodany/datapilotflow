# RAG MCP Standalone Project Architecture

## Executive Summary

**RAG MCP as a standalone, distributable service** - Perfect for supporting multiple retrieval consumers (supervisor agents, external applications, etc.).

Your revised architecture becomes **5 independent projects**:

```
1. datapilotflow-common       (Shared foundation)
2. datapilotflow-ingestion    (Knowledge ingestion pipeline)
3. datapilotflow-rag-mcp      (Standalone RAG retrieval service - NEW!)
4. datapilotflow-agents       (Supervisor & other agents)
5. datapilotflow-api          (Main REST/WebSocket API)
```

---

## Project Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         External Consumers (Supervisor Agents)      │
│              Other RAG Applications                  │
└────────────────────┬────────────────────────────────┘
                     │ (HTTP/MCP Protocol)
                     │
        ┌────────────▼──────────────┐
        │  datapilotflow-rag-mcp    │ ⭐ STANDALONE SERVICE
        │  (Distributed Package)     │
        │  - Runs independently      │
        │  - HTTP MCP Server on 65510│
        │  - Docker container ready  │
        └────┬──────────────────────┘
             │ (Depends on Common)
             │
┌────────────▼───────────────────────────────────────┐
│         datapilotflow-common                        │
│  (Domain, Persistence, VectorDB, Events)           │
└─────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│      datapilotflow-ingestion                         │
│  (Knowledge jobs, pipelines, processors)             │
│      ↓ depends on Common                             │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│      datapilotflow-agents                            │
│  (Supervisor, tools, orchestration)                  │
│      ↓ depends on Common + RAG MCP                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│      datapilotflow-api                               │
│  (REST/WebSocket API - main entry point)             │
│      ↓ depends on all above                          │
└──────────────────────────────────────────────────────┘
```

---

## Project 1: datapilotflow-common

**Purpose**: Shared foundation for all other projects

**Contents**:
```
datapilotflow-common/
├── src/datapilotflow/
│   ├── domain/
│   │   ├── agent/
│   │   ├── conversation/
│   │   ├── knowledge/
│   │   ├── embedding/
│   │   ├── generative/
│   │   ├── model_provider/
│   │   ├── rag/
│   │   ├── vectordb/
│   │   ├── user/
│   │   ├── tool/
│   │   ├── notification/
│   │   ├── events/
│   │   ├── llm_prompts/
│   │   └── core/
│   ├── persistence/
│   │   ├── mongo/
│   │   │   ├── client.py
│   │   │   └── indexes.py
│   │   └── dao/
│   │       ├── base.py
│   │       ├── conversation_dao.py
│   │       ├── knowledge_dao.py
│   │       ├── job_dao.py
│   │       ├── user_dao.py
│   │       └── ... (all DAOs)
│   ├── vectordb/
│   │   ├── milvus/
│   │   │   ├── client.py
│   │   │   └── utils.py
│   │   ├── processor/
│   │   └── schemas/
│   ├── processors/
│   │   ├── document/
│   │   ├── splitters/
│   │   ├── crawler/
│   │   └── extractors/
│   ├── events/
│   │   ├── broker/
│   │   ├── publishers/
│   │   ├── listeners/
│   │   └── schemas/
│   ├── config.py
│   └── __init__.py
├── tests/
├── pyproject.toml
└── README.md
```

**Dependencies**:
- `pydantic>=2.10.6`
- `pymongo>=4.9.2`
- `pymilvus>=2.4.0`
- `langchain-core>=1.0.0`
- `aio-pika>=9.5.5`
- `sentence-transformers>=4.1.0`
- `marker-pdf[full]`
- `crawl4ai>=0.6.3`

**Status**: ✅ Foundation for all projects

---

## Project 2: datapilotflow-rag-mcp ⭐ (STANDALONE)

**Purpose**: Standalone RAG retrieval service consumed by external applications

**Key Feature**: Can run independently as a microservice

**Contents**:
```
datapilotflow-rag-mcp/
├── src/datapilotflow/rag_mcp/
│   ├── server.py              # FastMCP server definition
│   ├── mcp_server_runner.py   # Entry point (replaces run_rag_mcp_server.py)
│   ├── tools.py               # MCP tool definitions
│   ├── agent/
│   │   ├── graph.py           # RAG workflow (LangGraph)
│   │   ├── state.py           # RAG state management
│   │   ├── chains/            # RAG chains
│   │   ├── nodes/             # Graph nodes
│   │   ├── prompts/           # RAG prompts
│   │   ├── retrieval/         # Retrieval strategies
│   │   └── services/          # RAG services
│   ├── config.py              # RAG MCP specific config
│   └── __init__.py
├── tests/
├── Dockerfile                 # Standalone container
├── docker-compose.yml         # Dev environment
├── pyproject.toml
└── README.md
```

**Dependencies**:
```
[project]
name = "datapilotflow-rag-mcp"
version = "1.0.0"
dependencies = [
    "datapilotflow-common>=1.0.0",
    "langgraph>=1.0.2",
    "langchain-core>=1.0.0",
    "fastmcp>=0.4.0",
    "litellm>=1.79.0",
    "opik>=1.9.11",
]
```

**Entry Points**:
```
[project.scripts]
rag-mcp-server = "datapilotflow.rag_mcp.mcp_server_runner:run"
```

**Docker Setup**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install .

# Expose MCP port
EXPOSE 65510

# Run RAG MCP server
CMD ["rag-mcp-server"]
```

**Status**: ✅ Ready to extract as standalone project

**Benefits**:
1. **Independent Deployment**: Docker image, separate versioning
2. **Horizontal Scaling**: Run multiple instances for high-traffic scenarios
3. **Consumer Flexibility**: Any MCP client can use it (supervisor agents, external apps)
4. **Clear Interface**: HTTP MCP protocol
5. **Monitoring**: Separate logs, metrics for retrieval service
6. **Cache/CDN Ready**: Could add caching layer in front

---

## Project 3: datapilotflow-ingestion

**Purpose**: Knowledge base ingestion and pipeline processing

**Contents**:
```
datapilotflow-ingestion/
├── src/datapilotflow/ingestion/
│   ├── services/
│   │   ├── knowledge_ingestion_service.py
│   │   ├── knowledge_job_service.py
│   │   ├── knowledge_source_service.py
│   │   ├── vectordb_collection_service.py
│   │   ├── document_extraction_service.py
│   │   ├── embedding_service.py
│   │   └── vector_storage_service.py
│   ├── processors/
│   │   ├── knowledge_job_processor.py
│   │   ├── knowledge_job_event_processor.py
│   │   ├── job_orchestration/
│   │   ├── pipeline/
│   │   │   ├── pipeline.py
│   │   │   ├── pipeline_factory.py
│   │   │   └── steps/
│   │   │       ├── file_extraction_step.py
│   │   │       ├── extraction_step.py
│   │   │       ├── chunking_step.py
│   │   │       ├── embedding_step.py
│   │   │       ├── storage_step.py
│   │   │       └── timeline_step.py
│   │   └── file_upload_processor.py
│   ├── dao/
│   │   ├── knowledge_dao.py
│   │   ├── job_dao.py
│   │   └── timeline_dao.py
│   ├── config.py
│   └── __init__.py
├── tests/
├── pyproject.toml
└── README.md
```

**Dependencies**:
```
dependencies = [
    "datapilotflow-common>=1.0.0",
    "langchain-core>=1.0.0",
    "sentence-transformers>=4.1.0",
]
```

**Status**: ⚠️ Moderate complexity

---

## Project 4: datapilotflow-agents

**Purpose**: Supervisor and orchestration agents

**Contents**:
```
datapilotflow-agents/
├── src/datapilotflow/agents/
│   ├── supervisor/
│   │   ├── agent.py           # Supervisor agent
│   │   ├── factory.py         # DeepAgents factory
│   │   ├── response_handler.py
│   │   └── state.py
│   ├── common/
│   │   ├── agent_interface.py
│   │   ├── base_prompt.py
│   │   └── prompts/
│   ├── tools/
│   │   ├── rag_mcp_tool.py     # Tool that calls RAG MCP
│   │   ├── retrieval_tools.py
│   │   └── tool_registry.py
│   ├── config.py
│   └── __init__.py
├── tests/
├── pyproject.toml
└── README.md
```

**Key Point**: Supervisor agents call RAG MCP via HTTP
```python
# In datapilotflow-agents
from datapilotflow.agents.tools import RAGMCPTool

rag_tool = RAGMCPTool(
    rag_mcp_url="http://localhost:65510"  # or env var
)

# Supervisor uses this tool to retrieve documents
```

**Dependencies**:
```
dependencies = [
    "datapilotflow-common>=1.0.0",
    "datapilotflow-ingestion>=1.0.0",
    "deepagents>=0.1.0",
    "langgraph>=1.0.2",
    "langchain-core>=1.0.0",
    "litellm>=1.79.0",
    "httpx",  # To call RAG MCP server
]
```

**Status**: ⚠️ Moderate complexity

---

## Project 5: datapilotflow-api

**Purpose**: Main REST/WebSocket API orchestrating all services

**Contents**:
```
datapilotflow-api/
├── src/datapilotflow/api/
│   ├── app.py                 # FastAPI setup
│   ├── routers/
│   │   ├── agent/
│   │   ├── knowledge/
│   │   ├── conversation/
│   │   ├── auth/
│   │   ├── model_provider/
│   │   ├── users/
│   │   ├── tools/
│   │   ├── notifications/
│   │   ├── vectordb/
│   │   └── health/
│   ├── middleware/
│   ├── dependencies/
│   ├── config.py
│   └── __init__.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

**Dependencies**:
```
dependencies = [
    "datapilotflow-common>=1.0.0",
    "datapilotflow-ingestion>=1.0.0",
    "datapilotflow-agents>=1.0.0",
    "fastapi[standard]>=0.115.8",
    "uvicorn",
]
```

**Status**: ⚠️ Core orchestration

---

## Communication Between Projects

### Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│ datapilotflow-api (Main App)                         │
│  REST/WebSocket on port 65500                        │
│                                                      │
│  ├─ /api/agents (Agent CRUD)                        │
│  ├─ /api/knowledge (Knowledge management)           │
│  ├─ /api/conversation (Conversation history)        │
│  └─ /ws/assistant-agent (WebSocket)                 │
│                                                      │
└──────────────┬───────────────────────────────────────┘
               │
               ├─────────────────────┐
               │                     │
        ┌──────▼──────┐      ┌──────▼──────┐
        │ Ingestion    │      │ Agents       │
        │ Services     │      │ (Supervisor) │
        └──────┬───────┘      └──────┬───────┘
               │                     │
               ├─────────────────────┤
               │                     │
               ▼                     ▼
        ┌──────────────────────────────────────┐
        │ Common                               │
        │ - Domain models                      │
        │ - MongoDB persistence                │
        │ - Milvus vector storage              │
        │ - RabbitMQ events                    │
        └──────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ datapilotflow-rag-mcp (Standalone)                   │
│  HTTP MCP Server on port 65510                       │
│                                                      │
│  Consumed by:                                        │
│  - datapilotflow-agents (Supervisor)                │
│  - External MCP clients                             │
│  - Other RAG applications                           │
│                                                      │
│  Accesses:                                           │
│  - Common (domain, persistence, vectordb)           │
└──────────────────────────────────────────────────────┘
```

### Key Communication Patterns

#### Pattern 1: API → RAG MCP (for Supervisor agents)
```python
# In datapilotflow-agents/tools/rag_mcp_tool.py
import httpx

class RAGMCPTool:
    def __init__(self, rag_mcp_url: str = "http://localhost:65510"):
        self.rag_mcp_url = rag_mcp_url
        self.client = httpx.AsyncClient()

    async def retrieve(self, search_query: List[str], collection_name: str) -> Dict:
        """Call RAG MCP server via HTTP"""
        response = await self.client.post(
            f"{self.rag_mcp_url}/mcp",
            json={"tool": "knowledge_expert", "params": {...}}
        )
        return response.json()
```

#### Pattern 2: Event-driven communication
```python
# Services publish events to RabbitMQ
# Processors listen and act on events

from datapilotflow.common import KnowledgeJobPublisher
from datapilotflow.ingestion import KnowledgeJobProcessor

publisher = KnowledgeJobPublisher()
processor = KnowledgeJobProcessor()

# When job is created
publisher.publish_job_created_event(job_id, user_id)

# Processor listens and processes
processor.handle_job_created(event)
```

#### Pattern 3: Direct service calls (within process)
```python
# Within API or Ingestion process

from datapilotflow.ingestion import KnowledgeService
from datapilotflow.common import VectorDBService

knowledge_service = KnowledgeService()
vectordb_service = VectorDBService()

# Direct call to create knowledge base
knowledge_base = await knowledge_service.create(...)

# Direct call to store embeddings
await vectordb_service.store(embeddings)
```

---

## Deployment Options

### Option 1: All-in-One Container (Development)
```bash
docker-compose up
# Runs: API (65500) + RAG MCP (65510) + MongoDB + Milvus + RabbitMQ
```

### Option 2: Distributed Deployment (Production)
```bash
# Deploy each as separate container
docker run datapilotflow-api:1.0
docker run datapilotflow-rag-mcp:1.0
docker run datapilotflow-ingestion:1.0  # Background worker
docker run datapilotflow-agents:1.0      # Optional agent service
```

### Option 3: Kubernetes
```yaml
# kubernetes/rag-mcp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-mcp-service
spec:
  replicas: 3  # Multiple instances for high availability
  template:
    spec:
      containers:
      - name: rag-mcp
        image: datapilotflow-rag-mcp:1.0
        ports:
        - containerPort: 65510
        env:
        - name: MILVUS_URL
          value: "milvus-service:19530"
        - name: MONGO_URL
          value: "mongodb-service:27017"
```

---

## Package Publishing Strategy

### Option 1: Private PyPI (Recommended for now)
```bash
# Publish to private registry (GitHub Packages, Artifactory, etc.)
uv build
uv publish --repository private-pypi datapilotflow-common
uv publish --repository private-pypi datapilotflow-rag-mcp
uv publish --repository private-pypi datapilotflow-ingestion
uv publish --repository private-pypi datapilotflow-agents
uv publish --repository private-pypi datapilotflow-api
```

### Option 2: Open Source (PyPI)
Publish packages publicly if desired:
```bash
uv publish datapilotflow-common
uv publish datapilotflow-rag-mcp  # Standalone retrieval for community
```

### Option 3: Monorepo with Workspaces
Keep all packages in single repo during development:
```
datapilotflow/
├── packages/
│   ├── common/
│   ├── rag-mcp/
│   ├── ingestion/
│   ├── agents/
│   └── api/
├── pyproject.toml (workspace root)
└── docker-compose.yml
```

---

## Migration Plan

### Phase 1: Extract Common Package (Week 1)
- [ ] Create `datapilotflow-common` repo/directory
- [ ] Move domain, persistence, vectordb, processors, events
- [ ] Create `pyproject.toml` with explicit dependencies
- [ ] Create tests

### Phase 2: Extract RAG MCP (Week 2) ⭐
- [ ] Create `datapilotflow-rag-mcp` repo
- [ ] Extract `src/agents/rag_agent/mcp/` and RAG logic
- [ ] Update to depend on `datapilotflow-common`
- [ ] Create standalone Docker image
- [ ] Test independent operation

### Phase 3: Extract Ingestion Package (Week 2-3)
- [ ] Create `datapilotflow-ingestion` repo
- [ ] Move knowledge services, processors
- [ ] Depend on common + processors

### Phase 4: Extract Agents Package (Week 3)
- [ ] Create `datapilotflow-agents` repo
- [ ] Move supervisor/assistant agent logic
- [ ] Add RAG MCP tool for HTTP communication
- [ ] Test with running RAG MCP instance

### Phase 5: Finalize API Package (Week 3-4)
- [ ] Update API to import from all packages
- [ ] Integration testing
- [ ] Update Docker compose for all services

---

## Benefits of This Architecture

### Immediate
1. **RAG Reusability**: Any application can use RAG MCP (via HTTP)
2. **Independent Scaling**: Scale RAG service separately
3. **Clear Ownership**: Team can own RAG MCP project
4. **Easy Distribution**: Package RAG MCP for consumption

### Long-term
1. **Microservices Ready**: Natural evolution path
2. **Version Independence**: Update RAG independently
3. **Community**: Can open-source RAG MCP separately
4. **Flexibility**: Swap ingestion or agents without affecting RAG

---

## Configuration & Deployment

### Environment Variables for RAG MCP
```env
# .env.rag-mcp
RAG_MCP_HOST=0.0.0.0
RAG_MCP_PORT=65510
MONGO_URL=mongodb://localhost:27017
MILVUS_HOST=localhost
MILVUS_PORT=19530
LLM_API_KEY=your-key
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

### Environment Variables for API/Agents
```env
# .env.api
API_PORT=65500
RAG_MCP_URL=http://rag-mcp:65510  # Connect to RAG MCP service
MONGO_URL=mongodb://localhost:27017
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

---

## Testing Strategy

### Unit Tests (Each Package)
```bash
cd datapilotflow-common && pytest tests/
cd datapilotflow-rag-mcp && pytest tests/
cd datapilotflow-ingestion && pytest tests/
```

### Integration Tests (RAG MCP Standalone)
```bash
# Start RAG MCP server
docker run -p 65510:65510 datapilotflow-rag-mcp:dev

# Test HTTP MCP calls
pytest tests/integration/test_rag_mcp_http.py
```

### End-to-End Tests (Full System)
```bash
docker-compose up  # All services

# Test full workflow
pytest tests/e2e/
```

---

## Summary: 5-Project Architecture

| Project | Purpose | Status | Deploy |
|---------|---------|--------|--------|
| **common** | Shared foundation | ✅ Extract first | Library |
| **rag-mcp** | Standalone retrieval | ⭐ **NEW** | Service (port 65510) |
| **ingestion** | Knowledge pipeline | ⚠️ Extract third | Library/Worker |
| **agents** | Supervisor agents | ⚠️ Extract fourth | Library |
| **api** | Main application | ⚠️ Extract last | Service (port 65500) |

**Key Insight**: RAG MCP runs as independent HTTP service, consumed by API + Agents + External apps via MCP protocol.

Is this the architecture you envisioned? Should we start extracting packages in this order?
