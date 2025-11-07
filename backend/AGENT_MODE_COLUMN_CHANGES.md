# Agent Mode Column - Implementation Summary

## Overview
Added an "Agent Mode" column to the knowledge-search dashboard to display whether each conversation is using "RAG" mode or "Assistant" (Supervisor) mode.

---

## Backend Changes

### File: `src/api/routers/conversation/conversation_router.py`

**Lines 163-174:** Added agent mode detection and serialization

```python
def _serialize_conversation_to_response(session: "ConversationSession") -> dict:
    """Serialize ConversationSession to API response format (new nested structure)."""
    # Determine agent mode based on assistant_config
    agent_mode = "assistant" if (session.assistant_config and session.assistant_config.enabled) else "rag"
    
    response = {
        "id": session._id,
        "name": session.name or f"Session {session._id[:8]}",
        "description": session.description,
        "created_at": session.created_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "message_count": session.message_count,
        "tags": session.tags or [],
        "agent_mode": agent_mode,  # "rag" or "assistant"
    }
```

**Logic:**
- If `session.assistant_config` exists AND `session.assistant_config.enabled == True` → `"assistant"`
- Otherwise → `"rag"`

**API Response Example:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": "67890abcdef",
      "name": "My RAG Conversation",
      "agent_mode": "rag",
      "message_count": 5,
      ...
    },
    {
      "id": "12345abcdef",
      "name": "My Assistant Conversation",
      "agent_mode": "assistant",
      "message_count": 10,
      ...
    }
  ]
}
```

---

## Frontend Changes

### File: `dashboard/src/pages/dashboard/apps/knowledge/knowledge-search.tsx`

#### 1. Updated Conversation Interface (Lines 23-31)
```typescript
interface Conversation {
  id: string;
  sessionName: string;
  messageCount: number;
  agentMode?: 'rag' | 'assistant'; // NEW: Agent mode type
  messages?: Message[];
  createdAt?: string;
  updatedAt?: string;
}
```

#### 2. Added Icons (Lines 9, 17)
```typescript
import {
  IconBrain,    // NEW: for RAG mode
  IconRobot,    // NEW: for Assistant mode
  // ... other icons
} from '@tabler/icons-react';
```

#### 3. Updated Data Mapping (Lines 84-91)
```typescript
const mappedSessions = (data.sessions || []).map((session: any) => ({
  id: session.id,
  sessionName: session.name,
  messageCount: session.message_count,
  agentMode: session.agent_mode || 'rag', // NEW: Map agent_mode field
  createdAt: session.created_at,
  updatedAt: session.created_at,
}));
```

#### 4. Added Agent Mode Column (Lines 293-310)
```typescript
{
  accessor: 'agentMode',
  title: 'Agent Mode',
  width: 150,
  sortable: true,
  render: (session) => {
    const isAssistant = session.agentMode === 'assistant';
    return (
      <Badge
        variant="light"
        color={isAssistant ? 'violet' : 'blue'}
        leftSection={isAssistant ? <IconRobot size={14} /> : <IconBrain size={14} />}
      >
        {isAssistant ? 'Assistant' : 'RAG'}
      </Badge>
    );
  },
}
```

---

## Visual Design

### RAG Mode Badge
- **Color:** Blue
- **Icon:** Brain (IconBrain)
- **Label:** "RAG"
- **Meaning:** Uses traditional RAG workflow (query enhancement → retrieval → judging → generation)

### Assistant Mode Badge
- **Color:** Violet/Purple
- **Icon:** Robot (IconRobot)
- **Label:** "Assistant"
- **Meaning:** Uses Supervisor multi-agent orchestration (RAG Expert + Task Expert)

---

## Table Layout

The new column appears in this order:

| Session Name | **Agent Mode** | Messages | Created | Updated | Actions |
|-------------|---------------|----------|---------|---------|---------|
| My RAG Chat | 🧠 RAG       | 5        | ...     | ...     | Open ⋮  |
| My Bot Chat | 🤖 Assistant | 10       | ...     | ...     | Open ⋮  |

---

## Key Features

✅ **Sortable Column** - Users can sort by agent mode
✅ **Visual Badges** - Easy to distinguish at a glance
✅ **Default Value** - Falls back to "rag" if backend doesn't provide agent_mode
✅ **Type Safe** - TypeScript ensures only 'rag' or 'assistant' values
✅ **Backward Compatible** - Works with existing conversations

---

## Testing

### Backend
```bash
# Syntax validation
python3 -m py_compile src/api/routers/conversation/conversation_router.py
# ✅ Backend syntax is valid
```

### Frontend
```bash
# No linter errors
# ✅ TypeScript compilation successful
```

---

## Impact

- **Backend:** GET `/conversations` endpoint now includes `agent_mode` field
- **Frontend:** Knowledge Search table displays agent mode for all conversations
- **User Experience:** Users can immediately see which conversations use RAG vs Assistant mode
- **Backward Compatible:** Existing code continues to work; new field is additive

