# DataPilotFlow RAG MCP

Standalone retrieval service for DataPilotFlow.

A Model Context Protocol (MCP) server that provides semantic search over knowledge bases using retrieval-augmented generation (RAG).

Contains:
- RAG agent with LangGraph workflows
- Multi-query search strategies
- Document reranking
- HTTP MCP server

## Installation

```bash
pip install datapilotflow-rag-mcp
```

## Usage

### As a Python Library

```python
from datapilotflow.rag_mcp import RAGAgentService

rag_service = RAGAgentService()
results = await rag_service.retrieve_documents(
    search_query=["query1", "query2"],
    collection_name="my_knowledge_base"
)
```

### As a Service

```bash
rag-mcp-server
# Starts HTTP MCP server on port 65510
```

## License

MIT
