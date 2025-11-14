# Tool Instructions: Complete Persistence & Display Fix

## Problem Statement
Users reported that:
1. Generated AI instructions were not being saved to the database
2. When editing an existing conversation with instructions, the instructions were not displayed in the textarea

## Root Causes & Solutions

### Issue 1: Instructions Not Persisting to Database

**Root Cause:** The `AssistantConfigRequest` model in the backend was missing the `tool_instructions` field, so the API rejected or ignored the field when users submitted the form.

**Files Fixed:**
- `src/api/routers/conversation/conversation_router.py`

**Changes Made:**

1. **Added `tool_instructions` to AssistantConfigRequest model (Line 109-111)**
   ```python
   class AssistantConfigRequest(BaseModel):
       enabled: bool
       tools: Optional[List[str]]
       tool_instructions: Optional[str] = Field(
           None, description="User's custom instructions for how tools should work together"
       )
   ```

2. **Added `tool_instructions` to AssistantConfigResponse model (Line 285-287)**
   ```python
   class AssistantConfigResponse(BaseModel):
       enabled: bool
       tools: List[str]
       tool_instructions: Optional[str] = Field(
           None, description="User's custom instructions for how tools should work together"
       )
   ```

3. **Updated create endpoint to pass `tool_instructions` (Line 385)**
   ```python
   assistant_config = AssistantConfig(
       enabled=create_request.assistant_config.enabled,
       tools=create_request.assistant_config.tools if create_request.assistant_config.tools else [],
       tool_instructions=create_request.assistant_config.tool_instructions,  # ← ADDED
   )
   ```

4. **Updated serialization function to include `tool_instructions` in response (Line 221)**
   ```python
   response["assistant_config"] = {
       "enabled": session.assistant_config.enabled,
       "tools": session.assistant_config.tools if session.assistant_config.tools else [],
       "tool_instructions": session.assistant_config.tool_instructions,  # ← ADDED
   }
   ```

5. **Update endpoint already had logic to include `tool_instructions` (Line 712-714)**
   ```python
   if hasattr(config_request.assistant_config, 'tool_instructions') and config_request.assistant_config.tool_instructions:
       assistant_config_dict["tool_instructions"] = config_request.assistant_config.tool_instructions
   ```

**Commit:** `3bbc91e` - "fix: Add tool_instructions persistence for assistant config"

---

### Issue 2: Instructions Not Displaying When Loading Existing Conversation

**Root Cause:** The `ToolInstructionsStep` component's `isExpanded` state was initialized only once when the component mounted (`useState(!!form.values.tool_instructions)`). When the parent component loaded the conversation data asynchronously via `form.setValues()`, the `isExpanded` state was not updated to reflect the newly loaded instructions.

**File Fixed:**
- `dashboard/src/pages/dashboard/apps/knowledge/tool-instructions-step.tsx`

**Changes Made:**

1. **Added `useEffect` import (Line 11)**
   ```typescript
   import { useState, useEffect } from 'react';
   ```

2. **Added `useEffect` hook to watch for changes to `tool_instructions` (Line 28-33)**
   ```typescript
   // Update isExpanded whenever tool_instructions change (e.g., when loading existing conversation)
   useEffect(() => {
     if (form.values.tool_instructions) {
       setIsExpanded(true);
     }
   }, [form.values.tool_instructions]);
   ```

**Commit:** `6fb5c96` - "fix: Auto-expand instructions textarea when loading existing conversation"

---

## Complete Data Flow (After Both Fixes)

### CREATE Flow:
```
User Input in Wizard
  ↓
Form: tool_instructions = "User's custom instructions"
  ↓
Frontend submits: POST /conversations
  {
    "assistant_config": {
      "enabled": true,
      "tools": ["tool-1", "tool-2"],
      "tool_instructions": "User's custom instructions"
    }
  }
  ↓
Backend: create_conversation_session
  - AssistantConfigRequest validates field ✅
  - AssistantConfig(tool_instructions=...) ✅
  - MongoDB saves: assistant_config.tool_instructions ✅
  ↓
Response includes: assistant_config.tool_instructions ✅
```

### EDIT/LOAD Flow:
```
User clicks "Edit Conversation"
  ↓
Frontend: GET /conversations/{id}
  ↓
Backend: _serialize_conversation_to_response
  - response["assistant_config"]["tool_instructions"] = ... ✅
  ↓
Frontend receives:
  {
    "assistant_config": {
      "enabled": true,
      "tools": ["tool-1", "tool-2"],
      "tool_instructions": "Previous instructions"
    }
  }
  ↓
Frontend: form.setValues({tool_instructions: "..."})
  ↓
ToolInstructionsStep detects change via useEffect ✅
  setIsExpanded(true)
  ↓
User sees:
  - Textarea is EXPANDED ✅
  - Instructions are DISPLAYED ✅
```

### AI GENERATION Flow:
```
User clicks "Generate with AI" button
  ↓
Frontend: POST /tools/instructions/generate
  ↓
Backend returns: {"instructions": "AI-generated text", ...}
  ↓
Frontend: form.setFieldValue('tool_instructions', 'AI text')
  ↓
ToolInstructionsStep useEffect triggers ✅
  setIsExpanded(true)
  ↓
User sees:
  - Textarea is EXPANDED ✅
  - AI-generated instructions are DISPLAYED ✅
  - User can edit if needed ✅
  ↓
User clicks Save
  ↓
Frontend: PUT /conversations/{id}
  {
    "assistant_config": {
      "tool_instructions": "AI-generated text"
    }
  }
  ↓
Backend: update_conversation_session
  - Includes tool_instructions in update ✅
  - MongoDB updates: assistant_config.tool_instructions ✅
  ↓
Success ✅
```

### EDIT EXISTING & UPDATE Flow:
```
User loads conversation with existing instructions
  ↓
Instructions auto-expand and display ✅
  ↓
User edits instructions in textarea
  ↓
User clicks "Generate with AI" (overwrites with AI text)
  OR
  User manually edits and clicks Save
  ↓
Frontend: PUT /conversations/{id}
  ↓
Backend saves new instructions ✅
  ↓
Next load shows updated instructions ✅
```

---

## Files Modified

### Backend
**File:** `src/api/routers/conversation/conversation_router.py`
- Line 109-111: Add `tool_instructions` to `AssistantConfigRequest`
- Line 221: Add `tool_instructions` to serialization response
- Line 285-287: Add `tool_instructions` to `AssistantConfigResponse`
- Line 385: Pass `tool_instructions` in create endpoint
- Line 388: Update logging to show `has_instructions`
- Line 712-714: Already had logic to include in update (verified)

**Commit:** `3bbc91e`

### Frontend
**File:** `dashboard/src/pages/dashboard/apps/knowledge/tool-instructions-step.tsx`
- Line 11: Import `useEffect`
- Line 28-33: Add `useEffect` hook to watch `tool_instructions` changes

**Commit:** `6fb5c96`

---

## Testing Checklist

### Test 1: Create with AI-Generated Instructions
```
1. Create new Assistant conversation
2. Select tools
3. Click "Generate with AI"
4. Verify instructions appear
5. Click Save
6. Refresh page
7. Edit conversation
8. Verify instructions display and textarea is expanded
```

**Expected Results:**
- ✅ Instructions generated successfully
- ✅ Textarea auto-expanded showing instructions
- ✅ Instructions saved to database
- ✅ On page refresh, instructions still present
- ✅ On edit, instructions displayed immediately

### Test 2: Create with Manual Instructions
```
1. Create new Assistant conversation
2. Select tools
3. Manually type instructions in textarea
4. Click Save
5. Edit conversation
6. Verify instructions display
```

**Expected Results:**
- ✅ Manual instructions saved
- ✅ On edit, instructions displayed and expanded

### Test 3: Edit Existing with AI Generation
```
1. Load existing conversation with instructions
2. Verify instructions are auto-expanded
3. Click "Generate with AI"
4. Verify new instructions replace old ones
5. Click Save
6. Edit conversation again
7. Verify new instructions are displayed
```

**Expected Results:**
- ✅ Instructions auto-expand on load
- ✅ AI generation overwrites previous instructions
- ✅ New instructions saved to database
- ✅ Next edit shows new instructions

### Test 4: Database Verification
```
Database Query:
db.conversations.find({
  "_id": "conversation_id"
}).pretty()
```

**Expected Results:**
```json
{
  "assistant_config": {
    "enabled": true,
    "tools": ["tool-id-1", "tool-id-2"],
    "tool_instructions": "The actual instructions text"
  }
}
```

---

## Browser Console Logs (Debug)

When loading a conversation, you should see:

```javascript
[DEBUG loadExistingConversation] session.assistant_config: {
  enabled: true,
  tools: ["tool-1", "tool-2"],
  tool_instructions: "Previous instructions"
}

[DEBUG loadExistingConversation] form.values.selectedTools after setValues: ["tool-1", "tool-2"]
```

When saving with instructions, you should see:

```javascript
DEBUG: assistant_config in payload: {
  enabled: true,
  tools: ["tool-1", "tool-2"],
  tools_count: 2
}

DEBUG: Payload being sent: {
  "assistant_config": {
    "enabled": true,
    "tools": ["tool-1", "tool-2"],
    "tool_instructions": "..."
  }
}
```

---

## Summary of Fixes

| Issue | Root Cause | Solution | Commit |
|-------|-----------|----------|--------|
| Instructions not saving | `AssistantConfigRequest` missing field | Added field to model and endpoints | `3bbc91e` |
| Instructions not displaying on load | `isExpanded` not updated after form load | Added `useEffect` to watch changes | `6fb5c96` |
| Instructions not in API response | Serialization missing field | Added field to serialization function | `3bbc91e` |
| Instructions not in create endpoint | Constructor not passing field | Added field to AssistantConfig constructor | `3bbc91e` |

---

## Status

✅ **ALL FIXED AND COMMITTED**

The complete flow now works end-to-end:

1. ✅ AI generates instructions via `/tools/instructions/generate` endpoint
2. ✅ User sees instructions immediately (auto-expand)
3. ✅ User can edit instructions manually
4. ✅ Instructions saved to database on save
5. ✅ Instructions retrieved when loading/editing conversation
6. ✅ Instructions displayed automatically (auto-expand) when editing
7. ✅ Subsequent edits and saves work correctly

Users can now confidently:
- Generate AI-powered tool orchestration instructions
- Save and persist them to database
- Reload conversations and see their saved instructions
- Edit instructions and save changes
- Know their work is being preserved
