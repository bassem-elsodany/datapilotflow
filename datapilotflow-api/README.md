# DataPilotFlow API

**API Layer - REST API and WebSocket Exposure**

The `datapilotflow-api` package provides the REST API and WebSocket endpoints for the DataPilotFlow platform. It orchestrates all services and agents to provide a unified API interface.

## 📦 Package Overview

- **Version**: 1.0.0
- **Python**: >=3.11
- **Dependencies**: All DataPilotFlow packages
- **Purpose**: API exposure layer for UI and integrations

## 🏗️ Architecture Position

```
┌─────────────────────────────────────────┐
│     Frontend, External Clients           │
└────────────────┬────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────▼────────────────────────┐
│   datapilotflow-api                    │
│   (REST API + WebSocket)                │
└────────────────┬────────────────────────┘
                 │ orchestrates
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
- REST API endpoints (FastAPI)
- WebSocket endpoints for real-time communication
- Authentication and authorization
- Request/response validation
- API documentation (OpenAPI/Swagger)

## 📁 Package Structure

```
datapilotflow-api/
├── src/datapilotflow/api/
│   ├── __init__.py
│   ├── server.py              # FastAPI application
│   ├── config.py              # API configuration
│   │
│   ├── routers/                # API routers
│   │   ├── agent/
│   │   │   ├── agent_router.py
│   │   │   └── assistant_websocket_router.py
│   │   ├── knowledge/
│   │   │   ├── knowledge_router.py
│   │   │   ├── knowledge_job_router.py
│   │   │   └── document_splitter_router.py
│   │   ├── conversation/
│   │   │   └── conversation_router.py
│   │   ├── auth/
│   │   │   └── auth_router.py
│   │   ├── notifications/
│   │   │   └── notification_router.py
│   │   ├── model_provider/
│   │   │   └── model_provider_router.py
│   │   ├── users/
│   │   │   └── user_router.py
│   │   ├── tools/
│   │   │   └── tool_router.py
│   │   └── vectordb/
│   │       └── vectordb_router.py
│   │
│   ├── middleware/             # Middleware
│   │   ├── auth.py
│   │   └── error_handling.py
│   │
│   └── dependencies/           # Dependency injection
│       ├── auth.py
│       └── services.py
│
├── run_api_server.py           # API server entry point
├── tests/
├── pyproject.toml
└── README.md
```

## 🔑 Key Components

### 1. FastAPI Application (`server.py`)

**Main Application**: FastAPI app with all routers

**Features**:
- CORS configuration
- Middleware setup
- Router registration
- WebSocket support
- OpenAPI documentation

### 2. API Routers

**Knowledge Routers**:
- `knowledge_router.py` - Knowledge source management
- `knowledge_job_router.py` - Knowledge job operations
- `document_splitter_router.py` - Document splitting

**Agent Routers**:
- `agent_router.py` - Agent operations
- `assistant_websocket_router.py` - WebSocket for assistant agent

**Other Routers**:
- `auth_router.py` - Authentication
- `conversation_router.py` - Conversation management
- `notification_router.py` - Notifications
- `model_provider_router.py` - Model providers
- `user_router.py` - User management
- `tool_router.py` - Tools and MCP servers
- `vectordb_router.py` - Vector database collections

### 3. Authentication Middleware

**JWT Authentication**: Token-based authentication

**Features**:
- JWT token validation
- User authentication
- Role-based access control

## 🔗 How This Package Uses Lower Layers

### Uses Services
```python
from datapilotflow.services.knowledge import KnowledgeJobService
from datapilotflow.services.auth import AuthService
from datapilotflow.services.conversation import ConversationHistoryService

# API uses all services
job_service = KnowledgeJobService()
auth_service = AuthService()
conversation_service = ConversationHistoryService()
```

### Uses Agents
```python
from datapilotflow.assistant_agent import AssistantAgentService
from datapilotflow.rag_agent import RAGAgentService

# API can use agents directly
assistant_agent = AssistantAgentService()
rag_agent = RAGAgentService()
```

### Uses Infrastructure
```python
# API uses infrastructure through services
# (API → Services → Infrastructure)
```

### Uses Domain
```python
from datapilotflow.domain.config import settings
from datapilotflow.domain.knowledge import KnowledgeJob

# API uses domain models for validation
# API uses config for settings
```

## 📦 Dependencies

### DataPilotFlow Dependencies
- `datapilotflow-domain>=1.0.0` - Domain models and configuration
- `datapilotflow-infrastructure>=1.0.0` - Database access
- `datapilotflow-services>=1.0.0` - Business logic services
- `datapilotflow-rag-agent>=1.0.0` - RAG agent
- `datapilotflow-assistant-agent>=1.0.0` - Assistant agent

### External Dependencies
- `fastapi[standard]>=0.115.8` - FastAPI framework
- `uvicorn>=0.24.0` - ASGI server
- `langgraph>=1.0.2` - Agent workflows
- `langgraph-checkpoint-mongodb>=0.1.0` - State checkpoints
- `PyJWT>=2.10.0` - JWT handling
- `python-multipart>=0.0.20` - File uploads
- `pydantic>=2.10.6` - Data validation
- `loguru>=0.7.3` - Logging
- `opik>=1.9.11` - Observability

## 🚀 Installation

```bash
# Install all dependencies first
cd datapilotflow-domain && pip install -e .
cd ../datapilotflow-infrastructure && pip install -e .
cd ../datapilotflow-services && pip install -e .
cd ../datapilotflow-rag-agent && pip install -e .
cd ../datapilotflow-assistant-agent && pip install -e .

# Install API
cd ../datapilotflow-api && pip install -e .
```

## 📝 Usage Examples

### Start API Server
```bash
uv pip install -e ../datapilotflow-domain -e ../datapilotflow-infrastructure -e ../datapilotflow-services -e ../datapilotflow-processors -e ../datapilotflow-events -e ../datapilotflow-rag-agent ../datapilotflow-assistant-agent  -e .

python run_api_server.py
```

The server will be available at:
- **HTTP**: `http://0.0.0.0:65500`
- **WebSocket**: `ws://0.0.0.0:65500/ws`
- **API Docs**: `http://0.0.0.0:65500/docs`
- **Log File**: `logs/api.log`

### API Endpoints

**Knowledge Jobs**:
```bash
# Create job
POST /api/knowledge/jobs
{
    "name": "My Job",
    "source_id": "source_123",
    "config": {...}
}

# Get job
GET /api/knowledge/jobs/{job_id}

# List jobs
GET /api/knowledge/jobs
```

**Authentication**:
```bash
# Login
POST /api/auth/login
{
    "email": "user@example.com",
    "password": "password"
}

# Returns JWT token
```

**WebSocket (Assistant Agent)**:
```javascript
const ws = new WebSocket('ws://localhost:65500/ws/assistant');

ws.send(JSON.stringify({
    message: "What is RAG?",
    conversation_id: "conv_123"
}));

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    console.log(response);
};
```

## 🧪 Testing

```bash
cd datapilotflow-api
pytest tests/
```

## 📚 Related Packages

**Depends on**:
- ✅ All DataPilotFlow packages

**Used by**:
- ✅ Frontend applications
- ✅ External integrations
- ✅ API clients

## 🎯 Design Principles

1. **RESTful API**: Standard REST endpoints
2. **WebSocket Support**: Real-time communication
3. **Service Orchestration**: Coordinates all services
4. **Authentication**: JWT-based security
5. **Validation**: Pydantic request/response validation
6. **Service-Specific Logging**: Dedicated log file

## 🔧 Configuration

API uses configuration from `datapilotflow-domain`:

```python
from datapilotflow.domain.config import settings

# API Configuration
API_SERVER_HOST = settings.API_SERVER_HOST
API_SERVER_PORT = settings.API_SERVER_PORT
WEBSOCKET_TIMEOUT = settings.WEBSOCKET_TIMEOUT

# JWT Configuration
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
```

## 📖 Documentation

For more details:
- **API Server**: See `src/datapilotflow/api/server.py`
- **Routers**: See `src/datapilotflow/api/routers/`
- **Middleware**: See `src/datapilotflow/api/middleware/`
- **API Docs**: Available at `/docs` when server is running

## 🚀 Deployment

**Start API Server**:
```bash
python run_api_server.py
```

**Environment Variables**:
- Configure via `.env` file or environment variables
- See `datapilotflow-domain` config for all settings

**Infrastructure Requirements**:
- MongoDB (for data persistence)
- Milvus (for vector search)
- RabbitMQ (for event processing)

