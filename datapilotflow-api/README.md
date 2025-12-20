# DataPilotFlow API

REST API exposure layer for DataPilotFlow - provides a FastAPI-based interface for UI applications and external integrations.

## Features

- **Agent Integration**: Query RAG and Assistant agents via REST endpoints
- **Conversation Management**: Full CRUD operations for conversations
- **Knowledge Management**: Manage knowledge sources, search documents
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`
- **WebSocket Support**: Real-time streaming responses (planned)
- **CORS Support**: Configured for web applications

## Installation

```bash
pip install -e /path/to/datapilotflow-api
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn datapilotflow.api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn datapilotflow.api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health
- `GET /api/v1/health/` - Health check

### Agents
- `POST /api/v1/agents/rag/query` - Query RAG agent
- `POST /api/v1/agents/assistant/message` - Send message to Assistant agent

### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{conversation_id}` - Get conversation
- `GET /api/v1/conversations/{conversation_id}/history` - Get conversation history
- `DELETE /api/v1/conversations/{conversation_id}` - Delete conversation

### Knowledge
- `POST /api/v1/knowledge/sources` - Create knowledge source
- `GET /api/v1/knowledge/sources/{source_id}` - Get knowledge source
- `POST /api/v1/knowledge/search` - Search knowledge base
- `POST /api/v1/knowledge/upload` - Upload document

## Architecture

```
datapilotflow-api/
├── src/datapilotflow/api/
│   ├── __init__.py           # Package exports
│   ├── app.py                # FastAPI application factory
│   ├── main.py               # Entry point
│   └── routers/              # API route handlers
│       ├── health.py         # Health endpoints
│       ├── agents.py         # Agent endpoints
│       ├── conversations.py  # Conversation endpoints
│       └── knowledge.py      # Knowledge endpoints
└── tests/                    # Test suite
```

## Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- datapilotflow-domain: Domain models
- datapilotflow-agents: Agent implementations
- datapilotflow-services: Business logic services

## Environment Variables

Configure via `datapilotflow.domain.config.settings`:

- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: "*")
- `LOG_LEVEL`: Logging level (default: "INFO")

## WebSocket Support (Planned)

Real-time streaming for:
- RAG query results with intermediate steps
- Assistant agent responses with streaming text
- Knowledge base ingestion progress

## Integration with Services

### Agent Queries
```python
from datapilotflow.agents import RAGAgentService

rag_service = RAGAgentService()
results = await rag_service.query(request)
```

### Conversation Management
```python
from datapilotflow.services.conversation import conversation_service

conversation = await conversation_service.create(request)
```

### Knowledge Base
```python
from datapilotflow.services.knowledge import knowledge_service

sources = await knowledge_service.list_sources(user_id)
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### API Documentation
Navigate to `http://localhost:8000/docs` for interactive Swagger UI

## License

MIT
