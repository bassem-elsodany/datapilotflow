# Retrieval Strategy Feature - Implementation Guide

## Overview
This feature allows users to choose between two retrieval strategies when using query enhancement with multiple query variants:

1. **Single Query** (Default) - Fast, uses only the first query variant
2. **Reciprocal Rank Fusion (RRF)** - Slower but higher quality, uses all query variants with fusion

---

## ✅ Phase 1: Backend Model/DAO/Service/API - COMPLETED

### Files Modified:

#### 1. Domain Model
**File**: `src/services/conversation/conversation_history_service.py`

**Changes**:
- Added `RetrievalStrategy` enum with two values:
  - `SINGLE_QUERY = "single_query"`
  - `RECIPROCAL_RANK_FUSION = "reciprocal_rank_fusion"`

- Added `AUGMENTED = "augmented"` to `QueryEnhancementStrategy` enum

- Added `retrieval_strategy` field to `ConversationSession`:
  ```python
  retrieval_strategy: str = "single_query"
  ```

- Updated `create_conversation()` method to accept `retrieval_strategy` parameter
- Updated `get_conversation()` to load `retrieval_strategy` from MongoDB
- Updated `update_conversation_config()` to update `retrieval_strategy`

#### 2. API Layer
**File**: `src/api/routers/conversation/conversation_router.py`

**Changes**:
- Added `retrieval_strategy` field to `CreateSessionRequest`:
  ```python
  retrieval_strategy: Optional[str] = Field(
      "single_query",
      description="Multi-query retrieval strategy: 'single_query' or 'reciprocal_rank_fusion'"
  )
  ```

- Added `retrieval_strategy` field to `UpdateSessionConfigRequest`

- Updated POST `/api/v1/conversation/sessions` endpoint to accept and return retrieval_strategy
- Updated PUT `/api/v1/conversation/sessions/{conversation_id}/config` endpoint

---

## 🔄 Phase 2: Workflow Implementation - IN PROGRESS

### Step 1: Create RRF Fusion Module ✅

**File**: `src/workflow/retrieval/reciprocal_rank_fusion.py` (NEW)

```python
"""
Reciprocal Rank Fusion (RRF) for multi-query retrieval.

RRF combines results from multiple query variants to improve ranking quality.
Documents appearing in multiple result sets rank higher.
"""

from typing import List, Dict, Any, Tuple
from loguru import logger


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = 60,
    final_top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Apply Reciprocal Rank Fusion to merge multiple retrieval result sets.

    RRF Formula: score(doc) = Σ(1 / (k + rank_i))
    where rank_i is the rank of the document in result set i

    Args:
        results_list: List of result lists from different queries
        k: RRF constant (default: 60, from original paper)
        final_top_k: Number of final results to return

    Returns:
        Fused results sorted by RRF score
    """
    # Track scores for each document by ID
    doc_scores = {}
    doc_data = {}

    # Process each result set
    for result_set_idx, results in enumerate(results_list):
        for rank, doc in enumerate(results, start=1):
            doc_id = doc.get("id") or doc.get("chunk_id") or f"doc_{result_set_idx}_{rank}"

            # Calculate RRF score for this document in this result set
            rrf_score = 1.0 / (k + rank)

            # Accumulate scores across result sets
            if doc_id not in doc_scores:
                doc_scores[doc_id] = 0.0
                doc_data[doc_id] = doc

            doc_scores[doc_id] += rrf_score

            logger.debug(
                f"Doc {doc_id} in result set {result_set_idx + 1}: "
                f"rank={rank}, rrf_score={rrf_score:.4f}, "
                f"total_score={doc_scores[doc_id]:.4f}"
            )

    # Sort documents by RRF score (highest first)
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Return top_k documents with their RRF scores
    fused_results = []
    for doc_id, score in sorted_docs[:final_top_k]:
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = round(score, 4)
        doc["fusion_rank"] = len(fused_results) + 1
        fused_results.append(doc)

    logger.info(
        f"✅ RRF Fusion: Combined {len(results_list)} result sets "
        f"({sum(len(r) for r in results_list)} total docs) → "
        f"{len(fused_results)} fused results"
    )

    return fused_results


async def parallel_retrieval(
    queries: List[str],
    retriever,
    top_k_per_query: int = 5
) -> List[List[Dict[str, Any]]]:
    """
    Execute multiple retrieval queries in parallel.

    Args:
        queries: List of query strings
        retriever: MilvusRetriever instance
        top_k_per_query: Number of documents to retrieve per query

    Returns:
        List of result lists, one per query
    """
    import asyncio

    async def retrieve_single(query: str, query_idx: int) -> List[Dict[str, Any]]:
        """Retrieve documents for a single query."""
        try:
            logger.debug(f"Query {query_idx + 1}: '{query[:50]}...'")
            # Use synchronous retriever in async context
            docs = await asyncio.to_thread(
                retriever.get_relevant_documents,
                query
            )

            # Format results
            results = []
            for doc in docs[:top_k_per_query]:
                results.append({
                    "text": doc.page_content,
                    "metadata": {k: v for k, v in doc.metadata.items() if k not in ["id", "distance"]},
                    "id": doc.metadata.get("id"),
                    "source_url": doc.metadata.get("source_url"),
                    "correlation_id": doc.metadata.get("correlation_id"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "distance": doc.metadata.get("distance", 0.0),
                    "query_variant": query_idx + 1,
                })

            logger.debug(f"Query {query_idx + 1}: Retrieved {len(results)} documents")
            return results

        except Exception as e:
            logger.error(f"Query {query_idx + 1} failed: {e}")
            return []

    # Execute all queries in parallel
    tasks = [retrieve_single(query, idx) for idx, query in enumerate(queries)]
    results_list = await asyncio.gather(*tasks)

    return results_list
```

### Step 2: Update Document Retriever

**File**: `src/workflow/nodes/document_retriever.py`

**Current Issue**: Only uses first query variant (line 49)

**Required Changes**:

```python
# NEW: Import RRF functions
from src.workflow.retrieval.reciprocal_rank_fusion import (
    reciprocal_rank_fusion,
    parallel_retrieval
)

# MODIFY: document_retriever function to support both strategies
async def document_retriever(state: WorkflowState) -> WorkflowState:
    """
    Retrieve relevant documents using semantic search.
    Supports both single-query and RRF strategies.
    """
    logger.info("🚀 [NODE START] document_retriever")
    try:
        # ... existing code ...

        # Get retrieval strategy from config
        retrieval_config = config.get("retrieval_config", {})
        retrieval_strategy = retrieval_config.get("retrieval_strategy", "single_query")

        # Check for multiple query variants
        query_variants = []

        if augmented_queries and isinstance(augmented_queries, list):
            query_variants = augmented_queries
            logger.info(f"🔍 Found {len(query_variants)} augmented query variants")

        elif enhanced_query and isinstance(enhanced_query, dict):
            # Extract variants from enhanced_query dict
            if enhanced_query.get("multi_query_variants"):
                query_variants = enhanced_query.get("multi_query_variants")
            elif enhanced_query.get("fusion_perspectives"):
                query_variants = enhanced_query.get("fusion_perspectives")
            # ... other variants ...

        # Decide: Single query or RRF?
        if len(query_variants) > 1 and retrieval_strategy == "reciprocal_rank_fusion":
            # === RECIPROCAL RANK FUSION ===
            logger.info(f"🔀 Using RRF with {len(query_variants)} query variants")

            top_k_per_query = retrieval_config.get("top_k_per_query", 5)
            rrf_k = retrieval_config.get("rrf_k", 60)

            # Execute parallel retrieval
            results_list = await parallel_retrieval(
                queries=query_variants,
                retriever=retriever,
                top_k_per_query=top_k_per_query
            )

            # Apply RRF fusion
            fused_docs = reciprocal_rank_fusion(
                results_list=results_list,
                k=rrf_k,
                final_top_k=top_k
            )

            state["retrieved_documents"] = fused_docs
            state["document_scores"] = [doc.get("rrf_score", 0.0) for doc in fused_docs]

            logger.info(f"✅ RRF Retrieved {len(fused_docs)} fused documents")

        else:
            # === SINGLE QUERY (CURRENT BEHAVIOR) ===
            search_query = query_variants[0] if query_variants else state["query"]
            logger.info(f"🔍 Using single query: '{search_query[:100]}...'")

            # ... existing single query retrieval code ...

        logger.info("✅ [NODE FINISH] document_retriever")

    except Exception as e:
        # ... existing error handling ...
```

### Step 3: Update Workflow Config Passing

**File**: `src/services/conversation/generate_response.py` (or wherever workflow config is built)

**Required Change**: Pass retrieval_strategy from conversation session to workflow config

```python
# When building workflow config, add:
config = {
    # ... existing config ...
    "retrieval_config": {
        "retrieval_strategy": conversation_session.retrieval_strategy,  # NEW
        "top_k_per_query": 5,
        "rrf_k": 60,
        "final_top_k": conversation_session.top_k,
    }
}
```

---

## 📱 Phase 3: Frontend UI Changes - TODO

### Dashboard Changes Required:

#### 1. Conversation Settings Modal
**File**: `dashboard/src/pages/dashboard/management/conversations/*.tsx`

**Add Retrieval Strategy Selector**:

```tsx
// Add to conversation settings form
<Select
  label="Retrieval Strategy"
  description="How to handle multiple query variants"
  value={retrievalStrategy}
  onChange={(value) => setRetrievalStrategy(value)}
  data={[
    {
      value: "single_query",
      label: "Single Query (Fast)",
      description: "Uses only the first query variant - faster but less comprehensive"
    },
    {
      value: "reciprocal_rank_fusion",
      label: "Reciprocal Rank Fusion (Quality)",
      description: "Searches with all variants and merges results - slower but better quality"
    },
  ]}
/>
```

**Conditional Display Logic**:
- Show retrieval strategy selector ONLY when enhancement_strategy is NOT "none"
- Disable when enhancement_strategy is "none" or "native"
- Show tooltip: "Available when using query enhancement strategies (augmented, multi_query, etc.)"

#### 2. API Integration
**File**: `dashboard/src/api/resources/conversation.ts` (or similar)

Update TypeScript types:

```typescript
export interface CreateConversationRequest {
  // ... existing fields ...
  retrieval_strategy?: "single_query" | "reciprocal_rank_fusion";
}

export interface ConversationSession {
  // ... existing fields ...
  retrieval_strategy: "single_query" | "reciprocal_rank_fusion";
}
```

Update API calls to include retrieval_strategy field.

#### 3. UI Display
- Show badge/indicator when RRF is enabled
- Display in conversation info panel: "Retrieval: RRF" or "Retrieval: Single Query"
- Performance indicator: "🐇 Fast" vs "🎯 Quality"

---

## 🧪 Testing Plan

### Backend Tests:

```bash
# Test 1: Create conversation with RRF
curl -X POST http://localhost:8000/api/v1/conversation/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RRF Test Session",
    "enhancement_strategy": "augmented",
    "retrieval_strategy": "reciprocal_rank_fusion",
    "enable_llm_generation": false
  }'

# Test 2: Update to single_query
curl -X PUT http://localhost:8000/api/v1/conversation/sessions/{id}/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "retrieval_strategy": "single_query"
  }'

# Test 3: Query with RRF
# Send a query and verify logs show "Using RRF with N query variants"
```

### Expected Behavior:

**Single Query (Default)**:
- Latency: ~100-150ms
- Uses first query variant only
- Logs: "Using single query: '...'"

**RRF**:
- Latency: ~120-200ms (slightly slower)
- Executes N parallel queries (N = number of variants)
- Logs: "Using RRF with N query variants"
- Logs: "RRF Fusion: Combined N result sets → X fused results"

---

## 📊 Performance Expectations

| Strategy | Latency | Milvus Calls | Quality | Use Case |
|----------|---------|--------------|---------|----------|
| Single Query | ~100ms | 1 | Medium | Speed-critical, simple queries |
| RRF | ~150ms | 4-5 | High | Quality-critical, complex queries |

---

## 🎯 Next Steps

1. ✅ Create `src/workflow/retrieval/__init__.py`
2. ✅ Create `src/workflow/retrieval/reciprocal_rank_fusion.py`
3. ⏳ Modify `src/workflow/nodes/document_retriever.py`
4. ⏳ Update workflow config passing in generate_response service
5. ⏳ Test backend thoroughly
6. ⏳ Implement frontend UI changes
7. ⏳ End-to-end testing

---

## 📝 Migration Notes

**Backward Compatibility**:
- Existing conversations default to `retrieval_strategy="single_query"`
- No database migration needed - field has default value
- Existing behavior unchanged unless user explicitly selects RRF

**MongoDB Document Example**:
```json
{
  "_id": ObjectId("..."),
  "user_id": "...",
  "enhancement_config": {
    "strategy": "augmented",
    "enabled": true
  },
  "retrieval_strategy": "reciprocal_rank_fusion",
  "collection_name": "LongTermMemory",
  "enable_reranking": true,
  "enable_llm_generation": false
}
```

---

## ✅ Status Summary

**Phase 1 (Backend Model/API)**: ✅ COMPLETE
**Phase 2 (Workflow Logic)**: 🔄 IN PROGRESS (50%)
**Phase 3 (Frontend UI)**: ⏳ TODO
