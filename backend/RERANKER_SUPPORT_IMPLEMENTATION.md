# Reranker Support Implementation

## Overview
Extended the model provider system to support **reranking** as a distinct capability alongside embeddings and generative AI.

## Business Requirements

### Provider Capabilities

| Provider | Embeddings | Generative AI | Reranker | Notes |
|----------|-----------|---------------|----------|-------|
| **Cohere** | ✅ | ✅ | ✅ | Dedicated reranker models (primary role) |
| **Voyage AI** | ✅ | ❌ | ✅ | Dedicated reranker models (primary role) |
| **OpenAI** | ✅ | ✅ | ❌ | Can be used for reranking but not primary role |
| **Anthropic** | ✅ | ✅ | ❌ | Can be used for reranking but not primary role |
| **Google** | ✅ | ✅ | ❌ | Can be used for reranking but not primary role |
| **Hugging Face** | ✅ | ✅ | ❌ | Can be used for reranking but not primary role |
| **Ollama** | ✅ | ✅ | ❌ | No reranking support |
| **Groq** | ❌ | ✅ | ❌ | No reranking support |

## Changes Made

### 1. Domain Model Updates (`src/domain/model_provider/model_provider.py`)

#### ModelType Enum
```python
class ModelType(str, Enum):
    EMBEDDING = "embedding"
    GENERATIVE = "generative"
    RERANKER = "reranker"  # NEW
    BOTH = "both"  # Now supports multiple model types
```

#### ModelProvider Class
- Added `reranker: Optional[ModelTypeConfig]` field
- Added `reranker_models` property
- Updated `supported_model_types` property to include `RERANKER`

#### ModelProviderCreate Class
- Added `reranker: Optional[ModelTypeConfig]` field

#### ModelProviderResponse Class
- Added `reranker: Optional[ModelTypeConfig]` field
- Added `reranker_models` property
- Updated `supported_model_types` property to include `RERANKER`

### 2. Initialization Service Updates (`src/services/model_provider/model_provider_initialization_service.py`)

#### New Providers Added

**Cohere** (Full Support: Embeddings + Generative + Reranker)
```python
{
    "name": "Cohere",
    "provider_type": "cohere",
    "endpoint": "https://api.cohere.ai/v1",
    "api_key_env_var": "COHERE_API_KEY",
    "embedding": {
        "models": [
            "embed-english-v3.0",
            "embed-english-light-v3.0",
            "embed-multilingual-v3.0",
            "embed-multilingual-light-v3.0"
        ]
    },
    "generative": {
        "models": [
            "command-r-plus",
            "command-r",
            "command",
            "command-light"
        ]
    },
    "reranker": {
        "models": [
            "rerank-english-v3.0",
            "rerank-multilingual-v3.0",
            "rerank-english-v2.0",
            "rerank-multilingual-v2.0"
        ],
        "config": {
            "endpoint_suffix": "/rerank",
            "max_documents": 1000,
            "top_n": 10
        }
    }
}
```

**Voyage AI** (Embeddings + Reranker)
```python
{
    "name": "Voyage AI",
    "provider_type": "voyage",
    "endpoint": "https://api.voyageai.com/v1",
    "api_key_env_var": "VOYAGE_API_KEY",
    "embedding": {
        "models": [
            "voyage-large-2",
            "voyage-code-2",
            "voyage-2",
            "voyage-lite-02-instruct"
        ]
    },
    "generative": None,
    "reranker": {
        "models": [
            "rerank-lite-1",
            "rerank-1"
        ],
        "config": {
            "endpoint_suffix": "/rerank",
            "max_documents": 1000,
            "top_n": 10
        }
    }
}
```

#### Updated Existing Providers
All existing providers now explicitly declare `reranker: None` to indicate they don't support dedicated reranking:
- OpenAI: `"reranker": None  # Can be used for reranking but not primary role`
- Anthropic: `"reranker": None  # Can be used for reranking but not primary role`
- Google: `"reranker": None  # Can be used for reranking but not primary role`
- Hugging Face: `"reranker": None  # Can be used for reranking but not primary role`
- Ollama: `"reranker": None  # Doesn't support reranking`
- Groq: `"reranker": None  # Doesn't support reranking`

#### Method Updates

**`get_provider_config_for_model_type()`**
- Added `has_reranker` check
- Added `ModelType.RERANKER` handling in conditional logic
- Returns reranker config when requested

**`get_provider_summary()`**
- Added `"supports_reranker"` field
- Added `"reranker_models_count"` field

**`get_providers_by_api_key_requirement()`**
- Added `"supports_reranker"` field to filtered results

## Environment Variables

### New Required API Keys
```bash
# Cohere (for embeddings, generative, and reranking)
COHERE_API_KEY=your_cohere_api_key

# Voyage AI (for embeddings and reranking)
VOYAGE_API_KEY=your_voyage_api_key
```

## Usage Examples

### Using Cohere for Reranking
```python
from src.services.model_provider.model_provider_initialization_service import ModelProviderInitializationService
from src.domain.model_provider.model_provider import ModelType

service = ModelProviderInitializationService()

# Get Cohere reranker configuration
config = service.get_provider_config_for_model_type("Cohere", ModelType.RERANKER)

# Available models: rerank-english-v3.0, rerank-multilingual-v3.0, etc.
```

### Using Voyage AI for Reranking
```python
# Get Voyage AI reranker configuration
config = service.get_provider_config_for_model_type("Voyage AI", ModelType.RERANKER)

# Available models: rerank-lite-1, rerank-1
```

### Checking Provider Capabilities
```python
# Get summary of all providers
summary = service.get_provider_summary()

for provider in summary:
    if provider["supports_reranker"]:
        print(f"{provider['name']}: {provider['reranker_models_count']} reranker models")
```

## Reranking in Conversation Workflow

The `enable_reranking` flag in the conversation model now has two implementation options:

1. **Use Dedicated Reranker** (Cohere/Voyage AI)
   - When `enable_reranking=True` and a reranker provider is configured
   - Use dedicated reranking models for optimal performance

2. **Use LLM for Reranking** (OpenAI/Anthropic/Google/etc.)
   - When `enable_reranking=True` but no dedicated reranker is configured
   - Use the conversation's LLM to perform reranking via prompting

## Next Steps

1. **Implement Reranker Client** (`src/infrastructure/reranker/`)
   - Create `RerankerClient` for Cohere
   - Create `RerankerClient` for Voyage AI
   - Add factory pattern for reranker selection

2. **Update Document Judger Node** (`src/workflow/nodes/document_judger.py`)
   - Add logic to detect if a dedicated reranker is available
   - Route to dedicated reranker if available
   - Fallback to LLM-based judging if not

3. **Add Reranker Configuration to Conversation**
   - Add `reranker_provider_id` and `reranker_model_name` to conversation model
   - Allow users to select reranker in conversation creation UI
   - Pass reranker config to workflow state

4. **Update Frontend**
   - Add Cohere and Voyage AI to provider list
   - Add reranker model selection in conversation settings
   - Display reranker capabilities in provider management UI

## Testing

```bash
# Test provider initialization
python -m pytest tests/services/model_provider/test_model_provider_initialization_service.py

# Verify Cohere provider
# Verify Voyage AI provider
# Verify reranker field in all providers
```

## Database Migration

No migration needed - the `reranker` field is optional and will be `null` for existing providers.

## Summary

✅ **Domain Model**: Added `RERANKER` to `ModelType` enum and `reranker` field to all provider models
✅ **Cohere Provider**: Added with full support (embeddings + generative + reranker)
✅ **Voyage AI Provider**: Added with embeddings + reranker support
✅ **Existing Providers**: Updated to explicitly declare `reranker: None`
✅ **Service Methods**: Updated to handle reranker type in all helper methods
✅ **No Linter Errors**: All changes validated

**Total Providers**: 8 (6 existing + 2 new)
**Providers with Dedicated Reranker**: 2 (Cohere, Voyage AI)

