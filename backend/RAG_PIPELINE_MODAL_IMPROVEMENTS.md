# RAG Pipeline Processing Modal - Improvements

## Changes Made

### 1. Hide Disabled Pipeline Steps ✅

**Issue:** Reranking and Query Enhancement steps were shown as "skipped" even when disabled in conversation settings.

**Fix:** Completely remove disabled stages from the timeline instead of showing them as "skipped"

**Implementation:**
- Changed timeline rendering to use `activeStages` (filtered list) instead of all `stages`
- `activeStages` is already filtered in line 277: `const activeStages = stages.filter(s => s.status !== 'skipped');`
- Removed the "Skipped indicator" section that was showing disabled stages
- Removed unused `IconArrowRight` import

**Before:**
```
Timeline showed:
1. Query Enhancement (skipped)
2. Document Retrieval (active)
3. Document Reranking (skipped)
4. Response Generation (pending)
```

**After:**
```
Timeline shows only active stages:
1. Document Retrieval (active)
2. Response Generation (pending)
```

### 2. Show Enhanced Query Prominently ✅

**Issue:** Enhanced query was shown but not prominently enough, users might miss it

**Fix:** Made the enhanced query section more visible with better styling

**Improvements:**
1. **Visual Distinction:**
   - Background color changes to violet when query is enhanced
   - Border color changes to violet to draw attention
   - Filled violet badge on divider saying "Query Enhanced"

2. **Better Labels:**
   - Changed "USER QUERY" to "ORIGINAL QUERY" for clarity
   - Made "ENHANCED QUERY" label bold and violet colored
   - Enhanced query text is now bold (`fw={500}`) and colored violet

3. **Enhanced Divider:**
   - Added a divider with a badge between original and enhanced query
   - Makes it immediately clear that enhancement occurred

**Before:**
```
┌──────────────────────────────┐
│ USER QUERY                    │
│ What is machine learning?     │
│                               │
│ ─────────────────────────    │
│                               │
│ ENHANCED QUERY                │
│ [enhanced text]               │
└──────────────────────────────┘
```

**After:**
```
┌──────────────────────────────┐ ← Violet background
│ ORIGINAL QUERY                │
│ What is machine learning?     │
│                               │
│ ───── Query Enhanced ─────   │ ← Badge on divider
│                               │
│ ✨ ENHANCED QUERY             │ ← Bold violet text
│ [enhanced text in bold]       │
└──────────────────────────────┘
```

## Files Modified

### `dashboard/src/components/workflow-progress-modal.tsx`

**Changes:**
1. Line 17-30: Removed `IconArrowRight` import (unused)
2. Line 389-438: Enhanced query comparison card with:
   - Dynamic background color (violet when enhanced)
   - Dynamic border color (violet when enhanced)
   - "ORIGINAL QUERY" instead of "USER QUERY"
   - Divider with "Query Enhanced" badge
   - Bold violet styling for enhanced query
3. Line 427-432: Changed timeline to use `activeStages` instead of `stages`
4. Line 433-540: Removed skipped stage indicator code

## How It Works

### Stage Filtering Logic

The modal already had logic to determine stage status:

```typescript
// In stage definition (line 102-128)
status: metadata.strategy && metadata.strategy !== 'native'
  ? getStageStatus('query_enhancement')
  : 'skipped',  // ← Native queries skip enhancement

status: rerankingEnabled
  ? getStageStatus('document_judging')
  : 'skipped',  // ← Disabled reranking skips this stage
```

Then stages are filtered (line 277):
```typescript
const activeStages = stages.filter(s => s.status !== 'skipped');
```

**Now** we render only `activeStages` in the timeline, so skipped stages don't appear at all.

### Enhanced Query Display Logic

The enhanced query section only appears when:
1. `metadata.originalQuery` exists
2. `metadata.enhancedQuery` exists
3. Enhanced query is different from original query

```typescript
{metadata.enhancedQuery && metadata.enhancedQuery !== metadata.originalQuery && (
  // Enhanced query section
)}
```

When these conditions are met:
- Card background becomes violet (`theme.colors.violet[0]`)
- Card border becomes violet (`theme.colors.violet[3]`)
- Divider shows "Query Enhanced" badge
- Enhanced query text is bold and violet colored

## Testing Checklist

### Test Case 1: Native Query (No Enhancement)
- [ ] Start conversation with "Native RAG" strategy
- [ ] Send a query
- [ ] Verify modal shows NO "Query Enhancement" stage
- [ ] Verify only original query is shown (no enhanced query section)

### Test Case 2: Enhanced Query (HyDE, Multi-Query, etc.)
- [ ] Start conversation with enhancement strategy (e.g., "HyDE")
- [ ] Send a query
- [ ] Verify "Query Enhancement" stage appears in timeline
- [ ] Verify both original and enhanced queries are shown
- [ ] Verify enhanced query section has violet background
- [ ] Verify divider shows "Query Enhanced" badge
- [ ] Verify enhanced query text is bold and violet colored

### Test Case 3: Reranking Disabled
- [ ] Start conversation with reranking disabled
- [ ] Send a query
- [ ] Verify modal shows NO "Document Reranking" stage
- [ ] Verify timeline goes directly from "Document Retrieval" to "Response Generation"

### Test Case 4: Reranking Enabled
- [ ] Start conversation with reranking enabled
- [ ] Send a query
- [ ] Verify "Document Reranking" stage appears in timeline
- [ ] Verify stage shows relevance judgment substages

### Test Case 5: LLM Generation Disabled
- [ ] Start conversation with LLM generation disabled
- [ ] Send a query
- [ ] Verify final stage is "Raw Response Formatting" (not "Response Generation")
- [ ] Verify substages show "Structuring documents" and "Formatting raw content"

## Expected User Experience

### Scenario 1: User selects "HyDE" strategy

**Before:**
- User sees "Query Enhancement (skipped)" in timeline (confusing!)
- Enhanced query shown but easy to miss

**After:**
- User sees "Query Enhancement" as active stage
- Enhanced query prominently displayed with violet styling
- Clear "Query Enhanced" badge on divider
- User immediately understands their query was modified

### Scenario 2: User disables reranking

**Before:**
- Timeline shows "Document Reranking (skipped)" (clutters UI)
- Takes up space unnecessarily

**After:**
- Reranking stage completely absent from timeline
- Cleaner, more focused pipeline view
- Only shows steps that are actually running

## Benefits

1. **Clearer Pipeline Visualization**
   - Users only see stages that are actually executing
   - No confusion about "skipped" stages
   - Better understanding of what's happening

2. **Enhanced Query Visibility**
   - Impossible to miss when query is enhanced
   - Clear visual distinction between original and enhanced
   - Users understand how their query was modified

3. **Better User Experience**
   - Less clutter in modal
   - More prominent important information
   - Easier to track progress

4. **Accurate Progress Tracking**
   - Progress bar reflects only active stages
   - "X of Y stages completed" is accurate
   - No misleading stage counts

## Summary

✅ **Fixed:** Skipped stages now completely hidden from timeline
✅ **Fixed:** Enhanced query now prominently displayed with violet styling
✅ **Improved:** Cleaner modal UI with only relevant stages
✅ **Improved:** Better visual hierarchy for query enhancement
✅ **Improved:** More accurate progress tracking
