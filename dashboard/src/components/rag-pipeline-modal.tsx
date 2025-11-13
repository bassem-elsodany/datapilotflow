import {
  Badge,
  Box,
  Card,
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
  IconCircleDot,
  IconDatabase,
  IconFileSearch,
  IconLoader,
  IconMessageCircle,
  IconScale,
  IconSearch,
  IconSparkles
} from '@tabler/icons-react';
import React, { useMemo } from 'react';

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

  const stages: WorkflowStage[] = useMemo(() => {
    console.log(`🔧 [RAG MODAL] Building stages with currentStage='${currentStage}', completedStages=[${completedStages.join(',')}]`);

    // Define getStageStatus inside useMemo to ensure fresh closure
    const getLocalStageStatus = (stageId: string): 'pending' | 'active' | 'completed' | 'skipped' => {
      if (completedStages.includes(stageId)) {
        return 'completed';
      }
      if (currentStage === stageId) {
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

    // Stage 3: Judge Ranker - Only show when reranking is enabled
    if (rerankingEnabled) {
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
    }

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
      <Stack gap="xs">
        {/* Header with Progress */}
        <Box>
          <Group justify="space-between" mb={4}>
            <Group gap="xs">
              <ThemeIcon
                size="md"
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan', deg: 45 }}
              >
                <IconSearch size={18} />
              </ThemeIcon>
              <Box>
                <Text size="sm" fw={600}>
                  RAG Pipeline
                </Text>
                <Text size="xs" c="dimmed">
                  {completedCount} of {totalStages} stages
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
            size="md"
            radius="xl"
            animated={currentStage !== null}
            color={currentStage ? 'blue' : 'green'}
            styles={{
              root: { backgroundColor: theme.colors.gray[2] }
            }}
          />
        </Box>

        {/* Circular Node Flow */}
        {(() => {
          console.log(`🔄 [CIRCULAR NODES] Rendering ${activeStages.length} stages:`, activeStages.map(s => `${s.id}=${s.status}`).join(', '));
          return null;
        })()}
        <Box style={{ overflowX: 'auto', padding: '12px 0' }}>
          <Group gap={4} wrap="nowrap" justify="center" style={{ minWidth: 'fit-content' }}>
            {activeStages.map((stage, index) => {
              const shouldShowLoader = stage.status === 'active';
              const stageOrder = ['query_enhancement', 'document_retrieval', 'document_judging', 'response_generation'];
              const stageNumber = stageOrder.indexOf(stage.id) + 1;
              console.log(`🎯 [STAGE #${stageNumber}] ${stage.id}: status='${stage.status}', shouldShowLoader=${shouldShowLoader}`);
              if (shouldShowLoader) {
                console.log(`  ✅✅✅ STAGE #${stageNumber} SHOULD SHOW LOADER! ✅✅✅`);
              } else {
                console.log(`  ❌ Stage #${stageNumber} will NOT show loader (status is '${stage.status}')`);
              }
              return (
                <React.Fragment key={stage.id}>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                      alignItems: 'center',
                      minWidth: '100px',
                    }}
                  >
                    <div
                      style={{
                        position: 'relative',
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: stage.status === 'active'
                          ? 'linear-gradient(135deg, #339af0 0%, #1c7ed6 100%)'
                          : '#e9ecef',
                        boxShadow: stage.status === 'active' || stage.status === 'completed'
                          ? '0 2px 6px rgba(0, 0, 0, 0.1)'
                          : 'none',
                        border: stage.status === 'pending' ? '2px dashed #adb5bd' : 'none',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      {(() => { console.log(`🔵 [DIV RENDER] ${stage.id} - bg=${stage.status === 'active' ? 'blue' : 'gray'}, will render children...`); return null; })()}
                      {(() => {
                        const isActive = stage.status === 'active';
                        console.log(`  ↳ [${stage.id}] isActive=${isActive}, stage.icon=`, stage.icon, `type=${typeof stage.icon}`);
                        if (isActive) {
                          console.log(`    🌀 Rendering IconLoader for ${stage.id}`);
                          return (
                            <IconLoader
                              size={20}
                              stroke={2}
                              className="animate-spin"
                              style={{
                                color: 'white',
                                display: 'block',
                                width: '20px',
                                height: '20px',
                                animation: 'spin 1s linear infinite',
                                opacity: 1,
                                visibility: 'visible',
                                pointerEvents: 'none'
                              }}
                            />
                          );
                        }
                        console.log(`    🖼️ Rendering cloned icon for ${stage.id}, color will be ${stage.status === 'completed' ? '#51cf66' : '#868e96'}`);
                        return React.cloneElement(stage.icon as React.ReactElement, {
                          size: 20,
                          style: { color: stage.status === 'completed' ? '#51cf66' : '#868e96' }
                        } as any);
                      })()}

                      {/* Green checkmark overlay for completed stages */}
                      {stage.status === 'completed' && (
                        <div
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
                        </div>
                      )}
                    </div>

                    <div
                      style={{
                        fontSize: '12px',
                        fontWeight: 500,
                        textAlign: 'center',
                        color: stage.status === 'pending' ? '#868e96' : '#212529',
                        maxWidth: '90px',
                        lineHeight: 1.3
                      }}
                    >
                      {stage.name}
                    </div>
                  </div>

                  {index < activeStages.length - 1 && (
                    <Box
                      style={{
                        width: '20px',
                        height: '2px',
                        backgroundColor: stage.status === 'completed' ? '#51cf66' : '#dee2e6',
                        transition: 'background-color 0.3s ease',
                        marginBottom: '24px',
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
