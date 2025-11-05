import {
  Box,
  Card,
  Divider,
  Group,
  Modal,
  Progress,
  Stack,
  Text,
  ThemeIcon,
  Badge
} from '@mantine/core';
import {
  IconBrain,
  IconCheck,
  IconChevronDown,
  IconDatabase,
  IconFileSearch,
  IconLoader,
  IconMessageCircle,
  IconScale,
  IconSparkles
} from '@tabler/icons-react';
import React, { useMemo, useState } from 'react';

interface WorkflowStage {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'skipped';
  icon: React.ReactNode;
  color: string;
  metadata?: {
    [key: string]: any;
  };
  substages?: WorkflowSubstage[];
}

interface WorkflowSubstage {
  name: string;
  status: 'active' | 'completed';
  metric?: string;
}

interface RAGPipelineModalProps {
  opened: boolean;
  onClose: () => void;
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
    stageDetails?: Record<string, any>;
    ragSubstages?: string[];
  };
}

export function RAGPipelineModal({
  opened,
  onClose,
  currentStage,
  completedStages,
  rerankingEnabled,
  enableLLMGeneration,
  metadata
}: RAGPipelineModalProps) {
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());

  const toggleExpanded = (stageId: string) => {
    setExpandedStages((prev) => {
      const next = new Set(prev);
      if (next.has(stageId)) {
        next.delete(stageId);
      } else {
        next.add(stageId);
      }
      return next;
    });
  };

  // Determine stage status
  const getStageStatus = (stageId: string): 'pending' | 'active' | 'completed' | 'skipped' => {
    if (completedStages.includes(stageId)) return 'completed';
    if (currentStage === stageId) return 'active';
    if (stageId === 'query_enhancement' && (!metadata.strategy || metadata.strategy === 'native')) return 'skipped';
    return 'pending';
  };

  // Build stages list
  const stages = useMemo(() => {
    const allStages: WorkflowStage[] = [];

    allStages.push({
      id: 'query_enhancement',
      name: 'Query Enhancement',
      description: metadata.strategy && metadata.strategy !== 'native' ? `Using ${metadata.strategy}` : 'Native query',
      status: getStageStatus('query_enhancement'),
      icon: <IconSparkles size={20} />,
      color: 'violet'
    });

    allStages.push({
      id: 'document_retrieval',
      name: 'Document Retrieval',
      description: `Searching ${metadata.documentCount || 0} documents`,
      status: getStageStatus('document_retrieval'),
      icon: <IconDatabase size={20} />,
      color: 'blue'
    });

    allStages.push({
      id: 'document_judging',
      name: 'Judge Ranker',
      description: `Evaluating ${metadata.documentCount || 0} documents`,
      status: getStageStatus('document_judging'),
      icon: <IconScale size={20} />,
      color: 'orange'
    });

    allStages.push({
      id: 'response_generation',
      name: enableLLMGeneration ? 'Response Generation' : 'Raw Response Formatting',
      description: enableLLMGeneration ? 'Generating AI response' : 'Formatting raw documents',
      status: getStageStatus('response_generation'),
      icon: enableLLMGeneration ? <IconBrain size={20} /> : <IconFileSearch size={20} />,
      color: 'green'
    });

    return allStages;
  }, [metadata, currentStage, completedStages, enableLLMGeneration]);

  const activeStages = stages.filter(s => s.status !== 'skipped');
  const completedCount = activeStages.filter(s => s.status === 'completed').length;
  const totalStages = activeStages.length;
  const progress = totalStages > 0 ? (completedCount / totalStages) * 100 : 0;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      centered={false}
      size="xl"
      padding="lg"
      styles={{
        inner: { alignItems: 'flex-end', paddingBottom: '80px' },
        body: { maxHeight: '70vh', overflowY: 'auto' }
      }}
      transitionProps={{ transition: 'slide-up', duration: 300 }}
    >
      <Stack gap="lg">
        {/* Progress Bar */}
        <Box>
          <Group justify="space-between" mb={8}>
            <Text size="sm" fw={600}>RAG Pipeline Progress</Text>
            <Text size="sm" c="dimmed">{completedCount}/{totalStages}</Text>
          </Group>
          <Progress value={progress} size="lg" radius="xl" animated={currentStage !== null} />
        </Box>

        {/* Stage Steps */}
        <Box>
          <Stack gap="md">
            {activeStages.map((stage) => {
              const isActive = stage.status === 'active';
              const isCompleted = stage.status === 'completed';
              const isPending = stage.status === 'pending';

              return (
                <Box
                  key={stage.id}
                  onClick={() => toggleExpanded(stage.id)}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: isActive ? '#e3f2fd' : isCompleted ? '#f1f8e9' : '#f5f5f5',
                    border: isActive ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Group justify="space-between">
                    <Group gap="md">
                      {/* Stage Icon/Loader */}
                      <div
                        style={{
                          width: '44px',
                          height: '44px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: isActive ? '#1976d2' : isCompleted ? '#4caf50' : '#bdbdbd',
                          color: 'white',
                          position: 'relative'
                        }}
                      >
                        {isActive ? (
                          <IconLoader size={24} className="animate-spin" />
                        ) : isCompleted ? (
                          <IconCheck size={24} strokeWidth={3} />
                        ) : (
                          React.cloneElement(stage.icon as React.ReactElement, {
                            style: { color: 'white' }
                          } as any)
                        )}
                      </div>

                      {/* Stage Info */}
                      <Stack gap={0}>
                        <Text fw={600} size="sm">{stage.name}</Text>
                        <Text size="xs" c="dimmed">{stage.description}</Text>
                      </Stack>
                    </Group>

                    {/* Status Badge */}
                    <Badge
                      size="lg"
                      variant={isActive ? 'filled' : isCompleted ? 'light' : 'outline'}
                      color={isActive ? 'blue' : isCompleted ? 'green' : 'gray'}
                    >
                      {isActive ? 'Processing' : isCompleted ? 'Done' : 'Pending'}
                    </Badge>
                  </Group>

                  {/* Expandable Details */}
                  {expandedStages.has(stage.id) && (
                    <Box mt="md">
                      <Divider my="sm" />
                      <Text size="xs" fw={600} c="dimmed" mb="xs">DETAILS</Text>
                      <Text size="xs">Stage ID: {stage.id}</Text>
                      {metadata.stageDetails?.[stage.id] && (
                        <>
                          <Text size="xs" mt="xs">{metadata.stageDetails[stage.id].message}</Text>
                          {metadata.stageDetails[stage.id].data?.document_count && (
                            <Text size="xs">Documents: {metadata.stageDetails[stage.id].data.document_count}</Text>
                          )}
                          {metadata.stageDetails[stage.id].data?.relevant_documents && (
                            <Text size="xs">Relevant: {metadata.stageDetails[stage.id].data.relevant_documents}</Text>
                          )}
                        </>
                      )}
                    </Box>
                  )}
                </Box>
              );
            })}
          </Stack>
        </Box>

        {/* Original Query Section */}
        {metadata.originalQuery && (
          <Card p="sm" radius="md" withBorder>
            <Stack gap="xs">
              <Group gap="xs">
                <ThemeIcon size="sm" color="indigo" variant="light">
                  <IconMessageCircle size={14} />
                </ThemeIcon>
                <Text size="xs" fw={600}>ORIGINAL QUERY</Text>
              </Group>
              <Text size="sm">{metadata.originalQuery}</Text>

              {metadata.enhancedQueries && metadata.enhancedQueries.length > 0 && (
                <>
                  <Divider my="xs" />
                  <Group gap="xs">
                    <ThemeIcon size="sm" color="violet" variant="filled">
                      <IconSparkles size={14} />
                    </ThemeIcon>
                    <Text size="xs" fw={600}>ENHANCED QUERIES ({metadata.enhancedQueries.length})</Text>
                  </Group>
                  {metadata.enhancedQueries.map((query, i) => (
                    <Text key={i} size="xs" c="violet.7">• {query}</Text>
                  ))}
                </>
              )}
            </Stack>
          </Card>
        )}
      </Stack>
    </Modal>
  );
}
