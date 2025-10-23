# DataPilotFlow - Comprehensive Project Overview

## 🎯 Project Purpose

**DataPilotFlow** is an advanced, event-driven platform for building and querying sophisticated Retrieval-Augmented Generation (RAG) knowledge bases. It's designed as a comprehensive AI-powered interview co-pilot that supports technical interviewers by dynamically selecting questions, scoring answers, suggesting follow-ups, and summarizing interview sessions.

## 🏗️ High-Level Architecture

### Core Components

1. **Backend API Server** (FastAPI + Python 3.13)
2. **Frontend Dashboard** (React + TypeScript + Mantine UI)
3. **Event-Driven Processing Pipeline** (RabbitMQ + Async Workers)
4. **Vector Database** (Milvus for embeddings)
5. **Document Database** (MongoDB for metadata)
6. **Containerized Infrastructure** (Docker Compose)

### Technology Stack

#### Backend
- **Framework**: FastAPI with async/await patterns
- **Language**: Python 3.13 with type hints
- **AI/ML**: LangGraph, LangChain, LiteLLM, Sentence Transformers
- **Vector DB**: Milvus for vector storage and similarity search
- **Document DB**: MongoDB for metadata and state management
- **Message Queue**: RabbitMQ for event-driven architecture
- **Logging**: Loguru for structured logging
- **Validation**: Pydantic for data models

#### Frontend
- **Framework**: React 19 with TypeScript
- **UI Library**: Mantine UI components
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v7
- **Build Tool**: Vite
- **Testing**: Vitest + Testing Library

#### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database**: MongoDB 7.0, Milvus 2.6.2
- **Message Broker**: RabbitMQ 3.12
- **Object Storage**: MinIO (for Milvus)
- **Metadata Store**: etcd (for Milvus)

## 🔄 Data Flow Architecture

### 1. Knowledge Ingestion Pipeline

```
User Upload → File Processing → Document Chunking → Embedding Generation → Vector Storage
     ↓              ↓                ↓                    ↓                ↓
RabbitMQ → Event Listeners → Text Splitters → LLM Providers → Milvus Vector DB
```

### 2. Query Processing Pipeline

```
User Query → Query Rewriting → Document Retrieval → Document Judging → Answer Generation
     ↓             ↓                ↓                   ↓                ↓
LangGraph → LLM Enhancement → Vector Search → Relevance Scoring → Final Response
```

### 3. Event-Driven Architecture

```
API Request → Event Publisher → RabbitMQ → Event Listener → Background Processor → Status Update
     ↓              ↓             ↓            ↓                ↓                ↓
User Action → Domain Events → Message Queue → Async Worker → Business Logic → Database Update
```

## 📁 Project Structure

### Backend (`/backend/`)
```
backend/
├── src/
│   ├── api/                    # FastAPI routes and endpoints
│   │   ├── routers/           # API route handlers
│   │   └── constants.py       # API configuration
│   ├── domain/                # Business domain models
│   │   ├── knowledge/         # Knowledge management models
│   │   ├── user/              # User and role models
│   │   ├── events/            # Domain events
│   │   └── rag/               # RAG-specific models
│   ├── services/              # Business logic services
│   │   ├── auth/              # Authentication services
│   │   ├── knowledge/         # Knowledge processing services
│   │   ├── events_listeners/  # Event processing
│   │   └── model_provider/    # LLM provider management
│   ├── processors/            # Background processors
│   │   ├── knowledge_job/    # Job processing
│   │   ├── file_upload/      # File processing
│   │   └── crawler/          # Web crawling
│   ├── workflow/             # LangGraph workflow
│   │   ├── graph.py          # Main workflow graph
│   │   ├── nodes/            # Workflow nodes
│   │   └── state.py          # Workflow state
│   ├── infrastructure/       # External system integrations
│   │   ├── mongo/            # MongoDB client
│   │   └── milvus/           # Milvus vector DB client
│   └── config.py             # Application configuration
├── run_*.py                  # Service entry points
├── pyproject.toml            # Python dependencies
└── Dockerfile               # Container configuration
```

### Frontend (`/dashboard/`)
```
dashboard/
├── src/
│   ├── pages/                # React page components
│   │   ├── dashboard/        # Main dashboard pages
│   │   │   ├── apps/         # Application pages
│   │   │   └── management/   # Management interfaces
│   │   └── auth/             # Authentication pages
│   ├── components/           # Reusable UI components
│   ├── api/                  # API client and resources
│   ├── hooks/                # Custom React hooks
│   ├── layouts/              # Page layouts
│   ├── routes/               # Routing configuration
│   └── theme/                # UI theme configuration
├── package.json              # Node.js dependencies
└── vite.config.mjs          # Build configuration
```

### Docker (`/docker/`)
```
docker/
├── docker-compose.yml        # Production services
├── docker-compose.dev.yml    # Development overrides
├── Dockerfile               # API server container
├── startup.sh              # Management script
└── mongo-init/              # Database initialization
```

## 🚀 Key Features

### 1. Knowledge Management
- **Multi-source Ingestion**: Web crawling, file uploads, API integrations
- **Intelligent Chunking**: Text and document structure-based splitting
- **Vector Embeddings**: Support for multiple embedding models
- **Semantic Search**: Advanced retrieval with relevance scoring

### 2. Interview Workflow
- **Dynamic Question Selection**: AI-powered question recommendation
- **Answer Scoring**: LLM-based evaluation with rationale
- **Follow-up Suggestions**: Context-aware follow-up questions
- **Session Management**: Complete interview state tracking

### 3. Event-Driven Processing
- **Asynchronous Jobs**: Background processing of large datasets
- **Real-time Updates**: WebSocket notifications for job progress
- **Fault Tolerance**: Dead letter queues and error handling
- **Scalable Architecture**: Horizontal scaling capabilities

### 4. User Management
- **Role-based Access**: Granular permission system
- **Authentication**: JWT-based security
- **Multi-user Support**: User isolation and data privacy

## 🔧 Development Workflow

### Local Development
1. **Infrastructure Setup**: `./docker/startup.sh dev`
2. **Backend Development**: `cd backend && python run_api_server.py`
3. **Frontend Development**: `cd dashboard && npm run dev`
4. **Event Listeners**: `python run_all_event_listeners.py`

### Production Deployment
1. **Full Stack**: `./docker/startup.sh start`
2. **Health Monitoring**: `./docker/startup.sh health`
3. **Log Management**: `./docker/startup.sh logs [service]`

## 📊 Service Architecture

### API Server (Port 8800)
- **FastAPI Application**: RESTful API with OpenAPI documentation
- **Authentication**: JWT-based user authentication
- **WebSocket Support**: Real-time communication
- **Health Checks**: Service monitoring endpoints

### Event Listeners
- **Job Event Listener**: Processes knowledge job requests
- **File Upload Listener**: Handles file processing events
- **Notification Listener**: Manages user notifications

### Database Services
- **MongoDB (Port 27020)**: Metadata and user data
- **Milvus (Port 19530)**: Vector embeddings and similarity search
- **RabbitMQ (Port 5675)**: Message queuing and event processing

## 🎯 Use Cases

### 1. Technical Interview Automation
- **Question Bank Management**: Curated technical questions by domain
- **Adaptive Interviewing**: Dynamic question selection based on candidate responses
- **Performance Analytics**: Scoring and recommendation generation

### 2. Knowledge Base Construction
- **Document Processing**: Automated extraction from various sources
- **Content Enrichment**: Metadata extraction and categorization
- **Search Enhancement**: Semantic search capabilities

### 3. Content Management
- **Multi-format Support**: PDF, DOCX, web pages, API data
- **Intelligent Chunking**: Context-aware document splitting
- **Version Control**: Document versioning and change tracking

## 🔒 Security & Compliance

### Authentication & Authorization
- **JWT Tokens**: Secure user authentication
- **Role-based Access**: Granular permission system
- **API Security**: CORS and trusted host middleware

### Data Protection
- **User Isolation**: Data segregation by user
- **Secure Storage**: Encrypted sensitive data
- **Audit Logging**: Comprehensive activity tracking

## 📈 Performance & Scalability

### Optimization Strategies
- **Async Processing**: Non-blocking I/O operations
- **Batch Processing**: Efficient bulk operations
- **Caching**: Redis for session and data caching
- **Connection Pooling**: Database connection optimization

### Monitoring & Observability
- **Structured Logging**: Comprehensive log management
- **Health Checks**: Service availability monitoring
- **Metrics Collection**: Performance and usage analytics
- **Error Tracking**: Detailed error reporting and debugging

## 🛠️ Development Guidelines

### Code Standards
- **Type Hints**: Comprehensive type annotations
- **Async/Await**: Consistent async programming patterns
- **Error Handling**: Comprehensive exception management
- **Documentation**: Detailed docstrings and comments

### Testing Strategy
- **Unit Tests**: Component-level testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Load and stress testing

## 🚀 Future Roadmap

### Short-term Enhancements
- **Enhanced UI/UX**: Improved user interface and experience
- **Advanced Analytics**: Detailed performance metrics and insights
- **API Rate Limiting**: Request throttling and protection
- **Multi-language Support**: Internationalization capabilities

### Long-term Vision
- **AI Model Integration**: Support for multiple LLM providers
- **Advanced Workflows**: Custom pipeline builder
- **Enterprise Features**: SSO, LDAP integration, audit trails
- **Mobile Support**: Mobile application development

---

This comprehensive overview provides a complete understanding of the DataPilotFlow project, its architecture, features, and development approach. The system represents a sophisticated, production-ready platform for AI-powered knowledge management and interview automation.
