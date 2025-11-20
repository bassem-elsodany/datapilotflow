import { useRef } from 'react';

/**
 * Hook for handling RAG-specific workflow progress events
 * Each RAG stage has its own state machine with START → ACTIVE → COMPLETE
 */
export function useRAGWorkflowProgress() {
  // Track timing for each stage to ensure loaders display for minimum duration
  const stageTimingsRef = useRef<Record<string, { activeTime: number; completionData?: any }>>({});
  const pendingCompletionTimeoutsRef = useRef<Record<string, NodeJS.Timeout>>({});

  const MINIMUM_LOADER_DISPLAY_MS = 500; // Minimum time to show loader before checkmark

  const nodeToStageMap: Record<string, string> = {
    'augmented_strategy_node': 'query_enhancement',
    'multi_query_strategy_node': 'query_enhancement',
    'hyde_strategy_node': 'query_enhancement',
    'decomposition_strategy_node': 'query_enhancement',
    'document_retriever': 'document_retrieval',
    'document_judger': 'document_judging',
    'answer_generator': 'response_generation',
    'raw_response_formatter': 'response_generation',
  };

  /**
   * Handle RAG workflow progress event
   * Returns the state update to apply
   */
  const handleRAGWorkflowProgress = (
    data: any,
    currentWorkflowState: any,
    setWorkflowState: (fn: (prev: any) => any) => void
  ) => {
    const currentNode = data?.current_node || '';
    const stageFromEvent = data?.stage || '';
    const isCompleteEvent = stageFromEvent.endsWith('_complete');

    let mappedStage = stageFromEvent.replace('_complete', '');
    if (!mappedStage) {
      mappedStage = nodeToStageMap[currentNode] || currentNode;
    }

    // console.log(`🎭 [RAG WORKFLOW] ${isCompleteEvent ? '✅ COMPLETE' : '▶️ START'} - ${mappedStage}`);

    if (isCompleteEvent) {
      // COMPLETE EVENT: Store data and schedule delayed completion
      // console.log(`✅ [RAG COMPLETE] ${mappedStage} - scheduling completion after ${MINIMUM_LOADER_DISPLAY_MS}ms`);

      const elapsedSinceActive = Date.now() - (stageTimingsRef.current[mappedStage]?.activeTime || 0);
      const delayNeeded = Math.max(0, MINIMUM_LOADER_DISPLAY_MS - elapsedSinceActive);

      // console.log(`⏱️  RAG Stage ${mappedStage} was active for ${elapsedSinceActive}ms, delaying by ${delayNeeded}ms`);

      // Store completion data
      if (stageTimingsRef.current[mappedStage]) {
        stageTimingsRef.current[mappedStage].completionData = data;
      }

      // Cancel existing timeout
      if (pendingCompletionTimeoutsRef.current[mappedStage]) {
        clearTimeout(pendingCompletionTimeoutsRef.current[mappedStage]);
      }

      // Schedule the completion
      pendingCompletionTimeoutsRef.current[mappedStage] = setTimeout(() => {
        // console.log(`🎯 [RAG APPLY COMPLETION] ${mappedStage} - marking as completed`);

        setWorkflowState((prev: any) => {
          const newCompleted = [...prev.completedStages];
          const newRagSubstages = [...(prev.ragSubstages || [])];
          const newStageDetails = { ...prev.stageDetails };

          // Add to ragSubstages if not already present
          if (!newRagSubstages.includes(mappedStage)) {
            newRagSubstages.push(mappedStage);
          }

          // Mark as completed
          if (!newCompleted.includes(mappedStage)) {
            newCompleted.push(mappedStage);
          }

          // Store detailed data
          newStageDetails[mappedStage] = {
            message: data?.message || '',
            data: data?.data || {},
            timestamp: new Date().toISOString(),
            execution_time_ms: data?.execution_time_ms || 0,
          };

          const newState: any = {
            ...prev,
            completedStages: newCompleted,
            ragSubstages: newRagSubstages,
            stageDetails: newStageDetails,
          };

          // Extract stage-specific data
          const queryVariants = data?.data?.query_variants || [];
          const strategyFromData = data?.data?.strategy || '';
          const documentCount = data?.data?.document_count || 0;
          const relevantCount = data?.data?.relevant_documents || 0;

          if (mappedStage === 'query_enhancement' && queryVariants.length > 0) {
            newState.enhancedQueries = queryVariants;
            newState.strategy = strategyFromData || prev.strategy;
            // console.log(`✨ RAG Enhanced queries:`, queryVariants);
          } else if (mappedStage === 'document_retrieval' && documentCount > 0) {
            newState.documentCount = documentCount;
            // console.log(`📚 RAG Document count:`, documentCount);
          } else if (mappedStage === 'document_judging' && relevantCount >= 0) {
            newState.relevantCount = relevantCount;
            // console.log(`⚖️ RAG Relevant count:`, relevantCount);
          }

          return newState;
        });

        // Cleanup
        delete stageTimingsRef.current[mappedStage];
        delete pendingCompletionTimeoutsRef.current[mappedStage];
      }, delayNeeded);

    } else {
      // START EVENT: Mark stage as active immediately
      // console.log(`▶️ [RAG START] ${mappedStage} - marking as active immediately`);

      stageTimingsRef.current[mappedStage] = {
        activeTime: Date.now(),
        completionData: undefined
      };

      setWorkflowState((prev: any) => {
        const newRagSubstages = [...(prev.ragSubstages || [])];

        if (!newRagSubstages.includes(mappedStage)) {
          newRagSubstages.push(mappedStage);
        }

        if (prev.currentStage !== mappedStage) {
          return {
            ...prev,
            currentStage: mappedStage,
            ragSubstages: newRagSubstages,
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
    handleRAGWorkflowProgress,
    cleanup,
  };
}
