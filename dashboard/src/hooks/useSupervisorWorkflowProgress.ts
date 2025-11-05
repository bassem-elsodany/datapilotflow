import { useRef } from 'react';

/**
 * Hook for handling Supervisor-specific workflow progress events
 * Supervisor has different stages: intent_detection → rag_agent_executing → task_agent_executing → response_generation
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
          const detectedIntent = data?.data?.intent || prev.intent;
          let nextActiveStage = null;

          if (completedStage === 'supervisor_init') {
            nextActiveStage = 'intent_detection';
          } else if (completedStage === 'intent_detection') {
            if (detectedIntent === 'rag_only' || detectedIntent === 'rag_then_task') {
              nextActiveStage = 'rag_agent_executing';
            } else if (detectedIntent === 'task_only') {
              nextActiveStage = 'task_agent_executing';
            } else {
              nextActiveStage = 'rag_agent_executing';
            }
          } else if (completedStage === 'rag_agent_executing') {
            if (detectedIntent === 'rag_then_task') {
              nextActiveStage = 'task_agent_executing';
            } else {
              nextActiveStage = 'response_generation';
            }
          } else if (completedStage === 'task_agent_executing') {
            nextActiveStage = 'response_generation';
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
