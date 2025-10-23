# Quick Start: New Job Event Listener

## ✅ Migration Complete!

The Job Event Listener now uses the **NEW refactored architecture** with the orchestrator and pipeline pattern.

## Start the Listener

```bash
# From the backend directory
python run_job_event_listener.py
```

## Expected Output

```
================================================================================
Starting Job Event Listener with NEW REFACTORED ARCHITECTURE
Using: Orchestrator + Pipeline Pattern + Modular Steps
================================================================================
2025-10-21 ... | INFO | ... | JobEventListener initialized with NEW refactored architecture
2025-10-21 ... | INFO | ... | RefactoredKnowledgeJobEventProcessor initialized
2025-10-21 ... | INFO | ... | Connected to RabbitMQ...
2025-10-21 ... | INFO | ... | Listening for job events on queue: job_execution_events
```

## Test It

1. **Go to UI:** Dashboard → Management → Knowledge Sources → Jobs
2. **Select a job**
3. **Click "Execute Job"**
4. **Watch the logs** for:
   ```
   [NEW ARCHITECTURE] Processing knowledge_job_action_requested for job <id>
   [NEW ARCHITECTURE] Delegating to RefactoredKnowledgeJobEventProcessor
   [ORCHESTRATOR] Starting job execution
   [PIPELINE] Executing step: ExtractionStep
   [PIPELINE] Executing step: ChunkingStep
   [PIPELINE] Executing step: EmbeddingStep
   [PIPELINE] Executing step: StorageStep
   [PIPELINE] Executing step: TimelineStep
   Job <id> execution completed: X docs, Y chunks
   ```

## What Changed

| Component | Old | New |
|-----------|-----|-----|
| **Event Processor** | 367 lines monolithic | 44 lines delegator |
| **Job Processor** | 701 lines God object | Modular pipeline steps |
| **Architecture** | Tightly coupled | Dependency injection |
| **Testing** | Difficult | Each step testable |
| **Extensibility** | Hard to add features | Add new pipeline steps |

## Architecture

```
RabbitMQ → JobEventListener → RefactoredProcessor → Orchestrator → Pipeline
                                                                      ├─ ExtractionStep
                                                                      ├─ ChunkingStep
                                                                      ├─ EmbeddingStep
                                                                      ├─ StorageStep
                                                                      └─ TimelineStep
```

## Files Modified

1. ✅ `src/services/events_listeners/job_event_listener.py`
2. ✅ `run_job_event_listener.py`

## Next Steps

Once you verify everything works:

1. ✅ Test several jobs
2. ✅ Monitor for errors
3. 🔜 Delete old processor files (when ready):
   - `src/processors/knowledge_job/knowledge_job_processor.py`
   - `src/processors/knowledge_job/knowledge_job_event_processor.py`

## Need Help?

See: [RABBITMQ_LISTENER_MIGRATION_COMPLETE.md](./RABBITMQ_LISTENER_MIGRATION_COMPLETE.md)

---

🎉 **You can now disable the old listener!** The new one is ready to go.
