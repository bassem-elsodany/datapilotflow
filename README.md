# DataPilotFlow

> **Intelligent Enterprise Knowledge Platform with Retrieval-Augmented Generation**

A modular, event-driven architecture for building AI-powered knowledge management systems. DataPilotFlow combines multi-agent AI orchestration, real-time document processing, and vector-based knowledge retrieval to enable intelligent conversational interfaces over enterprise data.

## 🎯 Core Capabilities

- **Multi-Agent Orchestration**: Supervisor agent coordinates RAG agent, tools, and services
- **Retrieval-Augmented Generation (RAG)**: Advanced document retrieval with semantic search
- **Event-Driven Architecture**: Asynchronous processing via RabbitMQ
- **Real-time Document Processing**: Text extraction, chunking, and vector embeddings
- **Vector Database Integration**: Milvus for semantic search and similarity matching
- **WebSocket Support**: Real-time AI responses and job progress tracking
- **MCP Server Exposure**: Model Context Protocol for external agent integration
- **Docker Containerization**: Production-ready deployment with 9 microservices

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["🎨 Frontend Layer"]
        Dashboard["📊 DataPilotFlow Dashboard<br/>React + Vite<br/>Port 3000"]
        WebSocket["🔌 WebSocket Clients"]
    end

    subgraph API["🔌 API Layer"]
        APIServer["REST API Server<br/>FastAPI<br/>Port 8800"]
    end

    subgraph Agents["🤖 Agent Layer"]
        AssistantAgent["👤 Assistant Agent<br/>Supervisor/Orchestrator<br/>LangGraph"]
        RAGAgent["🧠 RAG Agent<br/>MCP Server<br/>Port 65510"]
    end

    subgraph Services["⚙️ Services Layer"]
        BizLogic["💼 Business Logic Services<br/>Knowledge | Auth | Users<br/>Notifications | Tools"]
    end

    subgraph Processing["📦 Processing Layer"]
        EventListeners["🎧 Event Listeners<br/>Job | File | Notification"]
        Processors["⚙️ Processors<br/>Extraction | Chunking<br/>Embedding | Storage"]
    end

    subgraph Infrastructure["🗄️ Infrastructure Layer"]
        MongoDB["🗃️ MongoDB<br/>Document Storage<br/>Port 27020"]
        RabbitMQ["📨 RabbitMQ<br/>Event Bus<br/>Port 5675"]
        Milvus["🔍 Milvus Vector DB<br/>Semantic Search<br/>Port 19530"]
        MinIO["📦 MinIO S3<br/>File Storage<br/>Port 9002"]
    end

    Dashboard -->|HTTP| APIServer
    WebSocket -->|WebSocket| APIServer
    APIServer -->|Calls| AssistantAgent
    AssistantAgent -->|MCP Client| RAGAgent
    RAGAgent -->|Query| Milvus
    APIServer -->|Uses| BizLogic
    BizLogic -->|Data Access| MongoDB
    BizLogic -->|Publish| RabbitMQ
    RabbitMQ -->|Consume| EventListeners
    EventListeners -->|Process| Processors
    Processors -->|Store| MongoDB
    Processors -->|Embed| Milvus
    Processors -->|Upload| MinIO
```

### Service Dependency Tree

```mermaid
graph TD
    subgraph Components["📦 Core Components"]
        Domain["datapilotflow-domain<br/>Foundation Layer<br/>Models & Config"]
    end

    subgraph DataAccess["🗄️ Data Access Layer"]
        Infrastructure["datapilotflow-infrastructure<br/>MongoDB | Milvus<br/>RabbitMQ Clients"]
        Domain --> Infrastructure
    end

    subgraph Business["💼 Business Layer"]
        Services["datapilotflow-services<br/>Business Logic<br/>Service Orchestration"]
        Infrastructure --> Services
    end

    subgraph Application["🚀 Application Layer"]
        API["datapilotflow-api<br/>REST API Server"]
        AssistantAgent["datapilotflow-assistant-agent<br/>Supervisor Agent"]
        RAGAgent["datapilotflow-rag-agent<br/>RAG Agent + MCP"]
        Dashboard["datapilotflow-dashboard<br/>React Frontend"]

        Domain --> API
        Services --> API
        Domain --> AssistantAgent
        Services --> AssistantAgent
        Domain --> RAGAgent
        Services --> RAGAgent
    end

    subgraph Events["📨 Event Processing"]
        Events["datapilotflow-events<br/>Event Listeners"]
        Processors["datapilotflow-processors<br/>Document Processing"]
        Domain --> Events
        Infrastructure --> Events
        Domain --> Processors
        Infrastructure --> Processors
        Services --> Processors
    end

    subgraph Orchestration["🐳 Orchestration"]
        Docker["docker/<br/>docker-compose.yml<br/>9 Services"]
    end

    API --> Docker
    AssistantAgent --> Docker
    RAGAgent --> Docker
    Events --> Docker
    Processors --> Docker
```

---

## 📦 Project Structure

### 8 Core Modules

#### 1. **datapilotflow-domain**
   - **Purpose**: Foundation layer with core domain models
   - **Responsibility**: Pure domain entities, configuration, validation
   - **Dependencies**: Minimal (Pydantic, loguru)
   - **Key Entities**: User, Knowledge, Job, Conversation, Agent, Tool
   - **Status**: Stable - Zero dependencies on other modules

#### 2. **datapilotflow-infrastructure**
   - **Purpose**: Data access and external system integration
   - **Responsibility**: MongoDB client, Milvus vector DB, RabbitMQ connection
   - **Dependencies**: `datapilotflow-domain`
   - **Key Components**: DAOs, Database indexes, Connection pools
   - **Databases**: MongoDB (documents), Milvus (vectors), RabbitMQ (events)

#### 3. **datapilotflow-services**
   - **Purpose**: Business logic and service orchestration
   - **Responsibility**: Knowledge management, user management, notifications, tool orchestration
   - **Dependencies**: `datapilotflow-domain`, `datapilotflow-infrastructure`
   - **Key Services**: KnowledgeService, AuthService, NotificationService, ToolService
   - **Pattern**: Service-Oriented Architecture (SOA)

#### 4. **datapilotflow-api**
   - **Purpose**: REST API and WebSocket exposure
   - **Responsibility**: Request routing, response formatting, endpoint definition
   - **Dependencies**: All modules
   - **Framework**: FastAPI
   - **Port**: 8800
   - **Endpoints**: /auth, /knowledge, /conversations, /agents, /tools, /health

#### 5. **datapilotflow-rag-agent**
   - **Purpose**: Retrieval-Augmented Generation with MCP server
   - **Responsibility**: Document retrieval, semantic search, response generation
   - **Dependencies**: `datapilotflow-domain`, `datapilotflow-infrastructure`, `datapilotflow-services`
   - **Framework**: LangGraph, FastMCP
   - **Port**: 65510
   - **Protocol**: MCP (Model Context Protocol)

#### 6. **datapilotflow-assistant-agent**
   - **Purpose**: Supervisor agent with multi-agent orchestration
   - **Responsibility**: Multi-turn conversations, tool orchestration, agent coordination
   - **Dependencies**: `datapilotflow-domain`, `datapilotflow-infrastructure`, `datapilotflow-services`
   - **Framework**: LangGraph
   - **Pattern**: Supervisor pattern for agent coordination

#### 7. **datapilotflow-events**
   - **Purpose**: Event-driven messaging and async processing
   - **Responsibility**: Event publishing, event listening, queue management
   - **Dependencies**: `datapilotflow-domain`
   - **Message Broker**: RabbitMQ
   - **Event Types**: JobEvents, FileUploadEvents, NotificationEvents

#### 8. **datapilotflow-processors**
   - **Purpose**: Document processing and knowledge ingestion pipeline
   - **Responsibility**: Text extraction, chunking, embedding, web crawling
   - **Dependencies**: `datapilotflow-domain`, `datapilotflow-infrastructure`, `datapilotflow-services`
   - **Processors**: FileProcessor, WebCrawler, DocumentSplitter, EmbeddingProcessor

#### 9. **datapilotflow-dashboard**
   - **Purpose**: Web UI for the platform
   - **Responsibility**: User interaction, job management, knowledge browsing
   - **Framework**: React + Vite + Mantine UI
   - **Port**: 3000
   - **Features**: Real-time updates, file uploads, conversation interface

---

## 🐳 Docker Architecture

### 9-Service Production Deployment

```mermaid
graph TB
    subgraph Applications["🚀 Application Services"]
        API["datapilotflow-api-server<br/>Port: 8800<br/>Health: /health"]
        Dashboard["datapilotflow-dashboard<br/>Port: 3000<br/>Health: GET /"]
        Events["datapilotflow-event-listeners<br/>Background Service<br/>No external port"]
        MCP["datapilotflow-mcp-rag<br/>Port: 65510<br/>Health: GET /"]
    end

    subgraph Infrastructure["🗄️ Infrastructure Services"]
        MongoDB["MongoDB<br/>Port: 27020<br/>Volume: data/mongodb"]
        RabbitMQ["RabbitMQ<br/>Port: 5675<br/>Management: 15675"]
        Milvus["Milvus Vector DB<br/>Port: 19530"]
        MinIO["MinIO S3<br/>Port: 9002<br/>Console: 9091"]
        ETcd["ETcd<br/>Port: 2379<br/>Milvus metadata"]
    end

    Dashboard -->|depends_on| API
    API -->|depends_on| MongoDB
    API -->|depends_on| RabbitMQ
    Events -->|depends_on| RabbitMQ
    MCP -->|depends_on| Milvus
    Milvus -->|depends_on| ETcd
    Milvus -->|depends_on| MinIO
```

### Service Startup Order

1. **Infrastructure Services** (no dependencies)
   - MongoDB
   - RabbitMQ
   - ETcd
   - MinIO

2. **Vector Database** (depends on infrastructure)
   - Milvus (depends on ETcd + MinIO)

3. **Application Services** (depends on infrastructure)
   - API Server (depends on MongoDB + RabbitMQ) ← Core service
   - Event Listeners (depends on RabbitMQ)
   - RAG MCP Agent (depends on Milvus)
   - Dashboard (depends on API)

### Health Check Configuration

Each service has configured health checks:
- **API Server**: HTTP GET `/health` every 10s
- **Dashboard**: HTTP GET `/` (wget) every 10s
- **RAG MCP**: HTTP GET `/` every 10s
- **Event Listeners**: Process monitoring via `ps aux`

---

## 🔄 Data Flow Diagrams

### Knowledge Ingestion Pipeline

```mermaid
graph TD
    User["👤 User Upload<br/>File/URL/Confluence"]
    API["📤 API Endpoint<br/>/knowledge/sources"]
    PublishEvent["📨 Publish Event<br/>file_upload_event"]
    RabbitMQ["RabbitMQ<br/>Topic Exchange"]

    EventListener["🎧 Event Listener<br/>FileUploadListener"]
    Processor["⚙️ Document Processor<br/>Extract + Parse"]
    Splitter["✂️ Text Splitter<br/>Chunk Documents"]

    Embedder["🧠 Embedding Service<br/>Generate Vectors"]
    VectorDB["🔍 Milvus<br/>Store Vectors"]

    StorageService["💾 Storage Service<br/>MongoDB + MinIO"]

    User --> API
    API --> PublishEvent
    PublishEvent --> RabbitMQ
    RabbitMQ --> EventListener
    EventListener --> Processor
    Processor --> Splitter
    Splitter --> Embedder
    Embedder --> VectorDB
    Processor --> StorageService
    StorageService --> VectorDB
```

### Query and Response Pipeline

```mermaid
graph TD
    User["👤 User Query<br/>Chat Interface"]
    Dashboard["📊 Dashboard<br/>WebSocket"]
    API["REST API<br/>POST /conversations/message"]

    AssistantAgent["👤 Assistant Agent<br/>LangGraph Orchestrator"]
    ToolCalls["🛠️ Tool Calls<br/>RAG | Knowledge | etc"]

    RAGAgent["🧠 RAG Agent<br/>MCP Client"]
    SemanticSearch["🔍 Semantic Search<br/>Query Embedding"]
    VectorDB["Milvus<br/>Retrieve Documents"]

    ResponseGen["✍️ Response Generation<br/>LLM"]
    WebSocket["🔌 WebSocket Response<br/>Real-time Streaming"]

    User --> Dashboard
    Dashboard --> API
    API --> AssistantAgent
    AssistantAgent --> ToolCalls
    ToolCalls -->|knowledge_expert| RAGAgent
    RAGAgent --> SemanticSearch
    SemanticSearch --> VectorDB
    VectorDB --> ResponseGen
    ResponseGen --> WebSocket
    WebSocket --> Dashboard
    Dashboard --> User
```

### Job Processing Pipeline

```mermaid
graph TD
    Job["📋 Knowledge Job<br/>Import + Process"]
    CreateJob["API Endpoint<br/>/knowledge/jobs"]
    PublishEvent["📨 Publish<br/>job_event"]

    RabbitMQ["RabbitMQ"]
    JobListener["🎧 Job Listener"]

    Pipeline["⚙️ Job Pipeline<br/>5 Steps"]
    Extraction["1️⃣ Extraction"]
    Chunking["2️⃣ Chunking"]
    Embedding["3️⃣ Embedding"]
    Storage["4️⃣ Storage"]
    Timeline["5️⃣ Timeline"]

    Timeline -->|Completion| Notification["🔔 Notification<br/>User Alert"]

    CreateJob --> PublishEvent
    PublishEvent --> RabbitMQ
    RabbitMQ --> JobListener
    JobListener --> Pipeline
    Pipeline --> Extraction
    Extraction --> Chunking
    Chunking --> Embedding
    Embedding --> Storage
    Storage --> Timeline
    Timeline --> Notification
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local dashboard development)
- Python 3.11+ (for local development)
- UV package manager

### Production Deployment

```bash
# Navigate to docker directory
cd docker

# Start all services (9 containers)
docker-compose up -d

# Verify all services are healthy
docker-compose ps

# View logs
docker-compose logs -f api
```

### Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:3000 | Web UI |
| **API** | http://localhost:8800 | REST API |
| **API Docs** | http://localhost:8800/docs | Swagger UI |
| **RabbitMQ UI** | http://localhost:15675 | Message broker management |
| **MinIO Console** | http://localhost:9002 | S3 storage management |
| **Milvus** | http://localhost:19530 | Vector database |

### Local Development

```bash
# Install dependencies for API
cd datapilotflow-api
uv pip install -e ../datapilotflow-domain -e ../datapilotflow-infrastructure -e ../datapilotflow-services -e .

# Install dependencies for Dashboard
cd ../datapilotflow-dashboard
npm install

# Run API server
cd ../datapilotflow-api
python run_api_server.py

# Run Dashboard (in another terminal)
cd ../datapilotflow-dashboard
npm run dev
```

---

## 📊 Component Interaction Matrix

| Component | Depends On | Used By | Protocol |
|-----------|-----------|---------|----------|
| **Domain** | None | All | Python imports |
| **Infrastructure** | Domain | Services, Events, Processors | Python imports |
| **Services** | Domain, Infrastructure | API, Agents, Processors | Python method calls |
| **API** | All | Dashboard, External clients | HTTP/REST + WebSocket |
| **RAG Agent** | Domain, Infrastructure, Services | Assistant Agent | MCP protocol |
| **Assistant Agent** | Domain, Infrastructure, Services | API | Python/LangGraph |
| **Events** | Domain | Infrastructure, Processors | RabbitMQ topics |
| **Processors** | Domain, Infrastructure, Services | Background jobs | Event-driven |
| **Dashboard** | None (frontend only) | User interaction | HTTP/WebSocket |

---

## 🔐 Security Architecture

### Service Isolation

- **Network**: Docker bridge network `datapilotflow-network`
- **Authentication**: JWT token-based API access
- **Authorization**: Role-based access control (Admin, User, Viewer)
- **Data Persistence**: Encrypted volumes at `../data/`

### Environment Configuration

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8800
ENVIRONMENT=production

# Database
MONGODB_URI=mongodb://mongodb:27017
MILVUS_HOST=milvus
MILVUS_PORT=19530

# Message Queue
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5675

# LLM Providers
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
```

---

## 📚 Module Documentation

Each module has detailed documentation:

- [datapilotflow-api/README.md](./datapilotflow-api/README.md) - REST API and endpoints
- [datapilotflow-rag-agent/README.md](./datapilotflow-rag-agent/README.md) - RAG implementation
- [datapilotflow-assistant-agent/README.md](./datapilotflow-assistant-agent/README.md) - Agent orchestration
- [datapilotflow-services/README.md](./datapilotflow-services/README.md) - Business logic
- [datapilotflow-domain/README.md](./datapilotflow-domain/README.md) - Domain models
- [datapilotflow-infrastructure/README.md](./datapilotflow-infrastructure/README.md) - Data access
- [datapilotflow-events/README.md](./datapilotflow-events/README.md) - Event system
- [datapilotflow-processors/README.md](./datapilotflow-processors/README.md) - Document processing
- [docker/README.md](./docker/README.md) - Docker deployment

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, Mantine UI | Web dashboard |
| **API** | FastAPI, Python 3.11 | REST endpoints |
| **Agents** | LangGraph, FastMCP | AI orchestration |
| **Services** | Python, Pydantic | Business logic |
| **Data Storage** | MongoDB 7.0 | Document persistence |
| **Vector Search** | Milvus 2.4 | Semantic search |
| **Message Queue** | RabbitMQ 3.12 | Event streaming |
| **File Storage** | MinIO (S3-compatible) | Object storage |
| **Orchestration** | Docker Compose | Container management |
| **Package Manager** | UV | Python dependency management |

---

## 📈 Performance Characteristics

### Scalability

- **Horizontal**: Event listeners can run in parallel
- **Vertical**: Vector embeddings batched for efficiency
- **Database**: MongoDB sharding, Milvus partitioning

### Latency

- **API Response**: <200ms for simple queries
- **RAG Pipeline**: <2s for document retrieval + generation
- **WebSocket**: Real-time (sub-100ms) for updates

### Throughput

- **Document Ingestion**: 1000+ documents/minute
- **Concurrent Users**: 100+ WebSocket connections
- **API Requests**: 1000+ requests/second

---

## 🔄 Data Models

### Core Entities

```mermaid
graph TD
    User["👤 User<br/>ID | Email | Roles<br/>created_at"]
    Knowledge["📚 Knowledge<br/>ID | Name | Description<br/>source_type"]
    Job["📋 Job<br/>ID | Status | Progress<br/>created_at"]
    Conversation["💬 Conversation<br/>ID | User | Messages<br/>created_at"]
    Document["📄 Document<br/>ID | Content | Metadata<br/>vectors"]

    User -->|owns| Knowledge
    User -->|owns| Conversation
    Knowledge -->|ingested_via| Job
    Job -->|creates| Document
    Conversation -->|retrieves| Document
```

### Event Types

- **JobEvent**: Job created/started/completed/failed
- **FileUploadEvent**: File uploaded and ready for processing
- **NotificationEvent**: System or user notifications
- **TimelineEvent**: Job step transitions

---

## 🚦 Deployment Checklist

- [ ] Docker daemon running
- [ ] Port 3000, 5675, 8800, 19530, 27020 available
- [ ] 10GB+ free disk space for data volumes
- [ ] Environment variables configured
- [ ] SSL certificates (for production)
- [ ] Monitoring/logging setup

---

## 📞 Support & Contributing

For detailed API documentation, see [http://localhost:8800/docs](http://localhost:8800/docs) after deployment.

For contribution guidelines and development setup, see individual module READMEs.

---

## 📄 License

DataPilotFlow © 2025. All rights reserved.

---

**Last Updated**: December 29, 2025
**Status**: Production Ready
**Version**: 1.0.0
