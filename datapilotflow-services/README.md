# datapilotflow-services

**Business logic layer — service orchestration, authentication, event publishing, and WebSocket management.**

This package sits between the infrastructure layer (data access) and the application layers (API, agents, processors). It owns all business rules and coordinates operations across DAOs, event publishers, and external integrations.

---

## Responsibility

- Orchestrate knowledge ingestion workflows
- Manage authentication, JWT issuance, and role-based access control
- Publish domain events to RabbitMQ
- Manage conversation history
- Handle file uploads and Confluence integration
- Provide WebSocket notification delivery
- Manage LLM model provider configuration
- Register and manage tools and MCP servers

---

## Package Structure

```
src/datapilotflow/services/
├── auth/
│   ├── auth_service.py                    # Login, JWT issuance, token validation
│   └── admin_initialization_service.py    # Default admin user seeding on startup
├── users/
│   ├── user_service.py                    # User CRUD and role assignment
│   └── roles_service.py                   # Role management and system role init
├── knowledge/
│   ├── knowledge_job_service.py           # Job lifecycle management
│   ├── knowledge_source_service.py        # Source configuration management
│   ├── knowledge_ingestion_service.py     # Ingestion orchestration
│   ├── job_timeline_service.py            # Job step timeline tracking
│   ├── document_splitter_service.py       # Splitter configuration service
│   ├── vectordb_collection_service.py     # Vector collection management
│   └── llm_content_filter_service.py      # LLM content filter management
├── conversation/
│   └── conversation_history_service.py    # Multi-turn conversation storage
├── confluence/
│   ├── confluence_credential_service.py   # Confluence credential management
│   └── confluence_metadata_service.py     # Space and page metadata
├── events_publisher/
│   ├── base_event_publisher.py            # Base publisher with RabbitMQ connection
│   ├── job_event_publisher.py             # Job lifecycle event publishing
│   ├── file_upload_event_publisher.py     # File upload event publishing
│   └── notification_event_publisher.py    # Notification event publishing
├── notification/
│   ├── notification_event_service.py      # Notification creation and persistence
│   ├── notification_listener_service.py   # Listens for notification events
│   ├── notification_websocket_service.py  # Delivers notifications over WebSocket
│   └── job_notification_helper.py         # Job-specific notification helpers
├── file_management/
│   └── file_upload_service.py             # File upload handling and tracking
├── model_provider/
│   ├── model_provider_service.py          # LLM provider CRUD
│   └── model_provider_initialization_service.py  # Default provider seeding
├── agent/
│   └── agent_service.py                   # Agent configuration management
├── tool/
│   ├── tool_service.py                    # Tool registration and management
│   └── mcp_server_service.py              # MCP server registry
├── vectordb/
│   └── collection_service.py              # Vector collection service
└── websocket/                             # WebSocket connection management
```

---

## Key Services

### Authentication

```python
from datapilotflow.services.auth.auth_service import AuthService

auth = AuthService()
token = auth.login(username="admin", password="admin123")
user = auth.validate_token(token)
```

### Knowledge Jobs

```python
from datapilotflow.services.knowledge.knowledge_job_service import KnowledgeJobService

service = KnowledgeJobService()
job = service.create_job(source_id=source_id)
service.update_job_status(job_id, "COMPLETED")
```

### Event Publishing

```python
from datapilotflow.services.events_publisher.job_event_publisher import JobEventPublisher

publisher = JobEventPublisher()
await publisher.publish_job_created(job_id=job_id)
await publisher.publish_job_completed(job_id=job_id)
```

### Notifications via WebSocket

```python
from datapilotflow.services.notification.notification_websocket_service import NotificationWebSocketService

ws_service = NotificationWebSocketService()
await ws_service.send_to_user(user_id=user_id, message=notification)
```

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
datapilotflow-infrastructure >= 1.0.0
langchain-core >= 1.0.0
litellm >= 1.79.0
PyJWT >= 2.10.0
passlib >= 1.7.4
bcrypt >= 4.0.1
python-multipart >= 0.0.20
pydantic >= 2.10.6
loguru >= 0.7.3
```

---

## Installation

```bash
cd datapilotflow-services
uv pip install -e ../datapilotflow-domain -e ../datapilotflow-infrastructure -e .
```

---

## Dependency Position

```
datapilotflow-api             --|
datapilotflow-processors      --|-->  datapilotflow-services  -->  datapilotflow-infrastructure  -->  datapilotflow-domain
datapilotflow-rag-agent       --|
datapilotflow-assistant-agent --|
```
