# Custom Variants Strategy

## Overview

The **Custom Variants** strategy is a new query enhancement strategy that allows API consumers to provide their own pre-defined query variants without any LLM-based enhancement. This enables:

- **User-defined query variations** for better control over search
- **Parallel vector search** across all variants
- **Reciprocal Rank Fusion (RRF)** to merge and rank results
- **Zero LLM cost** for query enhancement (passthrough only)

## How It Works

```
User provides variants → custom_variants_node (passthrough) → 
parallel_retrieval (N async searches) → RRF fusion → top_k documents
```

### Architecture Flow

1. **Input**: User provides list of query variants
2. **Custom Variants Node**: Stores variants in state (no LLM calls)
3. **Document Retriever**: Detects multiple variants → auto-enables RRF
4. **Parallel Retrieval**: Executes N parallel vector searches
5. **RRF Fusion**: Merges results using Reciprocal Rank Fusion algorithm
6. **Output**: Top K fused documents ranked by consensus

## Comparison with Other Strategies

| Strategy | LLM Enhancement | Input Format | RRF Support |
|----------|----------------|--------------|-------------|
| **native** | ❌ None | Single string | ❌ No |
| **augmented** | ✅ 4 transformations | Single string | ✅ Yes (auto) |
| **multi_query** | ✅ 5 variants | Single string | ✅ Yes (auto) |
| **hyde** | ✅ Hypothetical answer | Single string | ❌ No (single doc) |
| **decomposition** | ✅ Sub-queries | Single string | ✅ Yes (auto) |
| **custom_variants** | ❌ None (passthrough) | String or List | ✅ Yes (auto) |

## Usage Examples

### Option 1: Query as List (Auto-Detection)

```python
# WebSocket message format
{
    "query": [
        "SSL certificate configuration",
        "TLS settings and setup",
        "HTTPS encryption configuration"
    ],
    "conversation_id": "conv_123"
}
```

When `query` is a list, the system **automatically selects** the `custom_variants` strategy.

### Option 2: Explicit Strategy Selection

```python
# WebSocket message format
{
    "query": [
        "How to configure SSL in Apache?",
        "Apache HTTPS setup guide",
        "Secure socket layer Apache tutorial"
    ],
    "conversation_id": "conv_123",
    # Optional: explicitly set strategy
    # "selected_strategy": "custom_variants"  
}
```

### Option 3: Original Query + Custom Variants

If you want to include the original query along with additional variants:

```python
{
    "query": "How to configure SSL?",
    "custom_variants": [
        "SSL certificate installation steps",
        "HTTPS configuration tutorial"
    ],
    "conversation_id": "conv_123"
}
```

Result: Uses `["How to configure SSL?", "SSL certificate installation steps", "HTTPS configuration tutorial"]`

## API Integration

### WebSocket Endpoint: `/ws/agent/query/rag`

```python
import asyncio
import websockets
import json

async def test_custom_variants():
    uri = "ws://localhost:8000/api/ws/agent/query/rag?token=YOUR_JWT_TOKEN"
    
    async with websockets.connect(uri) as websocket:
        # Send query with custom variants
        query_message = {
            "query": [
                "Salesforce API authentication methods",
                "OAuth flow in Salesforce",
                "Connected apps authentication"
            ],
            "conversation_id": "conv_abc123"
        }
        
        await websocket.send(json.dumps(query_message))
        
        # Receive streaming responses
        async for message in websocket:
            data = json.loads(message)
            print(f"Stage: {data.get('stage')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('type') == 'workflow_complete':
                print(f"Final answer: {data.get('data', {}).get('answer')}")
                break
```

## Benefits

### ✅ Advantages

1. **Full Control**: Users define exact query variations
2. **No LLM Cost**: Zero tokens spent on enhancement
3. **Predictable**: No LLM unpredictability
4. **Fast**: Only vector search time (parallel execution)
5. **RRF Enabled**: Automatic consensus-based ranking
6. **Language Agnostic**: Works with any language variants

### ⚠️ Considerations

1. **User Responsibility**: Quality depends on user-provided variants
2. **No Enhancement**: Doesn't benefit from LLM creativity
3. **Requires Knowledge**: User must know good variations

## Use Cases

### 1. **Multi-Language Search**
```python
query = [
    "How to reset password?",           # English
    "Comment réinitialiser le mot de passe?",  # French
    "Wie setze ich das Passwort zurück?"      # German
]
```

### 2. **Acronym Expansion**
```python
query = [
    "JWT authentication",
    "JSON Web Token authentication",
    "Bearer token authentication"
]
```

### 3. **Domain-Specific Variants**
```python
query = [
    "API rate limiting",
    "request throttling",
    "quota management",
    "call limits per minute"
]
```

### 4. **Testing & Debugging**
```python
# Test specific query variations
query = [
    "exact phrase from documentation",
    "slight variation of phrase",
    "completely different phrasing"
]
```

## RRF Configuration

The system automatically enables RRF when multiple variants are detected:

```python
# Default RRF configuration (from retrieval_config)
{
    "top_k_per_query": 5,      # Docs retrieved per variant
    "rrf_k": 60,               # RRF constant (from paper)
    "final_top_k": 5           # Final merged results
}
```

### RRF Formula

```
score(doc) = Σ(1 / (k + rank_i))
```

Where:
- `k` = RRF constant (default: 60)
- `rank_i` = rank of document in result set i
- Documents appearing in multiple result sets score higher

## Logging Output

When using custom_variants, you'll see detailed logging:

```
🚀 [NODE START] custom_variants_node
📋 Received 3 custom variants from query field (list)
✅ Custom Variants Strategy: Using 3 user-provided variants
--------------------------------------------------------------------------------
   🔍 VARIANT [1/3]: 'SSL certificate configuration'
   🔍 VARIANT [2/3]: 'TLS settings and setup'
   🔍 VARIANT [3/3]: 'HTTPS encryption configuration'
--------------------------------------------------------------------------------
✅ [NODE FINISH] custom_variants_node - Stored 3 variants in state

🔥🔥🔥 ... [document_retriever output] ... 🔥🔥🔥
📊 TOTAL QUERY VARIANTS: 3
⚙️  RETRIEVAL STRATEGY DECISION
✅ Auto-enabling RRF because we have 3 query variants

🚨 USING RECIPROCAL RANK FUSION (RRF) STRATEGY 🚨
📊 Number of query variants: 3
📊 Documents per query variant: 5
📊 Total docs retrieved before fusion: 15
📊 RRF constant k: 60
📊 Final top_k after RRF fusion: 5
```

## Configuration via Conversation Settings

The custom_variants strategy can be set as the default for a conversation:

```python
# Create conversation with custom_variants strategy
POST /api/conversations
{
    "name": "Custom Variants Session",
    "enhancement": {
        "strategy": "custom_variants"
    },
    "collection_name": "knowledge_base"
}
```

## Integration with Existing Code

The custom_variants strategy integrates seamlessly:

1. **Uses same field** as augmented strategy (`augmented_queries`)
2. **Same RRF code path** as multi_query/decomposition
3. **No changes required** to downstream nodes
4. **Backward compatible** with existing strategies

## Example: Complete Workflow

```python
import asyncio
import websockets
import json

async def demo_custom_variants():
    """
    Complete example: Send custom variants and process results
    """
    uri = "ws://localhost:8000/api/ws/agent/query/rag?token=YOUR_TOKEN"
    
    async with websockets.connect(uri) as ws:
        # Define custom variants
        message = {
            "query": [
                "MuleSoft API gateway configuration",
                "Anypoint Platform API management",
                "Mule runtime API deployment"
            ],
            "conversation_id": "conv_mulesoft_123"
        }
        
        print(f"📤 Sending custom variants:")
        for i, variant in enumerate(message["query"], 1):
            print(f"   {i}. {variant}")
        
        await ws.send(json.dumps(message))
        
        # Process responses
        async for msg in ws:
            data = json.loads(msg)
            stage = data.get("stage")
            
            if stage == "query_enhancement_complete":
                variants_used = data.get("data", {}).get("enhanced_queries", [])
                print(f"\n✅ Variants confirmed: {len(variants_used)}")
            
            elif stage == "document_retrieval_complete":
                docs = data.get("data", {}).get("documents", [])
                print(f"\n✅ Retrieved {len(docs)} fused documents")
            
            elif stage == "workflow_complete":
                answer = data.get("data", {}).get("answer")
                print(f"\n📝 Final Answer:\n{answer}")
                break

# Run demo
asyncio.run(demo_custom_variants())
```

## Summary

The **custom_variants** strategy is ideal when:

- ✅ You want **full control** over query variations
- ✅ You need **predictable results** (no LLM randomness)
- ✅ You want to **avoid LLM costs** for enhancement
- ✅ You have **domain expertise** to craft good variants
- ✅ You need **multi-language** or **multi-format** search

It's the **fastest enhancement strategy** (no LLM calls) while still leveraging the power of **parallel search + RRF fusion**!

