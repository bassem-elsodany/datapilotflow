# Query Enhancement Chains Implementation

## Overview
Created a dedicated `chains` package under `@workflow/` to improve Opik traceability for query enhancement strategies. Each strategy now uses a dedicated chain that properly instruments LLM calls for observability.

## Architecture

### Chains Package Structure
```
src/workflow/chains/
├── __init__.py
├── step_back_chain.py
├── hyde_chain.py
├── decomposition_chain.py
├── rag_fusion_chain.py
├── multi_query_chain.py
└── query_fusion_chain.py
```

### Chain Design Pattern

Each chain follows a consistent pattern:

1. **Initialization**: Accepts configuration and sets up defaults
2. **Run Method**: Main entry point that conditionally uses Opik tracking
3. **Opik Integration**: Tracks inputs, outputs, and metadata when `AGENT_TRACING_ENABLED=True`
4. **Prompt Usage**: Uses prompts from `@prompts/` package
5. **Error Handling**: Graceful error handling with detailed logging

### Chain Features

#### 1. **StepBackChain**
- **Purpose**: Generate broader conceptual questions
- **LLM Call**: Yes
- **Opik Tracking**: Full traceability of step-back generation
- **Metadata**: Temperature, max_tokens, execution_time_ms, llm_model

#### 2. **HyDEChain**
- **Purpose**: Generate hypothetical answers for better embeddings
- **LLM Call**: Yes
- **Opik Tracking**: Full traceability of HyDE generation
- **Metadata**: Temperature, max_tokens, style, answer_length_words, execution_time_ms

#### 3. **DecompositionChain**
- **Purpose**: Break complex queries into sub-questions
- **LLM Call**: Yes
- **Opik Tracking**: Full traceability of decomposition process
- **Metadata**: Temperature, max_tokens, max_sub_queries, num_sub_queries, is_complex

#### 4. **RAGFusionChain**
- **Purpose**: Generate multiple query perspectives
- **LLM Call**: Yes
- **Opik Tracking**: Full traceability of perspective generation
- **Metadata**: Temperature, max_tokens, num_perspectives, execution_time_ms

#### 5. **MultiQueryChain**
- **Purpose**: Generate alternative phrasings
- **LLM Call**: Yes
- **Opik Tracking**: Full traceability of variant generation
- **Metadata**: Temperature, max_tokens, num_variants, execution_time_ms

#### 6. **QueryFusionChain**
- **Purpose**: Combine original and enhanced queries
- **LLM Call**: No (pure combination logic)
- **Opik Tracking**: Tracks combination process
- **Metadata**: include_original, max_total_queries, num_queries

## Opik Integration

### Conditional Tracking
All chains check `settings.AGENT_TRACING_ENABLED` to conditionally enable Opik tracking:

```python
if settings.AGENT_TRACING_ENABLED:
    return await self._run_with_opik(query, llm_client, start_time, **kwargs)
else:
    return await self._run_without_opik(query, llm_client, start_time, **kwargs)
```

### Tracked Information

Each chain tracks:
- **Input**: Original query and parameters
- **Output**: Generated results (step-back query, variants, etc.)
- **Metadata**: 
  - Configuration parameters (temperature, max_tokens, etc.)
  - Execution metrics (execution_time_ms)
  - LLM details (model_name)
  - Result statistics (num_variants, answer_length, etc.)

### Opik Dashboard View

With chains, the Opik dashboard now shows:
1. **Chain-level traces**: Each strategy execution as a separate chain
2. **Prompt versioning**: Prompts from `@prompts/` are versioned
3. **Execution flow**: Clear hierarchy of operations
4. **Performance metrics**: Execution time per chain
5. **Input/Output inspection**: Full visibility into transformations

## Strategy Integration

### Updated Strategy Pattern

Strategies now:
1. Initialize their corresponding chain in `__init__`
2. Delegate LLM calls to the chain in `transform()`
3. Process chain results and return `TransformResult`

### Example: StepBackStrategy

```python
class StepBackStrategy(QueryStrategy):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="step_back", ...)
        self.chain = StepBackChain(config=self.config)  # Initialize chain
    
    async def transform(self, query: str, state: Dict[str, Any]) -> TransformResult:
        # Get LLM client
        llm_client = state.get("config", {}).get("llm_client")
        
        # Execute chain (with Opik tracing if enabled)
        chain_result = await self.chain.run(query=query, llm_client=llm_client)
        
        if not chain_result["success"]:
            raise ValueError(chain_result.get("error"))
        
        # Process result and return TransformResult
        return TransformResult(
            strategy_name=self.name,
            transformed_queries=[chain_result["step_back_query"]],
            ...
        )
```

## Benefits

### 1. **Improved Observability**
- Each strategy execution is now a traceable chain in Opik
- Clear visibility into what each strategy is doing
- Easy debugging of strategy failures

### 2. **Better Prompt Management**
- Prompts are centralized in `@prompts/`
- Opik tracks prompt versions
- Easy to A/B test different prompts

### 3. **Performance Monitoring**
- Execution time tracked per chain
- Identify slow strategies
- Optimize based on metrics

### 4. **Consistent Error Handling**
- All chains follow the same error handling pattern
- Graceful degradation
- Detailed error logging

### 5. **Maintainability**
- Clear separation of concerns
- Chain logic separate from strategy logic
- Easy to add new chains/strategies

## Configuration

### Enable Opik Tracing

In `config.py`:
```python
AGENT_TRACING_ENABLED: bool = Field(
    default=False,
    description="Whether to enable agent tracing and prompt versioning with Opik"
)
```

Set environment variable:
```bash
export AGENT_TRACING_ENABLED=true
```

### Opik URL Override

```python
OPIK_URL_OVERRIDE: Optional[str] = Field(
    default="http://localhost:5173/api",
    description="Override Opik URL for custom deployment"
)
```

## Next Steps

### Remaining Strategies to Update

The following strategies still need to be updated to use chains:
- ✅ StepBackStrategy (DONE)
- ⏳ HyDEStrategy
- ⏳ DecompositionStrategy
- ⏳ RAGFusionStrategy
- ⏳ MultiQueryStrategy
- ⏳ QueryFusionStrategy

### Update Process

For each strategy:
1. Import the corresponding chain
2. Initialize chain in `__init__`
3. Replace direct LLM calls with `chain.run()`
4. Process chain results
5. Test with Opik enabled/disabled

## Testing

### Test with Opik Disabled
```bash
export AGENT_TRACING_ENABLED=false
python -m pytest tests/workflow/test_query_enhancement.py
```

### Test with Opik Enabled
```bash
export AGENT_TRACING_ENABLED=true
export OPIK_URL_OVERRIDE=http://localhost:5173/api
python -m pytest tests/workflow/test_query_enhancement.py
```

### Verify Opik Dashboard
1. Start Opik server
2. Run query enhancement
3. Check Opik dashboard for chain traces
4. Verify all metadata is captured

## Files Modified

### New Files
- `src/workflow/chains/__init__.py`
- `src/workflow/chains/step_back_chain.py`
- `src/workflow/chains/hyde_chain.py`
- `src/workflow/chains/decomposition_chain.py`
- `src/workflow/chains/rag_fusion_chain.py`
- `src/workflow/chains/multi_query_chain.py`
- `src/workflow/chains/query_fusion_chain.py`

### Modified Files
- `src/workflow/query_enhancement/strategies/step_back_strategy.py` (Updated to use StepBackChain)

### Pending Modifications
- `src/workflow/query_enhancement/strategies/hyde_strategy.py`
- `src/workflow/query_enhancement/strategies/decomposition_strategy.py`
- `src/workflow/query_enhancement/strategies/rag_fusion_strategy.py`
- `src/workflow/query_enhancement/strategies/multi_query_strategy.py`
- `src/workflow/query_enhancement/strategies/query_fusion_strategy.py`

## Summary

✅ Created dedicated chains package for query enhancement
✅ Implemented 6 chain classes with Opik integration
✅ Updated StepBackStrategy to use StepBackChain
✅ Conditional Opik tracking based on configuration
✅ Comprehensive metadata tracking
✅ Consistent error handling across all chains

The chains architecture provides full traceability of query enhancement strategies in Opik, making it easy to monitor, debug, and optimize the RAG pipeline.

