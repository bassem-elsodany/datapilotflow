# Conversation Settings Feature Implementation

## Overview
Added the ability for users to dynamically change LLM provider, model, query enhancement strategy, and vector database collection during an active conversation.

## Changes Made

### Frontend: `dashboard/src/pages/dashboard/apps/knowledge/conversation-window.tsx`

#### 1. New Imports
- Added `Modal`, `Select`, `Divider` from Mantine components
- Added `IconSettings`, `IconCheck`, `IconAlertCircle` icons
- Added `useGetActiveModelProviders` and `useGetCollections` hooks

#### 2. New State Variables
```typescript
// Settings modal state
const [settingsModalOpen, setSettingsModalOpen] = useState(false);
const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [selectedStrategy, setSelectedStrategy] = useState<string>('query_fusion');
const [collectionName, setCollectionName] = useState('LongTermMemory');
const [isSavingSettings, setIsSavingSettings] = useState(false);
```

#### 3. Enhancement Strategies Constant
```typescript
const ENHANCEMENT_STRATEGIES = [
  { value: 'none', label: 'None' },
  { value: 'query_fusion', label: 'Query Fusion (Recommended)' },
  { value: 'step_back', label: 'Step-Back' },
  { value: 'multi_query', label: 'Multi-Query' },
  { value: 'hyde', label: 'HyDE' },
  { value: 'decomposition', label: 'Decomposition' },
  { value: 'rag_fusion', label: 'RAG Fusion' },
];
```

#### 4. Load Current Settings
Modified `loadConversationHistory()` to load and populate current conversation settings:
- LLM Provider ID
- LLM Model Name
- Enhancement Strategy
- Vector DB Collection Name

#### 5. Save Settings Function
```typescript
const handleSaveSettings = async () => {
  // Calls PUT /api/v1/conversations/{sessionId}/config
  // Updates: llm_provider_id, llm_model_name, enhancement_strategy, collection_name
  // Shows success/error notifications
}
```

#### 6. UI Components

**Input Area Layout**
- Text input field (flex: 1)
- Send button directly beside the input
- Settings button after the Send button
- Current settings displayed as dimmed text below the input:
  - Provider name (with model if selected)
  - Enhancement strategy
  - Vector DB collection name

**Settings Button**
- Positioned after the Send button
- Blue ActionIcon with IconSettings
- Opens settings modal when clicked
- Disabled during loading states

**Settings Modal**
- Organized into three sections:
  1. **LLM Provider**: Provider selection + Model selection (conditional)
  2. **Query Enhancement**: Strategy dropdown
  3. **Vector Database**: Collection dropdown with record counts
- Cancel and Save buttons
- Loading states during save operation

## User Flow

1. User opens a conversation
2. Current settings are loaded automatically
3. **Current settings are always visible** as dimmed text below the input field:
   - Example: `Provider: OpenAI (gpt-4) • Strategy: Query Fusion (Recommended) • Collection: LongTermMemory`
4. To change settings, user clicks the Settings icon (⚙️) after the Send button
5. Modal opens showing current configuration
6. User modifies any settings:
   - Change LLM provider and/or model
   - Select different query enhancement strategy
   - Choose different vector DB collection
7. User clicks "Save Settings"
8. Settings are persisted to the backend
9. Success notification is shown
10. Modal closes and updated settings are reflected in the dimmed text below the input

## API Endpoint Used

### GET `/api/v1/conversations/{conversation_id}`
Returns conversation details including current settings:
```json
{
  "session": {
    "llm_provider_id": "provider-id",
    "llm_model_name": "gpt-4",
    "enhancement_config": {
      "strategy": "query_fusion"
    },
    "collection_name": "LongTermMemory"
  }
}
```

### PUT `/api/v1/conversations/{conversation_id}/config`
Updates conversation configuration:
```json
{
  "llm_provider_id": "provider-id",
  "llm_model_name": "gpt-4",
  "enhancement_strategy": "query_fusion",
  "collection_name": "LongTermMemory"
}
```

## Key Features

1. **Real-time Configuration**: Users can change settings mid-conversation
2. **Persistent Settings**: Configuration is saved to the database
3. **Visual Feedback**: Loading states and success/error notifications
4. **Smart Defaults**: Loads current settings on conversation open
5. **Validation**: Dropdowns prevent invalid selections
6. **Accessibility**: Tooltips and clear labels for all controls
7. **Responsive**: Modal adapts to screen size

## Benefits

- **Transparency**: Current settings are always visible below the input field
- **Flexibility**: Users can experiment with different LLM providers without creating new conversations
- **Optimization**: Switch to faster/cheaper models for simple queries
- **Testing**: Compare different enhancement strategies on the same conversation
- **Collection Switching**: Query different knowledge bases without losing context
- **User Experience**: Settings are always accessible, never more than 2 clicks away
- **Visual Clarity**: Dimmed text doesn't distract from the main conversation flow

## Technical Notes

- Input area uses a Stack layout with the input/buttons on top and settings display below
- Send button is directly beside the input field for quick access
- Settings icon is positioned after the Send button
- Current settings are displayed as dimmed text with bullet separators
- Modal uses Mantine's theming for consistent styling
- All API calls include proper error handling
- State is synchronized between conversation history and settings modal
- Providers and collections are fetched using React Query hooks for automatic caching

## Future Enhancements

- Add settings history/versioning
- Allow per-message strategy override
- Add advanced settings (temperature, top_k, etc.)
- Export/import conversation settings as templates
- Add color coding for different strategies in the display
- Show provider status (active/inactive) in real-time

