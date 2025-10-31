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
  Timeline,
  Tooltip,
  useMantineTheme
} from '@mantine/core';
import {
  IconBrain,
  IconCheck,
  IconChevronDown,
  IconCircleDot,
  IconClock,
  IconDatabase,
  IconFileSearch,
  IconLoader,
  IconMessageCircle,
  IconScale,
  IconSearch,
  IconSparkles
} from '@tabler/icons-react';
import React, { useEffect, useState } from 'react';

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

interface WorkflowProgressModalProps {
  opened: boolean;
  onClose: () => void;
  currentStage: string | null;
  completedStages: string[];
  rerankingEnabled: boolean;
  enableLLMGeneration: boolean;
  metadata: {
    originalQuery?: string;
    enhancedQuery?: string;
    enhancedQueries?: string[];  // Array of all enhanced query variants
    strategy?: string;
    documentCount?: number;
    relevantCount?: number;
    indexType?: string;
    searchTime?: number;
    vectorDimension?: number;
  };
}

export function WorkflowProgressModal({
  opened,
  onClose,
  currentStage,
  completedStages,
  rerankingEnabled,
  enableLLMGeneration,
  metadata
}: WorkflowProgressModalProps) {
  const theme = useMantineTheme();
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime] = useState(Date.now());

  // Update elapsed time
  useEffect(() => {
    if (!opened) return;

    const interval = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 100);

    return () => clearInterval(interval);
  }, [opened, startTime]);

  // Define workflow stages based on actual LangGraph flow
  const stages: WorkflowStage[] = [
    // Stage 1: Query Analysis & Enhancement (conditional - skip if native)
    {
      id: 'query_enhancement',
      name: 'Query Enhancement',
      description: metadata.strategy && metadata.strategy !== 'native'
        ? `Using ${getStrategyLabel(metadata.strategy)} strategy`
        : 'Native query (no enhancement needed)',
      status: getStageStatus('query_enhancement'), // Let getStageStatus handle all the logic
      icon: <IconSparkles size={20} />,
      color: 'violet',
      metadata: {
        originalQuery: metadata.originalQuery,
        enhancedQuery: metadata.enhancedQuery,
        strategy: metadata.strategy
      },
      substages: metadata.strategy && metadata.strategy !== 'native' ? [
        {
          name: 'Analyzing query intent',
          // Always completed once we've started query enhancement
          status: 'completed'
        },
        {
          name: getStrategySubstage(metadata.strategy),
          // Completed if stage is done, or if we've moved past this stage
          status: completedStages.includes('query_enhancement') || currentStage !== 'query_enhancement' ? 'completed' : 'active'
        }
      ] : undefined
    },

    // Stage 2: Vector Search & Retrieval
    {
      id: 'document_retrieval',
      name: 'Document Retrieval',
      description: `Searching ${metadata.documentCount || 0} documents with HNSW index`,
      status: getStageStatus('document_retrieval'),
      icon: <IconDatabase size={20} />,
      color: 'blue',
      metadata: {
        documentCount: metadata.documentCount,
        indexType: metadata.indexType || 'HNSW',
        vectorDimension: metadata.vectorDimension,
        searchTime: metadata.searchTime
      },
      substages: [
        {
          name: 'Converting query to embedding',
          // Always completed once we've started retrieval
          status: 'completed',
          metric: metadata.vectorDimension ? `${metadata.vectorDimension}D vector` : undefined
        },
        {
          name: 'Performing vector similarity search',
          // Always completed once we've started retrieval
          status: 'completed',
          metric: metadata.indexType ? `${metadata.indexType} index` : undefined
        },
        {
          name: 'Applying distance threshold filter',
          // Always completed once we've started retrieval
          status: 'completed',
          metric: 'COSINE < 0.5'
        },
        {
          name: 'Retrieved documents',
          // Completed if stage is done, or if we've moved past this stage
          status: completedStages.includes('document_retrieval') || currentStage !== 'document_retrieval' ? 'completed' : 'active',
          metric: metadata.documentCount ? `${metadata.documentCount} docs` : undefined
        }
      ]
    },

    // Stage 3: Document Reranking (conditional)
    {
      id: 'document_judging',
      name: 'Document Reranking',
      description: rerankingEnabled
        ? `Evaluating relevance of ${metadata.documentCount || 0} documents`
        : 'Reranking disabled - skipped',
      status: rerankingEnabled
        ? getStageStatus('document_judging')
        : 'skipped',
      icon: <IconScale size={20} />,
      color: 'orange',
      metadata: {
        documentCount: metadata.documentCount,
        relevantCount: metadata.relevantCount
      },
      substages: rerankingEnabled ? [
        {
          name: 'LLM-based relevance judgment',
          // Always completed once we've started reranking
          status: 'completed'
        },
        {
          name: 'Filtering relevant documents',
          // Completed if stage is done, or if we've moved past this stage
          status: completedStages.includes('document_judging') || currentStage !== 'document_judging' ? 'completed' : 'active',
          metric: metadata.relevantCount ? `${metadata.relevantCount} relevant` : undefined
        }
      ] : undefined
    },

    // Stage 4: Response Generation or Raw Formatting (conditional based on enableLLMGeneration)
    {
      id: 'response_generation',
      name: enableLLMGeneration ? 'Response Generation' : 'Raw Response Formatting',
      description: enableLLMGeneration
        ? 'Generating AI response from context'
        : 'Formatting raw documents without LLM processing',
      status: getStageStatus('response_generation'),
      icon: enableLLMGeneration ? <IconBrain size={20} /> : <IconFileSearch size={20} />,
      color: 'green',
      substages: enableLLMGeneration ? [
        {
          name: 'Building context from documents',
          status: completedStages.includes('response_generation') ? 'completed' :
            currentStage === 'response_generation' ? 'active' : 'completed'
        },
        {
          name: 'Streaming LLM response',
          status: completedStages.includes('response_generation') ? 'completed' : 'active'
        }
      ] : [
        {
          name: 'Structuring documents for display',
          status: completedStages.includes('response_generation') ? 'completed' :
            currentStage === 'response_generation' ? 'active' : 'completed'
        },
        {
          name: 'Formatting raw content',
          status: completedStages.includes('response_generation') ? 'completed' : 'active'
        }
      ]
    }
  ];

  function getStageStatus(stageId: string): 'pending' | 'active' | 'completed' | 'skipped' {
    if (completedStages.includes(stageId)) return 'completed';
    if (currentStage === stageId) return 'active';

    // Handle skipped stages based on configuration
    if (stageId === 'query_enhancement' && (!metadata.strategy || metadata.strategy === 'native')) return 'skipped';
    if (stageId === 'document_judging' && !rerankingEnabled) return 'skipped';

    // Check if stage should be pending
    const stageOrder = ['query_enhancement', 'document_retrieval', 'document_judging', 'response_generation'];
    const currentIndex = currentStage ? stageOrder.indexOf(currentStage) : -1;
    const stageIndex = stageOrder.indexOf(stageId);

    if (currentIndex >= 0 && stageIndex > currentIndex) return 'pending';
    if (currentIndex === -1 && !completedStages.includes(stageId)) return 'pending';

    return 'pending';
  }

  function getStrategyLabel(strategy: string): string {
    const labels: { [key: string]: string } = {
      'augmented': 'Augmented',
      'step_back': 'Step-Back',
      'multi_query': 'Multi-Query',
      'hyde': 'HyDE',
      'decomposition': 'Decomposition',
      'rag_fusion': 'RAG Fusion',
      'native': 'Native'
    };
    return labels[strategy] || strategy;
  }

  function getStrategySubstage(strategy: string): string {
    const substages: { [key: string]: string } = {
      'augmented': 'Combining original with enhanced variants',
      'step_back': 'Generating broader conceptual questions',
      'multi_query': 'Creating alternative phrasings',
      'hyde': 'Generating hypothetical answers',
      'decomposition': 'Breaking down into sub-questions',
      'rag_fusion': 'Creating multiple perspectives'
    };
    return substages[strategy] || 'Enhancing query';
  }

  // Filter out skipped stages for accurate counting
  const activeStages = stages.filter(s => s.status !== 'skipped');
  const completedCount = activeStages.filter(s => s.status === 'completed').length;
  const totalStages = activeStages.length;
  const progress = totalStages > 0 ? (completedCount / totalStages) * 100 : 0;

  const formatTime = (ms: number) => {
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const toggleExpanded = (stageId: string) => {
    const newExpanded = new Set(expandedStages);
    if (newExpanded.has(stageId)) {
      newExpanded.delete(stageId);
    } else {
      newExpanded.add(stageId);
    }
    setExpandedStages(newExpanded);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      centered={false}
      size="xl"
      padding="lg"
      styles={{
        inner: {
          alignItems: 'flex-end',
          paddingBottom: '80px'
        },
        body: {
          maxHeight: '70vh',
          overflowY: 'auto'
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
                <Text size="lg" fw={600}>RAG Pipeline Processing</Text>
                <Text size="xs" c="dimmed">
                  {completedCount} of {totalStages} stages completed
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
              <Tooltip label="Elapsed time">
                <Badge size="lg" variant="light" color="gray" style={{ paddingLeft: '10px', paddingRight: '10px' }}>
                  <Group gap={6}>
                    <IconClock size={14} />
                    <Text size="sm" fw={500}>
                      {formatTime(elapsedTime)}
                    </Text>
                  </Group>
                </Badge>
              </Tooltip>
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

        {/* Query Comparison */}
        {metadata.originalQuery && (
          <Card
            withBorder
            p="sm"
            radius="md"
            style={{
              backgroundColor: metadata.enhancedQuery && metadata.enhancedQuery !== metadata.originalQuery
                ? theme.colors.violet[0]
                : theme.colors.gray[0],
              borderColor: metadata.enhancedQuery && metadata.enhancedQuery !== metadata.originalQuery
                ? theme.colors.violet[3]
                : theme.colors.gray[3]
            }}
          >
            <Stack gap="xs">
              <Group gap="xs">
                <ThemeIcon size="sm" color="indigo" variant="light">
                  <IconMessageCircle size={14} />
                </ThemeIcon>
                <Text size="xs" fw={600} c="dimmed">ORIGINAL QUERY</Text>
              </Group>
              <Text size="sm" style={{ wordBreak: 'break-word' }}>
                {metadata.originalQuery}
              </Text>

              {((metadata.enhancedQueries && metadata.enhancedQueries.length > 0) ||
                (metadata.enhancedQuery && metadata.enhancedQuery !== metadata.originalQuery)) && (
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
                        {metadata.enhancedQueries && metadata.enhancedQueries.length > 1
                          ? 'ENHANCED QUERIES'
                          : 'ENHANCED QUERY'}
                      </Text>
                      <Badge size="xs" variant="dot" color="violet">
                        {getStrategyLabel(metadata.strategy || 'unknown')}
                      </Badge>
                    </Group>
                    <Text size="xs" c="violet.8" style={{ lineHeight: 1.5 }}>
                      {metadata.enhancedQueries && metadata.enhancedQueries.length > 0 ? (
                        // Show all enhanced queries inline with bullets
                        metadata.enhancedQueries.map((query, index) => (
                          <span key={index}>
                            <Text component="span" size="xs" fw={600} c="violet.6" style={{ marginRight: '4px' }}>
                              [{index + 1}]
                            </Text>
                            {query}
                            {index < metadata.enhancedQueries!.length - 1 && ' • '}
                          </span>
                        ))
                      ) : (
                        // Fallback to single enhanced query
                        metadata.enhancedQuery && (
                          <span>{metadata.enhancedQuery}</span>
                        )
                      )}
                    </Text>
                  </>
                )}
            </Stack>
          </Card>
        )}

        {/* Circular Node Flow - Visual Pipeline */}
        <Box style={{ overflowX: 'auto', padding: '12px 0' }}>
          <Group gap={4} wrap="nowrap" justify="center" style={{ minWidth: 'fit-content' }}>
            {activeStages.map((stage, index) => (
              <React.Fragment key={stage.id}>
                {/* Node */}
                <Stack gap={6} align="center" style={{ minWidth: '100px' }}>
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
                      transition: 'all 0.3s ease'
                    }}
                  >
                    {stage.status === 'completed' ? (
                      <IconCheck size={24} style={{ color: 'white' }} />
                    ) : stage.status === 'active' ? (
                      <IconLoader size={24} className="animate-spin" style={{ color: 'white' }} />
                    ) : (
                      React.cloneElement(stage.icon as React.ReactElement, {
                        size: 20,
                        style: { color: '#868e96' }
                      })
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

        <Divider label="Detailed Progress" labelPosition="center" />

        {/* Timeline of Stages (kept for detailed view) */}
        <Timeline
          active={activeStages.findIndex(s => s.status === 'active')}
          bulletSize={32}
          lineWidth={2}
          color="blue"
        >
          {activeStages.map((stage) => (
            <Timeline.Item
              key={stage.id}
              bullet={
                stage.status === 'completed' ? (
                  <IconCheck size={18} />
                ) : stage.status === 'active' ? (
                  <IconLoader size={18} className="animate-spin" />
                ) : (
                  <IconCircleDot size={18} />
                )
              }
              title={
                <Group gap="xs" wrap="nowrap">
                  <ThemeIcon
                    size="md"
                    variant={stage.status === 'active' ? 'filled' : stage.status === 'completed' ? 'light' : 'default'}
                    color={stage.status === 'skipped' ? 'gray' : stage.color}
                  >
                    {stage.icon}
                  </ThemeIcon>
                  <Box style={{ flex: 1 }}>
                    <Text size="sm" fw={500}>{stage.name}</Text>
                    <Text size="xs" c="dimmed">{stage.description}</Text>
                  </Box>
                  {stage.substages && stage.status !== 'skipped' && (
                    <ThemeIcon
                      size="sm"
                      variant="subtle"
                      color="gray"
                      style={{ cursor: 'pointer' }}
                      onClick={() => toggleExpanded(stage.id)}
                    >
                      <IconChevronDown
                        size={16}
                        style={{
                          transform: expandedStages.has(stage.id) ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: 'transform 0.2s ease'
                        }}
                      />
                    </ThemeIcon>
                  )}
                </Group>
              }
            >
              {/* Substages */}
              {stage.substages && stage.status !== 'skipped' && (
                <Collapse in={expandedStages.has(stage.id) || stage.status === 'active'}>
                  <Card
                    withBorder
                    p="xs"
                    radius="md"
                    mt="xs"
                    style={{
                      backgroundColor: stage.status === 'active'
                        ? theme.colors[stage.color][0]
                        : theme.colors.gray[0],
                      borderColor: stage.status === 'active'
                        ? theme.colors[stage.color][3]
                        : theme.colors.gray[3]
                    }}
                  >
                    <Stack gap="xs">
                      {stage.substages.map((substage, subIndex) => (
                        <Group key={subIndex} gap="xs" wrap="nowrap">
                          <ThemeIcon
                            size="xs"
                            variant="light"
                            color={substage.status === 'completed' ? 'green' : stage.color}
                          >
                            {substage.status === 'completed' ? (
                              <IconCheck size={12} />
                            ) : (
                              <IconLoader size={12} className="animate-spin" />
                            )}
                          </ThemeIcon>
                          <Text size="xs" style={{ flex: 1 }}>
                            {substage.name}
                          </Text>
                          {substage.metric && (
                            <Badge size="xs" variant="light" color={stage.color}>
                              {substage.metric}
                            </Badge>
                          )}
                        </Group>
                      ))}
                    </Stack>
                  </Card>
                </Collapse>
              )}
            </Timeline.Item>
          ))}
        </Timeline>

        {/* Technical Details (Expandable) */}
        <Card withBorder p="xs" radius="md" style={{ backgroundColor: theme.colors.gray[0] }}>
          <Group gap="xs" style={{ cursor: 'pointer' }} onClick={() => toggleExpanded('technical')}>
            <ThemeIcon size="xs" variant="light" color="blue">
              <IconFileSearch size={12} />
            </ThemeIcon>
            <Text size="xs" fw={500} style={{ flex: 1 }}>Technical Details</Text>
            <IconChevronDown
              size={14}
              style={{
                transform: expandedStages.has('technical') ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}
            />
          </Group>

          <Collapse in={expandedStages.has('technical')}>
            <Stack gap="xs" mt="xs">
              <Group gap="xs">
                <Text size="xs" c="dimmed" style={{ width: '140px' }}>Vector Index:</Text>
                <Badge size="xs" variant="light" color="blue">
                  {metadata.indexType || 'HNSW'}
                </Badge>
              </Group>
              {metadata.vectorDimension && (
                <Group gap="xs">
                  <Text size="xs" c="dimmed" style={{ width: '140px' }}>Vector Dimension:</Text>
                  <Badge size="xs" variant="light" color="cyan">
                    {metadata.vectorDimension}D
                  </Badge>
                </Group>
              )}
              <Group gap="xs">
                <Text size="xs" c="dimmed" style={{ width: '140px' }}>Documents Retrieved:</Text>
                <Badge size="xs" variant="light" color="green">
                  {metadata.documentCount || 0}
                </Badge>
              </Group>
              {metadata.relevantCount !== undefined && (
                <Group gap="xs">
                  <Text size="xs" c="dimmed" style={{ width: '140px' }}>Relevant After Reranking:</Text>
                  <Badge size="xs" variant="light" color="orange">
                    {metadata.relevantCount}
                  </Badge>
                </Group>
              )}
            </Stack>
          </Collapse>
        </Card>
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
