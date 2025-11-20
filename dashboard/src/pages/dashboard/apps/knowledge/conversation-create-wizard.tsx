/**
 * Conversation Creation Wizard
 *
 * Multi-step wizard for creating conversations with:
 * Step 0: Agent Type & Settings (Mode selection + Name/Description)
 * Step 1: Enhancement Strategy (Query enhancement options - requires LLM provider if non-native strategy selected)
 * Step 2: Vector Database Selection
 * Step 3: Judge Ranker (Document ranking - optional)
 * Step 4: Generative Answer (LLM configuration)
 * Step 5: Tools & Instructions (Assistant mode - select tools and configure orchestration)
 * Step 6: Review & Create
 */

import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetTools } from '@/api/resources/tools';
import { useGetCollections } from '@/api/resources/vectordb';
import { ColorfulVerticalStepper } from '@/components/colorful-vertical-stepper';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
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
  ThemeIcon
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconArrowsLeftRight,
  IconCheck,
  IconDatabase,
  IconHelp,
  IconInfoCircle,
  IconRobot,
  IconScale,
  IconTool,
  IconWand
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ToolInstructionsStep } from './tool-instructions-step';

// ============================================================================
// TYPES & CONSTANTS
// ============================================================================

interface ConversationFormData {
  // Step 0 - Agent Type & Settings
  agentType: 'rag' | 'assistant';
  conversationName: string;
  conversationDescription: string;

  // Step 1 - Enhancement Strategy
  selectedStrategy: string;
  selectedProviderId: string | null;
  selectedModel: string | null;

  // Step 2 - Vector Database
  collectionName: string;
  topK: number;

  // Step 3 - Judge Ranker
  enableReranking: boolean;
  relevanceThreshold: number;
  selectedRerankerId: string | null;
  selectedRerankerModel: string | null;

  // Step 4 - Generative Answer
  enableLLMGeneration: boolean;
  enableKnowledgeAssistant: boolean;

  // Step 5 - Tools Binding (Assistant mode only)
  selectedTools: string[]; // Array of tool IDs
  instructions: string; // User's custom instructions for assistant behavior
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
    label: 'Agent Type & Settings',
    description: 'Choose mode and basic info',
    icon: <IconRobot size={20} />,
    color: 'blue',
    gradientFrom: LOGO_COLORS.data,        // Teal (Data)
    gradientTo: LOGO_COLORS.accent2,       // Vibrant Green
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
    label: 'Tools & Instructions',
    description: 'Select tools and configure orchestration',
    icon: <IconTool size={20} />,
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
  const { data: tools, isLoading: toolsLoading } = useGetTools();

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
      selectedTools: [], // Initialize as empty array - will be populated when user selects tools
      instructions: '', // Initialize as empty string - optional user-provided assistant behavior instructions
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
    const state = location.state as {
      editingConversationId?: string;
      fromJob?: boolean;
      jobId?: string;
      jobName?: string;
      jobDescription?: string;
      vectordbCollectionId?: string;
    } | null;

    if (state?.editingConversationId) {
      setIsEditMode(true);
      setEditingConversationId(state.editingConversationId);
      loadExistingConversation(state.editingConversationId);
    } else if (state?.fromJob && state.jobId) {
      // Pre-populate from job data
      console.log('[DEBUG] Pre-populating conversation from job:', state);

      // Set conversation name and description from job
      if (state.jobName) {
        form.setFieldValue('conversationName', `${state.jobName} Agent`);
      }
      if (state.jobDescription) {
        form.setFieldValue('conversationDescription', `Conversation agent for ${state.jobDescription}`);
      }

      // Fetch and set vectordb collection name
      if (state.vectordbCollectionId) {
        fetchCollectionName(state.vectordbCollectionId);
      }
    }
  }, []);

  // Auto-select custom_variants strategy when Assistant mode is selected
  useEffect(() => {
    if (form.values.agentType === 'assistant') {
      // Only change if not already set to custom_variants (to avoid overwriting in edit mode)
      if (form.values.selectedStrategy !== 'custom_variants') {
        form.setFieldValue('selectedStrategy', 'custom_variants');
      }
      // Ensure enableKnowledgeAssistant is true for assistant mode
      if (!form.values.enableKnowledgeAssistant) {
        form.setFieldValue('enableKnowledgeAssistant', true);
      }
    } else {
      // RAG mode - ensure enableKnowledgeAssistant is false
      if (form.values.enableKnowledgeAssistant) {
        form.setFieldValue('enableKnowledgeAssistant', false);
      }
    }
  }, [form.values.agentType]);

  // Fetch collection name by ID
  const fetchCollectionName = async (collectionId: string) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(apiUtils.buildApiUrl(`/knowledge/vectordb-collections/${collectionId}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const collection = await response.json();
        console.log('[DEBUG] Fetched collection:', collection);
        if (collection.collection_name) {
          form.setFieldValue('collectionName', collection.collection_name);
        }
      } else {
        console.error('[ERROR] Failed to fetch collection:', response.status);
      }
    } catch (error) {
      console.error('[ERROR] Error fetching collection:', error);
    }
  };

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

        console.log('[DEBUG loadExistingConversation] Full session object:', JSON.stringify(session, null, 2));
        console.log('[DEBUG loadExistingConversation] session.assistant_config:', session.assistant_config);

        // Populate form with existing conversation data
        form.setValues({
          agentType: session.assistant_config?.enabled ? 'assistant' : 'rag',
          conversationName: session.name || '',
          conversationDescription: session.description || '',
          // Load LLM provider/model - prefer answer_generation, fallback to enhancement
          selectedProviderId: session.answer_generation?.provider?.id || session.enhancement?.provider?.id || null,
          selectedModel: session.answer_generation?.provider?.model_name || session.enhancement?.provider?.model_name || null,
          selectedStrategy: session.enhancement?.strategy || 'native',
          collectionName: session.vector_database?.collection_name || '',
          topK: session.vector_database?.top_k || 5,
          enableReranking: session.reranker?.enabled || false,
          relevanceThreshold: session.reranker?.relevance_threshold || 0.5,
          selectedRerankerId: session.reranker?.provider?.id || null,
          selectedRerankerModel: session.reranker?.provider?.model_name || null,
          enableLLMGeneration: session.answer_generation?.enabled || false,
          enableKnowledgeAssistant: session.assistant_config?.enabled || false,
          selectedTools: session.assistant_config?.tools || [],
          instructions: session.assistant_config?.instructions || '',
        });

        console.log('[DEBUG loadExistingConversation] form.values after setValues:', form.values);
        console.log('[DEBUG loadExistingConversation] form.values.selectedTools after setValues:', form.values.selectedTools);

        // No need to set selectedSystemPrompt as tools are now standalone
        if (false) { // Removed old system prompt logic
        } else {
          console.log('[DEBUG loadExistingConversation] No system_prompt_tasks found in session');
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
        // Agent type & conversation settings - name required
        return !!form.values.conversationName.trim();
      case 1:
        // Enhancement Strategy - if non-native, LLM provider & model are required for generating variants
        if (form.values.selectedStrategy !== 'native') {
          return !!form.values.selectedProviderId && !!form.values.selectedModel;
        }
        return true; // Native strategy doesn't need LLM provider
      case 2:
        // Vector Database - collection & topK required
        return !!form.values.collectionName && form.values.topK >= 5;
      case 3:
        // Judge Ranker - all optional
        return true;
      case 4:
        // Generative Answer - provider & model required only if enabled
        if (form.values.enableLLMGeneration) {
          return !!form.values.selectedProviderId && !!form.values.selectedModel;
        }
        return true;
      case 5:
        // Tools & Instructions - only for Assistant mode, always valid
        return true;
      case 6:
        // Review & Create - always valid
        return true;
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

    // Skip Step 5 (Tools & Instructions) for RAG mode
    let nextStep = activeStep + 1;
    if (activeStep === 4 && form.values.agentType === 'rag') {
      nextStep = 6; // Skip to Review & Create for RAG mode
    }

    setActiveStep(nextStep);
  };

  const handlePreviousStep = () => {
    if (activeStep > 0) {
      let prevStep = activeStep - 1;
      // Skip Step 5 (Tools & Instructions) when going back in RAG mode
      if (activeStep === 6 && form.values.agentType === 'rag') {
        prevStep = 4; // Skip from Review & Create back to Generative Answer for RAG
      }
      setActiveStep(prevStep);
    }
  };

  const handleStepClick = (step: number) => {
    // In edit mode, allow free navigation between any steps
    if (isEditMode) {
      setActiveStep(step);
      return;
    }

    // In create mode, enforce sequential validation
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
      console.log('=== DEBUG: PRE-PAYLOAD STATE ===');
      console.log('agentType:', form.values.agentType);
      console.log('form.values.selectedTools:', form.values.selectedTools);
      console.log('isEditMode:', isEditMode);
      console.log('editingConversationId:', editingConversationId);

      const payload: any = {
        name: form.values.conversationName.trim(),
        description: form.values.conversationDescription.trim() || null,
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
        // Complex nested assistant configuration
        // RAG mode: assistant_config = { enabled: false, tools: [] }
        // Assistant mode: assistant_config = { enabled: true, tools: [...tool_ids], instructions: "..." }
        assistant_config: {
          enabled: form.values.agentType === 'assistant',
          tools: form.values.agentType === 'assistant' ? form.values.selectedTools : [],
          instructions: form.values.agentType === 'assistant' ? form.values.instructions : null,
        },
      };

      console.log('DEBUG: assistant_config in payload:', {
        enabled: payload.assistant_config.enabled,
        tools: payload.assistant_config.tools,
        tools_count: payload.assistant_config.tools?.length || 0,
      });

      // Use PUT for edit mode, POST for create mode
      const url = isEditMode
        ? apiUtils.buildApiUrl(`/conversations/${editingConversationId}`)
        : apiUtils.buildApiUrl('/conversations');
      const method = isEditMode ? 'PUT' : 'POST';

      console.log('DEBUG: Payload being sent:', JSON.stringify(payload, null, 2));

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
        console.log('[DEBUG] Response from backend:', data);
        const sessionId = isEditMode ? editingConversationId : data.id;

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
          message: errorData.detail || 'Failed to create conversation Agent',
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
  // RAG mode: exclude Step 5 (Tools & Instructions)
  // Assistant mode: include all steps
  const visibleSteps = form.values.agentType === 'rag'
    ? STEP_CONFIGS.filter((_, index) => index !== 5) // Remove Tools & Instructions step for RAG mode
    : STEP_CONFIGS;

  // Adjust activeStep display for stepper component based on filtered steps
  // For RAG mode: steps 0-4 stay the same, step 6 (Review & Create) becomes visual step 5
  // For Assistant mode: no adjustment needed
  const displayActiveStep = form.values.agentType === 'rag' && activeStep === 6 ? 5 : activeStep;

  const pageTitle = isEditMode ? 'Edit Conversation Agent' : 'Create New Conversation Agent';

  return (
    <Page title={pageTitle}>
      <PageHeader title={pageTitle} />

      <ColorfulVerticalStepper
        activeStep={displayActiveStep}
        completedSteps={completedSteps}
        steps={visibleSteps}
        onStepClick={handleStepClick}
        isEditMode={isEditMode}
      >
        {/* STEP 0: AGENT TYPE & SETTINGS */}
        {activeStep === 0 && <StepAgentTypeAndSettings form={form} />}

        {/* STEP 1: ENHANCEMENT STRATEGY */}
        {activeStep === 1 && (
          <StepEnhancementStrategy
            form={form}
            onLearnClick={() => setStrategiesInfoModalOpen(true)}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 2: VECTOR DATABASE */}
        {activeStep === 2 && (
          <StepVectorDatabase
            form={form}
            collections={collections}
            collectionsLoading={collectionsLoading}
          />
        )}

        {/* STEP 3: JUDGE RANKER */}
        {activeStep === 3 && (
          <StepReranker
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 4: GENERATIVE ANSWER */}
        {activeStep === 4 && (
          <StepAdvancedSettings
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 5: TOOLS & INSTRUCTIONS (Assistant mode only) */}
        {form.values.agentType === 'assistant' && activeStep === 5 && (
          <Stack gap="lg">
            {/* Tools Selection Section */}
            <Card withBorder shadow="sm">
              <Stack gap="lg">
                <div>
                  <Text size="lg" fw={600} mb="xs">
                    Select Tools for Agent
                  </Text>
                  <Text size="sm" c="dimmed">
                    Choose which tools the assistant agent can use. Tools extend the agent's capabilities by allowing it to perform specialized tasks.
                  </Text>
                </div>

                {toolsLoading ? (
                  <Text size="sm" c="dimmed">Loading tools...</Text>
                ) : !tools || !Array.isArray(tools) || tools.length === 0 ? (
                  <Alert icon={<IconAlertCircle size={16} />} color="yellow" variant="light">
                    <Text size="sm">No tools available. Create tools in the Tools Management section first.</Text>
                  </Alert>
                ) : (
                  <Stack gap="md">
                    <Text size="sm" fw={500}>Available Tools ({tools?.filter((t: any) => t.is_active).length || 0} active)</Text>
                    <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '8px' }}>
                      <Stack gap="md">
                        {tools?.filter((t: any) => t.is_active).map((tool: any) => (
                          <Card key={tool.id} withBorder p="sm" style={{ cursor: 'pointer' }} onClick={() => {
                            const currentTools = form.values.selectedTools || [];
                            const isSelected = currentTools.includes(tool.id);
                            form.setFieldValue(
                              'selectedTools',
                              isSelected
                                ? currentTools.filter((id: string) => id !== tool.id)
                                : [...currentTools, tool.id]
                            );
                          }}>
                            <Group justify="space-between" align="flex-start">
                              <Group align="flex-start" gap="md" style={{ flex: 1 }}>
                                <input
                                  type="checkbox"
                                  checked={form.values.selectedTools?.includes(tool.id) || false}
                                  onChange={() => { }} // Handled by card onClick
                                  style={{ marginTop: '4px', cursor: 'pointer' }}
                                />
                                <Stack gap="xs" style={{ flex: 1 }}>
                                  <div>
                                    <Group gap="xs">
                                      <Text fw={600} size="sm">{tool.display_name || tool.name}</Text>
                                      <Badge size="sm" color={tool.tool_type === 'prompt_based' ? 'blue' : 'green'}>
                                        {tool.tool_type === 'prompt_based' ? 'Prompt-Based' : 'MCP Remote'}
                                      </Badge>
                                    </Group>
                                    <Text size="xs" c="dimmed">ID: {tool.name}</Text>
                                  </div>
                                  <Text size="sm" c="dark" lineClamp={2}>
                                    {tool.description || 'No description'}
                                  </Text>
                                  {tool.tags && tool.tags.length > 0 && (
                                    <Group gap="xs">
                                      {tool.tags.map((tag: string) => (
                                        <Badge key={tag} size="xs" variant="dot" color="gray">
                                          {tag}
                                        </Badge>
                                      ))}
                                    </Group>
                                  )}
                                </Stack>
                              </Group>
                            </Group>
                          </Card>
                        ))}
                      </Stack>
                    </div>
                  </Stack>
                )}

                {form.values.selectedTools && form.values.selectedTools.length > 0 && (
                  <Alert icon={<IconCheck size={16} />} color="blue" variant="light">
                    <Text size="sm">{form.values.selectedTools.length} tool(s) selected</Text>
                  </Alert>
                )}
              </Stack>
            </Card>

            {/* Instructions & Tool Orchestration - ALWAYS visible (instructions control overall agent behavior) */}
            <Card withBorder shadow="sm">
              <ToolInstructionsStep
                form={form}
                tools={tools && Array.isArray(tools) ? tools : []}
                providers={providers}
              />
            </Card>
          </Stack>
        )}

        {/* STEP 6: REVIEW & CREATE (depends on agent type) */}
        {displayActiveStep === (form.values.agentType === 'assistant' ? 6 : 5) && (
          <StepReviewAndCreate
            form={form}
            providers={providers}
            collections={collections}
            tools={tools}
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
                {isEditMode ? 'Update Conversation Agent' : 'Create Conversation Agent'}
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
              {ENHANCEMENT_STRATEGIES
                .filter(strategy => form.values.agentType === 'assistant' || strategy.value !== 'custom_variants') // Hide custom_variants in RAG mode
                .map((strategy) => (
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
                {ENHANCEMENT_STRATEGIES
                  .filter(strategy => form.values.agentType === 'assistant' || strategy.value !== 'custom_variants') // Hide custom_variants in RAG mode
                  .map((strategy) => (
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
  tools?: any[];
  onPromptSelected?: (prompt: any) => void;
  selectedSystemPrompt?: any;
}

function StepAgentTypeAndSettings({ form }: StepProps) {
  return (
    <Stack gap="xl">
      {/* Agent Type Selection */}
      <div>
        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          <Text size="sm">
            Choose how you want to use this conversation. <strong>RAG Mode</strong> searches your knowledge base.
            <strong>Assistant Mode</strong> performs tasks using knowledge base information.
          </Text>
        </Alert>

        <Grid mt="md">
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
                // RAG mode uses native strategy by default (or user can choose)
                if (form.values.selectedStrategy === 'custom_variants') {
                  form.setFieldValue('selectedStrategy', 'native');
                }
                // Clear assistant-only fields when switching to RAG mode
                form.setFieldValue('selectedTools', []);
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
                // Assistant mode always uses custom_variants strategy
                form.setFieldValue('selectedStrategy', 'custom_variants');
                // Ensure assistant-only fields are initialized
                if (!form.values.selectedTools) {
                  form.setFieldValue('selectedTools', []);
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
            mt="md"
          >
            <Text size="sm">
              Assistant Mode requires a system prompt. You can create or customize one in the Advanced Settings step.
            </Text>
          </Alert>
        )}
      </div>

      {/* Conversation Settings */}
      <Divider label="Conversation Details" labelPosition="center" />

      <div>
        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light" mb="md">
          <Text size="sm">
            Set up basic information about your conversation. These details help you organize and identify different conversations.
          </Text>
        </Alert>

        <TextInput
          label="Conversation Name"
          placeholder="e.g., Customer Support Bot"
          {...form.getInputProps('conversationName')}
          required
          mb="md"
        />

        <Textarea
          label="Description (Optional)"
          placeholder="Brief description of what this conversation is for..."
          {...form.getInputProps('conversationDescription')}
          rows={4}
        />
      </div>
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
  const isAssistantMode = form.values.agentType === 'assistant';

  return (
    <Stack gap="md">
      {isAssistantMode && (
        <Alert icon={<IconRobot size={16} />} color="grape" variant="light">
          <Text size="sm">
            🔒 <strong>Strategy Locked</strong> - Custom Variants automatically generates 3-5 query variants before passing to RAG with parallel search &amp; RRF fusion.
          </Text>
        </Alert>
      )}

      {!isAssistantMode && (
        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          <Text size="sm">
            Choose how your queries will be enhanced before searching the knowledge base.
          </Text>
        </Alert>
      )}

      <Group justify="space-between" align="flex-end">
        <div style={{ flex: 1 }}>
          {isAssistantMode ? (
            // Read-only display for Assistant mode
            <div>
              <label style={{ fontSize: '14px', fontWeight: 500, display: 'block', marginBottom: '8px' }}>
                Enhancement Strategy
              </label>
              <div style={{
                padding: '8px 12px',
                border: '1px solid var(--mantine-color-gray-3)',
                borderRadius: '4px',
                backgroundColor: 'var(--mantine-color-gray-1)',
                color: 'var(--mantine-color-gray-7)',
                opacity: 0.7,
              }}>
                Custom Variants
              </div>
            </div>
          ) : (
            <Select
              label="Enhancement Strategy"
              placeholder="Select strategy"
              data={ENHANCEMENT_STRATEGIES
                .filter(s => s.value !== 'custom_variants') // Hide custom_variants in RAG mode
                .map((s) => ({
                  value: s.value,
                  label: s.label,
                }))}
              {...form.getInputProps('selectedStrategy')}
              description="How to enhance queries for better retrieval"
            />
          )}
        </div>
        {!isAssistantMode && (
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
        )}
      </Group>

      {isNonNativeStrategy && (
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="cyan" variant="light">
            <Text size="sm">
              <strong>LLM Required:</strong> Select an LLM provider &amp; model below (also used for answer generation if enabled in Step 5).
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
  const isSupervisorMode = form.values.enableKnowledgeAssistant;

  return (
    <Stack gap="md">
      <Alert icon={<IconInfoCircle size={16} />} color={isSupervisorMode ? 'grape' : 'blue'} variant="light">
        <Text size="sm">
          {isSupervisorMode
            ? 'In Supervisor Agent mode, RAG returns raw documents without LLM generation. The Task Engine receives full document context for powerful task execution.'
            : 'Configure how answers are generated. You can either enable AI-powered responses or use raw document results.'}
        </Text>
      </Alert>

      {!isSupervisorMode && (
        <Switch
          label="Enable Generative Answer"
          description="Generate natural language answers using LLM"
          {...form.getInputProps('enableLLMGeneration', {
            type: 'checkbox',
          })}
        />
      )}

      {isSupervisorMode && (
        <Alert icon={<IconAlertCircle size={16} />} color="violet" variant="light">
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" fw={600}>
                Generative Answer
              </Text>
              <Badge color="violet" variant="filled">
                Disabled in Supervisor Mode
              </Badge>
            </Group>
            <Text size="sm" c="dimmed">
              Task Engine receives raw retrieval results for maximum context and flexibility in task execution.
            </Text>
          </Stack>
        </Alert>
      )}

      {!isSupervisorMode && (
        <>
          {form.values.enableLLMGeneration ? (
            <>
              {form.values.selectedStrategy !== 'native' ? (
                <>
                  <Alert icon={<IconInfoCircle size={16} />} color="cyan" variant="light">
                    <Text size="sm">
                      <strong>Using Enhancement Strategy LLM:</strong> Since you selected a non-native enhancement strategy, the same LLM provider and model from Step 2 will be used for both query enhancement and answer generation. To use a different LLM, please go back to Step 2 and change the strategy to "Native" or select a different provider.
                    </Text>
                  </Alert>

                  {form.values.selectedProviderId && form.values.selectedModel && (
                    <Card withBorder p="md" bg="cyan.0">
                      <Stack gap="xs">
                        <Text size="sm" fw={600} c="cyan.9">
                          LLM Configuration (from Enhancement Step)
                        </Text>
                        <Group gap="xs">
                          <Badge size="lg" color="cyan" variant="filled">
                            Provider: {providers?.find((p: any) => p.id === form.values.selectedProviderId)?.name || form.values.selectedProviderId}
                          </Badge>
                          <Badge size="lg" color="cyan" variant="filled">
                            Model: {form.values.selectedModel}
                          </Badge>
                        </Group>
                      </Stack>
                    </Card>
                  )}
                </>
              ) : (
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
        existingPrompts={form.values.systemPromptTasks || []}
        onPromptSelected={(prompt) => {
          console.log('[DEBUG SystemPromptConfiguration] onPromptSelected called with:', prompt);
          form.setFieldValue('selectedSystemPromptId', prompt?.id || null);
          console.log('[DEBUG SystemPromptConfiguration] Calling parent onPromptSelected callback...');
          onPromptSelected?.(prompt);
        }}
        onPromptsChanged={(prompts) => {
          console.log('[DEBUG SystemPromptConfiguration] Prompts changed:', prompts);
          form.setFieldValue('systemPromptTasks', prompts);
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

function StepReviewAndCreate({ form, providers, collections, tools }: StepProps) {
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
          Review your configuration below. All settings will be saved as nested configuration. Click <strong>Create Conversation Agent</strong> to proceed.
        </Text>
      </Alert>

      {/* STEP 0: AGENT TYPE & SETTINGS */}
      <Card withBorder p="md" bg="blue.0">
        <Stack gap="sm">
          <Group justify="space-between">
            <Text fw={600}>Step 0: Agent Type & Settings</Text>
            <Badge size="lg" color={form.values.agentType === 'rag' ? 'blue' : 'grape'}>
              {form.values.agentType === 'rag' ? 'RAG Mode' : 'Assistant Mode'}
            </Badge>
          </Group>
          <Text size="xs" c="dark" mb="xs">
            {form.values.agentType === 'rag'
              ? 'Standard RAG pipeline: retrieval + optional reranking + optional answer generation'
              : 'Supervisor mode: intelligent task routing + RAG context + dynamic tool execution'}
          </Text>
          <Divider />
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

      {/* STEP 1: ENHANCEMENT STRATEGY */}
      <Card withBorder p="md" bg="cyan.0">
        <Stack gap="sm">
          <Text fw={600}>Step 1: Enhancement Strategy</Text>
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

      {/* STEP 2: VECTOR DATABASE */}
      <Card withBorder p="md" bg="teal.0">
        <Stack gap="sm">
          <Text fw={600}>Step 2: Vector Database</Text>
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

      {/* STEP 3: RERANKER (OPTIONAL) */}
      {form.values.enableReranking && (
        <Card withBorder p="md" bg="yellow.0">
          <Stack gap="sm">
            <Text fw={600}>Step 3: Judge Ranker (Document Re-ranking)</Text>
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

      {/* STEP 4: ANSWER GENERATION */}
      <Card withBorder p="md" bg="lime.0">
        <Stack gap="sm">
          <Text fw={600}>
            Step 4: Answer Generation
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
        </Stack>
      </Card>

      {/* STEP 5: TOOLS BINDING (Assistant mode only) */}
      {form.values.agentType === 'assistant' && (
        <Card withBorder p="md" bg="violet.1" style={{ borderColor: '#a78bfa' }}>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text fw={600}>Step 5: Tools Binding</Text>
              <Badge size="lg" color="violet">
                {form.values.selectedTools?.length || 0} Tool{form.values.selectedTools?.length !== 1 ? 's' : ''}
              </Badge>
            </Group>
            {/* Assistant Instructions */}
            {form.values.instructions && (
              <Stack gap="xs">
                <Text fw={500} size="sm" c="grape">
                  Assistant Instructions
                </Text>
                <Paper p="sm" bg="white" style={{ border: '1px solid #d8b4fe', borderRadius: '4px' }}>
                  <Text size="xs" style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }} c="dark">
                    {form.values.instructions}
                  </Text>
                </Paper>
              </Stack>
            )}

            {/* Selected Tools */}
            {form.values.selectedTools && form.values.selectedTools.length > 0 ? (
              <Stack gap="sm">
                <Text fw={500} size="sm" c="grape">
                  Selected Tools
                </Text>
                <Stack gap="xs">
                  {form.values.selectedTools.map((toolId: string) => {
                    const tool = (tools && Array.isArray(tools) ? tools : [])?.find((t: any) => t.id === toolId);
                    if (!tool) return null;
                    return (
                      <Card key={toolId} withBorder p="sm" bg="white" style={{ borderColor: '#d8b4fe' }}>
                        <Stack gap="xs">
                          <Group justify="space-between">
                            <div style={{ flex: 1 }}>
                              <Text fw={600} size="sm" c="dark">
                                {tool.display_name || tool.name}
                              </Text>
                              <Text size="xs" c="dimmed">
                                {tool.name}
                              </Text>
                            </div>
                            <Badge size="sm" color={tool.tool_type === 'prompt_based' ? 'blue' : 'green'}>
                              {tool.tool_type === 'prompt_based' ? 'Prompt-Based' : 'MCP Remote'}
                            </Badge>
                          </Group>
                          <Text size="sm" c="dark" lineClamp={2}>
                            {tool.description || 'No description'}
                          </Text>
                          {tool.tags && tool.tags.length > 0 && (
                            <Group gap="xs">
                              {tool.tags.map((tag: string) => (
                                <Badge key={tag} size="xs" variant="dot" color="gray">
                                  {tag}
                                </Badge>
                              ))}
                            </Group>
                          )}
                        </Stack>
                      </Card>
                    );
                  })}
                </Stack>
              </Stack>
            ) : (
              <Alert icon={<IconAlertCircle size={16} />} color="yellow" variant="light">
                <Text size="sm">No tools selected</Text>
              </Alert>
            )}
          </Stack>
        </Card>
      )}

    </Stack>
  );
}

export default ConversationCreateWizard;
