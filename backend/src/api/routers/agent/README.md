# Agent WebSocket API

## Overview

The Agent WebSocket API provides a real-time interface to the LangGraph workflow with query enhancement capabilities. This endpoint allows the UI to send queries with specific enhancement strategies and receive streaming responses.

## Endpoint

```
ws://localhost:8000/api/v1/ws/agent/query?token={JWT_TOKEN}
```

## Authentication

- **Method**: JWT Token via query parameter
- **Parameter**: `token` (required)
- **Example**: `?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## Request Message Format

The client sends a JSON message with the following structure:

```json
{
  "query": "How do I configure SSL certificates in Mule 4.5?",
  "selected_strategy": "step_back",
  "llm_provider_id": "67890abc-def0-1234-5678-9abcdef01234",
  "llm_model_name": "gpt-4",
  "collection_name": "LongTermMemory",
  "enhancement_config": {
    "query_enhancement": {
      "enabled": true,
      "timeout_seconds": 30
    }
  }
}
```

### Required Fields

- **query** (string): The user's question or search query
- **llm_provider_id** (string): The ID of the LLM provider from the database

### Optional Fields

- **selected_strategy** (string): Query enhancement strategy to use. Options:
  - `"step_back"` - Generates broader conceptual questions
  - `"multi_query"` - Creates multiple query variants
  - `"hyde"` - Generates hypothetical answers
  - `"decomposition"` - Breaks complex queries into sub-questions
  - `"rag_fusion"` - Multiple search perspectives with rank fusion
  - `"query_fusion"` - Combines original + enhanced queries (runs last)
  - `null` or omitted - No enhancement applied
  
- **llm_model_name** (string): Specific model name (defaults to provider's default)
- **collection_name** (string): Vector DB collection name (default: "LongTermMemory")
- **enhancement_config** (object): Additional configuration for query enhancement

## Response Message Format

The server sends JSON messages with different stages:

### Stage 1: Starting

```json
{
  "stage": "starting",
  "message": "Processing query: How do I configure...",
  "data": {
    "query": "How do I configure SSL certificates...",
    "strategy": "step_back",
    "provider_id": "67890abc-def0-1234-5678-9abcdef01234"
  },
  "timestamp": 1698765432.123
}
```

### Stage 2: Query Enhancement

```json
{
  "stage": "query_enhancement",
  "message": "Enhancing query...",
  "data": {
    "strategy": "step_back"
  },
  "timestamp": 1698765433.456
}
```

### Stage 3: Query Enhancement Complete

```json
{
  "stage": "query_enhancement_complete",
  "message": "Query enhanced using step_back strategy",
  "data": {
    "original_query": "How do I configure SSL certificates in Mule 4.5?",
    "enhanced_queries": [
      "What are the security fundamentals in Mule ESB?",
      "How does certificate management work in integration platforms?"
    ],
    "strategies_applied": ["step_back"],
    "step_back_query": "What are the security fundamentals in Mule ESB?",
    "hypothetical_answer": null,
    "sub_queries": [],
    "fusion_perspectives": [],
    "multi_query_variants": []
  },
  "timestamp": 1698765434.789
}
```

### Stage 4: Document Retrieval

```json
{
  "stage": "document_retrieval",
  "message": "Retrieving relevant documents...",
  "timestamp": 1698765435.012
}
```

### Stage 5: Document Retrieval Complete

```json
{
  "stage": "document_retrieval_complete",
  "message": "Retrieved 15 relevant documents",
  "data": {
    "document_count": 15,
    "documents": [
      {
        "text": "SSL configuration in Mule 4.5 requires...",
        "metadata": {
          "source_url": "https://docs.mulesoft.com/ssl",
          "title": "SSL Configuration Guide"
        }
      }
      // ... first 5 documents
    ]
  },
  "timestamp": 1698765436.345
}
```

### Stage 6: Response Generation

```json
{
  "stage": "response_generation",
  "message": "Generating AI response...",
  "timestamp": 1698765437.678
}
```

### Stage 7: Streaming Response

```json
{
  "stage": "streaming_response",
  "message": "Streaming response...",
  "data": {
    "chunk": "To configure SSL certificates in Mule 4.5, y",
    "chunk_index": 0,
    "total_length": 523
  },
  "timestamp": 1698765438.901
}
```

### Stage 8: Completed

```json
{
  "stage": "completed",
  "message": "Query processing completed successfully",
  "data": {
    "query": "How do I configure SSL certificates in Mule 4.5?",
    "response": "To configure SSL certificates in Mule 4.5, you need to...",
    "document_count": 15,
    "enhancement_strategy": "step_back",
    "strategies_applied": ["step_back"],
    "workflow_metadata": {
      "steps_executed": ["query_enhancer", "document_retriever", "response_generator"],
      "total_time_ms": 3456
    }
  },
  "timestamp": 1698765440.234
}
```

### Error Response

```json
{
  "stage": "error",
  "message": "LLM provider not found: invalid-id",
  "data": {
    "error_type": "HTTPException",
    "error_details": "Provider not found"
  },
  "timestamp": 1698765432.567
}
```

## Query Enhancement Strategies

### 1. Step Back Strategy
**Purpose**: Generates broader, more conceptual questions to capture high-level understanding

**Use Case**: When the query is very specific and you want to also retrieve foundational concepts

**Example**:
- Original: "How to fix timeout error in Mule HTTP connector?"
- Enhanced: "What are common HTTP connection issues in Mule ESB?"

### 2. Multi Query Strategy
**Purpose**: Generates multiple alternative phrasings of the same question

**Use Case**: To handle terminology variations and improve recall

**Example**:
- Original: "How to deploy Mule app to CloudHub?"
- Enhanced: ["CloudHub deployment process", "Deploying applications to Anypoint platform", "Mule app hosting on CloudHub"]

### 3. HyDE Strategy (Hypothetical Document Embeddings)
**Purpose**: Generates a hypothetical answer and searches with it

**Use Case**: When you want to match against answer-style documents

**Example**:
- Original: "What is DataWeave?"
- Enhanced: "DataWeave is a powerful data transformation language in MuleSoft..."

### 4. Decomposition Strategy
**Purpose**: Breaks complex queries into simpler sub-questions

**Use Case**: For multi-part or complex questions

**Example**:
- Original: "How to set up OAuth 2.0 authentication with token refresh in Mule?"
- Enhanced: ["What is OAuth 2.0?", "How to configure OAuth in Mule?", "How does token refresh work?"]

### 5. RAG Fusion Strategy
**Purpose**: Generates multiple perspectives with reciprocal rank fusion

**Use Case**: For comprehensive coverage using multiple search angles

**Example**:
- Original: "Best practices for error handling?"
- Enhanced: ["Error handling patterns", "Exception management strategies", "Fault tolerance techniques"]

### 6. Query Fusion Strategy
**Purpose**: Combines original query with all enhanced queries

**Use Case**: Always runs last to ensure original query is preserved alongside enhancements

**Behavior**: Automatically includes the original query + all generated variants

## JavaScript/TypeScript Client Example

```typescript
class AgentWebSocketClient {
  private ws: WebSocket | null = null;
  
  connect(token: string) {
    const url = `ws://localhost:8000/api/v1/ws/agent/query?token=${token}`;
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('Connected to Agent WebSocket');
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('Disconnected from Agent WebSocket');
    };
  }
  
  sendQuery(query: string, strategy: string, providerId: string) {
    if (!this.ws) {
      throw new Error('WebSocket not connected');
    }
    
    const message = {
      query: query,
      selected_strategy: strategy,
      llm_provider_id: providerId,
      llm_model_name: 'gpt-4',
      collection_name: 'LongTermMemory'
    };
    
    this.ws.send(JSON.stringify(message));
  }
  
  handleMessage(message: any) {
    switch (message.stage) {
      case 'starting':
        console.log('Query processing started');
        break;
        
      case 'query_enhancement_complete':
        console.log('Enhanced queries:', message.data.enhanced_queries);
        break;
        
      case 'document_retrieval_complete':
        console.log(`Retrieved ${message.data.document_count} documents`);
        break;
        
      case 'streaming_response':
        // Append chunk to UI
        this.appendResponseChunk(message.data.chunk);
        break;
        
      case 'completed':
        console.log('Query completed:', message.data.response);
        break;
        
      case 'error':
        console.error('Error:', message.message);
        break;
    }
  }
  
  appendResponseChunk(chunk: string) {
    // Update your UI with the streaming chunk
    document.getElementById('response').textContent += chunk;
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage
const client = new AgentWebSocketClient();
client.connect('your-jwt-token-here');
client.sendQuery(
  'How to configure SSL in Mule?',
  'step_back',
  'provider-id-here'
);
```

## Error Handling

### Common Errors

1. **Missing Authentication Token**
   - Code: `1008`
   - Reason: "Missing authentication token"
   - Solution: Include `?token={JWT}` in WebSocket URL

2. **Invalid Token**
   - Code: `1008`
   - Reason: "Invalid token payload"
   - Solution: Ensure token is valid and not expired

3. **Missing Query**
   - Stage: `"error"`
   - Message: "Query is required"
   - Solution: Include `query` field in request

4. **Missing LLM Provider**
   - Stage: `"error"`
   - Message: "LLM provider ID is required"
   - Solution: Include `llm_provider_id` field in request

5. **Provider Not Found**
   - Stage: `"error"`
   - Message: "LLM provider not found: {id}"
   - Solution: Verify provider ID exists in database

6. **Provider Inactive**
   - Stage: `"error"`
   - Message: "LLM provider is not active: {name}"
   - Solution: Activate the provider in settings

7. **Workflow Execution Failed**
   - Stage: `"error"`
   - Message: "Workflow execution failed: {details}"
   - Solution: Check logs for detailed error trace

## Testing with Postman/Insomnia

1. Create a new WebSocket request
2. URL: `ws://localhost:8000/api/v1/ws/agent/query?token=YOUR_TOKEN`
3. Connect to the WebSocket
4. Send a message:
```json
{
  "query": "What is MuleSoft?",
  "selected_strategy": "step_back",
  "llm_provider_id": "your-provider-id",
  "llm_model_name": "gpt-4"
}
```
5. Observe the streaming responses

## Integration with LangGraph Workflow

The WebSocket endpoint integrates with the following LangGraph workflow:

```
┌─────────────────┐
│  query_enhancer │ ← Uses selected_strategy
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│document_retriever│ ← Uses enhanced queries
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│response_generator│ ← Uses LLM config
└─────────────────┘
```

Each stage sends progress updates to the WebSocket client, providing real-time feedback on the processing pipeline.

## Best Practices

1. **Strategy Selection**:
   - Use `step_back` for specific technical questions
   - Use `multi_query` for general queries with terminology variations
   - Use `hyde` when searching for explanatory content
   - Use `decomposition` for complex, multi-part questions
   - Use `rag_fusion` for comprehensive research queries
   - Use `query_fusion` or `null` to include original query without modification

2. **Error Recovery**:
   - Implement reconnection logic for network failures
   - Display user-friendly error messages
   - Log all errors for debugging

3. **UI/UX**:
   - Show loading indicators during each stage
   - Display enhanced queries to users (optional)
   - Stream response chunks for better perceived performance
   - Show document count and sources

4. **Performance**:
   - Close WebSocket connections when not in use
   - Implement connection pooling for multiple queries
   - Handle timeout scenarios gracefully

## Security Considerations

- Always validate JWT tokens on the server
- Use WSS (WebSocket Secure) in production
- Implement rate limiting for query submissions
- Sanitize user input before processing
- Never expose API keys or sensitive data in responses

