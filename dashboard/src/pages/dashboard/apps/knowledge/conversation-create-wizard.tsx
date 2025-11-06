/**
 * Conversation Creation Wizard
 *
 * Multi-step wizard for creating conversations with:
 * Step 0: Agent Type Selection (RAG vs Assistant)
 * Step 1: Conversation Settings (Name, Description)
 * Step 2: Enhancement Strategy (Query enhancement options - requires LLM provider if non-native strategy selected)
 * Step 3: Vector Database Selection
 * Step 4: Judge Ranker (Document ranking - optional)
 * Step 5: Generative Answer (LLM configuration, System Prompt)
 * Step 6: Review & Create
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
  IconMessageCircle,
  IconRobot,
  IconScale,
  IconSettings,
  IconWand,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

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

  // Step 6 - System Prompt (Assistant mode only)
  systemPromptTitle: string;
  systemPromptContent: string;
  selectedSystemPromptId: string | null;
  systemPromptTasks: any[];
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
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Searches directly with: "How to configure SSL certificates in Apache?"'
    },
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
    example: {
      original: 'SSL configuration in production',
      output: 'Transforms systematically:\n1. Original: "SSL configuration in production"\n2. Synonym: "secure socket layer setup in production environment"\n3. Expanded: "SSL certificate configuration HTTPS production deployment"\n4. Contracted: "SSL production config"\n5. Technical: "TLS security settings live environment"'
    },
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
    example: {
      original: 'Salesforce platform event listener config',
      output: 'Rephrases in different ways:\n1. "How to configure Salesforce platform event listeners?"\n2. "Salesforce platform event subscription setup"\n3. "Setting up Salesforce platform event handlers"\n4. "Salesforce platform event listener configuration guide"\n5. "Steps to configure Salesforce event listeners"'
    },
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
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Generates hypothetical answer:\n"To configure SSL in Apache, first install mod_ssl, then create a VirtualHost with SSLEngine on, SSLCertificateFile pointing to your cert, and SSLCertificateKeyFile for the private key. Restart Apache to apply changes."\n\nThen searches for documents similar to this answer.'
    },
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
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Breaks down into sub-questions:\n1. "What are the prerequisites for SSL in Apache?"\n2. "How to generate or obtain SSL certificates?"\n3. "What are the Apache SSL configuration directives?"\n4. "How to test and verify SSL configuration?"'
    },
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
    color: 'violet',
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
    label: 'Judge Ranker',
    description: 'Document ranking (optional)',
    icon: <IconScale size={20} />,
    color: 'orange',
    gradientFrom: '#f97316',                // Orange
    gradientTo: '#ea580c',                  // Dark Orange
  },
  {
    label: 'Generative Answer',
    description: 'Answer generation mode',
    icon: <IconWand size={20} />,
    color: 'violet',
    gradientFrom: LOGO_COLORS.pilot,       // Purple (Pilot)
    gradientTo: LOGO_COLORS.accent3,       // Yellow-Green
  },
  {
    label: 'System Prompt',
    description: 'Define task engine behavior',
    icon: <IconMessageCircle size={20} />,
    color: 'grape',
    gradientFrom: '#a855f7',               // Purple
    gradientTo: LOGO_COLORS.pilot,         // Purple (Pilot)
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
  const location = useLocation();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedSystemPrompt, setSelectedSystemPrompt] = useState<any>(null);
  const [strategiesInfoModalOpen, setStrategiesInfoModalOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [isLoadingExisting, setIsLoadingExisting] = useState(false);

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
      collectionName: '',  // Empty - user must select a collection
      topK: 5,
      enableReranking: false,
      relevanceThreshold: 0.5,
      selectedRerankerId: null,
      selectedRerankerModel: null,
      enableLLMGeneration: true,
      enableKnowledgeAssistant: false, // RAG mode (default) - false, switched to true when Assistant selected
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

  // Detect edit mode and load existing conversation
  useEffect(() => {
    const state = location.state as { editingConversationId?: string } | null;
    if (state?.editingConversationId) {
      setIsEditMode(true);
      setEditingConversationId(state.editingConversationId);
      loadExistingConversation(state.editingConversationId);
    }
  }, []);

  // Load existing conversation data for edit mode
  const loadExistingConversation = async (conversationId: string) => {
    try {
      setIsLoadingExisting(true);
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(apiUtils.buildApiUrl(`/conversations/${conversationId}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const session = data.session;

        // Populate form with existing conversation data
        form.setValues({
          agentType: session.assistant_config?.enabled ? 'assistant' : 'rag',
          conversationName: session.name || '',
          conversationDescription: session.description || '',
          selectedProviderId: session.answer_generation?.provider?.id || null,
          selectedModel: session.answer_generation?.provider?.model_name || null,
          selectedStrategy: session.enhancement?.strategy || 'native',
          collectionName: session.vector_database?.collection_name || '',
          topK: session.vector_database?.top_k || 5,
          enableReranking: session.reranker?.enabled || false,
          relevanceThreshold: session.reranker?.relevance_threshold || 0.5,
          selectedRerankerId: session.reranker?.provider?.id || null,
          selectedRerankerModel: session.reranker?.provider?.model_name || null,
          enableLLMGeneration: session.answer_generation?.enabled || false,
          enableKnowledgeAssistant: session.assistant_config?.enabled || false,
          selectedSystemPromptId: session.assistant_config?.system_prompt_tasks?.[0]?.id || null,
          systemPromptTasks: session.assistant_config?.system_prompt_tasks || [],
        });

        // Set selected system prompt for display
        if (session.assistant_config?.system_prompt_tasks?.[0]) {
          setSelectedSystemPrompt({
            id: session.assistant_config.system_prompt_tasks[0].id,
            title: session.assistant_config.system_prompt_tasks[0].title,
            content: session.assistant_config.system_prompt_tasks[0].content,
            is_active: session.assistant_config.system_prompt_tasks[0].is_active,
          });
        }
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to load conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to load conversation',
        color: 'red',
      });
    } finally {
      setIsLoadingExisting(false);
    }
  };

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
        // If non-native enhancement strategy is selected, LLM provider & model are required for generating variants
        if (form.values.selectedStrategy !== 'native') {
          return !!form.values.selectedProviderId && !!form.values.selectedModel;
        }
        return true; // Native strategy doesn't need LLM provider
      case 3:
        return !!form.values.collectionName && form.values.topK >= 5; // Collection & topK required
      case 4:
        return true; // Reranker all optional
      case 5:
        // Provider & model required only if generative answer enabled
        if (form.values.enableLLMGeneration) {
          return !!form.values.selectedProviderId && !!form.values.selectedModel;
        }
        return true; // All optional if generative answer disabled
      case 6:
        // System Prompt step - only for Assistant mode, always valid
        if (form.values.agentType === 'assistant') {
          return true; // System prompt configuration always valid (optional to select)
        }
        return true; // Not a real step for RAG mode
      case 7:
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

    // Skip Step 6 (System Prompt) for RAG mode
    let nextStep = activeStep + 1;
    if (activeStep === 5 && form.values.agentType === 'rag') {
      nextStep = 7; // Skip to Review & Create for RAG mode
    }

    setActiveStep(nextStep);
  };

  const handlePreviousStep = () => {
    if (activeStep > 0) {
      let prevStep = activeStep - 1;
      // Skip Step 6 (System Prompt) when going back in RAG mode
      if (activeStep === 7 && form.values.agentType === 'rag') {
        prevStep = 5; // Skip from Review & Create back to Generative Answer for RAG
      }
      setActiveStep(prevStep);
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

      // Build nested configuration structure
      const payload: any = {
        name: form.values.conversationName.trim(),
        description: form.values.conversationDescription.trim() || null,
        enable_knowledge_assistant:
          form.values.agentType === 'assistant'
            ? true
            : form.values.enableKnowledgeAssistant,
        // Enhancement configuration
        enhancement: form.values.selectedStrategy !== 'native' && form.values.selectedProviderId && form.values.selectedModel ? {
          strategy: form.values.selectedStrategy,
          provider: {
            id: form.values.selectedProviderId,
            model_name: form.values.selectedModel,
          },
        } : {
          strategy: 'native',
          provider: null,
        },
        // Vector database configuration
        vector_database: {
          collection_name: form.values.collectionName,
          top_k: form.values.topK,
        },
        // Reranker configuration
        reranker: {
          enabled: form.values.enableReranking,
          provider: form.values.enableReranking && form.values.selectedRerankerId && form.values.selectedRerankerModel ? {
            id: form.values.selectedRerankerId,
            model_name: form.values.selectedRerankerModel,
          } : null,
          relevance_threshold: form.values.relevanceThreshold,
        },
        // Answer generation configuration
        answer_generation: {
          enabled: form.values.enableLLMGeneration && form.values.selectedProviderId && form.values.selectedModel ? true : false,
          provider: form.values.enableLLMGeneration && form.values.selectedProviderId && form.values.selectedModel ? {
            id: form.values.selectedProviderId,
            model_name: form.values.selectedModel,
          } : null,
        },
        // System prompt (only for Assistant/Supervisor mode)
        system_prompt: form.values.agentType === 'assistant' && form.values.selectedSystemPromptId && !form.values.selectedSystemPromptId.startsWith('temp-') ? {
          id: form.values.selectedSystemPromptId,
          title: 'Selected System Prompt',
          content: '',
        } : null,
        // Complex nested assistant configuration
        // RAG mode: assistant_config = { enabled: false }
        // Assistant mode: assistant_config = { enabled: true, system_prompt_tasks: [...] }
        assistant_config: {
          enabled: form.values.agentType === 'assistant',
          system_prompt_tasks: form.values.agentType === 'assistant' && form.values.systemPromptTasks && form.values.systemPromptTasks.length > 0 ?
            form.values.systemPromptTasks.map((task: any) => ({
              id: task.id || '',
              title: task.title || task.name || '',
              content: task.content || task.system_prompt || '',
              is_active: task.is_active !== false,
            }))
            : null,
        },
      };

      // Use PUT for edit mode, POST for create mode
      const url = isEditMode
        ? apiUtils.buildApiUrl(`/conversations/${editingConversationId}`)
        : apiUtils.buildApiUrl('/conversations');
      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        const sessionId = isEditMode ? editingConversationId : data.id;

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
          message: isEditMode ? 'Conversation updated successfully' : 'Conversation created successfully',
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

  // Filter steps based on agent type
  // RAG mode: exclude Step 6 (System Prompt)
  // Assistant mode: include all steps
  const visibleSteps = form.values.agentType === 'rag'
    ? STEP_CONFIGS.filter((_, index) => index !== 6) // Remove System Prompt step (index 6)
    : STEP_CONFIGS;

  // Adjust activeStep display for stepper component based on filtered steps
  // For RAG mode: steps 0-5 stay the same, step 7 becomes visual step 6
  // For Assistant mode: no adjustment needed
  const displayActiveStep = form.values.agentType === 'rag' && activeStep === 7 ? 6 : activeStep;

  const pageTitle = isEditMode ? 'Edit Conversation' : 'Create New Conversation';

  return (
    <Page title={pageTitle}>
      <PageHeader title={pageTitle} />

      <ColorfulVerticalStepper
        activeStep={displayActiveStep}
        completedSteps={completedSteps}
        steps={visibleSteps}
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
            providers={providers}
            providersLoading={providersLoading}
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

        {/* STEP 4: JUDGE RANKER */}
        {activeStep === 4 && (
          <StepReranker
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 5: ADVANCED SETTINGS */}
        {activeStep === 5 && (
          <StepAdvancedSettings
            form={form}
            providers={providers}
            providersLoading={providersLoading}
            onPromptSelected={(prompt) => {
              form.setFieldValue('selectedSystemPromptId', prompt.id);
              setSelectedSystemPrompt(prompt);
              // Store the prompt as a system prompt task for assistant_config
              if (prompt) {
                form.setFieldValue('systemPromptTasks', [
                  {
                    id: prompt.id,
                    title: prompt.title || prompt.name,
                    content: prompt.content || prompt.system_prompt,
                    is_active: prompt.is_active !== false,
                  },
                ]);
              }
            }}
            selectedSystemPrompt={selectedSystemPrompt}
          />
        )}

        {/* STEP 6: SYSTEM PROMPT (Assistant mode only) */}
        {form.values.agentType === 'assistant' && activeStep === 6 && (
          <StepSystemPromptConfiguration
            form={form}
            onPromptSelected={(prompt) => {
              form.setFieldValue('selectedSystemPromptId', prompt.id);
              setSelectedSystemPrompt(prompt);
              // Store the prompt as a system prompt task for assistant_config
              if (prompt) {
                form.setFieldValue('systemPromptTasks', [
                  {
                    id: prompt.id,
                    title: prompt.title || prompt.name,
                    content: prompt.content || prompt.system_prompt,
                    is_active: prompt.is_active !== false,
                  },
                ]);
              }
            }}
            selectedSystemPrompt={selectedSystemPrompt}
          />
        )}

        {/* STEP 6 or 7: REVIEW & CREATE (depends on agent type) */}
        {displayActiveStep === (form.values.agentType === 'assistant' ? 7 : 6) && (
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

            {activeStep < 6 ? (
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
                {isEditMode ? 'Update Conversation' : 'Create Conversation'}
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
            onClick={() => {
              form.setFieldValue('agentType', 'rag');
              form.setFieldValue('enableKnowledgeAssistant', false);
              // Clear assistant-only fields when switching to RAG mode
              form.setFieldValue('systemPromptTasks', []);
              form.setFieldValue('selectedSystemPromptId', null);
            }}
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
            onClick={() => {
              form.setFieldValue('agentType', 'assistant');
              form.setFieldValue('enableKnowledgeAssistant', true);
              // Ensure assistant-only fields are initialized
              if (!form.values.systemPromptTasks) {
                form.setFieldValue('systemPromptTasks', []);
              }
            }}
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

      {form.values.selectedStrategy !== 'native' &&
        form.values.selectedStrategy !== 'hyde' && (
          <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
            <Stack gap="xs">
              <Text size="xs">
                <strong>{ENHANCEMENT_STRATEGIES.find((s) => s.value === form.values.selectedStrategy)?.label}:</strong> This strategy generates multiple query variations to comprehensively search your knowledge base.
              </Text>
              <List size="xs">
                <List.Item>Generate {form.values.selectedStrategy === 'augmented' ? '4' : '3-5'} query variants ({form.values.selectedStrategy === 'augmented' ? 'via transformations' : 'via rephrasing'})</List.Item>
                <List.Item>Search the knowledge base with each variant</List.Item>
                <List.Item>Merge results using RRF algorithm (documents appearing in multiple searches rank higher)</List.Item>
                <List.Item>Return your configured Top K documents (the best matches after merging)</List.Item>
              </List>
              <Text size="xs" c="dimmed">
                Example: With {form.values.selectedStrategy === 'augmented' ? '4' : '5'} query variants and Top K={form.values.topK}, the system retrieves ~{Math.ceil((form.values.topK * 1.5) / 5) * 5} documents per variant, merges them via RRF, and returns your final {form.values.topK} best documents.
              </Text>
            </Stack>
          </Alert>
        )}

      {form.values.selectedStrategy === 'hyde' && (
        <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
          <Text size="xs">
            <strong>{ENHANCEMENT_STRATEGIES.find((s) => s.value === 'hyde')?.label}:</strong> This strategy generates one enhanced query variant.
            The system will search using this single enhanced query (no RRF merging needed).
          </Text>
        </Alert>
      )}
    </Stack>
  );
}

function StepEnhancementStrategy({ form, onLearnClick, providers, providersLoading }: StepProps & { onLearnClick: () => void; providers?: any; providersLoading?: boolean }) {
  const selectedStrategyInfo = ENHANCEMENT_STRATEGIES.find((s) => s.value === form.values.selectedStrategy);
  const isNonNativeStrategy = form.values.selectedStrategy !== 'native';

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

      {isNonNativeStrategy && (
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="cyan" variant="light">
            <Text size="sm">
              <strong>LLM Required:</strong> Query enhancement strategies need an LLM to generate query variants. Please select an LLM provider and model below.
            </Text>
          </Alert>

          <Divider my="sm" />

          <Select
            label="LLM Provider for Query Enhancement"
            placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
            data={
              providers?.map((p: any) => ({
                value: p.id,
                label: `${p.name} (${p.provider_type})`,
              })) || []
            }
            {...form.getInputProps('selectedProviderId')}
            searchable
            disabled={providersLoading}
            required
            description="Choose an LLM provider to generate query variants"
          />

          {form.values.selectedProviderId && providers ? (
            <Select
              label="Model for Query Enhancement"
              placeholder="Select a model"
              data={
                providers
                  .find((p: any) => p.id === form.values.selectedProviderId)
                  ?.generative?.models.map((m: string) => ({
                    value: m,
                    label: m,
                  })) || []
              }
              {...form.getInputProps('selectedModel')}
              searchable
              required
              description="This model will be used to generate query variants"
            />
          ) : (
            <Select
              label="Model for Query Enhancement"
              placeholder="Select provider first"
              disabled
              required
            />
          )}
        </>
      )}

      {selectedStrategyInfo && (
        <Card
          withBorder
          p="md"
          style={{
            background: `linear-gradient(135deg, ${selectedStrategyInfo.color === 'green' ? '#dcfce7' : selectedStrategyInfo.color === 'cyan' ? '#cffafe' : selectedStrategyInfo.color === 'blue' ? '#dbeafe' : selectedStrategyInfo.color === 'grape' ? '#f3e8ff' : selectedStrategyInfo.color === 'violet' ? '#ede9fe' : '#f3f4f6'} 0%, #ffffff 100%)`,
            borderColor: selectedStrategyInfo.color === 'green' ? '#22c55e' : selectedStrategyInfo.color === 'cyan' ? '#06b6d4' : selectedStrategyInfo.color === 'blue' ? '#3b82f6' : selectedStrategyInfo.color === 'grape' ? '#a855f7' : selectedStrategyInfo.color === 'violet' ? '#8b5cf6' : '#d1d5db',
            borderWidth: '2px'
          }}
        >
          <Stack gap="md">
            <Group gap="sm">
              <div
                style={{
                  width: '8px',
                  height: '40px',
                  borderRadius: '4px',
                  background: selectedStrategyInfo.color === 'green' ? '#22c55e' : selectedStrategyInfo.color === 'cyan' ? '#06b6d4' : selectedStrategyInfo.color === 'blue' ? '#3b82f6' : selectedStrategyInfo.color === 'grape' ? '#a855f7' : selectedStrategyInfo.color === 'violet' ? '#8b5cf6' : '#d1d5db'
                }}
              />
              <div>
                <Text fw={700} size="md" style={{
                  color: selectedStrategyInfo.color === 'green' ? '#15803d' : selectedStrategyInfo.color === 'cyan' ? '#164e63' : selectedStrategyInfo.color === 'blue' ? '#1e40af' : selectedStrategyInfo.color === 'grape' ? '#6b21a8' : selectedStrategyInfo.color === 'violet' ? '#5b21b6' : '#374151'
                }}>
                  {selectedStrategyInfo.label}
                </Text>
                <Text size="sm" c="dimmed" mt="4px">
                  {selectedStrategyInfo.description}
                </Text>
              </div>
            </Group>

            <Grid gutter="md">
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <Group gap="xs">
                    <div style={{
                      width: '4px',
                      height: '16px',
                      borderRadius: '2px',
                      background: '#22c55e'
                    }} />
                    <Text fw={600} size="xs" c="green">
                      Pros
                    </Text>
                  </Group>
                  <List size="xs">
                    {selectedStrategyInfo.pros.map((pro) => (
                      <List.Item key={pro}>{pro}</List.Item>
                    ))}
                  </List>
                </Stack>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <Group gap="xs">
                    <div style={{
                      width: '4px',
                      height: '16px',
                      borderRadius: '2px',
                      background: '#ef4444'
                    }} />
                    <Text fw={600} size="xs" c="red">
                      Cons
                    </Text>
                  </Group>
                  <List size="xs">
                    {selectedStrategyInfo.cons.map((con) => (
                      <List.Item key={con}>{con}</List.Item>
                    ))}
                  </List>
                </Stack>
              </Grid.Col>
            </Grid>

            {selectedStrategyInfo.example && (
              <Stack gap="xs" style={{
                backgroundColor: '#f9fafb',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}>
                <Text fw={600} size="xs" c="dimmed">
                  Example
                </Text>
                <Stack gap="6px" style={{ fontSize: '12px' }}>
                  <div>
                    <Text size="xs" c="dimmed" fw={500}>Input Query:</Text>
                    <Text size="xs" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>"{selectedStrategyInfo.example.original}"</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed" fw={500}>What Happens:</Text>
                    <Text size="xs" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: '#666' }}>
                      {selectedStrategyInfo.example.output}
                    </Text>
                  </div>
                </Stack>
              </Stack>
            )}
          </Stack>
        </Card>
      )}
    </Stack>
  );
}

function StepReranker({ form, providers, providersLoading }: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
        <Text size="sm">
          Optionally enable document ranking to evaluate and re-rank retrieved documents by relevance before answer generation. This step is optional and can be skipped.
        </Text>
      </Alert>

      <Switch
        label="Enable Judge Ranker"
        description="When enabled, retrieved documents are evaluated and ranked by relevance before answer generation"
        {...form.getInputProps('enableReranking', {
          type: 'checkbox',
        })}
      />

      {form.values.enableReranking && (
        <>
          <Divider my="sm" />

          <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
            <Text size="sm">
              Select a specialized judge provider or use any LLM to evaluate document relevance. The judge will re-rank documents before they are used for answer generation.
            </Text>
          </Alert>

          <Grid gutter="md">
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select
                label="Judge Provider"
                placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
                data={
                  providers?.map((p) => ({
                    value: p.id,
                    label: p.name,
                  })) || []
                }
                {...form.getInputProps('selectedRerankerId')}
                searchable
                disabled={providersLoading}
                description="Choose a specialized judge or any LLM"
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              {(() => {
                const selectedProvider = providers?.find(
                  (p) => p.id === form.values.selectedRerankerId
                );
                const rerankerModels = selectedProvider?.reranker?.models || [];
                const generativeModels =
                  selectedProvider?.generative?.models || [];
                const hasRerankerModels = rerankerModels.length > 0;

                const modelData = hasRerankerModels
                  ? rerankerModels.map((m: string) => ({
                      value: m,
                      label: m,
                    }))
                  : generativeModels.map((m: string) => ({
                      value: m,
                      label: m,
                    }));

                return (
                  <Select
                    label="Judge Model"
                    placeholder="Select a model"
                    data={modelData}
                    {...form.getInputProps('selectedRerankerModel')}
                    searchable
                    description={
                      hasRerankerModels
                        ? "Specialized reranker model"
                        : "Using generative LLM for ranking"
                    }
                  />
                );
              })()}
            </Grid.Col>
          </Grid>

          <NumberInput
            label="Relevance Threshold"
            min={0}
            max={1}
            step={0.05}
            {...form.getInputProps('relevanceThreshold')}
            description="Minimum relevance score (0-1) for filtering documents (optional)"
          />
        </>
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
          Configure how answers are generated. You can either enable AI-powered responses or use raw document results.
        </Text>
      </Alert>

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
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="yellow" variant="light">
            <Text size="sm">
              Raw results mode. Shows retrieved documents as-is without LLM processing. Faster and more cost-effective.
            </Text>
          </Alert>

          {form.values.selectedStrategy !== 'native' && (
            <Alert icon={<IconAlertCircle size={16} />} color="orange" variant="light">
              <Text size="sm">
                <strong>Note:</strong> You've selected a query enhancement strategy ({form.values.selectedStrategy}) but disabled generative answers. The multi-variant retrieval results will be merged and ranked, but returned as raw documents. Consider enabling generative answers to better utilize the enhanced retrieval results.
              </Text>
            </Alert>
          )}
        </>
      )}
    </Stack>
  );
}

function StepSystemPromptConfiguration({
  form,
  onPromptSelected,
  selectedSystemPrompt,
}: StepProps) {
  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light">
        <Text size="sm">
          Define how the task engine assistant should behave when performing tasks. You can create custom prompts or use built-in templates. This prompt will guide the supervisor agent's decision-making and task execution.
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

      {/* Display selected/created prompt content */}
      {selectedSystemPrompt && (
        <Card withBorder p="md" bg="grape.1" style={{ borderColor: '#a855f7' }}>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text fw={600} c="grape">
                {selectedSystemPrompt.title || selectedSystemPrompt.name}
              </Text>
              <Badge size="lg" color="grape">
                Selected
              </Badge>
            </Group>

            {selectedSystemPrompt.description && (
              <Text size="sm" c="dimmed">
                {selectedSystemPrompt.description}
              </Text>
            )}

            <Divider />

            <div>
              <Text size="sm" fw={500} mb="xs" c="dark">
                System Prompt Content:
              </Text>
              <Paper p="sm" bg="white" style={{ borderRadius: '4px', fontFamily: 'monospace', fontSize: '12px', maxHeight: '200px', overflow: 'auto', lineHeight: '1.5', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {selectedSystemPrompt.content || selectedSystemPrompt.system_prompt}
              </Paper>
            </div>
          </Stack>
        </Card>
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
  const selectedRerankerProvider = providers?.find(
    (p) => p.id === form.values.selectedRerankerId
  );
  const enhancementStrategyInfo = ENHANCEMENT_STRATEGIES.find((s) => s.value === form.values.selectedStrategy);

  return (
    <Stack gap="md">
      <Alert icon={<IconCheck size={16} />} color="green" variant="light">
        <Text size="sm">
          Review your configuration below. All settings will be saved as nested configuration. Click <strong>Create Conversation</strong> to proceed.
        </Text>
      </Alert>

      {/* STEP 0: AGENT TYPE */}
      <Card withBorder p="md" bg="blue.0">
        <Stack gap="xs">
          <Group justify="space-between">
            <Text fw={600}>Step 0: Agent Type</Text>
            <Badge size="lg" color={form.values.agentType === 'rag' ? 'blue' : 'grape'}>
              {form.values.agentType === 'rag' ? 'RAG Mode' : 'Assistant Mode'}
            </Badge>
          </Group>
          <Text size="xs" c="dark">
            {form.values.agentType === 'rag'
              ? 'Standard RAG pipeline: retrieval + optional reranking + optional answer generation'
              : 'Supervisor mode: intelligent task routing + RAG context + system prompt execution'}
          </Text>
        </Stack>
      </Card>

      {/* STEP 1: CONVERSATION SETTINGS */}
      <Card withBorder p="md" bg="blue.0">
        <Stack gap="sm">
          <Text fw={600}>Step 1: Conversation Settings</Text>
          <Text fw={500} size="lg" c="dark">
            {form.values.conversationName}
          </Text>
          {form.values.conversationDescription && (
            <Text size="sm" c="dark">
              {form.values.conversationDescription}
            </Text>
          )}
        </Stack>
      </Card>

      {/* STEP 2: ENHANCEMENT STRATEGY */}
      <Card withBorder p="md" bg="cyan.0">
        <Stack gap="sm">
          <Text fw={600}>Step 2: Enhancement Strategy</Text>
          <Group gap="md">
            <div>
              <Text size="sm" fw={500} mb="xs">
                Strategy
              </Text>
              <Badge size="lg" color={enhancementStrategyInfo?.color || 'gray'}>
                {enhancementStrategyInfo?.label || 'Native'}
              </Badge>
            </div>
            {form.values.selectedStrategy !== 'native' && (
              <div>
                <Text size="sm" fw={500} mb="xs">
                  Query Enhancement Provider
                </Text>
                <Stack gap="4px">
                  <Text size="sm" c="dark">
                    Provider: {selectedProvider?.name || 'Not selected'}
                  </Text>
                  <Text size="sm" c="dark">
                    Model: {form.values.selectedModel || 'Not selected'}
                  </Text>
                </Stack>
              </div>
            )}
          </Group>
        </Stack>
      </Card>

      {/* STEP 3: VECTOR DATABASE */}
      <Card withBorder p="md" bg="teal.0">
        <Stack gap="sm">
          <Text fw={600}>Step 3: Vector Database</Text>
          <Grid gutter="md">
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Stack gap="xs">
                <div>
                  <Text size="xs" fw={500} c="dark">Collection Name</Text>
                  <Text size="sm" fw={500} c="dark">{selectedCollection?.name || form.values.collectionName}</Text>
                </div>
                <div>
                  <Text size="xs" fw={500} c="dark">Records</Text>
                  <Text size="sm" fw={500} c="dark">{selectedCollection?.record_count.toLocaleString() || 'Unknown'}</Text>
                </div>
              </Stack>
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Stack gap="xs">
                <div>
                  <Text size="xs" fw={500} c="dark">Top K (Retrieval Count)</Text>
                  <Text size="sm" fw={500} c="dark">{form.values.topK} documents</Text>
                </div>
              </Stack>
            </Grid.Col>
          </Grid>
        </Stack>
      </Card>

      {/* STEP 4: RERANKER (OPTIONAL) */}
      {form.values.enableReranking && (
        <Card withBorder p="md" bg="yellow.0">
          <Stack gap="sm">
            <Text fw={600}>Step 4: Judge Ranker (Document Re-ranking)</Text>
            <Grid gutter="md">
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <div>
                    <Text size="xs" fw={500} c="dark">Reranker Provider</Text>
                    <Text size="sm" fw={500} c="dark">{selectedRerankerProvider?.name || 'Not selected'}</Text>
                  </div>
                  <div>
                    <Text size="xs" fw={500} c="dark">Model</Text>
                    <Text size="sm" fw={500} c="dark">{form.values.selectedRerankerModel || 'Not selected'}</Text>
                  </div>
                </Stack>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Stack gap="xs">
                  <div>
                    <Text size="xs" fw={500} c="dark">Relevance Threshold</Text>
                    <Text size="sm" fw={500} c="dark">{form.values.relevanceThreshold} (0-1 scale)</Text>
                  </div>
                  <Text size="xs" c="dark">
                    Documents below this score will be filtered out
                  </Text>
                </Stack>
              </Grid.Col>
            </Grid>
          </Stack>
        </Card>
      )}

      {/* STEP 5: ANSWER GENERATION & SYSTEM PROMPT */}
      <Card withBorder p="md" bg="lime.0">
        <Stack gap="sm">
          <Text fw={600}>
            Step 5: Answer Generation {form.values.agentType === 'assistant' && '& System Prompt'}
          </Text>
          <Group gap="md">
            <div>
              <Text size="sm" fw={500} mb="xs" c="dark">
                Generative Answer
              </Text>
              <Badge size="lg" color={form.values.enableLLMGeneration ? 'green' : 'gray'}>
                {form.values.enableLLMGeneration ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
            {form.values.enableLLMGeneration && (
              <div>
                <Text size="sm" fw={500} mb="xs" c="dark">
                  Answer Generation Provider
                </Text>
                <Stack gap="4px">
                  <Text size="sm" c="dark">
                    Provider: {selectedProvider?.name || 'Not selected'}
                  </Text>
                  <Text size="sm" c="dark">
                    Model: {form.values.selectedModel || 'Not selected'}
                  </Text>
                </Stack>
              </div>
            )}
          </Group>
          {form.values.agentType === 'assistant' && (
            <div style={{ borderTop: '1px solid #dee2e6', paddingTop: '12px', marginTop: '12px' }}>
              <Text size="sm" fw={500} mb="xs" c="dark">System Prompt</Text>
              <Badge color={form.values.selectedSystemPromptId ? 'blue' : 'gray'}>
                {form.values.selectedSystemPromptId ? 'Configured' : 'Not configured'}
              </Badge>
            </div>
          )}
        </Stack>
      </Card>

      {/* STEP 6: SYSTEM PROMPT CONFIGURATION (Assistant mode only) */}
      {form.values.agentType === 'assistant' && (
        <Card withBorder p="md" bg="violet.1" style={{ borderColor: '#a78bfa' }}>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text fw={600}>Step 6: System Prompt Configuration</Text>
              <Badge size="lg" color="violet">
                {form.values.systemPromptTasks?.length || 0} Task{form.values.systemPromptTasks?.length !== 1 ? 's' : ''}
              </Badge>
            </Group>
            {form.values.systemPromptTasks && form.values.systemPromptTasks.length > 0 ? (
              <Stack gap="sm">
                <Stack gap="xs">
                  {form.values.systemPromptTasks.map((task: any, index: number) => (
                    <Card key={index} withBorder p="sm" bg="white" style={{ borderColor: '#d8b4fe' }}>
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <div style={{ flex: 1 }}>
                            <Text fw={600} size="sm" c="dark">
                              {task.title || task.name || `Task ${index + 1}`}
                            </Text>
                          </div>
                          <Badge size="sm" color={task.is_active !== false ? 'green' : 'gray'}>
                            {task.is_active !== false ? 'Active' : 'Inactive'}
                          </Badge>
                        </Group>
                        <Text size="sm" c="dark" lineClamp={3}>
                          {task.content || task.system_prompt || 'No content'}
                        </Text>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </Stack>
            ) : (
              <Alert icon={<IconAlertCircle size={16} />} color="yellow" variant="light">
                <Text size="sm">No system prompt tasks configured</Text>
              </Alert>
            )}
          </Stack>
        </Card>
      )}

    </Stack>
  );
}

export default ConversationCreateWizard;
