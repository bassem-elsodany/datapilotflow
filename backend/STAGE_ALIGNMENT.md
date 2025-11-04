# Backend-Frontend Stage Alignment

## ✅ FIXED - FINAL CORRECT FLOW

### Backend Events (In Order):
```
1. type: "supervisor_started", stage: "supervisor_init"
   → Frontend: Sets currentStage = 'supervisor_init'

2. type: "supervisor_progress", stage: "supervisor_init_complete"
   → Frontend: Marks 'supervisor_init' as completed, moves to 'intent_detection'

3. type: "supervisor_progress", stage: "intent_detection"
   → Frontend: Marks previous stage complete, sets currentStage = 'intent_detection'

4. **supervisor.execute() runs here - does intent + RAG + Task + Response all together**

5. type: "supervisor_progress", stage: "intent_detection_complete"
   → Frontend: Marks 'intent_detection' as completed, moves to 'rag_agent_executing'
   → Stores details: intent, intent_description, routing_decision, detection_time_ms

6. type: "supervisor_progress", stage: "rag_agent_complete"
   → Frontend: Marks 'rag_agent_executing' as completed, moves to 'task_agent_executing' or 'response_generation'
   → Stores details: documents_retrieved, relevant_documents, strategy_used

7. [IF rag_then_task] type: "supervisor_progress", stage: "task_agent_complete"
   → Frontend: Marks 'task_agent_executing' as completed, moves to 'response_generation'
   → Stores details: task_type, used_rag_context, context_documents

8. type: "supervisor_progress", stage: "response_generation_complete"
   → Frontend: Marks 'response_generation' as completed, moves to 'completed'
   → Stores details: response_length, tokens_estimated, sources_used, generation_time_ms

9. type: "workflow_complete"
   → Frontend: Final completion, modal shows all stages completed
```

### Frontend Stage IDs:
```
1. supervisor_init          ← Shows "Supervisor Orchestration"
2. intent_detection         ← Shows "Intent Detection"
3. rag_agent_executing      ← Shows "RAG Agent Execution" (with subflow when expanded)
4. task_agent_executing     ← Shows "Task Agent Execution" (conditional, only if rag_then_task)
5. response_generation      ← Shows "Response Generation"
```

### Frontend Stage Transition Logic:
```javascript
// When _complete event arrives:
if (stage.endsWith('_complete')) {
  baseStage = stage.replace('_complete', '')
  
  // Mark base stage as completed
  completedStages.push(baseStage)
  
  // Store details for this stage
  stageDetails[baseStage] = { data, message, timestamp, execution_time_ms }
  
  // Move to next stage
  if (baseStage === 'supervisor_init') → next = 'intent_detection'
  if (baseStage === 'intent_detection') → next = 'rag_agent_executing' (or 'task_agent_executing' if task_only)
  if (baseStage === 'rag_agent_executing') → next = 'task_agent_executing' (if rag_then_task) OR 'response_generation'
  if (baseStage === 'task_agent_executing') → next = 'response_generation'
  if (baseStage === 'response_generation') → next = 'completed'
  
  currentStage = next
}
```

### Key Points:
- ✅ We emit ONLY intent_detection as START (before supervisor.execute())
- ✅ We emit RAG/Task/Response as COMPLETE events only (after supervisor.execute())
- ✅ Frontend handles _complete by marking base stage done and moving to next
- ✅ Each completed stage shows detailed information in timeline
- ✅ Stage transitions follow intent routing logic (rag_only vs rag_then_task)

