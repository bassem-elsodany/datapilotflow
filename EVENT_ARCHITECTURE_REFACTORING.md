# Event Architecture Refactoring - Complete

## Summary of Changes

The DataPilotFlow event-driven architecture has been refactored to separate concerns across dedicated packages with a clear single source of truth for event constants and configuration.

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────┐
│  datapilotflow-domain (Single Source of Truth)  │
│  - domain/events/constants.py                    │
│  - domain/config.py (MCP, Business Logic)        │
└─────────────────────────────────────────────────┘
          ▲                                    ▲
          │                                    │
          │ imports event constants            │ imports business logic
          │                                    │
    ┌─────┴──────┐                     ┌───────┴──────┐
    │             │                     │              │
    ▼             ▼                     ▼              ▼
┌─────────┐  ┌──────────┐  ┌─────────────────┐  ┌──────────────┐
│  Events │  │ Services │  │  API (Separate) │  │  MCP (RAG)   │
│Listeners│  │Publishers│  │   Package       │  │   Package    │
└─────────┘  └──────────┘  └─────────────────┘  └──────────────┘
```

## Package Organization

### 1. **datapilotflow-domain**
**Single source of truth for event system**

- **Location**: `datapilotflow-domain/src/datapilotflow/domain/events/constants.py`
- **Responsibility**: Define all event constants, types, and configuration classes
- **Exports**:
  - Exchange/Queue/Routing Key constants (JOB_*, FILE_UPLOAD_*, NOTIFICATION_*, TIMELINE_*)
  - DLQ (Dead Letter Queue) constants
  - Event type enums (EventTypes)
  - Event category enums (EventCategories)
  - Configuration classes (RetryConfig, MessageHeaders)
- **Usage**: All packages import event constants from here

```python
# Example: Event Constants in domain
JOB_EVENTS_EXCHANGE = "job_events_exchange"
JOB_EVENTS_QUEUE = "knowledge_job_action_requested_queue"
JOB_EVENTS_ROUTING_KEY = "knowledge.job.action.requested"

class EventTypes:
    KNOWLEDGE_JOB_ACTION_REQUESTED = "knowledge_job_action_requested"
    FILE_UPLOAD = "file_upload"
```

### 2. **datapilotflow-events**
**Event listeners only - listens to RabbitMQ events**

- **Location**: `datapilotflow-events/src/datapilotflow/events/`
- **Responsibility**: Listen to RabbitMQ events and process them
- **Structure**:
  - `events_listeners/base_event_listener.py` - Base class for all listeners
  - `events_listeners/job_event_listener.py` - Processes job events
  - `events_listeners/file_upload_event_listener.py` - Processes file upload events
  - `events_listeners/notification_event_listener.py` - Processes notification events
  - `config.py` - Events package configuration (RabbitMQ, MongoDB, Vector DB)
- **Startup Scripts**:
  - `run_job_event_listener.py`
  - `run_file_upload_event_listener.py`
  - `run_notification_event_listener.py`
  - `run_all_event_listeners.py` - Orchestrates all listeners in separate processes
- **Public API**:
  ```python
  from datapilotflow.events.events_listeners import (
      start_job_event_listener,
      start_file_upload_event_listener,
      start_notification_event_listener,
  )
  ```

### 3. **datapilotflow-services**
**Event publishers and business logic services**

- **Location**: `datapilotflow-services/src/datapilotflow/services/`
- **Responsibility**: Publish events and implement business logic
- **Structure**:
  - `events_publisher/base_event_publisher.py` - Base class for publishers
  - `events_publisher/job_event_publisher.py` - Publishes job events
  - `events_publisher/file_upload_event_publisher.py` - Publishes file upload events
  - `events_publisher/notification_event_publisher.py` - Publishes notification events
  - `events/__init__.py` - Re-exports domain event constants (backward compatibility)
- **Public API**:
  ```python
  from datapilotflow.services.events_publisher import (
      get_job_event_publisher,
      get_file_upload_event_publisher,
      get_notification_event_publisher,
  )
  ```
- **Note**: Event constants are imported from domain and re-exported for backward compatibility

### 4. **datapilotflow-api**
**API exposure layer with independent configuration**

- **Location**: `datapilotflow-api/src/datapilotflow/api/`
- **Responsibility**: REST API with business logic from domain
- **Configuration**: `api/config.py` with:
  - API-specific settings (host, port, websocket timeout)
  - Infrastructure settings (MongoDB, Vector DB, JWT)
  - Business logic settings (RAG_TOP_K, tracing)

### 5. **datapilotflow-rag-agent**
**MCP (Model Context Protocol) server with domain configuration**

- **Location**: `datapilotflow-rag-agent/src/datapilotflow/rag_agent/`
- **Responsibility**: MCP server implementation
- **Configuration**: Uses `datapilotflow.domain.config` with MCP_* fields:
  - MCP_SERVER_HOST, MCP_SERVER_PORT
  - MCP_SERVER_NAME, MCP_ENABLED_TOOLS
  - MCP_LOG_LEVEL, MCP_WORKER_THREADS

## Key Changes Made

### 1. **Constants Consolidation**
- ✅ Created `datapilotflow-domain/src/datapilotflow/domain/events/constants.py`
- ✅ Removed duplicate constants from `datapilotflow-services/src/datapilotflow/services/events/constants.py`
- ✅ Removed duplicate constants from `backend/src/services/events/constants.py`
- ✅ Updated all imports to use domain constants

### 2. **Listeners Organization**
- ✅ Moved all listener implementations from `datapilotflow-services` to `datapilotflow-events`
- ✅ Moved listener startup functions to `datapilotflow-events`
- ✅ Created startup scripts in `datapilotflow-events` root:
  - `run_job_event_listener.py`
  - `run_file_upload_event_listener.py`
  - `run_notification_event_listener.py`
  - `run_all_event_listeners.py`

### 3. **Publishers Isolation**
- ✅ Kept all publisher implementations in `datapilotflow-services/events_publisher/`
- ✅ Maintained publisher getter functions

### 4. **Configuration Distribution**
- ✅ Created `datapilotflow-api/src/datapilotflow/api/config.py`
- ✅ Created `datapilotflow-events/src/datapilotflow/events/config.py`
- ✅ Updated `datapilotflow-domain/src/datapilotflow/domain/config.py` with MCP fields
- ✅ Each package has independent `.env` file

### 5. **Import Updates**
- ✅ API package imports from `datapilotflow.api.config`
- ✅ Events package imports from `datapilotflow.events.config`
- ✅ Services re-exports constants from domain for backward compatibility
- ✅ MCP server imports from `datapilotflow.domain.config`

## Deployment Independence

Each exposure package can now be deployed independently:

### API Service
```bash
cd datapilotflow-api
# Uses datapilotflow-api/.env
python run_api_server.py
```

### Events Service
```bash
cd datapilotflow-events
# Uses datapilotflow-events/.env
python run_all_event_listeners.py  # All listeners
# OR individual listeners:
python run_job_event_listener.py
python run_file_upload_event_listener.py
python run_notification_event_listener.py
```

### MCP Server
```bash
cd datapilotflow-rag-agent
# Uses datapilotflow-rag-agent/.env
python -m datapilotflow.rag_agent.mcp.cli.run_server
```

## Environment Files

### `.env` Locations
- `datapilotflow-api/.env` - API server configuration
- `datapilotflow-events/.env` - Events listeners configuration
- `datapilotflow-rag-agent/.env` - MCP server configuration
- `backend/.env` - Backend monolith configuration (legacy)

### Configuration Inheritance
- **Business Logic Settings** (shared): Defined in domain, loaded by each package from its `.env`
  - RAG_TOP_K, RAG_SIMILARITY_THRESHOLD
  - AGENT_TRACING_ENABLED, AGENT_TRACING_*
- **Infrastructure Settings** (independent): Each package declares its own
  - API: API_SERVER_*, MONGO_*, VECTOR_DB_*, JWT_*
  - Events: RABBITMQ_*, MONGO_*, VECTOR_DB_*
  - MCP: MCP_SERVER_* (from domain)

## Backward Compatibility

The refactoring maintains backward compatibility:
- Services package re-exports domain event constants
- Domain config keeps deprecated fields with warnings (optional)
- Old startup scripts in backend still work (they import from monolith src/)

## Files Changed Summary

### Created Files (5)
1. `datapilotflow-domain/src/datapilotflow/domain/events/constants.py` - Event constants
2. `datapilotflow-api/src/datapilotflow/api/config.py` - API configuration
3. `datapilotflow-events/src/datapilotflow/events/config.py` - Events configuration
4. `datapilotflow-events/run_all_event_listeners.py` - Orchestrator startup script
5. `datapilotflow-events/run_*_event_listener.py` (4 scripts) - Individual listener startup scripts

### Deleted Files (3)
1. `datapilotflow-services/src/datapilotflow/services/events/constants.py` - Duplicate
2. `backend/src/services/events/constants.py` - Duplicate
3. `datapilotflow-rag-agent/src/datapilotflow/rag_agent/mcp/config.py` - Duplicate MCP config

### Modified Imports (15+)
- datapilotflow-domain: Added MCP fields to config
- datapilotflow-services: Updated to import constants from domain
- datapilotflow-events: Updated to use events package config
- datapilotflow-api: Updated 10 routers to import from api config
- datapilotflow-rag-agent: Updated MCP imports from domain config

## Architecture Benefits

1. **Separation of Concerns**
   - Events layer: Listeners only
   - Services layer: Publishers and business logic
   - Domain layer: Shared knowledge and constants

2. **Deployment Independence**
   - Each package has its own configuration and startup scripts
   - Can be deployed to different servers/containers
   - Can scale independently

3. **Configuration Clarity**
   - Business logic settings centralized in domain
   - Infrastructure settings localized to each package
   - Clear, explicit dependencies

4. **Single Source of Truth**
   - Event constants in domain (not duplicated)
   - Configuration structure follows package responsibility
   - Easy to track and update event system

5. **Maintainability**
   - Changes to event constants update once in domain
   - Each package is responsible for its infrastructure
   - Clear module organization and relationships
