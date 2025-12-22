# DataPilotFlow Infrastructure

**Infrastructure Layer - Database Access and External System Integration**

The `datapilotflow-infrastructure` package provides data access objects (DAOs), database clients, and infrastructure abstractions. It sits directly above the domain layer and provides concrete implementations for data persistence.

## 📦 Package Overview

- **Version**: 1.0.0
- **Python**: >=3.11
- **Dependencies**: `datapilotflow-domain` + database drivers
- **Purpose**: Database access, message queues, and infrastructure abstractions

## 🏗️ Architecture Position

```
┌─────────────────────────────────────────┐
│     Services, API, Agents, Processors   │
└────────────────┬────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────┐
│   datapilotflow-infrastructure          │
│   (Database Access & Infrastructure)    │
└────────────────┬────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────┐
│      datapilotflow-domain               │
│      (Foundation - Models & Config)      │
└─────────────────────────────────────────┘
```

**This package provides**:
- MongoDB client and DAOs
- Milvus vector database client
- RabbitMQ message queue client
- Data access objects for all domain entities

## 📁 Package Structure

```
datapilotflow-infrastructure/
├── src/datapilotflow/infrastructure/
│   ├── __init__.py
│   │
│   ├── mongo/                    # MongoDB infrastructure
│   │   ├── client.py            # MongoClientWrapper (singleton)
│   │   └── indexes.py           # Database indexes
│   │
│   ├── mq/                       # Message Queue (RabbitMQ)
│   │   ├── client.py            # RabbitMQClient (singleton)
│   │   └── __init__.py
│   │
│   ├── vectordb/                 # Vector Database (Milvus)
│   │   ├── milvus/
│   │   │   ├── client.py        # MilvusClientWrapper
│   │   │   ├── indexes.py       # Vector indexes
│   │   │   ├── utils.py         # Utility functions
│   │   │   └── examples.py      # Usage examples
│   │   └── processor.py         # Vector processing utilities
│   │
│   └── dao/                      # Data Access Objects (organized by domain)
│       ├── __init__.py
│       │
│       ├── auth/                 # Authentication & Authorization
│       │   ├── auth_dao.py      # User authentication DAO
│       │   └── roles_dao.py     # Roles and permissions DAO
│       │
│       ├── file_management/     # File upload management
│       │   └── rag_file_upload_service.py
│       │
│       ├── knowledge/            # Knowledge base DAOs
│       │   ├── document_splitter_dao.py
│       │   ├── job_timeline_dao.py
│       │   ├── knowledge_job_dao.py
│       │   ├── knowledge_source_dao.py
│       │   ├── llm_content_filter_dao.py
│       │   └── url_source_dao.py
│       │
│       ├── model_provider/       # Model provider DAO
│       │   └── model_provider_dao.py
│       │
│       ├── notification/         # Notification DAO
│       │   └── notification_service.py
│       │
│       ├── tool/                 # Tool & MCP server DAOs
│       │   ├── mcp_server_dao.py
│       │   └── tool_dao.py
│       │
│       └── vectordb/            # Vector database collection DAO
│           └── vectordb_collection_dao.py
│
├── tests/
├── pyproject.toml
└── README.md
```

## 🔑 Key Components

### 1. MongoDB Client (`mongo/client.py`)

Singleton MongoDB client wrapper with connection pooling:

**Features**:
- Thread-safe singleton pattern
- Connection pooling configuration
- Automatic reconnection handling
- Index management

**Usage**:
```python
from datapilotflow.infrastructure.mongo.client import (
    MongoClientWrapper,
    get_mongo_client,
    close_mongo_client
)

# Get singleton client
client = await get_mongo_client()

# Access database
db = client.get_database("datapilotflow")
collection = db.get_collection("knowledge_jobs")

# Cleanup (on shutdown)
await close_mongo_client()
```

### 2. Vector Database Client (`vectordb/milvus/client.py`)

Milvus vector database client wrapper:

**Features**:
- Generic type support for different collection types
- Collection management (create, delete, list)
- Vector search operations
- Index management

**Usage**:
```python
from datapilotflow.infrastructure.vectordb.milvus.client import (
    MilvusClientWrapper
)

# Initialize client
client = MilvusClientWrapper()

# Create collection
await client.create_collection(
    collection_name="my_collection",
    dimension=1536,
    description="My vector collection"
)

# Search vectors
results = await client.search(
    collection_name="my_collection",
    query_vectors=[[0.1, 0.2, ...]],
    top_k=5
)
```

### 3. RabbitMQ Client (`mq/client.py`)

RabbitMQ message queue client with connection pooling:

**Features**:
- Async message publishing
- Message consumption with callbacks
- Exchange and queue declaration
- Connection pooling

**Usage**:
```python
from datapilotflow.infrastructure.mq.client import (
    RabbitMQClient,
    get_rabbitmq_client,
    close_rabbitmq_client
)

# Get singleton client
connection = await get_rabbitmq_client()

# Declare exchange and queue
client = RabbitMQClient(connection)
exchange = await client.declare_exchange("events", "topic")
queue = await client.declare_queue("job_events")

# Publish message
await client.publish_message(
    exchange=exchange,
    routing_key="job.created",
    message={"job_id": "123", "status": "pending"}
)

# Consume messages
await client.consume_messages(
    queue=queue,
    callback=handle_message
)
```

### 4. Data Access Objects (DAOs)

Organized by domain, each DAO provides CRUD operations for domain entities:

**Knowledge DAOs**:
```python
from datapilotflow.infrastructure.dao.knowledge import (
    KnowledgeJobDAO,
    KnowledgeSourceDAO,
    JobTimelineDAO,
    DocumentSplitterDAO,
    UrlSourceDAO,
    LLMContentFilterDAO
)

# Create DAO instance
job_dao = KnowledgeJobDAO()

# CRUD operations
job = await job_dao.create(knowledge_job)
job = await job_dao.get_by_id(job_id)
jobs = await job_dao.get_all()
await job_dao.update(job_id, updates)
await job_dao.delete(job_id)
```

**Auth DAOs**:
```python
from datapilotflow.infrastructure.dao.auth import (
    AuthDAO,
    RolesDAO
)

auth_dao = AuthDAO()
user = await auth_dao.authenticate(email, password)
```

**Other DAOs**:
- `ModelProviderDAO` - Model provider management
- `VectorDBCollectionDAO` - Vector collection management
- `NotificationService` - Notification persistence
- `ToolDAO`, `MCPServerDAO` - Tool and MCP server management

## 🔗 How This Package Uses Domain

### Configuration
```python
from datapilotflow.domain.config import settings

# Use domain config for connection settings
mongo_conn_str = settings.MONGO_CONN_STR
vector_db_host = settings.VECTOR_DB_HOST
rabbitmq_host = settings.RABBITMQ_HOST
```

### Domain Models
```python
from datapilotflow.domain.knowledge import KnowledgeJob, KnowledgeSource
from datapilotflow.domain.user import User
from datapilotflow.domain.vectordb import VectorDBCollection

# DAOs work with domain models
job = KnowledgeJob(name="My Job", ...)
await job_dao.create(job)  # Persist domain model
```

### Logging
```python
from datapilotflow.domain.logging import setup_service_logging

# Use domain logging utility
setup_service_logging("infrastructure")
```

## 🔗 How Other Packages Use This Package

### Services Layer
```python
from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO
from datapilotflow.infrastructure.mongo.client import get_mongo_client
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper

# Services use DAOs for data access
class KnowledgeJobService:
    def __init__(self):
        self.job_dao = KnowledgeJobDAO()
    
    async def create_job(self, job_data):
        job = await self.job_dao.create(job_data)
        return job
```

### Processors Layer
```python
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper

# Processors use infrastructure for vector operations
client = MilvusClientWrapper()
await client.insert_vectors(collection_name, vectors)
```

### Events Layer
```python
from datapilotflow.infrastructure.mq.client import RabbitMQClient

# Events use RabbitMQ for message publishing
client = RabbitMQClient(connection)
await client.publish_message(exchange, routing_key, message)
```

### API Layer
```python
from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO

# API uses DAOs through services
# (API → Services → Infrastructure)
```

## 📦 Dependencies

### DataPilotFlow Dependencies
- `datapilotflow-domain>=1.0.0` - Domain models and configuration

### External Dependencies
- `pymongo>=4.9.2` - MongoDB driver
- `pymilvus>=2.6.5` - Milvus vector database client
- `sentence-transformers>=5.2.0` - Embedding models
- `aio-pika>=9.3.0` - RabbitMQ async client
- `pydantic>=2.10.6` - Data validation
- `loguru>=0.7.3` - Logging

## 🚀 Installation

```bash
cd datapilotflow-infrastructure
pip install -e .
```

**Note**: Install `datapilotflow-domain` first:
```bash
cd ../datapilotflow-domain && pip install -e .
cd ../datapilotflow-infrastructure && pip install -e .
```

## 📝 Usage Examples

### MongoDB Operations
```python
from datapilotflow.infrastructure.mongo.client import get_mongo_client

client = await get_mongo_client()
db = client.get_database("datapilotflow")
collection = db.get_collection("knowledge_jobs")

# Insert document
await collection.insert_one({"name": "My Job", "status": "pending"})

# Query documents
jobs = await collection.find({"status": "pending"}).to_list(length=100)
```

### Vector Database Operations
```python
from datapilotflow.infrastructure.vectordb.milvus.client import MilvusClientWrapper

client = MilvusClientWrapper()

# Create collection
await client.create_collection(
    collection_name="documents",
    dimension=1536,
    description="Document embeddings"
)

# Insert vectors
vectors = [[0.1] * 1536, [0.2] * 1536]
ids = await client.insert_vectors("documents", vectors, ids=["1", "2"])

# Search
results = await client.search(
    collection_name="documents",
    query_vectors=[[0.15] * 1536],
    top_k=5
)
```

### DAO Usage
```python
from datapilotflow.infrastructure.dao.knowledge import KnowledgeJobDAO
from datapilotflow.domain.knowledge import KnowledgeJob

job_dao = KnowledgeJobDAO()

# Create
job = KnowledgeJob(name="My Job", source_id="source_123")
created_job = await job_dao.create(job)

# Read
job = await job_dao.get_by_id(created_job.id)
all_jobs = await job_dao.get_all()

# Update
await job_dao.update(job.id, {"status": "completed"})

# Delete
await job_dao.delete(job.id)
```

## 🧪 Testing

```bash
cd datapilotflow-infrastructure
pytest tests/
```

**Test Requirements**:
- MongoDB instance (or test container)
- Milvus instance (or test container)
- RabbitMQ instance (or test container)

## 📚 Related Packages

**Depends on**:
- ✅ `datapilotflow-domain` - Uses config and domain models

**Used by**:
- ✅ `datapilotflow-services` - Uses DAOs and clients
- ✅ `datapilotflow-processors` - Uses vector DB client
- ✅ `datapilotflow-events` - Uses RabbitMQ client
- ✅ `datapilotflow-api` - Uses through services layer
- ✅ `datapilotflow-rag-agent` - Uses vector DB client
- ✅ `datapilotflow-assistant-agent` - Uses infrastructure clients

## 🎯 Design Principles

1. **Separation of Concerns**: Infrastructure separate from business logic
2. **DAO Pattern**: Data access objects for each domain entity
3. **Singleton Clients**: Shared connection pools for efficiency
4. **Domain Model Usage**: Works with domain models, not raw data
5. **Async/Await**: All operations are async for performance

## 🔧 Configuration

Infrastructure uses configuration from `datapilotflow-domain`:

```python
from datapilotflow.domain.config import settings

# MongoDB
MONGO_HOST = settings.MONGO_HOST
MONGO_PORT = settings.MONGO_PORT
MONGO_DB_NAME = settings.MONGO_DB_NAME

# Vector DB
VECTOR_DB_HOST = settings.VECTOR_DB_HOST
VECTOR_DB_HTTP_PORT = settings.VECTOR_DB_HTTP_PORT

# RabbitMQ
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
```

## 📖 Documentation

For more details:
- MongoDB Client: See `src/datapilotflow/infrastructure/mongo/client.py`
- Vector DB Client: See `src/datapilotflow/infrastructure/vectordb/milvus/client.py`
- RabbitMQ Client: See `src/datapilotflow/infrastructure/mq/client.py`
- DAOs: See `src/datapilotflow/infrastructure/dao/`
