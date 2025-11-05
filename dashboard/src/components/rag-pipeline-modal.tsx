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
  IconScale,
  IconSearch,
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
  console.log(`🎬 [RAG MODAL COMPONENT] Render - opened=${opened}, currentStage='${currentStage}', completed=[${completedStages.join(',')}]`);
  const theme = useMantineTheme();
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

  const renderStageDetails = (stageId: string) => {
    const details = metadata?.stageDetails?.[stageId];
    if (!details || !details.data) return null;

    const { data, message } = details;

    switch (stageId) {
      case 'query_enhancement':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.violet[0], borderColor: theme.colors.violet[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="violet.7">✨ Query Enhanced</Text>
              {data.query_variants && (
                <Text size="xs" c="dimmed">
                  <strong>Variants:</strong> {data.query_variants.length}
                </Text>
              )}
              {data.strategy && (
                <Badge size="xs" variant="light" color="violet">
                  {data.strategy}
                </Badge>
              )}
            </Stack>
          </Card>
        );

      case 'document_retrieval':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.blue[0], borderColor: theme.colors.blue[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="blue.7">📚 Documents Retrieved</Text>
              <Group gap="xs">
                <Badge size="xs" variant="filled" color="green">
                  {data.document_count || 0} documents
                </Badge>
              </Group>
              {data.collection && (
                <Text size="xs" c="dimmed">
                  <strong>Collection:</strong> {data.collection}
                </Text>
              )}
            </Stack>
          </Card>
        );

      case 'document_judging':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.orange[0], borderColor: theme.colors.orange[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="orange.7">⚖️ Documents Ranked</Text>
              <Group gap="xs">
                <Badge size="xs" variant="filled" color="green">
                  {data.total_documents || 0} total
                </Badge>
                <Badge size="xs" variant="filled" color="orange">
                  {data.relevant_documents || 0} relevant
                </Badge>
              </Group>
              {data.avg_score !== undefined && (
                <Text size="xs" c="dimmed">
                  <strong>Avg Score:</strong> {(data.avg_score * 100).toFixed(1)}%
                </Text>
              )}
            </Stack>
          </Card>
        );

      case 'response_generation':
        return (
          <Card withBorder p="xs" mt="xs" style={{ backgroundColor: theme.colors.teal[0], borderColor: theme.colors.teal[3] }}>
            <Stack gap="xs">
              <Text size="xs" fw={500} c="teal.7">✅ Response Generated</Text>
              <Group gap="xs">
                {metadata && (
                  <Badge size="xs" variant="light" color="teal">
                    Complete
                  </Badge>
                )}
              </Group>
            </Stack>
          </Card>
        );

      default:
        return null;
    }
  };

  const stages: WorkflowStage[] = useMemo(() => {
    console.log(`🔧 [RAG MODAL] Building stages with currentStage='${currentStage}', completedStages=[${completedStages.join(',')}]`);

    // Define getStageStatus inside useMemo to ensure fresh closure
    const getLocalStageStatus = (stageId: string): 'pending' | 'active' | 'completed' | 'skipped' => {
      if (completedStages.includes(stageId)) {
        console.log(`🎯 [RAG MODAL] getLocalStageStatus('${stageId}') = COMPLETED`);
        return 'completed';
      }
      if (currentStage === stageId) {
        console.log(`🎯 [RAG MODAL] getLocalStageStatus('${stageId}') = ACTIVE (currentStage='${currentStage}')`);
        return 'active';
      }

      if (stageId === 'query_enhancement' && (!metadata.strategy || metadata.strategy === 'native')) return 'skipped';

      const stageOrder = ['query_enhancement', 'document_retrieval', 'document_judging', 'response_generation'];
      const currentIndex = currentStage ? stageOrder.indexOf(currentStage) : -1;
      const stageIndex = stageOrder.indexOf(stageId);

      if (currentIndex >= 0 && stageIndex > currentIndex) return 'pending';
      if (currentIndex === -1 && !completedStages.includes(stageId)) return 'pending';

      return 'pending';
    };

    const allStages: WorkflowStage[] = [];

    // Stage 1: Query Enhancement
    allStages.push({
      id: 'query_enhancement',
      name: 'Query Enhancement',
      description: metadata.strategy && metadata.strategy !== 'native'
        ? `Using ${getStrategyLabel(metadata.strategy)} strategy`
        : 'Native query (no enhancement needed)',
      status: getLocalStageStatus('query_enhancement'),
      icon: <IconSparkles size={20} />,
      color: 'violet',
      metadata: {
        originalQuery: metadata.originalQuery,
        enhancedQueries: metadata.enhancedQueries,
        strategy: metadata.strategy
      },
      substages: metadata.strategy && metadata.strategy !== 'native' ? [
        {
          name: 'Analyzing query intent',
          status: getSubstageStatus('query_enhancement')
        },
        {
          name: getStrategySubstage(metadata.strategy),
          status: getSubstageStatus('query_enhancement')
        }
      ] : undefined
    });

    // Stage 2: Document Retrieval
    allStages.push({
      id: 'document_retrieval',
      name: 'Document Retrieval',
      description: `Searching ${metadata.documentCount || 0} documents with HNSW index`,
      status: getLocalStageStatus('document_retrieval'),
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
          status: getSubstageStatus('document_retrieval'),
          metric: metadata.vectorDimension ? `${metadata.vectorDimension}D vector` : undefined
        },
        {
          name: 'Performing vector similarity search',
          status: getSubstageStatus('document_retrieval'),
          metric: metadata.indexType ? `${metadata.indexType} index` : undefined
        },
        {
          name: 'Applying distance threshold filter',
          status: getSubstageStatus('document_retrieval'),
          metric: 'COSINE < 0.5'
        },
        {
          name: 'Retrieved documents',
          status: getSubstageStatus('document_retrieval'),
          metric: metadata.documentCount ? `${metadata.documentCount} docs` : undefined
        }
      ]
    });

    // Stage 3: Judge Ranker - ALWAYS show because backend always runs it
    allStages.push({
      id: 'document_judging',
      name: 'Judge Ranker',
      description: `Evaluating relevance of ${metadata.documentCount || 0} documents`,
      status: getLocalStageStatus('document_judging'),
      icon: <IconScale size={20} />,
      color: 'orange',
      metadata: {
        documentCount: metadata.documentCount,
        relevantCount: metadata.relevantCount
      },
      substages: [
        {
          name: 'LLM-based relevance evaluation',
          status: getSubstageStatus('document_judging')
        },
        {
          name: 'Ranking and filtering documents',
          status: getSubstageStatus('document_judging'),
          metric: metadata.relevantCount ? `${metadata.relevantCount} relevant` : undefined
        }
      ]
    });

    // Stage 4: Response Generation
    allStages.push({
      id: 'response_generation',
      name: enableLLMGeneration ? 'Response Generation' : 'Raw Response Formatting',
      description: enableLLMGeneration
        ? 'Generating AI response from context'
        : 'Formatting raw documents without LLM processing',
      status: getLocalStageStatus('response_generation'),
      icon: enableLLMGeneration ? <IconBrain size={20} /> : <IconFileSearch size={20} />,
      color: 'green',
      substages: enableLLMGeneration ? [
        {
          name: 'Building context from documents',
          status: getSubstageStatus('response_generation')
        },
        {
          name: 'Streaming LLM response',
          status: getSubstageStatus('response_generation')
        }
      ] : [
        {
          name: 'Structuring documents for display',
          status: getSubstageStatus('response_generation')
        },
        {
          name: 'Formatting raw content',
          status: getSubstageStatus('response_generation')
        }
      ]
    });

    console.log(`✅ [RAG MODAL] Built ${allStages.length} stages:`, allStages.map(s => `${s.id}(${s.status})`).join(' → '));
    return allStages;
  }, [metadata, currentStage, completedStages, rerankingEnabled, enableLLMGeneration]);

  function isSubstageCompleted(substageKey: string): boolean {
    // Map substage keys to ragSubstages array values (MUST match backend stage names)
    const substageMapping: Record<string, string> = {
      'query_enhancement': 'query_enhancement',
      'document_retrieval': 'document_retrieval',
      'document_judging': 'document_judging',
      'response_generation': 'response_generation',
    };

    const mapped = substageMapping[substageKey];
    return mapped ? (metadata?.ragSubstages?.includes(mapped) ?? false) : false;
  }

  function getSubstageStatus(substageKey: string): 'active' | 'completed' {
    // Check if this substage is in the completed ragSubstages list
    if (isSubstageCompleted(substageKey)) return 'completed';
    // If currentStage matches this substage, it's active
    if (currentStage === substageKey) return 'active';
    // Otherwise it's pending (will be shown as active in the UI until marked complete)
    return 'active';
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

  const activeStages = stages.filter(s => s.status !== 'skipped');
  console.log(`🎨 [RAG MODAL] activeStages (${activeStages.length}):`, activeStages.map(s => `${s.id}(${s.status})`).join(' → '));
  const completedCount = activeStages.filter(s => s.status === 'completed').length;
  const totalStages = activeStages.length;
  const progress = totalStages > 0 ? (completedCount / totalStages) * 100 : 0;

  console.log(`📱 [RAG MODAL RENDER] opened=${opened}, currentStage=${currentStage}, completedCount=${completedCount}/${totalStages}`);

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
                <Text size="lg" fw={600}>
                  RAG Pipeline Processing
                </Text>
                <Text size="xs" c="dimmed">
                  {completedCount} of {totalStages} stages completed
                </Text>
              </Box>
            </Group>
            <Group gap="xs">
              <Badge
                size="lg"
                variant="light"
                color={currentStage ? 'blue' : completedCount > 0 ? 'green' : 'gray'}
                style={{ paddingLeft: '10px', paddingRight: '10px' }}
              >
                <Group gap={6}>
                  {currentStage ? (
                    <IconLoader size={14} className="animate-spin" />
                  ) : completedCount > 0 ? (
                    <IconCheck size={14} />
                  ) : (
                    <IconCircleDot size={14} />
                  )}
                  <Text size="sm" fw={500}>
                    {currentStage ? 'Processing' : completedCount > 0 ? 'Completed' : 'Ready'}
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

        {/* Query Comparison */}
        {metadata.originalQuery && (
          <Card
            p="sm"
            radius="md"
            style={{
              backgroundColor: metadata.enhancedQueries && metadata.enhancedQueries.length > 0
                ? theme.colors.violet[0]
                : theme.colors.gray[0],
              border: `1px solid ${metadata.enhancedQueries && metadata.enhancedQueries.length > 0
                ? theme.colors.violet[3]
                : theme.colors.gray[3]}`
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

              {metadata.enhancedQueries && metadata.enhancedQueries.length > 0 && (
                <>
                  <Divider my={6} label={
                    <Badge size="sm" variant="filled" color="violet">
                      {metadata.enhancedQueries.length > 1
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
                    {metadata.enhancedQueries.map((query, index) => (
                      <span key={index}>
                        <Text component="span" size="xs" fw={600} c="violet.6" style={{ marginRight: '4px' }}>
                          [{index + 1}]
                        </Text>
                        {query}
                        {index < (metadata.enhancedQueries?.length || 0) - 1 && ' • '}
                      </span>
                    ))}
                  </Text>
                </>
              )}
            </Stack>
          </Card>
        )}

        {/* Circular Node Flow */}
        {(() => {
          console.log(`🔄 [CIRCULAR NODES] Rendering ${activeStages.length} stages:`, activeStages.map(s => `${s.id}=${s.status}`).join(', '));
          return null;
        })()}
        <Box style={{ overflowX: 'auto', padding: '12px 0' }}>
          <Group gap={4} wrap="nowrap" justify="center" style={{ minWidth: 'fit-content' }}>
            {activeStages.map((stage, index) => {
              console.log(`🎯 [NODE RENDER] ${stage.id}: status='${stage.status}', should show loader? ${stage.status === 'active'}`);
              return (
              <React.Fragment key={stage.id}>
                <Stack
                  gap={6}
                  align="center"
                  style={{ minWidth: '100px' }}
                >
                  <Box
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: stage.status === 'active'
                        ? 'linear-gradient(135deg, #339af0 0%, #1c7ed6 100%)'
                        : '#e9ecef',
                      boxShadow: stage.status === 'active' || stage.status === 'completed'
                        ? '0 2px 8px rgba(0, 0, 0, 0.12)'
                        : 'none',
                      border: stage.status === 'pending' ? '2px dashed #adb5bd' : 'none',
                      transition: 'all 0.3s ease',
                      position: 'relative',
                    }}
                  >
                    {(() => {
                      const isActive = stage.status === 'active';
                      console.log(`  ↳ [${stage.id}] isActive=${isActive}, will render loader=${isActive}`);
                      if (isActive) {
                        console.log(`    🌀 Rendering IconLoader for ${stage.id}`);
                        return (
                          <IconLoader
                            size={24}
                            stroke={2}
                            className="animate-spin"
                            style={{
                              color: 'white',
                              display: 'block',
                              width: '24px',
                              height: '24px',
                              animation: 'spin 1s linear infinite',
                              opacity: 1,
                              visibility: 'visible'
                            }}
                          />
                        );
                      }
                      return React.cloneElement(stage.icon as React.ReactElement, {
                        style: { color: stage.status === 'completed' ? '#51cf66' : '#868e96' }
                      } as any);
                    })()}

                    {/* Green checkmark overlay for completed stages */}
                    {stage.status === 'completed' && (
                      <Box
                        style={{
                          position: 'absolute',
                          bottom: '-2px',
                          right: '-2px',
                          width: '18px',
                          height: '18px',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 1px 4px rgba(0, 0, 0, 0.15)',
                          border: '2px solid white',
                        }}
                      >
                        <IconCheck size={12} style={{ color: 'white', strokeWidth: 3 }} />
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
            );
            })}
          </Group>
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

        {/* Technical Details */}
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
