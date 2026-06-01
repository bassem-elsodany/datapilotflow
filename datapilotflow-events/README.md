# datapilotflow-events

**Event listener service — consumes RabbitMQ messages and triggers the document processing pipeline.**

This package runs as a standalone background process. It listens on RabbitMQ queues and dispatches incoming events to the appropriate processors. It has no HTTP interface.

---

## Responsibility

- Listen for job events, file upload events, and notification events from RabbitMQ
- Dispatch each event to the correct processor
- Maintain independent configuration for RabbitMQ and MongoDB connections

---

## Package Structure

```
src/datapilotflow/events/
├── config.py                              # EventsSettings — independent configuration
└── events_listeners/
    ├── base_event_listener.py             # Base listener with RabbitMQ connection setup
    ├── job_event_listener.py              # Listens on job queue → triggers KnowledgeJobProcessor
    ├── file_upload_event_listener.py      # Listens on file upload queue → triggers FileUploadProcessor
    └── notification_event_listener.py     # Listens on notification queue → delivers notifications
```

---

## Event Types

| Event | Routing Key | Triggered By | Handled By |
|-------|-------------|-------------|------------|
| Job Created | `job.created` | API / Services | `job_event_listener` |
| Job Started | `job.started` | Processor | `job_event_listener` |
| Job Completed | `job.completed` | Processor | `job_event_listener` |
| File Uploaded | `file.uploaded` | API | `file_upload_event_listener` |
| Notification | `notification.*` | Services | `notification_event_listener` |

---

## Running the Service

```bash
cd datapilotflow-events
python run_event_listeners.py
```

The service connects to RabbitMQ on startup and begins consuming from all configured queues. It runs indefinitely until stopped.

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
aio-pika >= 9.5.5
pydantic >= 2.10.6
pydantic-settings >= 2.7.1
loguru >= 0.7.3
```

Note: this package intentionally does not depend on `datapilotflow-infrastructure` or `datapilotflow-services` directly. It uses local imports inside listener methods to avoid circular dependencies with the processors layer.

---

## Installation

```bash
cd datapilotflow-events
uv pip install -e ../datapilotflow-domain -e .
```

---

## Dependency Position

```
datapilotflow-events  -->  datapilotflow-domain
                      -->  (local imports) datapilotflow-processors
```
