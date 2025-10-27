import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Grid,
  Group,
  NumberInput,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  ThemeIcon,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconArrowRight,
  IconBrain,
  IconCheck,
  IconDatabase,
  IconFilter,
  IconInfoCircle,
  IconMessageCircle,
  IconPlus,
  IconSettings,
  IconWand
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Pipeline Visualization Component
interface PipelineStep {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  isActive: boolean;
  isVisible: boolean;
}

interface PipelineVisualizationProps {
  selectedStrategy: string;
  selectedProviderId: string | null;
  selectedModel: string | null;
  enableReranking: boolean;
  selectedRerankerId: string | null;
  selectedRerankerModel: string | null;
  collectionName: string;
  providers: any[];
}

function PipelineVisualization({
  selectedStrategy,
  selectedProviderId,
  selectedModel,
  enableReranking,
  selectedRerankerId,
  selectedRerankerModel,
  collectionName,
  providers
}: PipelineVisualizationProps) {

  // Get provider names
  const getProviderName = (providerId: string | null) => {
    if (!providerId || !providers) return 'Not Selected';
    const provider = providers.find(p => p.id === providerId);
    return provider ? provider.name : 'Not Selected';
  };

  const getModelDisplay = (providerId: string | null, model: string | null) => {
    if (!model) return 'No Model Selected';
    return model;
  };

  // Build pipeline steps based on selections
  const buildPipelineSteps = (): PipelineStep[] => {
    const steps: PipelineStep[] = [];

    // Step 1: User Query
    steps.push({
      id: 'user_query',
      title: 'User Query',
      description: 'Input Question',
      icon: IconMessageCircle,
      color: 'indigo',
      isActive: true,
      isVisible: true
    });

    // Step 2: Query Enhancement (if not native)
    if (selectedStrategy !== 'native') {
      const strategyInfo = ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy);
      steps.push({
        id: 'query_enhancement',
        title: 'Query Enhancement',
        description: strategyInfo?.label || 'Enhance Query',
        icon: IconWand,
        color: strategyInfo?.color || 'blue',
        isActive: true,
        isVisible: true
      });
    }

    // Step 3: Document Retrieval
    steps.push({
      id: 'document_retrieval',
      title: 'Document Retrieval',
      description: collectionName ? `Search ${collectionName}` : 'No Collection Selected',
      icon: IconDatabase,
      color: collectionName ? 'cyan' : 'gray',
      isActive: !!collectionName,
      isVisible: true
    });

    // Step 4: Document Reranking (if enabled)
    if (enableReranking) {
      const rerankerProvider = getProviderName(selectedRerankerId);
      const rerankerModel = getModelDisplay(selectedRerankerId, selectedRerankerModel);

      steps.push({
        id: 'document_reranking',
        title: 'Document Reranking',
        description: `${rerankerProvider} (${rerankerModel})`,
        icon: IconFilter,
        color: 'orange',
        isActive: true,
        isVisible: true
      });
    }

    // Step 5: Generative Answer
    const llmProvider = getProviderName(selectedProviderId);
    const llmModel = getModelDisplay(selectedProviderId, selectedModel);

    steps.push({
      id: 'answer_generation',
      title: 'Generative Answer',
      description: `${llmProvider} (${llmModel})`,
      icon: IconBrain,
      color: 'green',
      isActive: true,
      isVisible: true
    });

    return steps;
  };

  const pipelineSteps = buildPipelineSteps();

  return (
    <Card withBorder p="md" radius="md" bg="gray.0" w="100%">
      <Stack gap="xs">
        <Group gap="xs">
          <IconSettings size={20} color="var(--mantine-color-blue-6)" />
          <Text fw={600} size="sm">Workflow Pipeline</Text>
        </Group>

        <Text size="xs" c="dimmed" style={{ lineHeight: 1.3, textAlign: 'center' }}>
          {pipelineSteps.length} steps • {selectedStrategy === 'native' ? 'Native RAG' : `${ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.label}`} • {enableReranking ? 'With Reranking' : 'No Reranking'} • {getProviderName(selectedProviderId)} LLM
        </Text>

        {/* Horizontal Pipeline Flow */}
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          paddingTop: '20px',
          paddingBottom: '20px',
          width: '100%',
          flexWrap: 'wrap'
        }}>
          {pipelineSteps.map((step, index) => {
            const StepIcon = step.icon;
            const isLast = index === pipelineSteps.length - 1;

            return (
              <div key={step.id} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                {/* Step */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: step.isVisible ? 1 : 0.5,
                  transform: step.isActive ? 'scale(1)' : 'scale(0.95)',
                  transition: 'all 0.3s ease',
                  minWidth: '100px',
                  maxWidth: '120px',
                  flexShrink: 0
                }}>
                  <ThemeIcon
                    size={28}
                    radius="xl"
                    color={step.color}
                    variant="light"
                    style={{
                      transition: 'all 0.3s ease',
                      boxShadow: step.isActive ? `0 2px 8px var(--mantine-color-${step.color}-3)` : 'none'
                    }}
                  >
                    <StepIcon size={14} />
                  </ThemeIcon>

                  <Stack gap={1} style={{ textAlign: 'center', maxWidth: '100px' }}>
                    <Text
                      size="xs"
                      fw={step.isActive ? 600 : 500}
                      c={step.isActive ? `${step.color}.7` : "gray.6"}
                      style={{ transition: 'all 0.3s ease' }}
                    >
                      {step.title}
                    </Text>
                    <Text size="xs" c="gray.6" style={{ lineHeight: 1.2 }}>
                      {step.description}
                    </Text>
                  </Stack>
                </div>

                {/* Connector Arrow (Horizontal) */}
                {!isLast && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '16px',
                    height: '16px',
                    flexShrink: 0,
                    marginLeft: '8px',
                    marginRight: '8px'
                  }}>
                    <IconArrowRight
                      size={14}
                      color="var(--mantine-color-gray-4)"
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

// Query enhancement strategies with detailed information
const ENHANCEMENT_STRATEGIES = [
  {
    value: 'native',
    label: 'Native RAG',
    description: 'Traditional RAG without query enhancement',
    details: 'Your query is sent directly to the retrieval system without any modifications. Best for simple, well-formed questions and fastest performance.',
    useCases: ['Simple lookups', 'Direct questions', 'Performance-critical scenarios', 'General purpose'],
    pros: ['Fastest performance', 'Most straightforward', 'No added complexity', 'Lowest cost'],
    cons: ['May miss relevant documents', 'Limited coverage', 'Depends on exact wording'],
    color: 'blue',
  },
  {
    value: 'augmented',
    label: 'Augmented (Best Coverage)',
    description: 'Combines original query with LLM-enhanced variants',
    details: 'Preserves your original query while also generating 2-3 enhanced variants. This ensures you never lose important context while benefiting from query improvements. Best of both worlds!',
    useCases: ['Important queries', 'When context matters', 'Balanced approach', 'Maximum coverage'],
    pros: ['Context preservation', 'Improved coverage', 'Safest option', 'Combines benefits'],
    cons: ['Slightly slower than Native', 'Uses more tokens'],
    color: 'green',
  },
  {
    value: 'step_back',
    label: 'Step-Back',
    description: 'Generate broader conceptual questions',
    details: 'Creates higher-level, conceptual questions from your specific query. Helps find foundational knowledge and principles.',
    useCases: ['Technical deep-dives', 'Learning new concepts', 'Understanding fundamentals'],
    pros: ['Better conceptual understanding', 'Finds foundational docs', 'Good for research'],
    cons: ['May be too broad', 'Could miss specific details'],
    color: 'violet',
  },
  {
    value: 'multi_query',
    label: 'Multi-Query',
    description: 'Generate alternative phrasings',
    details: 'Creates multiple alternative ways to phrase your question. Helps overcome vocabulary mismatches between your query and documents.',
    useCases: ['Complex queries', 'When exact terms are unknown', 'Broad coverage needed'],
    pros: ['Better coverage', 'Handles synonyms', 'Vocabulary flexibility'],
    cons: ['More processing time', 'May introduce noise'],
    color: 'teal',
  },
  {
    value: 'hyde',
    label: 'HyDE (Hypothetical Document Embeddings)',
    description: 'Generate hypothetical answers for better matching',
    details: 'Creates hypothetical answers to your question, then searches for documents similar to those answers. Excellent for semantic similarity.',
    useCases: ['Answer-seeking queries', 'When you know what format you want', 'Semantic search'],
    pros: ['Excellent semantic matching', 'Finds answer-like docs', 'Good for how-to questions'],
    cons: ['Requires good LLM', 'May hallucinate', 'Slower performance'],
    color: 'grape',
  },
  {
    value: 'decomposition',
    label: 'Decomposition',
    description: 'Break complex queries into sub-questions',
    details: 'Splits your complex question into simpler sub-questions. Each sub-question is processed separately for comprehensive coverage.',
    useCases: ['Complex multi-part questions', 'Research tasks', 'Thorough analysis needed'],
    pros: ['Handles complexity', 'Comprehensive results', 'Systematic approach'],
    cons: ['Slowest option', 'Most expensive', 'May over-complicate simple queries'],
    color: 'orange',
  },
  {
    value: 'rag_fusion',
    label: 'RAG Fusion',
    description: 'Generate multiple query perspectives',
    details: 'Creates multiple diverse perspectives of your query and fuses the results using reciprocal rank fusion. Excellent for comprehensive retrieval.',
    useCases: ['Research queries', 'When you need diverse perspectives', 'Critical decisions'],
    pros: ['Most comprehensive', 'Diverse perspectives', 'Robust results'],
    cons: ['Expensive', 'Slower', 'May be overkill for simple queries'],
    color: 'pink',
  },
];

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Apps', href: paths.dashboard.apps.root },
  { label: 'Knowledge Conversations', href: paths.dashboard.apps.knowledgeSearch },
  { label: 'Create Conversation' },
];

// Query transformation examples for each strategy
const getQueryExample = (strategyValue: string): string => {
  switch (strategyValue) {
    case 'hyde':
      return '"What are the steps to configure SSL certificates? What are the security considerations? What are the common SSL configuration issues?"';
    case 'step_back':
      return '"What is SSL? How do I configure SSL certificates? What are SSL security best practices?"';
    case 'decomposition':
      return '"How to configure SSL certificates", "SSL certificate installation steps", "SSL security configuration"';
    case 'rag_fusion':
      return '"How to configure SSL certificates", "SSL certificate setup guide", "SSL configuration best practices"';
    case 'multi_query':
      return '"How to configure SSL certificates", "SSL certificate installation", "SSL setup tutorial"';
    case 'augmented':
      return '"How to configure SSL certificates" + "Please provide detailed steps for SSL certificate configuration including security considerations"';
    default:
      return '"How to configure SSL certificates"';
  }
};

export default function ConversationCreate() {
  const navigate = useNavigate();

  // Form state
  const [conversationName, setConversationName] = useState('');
  const [conversationDescription, setConversationDescription] = useState('');
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('native');
  const [collectionName, setCollectionName] = useState('LongTermMemory');
  const [enableReranking, setEnableReranking] = useState(false);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [enableLLMGeneration, setEnableLLMGeneration] = useState(true);
  const [topK, setTopK] = useState(5);
  const [isCreating, setIsCreating] = useState(false);

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // Update reranker defaults when LLM provider or model changes
  useEffect(() => {
    if (enableReranking && selectedProviderId && selectedModel) {
      setSelectedRerankerId(selectedProviderId);
      setSelectedRerankerModel(selectedModel);
    }
  }, [selectedProviderId, selectedModel, enableReranking]);

  // API functions
  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  const createNewConversation = async () => {
    try {
      setIsCreating(true);

      // Validate required fields
      if (enableLLMGeneration && !selectedProviderId) {
        notifications.show({
          title: 'Error',
          message: 'Please select an LLM provider when Generative Answer is enabled',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
        return;
      }

      if (enableLLMGeneration && !selectedModel) {
        notifications.show({
          title: 'Error',
          message: 'Please select an LLM model when Generative Answer is enabled',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
        return;
      }

      if (!collectionName) {
        notifications.show({
          title: 'Error',
          message: 'Please select a Vector DB Collection',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
        return;
      }

      const token = localStorage.getItem('jwt_token');

      const payload: any = {
        name: conversationName.trim() || 'New Conversation',
      };

      if (conversationDescription.trim()) {
        payload.description = conversationDescription.trim();
      }

      if (selectedProviderId) {
        payload.llm_provider_id = selectedProviderId;
      }

      if (selectedModel) {
        payload.llm_model_name = selectedModel;
      }

      if (selectedStrategy && selectedStrategy !== 'none') {
        payload.enhancement_strategy = selectedStrategy;
      }

      if (collectionName.trim()) {
        payload.collection_name = collectionName.trim();
      }

      // Reranking configuration
      payload.enable_reranking = enableReranking;
      if (enableReranking && selectedRerankerId) {
        payload.reranker_provider_id = selectedRerankerId;
      }
      if (enableReranking && selectedRerankerModel) {
        payload.reranker_model_name = selectedRerankerModel;
      }

      // LLM generation configuration
      payload.enable_llm_generation = enableLLMGeneration;

      // Vector search configuration
      payload.top_k = topK;

      const response = await fetch(buildApiUrl('/conversations'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        const sessionId = data.id;

        notifications.show({
          title: 'Success',
          message: 'Conversation created successfully',
          color: 'green',
          icon: <IconCheck size={16} />,
        });

        // Navigate to the conversation window
        navigate(paths.dashboard.apps.conversation(sessionId));
      } else {
        const errorData = await response.json().catch(() => ({}));
        notifications.show({
          title: 'Error',
          message: errorData.detail || 'Failed to create conversation',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
      }
    } catch (error) {
      console.error('Error creating new conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to create conversation',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setIsCreating(false);
    }
  };


  return (
    <Page title="Create Conversation">
      <PageHeader
        title="Create New Conversation"
        breadcrumbs={breadcrumbs}
      />

      <Grid>
        {/* Left Column - Form */}
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Stack gap="md">
            {/* Basic Information */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconMessageCircle size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Basic Information</Title>
                </Group>

                <Grid gutter="md">
                  <Grid.Col span={6}>
                    <TextInput
                      label="Conversation Name"
                      placeholder="e.g., SSL Configuration Help"
                      value={conversationName}
                      onChange={(e) => setConversationName(e.target.value)}
                      required
                      description="Give your conversation a descriptive name"
                    />
                  </Grid.Col>

                  <Grid.Col span={6}>
                    <Textarea
                      label="Description (Optional)"
                      placeholder="Brief description of what this conversation is about..."
                      value={conversationDescription}
                      onChange={(e) => setConversationDescription(e.target.value)}
                      minRows={2}
                      maxRows={4}
                      description="Optional description for context"
                    />
                  </Grid.Col>
                </Grid>

                <Grid gutter="md">
                  <Grid.Col span={6}>
                    <Select
                      label="Vector DB Collection"
                      placeholder={collectionsLoading ? 'Loading collections...' : 'Select a collection'}
                      data={collections?.map((c) => ({
                        value: c.name,
                        label: `${c.name} (${c.record_count.toLocaleString()} records)`,
                      })) || []}
                      value={collectionName}
                      onChange={(value) => setCollectionName(value || 'LongTermMemory')}
                      searchable
                      required
                      disabled={collectionsLoading}
                      description="Choose the vector database collection to search"
                      renderOption={(item) => (
                        <div>
                          <Group justify="space-between" w="100%">
                            <div>
                              <Text size="sm" fw={500}>{collections?.find(c => c.name === item.option.value)?.name}</Text>
                              {collections?.find(c => c.name === item.option.value)?.description && (
                                <Text size="xs" c="dimmed">
                                  {collections.find(c => c.name === item.option.value)?.description}
                                </Text>
                              )}
                            </div>
                            <Badge size="sm" variant="light">
                              {collections?.find(c => c.name === item.option.value)?.record_count.toLocaleString()} records
                            </Badge>
                          </Group>
                        </div>
                      )}
                    />
                  </Grid.Col>

                  <Grid.Col span={6}>
                    <NumberInput
                      label="Search Results Limit"
                      placeholder="Number of documents to retrieve"
                      value={topK}
                      onChange={(value) => setTopK(typeof value === 'number' ? value : 5)}
                      min={3}
                      max={10}
                      required
                      description="Number of documents to retrieve from vector database (3-10)"
                    />
                  </Grid.Col>
                </Grid>
              </Stack>
            </Card>

            {/* Query Enhancement Strategy */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconSettings size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Query Enhancement Strategy</Title>
                </Group>

                <Select
                  label="Enhancement Strategy"
                  placeholder="Select strategy"
                  data={ENHANCEMENT_STRATEGIES.map((s) => ({
                    value: s.value,
                    label: s.label,
                  }))}
                  value={selectedStrategy}
                  onChange={(value) => setSelectedStrategy(value || 'none')}
                  description="Select how your queries will be enhanced for better retrieval"
                />
              </Stack>
            </Card>

            {/* Document Reranking Configuration */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconFilter size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Document Reranking</Title>
                </Group>

                <Switch
                  label="Enable Document Reranking"
                  description="When enabled, retrieved documents are judged and reranked before answer generation. When disabled, documents go directly to answer generation."
                  checked={enableReranking}
                  onChange={(event) => {
                    setEnableReranking(event.currentTarget.checked);
                    if (!event.currentTarget.checked) {
                      setSelectedRerankerId(null);
                      setSelectedRerankerModel(null);
                    } else {
                      // When enabling reranking, default to LLM provider and model
                      setSelectedRerankerId(selectedProviderId);
                      setSelectedRerankerModel(selectedModel);
                    }
                  }}
                />

                {enableReranking && (
                  <>
                    <Grid gutter="md">
                      <Grid.Col span={6}>
                        <Select
                          label="Reranker Provider (Optional)"
                          placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
                          data={[
                            {
                              group: 'Specialized Rerankers',
                              items: providers
                                ?.filter((p) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
                                .map((p) => ({
                                  value: p.id,
                                  label: `${p.name} (Dedicated Reranker)`,
                                })) || []
                            },
                            {
                              group: 'LLMs as Rerankers',
                              items: providers
                                ?.filter((p) => p.generative && p.generative.models && p.generative.models.length > 0 && (!p.reranker || !p.reranker.models || p.reranker.models.length === 0))
                                .map((p) => ({
                                  value: p.id,
                                  label: `${p.name} (LLM Judging)`,
                                })) || []
                            }
                          ]}
                          value={selectedRerankerId}
                          onChange={(value) => {
                            setSelectedRerankerId(value);
                            setSelectedRerankerModel(null);
                          }}
                          searchable
                          clearable
                          disabled={providersLoading || !providers}
                          description="Choose a specialized reranker or any LLM"
                        />
                      </Grid.Col>

                      <Grid.Col span={6}>
                        <Select
                          label="Reranker Model"
                          placeholder="Select a model"
                          data={
                            selectedRerankerId && providers
                              ? (() => {
                                const provider = providers.find((p) => p.id === selectedRerankerId);
                                if (!provider) return [];

                                // If provider has dedicated reranker models, use those
                                if (provider.reranker && provider.reranker.models && provider.reranker.models.length > 0) {
                                  return provider.reranker.models.map((model) => ({
                                    value: model,
                                    label: model,
                                  }));
                                }

                                // Otherwise, use generative models for LLM judging
                                if (provider.generative && provider.generative.models) {
                                  return provider.generative.models.map((model) => ({
                                    value: model,
                                    label: model,
                                  }));
                                }

                                return [];
                              })()
                              : []
                          }
                          value={selectedRerankerModel}
                          onChange={setSelectedRerankerModel}
                          searchable
                          clearable
                          disabled={!selectedRerankerId}
                          description="Choose the model for reranking"
                        />
                      </Grid.Col>
                    </Grid>
                  </>
                )}
              </Stack>
            </Card>

            {/* Generative Answer Configuration */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconBrain size={20} color="var(--mantine-color-green-6)" />
                  <Title order={4}>Generative Answer</Title>
                </Group>

                <Switch
                  label="Enable Generative Answer"
                  description="Generate natural language answers (slower, costs tokens) or show raw results (faster, exact sources)"
                  checked={enableLLMGeneration}
                  onChange={(event) => setEnableLLMGeneration(event.currentTarget.checked)}
                />

                {enableLLMGeneration ? (
                  <>
                    <Grid gutter="md">
                      <Grid.Col span={6}>
                        <Select
                          label="LLM Provider"
                          placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
                          data={providers?.map((p) => ({
                            value: p.id,
                            label: `${p.name} (${p.provider_type})`,
                          })) || []}
                          value={selectedProviderId}
                          onChange={(value) => {
                            setSelectedProviderId(value);
                            setSelectedModel(null);
                          }}
                          searchable
                          required
                          disabled={providersLoading || !providers || providers.length === 0}
                          description="Choose the LLM provider for this conversation"
                        />
                      </Grid.Col>

                      <Grid.Col span={6}>
                        <Select
                          label="LLM Provider Model"
                          placeholder="Select a model"
                          data={
                            selectedProviderId && providers
                              ? providers
                                .find((p) => p.id === selectedProviderId)
                                ?.generative?.models.map((model) => ({
                                  value: model,
                                  label: model,
                                })) || []
                              : []
                          }
                          value={selectedModel}
                          onChange={setSelectedModel}
                          searchable
                          disabled={!selectedProviderId}
                          required
                          description="Choose the LLM provider model for this conversation"
                        />
                      </Grid.Col>
                    </Grid>
                  </>
                ) : (
                  <Alert icon={<IconInfoCircle size={16} />} color="yellow" variant="light">
                    <Text size="sm">
                      <strong>Raw Results Mode:</strong> Documents will be displayed as-is without LLM processing.
                      <br />
                      <strong>Benefits:</strong> Faster responses, no token costs, 100% factual accuracy, full traceability.
                      <br />
                      <strong>Best for:</strong> Research, legal review, debugging, technical documentation.
                    </Text>
                  </Alert>
                )}
              </Stack>
            </Card>

            {/* Action Buttons */}
            <Group justify="space-between">
              <Button
                variant="subtle"
                color="gray"
                onClick={() => navigate(paths.dashboard.apps.knowledgeSearch)}
                disabled={isCreating}
                leftSection={<IconArrowLeft size={16} />}
              >
                Cancel
              </Button>
              <Button
                onClick={createNewConversation}
                loading={isCreating}
                leftSection={<IconPlus size={16} />}
                color="blue"
                size="md"
              >
                Create Conversation
              </Button>
            </Group>
          </Stack>
        </Grid.Col>

        {/* Right Column - Strategy Information */}
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Stack gap="sm" pos="sticky" top={20}>
            {/* Pipeline Visualization */}
            <PipelineVisualization
              selectedStrategy={selectedStrategy}
              selectedProviderId={selectedProviderId}
              selectedModel={selectedModel}
              enableReranking={enableReranking}
              selectedRerankerId={selectedRerankerId}
              selectedRerankerModel={selectedRerankerModel}
              collectionName={collectionName}
              providers={providers || []}
            />

            {/* Strategy Details Card - Shows when strategy is selected */}
            {selectedStrategy && selectedStrategy !== 'none' && (
              <Card withBorder p="md" radius="md" bg="blue.0" style={{ border: '1px solid var(--mantine-color-blue-2)' }}>
                <Stack gap="sm">
                  <Group gap="xs">
                    <Badge size="sm" color={ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.color || 'blue'} variant="light">
                      {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.label}
                    </Badge>
                  </Group>

                  <Text size="sm" c="dimmed">
                    {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.description}
                  </Text>

                  {/* Query Transformation Example */}
                  {selectedStrategy !== 'native' && (
                    <Box>
                      <Text size="sm" fw={500} mb="xs" c="blue.7">Query Transformation Example:</Text>
                      <Box p="sm" bg="white" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-blue-2)' }}>
                        <Text size="xs" c="dimmed" mb="xs">
                          <strong>Original Query:</strong> "How to configure SSL?"
                        </Text>
                        <Text size="xs" c="blue.7">
                          <strong>Enhanced Query:</strong> {getQueryExample(selectedStrategy)}
                        </Text>
                      </Box>
                    </Box>
                  )}

                  <Grid gutter="sm">
                    <Grid.Col span={6}>
                      <Text size="xs" fw={500} mb="xs" c="dimmed">Best For:</Text>
                      <Stack gap={2}>
                        {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.useCases.slice(0, 3).map((useCase: string, idx: number) => (
                          <Text key={idx} size="xs" c="dimmed">
                            • {useCase}
                          </Text>
                        ))}
                      </Stack>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="xs" fw={500} mb="xs" c="dimmed">Pros:</Text>
                      <Stack gap={2}>
                        {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.pros.slice(0, 2).map((pro: string, idx: number) => (
                          <Text key={idx} size="xs" c="green.7">
                            ✓ {pro}
                          </Text>
                        ))}
                      </Stack>
                    </Grid.Col>
                  </Grid>
                </Stack>
              </Card>
            )}

            {/* Reranking Information Card */}
            <Card withBorder p="md" radius="md" bg="orange.0" style={{ border: '1px solid var(--mantine-color-orange-2)' }}>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconFilter size={16} color="var(--mantine-color-orange-6)" />
                  <Text fw={600} size="sm" c="orange.7">Document Reranking</Text>
                </Group>

                <Text size="xs" c="dimmed" mb="xs">
                  When enabled, retrieved documents are judged and reranked before answer generation for better accuracy.
                </Text>

                <Box p="xs" bg="white" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-orange-2)' }}>
                  <Text size="xs" c="dimmed" fw={500} mb="xs">Reranking Options:</Text>
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed">
                      • <strong>Dedicated Reranker:</strong> Specialized models (Cohere, Voyage AI)
                    </Text>
                    <Text size="xs" c="dimmed">
                      • <strong>LLM as Reranker:</strong> Any generative LLM for judging
                    </Text>
                    <Text size="xs" c="dimmed">
                      • <strong>No Selection:</strong> Uses conversation's main LLM
                    </Text>
                  </Stack>
                </Box>

                <Text size="xs" c="orange.6" fw={500}>
                  Note: If disabled, documents go directly from retrieval to answer generation.
                </Text>
              </Stack>
            </Card>
          </Stack>
        </Grid.Col>
      </Grid>
    </Page>
  );
}

