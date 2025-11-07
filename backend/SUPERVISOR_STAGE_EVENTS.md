# Supervisor Stage Events

## Overview
The official LangGraph Supervisor now emits detailed stage events from subagents, matching the behavior of the old custom supervisor.

## Event Flow

### 1. Supervisor Level Events

#### Initialization
- `supervisor_started` - Supervisor initialization begins
- `supervisor_init_complete` - Supervisor ready to route

#### Agent Routing
- `rag_agent_executing` - Routing to RAG Expert
- `task_agent_executing` - Routing to Task Expert

### 2. RAG Agent Detailed Stage Events

When RAG Expert is invoked, the following stages are emitted:

#### Query Enhancement
```json
{
  "type": "workflow_progress",
  "stage": "query_enhancement",
  "message": "Enhancing query...",
  "execution_time_ms": 150
}
```

```json
{
  "type": "workflow_progress",
  "stage": "query_enhancement_complete",
  "message": "Query enhancement complete (augmented)",
  "data": {
    "enhanced_queries": ["enhanced query 1", "enhanced query 2"],
    "strategy": "augmented"
  },
  "execution_time_ms": 250
}
```

#### Document Retrieval
```json
{
  "type": "workflow_progress",
  "stage": "document_retrieval",
  "message": "Retrieving documents...",
  "execution_time_ms": 300
}
```

```json
{
  "type": "workflow_progress",
  "stage": "document_retrieval_complete",
  "message": "Retrieved 10 documents",
  "data": {
    "document_count": 10,
    "documents": [...]
  },
  "execution_time_ms": 450
}
```

#### Document Judging (if reranking enabled)
```json
{
  "type": "workflow_progress",
  "stage": "document_judging",
  "message": "Judging document relevance...",
  "execution_time_ms": 500
}
```

```json
{
  "type": "workflow_progress",
  "stage": "document_judging_complete",
  "message": "Document judging complete: 7/10 relevant",
  "data": {
    "total_documents": 10,
    "relevant_documents": 7,
    "judged_documents": [...]
  },
  "execution_time_ms": 800
}
```

#### Response Generation
```json
{
  "type": "workflow_progress",
  "stage": "response_generation",
  "message": "Generating response...",
  "execution_time_ms": 850
}
```

### 3. Response Streaming

#### First Chunk with Metadata
```json
{
  "type": "streaming_response",
  "chunk": "Here is the answer...",
  "metadata": {
    "agents_executed": ["rag_expert"],
    "orchestrator_type": "official_langgraph_supervisor",
    "enhancement_strategy": "augmented",
    "source_urls": ["url1", "url2"],
    "chunk_ids": ["chunk1", "chunk2"],
    "document_count": 10,
    "relevant_document_count": 7,
    "enhanced_queries": ["query1", "query2"]
  },
  "execution_time_ms": 1200
}
```

#### Subsequent Chunks
```json
{
  "type": "streaming_response",
  "chunk": "... more text...",
  "execution_time_ms": 1250
}
```

### 4. Completion Event

```json
{
  "type": "workflow_complete",
  "execution_time_ms": 1500,
  "workflow_completed": true,
  "query": "user query",
  "response": "complete response",
  "documents": [...],
  "metadata": {
    "orchestrator_type": "official_langgraph_supervisor",
    "agents_executed": ["rag_expert"],
    "enhancement_strategy": "augmented",
    "document_count": 10,
    "relevant_document_count": 7,
    "enhanced_queries": ["query1", "query2"]
  }
}
```

## RAG Agent Nodes Tracked

The supervisor monitors these RAG agent internal nodes:

1. **Query Enhancement Nodes**
   - `augmented_strategy_node`
   - `hyde_strategy_node`
   - `decomposition_strategy_node`
   - `multi_query_strategy_node`

2. **Retrieval Node**
   - `document_retriever`

3. **Judging Node**
   - `document_judger`

4. **Generation Node**
   - `answer_generator`

## Implementation Details

### Stage Tracking Variables
```python
# Track RAG agent stage emissions
rag_stages_emitted = set()  # Avoid duplicate stage events
total_docs = 0
relevant_docs = 0
rag_documents = []
rag_enhanced_queries = []
rag_enhancement_strategy = "native"
current_agent = None  # Track which agent is executing
```

### Event Capture Pattern
```python
# Capture RAG agent internal node events
if current_agent == "rag_expert" and event_type == "on_chain_end":
    node_name = event_name
    
    # Extract node output
    node_output = event_data.get("output", {})
    
    # Emit stage events based on node name
    if node_name in ["augmented_strategy_node", ...]:
        # Emit query_enhancement events
    elif node_name == "document_retriever":
        # Emit document_retrieval events
    # ... etc
```

## Benefits

✅ **Detailed Progress Tracking** - Frontend can show exact stage being executed
✅ **Same as Old Supervisor** - Maintains backward compatibility with UI
✅ **RAG Metadata Included** - Documents, enhanced queries, strategies all available
✅ **No Code Duplication** - Reuses RAG agent's existing node structure
✅ **Official Library Compatible** - Works with langgraph-supervisor

