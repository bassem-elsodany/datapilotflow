/**
 * Conversation Creation Wizard
 *
 * Multi-step wizard for creating conversations with:
 * Step 0: Agent Type Selection (RAG vs Assistant)
 * Step 1: Conversation Settings (Name, Description)
 * Step 2: Vector Database Selection
 * Step 3: Enhancement Strategy (Query enhancement options)
 * Step 4: Advanced Settings (Reranking, LLM, System Prompt)
 * Step 5: Review & Create
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
  TextInput,
  Textarea,
  ThemeIcon,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconArrowsLeftRight,
  IconCheck,
  IconDatabase,
  IconFilter,
  IconHelp,
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
    description: 'Systematic transformations for maximum coverage',
    details: 'Applies 4 specific transformation techniques to your query: (1) Synonym Expansion, (2) Query Expansion (add implicit concepts), (3) Query Contraction (focus on core), (4) Technical Reformulation. Each variant explores a different semantic space (broad/narrow/technical/simple). Preserves original query. Uses RRF to merge all variants.',
    useCases: ['Maximum coverage needed', 'Comprehensive search', 'Documents use varied styles', 'Critical queries'],
    pros: ['Systematic coverage', 'Fills retrieval gaps', 'Explores all angles', 'Context preserved'],
    cons: ['Slightly slower than Native', 'Uses more tokens', 'May be overkill for simple queries'],
    color: 'green',
  },
  {
    value: 'multi_query',
    label: 'Multi-Query',
    description: 'Rephrase the same question in different ways',
    details: 'Generates 3-5 alternative phrasings of the SAME question using different vocabulary and wording. Targets different document types (tutorials, guides, API docs) and expertise levels (beginner vs expert). All variants express the same intent. Uses RRF to merge results from all phrasings.',
    useCases: ['Documents use varied terminology', 'Unknown exact terms', 'Vocabulary mismatches', 'Different doc styles'],
    pros: ['Linguistic flexibility', 'Handles synonyms', 'Matches varied writing styles', 'Simple approach'],
    cons: ['Same semantic space', 'May miss edge cases', 'Not as systematic as Augmented'],
    color: 'cyan',
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
    details: 'Splits your complex question into simpler sub-questions. Each sub-question is processed separately for comprehensive coverage. Uses RRF to merge results from all sub-queries.',
    useCases: ['Complex multi-part questions', 'Research tasks', 'Thorough analysis needed'],
    pros: ['Handles complexity', 'RRF merges sub-queries', 'Comprehensive results', 'Systematic approach'],
    cons: ['Slowest option', 'Most expensive', 'May over-complicate simple queries'],
    color: 'violet',
  },
];

// Logo color palette from DataPilotFlow branding
const LOGO_COLORS = {
  data: '#45c9bb',        // Teal (Data)
  pilot: '#ae89ae',       // Purple (Pilot)
  flow: '#bbe773',        // Lime Green (Flow)
  accent1: '#87cbbc',     // Soft Teal
  accent2: '#3bc57d',     // Vibrant Green
  accent3: '#9dd245',     // Yellow-Green
  accent4: '#ddde65',     // Yellow
  gray: '#8d949d',        // Cool Gray
};

const STEP_CONFIGS = [
  {
    label: 'Agent Type',
    description: 'Choose conversation mode',
    icon: <IconRobot size={20} />,
    color: 'blue',
    gradientFrom: LOGO_COLORS.data,        // Teal (Data)
    gradientTo: LOGO_COLORS.accent2,       // Vibrant Green
  },
  {
    label: 'Conversation Settings',
    description: 'Basic conversation info',
    icon: <IconSettings size={20} />,
    color: 'cyan',
    gradientFrom: LOGO_COLORS.accent1,     // Soft Teal
    gradientTo: LOGO_COLORS.data,          // Teal (Data)
  },
  {
    label: 'Enhancement Strategy',
    description: 'Query enhancement options',
    icon: <IconWand size={20} />,
    color: 'grape',
    gradientFrom: LOGO_COLORS.pilot,       // Purple (Pilot)
    gradientTo: LOGO_COLORS.flow,          // Lime Green (Flow)
  },
  {
    label: 'Vector Database',
    description: 'Select collection',
    icon: <IconDatabase size={20} />,
    color: 'teal',
    gradientFrom: LOGO_COLORS.data,        // Teal (Data)
    gradientTo: LOGO_COLORS.flow,          // Lime Green (Flow)
  },
  {
    label: 'Advanced Settings',
    description: 'Fine-tune behavior',
    icon: <IconFilter size={20} />,
    color: 'violet',
    gradientFrom: LOGO_COLORS.pilot,       // Purple (Pilot)
    gradientTo: LOGO_COLORS.accent3,       // Yellow-Green
  },
  {
    label: 'Review & Create',
    description: 'Confirm and submit',
    icon: <IconCheck size={20} />,
    color: 'green',
    gradientFrom: LOGO_COLORS.accent2,     // Vibrant Green
    gradientTo: LOGO_COLORS.accent3,       // Yellow-Green
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
  const [strategiesInfoModalOpen, setStrategiesInfoModalOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

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
        return !!form.values.conversationName.trim(); // Conversation name required
      case 2:
        return !!form.values.collectionName && form.values.topK >= 5; // Collection & topK required
      case 3:
        return true; // Enhancement strategy always valid
      case 4:
        // Provider & model required only if generative answer enabled
        if (form.values.enableLLMGeneration) {
          return !!form.values.selectedProviderId && !!form.values.selectedModel;
        }
        return true; // All optional if generative answer disabled
      case 5:
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

        {/* STEP 1: CONVERSATION SETTINGS */}
        {activeStep === 1 && (
          <StepConversationSettings
            form={form}
          />
        )}

        {/* STEP 2: ENHANCEMENT STRATEGY */}
        {activeStep === 2 && (
          <StepEnhancementStrategy
            form={form}
            onLearnClick={() => setStrategiesInfoModalOpen(true)}
          />
        )}

        {/* STEP 3: VECTOR DATABASE */}
        {activeStep === 3 && (
          <StepVectorDatabase
            form={form}
            collections={collections}
            collectionsLoading={collectionsLoading}
          />
        )}

        {/* STEP 4: ADVANCED SETTINGS */}
        {activeStep === 4 && (
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

        {/* STEP 5: REVIEW & CREATE */}
        {activeStep === 5 && (
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

            {activeStep < 5 ? (
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

      {/* LEARN & COMPARE MODAL */}
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
            <Accordion variant="separated">
              {ENHANCEMENT_STRATEGIES.map((strategy) => (
                <Accordion.Item key={strategy.value} value={strategy.value}>
                  <Accordion.Control>
                    <Group gap="sm">
                      <Badge color={strategy.color}>{strategy.label}</Badge>
                      <Text size="sm" c="dimmed">{strategy.description}</Text>
                    </Group>
                  </Accordion.Control>
                  <Accordion.Panel>
                    <Stack gap="md">
                      <div>
                        <Text fw={600} size="sm" mb="xs">Details</Text>
                        <Text size="sm">{strategy.details}</Text>
                      </div>

                      <div>
                        <Text fw={600} size="sm" mb="xs">Use Cases</Text>
                        <List size="sm">
                          {strategy.useCases.map((useCase) => (
                            <List.Item key={useCase}>{useCase}</List.Item>
                          ))}
                        </List>
                      </div>

                      <Grid>
                        <Grid.Col span={{ base: 12, sm: 6 }}>
                          <div>
                            <Text fw={600} size="sm" mb="xs" c="green">Pros</Text>
                            <List size="sm">
                              {strategy.pros.map((pro) => (
                                <List.Item key={pro}>{pro}</List.Item>
                              ))}
                            </List>
                          </div>
                        </Grid.Col>
                        <Grid.Col span={{ base: 12, sm: 6 }}>
                          <div>
                            <Text fw={600} size="sm" mb="xs" c="red">Cons</Text>
                            <List size="sm">
                              {strategy.cons.map((con) => (
                                <List.Item key={con}>{con}</List.Item>
                              ))}
                            </List>
                          </div>
                        </Grid.Col>
                      </Grid>

                      <Button
                        size="xs"
                        variant="light"
                        onClick={() => {
                          form.setFieldValue('selectedStrategy', strategy.value);
                          setStrategiesInfoModalOpen(false);
                        }}
                      >
                        Select This Strategy
                      </Button>
                    </Stack>
                  </Accordion.Panel>
                </Accordion.Item>
              ))}
            </Accordion>
          ) : (
            // Comparison Mode
            <Stack gap="md">
              {selectedForComparison.length < 2 && (
                <Text size="sm" c="dimmed">
                  {selectedForComparison.length === 0
                    ? 'Select two strategies to compare'
                    : 'Select one more strategy'}
                </Text>
              )}
              <Group gap="sm" wrap="wrap">
                {ENHANCEMENT_STRATEGIES.map((strategy) => (
                  <Button
                    key={strategy.value}
                    variant={selectedForComparison.includes(strategy.value) ? 'filled' : 'light'}
                    color={selectedForComparison.includes(strategy.value) ? 'blue' : 'gray'}
                    size="sm"
                    disabled={selectedForComparison.length === 2 && !selectedForComparison.includes(strategy.value)}
                    onClick={() => {
                      setSelectedForComparison((prev) =>
                        prev.includes(strategy.value)
                          ? prev.filter((v) => v !== strategy.value)
                          : [...prev, strategy.value]
                      );
                    }}
                  >
                    {strategy.label}
                  </Button>
                ))}
              </Group>

              {selectedForComparison.length === 2 && (
                <Table striped>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Aspect</Table.Th>
                      <Table.Th>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[0])?.label}</Table.Th>
                      <Table.Th>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[1])?.label}</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={600}>Description</Table.Td>
                      <Table.Td>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[0])?.description}</Table.Td>
                      <Table.Td>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[1])?.description}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Details</Table.Td>
                      <Table.Td>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[0])?.details}</Table.Td>
                      <Table.Td>{ENHANCEMENT_STRATEGIES.find((s) => s.value === selectedForComparison[1])?.details}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Performance</Table.Td>
                      <Table.Td>{selectedForComparison[0] === 'native' ? 'Fastest' : selectedForComparison[0] === 'decomposition' ? 'Slowest' : 'Moderate'}</Table.Td>
                      <Table.Td>{selectedForComparison[1] === 'native' ? 'Fastest' : selectedForComparison[1] === 'decomposition' ? 'Slowest' : 'Moderate'}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              )}
            </Stack>
          )}
        </Stack>
      </Modal>
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
                  ? `2px solid ${LOGO_COLORS.data}`
                  : '1px solid var(--mantine-color-gray-3)',
              backgroundColor:
                form.values.agentType === 'rag'
                  ? `${LOGO_COLORS.data}15`
                  : undefined,
            }}
            onClick={() => form.setFieldValue('agentType', 'rag')}
          >
            <Group gap="sm" mb="md">
              <ThemeIcon size="lg" variant="light" radius="md" style={{ backgroundColor: `${LOGO_COLORS.data}20`, color: LOGO_COLORS.data }}>
                <IconDatabase size={20} />
              </ThemeIcon>
              <div>
                <Text fw={600} size="md" style={{ color: LOGO_COLORS.data }}>
                  RAG Mode
                </Text>
              </div>
              {form.values.agentType === 'rag' && (
                <Badge ml="auto" size="lg" style={{ backgroundColor: LOGO_COLORS.data, color: 'white' }}>
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
                  ? `2px solid ${LOGO_COLORS.pilot}`
                  : '1px solid var(--mantine-color-gray-3)',
              backgroundColor:
                form.values.agentType === 'assistant'
                  ? `${LOGO_COLORS.pilot}15`
                  : undefined,
            }}
            onClick={() => form.setFieldValue('agentType', 'assistant')}
          >
            <Group gap="sm" mb="md">
              <ThemeIcon size="lg" variant="light" radius="md" style={{ backgroundColor: `${LOGO_COLORS.pilot}20`, color: LOGO_COLORS.pilot }}>
                <IconRobot size={20} />
              </ThemeIcon>
              <div>
                <Text fw={600} size="md" style={{ color: LOGO_COLORS.pilot }}>
                  Assistant Mode
                </Text>
              </div>
              {form.values.agentType === 'assistant' && (
                <Badge ml="auto" size="lg" style={{ backgroundColor: LOGO_COLORS.pilot, color: 'white' }}>
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

function StepConversationSettings({
  form,
}: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Set up basic information about your conversation. These details help you organize and identify different conversations.
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
        rows={4}
      />
    </Stack>
  );
}

function StepVectorDatabase({ form, collections, collectionsLoading }: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Select the knowledge base collection you want to search from. Configure how many relevant documents to retrieve.
        </Text>
      </Alert>

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

function StepEnhancementStrategy({ form, onLearnClick }: StepProps & { onLearnClick: () => void }) {
  const selectedStrategyInfo = ENHANCEMENT_STRATEGIES.find((s) => s.value === form.values.selectedStrategy);

  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Choose how your queries will be enhanced before searching the knowledge base. Different strategies work better for different types of questions.
        </Text>
      </Alert>

      <Group justify="space-between" align="flex-end">
        <div style={{ flex: 1 }}>
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
        </div>
        <Button
          size="xs"
          variant="gradient"
          gradient={{ from: 'violet', to: 'purple', deg: 135 }}
          leftSection={<IconHelp size={16} />}
          onClick={onLearnClick}
          style={{
            boxShadow: '0 2px 8px rgba(109, 40, 217, 0.3)',
          }}
        >
          Learn & Compare
        </Button>
      </Group>

      {selectedStrategyInfo && (
        <Card withBorder p="md" bg="gray.0">
          <Stack gap="sm">
            <div>
              <Text fw={600} size="sm" mb="xs">
                {selectedStrategyInfo.label}
              </Text>
              <Text size="sm" c="dimmed">
                {selectedStrategyInfo.description}
              </Text>
            </div>

            <Grid gutter="md">
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <Text fw={600} size="xs" c="green">
                    Pros
                  </Text>
                  <List size="xs">
                    {selectedStrategyInfo.pros.map((pro) => (
                      <List.Item key={pro}>{pro}</List.Item>
                    ))}
                  </List>
                </Stack>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <Text fw={600} size="xs" c="red">
                    Cons
                  </Text>
                  <List size="xs">
                    {selectedStrategyInfo.cons.map((con) => (
                      <List.Item key={con}>{con}</List.Item>
                    ))}
                  </List>
                </Stack>
              </Grid.Col>
            </Grid>
          </Stack>
        </Card>
      )}
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
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
            <Text size="sm">
              AI will generate natural language answers based on retrieved documents. Uses tokens but provides polished responses.
            </Text>
          </Alert>

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
        </>
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
