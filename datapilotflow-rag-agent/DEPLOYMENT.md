# MCP RAG Agent Deployment Guide

This document outlines all packages and dependencies required to deploy **only** the MCP RAG Agent service.

## Required DataPilotFlow Packages

### 1. **datapilotflow-rag-agent** (Main Package)
- **Location**: `datapilotflow-rag-agent/`
- **Purpose**: RAG agent implementation with MCP server
- **Entry Point**: `run_rag_mcp_server.py`

### 2. **datapilotflow-domain** (Required Dependency)
- **Location**: `datapilotflow-domain/`
- **Purpose**: Core domain models, configuration, and logging utilities
- **Why Required**: 
  - Configuration settings (`datapilotflow.domain.config`)
  - Logging setup (`datapilotflow.domain.logging`)
  - Domain models used by RAG agent

### 3. **datapilotflow-infrastructure** (Required Dependency)
- **Location**: `datapilotflow-infrastructure/`
- **Purpose**: Database and infrastructure access
- **Why Required**:
  - Vector database client (`datapilotflow.infrastructure.vectordb.milvus.client`)
  - MongoDB client (for conversation history, if used)
  - Message queue client (if needed for async operations)

### 4. **datapilotflow-services** (Required Dependency)
- **Location**: `datapilotflow-services/`
- **Purpose**: Business logic services
- **Why Required**:
  - Conversation history service (`datapilotflow.services.conversation.conversation_history_service`)
  - Model provider service (`datapilotflow.services.model_provider.model_provider_service`)
  - Other services used by RAG workflow

## External Python Dependencies

### Core Dependencies (from rag-agent)
```python
fastmcp>=0.4.0          # MCP server framework
langgraph>=1.0.2        # Agent workflow orchestration
langchain-core>=1.0.0   # LangChain core
langchain-community>=0.0.1  # LangChain community integrations
litellm>=1.79.0         # LLM provider abstraction
opik>=1.9.11            # Observability/tracing
loguru>=0.7.3           # Logging
pydantic>=2.10.6        # Data validation
pydantic-settings>=2.0.0  # Settings management
```

### Transitive Dependencies (from domain)
```python
python-dateutil>=2.8.2
email-validator>=2.3.0
```

### Transitive Dependencies (from infrastructure)
```python
pymongo>=4.9.2          # MongoDB client
pymilvus>=2.6.5         # Milvus vector database client
sentence-transformers>=5.2.0  # Embedding models
aio-pika>=9.3.0         # Included in infrastructure package (not used by RAG agent)
```

### Transitive Dependencies (from services)
```python
PyJWT>=2.10.0           # JWT token handling
passlib>=1.7.4          # Password hashing
bcrypt>=4.0.1,<4.1.0    # Password encryption
python-multipart>=0.0.20  # Multipart form handling
```

## Infrastructure Requirements

### 1. **Vector Database (Milvus)**
- **Required**: Yes (for knowledge retrieval)
- **Configuration**: Set via environment variables
  - `VECTOR_DB_HOST` (default: localhost)
  - `VECTOR_DB_HTTP_PORT` (default: 19530)
  - `VECTOR_DB_USERNAME` (default: root)
  - `VECTOR_DB_PASSWORD` (default: Milvus)
  - `VECTOR_DB_CONNECTION_SCHEME` (default: http)

### 2. **MongoDB** (Optional)
- **Required**: Only if using conversation history features
- **Configuration**: Set via environment variables (only if needed)
  - `MONGO_HOST` (default: localhost)
  - `MONGO_PORT` (default: 27017)
  - `MONGO_DB_NAME` (default: datapilotflow)
  - `MONGO_USER` (optional)
  - `MONGO_PASS` (optional)

## Deployment Steps

### 1. Install Required Packages

```bash
# Install in order (dependencies first)
cd datapilotflow-domain
pip install -e .

cd ../datapilotflow-infrastructure
pip install -e .

cd ../datapilotflow-services
pip install -e .

cd ../datapilotflow-rag-agent
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file in `datapilotflow-rag-agent/`:

```env
# MCP Server Configuration (Required)
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=65510
MCP_SERVER_NAME=datapilotflow-rag

# Vector Database Configuration (Required)
VECTOR_DB_HOST=localhost
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=root
VECTOR_DB_PASSWORD=Milvus
VECTOR_DB_CONNECTION_SCHEME=http

# MongoDB Configuration (Optional - only if using conversation history)
# MONGO_HOST=localhost
# MONGO_PORT=27017
# MONGO_DB_NAME=datapilotflow

# Agent Tracing (Optional - for observability)
# AGENT_TRACING_ENABLED=false
# AGENT_TRACING_API_KEY=your_api_key
# AGENT_TRACING_URL=http://localhost:5173/api
```

### 3. Start the MCP Server

```bash
cd datapilotflow-rag-agent
python run_rag_mcp_server.py
```

The server will be available at:
- **HTTP Endpoint**: `http://0.0.0.0:65510/mcp`
- **Log File**: `logs/rag-agent.log`

## Minimal Deployment (Without Optional Services)

If you want to deploy **without** MongoDB:

1. **Remove/comment out** imports that require conversation history services
2. **Ensure** the RAG agent doesn't use conversation history features
3. **Only** Milvus vector database is required

### Files to Check for Optional Dependencies:
- `datapilotflow-rag-agent/src/datapilotflow/rag_agent/services/generate_response_rag.py` - uses conversation service
- Any code that imports `datapilotflow.services.conversation` - can be made optional

## Package Dependency Tree

```
datapilotflow-rag-agent
├── datapilotflow-domain (core models, config, logging)
│   ├── pydantic
│   ├── pydantic-settings
│   ├── loguru
│   ├── opik
│   └── python-dateutil
├── datapilotflow-infrastructure (database access)
│   ├── datapilotflow-domain
│   ├── pymongo
│   ├── pymilvus
│   ├── sentence-transformers
│   └── aio-pika
├── datapilotflow-services (business logic)
│   ├── datapilotflow-domain
│   ├── datapilotflow-infrastructure
│   ├── langchain-core
│   ├── litellm
│   └── PyJWT, passlib, bcrypt
└── External dependencies
    ├── fastmcp
    ├── langgraph
    ├── langchain-core
    ├── langchain-community
    └── litellm
```

## Summary

**Minimum Required Packages:**
1. `datapilotflow-rag-agent`
2. `datapilotflow-domain`
3. `datapilotflow-infrastructure`
4. `datapilotflow-services`

**Minimum Infrastructure:**
- Milvus vector database (required)
- MongoDB (optional, for conversation history)

**Total Package Count:** 4 DataPilotFlow packages + external dependencies

