# DataPilotFlow MCP

**Model Context Protocol exposure layer for DataPilotFlow agents**

This package exposes DataPilotFlow agents (RAG, Assistant, etc.) as MCP servers for use by any MCP-compatible client.

## Overview

`datapilotflow-mcp` is a unified MCP server that provides a clean interface to agent capabilities. It follows the architectural principle:

```
datapilotflow-agents (business logic) → datapilotflow-mcp (protocol exposure)
```

### Architecture

```
┌─────────────────────────────┐
│   MCP Clients (Claude,      │
│   LangChain, Custom Apps)   │
└────────────┬────────────────┘
             │ HTTP/MCP Protocol
             ▼
┌─────────────────────────────┐
│ datapilotflow-mcp Server    │
│ ┌───────────────────────┐   │
│ │ knowledge_expert tool │   │ (RAG Query)
│ └───────┬───────────────┘   │
│         │                   │
│ ┌───────▼───────────────┐   │
│ │ RAG Adapter           │   │
│ │ - Workflow execution  │   │
│ │ - Result formatting   │   │
│ └───────┬───────────────┘   │
└────────┼───────────────────┘
         │ Python Imports
         ▼
┌─────────────────────────────┐
│ datapilotflow-agents        │
│ ┌───────────────────────┐   │
│ │ RAG Agent             │   │
│ │ - Graph workflow      │   │
│ │ - State management    │   │
│ └───────────────────────┘   │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ datapilotflow-persistence   │
│ - MongoDB                   │
│ - Milvus Vector DB          │
└─────────────────────────────┘
```

## Features

- **Unified MCP Server**: Single server exposing multiple agent tools
- **Knowledge Retrieval**: RAG-powered document search with multi-query variants
- **Document Reranking**: Optional relevance-based reranking via LLM
- **Multi-language Support**: Query variants in same language as user query
- **Structured Output**: JSON-compatible document results with metadata
- **Easy Extensibility**: Add new agents by creating tools + adapters

## Installation

```bash
pip install datapilotflow-mcp
```

Or with development dependencies:

```bash
pip install datapilotflow-mcp[dev]
```

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in your working directory:

```bash
# Vector Database (Milvus)
VECTOR_DB_HOST=localhost
VECTOR_DB_HTTP_PORT=19530
VECTOR_DB_USERNAME=root
VECTOR_DB_PASSWORD=Milvus
VECTOR_DB_CONNECTION_SCHEME=http

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=root
MONGO_PASS=password

# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=65510
MCP_LOG_LEVEL=INFO
```

### 2. Start the MCP Server

```bash
datapilotflow-mcp
```

Output:
```
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - ======================================================================
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - 🚀 Starting DataPilotFlow MCP Server
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - ======================================================================
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Server: datapilotflow
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Host: 0.0.0.0
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Port: 65510
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Enabled tools: knowledge_expert
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Log level: INFO
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - ======================================================================
2025-12-20 10:15:30 | INFO     | datapilotflow.mcp.cli.run_server | main - Listening on http://0.0.0.0:65510
```

### 3. Call the MCP Server

Using an MCP client:

```python
import httpx
import json

# Call knowledge_expert tool
response = httpx.post(
    "http://localhost:65510/call_tool",
    json={
        "tool": "knowledge_expert",
        "arguments": {
            "search_query": [
                "What is machine learning?",
                "Define machine learning concepts",
                "Machine learning fundamentals",
                "ML algorithms and techniques",
                "Machine learning applications"
            ],
            "collection_name": "my_documents",
            "user_id": "user123",
            "embedding_provider_id": "openai",
            "embedding_model_name": "text-embedding-3-small",
            "vector_dimension": 1536,
            "conversation_id": "conv123"
        }
    }
)

result = response.json()
print(json.dumps(result, indent=2))
```

## Available Tools

### `knowledge_expert`

Retrieves relevant documents from the knowledge base using RAG.

**Input Schema:**

```python
{
    "search_query": [  # Required: List of 5 query variants
        "variant1",
        "variant2",
        "variant3",
        "variant4",
        "variant5"
    ],
    "collection_name": "string",  # Required
    "user_id": "string",           # Required
    "embedding_provider_id": "string",    # Required
    "embedding_model_name": "string",     # Required
    "vector_dimension": 1536,      # Default: 1536
    "top_k": 5,                    # Default: 5 (max: 30)
    "enable_reranking": false,     # Default: false
    "llm_provider_id": "string",   # Optional (required if enable_reranking=true)
    "llm_model_name": "string",    # Optional (required if enable_reranking=true)
    "conversation_id": "string",   # Required
    "conversation_description": "string"  # Optional
}
```

**Output Schema:**

```python
{
    "documents": [
        {
            "id": "doc_id",
            "content": "document text...",
            "source": "https://...",
            "metadata": {
                "title": "...",
                "author": "...",
                ...
            }
        },
        ...
    ],
    "metadata": {
        "total_documents": 10,
        "relevant_documents": 10,
        "source_count": 3,
        "sources": ["url1", "url2", "url3"]
    },
    "error": null  # null on success, error message on failure
}
```

**Example Usage:**

```python
response = await client.call_tool("knowledge_expert", {
    "search_query": [
        "What is semantic search?",
        "Define semantic search",
        "How semantic search works",
        "Semantic search algorithms",
        "Semantic search applications"
    ],
    "collection_name": "documentation",
    "user_id": "user1",
    "embedding_provider_id": "openai",
    "embedding_model_name": "text-embedding-3-small",
    "vector_dimension": 1536,
    "top_k": 5,
    "conversation_id": "conv1"
})
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_HOST` | `0.0.0.0` | Server listening host |
| `MCP_SERVER_PORT` | `65510` | Server listening port |
| `MCP_SERVER_NAME` | `datapilotflow` | Server name for MCP protocol |
| `MCP_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MCP_ENABLED_TOOLS` | `knowledge_expert` | Comma-separated list of enabled tools |
| `MCP_WORKER_THREADS` | `4` | Number of worker threads for async execution |

### Domain Configuration

The MCP server uses configuration from `datapilotflow-domain`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_HOST` | `localhost` | Milvus host |
| `VECTOR_DB_HTTP_PORT` | `19530` | Milvus port |
| `VECTOR_DB_USERNAME` | `root` | Milvus username |
| `VECTOR_DB_PASSWORD` | `Milvus` | Milvus password |
| `MONGO_HOST` | `localhost` | MongoDB host |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_USER` | `` | MongoDB username |
| `MONGO_PASS` | `` | MongoDB password |

## Architecture

### Package Structure

```
datapilotflow-mcp/
├── src/datapilotflow/mcp/
│   ├── __init__.py              # Package exports
│   ├── server.py                # Unified FastMCP server
│   ├── config.py                # Configuration (environment variables)
│   │
│   ├── tools/                   # MCP tool schemas
│   │   ├── __init__.py
│   │   └── rag_tools.py         # RAG schemas (RAGQueryInput, RAGQueryOutput)
│   │
│   ├── adapters/                # Agent → MCP adapters
│   │   ├── __init__.py
│   │   └── rag_adapter.py       # RAG workflow adapter
│   │
│   └── cli/                     # Console entry points
│       ├── __init__.py
│       └── run_server.py        # Server runner
│
├── tests/                       # Test suite
├── pyproject.toml              # Project metadata
└── README.md
```

### Design Patterns

1. **Adapter Pattern**: Each agent has an adapter (e.g., `RAGAdapter`) that translates between MCP tool calls and agent workflows

2. **Separation of Concerns**:
   - `tools/`: Data schemas (Pydantic models)
   - `adapters/`: Business logic (agent orchestration)
   - `server.py`: Protocol implementation (MCP)

3. **Extensibility**: Adding a new agent requires:
   - Create tool schema in `tools/`
   - Create adapter in `adapters/`
   - Register tool in `server.py`

## Adding New Agents

To expose a new agent via MCP:

### Step 1: Create Tool Schema

Create `src/datapilotflow/mcp/tools/agent_tools.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentTaskInput(BaseModel):
    """Input schema for agent tool."""
    task: str = Field(description="Task to execute")
    user_id: str = Field(description="User ID")
    # ... other parameters

class AgentTaskOutput(BaseModel):
    """Output schema for agent tool."""
    result: str = Field(description="Task result")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = Field(default=None)
```

### Step 2: Create Adapter

Create `src/datapilotflow/mcp/adapters/agent_adapter.py`:

```python
from datapilotflow.agents.agent import MyAgent
from datapilotflow.mcp.tools.agent_tools import AgentTaskInput, AgentTaskOutput

class MyAgentAdapter:
    async def execute_task(self, input_data: AgentTaskInput) -> AgentTaskOutput:
        # Orchestrate agent workflow
        # Return structured output
        pass
```

### Step 3: Register Tool

Edit `src/datapilotflow/mcp/server.py`:

```python
from datapilotflow.mcp.adapters.agent_adapter import MyAgentAdapter

agent_adapter = MyAgentAdapter()

@mcp.tool()
async def my_agent_task(task: str, user_id: str, ...) -> Dict[str, Any]:
    input_data = AgentTaskInput(task=task, user_id=user_id, ...)
    output = await agent_adapter.execute_task(input_data)
    return output.model_dump()
```

## Testing

Run the test suite:

```bash
pytest datapilotflow-mcp/tests
```

Or with coverage:

```bash
pytest datapilotflow-mcp/tests --cov=datapilotflow.mcp
```

## Docker

Run the MCP server in Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .[dev]

# Copy source
COPY src ./src

# Expose MCP port
EXPOSE 65510

# Run MCP server
CMD ["datapilotflow-mcp"]
```

Build and run:

```bash
docker build -t datapilotflow-mcp .
docker run -p 65510:65510 -e MCP_LOG_LEVEL=INFO datapilotflow-mcp
```

## Troubleshooting

### Server won't start

Check that all dependencies are installed:
```bash
pip install -e datapilotflow-mcp[dev]
```

Check that agents and persistence packages are installed:
```bash
pip list | grep datapilotflow
```

### Connection to Milvus failed

Verify Milvus is running and accessible:
```bash
python -c "from pymilvus import connections; connections.connect(host='localhost', port=19530)"
```

### Tool execution timeout

Increase timeout in your MCP client configuration or reduce `top_k` parameter in RAG queries.

## Related Packages

- **datapilotflow-domain**: Core models and configuration
- **datapilotflow-persistence**: MongoDB and Milvus vector database
- **datapilotflow-services**: Business logic orchestration
- **datapilotflow-agents**: Agent implementations (RAG, Assistant, etc.)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please ensure:

1. Code follows the existing style
2. Tests pass: `pytest tests/`
3. Type hints are present
4. Docstrings are clear
5. Commit messages are descriptive
