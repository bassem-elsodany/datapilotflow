# Event Listener Startup Scripts - Complete Index

## 📍 Location
All event listener startup scripts have been migrated from the backend monolith to the dedicated events package:

```
datapilotflow-events/
├── run_job_event_listener.py
├── run_file_upload_event_listener.py
├── run_notification_event_listener.py
├── run_all_event_listeners.py
└── README_STARTUP.md
```

## 📝 Why They Moved

Previously, event listener startup scripts were located at the backend root:
- `backend/run_job_event_listener.py`
- `backend/run_file_upload_event_listener.py`
- `backend/run_notification_event_listener.py`
- `backend/run_all_event_listeners.py`

These scripts were importing from the monolith (`src.services.events_listeners`), but after the architecture refactoring:

1. **Event Listeners Extracted** - Moved from `datapilotflow-services` to `datapilotflow-events`
2. **Package Independence** - `datapilotflow-events` is now a standalone package
3. **Startup Visibility** - Startup scripts belong with the package they serve
4. **Clean Organization** - Each package contains its startup entry points

## 🚀 Available Scripts

### Individual Listener Scripts

#### `run_job_event_listener.py`
- **Purpose**: Process job execution events
- **Event Type**: `knowledge_job_action_requested`
- **Queue**: `knowledge_job_action_requested_queue`
- **Usage**: `python run_job_event_listener.py`
- **Output**: `logs/job_event_listener.log`

#### `run_file_upload_event_listener.py`
- **Purpose**: Process file upload events for RAG
- **Event Type**: `file_upload`
- **Queue**: `rag_file_upload_queue`
- **Usage**: `python run_file_upload_event_listener.py`
- **Output**: `logs/file_upload_event_listener.log`

#### `run_notification_event_listener.py`
- **Purpose**: Process notification events
- **Event Type**: `NewNotification`
- **Queue**: `notification_queue`
- **Usage**: `python run_notification_event_listener.py`
- **Output**: `logs/notification_event_listener.log`

### Orchestrator Script

#### `run_all_event_listeners.py`
- **Purpose**: Start all event listeners in separate processes
- **Features**:
  - Concurrent process management
  - Health monitoring (checks every 5 minutes)
  - Auto-restart on crash
  - Graceful shutdown with SIGTERM
  - Force kill with SIGKILL after 3 signals
- **Usage**: `python run_all_event_listeners.py`
- **Output**: `logs/all_event_listeners.log`
- **Log Files**:
  - `logs/job_event_listener.log`
  - `logs/file_upload_event_listener.log`
  - `logs/notification_event_listener.log`

## 🔧 Configuration

All scripts use configuration from:
- **Source**: `datapilotflow-events/src/datapilotflow/events/config.py`
- **Environment**: `datapilotflow-events/.env`

### Required Environment Variables
```bash
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=skillpilot
RABBITMQ_PASS=skillpilot123
RABBITMQ_VHOST=/

# MongoDB Configuration
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=datapilotflow
MONGO_USER=root
MONGO_PASS=root

# Vector DB Configuration
VECTOR_DB_HOST=localhost
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=root
VECTOR_DB_PASSWORD=Milvus

# Tracing (Optional)
AGENT_TRACING_ENABLED=false
AGENT_TRACING_URL=http://localhost:5173/api
AGENT_TRACING_API_KEY=your-api-key
```

## 📦 Package Dependencies

These startup scripts require:
- `datapilotflow-events` (main package)
- `datapilotflow-domain` (event constants, business logic)
- `datapilotflow-services` (processors that handle events)
- `datapilotflow-processors` (event processing implementations)
- RabbitMQ (event message broker)
- MongoDB (data persistence)
- Milvus (vector database)

## 📍 Import Paths

The scripts import from the events package:

```python
# Instead of old backend path:
# from src.services.events_listeners import start_job_event_listener

# Now uses:
from datapilotflow.events.events_listeners import start_job_event_listener
```

## ✅ Compilation Status

All scripts have been verified to compile correctly:
```
✓ run_job_event_listener.py - OK
✓ run_file_upload_event_listener.py - OK
✓ run_notification_event_listener.py - OK
✓ run_all_event_listeners.py - OK
```

## 🔄 Migration Path

### Old Way (Backend Monolith)
```bash
cd backend
python run_job_event_listener.py
# Imports from: src.services.events_listeners
```

### New Way (Events Package)
```bash
cd datapilotflow-events
python run_job_event_listener.py
# Imports from: datapilotflow.events.events_listeners
```

## 📊 Architecture

```
Backend Monolith (Legacy)
├── run_*_event_listener.py (DEPRECATED)
└── src/services/events_listeners/ (MOVED)

datapilotflow-events (New)
├── run_job_event_listener.py ✅
├── run_file_upload_event_listener.py ✅
├── run_notification_event_listener.py ✅
├── run_all_event_listeners.py ✅
└── src/datapilotflow/events/events_listeners/ ✅
    ├── base_event_listener.py
    ├── job_event_listener.py
    ├── file_upload_event_listener.py
    └── notification_event_listener.py
```

## 🎯 Why This Organization?

1. **Package Responsibility** - Startup scripts belong with the package they start
2. **Visibility** - Easier to discover how to run the events service
3. **Independence** - Events package can be deployed standalone
4. **Single Purpose** - `datapilotflow-events` = listener exposure layer
5. **Clean Separation** - Domain (constants), Services (publishers), Events (listeners)

## 📚 Related Documentation

- **Startup Scripts Guide**: See `datapilotflow-events/README_STARTUP.md`
- **Full Architecture**: See `EVENT_ARCHITECTURE_REFACTORING.md`
- **Quick Reference**: See `QUICK_REFERENCE.md`
- **Completion Status**: See `COMPLETION_STATUS.md`

## ⚙️ Advanced Usage

### Running with Custom Python Interpreter
```bash
/path/to/python/bin/python run_all_event_listeners.py
```

### Running in Background
```bash
nohup python run_all_event_listeners.py > events.log 2>&1 &
```

### Running with Systemd
Create `/etc/systemd/system/datapilotflow-events.service`:
```ini
[Unit]
Description=DataPilotFlow Event Listeners
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/datapilotflow-events
ExecStart=/path/to/python/bin/python run_all_event_listeners.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Running with Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY datapilotflow-events /app
RUN pip install -e .
CMD ["python", "run_all_event_listeners.py"]
```

## 🔍 Troubleshooting

### Script Not Found?
```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow/datapilotflow-events
python run_job_event_listener.py
```

### Import Error: "No module named 'datapilotflow'"?
1. Install the events package: `pip install -e datapilotflow-events`
2. Or ensure Python path includes: `PYTHONPATH=datapilotflow-events/src`

### RabbitMQ Connection Error?
1. Check RabbitMQ is running: `localhost:5672`
2. Verify credentials in `.env` file
3. Check network connectivity

### MongoDB Connection Error?
1. Check MongoDB is running: `localhost:27017`
2. Verify credentials in `.env` file
3. Check database permissions

## 📈 Monitoring

### View Running Processes
```bash
ps aux | grep "run_.*_event_listener"
```

### View Logs
```bash
# Real-time log
tail -f logs/all_event_listeners.log

# All logs
ls -la logs/
```

### Check Health
The `run_all_event_listeners.py` script automatically:
- Monitors each listener every 5 minutes
- Logs listener status
- Restarts crashed listeners
- Handles graceful shutdown
