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
  Paper,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconBrain,
  IconCheck,
  IconFilter,
  IconInfoCircle,
  IconMessageCircle,
  IconPlus,
  IconSettings
} from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Query enhancement strategies with detailed information
const ENHANCEMENT_STRATEGIES = [
  {
    value: 'native',
    label: 'Native RAG (Recommended)',
    description: 'Traditional RAG without query enhancement',
    details: 'Your query is sent directly to the retrieval system without any modifications. Best for simple, well-formed questions and fastest performance.',
    useCases: ['Simple lookups', 'Direct questions', 'Performance-critical scenarios', 'General purpose'],
    pros: ['Fastest performance', 'Most straightforward', 'No added complexity', 'Lowest cost'],
    cons: ['May miss relevant documents', 'Limited coverage', 'Depends on exact wording'],
    color: 'blue',
    recommended: true,
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

export default function ConversationCreate() {
  const navigate = useNavigate();

  // Form state
  const [conversationName, setConversationName] = useState('');
  const [conversationDescription, setConversationDescription] = useState('');
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('native');
  const [collectionName, setCollectionName] = useState('LongTermMemory');
  const [enableReranking, setEnableReranking] = useState(true);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // API functions
  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  const createNewConversation = async () => {
    try {
      setIsCreating(true);
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

  const selectedStrategyInfo = ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy);

  return (
    <Page title="Create Conversation">
      <PageHeader
        title="Create New Conversation"
        breadcrumbs={breadcrumbs}
        actions={
          <Button
            variant="subtle"
            leftSection={<IconArrowLeft size={16} />}
            onClick={() => navigate(paths.dashboard.apps.knowledgeSearch)}
          >
            Back to Conversations
          </Button>
        }
      />

      <Grid>
        {/* Left Column - Form */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="lg">
            {/* Basic Information */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
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
                      clearable
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
                </Grid>

                <Textarea
                  label="Description (Optional)"
                  placeholder="Brief description of what this conversation is about..."
                  value={conversationDescription}
                  onChange={(e) => setConversationDescription(e.target.value)}
                  minRows={2}
                  maxRows={4}
                  description="Optional description for context"
                />
              </Stack>
            </Card>

            {/* LLM Configuration */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
                <Group gap="xs">
                  <IconBrain size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>LLM Configuration</Title>
                </Group>

                <Grid gutter="md">
                  <Grid.Col span={6}>
                    <Select
                      label="LLM Provider"
                      placeholder={providersLoading ? 'Loading providers...' : 'Select a provider (optional)'}
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
                      clearable
                      disabled={providersLoading || !providers || providers.length === 0}
                      description="Choose the LLM provider for this conversation"
                    />
                  </Grid.Col>

                  <Grid.Col span={6}>
                    <Select
                      label="Model"
                      placeholder="Select a model (optional)"
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
                      clearable
                      disabled={!selectedProviderId}
                      description="Leave empty to use provider's default model"
                    />
                  </Grid.Col>
                </Grid>

                {!selectedProviderId && (
                  <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                    No provider selected. The system will use the default provider.
                  </Alert>
                )}
              </Stack>
            </Card>

            {/* Query Enhancement Strategy */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
                <Group gap="xs">
                  <IconSettings size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Query Enhancement Strategy</Title>
                </Group>

                <Select
                  label="Enhancement Strategy"
                  placeholder="Select strategy"
                  data={ENHANCEMENT_STRATEGIES.map((s) => ({
                    value: s.value,
                    label: s.label + (s.recommended ? ' ⭐' : ''),
                  }))}
                  value={selectedStrategy}
                  onChange={(value) => setSelectedStrategy(value || 'none')}
                  description="Select how your queries will be enhanced for better retrieval"
                />
              </Stack>
            </Card>

            {/* Document Reranking Configuration */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="md">
                <Group gap="xs">
                  <IconFilter size={20} color="var(--mantine-color-blue-6)" />
                  <Title order={4}>Document Reranking</Title>
                </Group>

                <Switch
                  label="Enable Document Reranking"
                  description="Rerank retrieved documents to improve relevance. Uses LLM judging or dedicated reranker models."
                  checked={enableReranking}
                  onChange={(event) => {
                    setEnableReranking(event.currentTarget.checked);
                    if (!event.currentTarget.checked) {
                      setSelectedRerankerId(null);
                      setSelectedRerankerModel(null);
                    }
                  }}
                />

                {enableReranking && (
                  <>
                    <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                      <Text size="sm">
                        <strong>Reranking Options:</strong>
                        <br />
                        • <strong>No Reranker Selected:</strong> Uses the conversation's LLM for judging (slower but works with any provider)
                        <br />
                        • <strong>Dedicated Reranker:</strong> Uses specialized reranking models (Cohere/Voyage AI) for faster, more accurate results
                      </Text>
                    </Alert>

                    <Grid gutter="md">
                      <Grid.Col span={6}>
                        <Select
                          label="Reranker Provider (Optional)"
                          placeholder={providersLoading ? 'Loading providers...' : 'Select a reranker provider'}
                          data={providers
                            ?.filter((p) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
                            .map((p) => ({
                              value: p.id,
                              label: `${p.name} (${p.provider_type})`,
                            })) || []}
                          value={selectedRerankerId}
                          onChange={(value) => {
                            setSelectedRerankerId(value);
                            setSelectedRerankerModel(null);
                          }}
                          searchable
                          clearable
                          disabled={providersLoading || !providers}
                          description="Leave empty to use LLM for reranking"
                        />
                      </Grid.Col>

                      <Grid.Col span={6}>
                        <Select
                          label="Reranker Model"
                          placeholder="Select a model"
                          data={
                            selectedRerankerId && providers
                              ? providers
                                .find((p) => p.id === selectedRerankerId)
                                ?.reranker?.models.map((model) => ({
                                  value: model,
                                  label: model,
                                })) || []
                              : []
                          }
                          value={selectedRerankerModel}
                          onChange={setSelectedRerankerModel}
                          searchable
                          clearable
                          disabled={!selectedRerankerId}
                          description="Choose the reranker model"
                        />
                      </Grid.Col>
                    </Grid>
                  </>
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
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Stack gap="md" pos="sticky" top={20}>
            {/* Strategy Details Card */}
            {selectedStrategyInfo && (
              <Paper shadow="sm" p="lg" radius="md" withBorder>
                <Stack gap="md">
                  <Group gap="xs">
                    <Badge size="lg" color={selectedStrategyInfo.color} variant="light">
                      {selectedStrategyInfo.label}
                    </Badge>
                    {selectedStrategyInfo.recommended && (
                      <Badge size="sm" color="yellow" variant="filled">
                        Recommended
                      </Badge>
                    )}
                  </Group>

                  <Box>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>
                      Description
                    </Text>
                    <Text size="sm">{selectedStrategyInfo.description}</Text>
                  </Box>

                  <Box>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>
                      How it works
                    </Text>
                    <Text size="sm">{selectedStrategyInfo.details}</Text>
                  </Box>

                  <Box>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>
                      Best for
                    </Text>
                    <Stack gap={4}>
                      {selectedStrategyInfo.useCases.map((useCase, idx) => (
                        <Text key={idx} size="sm">
                          • {useCase}
                        </Text>
                      ))}
                    </Stack>
                  </Box>

                  <Box>
                    <Text size="xs" c="green.7" tt="uppercase" fw={600} mb={4}>
                      ✓ Pros
                    </Text>
                    <Stack gap={4}>
                      {selectedStrategyInfo.pros.map((pro, idx) => (
                        <Text key={idx} size="sm" c="green.8">
                          • {pro}
                        </Text>
                      ))}
                    </Stack>
                  </Box>

                  <Box>
                    <Text size="xs" c="orange.7" tt="uppercase" fw={600} mb={4}>
                      ⚠ Cons
                    </Text>
                    <Stack gap={4}>
                      {selectedStrategyInfo.cons.map((con, idx) => (
                        <Text key={idx} size="sm" c="orange.8">
                          • {con}
                        </Text>
                      ))}
                    </Stack>
                  </Box>
                </Stack>
              </Paper>
            )}

            {/* Quick Tips */}
            <Alert icon={<IconInfoCircle size={16} />} title="Quick Tips" color="blue">
              <Stack gap="xs">
                <Text size="sm">
                  • <strong>Query Fusion</strong> is recommended for most use cases
                </Text>
                <Text size="sm">
                  • Choose <strong>None</strong> for fastest performance
                </Text>
                <Text size="sm">
                  • Use <strong>RAG Fusion</strong> for comprehensive research
                </Text>
                <Text size="sm">
                  • Try <strong>Step-Back</strong> for learning new concepts
                </Text>
              </Stack>
            </Alert>
          </Stack>
        </Grid.Col>
      </Grid>
    </Page>
  );
}

