import {
  Badge,
  Box,
  Card,
  Collapse,
  Divider,
  Group,
  Modal,
  Progress,
  Stack,
  Text,
  ThemeIcon,
  useMantineTheme
} from '@mantine/core';
import {
  IconBrain,
  IconCheck,
  IconChevronDown,
  IconDatabase,
  IconFileSearch,
  IconLoader,
  IconMessageCircle,
  IconRobot,
  IconRoute,
  IconScale,
  IconSearch,
  IconSparkles,
  IconTool
} from '@tabler/icons-react';
import React, { useMemo, useState } from 'react';

interface WorkflowStage {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'skipped';
  icon: React.ReactNode;
  color: string;
  startTime?: number;
  endTime?: number;
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

interface SupervisorModePipelineModalProps {
  opened: boolean;
  onClose: () => void;
  currentStage: string | null;
  completedStages: string[];
  rerankingEnabled: boolean;
  enableLLMGeneration: boolean;
  metadata: {
    originalQuery?: string;
    enhancedQueries?: string[];  // ALWAYS an array - even for single queries
    strategy?: string;
    documentCount?: number;
    relevantCount?: number;
    indexType?: string;
    searchTime?: number;
    vectorDimension?: number;
    intent?: string;  // Supervisor detected intent
    stageDetails?: Record<string, any>;  // Detailed data for each completed stage
    ragSubstages?: string[];  // Track completed RAG substages (query_enhancement, document_retrieval, document_judging)
  };
}

export function SupervisorModePipelineModal({
  opened,
  onClose,
  currentStage,
  completedStages,
  rerankingEnabled,
  enableLLMGeneration,
  metadata
}: SupervisorModePipelineModalProps) {
  const theme = useMantineTheme();
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());

  // Auto-expand RAG Agent Execution when it's active or has substages completing
  React.useEffect(() => {
    if (currentStage === 'rag_agent_executing' || (metadata.ragSubstages && metadata.ragSubstages.length > 0)) {
      setExpandedStages((prev) => {
        if (!prev.has('rag_agent_executing')) {
          const next = new Set(prev);
          next.add('rag_agent_executing');
          return next;
        }
        return prev;
      });
    }
  }, [currentStage, metadata.ragSubstages]);

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

  // Define workflow stages based on actual LangGraph flow - memoized to prevent infinite re-renders
  const stages: WorkflowStage[] = useMemo(() => {
    console.log('🔧 [SUPERVISOR MODAL] Building supervisor stages with ragSubstages:', metadata.ragSubstages);
    const allStages: WorkflowStage[] = [];

    // Add supervisor stages (always enabled in this component)
    // NEW: Updated to match actual supervisor orchestration stages from backend
    allStages.push(
        {
          id: 'supervisor_init_complete',
          name: 'Supervisor Initialization',
          description: 'Initializing multi-agent supervisor system',
          status: getStageStatus('supervisor_init_complete'),
          icon: <IconRobot size={20} />,
          color: 'grape',
          substages: [
            {
              name: 'Multi-agent system initialized',
              status: completedStages.includes('supervisor_init_complete') ? 'completed' : 'active'
            }
          ]
        },
        {
          id: 'agent_execution_starting',
          name: 'Query Analysis & Planning',
          description: 'Agent analyzing query and creating execution plan',
          status: getStageStatus('agent_execution_starting'),
          icon: <IconBrain size={20} />,
          color: 'indigo',
          substages: [
            {
              name: 'Analyzing user query intent and requirements',
              status: completedStages.includes('agent_execution_starting') ? 'completed' : 'active'
            },
            {
              name: 'Planning execution strategy',
              status: completedStages.includes('agent_execution_starting') ? 'completed' : 'active'
            }
          ]
        },
        {
          id: 'rag_agent_executing',
          name: 'Knowledge Base Retrieval',
          description: 'Retrieving and processing relevant documents',
          status: getStageStatus('rag_agent_executing'),
          icon: <IconDatabase size={20} />,
          color: 'cyan',
          substages: [
            {
              name: 'Searching knowledge base with multiple query variants',
              status: completedStages.includes('rag_agent_executing') ? 'completed' : 'active',
              metric: metadata.strategy ? getStrategyLabel(metadata.strategy) : 'custom_variants'
            },
            {
              name: 'Retrieving and ranking documents by relevance',
              status: completedStages.includes('rag_documents_extracted') || completedStages.includes('rag_agent_executing') ? 'completed' : 'active',
              metric: metadata.documentCount ? `${metadata.documentCount} docs` : undefined
            }
          ]
        }
      );

      // Only add Task Agent if generation tools are needed
      if (enableLLMGeneration) {
        // Get tool name from stage details if available
        const taskStageDetails = metadata.stageDetails?.task_agent_executing;
        const toolName = taskStageDetails?.tool_name || taskStageDetails?.data?.tool_name;
        const displayToolName = toolName ? ` (${toolName})` : '';
        
        allStages.push({
          id: 'task_agent_executing',
          name: 'Response Generation with Tools',
          description: 'Executing generation tools with RAG context injected',
          status: getStageStatus('task_agent_executing'),
          icon: <IconTool size={20} />,
          color: 'teal',
          substages: [
            {
              name: `Invoking generation tools with knowledge base context${displayToolName}`,
              status: completedStages.includes('task_agent_executing') ? 'completed' : 'active'
            },
            {
              name: 'Processing tool outputs',
              status: completedStages.includes('task_agent_executing') ? 'completed' : 'active'
            }
          ]
        });
      }

    // Add Response Streaming stage (final stage)
    allStages.push({
      id: 'response_streaming_started',
      name: 'Response Streaming',
      description: 'Streaming final response to client',
      status: getStageStatus('response_streaming_started'),
      icon: <IconSparkles size={20} />,
      color: 'green',
      substages: [
        {
          name: 'Preparing response metadata and sources',
          status: completedStages.includes('response_generation_complete') || completedStages.includes('response_streaming_started') ? 'completed' : 'active'
        },
        {
          name: 'Streaming response chunks to client',
          status: completedStages.includes('response_streaming_started') ? 'completed' : 'active'
        },
        {
          name: 'Response delivery complete',
          status: completedStages.includes('workflow_complete') ? 'completed' : 'active'
        }
      ]
    });

    return allStages;
  }, [
    metadata,
    currentStage,
    completedStages,
    rerankingEnabled,
    enableLLMGeneration
  ]);

  function getStageStatus(stageId: string): 'pending' | 'active' | 'completed' | 'skipped' {
    // Check if stage is marked as completed
    if (completedStages.includes(stageId)) return 'completed';

    // Check if stage is currently active
    if (currentStage === stageId) return 'active';

    // Build supervisor stage order - matches actual backend stages
    const stageOrder: string[] = [
      'supervisor_init_complete',
      'agent_execution_starting',
      'rag_agent_executing',
      'rag_documents_extracted'
    ];

    // Only add task_agent to order if generation tools are enabled
    if (enableLLMGeneration) {
      stageOrder.push('task_agent_executing');
    }

    stageOrder.push('response_generation_complete', 'response_streaming_started', 'workflow_complete');

    const currentIndex = currentStage ? stageOrder.indexOf(currentStage) : -1;
    const stageIndex = stageOrder.indexOf(stageId);

    // If current stage is defined and this stage comes after it, it's pending
    if (currentIndex >= 0 && stageIndex > currentIndex) return 'pending';

    // If current stage is not defined and this stage hasn't completed, it's pending
    if (currentIndex === -1 && !completedStages.includes(stageId)) return 'pending';

    // If we get here, the stage has passed (before current), so it's completed
    // This handles stages that come before the current stage in the order
    if (stageIndex < currentIndex) return 'completed';

    return 'pending';
  }

  function getStrategyLabel(strategy: string): string {
    const labels: { [key: string]: string } = {
      'augmented': 'Augmented',
      'multi_query': 'Multi-Query',
      'hyde': 'HyDE',
      'decomposition': 'Decomposition',
      'native': 'Native'
    };
    return labels[strategy] || strategy;
  }

  function getStrategySubstage(strategy: string): string {
    const substages: { [key: string]: string } = {
      'augmented': 'Combining original with enhanced variants',
      'multi_query': 'Creating alternative phrasings',
      'hyde': 'Generating hypothetical answers',
      'decomposition': 'Breaking down into sub-questions'
    };
    return substages[strategy] || 'Enhancing query';
  }

  // Filter out skipped stages for accurate counting
  const activeStages = stages.filter(s => s.status !== 'skipped');
  const completedCount = activeStages.filter(s => s.status === 'completed').length;
  const totalStages = activeStages.length;
  const progress = totalStages > 0 ? (completedCount / totalStages) * 100 : 0;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      withOverlay={false}
      centered={false}
      size="lg"
      padding="md"
      styles={{
        inner: {
          alignItems: 'flex-end',
          paddingBottom: '20px',
          pointerEvents: 'none',
        },
        content: {
          pointerEvents: 'auto',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
        },
        body: {
          padding: '12px 16px',
          maxHeight: 'none',
          overflowY: 'visible'
        }
      }}
      transitionProps={{ transition: 'slide-up', duration: 300 }}
    >
      <Stack gap="md">
        {/* Header with Progress */}
        <Box>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <ThemeIcon
                size="lg"
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan', deg: 45 }}
              >
                <IconSearch size={20} />
              </ThemeIcon>
              <Box>
                <Text size="lg" fw={600}>
                  Knowledge Assistant Processing
                </Text>
                <Text size="xs" c="dimmed">
                  {completedCount} of {totalStages} stages completed
                  {metadata.intent && ` • Mode: ${metadata.intent}`}
                </Text>
              </Box>
            </Group>
            <Group gap="xs">
              <Badge
                size="lg"
                variant="light"
                color={currentStage ? 'blue' : 'green'}
                style={{ paddingLeft: '10px', paddingRight: '10px' }}
              >
                <Group gap={6}>
                  {currentStage ? (
                    <IconLoader size={14} className="animate-spin" />
                  ) : (
                    <IconCheck size={14} />
                  )}
                  <Text size="sm" fw={500}>
                    {currentStage ? 'Processing' : 'Completed'}
                  </Text>
                </Group>
              </Badge>
            </Group>
          </Group>

          <Progress
            value={progress}
            size="lg"
            radius="xl"
            animated={currentStage !== null}
            color={currentStage ? 'blue' : 'green'}
            styles={{
              root: { backgroundColor: theme.colors.gray[2] }
            }}
          />
        </Box>

        {/* Circular Node Flow - Visual Pipeline */}
        <Box style={{ overflowX: 'auto', padding: '12px 0' }}>
          <Group gap={4} wrap="nowrap" justify="center" style={{ minWidth: 'fit-content' }}>
            {activeStages.map((stage, index) => (
              <React.Fragment key={stage.id}>
                {/* Node */}
                <Stack
                  gap={6}
                  align="center"
                  style={{
                    minWidth: '100px',
                    cursor: stage.substages && stage.id === 'rag_agent_executing' ? 'pointer' : 'default'
                  }}
                  onClick={() => {
                    if (stage.substages && stage.id === 'rag_agent_executing') {
                      toggleExpanded(stage.id);
                    }
                  }}
                >
                  {/* Circular Icon */}
                  <Box
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: stage.status === 'completed'
                        ? 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)'
                        : stage.status === 'active'
                          ? 'linear-gradient(135deg, #339af0 0%, #1c7ed6 100%)'
                          : '#e9ecef',
                      boxShadow: stage.status === 'active' || stage.status === 'completed'
                        ? '0 2px 8px rgba(0, 0, 0, 0.12)'
                        : 'none',
                      border: stage.status === 'pending' ? '2px dashed #adb5bd' : 'none',
                      transition: 'all 0.3s ease',
                      position: 'relative'
                    }}
                  >
                    {stage.status === 'completed' ? (
                      // Show original icon in green for completed stages (checkmark will be overlaid)
                      React.cloneElement(stage.icon as React.ReactElement, {
                        size: 24,
                        style: { color: 'white' }
                      } as any)
                    ) : stage.status === 'active' ? (
                      <IconLoader size={24} className="animate-spin" style={{ color: 'white' }} />
                    ) : (
                      React.cloneElement(stage.icon as React.ReactElement, {
                        style: { color: '#868e96' }
                      } as any)
                    )}
                    {/* Show expand indicator for RAG Agent */}
                    {stage.substages && stage.id === 'rag_agent_executing' && !stage.substages?.length && (
                      <Box
                        style={{
                          position: 'absolute',
                          bottom: '-4px',
                          right: '-4px',
                          background: 'white',
                          borderRadius: '50%',
                          padding: '2px',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
                        }}
                      >
                        <IconChevronDown
                          size={12}
                          style={{
                            transform: expandedStages.has(stage.id) ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s ease',
                            color: theme.colors.cyan[6]
                          }}
                        />
                      </Box>
                    )}

                    {/* Green checkmark overlay for completed stages */}
                    {stage.status === 'completed' && (
                      <Box
                        style={{
                          position: 'absolute',
                          bottom: '-2px',
                          right: '-2px',
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
                          border: '2px solid white',
                        }}
                      >
                        <IconCheck size={10} style={{ color: 'white', strokeWidth: 3 }} />
                      </Box>
                    )}
                  </Box>

                  {/* Node Label */}
                  <Text
                    size="xs"
                    fw={500}
                    ta="center"
                    style={{
                      color: stage.status === 'pending' ? '#868e96' : '#212529',
                      maxWidth: '90px',
                      lineHeight: 1.3
                    }}
                  >
                    {stage.name}
                  </Text>
                </Stack>

                {/* Connecting Arrow */}
                {index < activeStages.length - 1 && (
                  <Box
                    style={{
                      width: '24px',
                      height: '2px',
                      backgroundColor: stage.status === 'completed' ? '#51cf66' : '#dee2e6',
                      transition: 'background-color 0.3s ease',
                      marginBottom: '30px',
                      position: 'relative'
                    }}
                  >
                    <Box
                      style={{
                        position: 'absolute',
                        right: '-4px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 0,
                        height: 0,
                        borderTop: '4px solid transparent',
                        borderBottom: '4px solid transparent',
                        borderLeft: `6px solid ${stage.status === 'completed' ? '#51cf66' : '#dee2e6'}`,
                        transition: 'border-color 0.3s ease'
                      }}
                    />
                  </Box>
                )}
              </React.Fragment>
            ))}
          </Group>

        </Box>

        {/* Query Comparison - Original Query and Enhanced Variants at Bottom */}
        {metadata.originalQuery && (
          <Card
            withBorder
            p="sm"
            radius="md"
            style={{
              backgroundColor: metadata.enhancedQueries && metadata.enhancedQueries.length > 0
                ? theme.colors.violet[0]
                : theme.colors.gray[0],
              borderColor: metadata.enhancedQueries && metadata.enhancedQueries.length > 0
                ? theme.colors.violet[3]
                : theme.colors.gray[3]
            }}
          >
            <Stack gap="xs">
              <Group gap="xs">
                <ThemeIcon size="sm" color="indigo" variant="light">
                  <IconMessageCircle size={14} />
                </ThemeIcon>
                <Text size="xs" fw={600} c="indigo.7">ORIGINAL QUERY</Text>
              </Group>
              <Text size="sm" style={{ wordBreak: 'break-word' }}>
                {metadata.originalQuery}
              </Text>

              {/* Show enhanced queries if available */}
              {metadata.enhancedQueries && metadata.enhancedQueries && metadata.enhancedQueries.length > 0 && (
                <>
                  <Divider my={6} label={
                    <Badge size="sm" variant="filled" color="violet">
                      {metadata.enhancedQueries && metadata.enhancedQueries.length > 1
                        ? `${metadata.enhancedQueries.length} Query Variants`
                        : 'Query Enhanced'}
                    </Badge>
                  } labelPosition="center" />
                  <Group gap="xs">
                    <ThemeIcon size="sm" color="violet" variant="filled">
                      <IconSparkles size={14} />
                    </ThemeIcon>
                    <Text size="xs" fw={700} c="violet.9">
                      {metadata.enhancedQueries.length > 1
                        ? 'ENHANCED QUERIES'
                        : 'ENHANCED QUERY'}
                    </Text>
                    <Badge size="xs" variant="dot" color="violet">
                      {getStrategyLabel(metadata.strategy || 'unknown')}
                    </Badge>
                  </Group>
                  <Text size="xs" c="violet.8" style={{ lineHeight: 1.5 }}>
                    {/* Show all enhanced queries with bullets */}
                    {metadata.enhancedQueries && metadata.enhancedQueries.map((query, index) => (
                      <span key={index}>
                        <Text component="span" size="xs" fw={600} c="violet.6" style={{ marginRight: '4px' }}>
                          [{index + 1}]
                        </Text>
                        {query}
                        {metadata.enhancedQueries && index < metadata.enhancedQueries.length - 1 && ' • '}
                      </span>
                    ))}
                  </Text>
                </>
              )}
            </Stack>
          </Card>
        )}
      </Stack>

      {/* CSS for animations */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </Modal>
  );
}

