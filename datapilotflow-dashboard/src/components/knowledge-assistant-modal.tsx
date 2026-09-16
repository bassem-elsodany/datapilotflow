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
  useMantineTheme
} from '@mantine/core';
import {
  IconBrain,
  IconCheck,
  IconChevronDown,
  IconCircleDot,
  IconDatabase,
  IconFileSearch,
  IconLoader,
  IconMessageCircle,
  IconRobot,
  IconRoute,
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

interface KnowledgeAssistantModalProps {
  opened: boolean;
  onClose: () => void;
  currentStage: string | null;
  completedStages: string[];
  enableLLMGeneration: boolean;
  metadata: {
    intent?: string;
    strategy?: string;
    documentCount?: number;
    relevantCount?: number;
    stageDetails?: Record<string, any>;
    ragSubstages?: string[];
  };
}

export function KnowledgeAssistantModal({
  opened,
  onClose,
  currentStage,
  completedStages,
  enableLLMGeneration,
  metadata
}: KnowledgeAssistantModalProps) {
  const theme = useMantineTheme();
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());

  React.useEffect(() => {
    if (currentStage === 'rag_agent_executing' || (metadata.ragSubstages?.length ?? 0) > 0) {
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

  const renderStageDetails = (stageId: string) => {
    // Try both stageId and stageId_complete format (since backend stores as stageId_complete)
    const details = metadata?.stageDetails?.[stageId] || metadata?.stageDetails?.[`${stageId}_complete`];
    if (!details || !details.data) return null;

    console.log(`📊 [RENDER STAGE DETAILS] stageId=${stageId}, details found:`, details);

    const { data } = details;

    switch (stageId) {
      case 'supervisor_init':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.cyan[0], borderColor: theme.colors.cyan[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="cyan.7">✅ Initialization Complete</Text>
              {data.agents_available && (
                <Text size="xs" c="dimmed">
                  <strong>Agents:</strong> {data.agents_available.join(', ')}
                </Text>
              )}
              {data.initialization_time_ms && (
                <Badge size="xs" variant="light" color="cyan">
                  {Math.round(data.initialization_time_ms)}ms
                </Badge>
              )}
            </Stack>
          </Card>
        );

      case 'agent_execution_starting':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.violet[0], borderColor: theme.colors.violet[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={600} c="violet.7">
                🧠 Agent Planning
              </Text>
              <Text size="xs" c="dimmed">
                Analyzing query and creating execution plan
              </Text>
            </Stack>
          </Card>
        );

      case 'rag_documents_extracted':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.blue[0], borderColor: theme.colors.blue[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={600} c="blue.7">
                📚 Documents Extracted
              </Text>
              <Group gap="xs">
                {data.document_count && (
                  <Badge size="xs" variant="filled" color="green">
                    {data.document_count} documents
                  </Badge>
                )}
                {data.relevant_document_count && (
                  <Badge size="xs" variant="filled" color="orange">
                    {data.relevant_document_count} relevant
                  </Badge>
                )}
              </Group>
              {data.rag_strategy && (
                <Text size="xs" c="dimmed">
                  <strong>Strategy:</strong> {data.rag_strategy}
                </Text>
              )}
            </Stack>
          </Card>
        );

      case 'rag_agent_executing':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.blue[0], borderColor: theme.colors.blue[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="blue.7">📚 RAG Agent Results</Text>
              <Group gap="xs">
                <Badge size="xs" variant="filled" color="green">
                  {data.documents_retrieved || 0} retrieved
                </Badge>
                {data.relevant_documents !== undefined && (
                  <Badge size="xs" variant="filled" color="orange">
                    {data.relevant_documents} relevant
                  </Badge>
                )}
              </Group>
              {data.strategy_used && (
                <Text size="xs" c="dimmed">
                  <strong>Strategy:</strong> {data.strategy_used}
                </Text>
              )}
            </Stack>
          </Card>
        );

      case 'task_agent_executing':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.indigo[0], borderColor: theme.colors.indigo[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="indigo.7">🔨 Task Execution Complete</Text>
              {data.task_type && (
                <Badge size="xs" variant="light" color="indigo">
                  {data.task_type}
                </Badge>
              )}
              {data.used_rag_context && data.context_documents && (
                <Text size="xs" c="dimmed">
                  Used context from <strong>{data.context_documents}</strong> documents
                </Text>
              )}
            </Stack>
          </Card>
        );

      case 'response_generation':
      case 'response_generation_complete':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.teal[0], borderColor: theme.colors.teal[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="teal.7">✨ Response Generated</Text>
              <Group gap="xs">
                {data.response_length && (
                  <Badge size="xs" variant="light" color="teal">
                    {data.response_length} chars
                  </Badge>
                )}
                {data.tokens_estimated && (
                  <Badge size="xs" variant="light" color="cyan">
                    ~{data.tokens_estimated} tokens
                  </Badge>
                )}
              </Group>
              {data.sources_used !== undefined && (
                <Text size="xs">
                  From <strong>{data.sources_used}</strong> source{data.sources_used !== 1 ? 's' : ''}
                </Text>
              )}

              {/* Display document sources if available - EXPANDABLE */}
              {data.document_sources && Array.isArray(data.document_sources) && data.document_sources.length > 0 && (
                <Box mt="sm">
                  <Group
                    gap="xs"
                    mb="xs"
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      setExpandedStages(prev => {
                        const next = new Set(prev);
                        if (next.has('document_sources')) {
                          next.delete('document_sources');
                        } else {
                          next.add('document_sources');
                        }
                        return next;
                      });
                    }}
                  >
                    <IconChevronDown
                      size={16}
                      style={{
                        transform: expandedStages.has('document_sources') ? 'rotate(0deg)' : 'rotate(-90deg)',
                        transition: 'transform 200ms',
                        color: theme.colors.teal[7],
                      }}
                    />
                    <Text size="xs" fw={600} c="teal.7">📚 Document Sources ({data.document_sources.length})</Text>
                  </Group>
                  <Collapse in={expandedStages.has('document_sources')} transitionDuration={200}>
                    <Stack gap="xs" pl="md" pb="xs" style={{ borderLeft: `2px solid ${theme.colors.teal[3]}` }}>
                      {data.document_sources.map((doc: any, idx: number) => (
                        <Box key={idx}>
                          <Text size="xs" fw={500}>
                            {idx + 1}. <strong>{doc.title || 'Unknown'}</strong>
                          </Text>
                          {doc.source && (
                            <Text size="xs">
                              <strong>URL:</strong> {doc.source}
                            </Text>
                          )}
                          {doc.distance !== null && doc.distance !== undefined && (
                            <Badge size="xs" variant="filled" color="cyan" mt={4}>
                              Relevance: {(doc.distance as number).toFixed(3)}
                            </Badge>
                          )}
                        </Box>
                      ))}
                    </Stack>
                  </Collapse>
                </Box>
              )}

              {/* Display search variants if available - EXPANDABLE */}
              {data.search_variants && Array.isArray(data.search_variants) && data.search_variants.length > 0 && (
                <Box mt="sm">
                  <Group
                    gap="xs"
                    mb="xs"
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      setExpandedStages(prev => {
                        const next = new Set(prev);
                        if (next.has('search_variants')) {
                          next.delete('search_variants');
                        } else {
                          next.add('search_variants');
                        }
                        return next;
                      });
                    }}
                  >
                    <IconChevronDown
                      size={16}
                      style={{
                        transform: expandedStages.has('search_variants') ? 'rotate(0deg)' : 'rotate(-90deg)',
                        transition: 'transform 200ms',
                        color: theme.colors.teal[7],
                      }}
                    />
                    <Text size="xs" fw={600} c="teal.7">🔍 Search Variants ({data.search_variants.length})</Text>
                  </Group>
                  <Collapse in={expandedStages.has('search_variants')} transitionDuration={200}>
                    <Stack gap="xs" pl="md" pb="xs" style={{ borderLeft: `2px solid ${theme.colors.teal[3]}` }}>
                      {data.search_variants.map((variant: string, idx: number) => (
                        <Text key={idx} size="xs" fw={500}>
                          {idx + 1}. {variant}
                        </Text>
                      ))}
                    </Stack>
                  </Collapse>
                </Box>
              )}
            </Stack>
          </Card>
        );

      default:
        return null;
    }
  };

  const stages: WorkflowStage[] = useMemo(() => {
    const allStages: WorkflowStage[] = [];

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
            name: 'Analyzing query requirements',
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
        name: 'RAG Agent Execution',
        description: 'Retrieving and ranking relevant documents',
        status: getStageStatus('rag_agent_executing'),
        icon: <IconFileSearch size={20} />,
        color: 'cyan',
        substages: [
          {
            name: '✨ Query Enhancement',
            status: (metadata.ragSubstages?.includes('query_enhancement') || completedStages.includes('rag_agent_executing')) ? 'completed' : 'active',
            metric: metadata.strategy ? getStrategyLabel(metadata.strategy) : 'Native'
          },
          {
            name: '🗄️ Document Retrieval',
            status: (metadata.ragSubstages?.includes('document_retrieval') || completedStages.includes('rag_agent_executing')) ? 'completed' : 'active',
            metric: metadata.documentCount ? `${metadata.documentCount} docs` : undefined
          },
          {
            name: '⚖️ Judge Ranker',
            status: (metadata.ragSubstages?.includes('document_judging') || completedStages.includes('rag_agent_executing')) ? 'completed' : 'active',
            metric: metadata.relevantCount ? `${metadata.relevantCount} relevant` : undefined
          }
        ]
      }
    );

    // Only add Task Agent if intent is rag_then_task
    if (metadata.intent === 'rag_then_task') {
      allStages.push({
        id: 'task_agent_executing',
        name: 'Task Agent Execution',
        description: 'Executing task with RAG context',
        status: getStageStatus('task_agent_executing'),
        icon: <IconTool size={20} />,
        color: 'teal',
        substages: [
          {
            name: 'Task agent processing with knowledge',
            status: completedStages.includes('task_agent_executing') ? 'completed' : 'active'
          }
        ]
      });
    }

    // Add Response Generation stage (always last)
    allStages.push({
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
    });

    return allStages;
  }, [metadata, currentStage, completedStages, enableLLMGeneration]);

  function getStageStatus(stageId: string): 'pending' | 'active' | 'completed' | 'skipped' {
    // Check if stage is marked as completed
    if (completedStages.includes(stageId)) return 'completed';

    // Check if stage is currently active
    if (currentStage === stageId) return 'active';

    const stageOrder: string[] = [
      'supervisor_init_complete',
      'agent_execution_starting',
      'rag_agent_executing',
      'rag_documents_extracted'
    ];

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
                gradient={{ from: 'grape', to: 'violet', deg: 45 }}
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

        {/* Circular Node Flow */}
        <Box style={{ overflowX: 'auto', padding: '12px 0' }}>
          <Group gap={4} wrap="nowrap" justify="center" style={{ minWidth: 'fit-content' }}>
            {activeStages.map((stage, index) => (
              <React.Fragment key={stage.id}>
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
                      <IconCheck size={24} style={{ color: 'white' }} />
                    ) : stage.status === 'active' ? (
                      <IconLoader size={24} className="animate-spin" style={{ color: 'white' }} />
                    ) : (
                      React.cloneElement(stage.icon as React.ReactElement, {
                        style: { color: '#868e96' }
                      } as any)
                    )}
                    {stage.substages && stage.id === 'rag_agent_executing' && (
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
                  </Box>

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

          {/* Expanded RAG Subflow */}
          {activeStages.find(s => s.id === 'rag_agent_executing' && s.substages) && expandedStages.has('rag_agent_executing') && (
            <Box style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Box
                style={{
                  width: '2px',
                  height: '20px',
                  background: theme.colors.cyan[4],
                  position: 'relative',
                  marginTop: '8px'
                }}
              >
                <Box
                  style={{
                    position: 'absolute',
                    bottom: '-5px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: 0,
                    height: 0,
                    borderLeft: '5px solid transparent',
                    borderRight: '5px solid transparent',
                    borderTop: `6px solid ${theme.colors.cyan[4]}`
                  }}
                />
              </Box>

              <Box
                mt="xs"
                p="md"
                style={{
                  background: 'linear-gradient(135deg, #e7f5ff 0%, #d0ebff 100%)',
                  borderRadius: '12px',
                  border: `2px solid ${theme.colors.cyan[3]}`,
                  boxShadow: '0 4px 12px rgba(34, 139, 230, 0.15)',
                  width: 'fit-content'
                }}
              >
                <Group gap="xs" mb="sm" justify="center">
                  <IconDatabase size={16} style={{ color: theme.colors.cyan[7] }} />
                  <Text size="sm" fw={600} c="cyan.7">
                    RAG Pipeline Stages
                  </Text>
                </Group>

                <Group justify="center" gap="md" wrap="nowrap">
                  <Box style={{ textAlign: 'center' }}>
                    <ThemeIcon size={44} radius="xl" variant="light" color="violet">
                      <IconSparkles size={22} />
                    </ThemeIcon>
                    <Text size="xs" mt={6} fw={500}>Query</Text>
                    <Text size="xs" c="dimmed">Enhancement</Text>
                    {completedStages.includes('rag_agent_executing') && (
                      <ThemeIcon size={18} radius="xl" color="green" variant="filled" mt={4} mx="auto">
                        <IconCheck size={12} />
                      </ThemeIcon>
                    )}
                  </Box>

                  <Text size="xl" c="cyan.6" fw={700}>→</Text>

                  <Box style={{ textAlign: 'center' }}>
                    <ThemeIcon size={44} radius="xl" variant="light" color="blue">
                      <IconDatabase size={22} />
                    </ThemeIcon>
                    <Text size="xs" mt={6} fw={500}>Document</Text>
                    <Text size="xs" c="dimmed">Retrieval</Text>
                    {completedStages.includes('rag_agent_executing') && (
                      <ThemeIcon size={18} radius="xl" color="green" variant="filled" mt={4} mx="auto">
                        <IconCheck size={12} />
                      </ThemeIcon>
                    )}
                  </Box>

                  <Text size="xl" c="cyan.6" fw={700}>→</Text>

                  <Box style={{ textAlign: 'center' }}>
                    <ThemeIcon size={44} radius="xl" variant="light" color="orange">
                      <IconSparkles size={22} />
                    </ThemeIcon>
                    <Text size="xs" mt={6} fw={500}>Judge</Text>
                    <Text size="xs" c="dimmed">Ranker</Text>
                    {completedStages.includes('rag_agent_executing') && (
                      <ThemeIcon size={18} radius="xl" color="green" variant="filled" mt={4} mx="auto">
                        <IconCheck size={12} />
                      </ThemeIcon>
                    )}
                  </Box>
                </Group>
              </Box>
            </Box>
          )}
        </Box>

        <Divider label="Detailed Progress" labelPosition="center" />

        {/* Timeline */}
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
                </Group>
              }
            >
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

              {stage.status === 'completed' && renderStageDetails(stage.id)}
            </Timeline.Item>
          ))}
        </Timeline>
      </Stack>

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
