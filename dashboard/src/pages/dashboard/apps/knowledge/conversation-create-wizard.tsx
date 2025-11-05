/**
 * Conversation Creation Wizard
 *
 * Multi-step wizard for creating conversations with:
 * Step 0: Agent Type Selection (RAG vs Assistant)
 * Step 1: LLM Provider & Model Configuration
 * Step 2: Vector Database & Query Enhancement Settings
 * Step 3: Advanced Settings (Reranking, Judge, Generation, System Prompt)
 * Step 4: Review & Create
 */

import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { SystemPromptManager } from '@/components/system-prompt-manager';
import { ColorfulVerticalStepper } from '@/components/colorful-vertical-stepper';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
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
  Text,
  TextInput,
  Textarea,
  ThemeIcon,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconDatabase,
  IconFilter,
  IconInfoCircle,
  IconRobot,
  IconSettings,
  IconWand,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// ============================================================================
// TYPES & CONSTANTS
// ============================================================================

interface ConversationFormData {
  // Step 0
  agentType: 'rag' | 'assistant';

  // Step 1
  conversationName: string;
  conversationDescription: string;
  selectedProviderId: string | null;
  selectedModel: string | null;

  // Step 2
  selectedStrategy: string;
  collectionName: string;
  topK: number;

  // Step 3
  enableReranking: boolean;
  relevanceThreshold: number;
  selectedRerankerId: string | null;
  selectedRerankerModel: string | null;
  enableLLMGeneration: boolean;
  enableKnowledgeAssistant: boolean;

  // System Prompt
  selectedSystemPromptId?: string;
}

const ENHANCEMENT_STRATEGIES = [
  { value: 'native', label: 'Native Query', color: 'blue' },
  { value: 'multi_query', label: 'Multi-Query', color: 'cyan' },
  { value: 'hyde', label: 'HyDE', color: 'teal' },
  { value: 'decomposition', label: 'Query Decomposition', color: 'grape' },
  { value: 'augmented', label: 'Augmented Queries', color: 'lime' },
  { value: 'none', label: 'No Enhancement', color: 'gray' },
];

const STEP_CONFIGS = [
  {
    label: 'Agent Type',
    description: 'Choose conversation mode',
    icon: <IconRobot size={20} />,
    color: 'blue',
    gradientFrom: '#45c9bb',
    gradientTo: '#3bc57d',
  },
  {
    label: 'LLM Setup',
    description: 'Configure language model',
    icon: <IconSettings size={20} />,
    color: 'cyan',
    gradientFrom: '#87cbbc',
    gradientTo: '#45c9bb',
  },
  {
    label: 'Vector Database',
    description: 'Set retrieval strategy',
    icon: <IconDatabase size={20} />,
    color: 'teal',
    gradientFrom: '#45c9bb',
    gradientTo: '#bbe773',
  },
  {
    label: 'Advanced Settings',
    description: 'Fine-tune behavior',
    icon: <IconFilter size={20} />,
    color: 'grape',
    gradientFrom: '#ae89ae',
    gradientTo: '#bbe773',
  },
  {
    label: 'Review & Create',
    description: 'Confirm and submit',
    icon: <IconCheck size={20} />,
    color: 'green',
    gradientFrom: '#3bc57d',
    gradientTo: '#9dd245',
  },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function ConversationCreateWizard() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedSystemPrompt, setSelectedSystemPrompt] = useState<any>(null);

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // Form setup
  const form = useForm<ConversationFormData>({
    initialValues: {
      agentType: 'rag',
      conversationName: '',
      conversationDescription: '',
      selectedProviderId: null,
      selectedModel: null,
      selectedStrategy: 'native',
      collectionName: 'LongTermMemory',
      topK: 5,
      enableReranking: false,
      relevanceThreshold: 0.5,
      selectedRerankerId: null,
      selectedRerankerModel: null,
      enableLLMGeneration: true,
      enableKnowledgeAssistant: true,
      selectedSystemPromptId: undefined,
    },
    validate: {
      conversationName: (value) =>
        !value?.trim() ? 'Conversation name is required' : null,
      selectedProviderId: (value) =>
        !value ? 'LLM provider is required' : null,
      selectedModel: (value) =>
        !value ? 'LLM model is required' : null,
      collectionName: (value) =>
        !value ? 'Vector DB collection is required' : null,
      topK: (value) =>
        value < 5 || value > 30 ? 'Top K must be between 5 and 30' : null,
    },
  });

  // Get selected provider for model info
  const selectedProvider = providers?.find(
    (p) => p.id === form.values.selectedProviderId
  );

  // Helper functions
  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        return true; // Agent type always valid
      case 1:
        return (
          !!form.values.conversationName.trim() &&
          !!form.values.selectedProviderId &&
          !!form.values.selectedModel
        );
      case 2:
        return !!form.values.collectionName && form.values.topK >= 5;
      case 3:
        return true; // Advanced settings all optional
      case 4:
        return true; // Review always valid
      default:
        return false;
    }
  };

  const handleNextStep = () => {
    if (!validateStep(activeStep)) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please fill in required fields before proceeding',
        color: 'red',
      });
      return;
    }
    setCompletedSteps((prev) => [...new Set([...prev, activeStep])]);
    setActiveStep((prev) => prev + 1);
  };

  const handlePreviousStep = () => {
    if (activeStep > 0) {
      setActiveStep((prev) => prev - 1);
    }
  };

  const handleStepClick = (step: number) => {
    if (step < activeStep) {
      setActiveStep(step);
      return;
    }
    if (completedSteps.includes(step) && step === activeStep + 1) {
      if (validateStep(activeStep)) {
        setCompletedSteps((prev) => [...new Set([...prev, activeStep])]);
        setActiveStep(step);
      }
      return;
    }
    if (completedSteps.includes(step)) {
      setActiveStep(step);
    }
  };

  const handleCreateConversation = async () => {
    if (!validateStep(activeStep)) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please review all required fields',
        color: 'red',
      });
      return;
    }

    try {
      setIsCreating(true);
      const token = localStorage.getItem('jwt_token');

      const payload: any = {
        name: form.values.conversationName.trim(),
        description: form.values.conversationDescription.trim() || null,
        llm_provider_id: form.values.selectedProviderId,
        llm_model_name: form.values.selectedModel,
        enhancement_strategy:
          form.values.selectedStrategy !== 'none'
            ? form.values.selectedStrategy
            : null,
        collection_name: form.values.collectionName,
        top_k: form.values.topK,
        enable_reranking: form.values.enableReranking,
        relevance_threshold: form.values.relevanceThreshold,
        reranker_provider_id: form.values.enableReranking
          ? form.values.selectedRerankerId
          : null,
        reranker_model_name: form.values.enableReranking
          ? form.values.selectedRerankerModel
          : null,
        enable_llm_generation: form.values.enableLLMGeneration,
        enable_knowledge_assistant:
          form.values.agentType === 'assistant'
            ? true
            : form.values.enableKnowledgeAssistant,
        selected_system_prompt_id:
          form.values.agentType === 'assistant' &&
          form.values.selectedSystemPromptId
            ? form.values.selectedSystemPromptId
            : null,
      };

      const response = await fetch(apiUtils.buildApiUrl('/conversations'), {
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

        // If user selected a temporary prompt during creation, create it now
        if (
          form.values.selectedSystemPromptId?.startsWith('temp-') &&
          selectedSystemPrompt
        ) {
          try {
            await fetch(
              apiUtils.buildApiUrl(`/conversations/${sessionId}/system-prompts`),
              {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  name: selectedSystemPrompt.name,
                  description: selectedSystemPrompt.description || '',
                  system_prompt: selectedSystemPrompt.system_prompt,
                  tags: selectedSystemPrompt.tags || [],
                }),
              }
            );
          } catch (error) {
            console.error('Error creating system prompt:', error);
          }
        }

        notifications.show({
          title: 'Success',
          message: 'Conversation created successfully',
          color: 'green',
          icon: <IconCheck size={16} />,
        });

        navigate(paths.dashboard.apps.conversation(sessionId));
      } else {
        const errorData = await response.json().catch(() => ({}));
        notifications.show({
          title: 'Error',
          message: errorData.detail || 'Failed to create conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error creating conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'An error occurred while creating the conversation',
        color: 'red',
      });
    } finally {
      setIsCreating(false);
    }
  };

  // ========================================================================
  // RENDER
  // ========================================================================

  return (
    <Page title="Create New Conversation">
      <PageHeader title="Create New Conversation" />

      <ColorfulVerticalStepper
        activeStep={activeStep}
        completedSteps={completedSteps}
        steps={STEP_CONFIGS}
        onStepClick={handleStepClick}
      >
        {/* STEP 0: AGENT TYPE SELECTION */}
        {activeStep === 0 && <StepAgentType form={form} />}

        {/* STEP 1: LLM CONFIGURATION */}
        {activeStep === 1 && (
          <StepLLMConfiguration
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 2: VECTOR DATABASE & QUERY ENHANCEMENT */}
        {activeStep === 2 && (
          <StepVectorDatabase
            form={form}
            collections={collections}
            collectionsLoading={collectionsLoading}
          />
        )}

        {/* STEP 3: ADVANCED SETTINGS */}
        {activeStep === 3 && (
          <StepAdvancedSettings
            form={form}
            providers={providers}
            providersLoading={providersLoading}
            onPromptSelected={(prompt) => {
              form.setFieldValue('selectedSystemPromptId', prompt.id);
              setSelectedSystemPrompt(prompt);
            }}
            selectedSystemPrompt={selectedSystemPrompt}
          />
        )}

        {/* STEP 4: REVIEW & CREATE */}
        {activeStep === 4 && (
          <StepReviewAndCreate
            form={form}
            providers={providers}
            collections={collections}
          />
        )}

        {/* NAVIGATION BUTTONS */}
        <Group justify="space-between" mt="xl">
          <Button
            variant="subtle"
            onClick={handlePreviousStep}
            disabled={activeStep === 0 || isCreating}
            leftSection={<IconArrowLeft size={16} />}
          >
            Previous
          </Button>

          <Group gap="xs">
            <Button
              variant="subtle"
              color="gray"
              onClick={() => navigate(paths.dashboard.apps.knowledgeSearch)}
              disabled={isCreating}
            >
              Cancel
            </Button>

            {activeStep < 4 ? (
              <Button
                onClick={handleNextStep}
                disabled={isCreating}
                color="blue"
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleCreateConversation}
                loading={isCreating}
                leftSection={<IconCheck size={16} />}
                color="green"
              >
                Create Conversation
              </Button>
            )}
          </Group>
        </Group>
      </ColorfulVerticalStepper>
    </Page>
  );
}

// ============================================================================
// STEP COMPONENTS
// ============================================================================

interface StepProps {
  form: ReturnType<typeof useForm<ConversationFormData>>;
  providers?: any[];
  providersLoading?: boolean;
  collections?: any[];
  collectionsLoading?: boolean;
  onPromptSelected?: (prompt: any) => void;
  selectedSystemPrompt?: any;
}

function StepAgentType({ form }: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Choose how you want to use this conversation. <strong>RAG Mode</strong> searches your knowledge base.
          <strong>Assistant Mode</strong> performs tasks using knowledge base information.
        </Text>
      </Alert>

      <Grid>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card
            p="lg"
            withBorder
            style={{
              cursor: 'pointer',
              border:
                form.values.agentType === 'rag'
                  ? '2px solid var(--mantine-color-blue-6)'
                  : '1px solid var(--mantine-color-gray-3)',
              backgroundColor:
                form.values.agentType === 'rag'
                  ? 'var(--mantine-color-blue-0)'
                  : undefined,
            }}
            onClick={() => form.setFieldValue('agentType', 'rag')}
          >
            <Group gap="sm" mb="md">
              <ThemeIcon size="lg" variant="light" color="blue" radius="md">
                <IconDatabase size={20} />
              </ThemeIcon>
              <div>
                <Text fw={600} size="md">
                  RAG Mode
                </Text>
              </div>
              {form.values.agentType === 'rag' && (
                <Badge ml="auto" size="lg" color="blue">
                  Selected
                </Badge>
              )}
            </Group>
            <Text size="sm" c="dimmed">
              Search and retrieve information from your knowledge base. Best for Q&A and information lookup.
            </Text>
            <List size="sm" mt="md" withPadding>
              <List.Item>Search knowledge base with queries</List.Item>
              <List.Item>Retrieve relevant documents</List.Item>
              <List.Item>Generate answers from results</List.Item>
              <List.Item>High accuracy, factual responses</List.Item>
            </List>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card
            p="lg"
            withBorder
            style={{
              cursor: 'pointer',
              border:
                form.values.agentType === 'assistant'
                  ? '2px solid var(--mantine-color-grape-6)'
                  : '1px solid var(--mantine-color-gray-3)',
              backgroundColor:
                form.values.agentType === 'assistant'
                  ? 'var(--mantine-color-grape-0)'
                  : undefined,
            }}
            onClick={() => form.setFieldValue('agentType', 'assistant')}
          >
            <Group gap="sm" mb="md">
              <ThemeIcon size="lg" variant="light" color="grape" radius="md">
                <IconRobot size={20} />
              </ThemeIcon>
              <div>
                <Text fw={600} size="md">
                  Assistant Mode
                </Text>
              </div>
              {form.values.agentType === 'assistant' && (
                <Badge ml="auto" size="lg" color="grape">
                  Selected
                </Badge>
              )}
            </Group>
            <Text size="sm" c="dimmed">
              Perform tasks (writing, coding, analysis) using knowledge base as context.
            </Text>
            <List size="sm" mt="md" withPadding>
              <List.Item>Execute complex tasks</List.Item>
              <List.Item>Use custom system prompts</List.Item>
              <List.Item>Create/write content</List.Item>
              <List.Item>Generate code or documentation</List.Item>
            </List>
          </Card>
        </Grid.Col>
      </Grid>

      {form.values.agentType === 'assistant' && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          color="yellow"
          variant="light"
        >
          <Text size="sm">
            Assistant Mode requires a system prompt. You can create or customize one in the Advanced Settings step.
          </Text>
        </Alert>
      )}
    </Stack>
  );
}

function StepLLMConfiguration({
  form,
  providers,
  providersLoading,
}: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Select the language model that will power your conversation. This model will be used for understanding queries and generating responses.
        </Text>
      </Alert>

      <TextInput
        label="Conversation Name"
        placeholder="e.g., Customer Support Bot"
        {...form.getInputProps('conversationName')}
        required
      />

      <Textarea
        label="Description (Optional)"
        placeholder="Brief description of what this conversation is for..."
        {...form.getInputProps('conversationDescription')}
        rows={3}
      />

      <Divider my="sm" />

      <Select
        label="LLM Provider"
        placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
        data={
          providers?.map((p) => ({
            value: p.id,
            label: `${p.name} (${p.provider_type})`,
          })) || []
        }
        {...form.getInputProps('selectedProviderId')}
        searchable
        disabled={providersLoading}
        required
      />

      {form.values.selectedProviderId && providers ? (
        <Select
          label="Model"
          placeholder="Select a model"
          data={
            providers
              .find((p) => p.id === form.values.selectedProviderId)
              ?.generative?.models.map((m: string) => ({
                value: m,
                label: m,
              })) || []
          }
          {...form.getInputProps('selectedModel')}
          searchable
          required
        />
      ) : (
        <Select label="Model" placeholder="Select provider first" disabled />
      )}
    </Stack>
  );
}

function StepVectorDatabase({ form, collections, collectionsLoading }: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Configure how the system retrieves information from your knowledge base. Query enhancement strategies help find more relevant documents.
        </Text>
      </Alert>

      <Select
        label="Enhancement Strategy"
        placeholder="Select strategy"
        data={ENHANCEMENT_STRATEGIES.map((s) => ({
          value: s.value,
          label: s.label,
        }))}
        {...form.getInputProps('selectedStrategy')}
        description="How to enhance queries for better retrieval"
      />

      {form.values.selectedStrategy !== 'native' &&
        form.values.selectedStrategy !== 'none' && (
          <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
            <Text size="sm">
              <strong>Multi-Variant Retrieval:</strong> This strategy generates multiple query variations, searches the knowledge base with each, and merges results using Reciprocal Rank Fusion (RRF).
            </Text>
          </Alert>
        )}

      <Select
        label="Vector DB Collection"
        placeholder={
          collectionsLoading ? 'Loading collections...' : 'Select a collection'
        }
        data={
          collections?.map((c) => ({
            value: c.name,
            label: `${c.name} (${c.record_count.toLocaleString()} records)`,
          })) || []
        }
        {...form.getInputProps('collectionName')}
        searchable
        disabled={collectionsLoading}
        required
      />

      <NumberInput
        label="Search Results Limit (Top K)"
        placeholder="Number of documents to retrieve"
        {...form.getInputProps('topK')}
        min={5}
        max={30}
        required
        description="How many relevant documents to retrieve (5-30)"
      />
    </Stack>
  );
}

function StepAdvancedSettings({
  form,
  providers,
  providersLoading,
  onPromptSelected,
  selectedSystemPrompt,
}: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Fine-tune advanced behavior including document ranking, answer generation, and system prompts for Assistant mode.
        </Text>
      </Alert>

      <Divider label="Document Ranking" labelPosition="left" />

      <Switch
        label="Enable Judge Ranker"
        description="Evaluate and rank retrieved documents by relevance"
        {...form.getInputProps('enableReranking', {
          type: 'checkbox',
        })}
      />

      {form.values.enableReranking && (
        <>
          <Grid gutter="md">
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select
                label="Judge Provider"
                placeholder="Select a provider"
                data={
                  providers?.map((p) => ({
                    value: p.id,
                    label: p.name,
                  })) || []
                }
                {...form.getInputProps('selectedRerankerId')}
                searchable
                disabled={providersLoading}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select
                label="Judge Model"
                placeholder="Select a model"
                data={
                  form.values.selectedRerankerId && providers
                    ? providers
                        .find((p) => p.id === form.values.selectedRerankerId)
                        ?.reranker?.models.map((m: string) => ({
                          value: m,
                          label: m,
                        })) || []
                    : []
                }
                {...form.getInputProps('selectedRerankerModel')}
                searchable
              />
            </Grid.Col>
          </Grid>

          <NumberInput
            label="Relevance Threshold"
            min={0}
            max={1}
            step={0.05}
            {...form.getInputProps('relevanceThreshold')}
            description="Minimum relevance score (0-1) for filtering documents"
          />
        </>
      )}

      <Divider label="Answer Generation" labelPosition="left" />

      <Switch
        label="Enable Generative Answer"
        description="Generate natural language answers using LLM"
        {...form.getInputProps('enableLLMGeneration', {
          type: 'checkbox',
        })}
      />

      {form.values.enableLLMGeneration ? (
        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          <Text size="sm">
            AI will generate natural language answers based on retrieved documents. Uses tokens but provides polished responses.
          </Text>
        </Alert>
      ) : (
        <Alert icon={<IconInfoCircle size={16} />} color="yellow" variant="light">
          <Text size="sm">
            Raw results mode. Shows retrieved documents as-is without LLM processing. Faster and more cost-effective.
          </Text>
        </Alert>
      )}

      {form.values.agentType === 'assistant' && (
        <>
          <Divider label="System Prompt" labelPosition="left" />

          <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light">
            <Text size="sm">
              Define how the assistant should behave when performing tasks. You can create custom prompts or use built-in templates.
            </Text>
          </Alert>

          <SystemPromptManager
            conversationId=""
            selectedPromptId={form.values.selectedSystemPromptId}
            selectedPromptData={selectedSystemPrompt}
            onPromptSelected={(prompt) => {
              form.setFieldValue('selectedSystemPromptId', prompt.id);
              onPromptSelected?.(prompt);
            }}
          />
        </>
      )}
    </Stack>
  );
}

function StepReviewAndCreate({ form, providers, collections }: StepProps) {
  const selectedProvider = providers?.find(
    (p) => p.id === form.values.selectedProviderId
  );
  const selectedCollection = collections?.find(
    (c) => c.name === form.values.collectionName
  );

  return (
    <Stack gap="md">
      <Alert icon={<IconCheck size={16} />} color="green" variant="light">
        <Text size="sm">
          Review your configuration below. Click <strong>Create Conversation</strong> to proceed.
        </Text>
      </Alert>

      <Card withBorder p="md" bg="blue.0">
        <Stack gap="xs">
          <Group justify="space-between">
            <Text fw={600}>Agent Type</Text>
            <Badge size="lg" color={form.values.agentType === 'rag' ? 'blue' : 'grape'}>
              {form.values.agentType === 'rag' ? 'RAG Mode' : 'Assistant Mode'}
            </Badge>
          </Group>
        </Stack>
      </Card>

      <Card withBorder p="md">
        <Stack gap="sm">
          <Text fw={600} size="lg">
            {form.values.conversationName}
          </Text>
          {form.values.conversationDescription && (
            <Text size="sm" c="dimmed">
              {form.values.conversationDescription}
            </Text>
          )}
        </Stack>
      </Card>

      <Grid>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card withBorder p="md">
            <Stack gap="xs">
              <Text fw={600} size="sm">
                LLM Configuration
              </Text>
              <Text size="xs" c="dimmed">
                Provider: {selectedProvider?.name || 'Not selected'}
              </Text>
              <Text size="xs" c="dimmed">
                Model: {form.values.selectedModel || 'Not selected'}
              </Text>
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card withBorder p="md">
            <Stack gap="xs">
              <Text fw={600} size="sm">
                Vector Database
              </Text>
              <Text size="xs" c="dimmed">
                Collection: {selectedCollection?.name || form.values.collectionName}
              </Text>
              <Text size="xs" c="dimmed">
                Records: {selectedCollection?.record_count.toLocaleString() || 'Unknown'}
              </Text>
              <Text size="xs" c="dimmed">
                Top K: {form.values.topK}
              </Text>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>

      <Card withBorder p="md">
        <Stack gap="xs">
          <Text fw={600} size="sm">
            Enhancement Strategy
          </Text>
          <Badge>
            {ENHANCEMENT_STRATEGIES.find((s) => s.value === form.values.selectedStrategy)?.label}
          </Badge>
        </Stack>
      </Card>

      {form.values.enableReranking && (
        <Card withBorder p="md" bg="yellow.0">
          <Stack gap="xs">
            <Text fw={600} size="sm">
              Judge Ranker Enabled
            </Text>
            <Text size="xs" c="dimmed">
              Relevance Threshold: {form.values.relevanceThreshold}
            </Text>
          </Stack>
        </Card>
      )}

      <Card withBorder p="md">
        <Stack gap="xs">
          <Text fw={600} size="sm">
            Answer Generation
          </Text>
          <Badge color={form.values.enableLLMGeneration ? 'green' : 'gray'}>
            {form.values.enableLLMGeneration ? 'Enabled' : 'Disabled'}
          </Badge>
        </Stack>
      </Card>
    </Stack>
  );
}

export default ConversationCreateWizard;
