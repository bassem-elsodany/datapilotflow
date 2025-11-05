import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { SystemPromptManager } from '@/components/system-prompt-manager';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  Accordion,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Checkbox,
  Divider,
  Grid,
  Group,
  List,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
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
  IconArrowsLeftRight,
  IconBrain,
  IconCheck,
  IconDatabase,
  IconFilter,
  IconHelp,
  IconInfoCircle,
  IconMessageCircle,
  IconPlus,
  IconRobot,
  IconSettings,
  IconWand,
  IconX
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ConversationCanvasBuilder } from './components/ConversationCanvasBuilder';

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

    // Step 4: Judge Ranker (if enabled)
    if (enableReranking) {
      const rankerProvider = getProviderName(selectedRerankerId);
      const rankerModel = getModelDisplay(selectedRerankerId, selectedRerankerModel);

      steps.push({
        id: 'judge_ranker',
        title: 'Judge Ranker',
        description: `${rankerProvider} (${rankerModel})`,
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
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Searches directly with: "How to configure SSL certificates in Apache?"'
    }
  },
  {
    value: 'augmented',
    label: 'Augmented (Best Coverage)',
    description: 'Systematic transformations for maximum coverage',
    details: 'Applies 4 specific transformation techniques to your query: (1) Synonym Expansion, (2) Query Expansion (add implicit concepts), (3) Query Contraction (focus on core), (4) Technical Reformulation. Each variant explores a different semantic space (broad/narrow/technical/simple). Preserves original query. Uses RRF to merge all variants.',
    useCases: ['Maximum coverage needed', 'Comprehensive search', 'Documents use varied styles', 'Critical queries'],
    pros: ['Systematic coverage', 'Fills retrieval gaps', 'Explores all angles', 'Context preserved'],
    cons: ['Slightly slower than Native', 'Uses more tokens', 'May be overkill for simple queries'],
    color: 'green',
    example: {
      original: 'SSL configuration in production',
      output: 'Transforms systematically:\n1. Original: "SSL configuration in production"\n2. Synonym: "secure socket layer setup in production environment"\n3. Expanded: "SSL certificate configuration HTTPS production deployment"\n4. Contracted: "SSL production config"\n5. Technical: "TLS security settings live environment"'
    }
  },
  {
    value: 'multi_query',
    label: 'Multi-Query',
    description: 'Rephrase the same question in different ways',
    details: 'Generates 3-5 alternative phrasings of the SAME question using different vocabulary and wording. Targets different document types (tutorials, guides, API docs) and expertise levels (beginner vs expert). All variants express the same intent. Uses RRF to merge results from all phrasings.',
    useCases: ['Documents use varied terminology', 'Unknown exact terms', 'Vocabulary mismatches', 'Different doc styles'],
    pros: ['Linguistic flexibility', 'Handles synonyms', 'Matches varied writing styles', 'Simple approach'],
    cons: ['Same semantic space', 'May miss edge cases', 'Not as systematic as Augmented'],
    color: 'teal',
    example: {
      original: 'Salesforce platform event listener config',
      output: 'Rephrases in different ways:\n1. "How to configure Salesforce platform event listeners?"\n2. "Salesforce platform event subscription setup"\n3. "Setting up Salesforce platform event handlers"\n4. "Salesforce platform event listener configuration guide"\n5. "Steps to configure Salesforce event listeners"'
    }
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
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Generates hypothetical answer:\n"To configure SSL in Apache, first install mod_ssl, then create a VirtualHost with SSLEngine on, SSLCertificateFile pointing to your cert, and SSLCertificateKeyFile for the private key. Restart Apache to apply changes."\n\nThen searches for documents similar to this answer.'
    }
  },
  {
    value: 'decomposition',
    label: 'Decomposition',
    description: 'Break complex queries into sub-questions',
    details: 'Splits your complex question into simpler sub-questions. Each sub-question is processed separately for comprehensive coverage. Uses RRF to merge results from all sub-queries.',
    useCases: ['Complex multi-part questions', 'Research tasks', 'Thorough analysis needed'],
    pros: ['Handles complexity', 'RRF merges sub-queries', 'Comprehensive results', 'Systematic approach'],
    cons: ['Slowest option', 'Most expensive', 'May over-complicate simple queries'],
    color: 'orange',
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Breaks down into sub-questions:\n1. "What are the prerequisites for SSL in Apache?"\n2. "How to generate or obtain SSL certificates?"\n3. "What are the Apache SSL configuration directives?"\n4. "How to test and verify SSL configuration?"'
    }
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
    case 'decomposition':
      return '"How to configure SSL certificates", "SSL certificate installation steps", "SSL security configuration"';
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
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') || 'wizard'; // 'wizard' or 'pipeline'

  // If mode is pipeline, render pipeline canvas instead
  if (mode === 'pipeline') {
    return <ConversationCanvasBuilder />;
  }

  // Otherwise, render the wizard
  return <ConversationWizard />;
}

// Wizard Component (existing logic)
function ConversationWizard() {
  const navigate = useNavigate();

  // Form state
  const [conversationName, setConversationName] = useState('');
  const [conversationDescription, setConversationDescription] = useState('');
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('native');
  const [collectionName, setCollectionName] = useState('LongTermMemory');
  const [enableReranking, setEnableReranking] = useState(false);
  const [relevanceThreshold, setRelevanceThreshold] = useState(0.5);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [enableLLMGeneration, setEnableLLMGeneration] = useState(true);
  const [topK, setTopK] = useState(5);
  const [enableKnowledgeAssistant, setEnableKnowledgeAssistant] = useState(true);
  const [selectedSystemPromptId, setSelectedSystemPromptId] = useState<string | undefined>();
  const [isCreating, setIsCreating] = useState(false);

  // Strategies info modal state
  const [strategiesInfoModalOpen, setStrategiesInfoModalOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // Helper function to get provider name
  const getProviderName = (providerId: string | null) => {
    if (!providerId || !providers) return 'Not Selected';
    const provider = providers.find(p => p.id === providerId);
    return provider ? provider.name : 'Not Selected';
  };

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
      if (selectedStrategy !== 'native' && !conversationDescription.trim()) {
        notifications.show({
          title: 'Error',
          message: 'Description is required when using query enhancement strategies',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
        return;
      }

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
      payload.relevance_threshold = relevanceThreshold;
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

      // Multi-agent orchestration configuration
      payload.enable_knowledge_assistant = enableKnowledgeAssistant;
      if (enableKnowledgeAssistant && selectedSystemPromptId) {
        payload.selected_system_prompt_id = selectedSystemPromptId;
      }

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
    <Page title="Create New Conversation Agent">
      <PageHeader
        title="Create New Conversation Agent"
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
                      label={selectedStrategy !== 'native' ? "Description (Required for Query Enhancement)" : "Description (Optional)"}
                      placeholder={selectedStrategy !== 'native'
                        ? "Describe the domain/topic to help enhance queries (e.g., 'MuleSoft API documentation and integration guides')"
                        : "Brief description of what this conversation is about..."}
                      value={conversationDescription}
                      onChange={(e) => setConversationDescription(e.target.value)}
                      minRows={2}
                      maxRows={4}
                      required={selectedStrategy !== 'native'}
                      error={selectedStrategy !== 'native' && !conversationDescription.trim() ? 'Description is required when using query enhancement' : undefined}
                      description={selectedStrategy !== 'native' ? "This helps the AI understand the domain and provide better query enhancements" : "Optional description for context"}
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
                      min={5}
                      max={30}
                      required
                      description="Number of documents to retrieve from vector database (5-30)"
                    />
                  </Grid.Col>
                </Grid>
              </Stack>
            </Card>

            {/* Query Enhancement Strategy */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs" justify="space-between" align="flex-start">
                  <Group gap="xs">
                    <IconSettings size={20} color="var(--mantine-color-blue-6)" />
                    <Title order={4}>Query Enhancement Strategy</Title>
                  </Group>
                  <Button
                    size="xs"
                    variant="gradient"
                    gradient={{ from: 'violet', to: 'purple', deg: 135 }}
                    leftSection={<IconHelp size={16} />}
                    onClick={() => setStrategiesInfoModalOpen(true)}
                    style={{
                      boxShadow: '0 2px 8px rgba(109, 40, 217, 0.3)',
                    }}
                  >
                    Learn & Compare
                  </Button>
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

                {/* RRF Info Alert for multi-variant strategies */}
                {selectedStrategy !== 'native' && selectedStrategy !== 'hyde' && (
                  <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                    <Stack gap={6}>
                      <Text size="xs">
                        <strong>Reciprocal Rank Fusion (RRF) Auto-Enabled:</strong> This strategy generates multiple query variants.
                      </Text>
                      <Text size="xs" c="dimmed">
                        The system will:
                      </Text>
                      <List size="xs" withPadding>
                        <List.Item>Search your knowledge base with ALL variants in parallel</List.Item>
                        <List.Item>Merge results using RRF algorithm (documents appearing in multiple searches rank higher)</List.Item>
                        <List.Item>Return your configured Top K documents (the best matches after merging)</List.Item>
                      </List>
                      <Text size="xs" c="dimmed">
                        Example: With 5 query variants and Top K=10, the system retrieves ~15 documents per variant, merges them via RRF, and returns your final 10 best documents.
                      </Text>
                    </Stack>
                  </Alert>
                )}

                {/* Single query info for HyDE */}
                {(selectedStrategy === 'hyde') && (
                  <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
                    <Text size="xs">
                      <strong>Single Enhanced Query:</strong> This strategy generates one enhanced query variant.
                      The system will search using this single enhanced query (no RRF merging needed).
                    </Text>
                  </Alert>
                )}
              </Stack>
            </Card>

            {/* Judge Ranker Configuration */}
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconFilter size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Judge Ranker</Title>
                </Group>

                <Switch
                  label="Enable Judge Ranker"
                  description="When enabled, retrieved documents are evaluated and ranked before answer generation. When disabled, documents go directly to answer generation."
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
                          label="Judge Ranker Provider (Optional)"
                          placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
                          data={[
                            {
                              group: 'Specialized Judges',
                              items: providers
                                ?.filter((p) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
                                .map((p) => ({
                                  value: p.id,
                                  label: `${p.name} (Dedicated Judge)`,
                                })) || []
                            },
                            {
                              group: 'LLMs as Judges',
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
                          description="Choose a specialized judge or any LLM"
                        />
                      </Grid.Col>

                      <Grid.Col span={6}>
                        <Select
                          label="Judge Model"
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
                          description="Choose the model for judging"
                        />
                      </Grid.Col>
                    </Grid>

                    <Stack gap="sm" mt="md">
                      <NumberInput
                        label="Relevance Threshold"
                        description="Minimum relevance score (0.0-1.0) for filtering documents. Documents scoring below this threshold are excluded from the answer."
                        min={0}
                        max={1}
                        step={0.05}
                        value={relevanceThreshold}
                        onChange={(value) => setRelevanceThreshold(typeof value === 'number' ? value : 0.5)}
                        placeholder="0.5"
                      />
                      <Alert
                        icon={<IconInfoCircle size={16} />}
                        title="Relevance Threshold Guide"
                        color="blue"
                        variant="light"
                      >
                        <List size="sm" spacing="xs">
                          <List.Item><strong>0.0 - 0.25:</strong> Very permissive - keeps almost all documents</List.Item>
                          <List.Item><strong>0.5 (Default):</strong> Moderate - balances quality and coverage</List.Item>
                          <List.Item><strong>0.75 - 1.0:</strong> Very strict - keeps only highly relevant documents</List.Item>
                        </List>
                      </Alert>
                    </Stack>
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

            {/* Knowledge Assistant Card */}
            <Card withBorder shadow="sm" radius="md" p="md">
              <Stack gap="md">
                <Group gap="xs">
                  <ThemeIcon size="md" variant="light" color="grape">
                    <IconRobot size={18} />
                  </ThemeIcon>
                  <Title order={4}>Knowledge Assistant</Title>
                </Group>

                <Switch
                  label="Enable Knowledge Assistant"
                  description="Let AI perform tasks (like writing, coding, analysis) using information from your knowledge base as context."
                  checked={enableKnowledgeAssistant}
                  onChange={(event) => setEnableKnowledgeAssistant(event.currentTarget.checked)}
                />

                {enableKnowledgeAssistant ? (
                  <>
                    <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light">
                      <Text size="sm">
                        <strong>Knowledge Assistant Mode:</strong> AI searches your knowledge base AND performs tasks using what it finds.
                        <br />
                        <strong>How it works:</strong> Finds relevant info from your docs → Uses it to complete your task
                        <br />
                        <strong>Best for:</strong> "Write a summary based on...", "Generate code using our docs", "Create a plan from..."
                      </Text>
                    </Alert>

                    <SystemPromptManager
                      conversationId=""
                      selectedPromptId={selectedSystemPromptId}
                      onPromptSelected={(prompt) => setSelectedSystemPromptId(prompt.id)}
                    />
                  </>
                ) : (
                  <Alert icon={<IconInfoCircle size={16} />} color="yellow" variant="light">
                    <Text size="sm">
                      <strong>Search-Only Mode:</strong> AI only searches and displays information from your knowledge base.
                      <br />
                      <strong>Best for:</strong> "What is...?", "Find documents about...", "Show me information on..."
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

          </Stack>
        </Grid.Col>
      </Grid>

      {/* Strategies Info Modal */}
      <Modal
        opened={strategiesInfoModalOpen}
        onClose={() => {
          setStrategiesInfoModalOpen(false);
          setComparisonMode(false);
          setSelectedForComparison([]);
        }}
        title={
          <Group gap="xs">
            <ThemeIcon
              size="md"
              variant="filled"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              }}
            >
              <IconHelp size={18} />
            </ThemeIcon>
            <Text fw={600}>Query Enhancement Strategies</Text>
          </Group>
        }
        size="xl"
      >
        <Stack gap="lg">
          <Group justify="space-between" align="center">
            <Text size="sm" c="dimmed">
              {comparisonMode
                ? 'Select two strategies to compare side-by-side'
                : 'Choose the right strategy based on your query complexity and desired retrieval quality'
              }
            </Text>
            <Button
              variant={comparisonMode ? 'filled' : 'light'}
              color="violet"
              size="xs"
              leftSection={<IconArrowsLeftRight size={16} />}
              onClick={() => {
                setComparisonMode(!comparisonMode);
                setSelectedForComparison([]);
              }}
            >
              {comparisonMode ? 'Back to Browse' : 'Compare Strategies'}
            </Button>
          </Group>

          {!comparisonMode ? (
            // Browse Mode - Accordion
            <>
              <Accordion
                variant="separated"
                defaultValue={selectedStrategy}
                styles={{
                  item: {
                    border: '1px solid var(--mantine-color-gray-3)',
                    '&[data-active]': {
                      borderLeftWidth: '4px',
                    },
                  },
                }}
              >
                {ENHANCEMENT_STRATEGIES.map((strategy) => (
                  <Accordion.Item
                    key={strategy.value}
                    value={strategy.value}
                    style={{
                      borderLeft: `4px solid var(--mantine-color-${strategy.color}-6)`,
                    }}
                  >
                    <Accordion.Control>
                      <Group justify="space-between" align="center" wrap="nowrap">
                        <Group gap="xs">
                          <ThemeIcon size="sm" color={strategy.color} variant="light">
                            <IconSettings size={14} />
                          </ThemeIcon>
                          <div>
                            <Text fw={600} size="sm">
                              {strategy.label}
                            </Text>
                            <Text size="xs" c="dimmed">
                              {strategy.description}
                            </Text>
                          </div>
                        </Group>
                        {selectedStrategy === strategy.value && (
                          <Badge color="green" variant="light" leftSection={<IconCheck size={12} />}>
                            Active
                          </Badge>
                        )}
                      </Group>
                    </Accordion.Control>
                    <Accordion.Panel>
                      <Stack gap="md" pt="xs">
                        <Text size="sm">{strategy.details}</Text>

                        <Grid gutter="md">
                          <Grid.Col span={6}>
                            <div>
                              <Text size="xs" fw={600} c="green.7" mb={4}>
                                ✓ Pros
                              </Text>
                              <List size="xs" spacing={2}>
                                {strategy.pros.map((pro, idx) => (
                                  <List.Item key={idx}>{pro}</List.Item>
                                ))}
                              </List>
                            </div>
                          </Grid.Col>

                          <Grid.Col span={6}>
                            <div>
                              <Text size="xs" fw={600} c="red.7" mb={4}>
                                ✗ Cons
                              </Text>
                              <List size="xs" spacing={2}>
                                {strategy.cons.map((con, idx) => (
                                  <List.Item key={idx}>{con}</List.Item>
                                ))}
                              </List>
                            </div>
                          </Grid.Col>
                        </Grid>

                        <div>
                          <Text size="xs" fw={600} c="blue.7" mb={4}>
                            Best for:
                          </Text>
                          <Group gap={6}>
                            {strategy.useCases.map((useCase, idx) => (
                              <Badge key={idx} size="xs" variant="dot" color={strategy.color}>
                                {useCase}
                              </Badge>
                            ))}
                          </Group>
                        </div>

                        {strategy.example && (
                          <Paper p="sm" withBorder bg="gray.0">
                            <Stack gap="xs">
                              <Text size="xs" fw={600} c="violet.7">
                                📝 Example
                              </Text>
                              <div>
                                <Text size="xs" c="dimmed" mb={2}>Original Query:</Text>
                                <Text size="xs" fw={500}>{strategy.example.original}</Text>
                              </div>
                              <div>
                                <Text size="xs" c="dimmed" mb={2}>Strategy Output:</Text>
                                <Text size="xs" style={{ whiteSpace: 'pre-line' }}>{strategy.example.output}</Text>
                              </div>
                            </Stack>
                          </Paper>
                        )}
                      </Stack>
                    </Accordion.Panel>
                  </Accordion.Item>
                ))}
              </Accordion>

              <Divider />

              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text size="sm">
                  <strong>Tip:</strong> Start with <strong>Native RAG</strong> for simple queries or <strong>Augmented</strong> for best coverage.
                  Use advanced strategies like <strong>RAG Fusion</strong> or <strong>Decomposition</strong> when you need comprehensive, high-quality results and don't mind the extra processing time.
                </Text>
              </Alert>
            </>
          ) : (
            // Comparison Mode
            <>
              {selectedForComparison.length < 2 ? (
                // Selection Phase
                <Stack gap="sm">
                  <Alert icon={<IconInfoCircle size={16} />} color="violet" variant="light">
                    <Text size="sm">
                      Select <strong>{2 - selectedForComparison.length}</strong> {selectedForComparison.length === 1 ? 'more strategy' : 'strategies'} to compare
                      {selectedForComparison.length > 0 && (
                        <Badge ml="xs" color="violet" variant="light">
                          {selectedForComparison.length} selected
                        </Badge>
                      )}
                    </Text>
                  </Alert>

                  <Stack gap="xs">
                    {ENHANCEMENT_STRATEGIES.map((strategy) => (
                      <Card
                        key={strategy.value}
                        padding="md"
                        radius="md"
                        withBorder
                        style={{
                          borderLeft: `4px solid var(--mantine-color-${strategy.color}-6)`,
                          cursor: 'pointer',
                          backgroundColor: selectedForComparison.includes(strategy.value)
                            ? 'var(--mantine-color-violet-0)'
                            : undefined,
                        }}
                        onClick={() => {
                          if (selectedForComparison.includes(strategy.value)) {
                            setSelectedForComparison(selectedForComparison.filter(s => s !== strategy.value));
                          } else if (selectedForComparison.length < 2) {
                            setSelectedForComparison([...selectedForComparison, strategy.value]);
                          }
                        }}
                      >
                        <Group justify="space-between" align="center">
                          <Group gap="sm">
                            <Checkbox
                              checked={selectedForComparison.includes(strategy.value)}
                              onChange={() => { }}
                              color="violet"
                            />
                            <ThemeIcon size="sm" color={strategy.color} variant="light">
                              <IconSettings size={14} />
                            </ThemeIcon>
                            <div>
                              <Text fw={600} size="sm">
                                {strategy.label}
                              </Text>
                              <Text size="xs" c="dimmed">
                                {strategy.description}
                              </Text>
                            </div>
                          </Group>
                          {selectedStrategy === strategy.value && (
                            <Badge color="green" variant="light" size="sm">
                              Active
                            </Badge>
                          )}
                        </Group>
                      </Card>
                    ))}
                  </Stack>
                </Stack>
              ) : (
                // Comparison View - Table Format
                <Stack gap="md">
                  <Group justify="space-between" align="center">
                    <Badge color="violet" variant="light" size="lg">
                      Comparing {selectedForComparison.length} Strategies
                    </Badge>
                    <Button
                      variant="subtle"
                      color="gray"
                      size="xs"
                      leftSection={<IconX size={14} />}
                      onClick={() => setSelectedForComparison([])}
                    >
                      Clear Selection
                    </Button>
                  </Group>

                  <Paper withBorder radius="md" style={{ overflow: 'hidden' }}>
                    <Table striped highlightOnHover withTableBorder withColumnBorders>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th style={{ width: '180px', backgroundColor: 'var(--mantine-color-gray-1)' }}>
                            <Text fw={700} size="sm">Attribute</Text>
                          </Table.Th>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy) return null;

                            return (
                              <Table.Th
                                key={strategy.value}
                                style={{
                                  backgroundColor: `var(--mantine-color-${strategy.color}-0)`,
                                  borderTop: `4px solid var(--mantine-color-${strategy.color}-6)`
                                }}
                              >
                                <Stack gap="xs">
                                  <Group gap="xs" wrap="nowrap">
                                    <ThemeIcon size="sm" color={strategy.color} variant="light">
                                      <IconSettings size={14} />
                                    </ThemeIcon>
                                    <div>
                                      <Text fw={700} size="sm">{strategy.label}</Text>
                                      <Text size="xs" c="dimmed">{strategy.description}</Text>
                                    </div>
                                  </Group>
                                  {selectedStrategy === strategy.value && (
                                    <Badge color="green" variant="light" size="xs" leftSection={<IconCheck size={12} />}>
                                      Currently Active
                                    </Badge>
                                  )}
                                </Stack>
                              </Table.Th>
                            );
                          })}
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {/* Overview Row */}
                        <Table.Tr>
                          <Table.Td style={{ backgroundColor: 'var(--mantine-color-gray-0)', verticalAlign: 'top' }}>
                            <Text fw={600} size="sm">Overview</Text>
                          </Table.Td>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy) return null;

                            return (
                              <Table.Td key={strategy.value} style={{ verticalAlign: 'top' }}>
                                <Text size="sm">{strategy.details}</Text>
                              </Table.Td>
                            );
                          })}
                        </Table.Tr>

                        {/* Pros Row */}
                        <Table.Tr>
                          <Table.Td style={{ backgroundColor: 'var(--mantine-color-gray-0)', verticalAlign: 'top' }}>
                            <Text fw={600} size="sm" c="green.7">✓ Pros</Text>
                          </Table.Td>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy) return null;

                            return (
                              <Table.Td key={strategy.value} style={{ verticalAlign: 'top' }}>
                                <List size="sm" spacing={4}>
                                  {strategy.pros.map((pro, idx) => (
                                    <List.Item key={idx}>{pro}</List.Item>
                                  ))}
                                </List>
                              </Table.Td>
                            );
                          })}
                        </Table.Tr>

                        {/* Cons Row */}
                        <Table.Tr>
                          <Table.Td style={{ backgroundColor: 'var(--mantine-color-gray-0)', verticalAlign: 'top' }}>
                            <Text fw={600} size="sm" c="red.7">✗ Cons</Text>
                          </Table.Td>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy) return null;

                            return (
                              <Table.Td key={strategy.value} style={{ verticalAlign: 'top' }}>
                                <List size="sm" spacing={4}>
                                  {strategy.cons.map((con, idx) => (
                                    <List.Item key={idx}>{con}</List.Item>
                                  ))}
                                </List>
                              </Table.Td>
                            );
                          })}
                        </Table.Tr>

                        {/* Use Cases Row */}
                        <Table.Tr>
                          <Table.Td style={{ backgroundColor: 'var(--mantine-color-gray-0)', verticalAlign: 'top' }}>
                            <Text fw={600} size="sm" c="blue.7">Best For</Text>
                          </Table.Td>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy) return null;

                            return (
                              <Table.Td key={strategy.value} style={{ verticalAlign: 'top' }}>
                                <Stack gap={6}>
                                  {strategy.useCases.map((useCase, idx) => (
                                    <Badge key={idx} size="sm" variant="light" color={strategy.color}>
                                      {useCase}
                                    </Badge>
                                  ))}
                                </Stack>
                              </Table.Td>
                            );
                          })}
                        </Table.Tr>

                        {/* Example Row */}
                        <Table.Tr>
                          <Table.Td style={{ backgroundColor: 'var(--mantine-color-gray-0)', verticalAlign: 'top' }}>
                            <Text fw={600} size="sm" c="violet.7">📝 Example</Text>
                          </Table.Td>
                          {selectedForComparison.map((strategyValue) => {
                            const strategy = ENHANCEMENT_STRATEGIES.find(s => s.value === strategyValue);
                            if (!strategy || !strategy.example) return null;

                            return (
                              <Table.Td key={strategy.value} style={{ verticalAlign: 'top' }}>
                                <Stack gap="sm">
                                  <div>
                                    <Text size="xs" c="dimmed" fw={500} mb={4}>Original Query:</Text>
                                    <Text size="xs">{strategy.example.original}</Text>
                                  </div>
                                  <Divider />
                                  <div>
                                    <Text size="xs" c="dimmed" fw={500} mb={4}>Strategy Output:</Text>
                                    <Text size="xs" style={{ whiteSpace: 'pre-line' }}>{strategy.example.output}</Text>
                                  </div>
                                </Stack>
                              </Table.Td>
                            );
                          })}
                        </Table.Tr>
                      </Table.Tbody>
                    </Table>
                  </Paper>
                </Stack>
              )}
            </>
          )}

          <Divider />

          <Group justify="flex-end">
            <Button onClick={() => {
              setStrategiesInfoModalOpen(false);
              setComparisonMode(false);
              setSelectedForComparison([]);
            }}>
              Close
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}

