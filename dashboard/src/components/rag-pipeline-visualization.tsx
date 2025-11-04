import { Badge, Card, Collapse, Group, Progress, Stack, Text, ThemeIcon } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconArrowRight,
  IconBrain,
  IconCheck,
  IconChevronDown,
  IconDatabase,
  IconFilter,
  IconMessageCircle,
  IconWand,
  IconRouter,
  IconGitFork
} from '@tabler/icons-react';
import { useMemo } from 'react';

// Workflow node types
type NodeStatus = 'completed' | 'active' | 'pending' | 'skipped';

interface WorkflowNode {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  status: NodeStatus;
  isVisible: boolean;
  substeps?: SubstepInfo[];
  metrics?: { label: string; value: string; color?: string }[];
}

interface SubstepInfo {
  name: string;
  status: NodeStatus;
  metric?: string;
}

interface RAGPipelineVisualizationProps {
  // Current workflow state
  currentStage?: string;
  completedStages?: string[];

  // Metadata
  metadata?: {
    strategy?: string;
    originalQuery?: string;
    enhancedQuery?: string;
    vectorDimension?: number;
    documentCount?: number;
    relevantCount?: number;
    distanceThreshold?: number;
    detectedIntent?: string;  // NEW: Intent from supervisor
    useTaskAgent?: boolean;    // NEW: Whether task agent was used
  };

  // Configuration
  rerankingEnabled?: boolean;
  enableLLMGeneration?: boolean;
}

export function RAGPipelineVisualization({
  currentStage = '',
  completedStages = [],
  metadata = {},
  rerankingEnabled = false,
  enableLLMGeneration = true,
}: RAGPipelineVisualizationProps) {

  // Debug logging
  console.log('🔍 RAGPipelineVisualization - Props:', {
    currentStage,
    completedStages,
    metadata,
    rerankingEnabled,
    enableLLMGeneration,
  });

  // Build workflow nodes based on configuration
  const workflowNodes: WorkflowNode[] = useMemo(() => {
    console.log('🔍 RAGPipelineVisualization - Building nodes with metadata:', metadata);
    // Helper functions inside useMemo to avoid dependency issues
    const getNodeStatus = (nodeId: string): NodeStatus => {
      if (completedStages.includes(nodeId)) return 'completed';
      if (currentStage === nodeId) return 'active';
      return 'pending';
    };

    const getStrategyLabel = (strategy?: string): string => {
      if (!strategy) return 'Native RAG';
      const labels: { [key: string]: string } = {
        native: 'Native RAG',
        augmented: 'Augmented',
        multi_query: 'Multi-Query',
        hyde: 'HyDE',
        decomposition: 'Decomposition',
      };
      return labels[strategy] || strategy;
    };

    const getStrategySubstage = (strategy?: string): string => {
      const substages: { [key: string]: string } = {
        augmented: 'Combining original with enhanced variants',
        multi_query: 'Generating multiple query variants',
        hyde: 'Generating hypothetical answer',
        decomposition: 'Decomposing into sub-questions',
      };
      return substages[strategy || ''] || 'Enhancing query';
    };
    const nodes: WorkflowNode[] = [];

    // Node 1: User Query
    nodes.push({
      id: 'user_query',
      title: 'User Query',
      description: metadata.originalQuery ? metadata.originalQuery.substring(0, 40) + '...' : 'Input Question',
      icon: IconMessageCircle,
      color: 'indigo',
      status: 'completed',
      isVisible: true,
    });

    // Node 2: Supervisor Intent Detection (NEW)
    const supervisorStatus = getNodeStatus('supervisor_intent');
    const intentLabel = metadata.detectedIntent === 'rag_only'
      ? 'Retrieval Only'
      : metadata.detectedIntent === 'rag_then_task'
      ? 'Retrieval + Task'
      : 'Detecting Intent...';

    nodes.push({
      id: 'supervisor_intent',
      title: 'Intent Detection',
      description: intentLabel,
      icon: IconRouter,
      color: 'blue',
      status: supervisorStatus,
      isVisible: true,
      substeps: [
        {
          name: 'Analyzing user intent',
          status: 'completed',
        },
        {
          name: `Route: ${intentLabel}`,
          status: completedStages.includes('supervisor_intent') || currentStage !== 'supervisor_intent'
            ? 'completed'
            : 'active',
        },
      ],
    });

    // Node 3: Query Enhancement (if strategy is not native)
    console.log('🔍 Checking Query Enhancement:', {
      hasStrategy: !!metadata.strategy,
      strategy: metadata.strategy,
      isNative: metadata.strategy === 'native',
      willShow: metadata.strategy && metadata.strategy !== 'native'
    });

    if (metadata.strategy && metadata.strategy !== 'native') {
      console.log('✅ Adding Query Enhancement node');
      const enhancementStatus = getNodeStatus('query_enhancement');
      nodes.push({
        id: 'query_enhancement',
        title: 'Query Enhancement',
        description: getStrategyLabel(metadata.strategy),
        icon: IconWand,
        color: 'violet',
        status: enhancementStatus,
        isVisible: true,
        substeps: [
          {
            name: 'Analyzing query intent',
            status: 'completed', // Always completed once started
          },
          {
            name: getStrategySubstage(metadata.strategy),
            status: completedStages.includes('query_enhancement') || currentStage !== 'query_enhancement'
              ? 'completed'
              : 'active',
          },
        ],
      });
    } else {
      console.log('❌ Skipping Query Enhancement node - strategy:', metadata.strategy);
    }

    // Node 3: Document Retrieval
    const retrievalStatus = getNodeStatus('document_retrieval');
    nodes.push({
      id: 'document_retrieval',
      title: 'Document Retrieval',
      description: 'Vector Similarity Search',
      icon: IconDatabase,
      color: 'cyan',
      status: retrievalStatus,
      isVisible: true,
      substeps: [
        {
          name: 'Converting query to embedding',
          status: currentStage === 'document_retrieval' ? 'completed' : (completedStages.includes('document_retrieval') ? 'completed' : 'pending'),
        },
        {
          name: 'Performing vector similarity search',
          status: currentStage === 'document_retrieval' ? 'active' : (completedStages.includes('document_retrieval') ? 'completed' : 'pending'),
        },
        {
          name: 'Applying distance threshold filter',
          status: completedStages.includes('document_retrieval') ? 'completed' : 'pending',
        },
      ],
      metrics: metadata.documentCount ? [
        { label: 'Retrieved', value: `${metadata.documentCount} docs`, color: 'cyan' },
      ] : undefined,
    });

    // Node 4: Document Reranking (if enabled)
    if (rerankingEnabled) {
      const rerankingStatus = getNodeStatus('document_judging');
      nodes.push({
        id: 'document_judging',
        title: 'Document Reranking',
        description: 'LLM-Based Relevance',
        icon: IconFilter,
        color: 'orange',
        status: rerankingStatus,
        isVisible: true,
        substeps: [
          {
            name: 'LLM-based relevance judgment',
            status: 'completed', // Always completed once started
          },
          {
            name: 'Filtering relevant documents',
            status: completedStages.includes('document_judging') || currentStage !== 'document_judging'
              ? 'completed'
              : 'active',
          },
        ],
        metrics: metadata.relevantCount ? [
          { label: 'Relevant', value: `${metadata.relevantCount} docs`, color: 'green' },
        ] : undefined,
      });
    }

    // Node 5: Answer Generation
    const generationStatus = getNodeStatus('answer_generation');
    nodes.push({
      id: 'answer_generation',
      title: enableLLMGeneration ? 'Answer Generation' : 'Results',
      description: enableLLMGeneration ? 'LLM Synthesis' : 'Raw Documents',
      icon: IconBrain,
      color: 'green',
      status: generationStatus,
      isVisible: true,
    });

    return nodes;
  }, [
    currentStage,
    completedStages,
    metadata?.strategy,
    metadata?.originalQuery,
    metadata?.documentCount,
    metadata?.relevantCount,
    rerankingEnabled,
    enableLLMGeneration
  ]);

  // Helper function for displaying strategy label (outside useMemo for use in JSX)
  const displayStrategyLabel = (strategy?: string): string => {
    if (!strategy) return 'Native RAG';
    const labels: { [key: string]: string } = {
      native: 'Native RAG',
      augmented: 'Augmented',
      multi_query: 'Multi-Query',
      hyde: 'HyDE',
      decomposition: 'Decomposition',
    };
    return labels[strategy] || strategy;
  };

  return (
    <Card withBorder p="sm" radius="sm" bg="gray.0" w="100%">
      <Stack gap="xs">
        <Group gap="xs">
          <IconBrain size={16} color="var(--mantine-color-blue-6)" />
          <Text fw={600} size="sm">RAG Pipeline Processing</Text>
        </Group>

        <Text size="xs" c="dimmed" style={{ lineHeight: 1.3, textAlign: 'center' }}>
          {workflowNodes.length} steps • {displayStrategyLabel(metadata.strategy)} • {rerankingEnabled ? 'With Reranking' : 'No Reranking'}
        </Text>

        {/* Horizontal Workflow Visualization */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'flex-start',
            justifyContent: 'center',
            gap: '12px',
            paddingTop: '16px',
            paddingBottom: '16px',
            width: '100%',
            flexWrap: 'wrap',
          }}
        >
          {workflowNodes.map((node, index) => {
            const NodeIcon = node.icon;
            const isLast = index === workflowNodes.length - 1;

            return (
              <div key={node.id} style={{ display: 'flex', alignItems: 'flex-start', flexShrink: 0 }}>
                {/* Workflow Node */}
                <WorkflowNodeCard node={node} />

                {/* Connector Arrow */}
                {!isLast && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '12px',
                      height: '120px',
                      flexShrink: 0,
                      marginLeft: '6px',
                      marginRight: '6px',
                    }}
                  >
                    <IconArrowRight
                      size={12}
                      color={node.status === 'completed' ? 'var(--mantine-color-green-5)' : 'var(--mantine-color-gray-4)'}
                      style={{ transition: 'all 0.3s ease' }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Stack>
    </Card>
  );
}

// Individual workflow node card component
function WorkflowNodeCard({ node }: { node: WorkflowNode }) {
  const [substepsOpened, { toggle: toggleSubsteps }] = useDisclosure(node.status === 'active');
  const NodeIcon = node.icon;

  const getStatusColor = (status: NodeStatus) => {
    switch (status) {
      case 'completed': return 'green';
      case 'active': return node.color;
      case 'pending': return 'gray';
      case 'skipped': return 'gray';
    }
  };

  const getStatusIcon = (status: NodeStatus) => {
    if (status === 'completed') return <IconCheck size={12} />;
    if (status === 'active') return <NodeIcon size={12} />;
    return <NodeIcon size={12} />;
  };

  return (
    <Card
      padding="xs"
      radius="sm"
      withBorder
      style={{
        minWidth: '140px',
        maxWidth: '160px',
        borderColor: node.status === 'active'
          ? `var(--mantine-color-${node.color}-4)`
          : node.status === 'completed'
            ? 'var(--mantine-color-green-3)'
            : 'var(--mantine-color-gray-3)',
        backgroundColor: node.status === 'active'
          ? `var(--mantine-color-${node.color}-0)`
          : node.status === 'completed'
            ? 'var(--mantine-color-green-0)'
            : 'white',
        transition: 'all 0.3s ease',
        opacity: node.status === 'pending' ? 0.6 : 1,
      }}
    >
      <Stack gap={4}>
        {/* Node Header */}
        <Group justify="space-between" wrap="nowrap">
          <ThemeIcon
            size={24}
            radius="md"
            color={getStatusColor(node.status)}
            variant={node.status === 'active' ? 'filled' : 'light'}
            style={{
              transition: 'all 0.3s ease',
              boxShadow: node.status === 'active' ? `0 2px 6px var(--mantine-color-${node.color}-3)` : 'none',
            }}
          >
            {getStatusIcon(node.status)}
          </ThemeIcon>

          {/* Expandable icon if has substeps */}
          {node.substeps && node.substeps.length > 0 && (
            <ThemeIcon
              size={16}
              radius="sm"
              variant="subtle"
              color="gray"
              onClick={toggleSubsteps}
              style={{ cursor: 'pointer' }}
            >
              <IconChevronDown
                size={12}
                style={{
                  transform: substepsOpened ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s ease',
                }}
              />
            </ThemeIcon>
          )}
        </Group>

        {/* Node Title & Description */}
        <Stack gap={2}>
          <Text
            size="xs"
            fw={600}
            c={node.status === 'active' ? `${node.color}.7` : node.status === 'completed' ? 'green.7' : 'gray.6'}
            style={{ lineHeight: 1.2 }}
          >
            {node.title}
          </Text>
          <Text size="xs" c="dimmed" style={{ lineHeight: 1.2 }}>
            {node.description}
          </Text>
        </Stack>

        {/* Progress Indicator for Active Node */}
        {node.status === 'active' && (
          <Progress
            size="xs"
            value={100}
            color={node.color}
            animated
            style={{ marginTop: '4px' }}
          />
        )}

        {/* Metrics */}
        {node.metrics && node.metrics.length > 0 && (
          <Group gap={4} mt={2}>
            {node.metrics.map((metric, idx) => (
              <Badge key={idx} size="xs" variant="dot" color={metric.color || node.color}>
                {metric.label}: {metric.value}
              </Badge>
            ))}
          </Group>
        )}

        {/* Substeps (Expandable) */}
        {node.substeps && node.substeps.length > 0 && (
          <Collapse in={substepsOpened}>
            <Stack gap={4} mt={4}>
              {node.substeps.map((substep, idx) => (
                <Group key={idx} gap={4} wrap="nowrap">
                  <ThemeIcon
                    size={12}
                    radius="xl"
                    color={substep.status === 'completed' ? 'green' : substep.status === 'active' ? node.color : 'gray'}
                    variant={substep.status === 'active' ? 'filled' : 'light'}
                  >
                    {substep.status === 'completed' ? (
                      <IconCheck size={8} />
                    ) : substep.status === 'active' ? (
                      <div
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: 'currentColor',
                          animation: 'pulse 1.5s ease-in-out infinite',
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: 'currentColor',
                        }}
                      />
                    )}
                  </ThemeIcon>
                  <Text
                    size="xs"
                    c={substep.status === 'completed' ? 'green.7' : substep.status === 'active' ? `${node.color}.7` : 'dimmed'}
                    style={{ lineHeight: 1.2, flex: 1 }}
                  >
                    {substep.name}
                  </Text>
                  {substep.metric && (
                    <Badge size="xs" variant="light" color={node.color}>
                      {substep.metric}
                    </Badge>
                  )}
                </Group>
              ))}
            </Stack>
          </Collapse>
        )}
      </Stack>
    </Card>
  );
}
