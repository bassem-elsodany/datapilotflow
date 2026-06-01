# datapilotflow-infrastructure

**Data access layer — MongoDB, Milvus, and RabbitMQ clients with DAOs for all domain entities.**

This package sits directly above `datapilotflow-domain`. It owns all database connections, collection management, and CRUD operations. No business logic lives here — only data access.

---

## Responsibility

- Provide singleton clients for MongoDB, Milvus, and RabbitMQ
- Define Data Access Objects (DAOs) for all domain entities
- Manage MongoDB indexes and Milvus collection schemas
- Expose a clean data access API to the services layer above

---

## Package Structure

```
src/datapilotflow/infrastructure/
├── mongo/
│   ├── client.py              # Singleton MongoDB client with connection pooling
│   └── indexes.py             # MongoDB index definitions and setup
├── mq/
│   └── client.py              # RabbitMQ async client (aio-pika)
├── vectordb/
│   ├── processor.py           # Vector processing utilities
│   └── milvus/
│       ├── client.py          # Milvus client wrapper
│       ├── indexes.py         # Milvus index configurations
│       ├── utils.py           # Milvus helper utilities
│       └── examples.py        # Usage examples
└── dao/
    ├── auth/
    │   ├── auth_dao.py        # User authentication data access
    │   └── roles_dao.py       # Role definitions and assignment
    ├── knowledge/
    │   ├── knowledge_job_dao.py       # Ingestion job CRUD
    │   ├── knowledge_source_dao.py    # Knowledge source CRUD
    │   ├── job_timeline_dao.py        # Job step timeline
    │   ├── document_splitter_dao.py   # Splitter configuration
    │   ├── url_source_dao.py          # URL source tracking
    │   └── llm_content_filter_dao.py  # LLM content filter config
    ├── confluence/
    │   ├── confluence_credential_dao.py  # Confluence credentials
    │   ├── confluence_space_dao.py       # Confluence space metadata
    │   └── confluence_page_dao.py        # Confluence page tracking
    ├── model_provider/
    │   └── model_provider_dao.py      # LLM provider configuration
    ├── notification/
    │   └── notification_service.py    # Notification persistence
    ├── tool/
    │   ├── tool_dao.py                # Tool definitions
    │   └── mcp_server_dao.py          # MCP server registry
    ├── vectordb/
    │   └── vectordb_collection_dao.py # Vector collection metadata
    └── file_management/
        └── rag_file_upload_service.py # File upload tracking
```

---

## Key Components

### MongoDB Client

Singleton client with connection pooling. All DAOs share the same underlying connection.

```python
from datapilotflow.infrastructure.mongo.client import get_mongo_client, close_mongo_client

client = get_mongo_client()
db = client.get_database()

# On service shutdown
close_mongo_client()
```

### Milvus Client

Manages vector collections and similarity search operations.

```python
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper

client = MilvusClientWrapper()
results = client.search(
    collection_name="my_collection",
    query_vectors=[[0.1, 0.2, ...]],
    top_k=5
)
```

### RabbitMQ Client

Async publish/consume over aio-pika with topic exchange routing.

```python
from datapilotflow.infrastructure.mq.client import RabbitMQClient

client = RabbitMQClient()
await client.publish_message(
    routing_key="job.created",
    message={"job_id": "123"}
)
```

### DAOs

Each DAO provides CRUD operations against MongoDB for its domain entity.

```python
from datapilotflow.infrastructure.dao.knowledge.knowledge_job_dao import KnowledgeJobDAO
from datapilotflow.infrastructure.dao.auth.auth_dao import AuthDAO
from datapilotflow.infrastructure.dao.tool.mcp_server_dao import MCPServerDAO

job_dao = KnowledgeJobDAO()
job = job_dao.get_by_id(job_id)
job_dao.update(job_id, {"status": "COMPLETED"})
```

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
pymongo >= 4.9.2
pymilvus >= 2.6.5
aio-pika >= 9.3.0
sentence-transformers >= 5.2.0
langchain-mongodb >= 0.1.0
pydantic >= 2.10.6
loguru >= 0.7.3
```

---

## Installation

```bash
cd datapilotflow-infrastructure
uv pip install -e ../datapilotflow-domain -e .
```

---

## Dependency Position

```
datapilotflow-services    --|
datapilotflow-events      --|-->  datapilotflow-infrastructure  -->  datapilotflow-domain
datapilotflow-processors  --|
datapilotflow-rag-agent   --|
```
