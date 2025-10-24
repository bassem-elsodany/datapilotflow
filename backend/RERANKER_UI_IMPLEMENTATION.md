# Reranker UI Implementation

## Overview
Added comprehensive UI support for document reranking configuration in conversation creation and settings, allowing users to choose between LLM-based judging and dedicated reranker models (Cohere/Voyage AI).

## Backend Changes

### 1. Conversation Model (`conversation_history_service.py`)

#### Updated `ConversationSession` Dataclass
```python
@dataclass
class ConversationSession:
    # ... existing fields ...
    enable_reranking: bool = True  # Enable document judging/reranking by default
    reranker_provider_id: Optional[str] = None  # Dedicated reranker provider (Cohere/Voyage)
    reranker_model_name: Optional[str] = None  # Reranker model name
```

#### Updated `create_conversation` Method
- Added `reranker_provider_id` and `reranker_model_name` parameters
- Added validation for reranker provider (checks if provider exists, is active, and supports reranking)
- Includes reranker settings in `conversation_data` dictionary

#### Updated `update_conversation_config` Method
- Added `enable_reranking`, `reranker_provider_id`, and `reranker_model_name` parameters
- Added validation for reranker provider when updating
- Updates reranker settings in MongoDB

### 2. API Router (`conversation_router.py`)

#### Updated `CreateSessionRequest` Model
```python
class CreateSessionRequest(BaseModel):
    # ... existing fields ...
    enable_reranking: bool = Field(
        True, description="Enable document reranking/judging for better relevance"
    )
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID (Cohere/Voyage AI)"
    )
    reranker_model_name: Optional[str] = Field(
        None, description="Reranker model name"
    )
```

#### Updated `UpdateSessionConfigRequest` Model
```python
class UpdateSessionConfigRequest(BaseModel):
    # ... existing fields ...
    enable_reranking: Optional[bool] = Field(None, description="Enable document reranking")
    reranker_provider_id: Optional[str] = Field(
        None, description="Dedicated reranker provider ID"
    )
    reranker_model_name: Optional[str] = Field(None, description="Reranker model name")
```

#### Updated Endpoints
- `POST /conversations`: Now accepts reranker configuration
- `PUT /conversations/{conversation_id}/config`: Now accepts reranker configuration updates

## Frontend Changes

### 1. Conversation Create Page (`conversation-create.tsx`)

#### New State Variables
```typescript
const [enableReranking, setEnableReranking] = useState(true);
const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
```

#### New UI Section: Document Reranking Configuration
- **Switch**: Enable/disable document reranking
- **Alert**: Explains reranking options (LLM vs. dedicated reranker)
- **Reranker Provider Select**: Filters providers to show only those with reranker support (Cohere/Voyage AI)
- **Reranker Model Select**: Shows available reranker models for selected provider

#### Features
- Automatically clears reranker selection when reranking is disabled
- Filters providers to show only those with `reranker` field and models
- Cascading selection (selecting provider enables model selection)
- Clear descriptions for each option

#### API Payload
```typescript
payload.enable_reranking = enableReranking;
if (enableReranking && selectedRerankerId) {
  payload.reranker_provider_id = selectedRerankerId;
}
if (enableReranking && selectedRerankerModel) {
  payload.reranker_model_name = selectedRerankerModel;
}
```

### 2. Conversation Window Settings Modal (`conversation-window.tsx`)

#### New State Variables
```typescript
const [enableReranking, setEnableReranking] = useState(true);
const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
```

#### Settings Loading
```typescript
// Load conversation settings
if (data.session) {
  setEnableReranking(data.session.enable_reranking !== undefined ? data.session.enable_reranking : true);
  setSelectedRerankerId(data.session.reranker_provider_id || null);
  setSelectedRerankerModel(data.session.reranker_model_name || null);
}
```

#### Settings Saving
```typescript
const payload: any = {
  // ... existing fields ...
  enable_reranking: enableReranking,
  reranker_provider_id: enableReranking ? selectedRerankerId : null,
  reranker_model_name: enableReranking ? selectedRerankerModel : null,
};
```

#### New Modal Section
- Added "Document Reranking" divider
- Switch to enable/disable reranking
- Alert explaining reranking options
- Grid layout with Reranker Provider and Model selects
- Same filtering logic as create page

## User Experience

### Reranking Options

1. **Reranking Disabled** (`enable_reranking: false`)
   - No document judging or reranking
   - Fastest performance
   - Uses raw retrieval results

2. **Reranking Enabled + No Reranker Selected** (`enable_reranking: true`, `reranker_provider_id: null`)
   - Uses conversation's LLM for document judging
   - Slower but works with any LLM provider
   - Good for general use

3. **Reranking Enabled + Dedicated Reranker** (`enable_reranking: true`, `reranker_provider_id: <cohere/voyage>`)
   - Uses specialized reranking models
   - Fastest reranking performance
   - Most accurate relevance scoring
   - Requires Cohere or Voyage AI provider

### UI Flow

#### Creating a Conversation
1. User fills in basic information (name, description)
2. User selects LLM provider and model
3. User selects query enhancement strategy
4. User configures document reranking:
   - Toggle reranking on/off
   - Optionally select dedicated reranker provider
   - Select reranker model (if provider selected)
5. User clicks "Create Conversation"

#### Updating Conversation Settings
1. User clicks settings icon in conversation window
2. Modal opens with current settings loaded
3. User can modify all settings including reranking
4. User clicks "Save Settings"
5. Settings are updated and applied to future queries

## Provider Filtering

Both UI components filter providers to show only those with reranker support:

```typescript
data={providers
  ?.filter((p) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
  .map((p) => ({
    value: p.id,
    label: `${p.name} (${p.provider_type})`,
  })) || []}
```

This ensures only Cohere and Voyage AI appear in the reranker provider dropdown.

## Validation

### Backend Validation
- Checks if reranker provider exists
- Checks if reranker provider is active
- Checks if provider actually supports reranking (`provider.reranker` is not None)
- Returns appropriate error messages if validation fails

### Frontend Validation
- Reranker model select is disabled until provider is selected
- Reranker settings are cleared when reranking is disabled
- Cascading dropdowns ensure consistent selection

## Database Schema

### MongoDB Document Structure
```json
{
  "_id": "conversation_id",
  "user_id": "user_id",
  "name": "Conversation Name",
  "llm_provider_id": "provider_id",
  "llm_model_name": "model_name",
  "enhancement_config": {
    "strategy": "native",
    "enabled": true
  },
  "collection_name": "LongTermMemory",
  "enable_reranking": true,
  "reranker_provider_id": "cohere_provider_id",  // Optional
  "reranker_model_name": "rerank-english-v3.0",  // Optional
  "messages": [],
  "created_at": "2025-10-24T...",
  "last_updated": "2025-10-24T..."
}
```

## API Examples

### Create Conversation with Reranker
```bash
POST /conversations
{
  "name": "My Conversation",
  "llm_provider_id": "openai_provider_id",
  "llm_model_name": "gpt-4o",
  "enhancement_strategy": "native",
  "collection_name": "LongTermMemory",
  "enable_reranking": true,
  "reranker_provider_id": "cohere_provider_id",
  "reranker_model_name": "rerank-english-v3.0"
}
```

### Update Conversation Reranking Settings
```bash
PUT /conversations/{conversation_id}/config
{
  "enable_reranking": true,
  "reranker_provider_id": "voyage_provider_id",
  "reranker_model_name": "rerank-1"
}
```

### Disable Reranking
```bash
PUT /conversations/{conversation_id}/config
{
  "enable_reranking": false,
  "reranker_provider_id": null,
  "reranker_model_name": null
}
```

## Benefits

1. **Flexibility**: Users can choose between LLM judging and dedicated rerankers
2. **Performance**: Dedicated rerankers are faster than LLM-based judging
3. **Accuracy**: Specialized reranking models provide better relevance scoring
4. **Cost Control**: Users can disable reranking for cost-sensitive scenarios
5. **Ease of Use**: Clear UI with helpful descriptions and validation
6. **Consistency**: Same reranking configuration UI in both create and edit flows

## Next Steps

1. **Implement Reranker Client** (`src/infrastructure/reranker/`)
   - Create `CohereRerankerClient`
   - Create `VoyageRerankerClient`
   - Add factory pattern for reranker selection

2. **Update Document Judger Node** (`src/workflow/nodes/document_judger.py`)
   - Check if dedicated reranker is configured
   - Route to dedicated reranker if available
   - Fallback to LLM-based judging if not

3. **Add Reranker to Workflow State**
   - Pass reranker config to workflow
   - Make it available to document_judger node

4. **Testing**
   - Test with Cohere reranker
   - Test with Voyage AI reranker
   - Test LLM fallback
   - Test reranking disabled

## Summary

✅ **Backend**: Added reranker fields to conversation model and API
✅ **Frontend**: Added reranker UI to conversation create page
✅ **Frontend**: Added reranker UI to conversation settings modal
✅ **Validation**: Provider validation and filtering implemented
✅ **UX**: Clear descriptions and helpful alerts
✅ **Flexibility**: Support for LLM judging, dedicated rerankers, or no reranking

**Total Files Modified**: 4
- `backend/src/services/conversation/conversation_history_service.py`
- `backend/src/api/routers/conversation/conversation_router.py`
- `dashboard/src/pages/dashboard/apps/knowledge/conversation-create.tsx`
- `dashboard/src/pages/dashboard/apps/knowledge/conversation-window.tsx`

