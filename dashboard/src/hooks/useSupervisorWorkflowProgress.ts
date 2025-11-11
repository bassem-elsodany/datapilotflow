import { useRef } from 'react';

/**
 * Hook for handling Supervisor-specific workflow progress events
 * Supervisor orchestration stages:
 * supervisor_init_complete → agent_execution_starting → rag_agent_executing → rag_documents_extracted
 * → task_agent_executing (optional) → response_generation_complete → response_streaming_started → workflow_complete
 */
export function useSupervisorWorkflowProgress() {
  // Track timing for each stage
  const stageTimingsRef = useRef<Record<string, { activeTime: number; completionData?: any }>>({});
  const pendingCompletionTimeoutsRef = useRef<Record<string, NodeJS.Timeout>>({});

  const MINIMUM_LOADER_DISPLAY_MS = 500; // Minimum time to show loader before checkmark

  /**
   * Handle Supervisor workflow progress event
   * Returns the state update to apply
   */
  const handleSupervisorWorkflowProgress = (
    data: any,
    currentWorkflowState: any,
    setWorkflowState: (fn: (prev: any) => any) => void
  ) => {
    const supervisorStage = data?.stage || '';
    const isCompleteEvent = supervisorStage.endsWith('_complete');

    console.log(`🤖 [SUPERVISOR WORKFLOW] ${isCompleteEvent ? '✅ COMPLETE' : '▶️ START'} - ${supervisorStage}`);

    if (isCompleteEvent) {
      // COMPLETE EVENT: Store data and schedule delayed completion
      const completedStage = supervisorStage.replace('_complete', '');
      console.log(`✅ [SUPERVISOR COMPLETE] ${completedStage} - scheduling completion after ${MINIMUM_LOADER_DISPLAY_MS}ms`);

      const elapsedSinceActive = Date.now() - (stageTimingsRef.current[completedStage]?.activeTime || 0);
      const delayNeeded = Math.max(0, MINIMUM_LOADER_DISPLAY_MS - elapsedSinceActive);

      console.log(`⏱️  Supervisor Stage ${completedStage} was active for ${elapsedSinceActive}ms, delaying by ${delayNeeded}ms`);

      // Store completion data
      if (stageTimingsRef.current[completedStage]) {
        stageTimingsRef.current[completedStage].completionData = data;
      }

      // Cancel existing timeout
      if (pendingCompletionTimeoutsRef.current[completedStage]) {
        clearTimeout(pendingCompletionTimeoutsRef.current[completedStage]);
      }

      // Schedule the completion
      pendingCompletionTimeoutsRef.current[completedStage] = setTimeout(() => {
        console.log(`🎯 [SUPERVISOR APPLY COMPLETION] ${completedStage} - marking as completed`);

        setWorkflowState((prev: any) => {
          const newCompleted = [...prev.completedStages];
          const newStageDetails = { ...prev.stageDetails };

          // Mark as completed
          if (!newCompleted.includes(completedStage)) {
            newCompleted.push(completedStage);
          }

          // Store detailed data
          newStageDetails[completedStage] = {
            message: data?.message || '',
            data: data?.data || {},
            timestamp: new Date().toISOString(),
            execution_time_ms: data?.execution_time_ms || 0,
          };

          const newState: any = {
            ...prev,
            completedStages: newCompleted,
            stageDetails: newStageDetails,
          };

          // Determine next active stage based on what just completed
          // Updated stage flow to match RAG pattern: stage_complete events mark completion
          // Frontend marks them as completed, and next stage naturally becomes active when its START event arrives
          let nextActiveStage = null;

          // The stage flow based on completion:
          if (completedStage === 'supervisor_init') {
            nextActiveStage = 'agent_execution_starting';
          } else if (completedStage === 'agent_execution_starting') {
            nextActiveStage = 'rag_agent_executing';
          } else if (completedStage === 'rag_agent_executing') {
            nextActiveStage = 'rag_documents_extracted';
          } else if (completedStage === 'rag_documents_extracted') {
            nextActiveStage = 'task_agent_executing';
          } else if (completedStage === 'task_agent_executing') {
            nextActiveStage = 'response_generation_complete';
          } else if (completedStage === 'response_generation_complete') {
            nextActiveStage = 'response_streaming_started';
          } else if (completedStage === 'response_streaming_started') {
            nextActiveStage = 'workflow_complete';
          }

          // Update current stage if next stage is determined
          if (nextActiveStage) {
            newState.currentStage = nextActiveStage;
          }

          // Capture intent if detected
          if (detectedIntent && !prev.intent) {
            newState.intent = detectedIntent;
          }

          // Capture RAG substages if this is rag_agent_executing completion
          if (completedStage === 'rag_agent_executing') {
            const ragSubstages = data?.data?.rag_substages || [];
            if (ragSubstages.length > 0) {
              newState.ragSubstages = ragSubstages;
            }
          }

          console.log(`✅ Supervisor ${completedStage} COMPLETED, next stage: ${nextActiveStage}`);

          return newState;
        });

        // Cleanup
        delete stageTimingsRef.current[completedStage];
        delete pendingCompletionTimeoutsRef.current[completedStage];
      }, delayNeeded);

    } else {
      // START EVENT: Mark stage as active immediately
      console.log(`▶️ [SUPERVISOR START] ${supervisorStage} - marking as active immediately`);

      stageTimingsRef.current[supervisorStage] = {
        activeTime: Date.now(),
        completionData: undefined
      };

      setWorkflowState((prev: any) => {
        if (prev.currentStage !== supervisorStage) {
          return {
            ...prev,
            currentStage: supervisorStage,
          };
        }
        return prev;
      });
    }
  };

  /**
   * Cleanup pending timeouts (call on unmount)
   */
  const cleanup = () => {
    Object.values(pendingCompletionTimeoutsRef.current).forEach(timeout => {
      clearTimeout(timeout);
    });
    pendingCompletionTimeoutsRef.current = {};
  };

  return {
    handleSupervisorWorkflowProgress,
    cleanup,
  };
}
