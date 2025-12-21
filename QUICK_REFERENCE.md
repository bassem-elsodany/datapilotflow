# Event Architecture Quick Reference

## 🎯 Core Concept

**Separation of Concerns**: Domain owns constants, Events owns listeners, Services owns publishers.

## 📁 Package Locations

| Package | Location | Responsibility |
|---------|----------|-----------------|
| **Constants** | `datapilotflow-domain/src/datapilotflow/domain/events/constants.py` | All event configuration (exchanges, queues, types, categories) |
| **Listeners** | `datapilotflow-events/src/datapilotflow/events/events_listeners/` | Listen to and process RabbitMQ events |
| **Publishers** | `datapilotflow-services/src/datapilotflow/services/events_publisher/` | Publish events to RabbitMQ |
| **API Config** | `datapilotflow-api/src/datapilotflow/api/config.py` | API server configuration |
| **Events Config** | `datapilotflow-events/src/datapilotflow/events/config.py` | Event listeners configuration |
| **Domain Config** | `datapilotflow-domain/src/datapilotflow/domain/config.py` | MCP + Business logic configuration |

## 🚀 Running Event Listeners

### All Listeners (Recommended)
```bash
cd datapilotflow-events
python run_all_event_listeners.py
```

### Individual Listeners
```bash
cd datapilotflow-events
python run_job_event_listener.py
python run_file_upload_event_listener.py
python run_notification_event_listener.py
```

## 📦 Importing Event Stuff

### Import Event Constants (from domain)
```python
from datapilotflow.domain.events import (
    JOB_EVENTS_EXCHANGE,
    FILE_UPLOAD_EVENTS_QUEUE,
    EventTypes,
    EventCategories,
)
```

### Import Listener Functions (from events)
```python
from datapilotflow.events.events_listeners import (
    start_job_event_listener,
    start_file_upload_event_listener,
    start_notification_event_listener,
)
```

### Import Publisher Functions (from services)
```python
from datapilotflow.services.events_publisher import (
    get_job_event_publisher,
    get_file_upload_event_publisher,
    get_notification_event_publisher,
)
```

## 🔧 Configuration

### Environment Files
- `datapilotflow-events/.env` - Events service config
- `datapilotflow-api/.env` - API service config
- `datapilotflow-rag-agent/.env` - MCP server config

### Key Variables (Events)
```bash
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=skillpilot
RABBITMQ_PASS=skillpilot123

MONGO_HOST=localhost
MONGO_PORT=27017
```

## 📋 Event Types

```python
# Define what event types exist
EventTypes.KNOWLEDGE_JOB_ACTION_REQUESTED
EventTypes.FILE_UPLOAD
EventTypes.NEW_NOTIFICATION

# Define what categories exist
EventCategories.JOB
EventCategories.FILE_UPLOAD
EventCategories.NOTIFICATION
```

## 🔌 RabbitMQ Configuration

### Job Events
```
Exchange: job_events_exchange
Queue: knowledge_job_action_requested_queue
Routing Key: knowledge.job.action.requested
DLQ: job_events_dlq_queue
```

### File Upload Events
```
Exchange: rag_file_upload_exchange
Queue: rag_file_upload_queue
Routing Key: rag_file_upload_routing_key
DLQ: rag_file_upload_dlq_queue
```

### Notification Events
```
Exchange: notification_events_exchange
Queue: notification_queue
Routing Key: notification.new
DLQ: notification_dlq_queue
```

### Timeline Events
```
Exchange: timeline_events_exchange
Queue: timeline_events_queue
Routing Key: timeline.*
DLQ: timeline_events_dlq_queue
```

## ✅ Architecture Benefits

1. **Single Source of Truth** - Event constants defined once in domain
2. **Clear Separation** - Listeners in events, publishers in services
3. **Independent Deployment** - Each package has own config and startup
4. **Scalability** - Run multiple listener instances independently
5. **Maintainability** - Changes to events affect one file

## 📊 Package Dependency Graph

```
datapilotflow-domain
    ↓ imports constants
datapilotflow-events
    ↓ listens to
RabbitMQ
    ↑ publishes to
datapilotflow-services
    ↓ imports constants
datapilotflow-api
    ↓ depends on
datapilotflow-domain (business logic)
```

## 🐛 Troubleshooting

### Listener not starting?
1. Check `datapilotflow-events/.env` exists and has RabbitMQ config
2. Verify RabbitMQ is running: `localhost:5672`
3. Check logs: `logs/job_event_listener.log`

### Import errors?
1. Ensure `datapilotflow-events` is installed
2. Use correct import: `from datapilotflow.events.events_listeners import ...`
3. Check Python path includes package source

### Event constants not found?
1. Import from domain: `from datapilotflow.domain.events import ...`
2. Not from services (services re-exports for backward compatibility)

## 📚 Documentation

- **Full Architecture**: See `EVENT_ARCHITECTURE_REFACTORING.md`
- **Startup Scripts**: See `datapilotflow-events/README_STARTUP.md`
- **Completion Status**: See `COMPLETION_STATUS.md`
