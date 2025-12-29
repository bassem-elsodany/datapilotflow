import React from 'react';
import { RAGPipelineModal } from './rag-pipeline-modal';
import { SupervisorModePipelineModal } from './supervisor-mode-pipeline-modal';

interface WorkflowProgressModalProps {
  opened: boolean;
  onClose: () => void;
  enableKnowledgeAssistant: boolean;  // Determines which modal to show
  currentStage: string | null;
  completedStages: string[];
  rerankingEnabled: boolean;
  enableLLMGeneration: boolean;
  metadata: {
    originalQuery?: string;
    enhancedQueries?: string[];
    strategy?: string;
    documentCount?: number;
    relevantCount?: number;
    indexType?: string;
    searchTime?: number;
    vectorDimension?: number;
    intent?: string;  // For supervisor mode
    stageDetails?: Record<string, any>;
    ragSubstages?: string[];
  };
}

/**
 * Router component that dispatches to either RAGPipelineModal or SupervisorModePipelineModal
 * based on enableKnowledgeAssistant flag
 */
export function WorkflowProgressModal({
  opened,
  onClose,
  enableKnowledgeAssistant,
  currentStage,
  completedStages,
  rerankingEnabled,
  enableLLMGeneration,
  metadata
}: WorkflowProgressModalProps) {
  if (enableKnowledgeAssistant) {
    // Show Supervisor/Agent mode modal
    return (
      <SupervisorModePipelineModal
        opened={opened}
        onClose={onClose}
        currentStage={currentStage}
        completedStages={completedStages}
        rerankingEnabled={rerankingEnabled}
        enableLLMGeneration={enableLLMGeneration}
        metadata={metadata}
      />
    );
  } else {
    // Show pure RAG mode modal
    return (
      <RAGPipelineModal
        opened={opened}
        onClose={onClose}
        currentStage={currentStage}
        completedStages={completedStages}
        rerankingEnabled={rerankingEnabled}
        enableLLMGeneration={enableLLMGeneration}
        metadata={metadata}
      />
    );
  }
}
