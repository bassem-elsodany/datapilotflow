# DataPilotFlow Events

RabbitMQ-based event system for DataPilotFlow.

Contains:
- Event publishers for asynchronous publishing
- Event listeners for consuming events
- Event schemas and models
- RabbitMQ connection management

## Installation

```bash
pip install datapilotflow-events
```

## Usage

```python
from datapilotflow.events import EventPublisher, EventListener

# Publish events
publisher = EventPublisher()
await publisher.publish_job_created(job_id, user_id)

# Listen for events
listener = EventListener()
await listener.listen_for_job_events()
```

## License

MIT
