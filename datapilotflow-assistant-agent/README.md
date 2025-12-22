# DataPilotFlow Assistant Agent

**Assistant Agent Package - Supervisor Agent with Tool Orchestration**

The `datapilotflow-assistant-agent` package provides a supervisor/assistant agent that orchestrates multiple tools and agents, including the RAG agent, to handle complex user queries and tasks.

## 📦 Package Overview

- **Version**: 1.0.0
- **Python**: >=3.11
- **Dependencies**: `datapilotflow-domain`, `datapilotflow-infrastructure`, `datapilotflow-services`
- **Purpose**: Supervisor agent with tool orchestration and multi-agent coordination

## 🏗️ Architecture Position

```
┌─────────────────────────────────────────┐
│     API, WebSocket Clients               │
└────────────────┬────────────────────────┘
                 │ calls
┌────────────────▼────────────────────────┐
│   datapilotflow-assistant-agent         │
│   (Supervisor Agent)                     │
└────────────────┬────────────────────────┘
                 │ orchestrates
┌────────────────▼────────────────────────┐
│   datapilotflow-rag-agent               │
│   (RAG Agent via MCP)                    │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-services                │
│   (Business Logic)                       │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│   datapilotflow-infrastructure          │
│   (Database Access)                      │
└────────────────┬────────────────────────┘
                 │ uses
┌────────────────▼────────────────────────┐
│      datapilotflow-domain               │
│      (Foundation)                        │
└─────────────────────────────────────────┘
```

**This package provides**:
- Supervisor agent implementation
- Tool orchestration
- Multi-agent coordination
- MCP tool integration
- Conversation management

## 📁 Package Structure

```
datapilotflow-assistant-agent/
├── src/datapilotflow/assistant_agent/
│   ├── __init__.py
│   │
│   ├── agent.py                 # AssistantAgentService
│   ├── graph.py                 # LangGraph supervisor workflow
│   ├── state.py                 # Agent state
│   │
│   ├── tools/                    # Agent tools
│   │   └── ...
│   │
│   └── prompts/                  # Agent prompts
│       └── ...
│
├── pyproject.toml
└── README.md
```

## 🔑 Key Components

### 1. Assistant Agent

**AssistantAgentService**: Supervisor agent that orchestrates tools and agents

**Responsibilities**:
- Route queries to appropriate agents/tools
- Coordinate multiple agents
- Manage conversation flow
- Integrate with MCP tools (RAG agent)

### 2. Supervisor Graph

**LangGraph Workflow**: Orchestrates agent and tool execution

**Features**:
- Agent routing
- Tool selection
- Multi-step reasoning
- Conversation management

## 🔗 How This Package Uses Lower Layers

### Uses RAG Agent (via MCP)
```python
# Assistant agent calls RAG agent via MCP
# Uses knowledge_expert tool from RAG MCP server
```

### Uses Services
```python
from datapilotflow.services.conversation import ConversationHistoryService
from datapilotflow.services.model_provider import ModelProviderService

# Assistant agent uses services
conversation_service = ConversationHistoryService()
model_service = ModelProviderService()
```

### Uses Domain
```python
from datapilotflow.domain.config import settings
from datapilotflow.domain.conversation import ConversationMessage

# Assistant agent uses domain models
```

## 📦 Dependencies

### DataPilotFlow Dependencies
- `datapilotflow-domain>=1.0.0` - Domain models and configuration
- `datapilotflow-infrastructure>=1.0.0` - Database access
- `datapilotflow-services>=1.0.0` - Business logic services

### External Dependencies
- `langgraph>=1.0.2` - Agent workflow orchestration
- `langchain-core>=1.0.0` - LangChain core
- `litellm>=1.79.0` - LLM provider abstraction
- `loguru>=0.7.3` - Logging
- `pydantic>=2.10.6` - Data validation

## 🚀 Installation

```bash
# Install dependencies first
cd datapilotflow-domain && pip install -e .
cd ../datapilotflow-infrastructure && pip install -e .
cd ../datapilotflow-services && pip install -e .

# Install assistant agent
cd ../datapilotflow-assistant-agent && pip install -e .
```

## 📚 Related Packages

**Depends on**:
- ✅ `datapilotflow-domain` - Uses config and domain models
- ✅ `datapilotflow-infrastructure` - Uses database access
- ✅ `datapilotflow-services` - Uses business logic services

**Used by**:
- ✅ `datapilotflow-api` - Exposes assistant agent via API

## 🎯 Design Principles

1. **Supervisor Pattern**: Orchestrates multiple agents and tools
2. **Tool Integration**: Integrates with MCP tools (RAG agent)
3. **Conversation Management**: Manages multi-turn conversations
4. **LangGraph Workflow**: Modular, composable agent pipeline

