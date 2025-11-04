# Multi-Agent Architecture

## Overview

The system uses a **supervisor pattern** with three specialized agents:

1. **RAG Agent** (`src/agents/rag_agent/`) - Document retrieval and ranking
2. **Task Agent** (`src/agents/task_agent/`) - Universal task execution
3. **Supervisor Agent** (`src/agents/supervisor_agent/`) - Intelligent orchestrator

## Package Structure

```
src/
├── agents/                              # All agent implementations
│   ├── __init__.py
│   │
│   ├── common/                          # Shared interfaces and utilities
│   │   ├── __init__.py
│   │   ├── agent_interface.py           # AgentService ABC
│   │   └── agent_state.py               # AgentState definition + RAGContext
│   │
│   ├── rag_agent/                       # RAG Agent (retrieval + ranking)
│   │   ├── __init__.py
│   │   ├── agent.py                     # RAGAgentService implementation
│   │   ├── state.py                     # RAG-specific state (RAGWorkflowState)
│   │   ├── graph.py                     # RAG LangGraph wrapper
│   │   ├── chains/                      # RAG chains (from workflow/chains)
│   │   ├── nodes/                       # RAG nodes (from workflow/nodes)
│   │   ├── prompts/                     # RAG prompts (from workflow/prompts)
│   │   ├── tools/                       # RAG tools (from workflow/tools)
│   │   └── retrieval/                   # Retrieval strategies (RRF, etc.)
│   │
│   ├── task_agent/                      # Task Agent (any task execution)
│   │   ├── __init__.py
│   │   ├── agent.py                     # TaskAgentService implementation
│   │   ├── state.py                     # Task-specific state (TaskAgentState)
│   │   └── prompts/                     # Task execution prompts
│   │
│   └── supervisor_agent/                # Supervisor Agent (orchestrator)
│       ├── __init__.py
│       ├── agent.py                     # SupervisorAgentService implementation
│       ├── state.py                     # Supervisor-specific state
│       └── prompts/                     # Intent detection prompts
│
├── orchestration/                       # Orchestration layer
│   ├── __init__.py
│   └── orchestrator.py                  # Factory + main entry point
│
└── ... (other packages)
```

## Agent Descriptions

### RAG Agent
**Location**: `src/agents/rag_agent/`

**Responsibilities**:
- Retrieve documents from knowledge base
- Judge document relevance
- Rank documents by relevance score
- Filter documents based on threshold
- Return ranked, filtered documents

**Implements**: `AgentService` interface

**Supported Intents**: `["rag_only", "task_with_rag"]`

**Key Files**:
- `agent.py`: `RAGAgentService` class
- `state.py`: `RAGWorkflowState` (TypedDict)
- `graph.py`: Wrapper to existing RAG LangGraph

### Task Agent
**Location**: `src/agents/task_agent/`

**Responsibilities**:
- Execute any task using LLM
- Handle code generation
- Handle task planning
- Handle data analysis
- Handle problem solving
- Optionally inject RAG knowledge if available

**Implements**: `AgentService` interface

**Supported Intents**: `["task_with_rag", "task_standalone"]`

**Key Files**:
- `agent.py`: `TaskAgentService` class
- `state.py`: `TaskAgentState` (TypedDict)

**Capabilities**:
- ✓ Write code (any language)
- ✓ Create task plans/workflows
- ✓ Analyze data
- ✓ Debug code
- ✓ Explain concepts
- ✓ Any LLM-capable task

### Supervisor Agent
**Location**: `src/agents/supervisor_agent/`

**Responsibilities**:
- Detect user intent
- Route to appropriate agent(s)
- Coordinate multi-step workflows
- Inject RAG context to Task Agent
- Synthesize final response

**Note**: NOT a worker agent, a COORDINATOR

**Implements**: `AgentService` interface

**Key Files**:
- `agent.py`: `SupervisorAgentService` class
- `state.py`: `SupervisorAgentState` (TypedDict)

**Routing Logic**:
1. Classify user intent using LLM
2. Route based on intent:
   - `"rag_only"` → RAG Agent only
   - `"task_with_rag"` → RAG Agent → Task Agent (with context injection)
   - `"task_standalone"` → Task Agent only

## Shared Interfaces

### AgentService (Abstract Base Class)
**Location**: `src/agents/common/agent_interface.py`

All agents implement this interface:

```python
class AgentService(ABC):
    async def execute(self, state: AgentState) -> AgentState:
        """Execute agent logic"""
        pass

    def get_agent_name(self) -> str:
        """Return agent name"""
        pass

    def get_supported_intents(self) -> List[str]:
        """Return supported intents"""
        pass

    def get_description(self) -> str:
        """Return description"""
        pass
```

### AgentState (Unified State)
**Location**: `src/agents/common/agent_state.py`

Unified state passed between supervisor and agents:

```python
class AgentState(MessagesState):
    messages: List[Dict[str, Any]]
    rag_context: Optional[RAGContext]  # Populated by RAG Agent
    task_result: Optional[str]         # Populated by Task Agent
    current_agent: Optional[str]
    user_id: str
    conversation_id: str
    intent: str
    execution_log: List[str]
```

### RAGContext
**Location**: `src/agents/common/agent_state.py`

Data structure for RAG results:

```python
class RAGContext:
    query: str
    original_documents: List[Dict[str, Any]]
    judged_documents: List[Dict[str, Any]]
    retrieved_count: int
    relevant_count: int
    relevance_threshold: float
    relevance_scores: List[float]
    execution_time_ms: float
```

## Data Flow Example

**User**: "Write Python code that analyzes these documents about machine learning"

1. **Supervisor receives** user message
2. **Supervisor detects intent**: "task_with_rag"
3. **Supervisor routes** to RAG Agent
   - RAG Agent retrieves ML documents
   - Returns ranked documents in `state.rag_context`
4. **Supervisor routes** to Task Agent with RAG context
   - Task Agent injects RAG knowledge into system prompt
   - Task Agent writes Python code using the documents
   - Returns code in `state.task_result`
5. **Supervisor composes** final response
6. **User receives** code with document references

## Orchestrator Usage

**Location**: `src/orchestration/orchestrator.py`

### Creating the Orchestrator

```python
from src.orchestration import create_multi_agent_orchestrator
from src.workflow.graph import get_graph

supervisor = create_multi_agent_orchestrator(
    llm_client=llm,
    rag_graph=get_graph(),
    conversation_service=conversation_service
)
```

### Processing User Queries

```python
from src.orchestration.orchestrator import process_user_query

result = await process_user_query(
    supervisor=supervisor,
    user_query="Write code that...",
    conversation_id="conv_123",
    user_id="user_456",
    config={"top_k": 10, "...": "..."}
)

# result contains:
# - final_response: String response from agents
# - intent: Detected intent
# - rag_context: RAG results if available
# - task_result: Task results if available
```

## Extending with New Agents

To add a new agent:

1. Create `src/agents/{agent_name}/` package
2. Create `agent.py` with class extending `AgentService`
3. Implement required methods
4. Register with supervisor in `orchestrator.py`

Example structure:

```python
# src/agents/analysis_agent/agent.py
from ..common.agent_interface import AgentService

class AnalysisAgentService(AgentService):
    async def execute(self, state: AgentState) -> AgentState:
        # Implementation
        pass
```

## Key Design Principles

✅ **Decoupling**: Each agent has independent implementation, own logic

✅ **Composition**: Agents work independently or chained together

✅ **Context Sharing**: RAGContext flows between agents via unified state

✅ **Extensibility**: Easy to add new agents by implementing AgentService

✅ **Type Safety**: Strong typing with TypedDict and dataclasses

✅ **Scalability**: Each agent can be deployed independently in future

## Migration Path

### Phase 1: Structure ✅ (CURRENT)
- Create package structure
- Implement agent classes
- Define shared interfaces
- Create orchestrator

### Phase 2: Integration (NEXT)
- Update API routes to use orchestrator
- Implement streaming for agent outputs
- Update WebSocket handlers for agent events
- Integration tests

### Phase 3: Optimization
- Per-agent performance monitoring
- Agent-specific caching
- Parallel agent execution where applicable
- Rate limiting per agent

### Phase 4: Full Migration
- Move all workflow files into agent packages
- Remove old workflow directory
- Update all imports across codebase
