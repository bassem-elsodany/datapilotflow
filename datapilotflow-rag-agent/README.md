# datapilotflow-rag-agent

**RAG agent — LangGraph-based retrieval pipeline exposed as an MCP server on port 65510.**

This package implements the Retrieval-Augmented Generation agent. It handles semantic search over Milvus, applies configurable retrieval strategies, generates answers using an LLM, and exposes the entire pipeline as a Model Context Protocol (MCP) server so the Assistant Agent can call it as a tool.

---

## Responsibility

- Accept a natural language query
- Apply a retrieval strategy (standard, HyDE, multi-query, decomposition, augmented)
- Search Milvus for relevant chunks
- Judge retrieved documents for relevance
- Generate a final answer with source citations
- Expose retrieval as an MCP tool via FastMCP

---

## Package Structure

```
src/datapilotflow/rag_agent/
├── agent.py                        # Agent entry point
├── agent_interface.py              # Public interface for programmatic calls
├── agent_state.py                  # LangGraph agent state definition
├── state.py                        # Shared state types
├── graph.py                        # LangGraph graph definition
├── nodes/
│   ├── document_retriever.py       # Milvus vector search
│   ├── document_judger.py          # LLM-based relevance judgment
│   ├── answer_generator.py         # Final answer generation
│   ├── raw_response_formatter.py   # Response formatting
│   ├── hyde_strategy_node.py       # HyDE query expansion
│   ├── multi_query_strategy_node.py        # Multi-query generation
│   ├── decomposition_strategy_node.py      # Query decomposition
│   ├── augmented_strategy_node.py          # Augmented retrieval
│   └── custom_variants_node.py             # Custom strategy variants
├── chains/
│   ├── answer_generation_chain.py  # Answer generation chain
│   ├── hyde_chain.py               # HyDE chain
│   ├── multi_query_chain.py        # Multi-query chain
│   ├── decomposition_chain.py      # Decomposition chain
│   ├── augmented_chain.py          # Augmented chain
│   └── judger_chain.py             # Document judgment chain
├── retrieval/
│   └── reciprocal_rank_fusion.py   # RRF re-ranking for multi-query results
├── tools/
│   ├── retrieval_tools.py          # LangChain retrieval tool wrappers
│   └── retriever_tool.py           # Core retriever tool
├── prompts/
│   ├── generation_prompts.py       # Answer generation prompts
│   ├── hyde_prompts.py             # HyDE prompts
│   ├── multi_query_prompts.py      # Multi-query prompts
│   ├── decomposition_prompts.py    # Decomposition prompts
│   ├── augmented_prompts.py        # Augmented retrieval prompts
│   └── judge_prompts.py            # Document judgment prompts
├── services/
│   └── generate_response_rag.py    # High-level response generation service
└── mcp/
    ├── server.py                   # FastMCP server definition
    ├── adapters/
    │   └── rag_adapter.py          # Adapts RAG agent to MCP tool interface
    ├── tools/
    │   └── rag_tools.py            # MCP tool definitions (knowledge_expert)
    └── cli/
        └── run_server.py           # Entry point: datapilotflow-rag-mcp
```

---

## Retrieval Strategies

| Strategy | Description |
|----------|-------------|
| Standard | Direct embedding search in Milvus |
| HyDE | Generates a hypothetical document before searching |
| Multi-Query | Generates multiple query variants, merges results with RRF |
| Decomposition | Breaks complex questions into sub-questions |
| Augmented | Combines retrieval with additional context augmentation |

The strategy is selected per-agent configuration in the dashboard.

---

## MCP Server

The RAG agent exposes a `knowledge_expert` MCP tool that the Assistant Agent calls via the Model Context Protocol.

```
MCP endpoint: http://localhost:65510
Tool: knowledge_expert(query: str, knowledge_id: str) -> RAGResponse
```

Start the MCP server:

```bash
cd datapilotflow-rag-agent
python run_mcp_rag_server.py

# Or using the installed entry point
datapilotflow-rag-mcp
```

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
datapilotflow-infrastructure >= 1.0.0
datapilotflow-services >= 1.0.0
langgraph >= 1.0.2
langchain-core >= 1.0.0
langchain-community >= 0.0.1
langchain-litellm >= 0.1.0
litellm >= 1.79.0
fastmcp >= 2.14.0, < 3.0.0
pydantic >= 2.10.6
loguru >= 0.7.3
```

---

## Installation

```bash
cd datapilotflow-rag-agent
uv pip install \
  -e ../datapilotflow-domain \
  -e ../datapilotflow-infrastructure \
  -e ../datapilotflow-services \
  -e .
```
