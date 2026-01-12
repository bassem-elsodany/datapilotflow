# DataPilotFlow API

**API Layer - REST API and WebSocket Exposure**

The `datapilotflow-api` package provides the REST API and WebSocket endpoints for the DataPilotFlow platform. It orchestrates all services and agents to provide a unified API interface.

## 🏗️ Architecture Position

### System Architecture Diagram

```mermaid
graph TB
    Frontend["🎨 Frontend<br/>Dashboard<br/>Mobile App"]
    Clients["🔌 External Clients<br/>API Users"]

    API["🌐 datapilotflow-api<br/>REST API + WebSocket<br/>:65500<br/><br/>33+ Routers<br/>Knowledge | Auth | Agent<br/>Conversation | Notifications<br/>Models | Files | Tools"]

    Services["🔧 Services<br/>Business Logic<br/><br/>Event Publishing<br/>Data Management"]

    Agents["🧠 Agents<br/>RAG | Assistant"]

    RabbitMQ["📨 RabbitMQ<br/>Message Broker<br/>Topic Exchanges<br/>Queues"]

    Events["🎧 Event Listeners<br/>(Separate Processes)<br/>Job | File | Notification"]
    Processors["⚙️ Processors<br/>Document Processing<br/>Pipeline Orchestration"]

    Databases["🗄️ Databases<br/>MongoDB | Milvus<br/>Cache/Sessions"]

    Frontend -->|HTTP/WS:65500| API
    Clients -->|HTTP/WS:65500| API

    API -->|calls| Services
    API -->|uses| Agents

    Services -->|accesses| Databases
    Services -->|publishes events to| RabbitMQ

    RabbitMQ -->|consumes messages| Events
    Events -->|triggers| Processors
    Processors -->|uses| Services

    Agents -->|access| Databases

    style API fill:#E6F3FF,stroke:#0051BA,stroke-width:3px
    style Services fill:#F0E6FF,stroke:#7851A9,stroke-width:2px
    style Agents fill:#E6F9FF,stroke:#0066CC,stroke-width:2px
    style Events fill:#FFE6F0,stroke:#CC0066,stroke-width:2px
    style RabbitMQ fill:#FFE6E6,stroke:#C41E3A,stroke-width:2px
    style Databases fill:#FFF9E6,stroke:#CC6600,stroke-width:2px
```

**Key Architectural Points**:

1. **Event-Driven Decoupling**:
   - Services publish events to RabbitMQ (not directly to Event Listeners)
   - Event Listeners (running as separate processes) consume messages from RabbitMQ
   - This provides complete decoupling and allows independent scaling
   - API requests trigger events asynchronously without waiting for processing

2. **Layered Processing**:
   - Synchronous: API → Services → Databases (immediate response to client)
   - Asynchronous: Services → RabbitMQ → Event Listeners → Processors → Services (background work)

3. **No Direct Dependencies**:
   - API doesn't know about Event Listeners
   - Services don't directly depend on Event Listeners
   - Only integration point is RabbitMQ message broker
   - Processors can use Services to update state after event processing

**This package provides**:
- REST API endpoints (FastAPI)
- WebSocket endpoints for real-time communication
- Authentication and authorization
- Request/response validation
- API documentation (OpenAPI/Swagger)
- Event publishing through services (JobEventPublisher, FileUploadEventPublisher, etc.)

## 📋 Module Capabilities

### 1. **REST API Endpoints**
- **Knowledge Management** (jobs, sources, documents, collections)
- **Authentication & Authorization** (login, user management, roles)
- **Agent Management** (RAG, Assistant agent operations)
- **Conversation Management** (chat history, multi-turn)
- **Notifications** (real-time updates, delivery)
- **Vector Database** (collection management, search)
- **Model Providers** (LLM configuration)
- **File Management** (uploads, processing)
- **Tool & MCP** (server management, tool configuration)

### 2. **WebSocket Real-Time Communication**
- Assistant agent streaming responses
- RAG agent interactions
- Job progress notifications
- Real-time status updates

### 3. **Authentication**
- JWT token-based authentication
- Role-based access control (RBAC)
- User session management

### 4. **Documentation**
- OpenAPI/Swagger UI at `/docs`
- ReDoc at `/redoc`
- JSON schema at `/openapi.json`

## 🔄 API Request Flow - Synchronous vs Event-Driven

### Synchronous Request Flow (Immediate Response)
```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Router
    participant Service as Business Service
    participant DAO as Data Access (DAO)
    participant DB as Database

    Client->>API: HTTP Request + JWT
    API->>API: Validate JWT
    API->>API: Validate Pydantic Schema
    API->>Service: Call Service Method
    Service->>DAO: Access/Update Data
    DAO->>DB: Execute Query
    DB-->>DAO: Return Result
    DAO-->>Service: Return Data
    Service-->>API: Return Business Result
    API-->>Client: HTTP Response
```
### Complete Request-Response-Notification Flow
```
1. SYNCHRONOUS (Blocking):
   Client → API Router → Service → DAO → Database
   ↑ Return immediate response (202 Accepted for async)

2. ASYNCHRONOUS (Non-blocking):
   Service → Event Publisher → RabbitMQ
   Event Listener (separate process) ← consumes
   → Event Processor → Service (update state)
   → WebSocket/Notification → Client (eventual notification)
```

## 🚀 Installation

### Prerequisites
- Python >=3.11
- All lower-layer packages installed
- MongoDB, Milvus, RabbitMQ running
- RAG MCP server accessible (if using RAG features)

### Install All Dependencies

```bash
uv pip install -e ../datapilotflow-domain \
  -e ../datapilotflow-infrastructure \
  -e ../datapilotflow-services \
  -e ../datapilotflow-processors \
  -e ../datapilotflow-events \
  -e ../datapilotflow-rag-agent \
  -e ../datapilotflow-assistant-agent \
  -e .
```

## 🛠️ How to Build & Start

### Build Steps

1. **Install all dependencies in order**
   ```bash
   cd ../datapilotflow-domain && pip install -e .
   cd ../datapilotflow-infrastructure && pip install -e .
   cd ../datapilotflow-services && pip install -e .
   cd ../datapilotflow-processors && pip install -e .
   cd ../datapilotflow-events && pip install -e .
   cd ../datapilotflow-rag-agent && pip install -e .
   cd ../datapilotflow-assistant-agent && pip install -e .
   cd ../datapilotflow-api && pip install -e .
   ```

2. **Start infrastructure services** (if using Docker)
   ```bash
   cd ../../docker
   docker-compose up -d mongodb milvus rabbitmq
   ```

### Starting the API Server

```bash
# Standard startup
python run_api_server.py

# With custom host/port
API_SERVER_HOST=127.0.0.1 API_SERVER_PORT=8000 python run_api_server.py

# With verbose logging
export DATAPILOTFLOW_LOG_LEVEL=DEBUG
python run_api_server.py
```
