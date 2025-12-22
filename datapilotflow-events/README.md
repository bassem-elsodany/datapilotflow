# DataPilotFlow Events

**Event-Driven Layer - RabbitMQ Event Publishing and Listening**

The `datapilotflow-events` package provides event-driven architecture capabilities using RabbitMQ. It handles event publishing, listening, and routing for asynchronous processing across the system.

## 📦 Package Overview

- **Version**: 1.0.0
- **Python**: >=3.11
- **Dependencies**: `datapilotflow-domain` + RabbitMQ client
- **Purpose**: Event-driven messaging, event listeners, and async processing

## 🏗️ Architecture Position

```
┌─────────────────────────────────────────┐
│     API, Services (Event Publishers)     │
└────────────────┬────────────────────────┘
                 │ publishes events
┌────────────────▼────────────────────────┐
│   datapilotflow-events                  │
│   (Event Listeners & Routing)           │
└────────────────┬────────────────────────┘
                 │ triggers
┌────────────────▼────────────────────────┐
│   datapilotflow-processors              │
│   (Event Processors)                    │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-services                │
│   (Business Logic)                       │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-infrastructure          │
│   (RabbitMQ Client)                      │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│      datapilotflow-domain               │
│      (Event Definitions)                 │
└─────────────────────────────────────────┘
```

**This package provides**:
- Event listener base classes
- Event routing and handling
- Async event processing
- Event-driven job processing

## 📁 Package Structure

```
datapilotflow-events/
├── src/datapilotflow/events/
│   ├── __init__.py
│   │
│   ├── events_listeners/         # Event listeners
│   │   ├── base_event_listener.py
│   │   ├── file_upload_event_listener.py
│   │   ├── job_event_listener.py
│   │   └── notification_event_listener.py
│   │
│   └── config.py                 # Event configuration
│
├── run_all_event_listeners.py    # Run all listeners
├── run_file_upload_event_listener.py
├── run_job_event_listener.py
├── run_notification_event_listener.py
│
├── tests/
├── pyproject.toml
└── README.md
```

## 🔑 Key Components

### 1. Base Event Listener

**BaseEventListener**: Abstract base class for all event listeners

**Features**:
- Automatic connection management
- Error handling and retry logic
- Graceful shutdown
- Event routing

**Usage**:
```python
from datapilotflow.events.events_listeners import BaseEventListener

class MyEventListener(BaseEventListener):
    async def handle_event(self, event_data: dict):
        # Process event
        await self.process_event(event_data)
    
    async def process_event(self, event_data: dict):
        # Your event processing logic
        pass
```

### 2. Job Event Listener

**JobEventListener**: Listens for knowledge job events

**Handles**:
- Job created events
- Job status update events
- Job completion events
- Job failure events

**Usage**:
```python
from datapilotflow.events.events_listeners import start_job_event_listener

# Start job event listener
await start_job_event_listener()
```

### 3. File Upload Event Listener

**FileUploadEventListener**: Listens for file upload events

**Handles**:
- File uploaded events
- File processing events
- File upload failures

**Usage**:
```python
from datapilotflow.events.events_listeners import start_file_upload_event_listener

# Start file upload event listener
await start_file_upload_event_listener()
```

### 4. Notification Event Listener

**NotificationEventListener**: Listens for notification events

**Handles**:
- Notification created events
- Notification delivery events

**Usage**:
```python
from datapilotflow.events.events_listeners import start_notification_event_listener

# Start notification event listener
await start_notification_event_listener()
```

## 🔗 How This Package Uses Lower Layers

### Uses Domain
```python
from datapilotflow.domain.events import (
    JobCreatedEvent,
    JobStatusUpdatedEvent,
    EventType
)
from datapilotflow.domain.config import settings
from datapilotflow.domain.logging import setup_service_logging

# Events use domain event definitions
event = JobCreatedEvent(job_id="123", ...)

# Use domain config
rabbitmq_host = settings.RABBITMQ_HOST

# Use domain logging
setup_service_logging("job-event-listener")
```

### Uses Infrastructure
```python
from datapilotflow.infrastructure.mq.client import (
    RabbitMQClient,
    get_rabbitmq_client
)

# Events use RabbitMQ client
connection = await get_rabbitmq_client()
client = RabbitMQClient(connection)
```

### Uses Processors
```python
from datapilotflow.processors.knowledge_job import KnowledgeJobEventProcessor

# Event listeners trigger processors
processor = KnowledgeJobEventProcessor()
await processor.process_job_created_event(event_data)
```

### Uses Services
```python
from datapilotflow.services.knowledge import KnowledgeJobService
from datapilotflow.services.events_publisher import JobEventPublisher

# Event listeners use services
job_service = KnowledgeJobService()
event_publisher = JobEventPublisher()
```

## 🔗 How Other Packages Use This Package

### Services Layer (Publishes Events)
```python
from datapilotflow.services.events_publisher import JobEventPublisher

# Services publish events
publisher = JobEventPublisher()
await publisher.publish_job_created(job_id, job_data)
```

### API Layer (Can Publish Events)
```python
from datapilotflow.services.events_publisher import JobEventPublisher

# API can publish events through services
# (API → Services → Event Publisher)
```

## 📦 Dependencies

### DataPilotFlow Dependencies
- `datapilotflow-domain>=1.0.0` - Event definitions and configuration

### External Dependencies
- `aio-pika>=9.5.5` - RabbitMQ async client
- `pydantic>=2.10.6` - Data validation
- `pydantic-settings>=2.7.1` - Settings management
- `loguru>=0.7.3` - Logging

## 🚀 Installation

```bash
cd datapilotflow-events
pip install -e .
```

## 📝 Usage Examples

### Start All Event Listeners
```bash
python run_all_event_listeners.py
```

### Start Individual Listeners
```bash
# Job event listener
python run_job_event_listener.py

# File upload event listener
python run_file_upload_event_listener.py

# Notification event listener
python run_notification_event_listener.py
```

### Custom Event Listener
```python
from datapilotflow.events.events_listeners import BaseEventListener

class CustomEventListener(BaseEventListener):
    async def handle_event(self, event_data: dict):
        # Process your event
        await self.process_custom_event(event_data)
    
    async def process_custom_event(self, event_data: dict):
        # Your logic here
        pass

# Start listener
listener = CustomEventListener()
await listener.start()
```

## 🧪 Testing

```bash
cd datapilotflow-events
pytest tests/
```

**Test Requirements**:
- RabbitMQ instance (or test container)

## 📚 Related Packages

**Depends on**:
- ✅ `datapilotflow-domain` - Uses event definitions and config

**Used by**:
- ✅ `datapilotflow-processors` - Triggered by events
- ✅ `datapilotflow-services` - Publishes events

## 🎯 Design Principles

1. **Event-Driven**: Asynchronous event processing
2. **Separation of Concerns**: Listeners separate from processors
3. **Error Handling**: Robust error handling and retry logic
4. **Graceful Shutdown**: Clean shutdown handling
5. **Service-Specific Logging**: Each listener has its own log file

## 🔧 Configuration

Events use configuration from `datapilotflow-domain`:

```python
from datapilotflow.domain.config import settings

# RabbitMQ Configuration
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASS = settings.RABBITMQ_PASS
RABBITMQ_VHOST = settings.RABBITMQ_VHOST
```

## 📖 Documentation

For more details:
- Event Listeners: See `src/datapilotflow/events/events_listeners/`
- Event Configuration: See `src/datapilotflow/events/config.py`
- Run Scripts: See `run_*.py` files

## 🚦 Event Flow

```
1. Service publishes event → RabbitMQ
2. Event listener receives event
3. Event listener triggers processor
4. Processor processes event
5. Processor updates state via services
6. Services may publish new events
```

## 📝 Logging

Each event listener writes to its own log file:
- `logs/job-event-listener.log`
- `logs/file-upload-event-listener.log`
- `logs/notification-event-listener.log`
- `logs/all-event-listeners.log`
