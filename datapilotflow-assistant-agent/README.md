# datapilotflow-assistant-agent

**Supervisor agent — orchestrates tools, RAG lookups, and multi-turn conversations via DeepAgents and LangGraph.**

This package implements the top-level conversational agent. It receives user messages from the API, plans tool calls, delegates knowledge retrieval to the RAG agent via MCP, and streams responses back over WebSocket.

---

## Responsibility

- Manage multi-turn conversation context
- Plan and execute tool calls based on user intent
- Connect to the RAG agent as an MCP client to invoke `knowledge_expert`
- Connect to registered external MCP servers for additional tools
- Stream responses token-by-token back to the API layer

---

## Package Structure

```
src/datapilotflow/assistant_agent/
├── factory.py            # Builds the agent graph with tools and MCP connections
└── response_handler.py   # Processes and streams agent output to the caller
```

The agent graph is built dynamically at runtime using `factory.py`, which wires together:
- Conversation history from MongoDB
- MCP tool connections (RAG agent + any registered external servers)
- The DeepAgents supervisor loop

---

## How It Works

1. The API WebSocket router receives a user message and calls the assistant agent factory
2. The factory builds a LangGraph agent with access to all configured tools
3. The agent reasons over the conversation history and decides which tools to call
4. For knowledge questions, it calls `knowledge_expert` on the RAG MCP server
5. For other tasks, it calls tools from registered MCP servers
6. The response handler streams tokens back to the API as they are generated

---

## Dependencies

```
datapilotflow-domain >= 1.0.0
datapilotflow-services >= 1.0.0
deepagents >= 0.1.0
langgraph >= 1.0.2
langchain-core >= 1.0.0
langchain-community >= 0.0.1
langchain-mcp-adapters >= 0.1.0
pymongo >= 4.0.0
loguru >= 0.7.3
```

---

## Installation

```bash
cd datapilotflow-assistant-agent
uv pip install \
  -e ../datapilotflow-domain \
  -e ../datapilotflow-services \
  -e .
```

---

## Dependency Position

```
datapilotflow-api  -->  datapilotflow-assistant-agent  -->  datapilotflow-domain
                                                        -->  datapilotflow-services
                                                        -->  (MCP client) datapilotflow-rag-agent
```
