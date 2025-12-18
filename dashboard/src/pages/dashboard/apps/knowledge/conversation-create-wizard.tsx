/**
 * Conversation Creation Wizard
 *
 * Multi-step wizard for creating agents with different flows for RAG and Assistant modes:
 *
 * RAG Mode (7 steps):
 * Step 0: Agent Type & Settings (Mode selection + Name/Description)
 * Step 2: Agent LLM Provider (Primary LLM for the agent)
 * Step 1: Enhancement Strategy (Query enhancement options - requires LLM provider if non-native strategy)
 * Step 3: Vector Database (Vector DB collection and search settings)
 * Step 4: Judge Ranker (Document ranking - optional)
 * Step 5: Generative Answer (LLM configuration)
 * Step 7: Review & Create
 *
 * Assistant Mode (5 steps):
 * Step 0: Agent Type & Settings (Mode selection + Name/Description)
 * Step 2: Agent LLM Provider (Primary LLM for the assistant)
 * Step 3: Knowledge Expert Settings (Enable/disable knowledge_expert MCP tool + Vector DB + Enhancement + Reranker)
 * Step 6: Tools & Instructions (Select tools and configure orchestration)
 * Step 7: Review & Create
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
  IconSearch,
  IconTool,
  IconWand
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { ToolInstructionsStep } from './tool-instructions-step';

// ============================================================================
// TYPES & CONSTANTS
// ============================================================================

interface ConversationFormData {
  // Step 0 - Agent Type & Settings
  agentType: 'rag' | 'assistant';
  conversationName: string;
  conversationDescription: string;

  // Step 1 - Enhancement Strategy (RAG mode only)
  selectedStrategy: string;
  selectedProviderId: string | null; // Enhancement LLM provider
  selectedModel: string | null;       // Enhancement LLM model

  // Agent LLM Provider (for Assistant mode - primary LLM powering the agent)
  agentLlmProviderId: string | null;
  agentLlmModel: string | null;

  // Knowledge Expert Settings (Assistant mode - Step 3)
  // When enabled, the agent uses the knowledge_expert MCP tool for RAG-like capabilities
  useKnowledgeExpert: boolean;

  // Vector Database settings (RAG mode always / Assistant mode if Knowledge Expert enabled)
  collectionName: string;
  topK: number;
  // Embedding provider - auto-populated from collection, for consistency and clarity
  embeddingProviderId: string | null;
  embeddingProviderName: string | null;  // Provider name (human-readable) from expanded response
  embeddingModelName: string | null;
  vectorDimension: number;

  // Step 3 - Judge Ranker (RAG) / Part of Knowledge Expert Config (Assistant)
  enableReranking: boolean;
  useAgentLlmAsJudge: boolean;  // Use agent's LLM provider/model for reranking instead of selecting a different one
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
    label: 'Agent LLM Provider',
    description: 'Primary LLM for agent',
    icon: <IconRobot size={20} />,
    color: 'grape',
    gradientFrom: '#a855f7',               // Purple
    gradientTo: LOGO_COLORS.pilot,         // Purple (Pilot)
    assistantModeOnly: true,               // Only show in Assistant mode
  },
  {
    label: 'Knowledge Expert Settings',
    description: 'Configure knowledge search',
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
    description: 'Define assistant behavior and select tools',
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
  const { agentId } = useParams<{ agentId: string }>();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [strategiesInfoModalOpen, setStrategiesInfoModalOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [isLoadingExisting, setIsLoadingExisting] = useState(false);
  const [toolSearchQuery, setToolSearchQuery] = useState('');

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
      agentLlmProviderId: null,
      agentLlmModel: null,
      selectedStrategy: 'native',
      useKnowledgeExpert: false, // Assistant mode: whether to use knowledge_expert MCP tool
      collectionName: '',  // Empty - user must select a collection
      topK: 5,
      embeddingProviderId: null,  // Auto-populated from collection
      embeddingProviderName: null,  // Provider name - auto-populated from collection expand response
      embeddingModelName: null,  // Auto-populated from collection
      vectorDimension: 1536,  // Auto-populated from collection
      enableReranking: false,
      useAgentLlmAsJudge: true,  // Default: use agent's LLM for reranking
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

    // Check for agentId from URL params (e.g., /agents/:agentId/edit)
    if (agentId) {
      setIsEditMode(true);
      setEditingAgentId(agentId);
      // Always reload fresh data when agentId changes
      loadExistingAgent(agentId);
    } else if (state?.editingConversationId) {
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
  }, [agentId]); // Re-run when agentId changes to fetch fresh data

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

  // Sync reranker settings when "Use Agent LLM as Judge" checkbox changes
  useEffect(() => {
    if (form.values.enableReranking && form.values.useAgentLlmAsJudge) {
      // When checkbox is enabled, sync reranker to use agent's LLM
      form.setFieldValue('selectedRerankerId', form.values.agentLlmProviderId);
      form.setFieldValue('selectedRerankerModel', form.values.agentLlmModel);
    }
  }, [form.values.useAgentLlmAsJudge, form.values.enableReranking]);

  // Auto-populate embedding provider details when collection name changes
  // This ensures the UI always shows the correct embedding configuration for the selected collection
  useEffect(() => {
    if (form.values.collectionName && !isLoadingExisting) {
      fetchEmbeddingProviderDetails(form.values.collectionName);
    }
  }, [form.values.collectionName, isLoadingExisting]);

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
          // Auto-populate embedding provider from collection
          if (collection.embedding_model_provider_id) {
            form.setFieldValue('embeddingProviderId', collection.embedding_model_provider_id);
          }
          if (collection.embedding_model_name) {
            form.setFieldValue('embeddingModelName', collection.embedding_model_name);
          }
          if (collection.vector_dimension) {
            form.setFieldValue('vectorDimension', collection.vector_dimension);
          }
        }
      } else {
        console.error('[ERROR] Failed to fetch collection:', response.status);
      }
    } catch (error) {
      console.error('[ERROR] Error fetching collection:', error);
    }
  };

  // Fetch and populate embedding provider details for a collection by name
  // This is automatically called when collection name changes to ensure UI always shows correct embedding config
  const fetchEmbeddingProviderDetails = async (collectionName: string) => {
    try {
      const token = localStorage.getItem('jwt_token');

      // Call the API with expand=embedding_provider to get full provider details
      // Use the collection name as query parameter
      const response = await fetch(
        apiUtils.buildApiUrl(`/knowledge/vectordb-collections/?name=${encodeURIComponent(collectionName)}&expand=embedding_provider`),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('[DEBUG] Collection embedding details response:', data);

        // The response should have embedding details at top level or in expanded provider
        if (data && data.collection_name && data.embedding_model_provider_id) {
          // Update form with embedding details
          form.setFieldValue('embeddingProviderId', data.embedding_model_provider_id);
          // Extract provider name from expanded provider object, or fallback to ID
          const providerName = data.embedding_provider?.name || data.embedding_model_provider_id;
          form.setFieldValue('embeddingProviderName', providerName);
          form.setFieldValue('embeddingModelName', data.embedding_model_name || '');
          form.setFieldValue('vectorDimension', data.vector_dimension || 1536);

          console.log('[DEBUG] Populated embedding details:', {
            providerId: data.embedding_model_provider_id,
            providerName: providerName,
            modelName: data.embedding_model_name,
            dimension: data.vector_dimension,
          });
        }
      } else {
        console.warn('[WARN] Failed to fetch collection embedding details:', response.status);
      }
    } catch (error) {
      console.error('[ERROR] Error fetching embedding provider details:', error);
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
          // Load primary agent LLM provider (may be null for legacy conversations)
          agentLlmProviderId: session.llm_provider?.id || null,
          agentLlmModel: session.llm_provider?.model_name || null,
          // Load enhancement LLM provider/model
          selectedProviderId: session.enhancement?.provider?.id || null,
          selectedModel: session.enhancement?.provider?.model_name || null,
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

  // Load existing agent data for edit mode (when navigating from /agents/:agentId/edit)
  const loadExistingAgent = async (agentId: string) => {
    try {
      setIsLoadingExisting(true);
      const token = localStorage.getItem('jwt_token');
      // Add timestamp to bust cache and ensure fresh data
      // Expand all nested objects for complete data
      const expandParams = 'expand=tools,enhancement,reranker,answer_generation,llm_provider';
      const response = await fetch(apiUtils.buildApiUrl(`/agents/${agentId}?${expandParams}&t=${Date.now()}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
        },
      });

      if (response.ok) {
        const agent = await response.json();

        console.log('[DEBUG loadExistingAgent] Full agent object:', JSON.stringify(agent, null, 2));

        const isAssistantMode = agent.agent_type === 'assistant';

        // With expand=tools, assistant_config.tools contains full tool objects
        // Extract tool IDs for the form (selectedTools expects IDs)
        const agentToolObjects = agent.assistant_config?.tools || [];
        const agentToolIds = agentToolObjects.map((t: any) => typeof t === 'string' ? t : t.id);

        // For Assistant mode: Determine if Knowledge Expert is enabled
        // Check multiple indicators:
        // 1. If vector_database is configured (most reliable - data in DB)
        // 2. OR if knowledge_expert tool is in the agent's tools (check by name from expanded objects)
        const hasVectorDbConfig = !!(agent.vector_database?.collection_name);
        let hasKnowledgeExpertTool = false;
        if (isAssistantMode && agentToolObjects.length > 0) {
          // With expanded tools, we can check directly by name
          hasKnowledgeExpertTool = agentToolObjects.some((t: any) => {
            const toolName = typeof t === 'string' ? null : t.name;
            return toolName === 'knowledge_expert';
          });
        }

        // Enable Knowledge Expert if EITHER vector_database is configured OR knowledge_expert tool is bound
        const shouldEnableKnowledgeExpert = isAssistantMode && (hasVectorDbConfig || hasKnowledgeExpertTool);

        console.log('[DEBUG loadExistingAgent] hasVectorDbConfig:', hasVectorDbConfig);
        console.log('[DEBUG loadExistingAgent] hasKnowledgeExpertTool:', hasKnowledgeExpertTool);
        console.log('[DEBUG loadExistingAgent] shouldEnableKnowledgeExpert:', shouldEnableKnowledgeExpert);
        console.log('[DEBUG loadExistingAgent] agentToolIds:', agentToolIds);

        // Populate form with existing agent data
        form.setValues({
          agentType: isAssistantMode ? 'assistant' : 'rag',
          conversationName: agent.name || '',
          conversationDescription: agent.description || '',
          // Load primary agent LLM provider
          agentLlmProviderId: agent.llm_provider?.id || null,
          agentLlmModel: agent.llm_provider?.model_name || null,
          // Load enhancement LLM provider/model - for RAG query enhancement
          selectedProviderId: agent.enhancement?.provider?.id || null,
          selectedModel: agent.enhancement?.provider?.model_name || null,
          selectedStrategy: agent.enhancement?.strategy || 'native',
          // Knowledge Expert toggle for Assistant mode
          useKnowledgeExpert: shouldEnableKnowledgeExpert,
          collectionName: agent.vector_database?.collection_name || '',
          topK: agent.vector_database?.top_k || 5,
          // Embedding provider - loaded from agent's vector database config
          embeddingProviderId: agent.vector_database?.embedding_provider?.id || null,
          embeddingProviderName: agent.vector_database?.embedding_provider?.name || null,
          embeddingModelName: agent.vector_database?.embedding_provider?.model_name || null,
          vectorDimension: agent.vector_database?.vector_dimension || 1536,
          enableReranking: agent.reranker?.enabled || false,
          useAgentLlmAsJudge: agent.reranker?.provider?.id === agent.llm_provider?.id && agent.reranker?.provider?.model_name === agent.llm_provider?.model_name,
          relevanceThreshold: agent.reranker?.relevance_threshold || 0.5,
          selectedRerankerId: agent.reranker?.provider?.id || null,
          selectedRerankerModel: agent.reranker?.provider?.model_name || null,
          enableLLMGeneration: agent.answer_generation?.enabled || false,
          enableKnowledgeAssistant: agent.assistant_config?.enabled || false,
          selectedTools: agentToolIds,
          instructions: agent.assistant_config?.instructions || '',
        });

        console.log('[DEBUG loadExistingAgent] form.values after setValues');
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to load agent',
          color: 'red',
        });
        navigate(paths.dashboard.apps.agents);
      }
    } catch (error) {
      console.error('Error loading agent:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to load agent',
        color: 'red',
      });
      navigate(paths.dashboard.apps.agents);
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
        // Enhancement Strategy - just need to select a strategy
        // For RAG: uses agent's primary LLM (selected in step 2), so no separate provider validation needed
        // For Assistant: this step is skipped (goes to step 2 instead)
        return !!form.values.selectedStrategy;
      case 2:
        // Agent LLM Provider - provider & model required for both RAG and Assistant modes
        return !!form.values.agentLlmProviderId && !!form.values.agentLlmModel;
      case 3:
        // Knowledge Expert Settings
        // For Assistant mode: if useKnowledgeExpert is disabled, no validation needed
        if (form.values.agentType === 'assistant') {
          if (!form.values.useKnowledgeExpert) {
            return true; // No validation needed if Knowledge Expert is disabled
          }
          // Validate vector DB settings
          if (!form.values.collectionName || form.values.topK < 5) {
            return false;
          }
          // Enhancement strategy uses agent's primary LLM for Assistant mode, so no separate provider validation needed
          // Validate reranker if enabled
          if (form.values.enableReranking) {
            // Reranker validation depends on whether using agent LLM or custom provider
            if (!form.values.useAgentLlmAsJudge) {
              // Only validate if NOT using agent LLM
              if (!form.values.selectedRerankerId || !form.values.selectedRerankerModel) {
                return false;
              }
            }
            // If using agent LLM, validation is automatic (inherited from agent's LLM)
          }
          return true;
        }
        // RAG mode: always require collection and topK
        return !!form.values.collectionName && form.values.topK >= 5;
      case 4:
        // Judge Ranker - only for RAG mode, all optional
        if (form.values.agentType === 'assistant') {
          return true; // Skip validation for assistant mode
        }
        return true;
      case 5:
        // Generative Answer - only for RAG mode
        // Uses agent's primary LLM for generation, so no separate provider validation needed
        if (form.values.agentType === 'assistant') {
          return true; // Skip validation for assistant mode
        }
        return true; // No validation needed - uses agent's primary LLM
      case 6:
        // Tools & Instructions - only for Assistant mode, always valid
        return true;
      case 7:
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

    // Determine next step based on agent type
    // STEP indices: 0=AgentType, 1=Enhancement, 2=AgentLLM, 3=VectorDB, 4=JudgeRanker, 5=GenerativeAnswer, 6=Tools, 7=Review
    let nextStep = activeStep + 1;

    if (form.values.agentType === 'rag') {
      // RAG mode: Order is 0,2,1,3,4,5,7 (Agent LLM before Enhancement)
      if (activeStep === 0) {
        nextStep = 2; // Agent Type -> Agent LLM Provider
      } else if (activeStep === 2) {
        nextStep = 1; // Agent LLM Provider -> Enhancement Strategy
      } else if (activeStep === 1) {
        nextStep = 3; // Enhancement Strategy -> Vector Database
      } else if (activeStep === 5) {
        nextStep = 7; // Generative Answer -> Review (skip Tools)
      } else {
        nextStep = activeStep + 1; // 3->4, 4->5
      }
    } else {
      // Assistant mode: Skip Step 1 (Enhancement), Step 4 (Judge Ranker), Step 5 (Generative Answer)
      if (activeStep === 0) {
        nextStep = 2; // Skip Enhancement Strategy, go to Agent LLM Provider
      } else if (activeStep === 3) {
        nextStep = 6; // Skip Judge Ranker and Generative Answer, go to Tools & Instructions
      } else if (activeStep === 6) {
        nextStep = 7; // Go to Review & Create
      }
    }

    setActiveStep(nextStep);
  };

  const handlePreviousStep = () => {
    if (activeStep > 0) {
      let prevStep = activeStep - 1;

      // STEP indices: 0=AgentType, 1=Enhancement, 2=AgentLLM, 3=VectorDB, 4=JudgeRanker, 5=GenerativeAnswer, 6=Tools, 7=Review
      if (form.values.agentType === 'rag') {
        // RAG mode: Order is 0,2,1,3,4,5,7 (Agent LLM before Enhancement)
        if (activeStep === 2) {
          prevStep = 0; // Agent LLM Provider -> Agent Type
        } else if (activeStep === 1) {
          prevStep = 2; // Enhancement Strategy -> Agent LLM Provider
        } else if (activeStep === 3) {
          prevStep = 1; // Vector Database -> Enhancement Strategy
        } else if (activeStep === 7) {
          prevStep = 5; // Review -> Generative Answer (skip Tools)
        } else {
          prevStep = activeStep - 1; // 5->4, 4->3
        }
      } else {
        // Assistant mode: Skip Step 1 (Enhancement), Step 4 and 5 when going back
        if (activeStep === 2) {
          prevStep = 0; // Skip from Agent LLM Provider back to Agent Type
        } else if (activeStep === 6) {
          prevStep = 3; // Skip from Tools & Instructions back to Vector Database
        } else if (activeStep === 7) {
          prevStep = 6; // From Review & Create back to Tools & Instructions
        }
      }

      setActiveStep(prevStep);
    }
  };

  const handleStepClick = (displayStepIndex: number) => {
    // Map display step index back to actual step index based on agent type
    // STEP indices: 0=AgentType, 1=Enhancement, 2=AgentLLM, 3=VectorDB, 4=JudgeRanker, 5=GenerativeAnswer, 6=Tools, 7=Review
    const getActualStep = (displayStep: number): number => {
      if (form.values.agentType === 'rag') {
        // RAG mode: display 0,1,2,3,4,5,6 -> actual 0,2,1,3,4,5,7 (Agent LLM before Enhancement)
        if (displayStep === 0) return 0; // Agent Type
        if (displayStep === 1) return 2; // Agent LLM Provider
        if (displayStep === 2) return 1; // Enhancement Strategy
        if (displayStep === 3) return 3; // Vector Database
        if (displayStep === 4) return 4; // Judge Ranker
        if (displayStep === 5) return 5; // Generative Answer
        if (displayStep === 6) return 7; // Review & Create
        return displayStep;
      } else {
        // Assistant mode: display 0,1,2,3,4 -> actual 0,2,3,6,7 (skip step 1 Enhancement)
        if (displayStep === 0) return 0;
        if (displayStep === 1) return 2; // Agent LLM Provider
        if (displayStep === 2) return 3; // Vector Database
        if (displayStep === 3) return 6; // Tools & Instructions
        if (displayStep === 4) return 7; // Review & Create
        return displayStep;
      }
    };

    const step = getActualStep(displayStepIndex);

    // In edit mode, allow free navigation between any steps
    if (isEditMode) {
      setActiveStep(step);
      return;
    }

    // In create mode, enforce sequential validation
    // Allow going back to any previous step
    if (step < activeStep) {
      setActiveStep(step);
      return;
    }

    // Allow clicking immediate next step (validate current step first)
    // Check for skip steps based on mode
    const isNextStep = (form.values.agentType === 'rag' && activeStep === 5 && step === 7) || // RAG: Skip Tools
      (form.values.agentType === 'assistant' && activeStep === 0 && step === 2) || // Assistant: Skip Enhancement
      (form.values.agentType === 'assistant' && activeStep === 3 && step === 6) || // Assistant: Skip Judge/Gen
      (form.values.agentType === 'assistant' && activeStep === 6 && step === 7) || // Assistant: Tools to Review
      (step === activeStep + 1);

    if (isNextStep) {
      if (validateStep(activeStep)) {
        setCompletedSteps((prev) => [...new Set([...prev, activeStep])]);
        setActiveStep(step);
      } else {
        notifications.show({
          title: 'Validation Error',
          message: 'Please fill in required fields before proceeding',
          color: 'red',
        });
      }
      return;
    }

    // Allow revisiting completed steps
    if (completedSteps.includes(step)) {
      setActiveStep(step);
      return;
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

      // Determine if Knowledge Expert is being used (RAG always uses it, Assistant only if enabled)
      const isAssistantMode = form.values.agentType === 'assistant';
      const useKnowledgeExpert = isAssistantMode ? form.values.useKnowledgeExpert : true;

      const payload: any = {
        name: form.values.conversationName.trim(),
        description: form.values.conversationDescription.trim() || null,
        // Primary Agent LLM Provider (for both RAG and Assistant modes)
        llm_provider: form.values.agentLlmProviderId && form.values.agentLlmModel ? {
          id: form.values.agentLlmProviderId,
          model_name: form.values.agentLlmModel,
        } : null,
        // Enhancement configuration - only if Knowledge Expert is used
        // For Assistant mode: always use custom_variants strategy
        // For RAG mode: use the selected strategy
        // Note: Provider is NOT sent - uses the agent's primary LLM provider instead
        enhancement_strategy: useKnowledgeExpert ? (isAssistantMode ? 'custom_variants' : form.values.selectedStrategy) : 'native',
        // Vector database configuration - only if Knowledge Expert is used
        vector_database: useKnowledgeExpert ? {
          collection_name: form.values.collectionName,
          top_k: form.values.topK,
          // Embedding provider - auto-populated from collection, ensures query embeddings match document embeddings
          embedding_provider: form.values.embeddingProviderId && form.values.embeddingModelName ? {
            id: form.values.embeddingProviderId,
            model_name: form.values.embeddingModelName,
          } : null,
          // Vector dimension - must match the collection's embeddings
          vector_dimension: form.values.vectorDimension,
        } : null,
        // Reranker configuration - only if Knowledge Expert is used
        reranker: useKnowledgeExpert ? {
          enabled: form.values.enableReranking,
          provider: form.values.enableReranking && form.values.selectedRerankerId && form.values.selectedRerankerModel ? {
            id: form.values.selectedRerankerId,
            model_name: form.values.selectedRerankerModel,
          } : null,
          relevance_threshold: form.values.relevanceThreshold,
        } : null,
        // Answer generation configuration - only for RAG mode
        // Note: Provider is NOT sent - uses the agent's primary LLM provider instead
        is_llm_generation_enabled: !isAssistantMode ? form.values.enableLLMGeneration : false,
        // Complex nested assistant configuration
        // RAG mode: assistant_config = { enabled: false, tools: [] }
        // Assistant mode: assistant_config = { enabled: true, tools: [...tool_ids], instructions: "..." }
        assistant_config: {
          enabled: isAssistantMode,
          tools: isAssistantMode ? form.values.selectedTools : [],
          instructions: isAssistantMode ? form.values.instructions : null,
        },
      };

      // For Assistant mode: If Knowledge Expert is enabled, ensure knowledge_expert tool is included
      if (isAssistantMode && useKnowledgeExpert && tools && Array.isArray(tools)) {
        const knowledgeExpertTool = tools.find((t: any) => t.name === 'knowledge_expert');
        if (knowledgeExpertTool && !payload.assistant_config.tools.includes(knowledgeExpertTool.id)) {
          payload.assistant_config.tools = [...payload.assistant_config.tools, knowledgeExpertTool.id];
        }
      }

      // Deduplicate tools before sending to prevent duplicate IDs
      const uniqueTools = payload.assistant_config.tools
        ? Array.from(new Set(payload.assistant_config.tools))
        : [];
      payload.assistant_config.tools = uniqueTools;

      console.log('✅ FRONTEND: assistant_config in payload:', {
        enabled: payload.assistant_config.enabled,
        tools: payload.assistant_config.tools,
        tools_count: payload.assistant_config.tools?.length || 0,
        original_count: form.values.selectedTools?.length || 0,
        duplicates_removed: (form.values.selectedTools?.length || 0) - uniqueTools.length,
      });

      console.log('✅ FRONTEND: form.values.selectedTools:', form.values.selectedTools);
      console.log('✅ FRONTEND: isEditMode:', isEditMode);
      console.log('✅ FRONTEND: editingAgentId:', editingAgentId);

      // Determine endpoint and method based on edit mode type
      let url: string;
      let method: string;

      if (editingAgentId) {
        // Editing an existing agent
        url = apiUtils.buildApiUrl(`/agents/${editingAgentId}`);
        method = 'PUT';
      } else if (editingConversationId) {
        // Editing an existing conversation (legacy)
        url = apiUtils.buildApiUrl(`/conversations/${editingConversationId}`);
        method = 'PUT';
      } else {
        // Creating a new agent
        url = apiUtils.buildApiUrl('/agents');
        method = 'POST';
      }

      console.log('✅ FRONTEND: Full payload being sent:', JSON.stringify(payload, null, 2));

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

        if (editingAgentId) {
          // After editing agent, go back to agent's conversations
          notifications.show({
            title: 'Success',
            message: 'Agent updated successfully',
            color: 'green',
            icon: <IconCheck size={16} />,
          });
          navigate(paths.dashboard.apps.agentConversations(editingAgentId));
        } else {
          // After creating new agent or editing conversation
          const sessionId = editingConversationId || data.id;
          notifications.show({
            title: 'Success',
            message: isEditMode ? 'Conversation updated successfully' : 'Agent created successfully',
            color: 'green',
            icon: <IconCheck size={16} />,
          });
          navigate(paths.dashboard.apps.conversation(sessionId));
        }
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
  // STEP_CONFIGS indices: 0=AgentType, 1=Enhancement, 2=AgentLLM, 3=VectorDB, 4=JudgeRanker, 5=GenerativeAnswer, 6=Tools, 7=Review
  // RAG mode: exclude Step 6 (Tools & Instructions) only, and reorder: Agent LLM (2) comes before Enhancement (1)
  // Assistant mode: exclude Step 1 (Enhancement Strategy - fixed to custom_variants), Step 4 (Judge Ranker), Step 5 (Generative Answer)
  const visibleSteps = useMemo(() => {
    const isRagMode = form.values.agentType === 'rag';
    let filteredSteps: typeof STEP_CONFIGS;

    if (isRagMode) {
      // RAG mode: Remove Tools, then reorder: 0,2,1,3,4,5,7 (Agent LLM before Enhancement)
      filteredSteps = STEP_CONFIGS.filter((_, index) => index !== 6);
      // Reorder: swap step 1 (Enhancement) and step 2 (Agent LLM)
      const reordered = [...filteredSteps];
      [reordered[1], reordered[2]] = [reordered[2], reordered[1]];
      filteredSteps = reordered;
    } else {
      // Assistant mode: Remove Enhancement, Judge Ranker, Generative Answer
      filteredSteps = STEP_CONFIGS.filter((_, index) => index !== 1 && index !== 4 && index !== 5);
    }

    // Update step labels based on agent type
    // Step 3 in STEP_CONFIGS = "Knowledge Expert Settings" for Assistant, "Vector Database" for RAG
    return filteredSteps.map((step) => {
      if (step.label === 'Knowledge Expert Settings' && isRagMode) {
        return { ...step, label: 'Vector Database', description: 'Configure vector database' };
      }
      return step;
    });
  }, [form.values.agentType]);

  // Adjust activeStep display for stepper component based on filtered steps
  // Map actual step indices to display indices based on agent type
  const getDisplayStep = (actualStep: number): number => {
    if (form.values.agentType === 'rag') {
      // RAG mode: 0,2,1,3,4,5,7 -> display as 0,1,2,3,4,5,6 (Agent LLM before Enhancement)
      if (actualStep === 0) return 0; // Agent Type
      if (actualStep === 2) return 1; // Agent LLM Provider
      if (actualStep === 1) return 2; // Enhancement Strategy
      if (actualStep === 3) return 3; // Vector Database
      if (actualStep === 4) return 4; // Judge Ranker
      if (actualStep === 5) return 5; // Generative Answer
      if (actualStep === 7) return 6; // Review & Create
      return actualStep;
    } else {
      // Assistant mode: 0,2,3,6,7 -> display as 0,1,2,3,4
      if (actualStep === 0) return 0;
      if (actualStep === 2) return 1; // Agent LLM Provider
      if (actualStep === 3) return 2; // Vector Database
      if (actualStep === 6) return 3; // Tools & Instructions
      if (actualStep === 7) return 4; // Review & Create
      return actualStep;
    }
  };

  const displayActiveStep = getDisplayStep(activeStep);

  const pageTitle = editingAgentId
    ? 'Edit Agent'
    : isEditMode
      ? 'Edit Conversation Agent'
      : 'Create New Agent';

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

        {/* STEP 1: ENHANCEMENT STRATEGY (RAG mode only) */}
        {form.values.agentType === 'rag' && activeStep === 1 && (
          <StepEnhancementStrategy
            form={form}
            onLearnClick={() => setStrategiesInfoModalOpen(true)}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 2: AGENT LLM PROVIDER (Both RAG and Assistant modes) */}
        {activeStep === 2 && (
          <StepAgentLlmProvider
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 3: KNOWLEDGE EXPERT SETTINGS (Vector DB + Enhancement + Reranker for Assistant) */}
        {activeStep === 3 && (
          <StepKnowledgeExpertSettings
            form={form}
            collections={collections}
            collectionsLoading={collectionsLoading}
            providers={providers}
            providersLoading={providersLoading}
            tools={tools && Array.isArray(tools) ? tools : []}
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

        {/* STEP 5: GENERATIVE ANSWER */}
        {activeStep === 5 && (
          <StepAdvancedSettings
            form={form}
            providers={providers}
            providersLoading={providersLoading}
          />
        )}

        {/* STEP 6: TOOLS & INSTRUCTIONS (Assistant mode only) */}
        {form.values.agentType === 'assistant' && activeStep === 6 && (
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
                    <Group justify="space-between" align="center">
                      <Text size="sm" fw={500}>
                        Available Tools ({tools?.filter((t: any) => t.is_active).length || 0} active)
                      </Text>
                    </Group>
                    <TextInput
                      placeholder="Search tools by name, description, or tags..."
                      leftSection={<IconSearch size={16} />}
                      value={toolSearchQuery}
                      onChange={(e) => setToolSearchQuery(e.currentTarget.value)}
                      mb="sm"
                    />
                    <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '8px' }}>
                      <Stack gap="md">
                        {(() => {
                          // Filter active tools, and exclude knowledge_expert if not enabled
                          const activeTools = tools?.filter((t: any) => {
                            if (!t.is_active) return false;
                            // Exclude knowledge_expert tool if Knowledge Expert is disabled
                            if (!form.values.useKnowledgeExpert && t.name === 'knowledge_expert') return false;
                            return true;
                          }) || [];
                          const searchLower = toolSearchQuery.toLowerCase().trim();

                          // Helper function to check if tool matches search
                          const matchesSearch = (tool: any) => {
                            if (!searchLower) return true;
                            const name = (tool.name || '').toLowerCase();
                            const displayName = (tool.display_name || '').toLowerCase();
                            const description = (tool.description || '').toLowerCase();
                            const tags = (tool.tags || []).map((tag: string) => tag.toLowerCase()).join(' ');
                            return (
                              name.includes(searchLower) ||
                              displayName.includes(searchLower) ||
                              description.includes(searchLower) ||
                              tags.includes(searchLower)
                            );
                          };

                          const filteredTools = searchLower
                            ? activeTools.filter(matchesSearch)
                            : activeTools;

                          if (filteredTools.length === 0 && searchLower) {
                            return (
                              <Alert icon={<IconAlertCircle size={16} />} color="yellow" variant="light">
                                <Text size="sm">No tools found matching "{toolSearchQuery}"</Text>
                              </Alert>
                            );
                          }

                          return filteredTools.map((tool: any) => (
                            <Card key={tool.id} withBorder p="sm" style={{ cursor: 'pointer' }} onClick={() => {
                              const currentTools = form.values.selectedTools || [];
                              const isSelected = currentTools.includes(tool.id);
                              const newTools = isSelected
                                ? currentTools.filter((id: string) => id !== tool.id)
                                : [...currentTools, tool.id];

                              // Deduplicate to prevent duplicate tool IDs
                              const uniqueTools = Array.from(new Set(newTools));

                              form.setFieldValue('selectedTools', uniqueTools);
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
                          ));
                        })()}
                      </Stack>
                    </div>
                    {toolSearchQuery && (
                      <Text size="xs" c="dimmed">
                        {(() => {
                          // Filter active tools, and exclude knowledge_expert if not enabled
                          const activeTools = tools?.filter((t: any) => {
                            if (!t.is_active) return false;
                            // Exclude knowledge_expert tool if Knowledge Expert is disabled
                            if (!form.values.useKnowledgeExpert && t.name === 'knowledge_expert') return false;
                            return true;
                          }) || [];
                          const searchLower = toolSearchQuery.toLowerCase().trim();
                          const filteredCount = searchLower
                            ? activeTools.filter((t: any) => {
                              const name = (t.name || '').toLowerCase();
                              const displayName = (t.display_name || '').toLowerCase();
                              const description = (t.description || '').toLowerCase();
                              const tags = (t.tags || []).map((tag: string) => tag.toLowerCase()).join(' ');
                              return (
                                name.includes(searchLower) ||
                                displayName.includes(searchLower) ||
                                description.includes(searchLower) ||
                                tags.includes(searchLower)
                              );
                            }).length
                            : activeTools.length;
                          return `Showing ${filteredCount} of ${activeTools.length} tools`;
                        })()}
                      </Text>
                    )}
                  </Stack>
                )}

                {(() => {
                  // Deduplicate tools for display to show accurate count
                  const uniqueToolCount = form.values.selectedTools
                    ? Array.from(new Set(form.values.selectedTools)).length
                    : 0;

                  return uniqueToolCount > 0 && (
                    <Alert icon={<IconCheck size={16} />} color="blue" variant="light">
                      <Text size="sm">{uniqueToolCount} tool(s) selected</Text>
                    </Alert>
                  );
                })()}
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

        {/* STEP 7: REVIEW & CREATE (actual step 7 for both modes) */}
        {activeStep === 7 && (
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
              onClick={() => navigate(paths.dashboard.apps.agents)}
              disabled={isCreating}
            >
              Cancel
            </Button>

            {(() => {
              // Determine if we should show "Next" or final action button
              // RAG: steps 0,1,3,4,5 show "Next", step 7 (Review) shows "Create/Update"
              // Assistant: steps 0,2,3,6 show "Next", step 7 (Review) shows "Create/Update"
              const isLastStep = activeStep >= 7; // Both modes end at step 7 (Review & Create)

              return isLastStep ? (
                <Button
                  onClick={handleCreateConversation}
                  loading={isCreating}
                  leftSection={<IconCheck size={16} />}
                  color="green"
                >
                  {isEditMode ? 'Update Conversation Agent' : 'Create Conversation Agent'}
                </Button>
              ) : (
                <Button
                  onClick={handleNextStep}
                  disabled={isCreating}
                  color="blue"
                >
                  Next
                </Button>
              );
            })()}
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


      </div>

      {/* Conversation Settings */}
      <Divider label="Conversation Details" labelPosition="center" />
      <div>
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

function StepKnowledgeExpertSettings({ form, collections, collectionsLoading, providers, providersLoading, tools }: StepProps & { providers?: any; providersLoading?: boolean; tools?: any[] }) {
  const isAssistantMode = form.values.agentType === 'assistant';

  return (
    <Stack gap="md">
      {/* For Assistant mode: Show checkbox to enable Knowledge Expert */}
      {isAssistantMode && (
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light">
            <Text size="sm">
              Enable <strong>Knowledge Expert</strong> to give your assistant access to a vector database for retrieving relevant documents.
              This uses the <code>knowledge_expert</code> MCP tool under the hood.
            </Text>
          </Alert>

          <Switch
            label="Enable Knowledge Expert (RAG capabilities)"
            description="Allow the assistant to search and retrieve from your knowledge base"
            checked={form.values.useKnowledgeExpert}
            onChange={(event) => {
              const enabled = event.currentTarget.checked;
              form.setFieldValue('useKnowledgeExpert', enabled);

              // If disabling Knowledge Expert, remove knowledge_expert tool from selected tools
              if (!enabled && form.values.selectedTools?.includes('knowledge_expert')) {
                // Also check by tool name in case ID is different
                const currentTools = form.values.selectedTools || [];
                const filteredTools = currentTools.filter((toolId: string) => {
                  const tool = tools?.find((t: any) => t.id === toolId);
                  return tool?.name !== 'knowledge_expert';
                });
                form.setFieldValue('selectedTools', filteredTools);
              }
            }}
            size="md"
          />
        </>
      )}

      {/* For RAG mode: Always show vector DB config */}
      {/* For Assistant mode: Only show if Knowledge Expert is enabled */}
      {(!isAssistantMode || form.values.useKnowledgeExpert) && (
        <>
          {isAssistantMode && <Divider my="sm" label="Vector Database Configuration" labelPosition="center" />}

          {!isAssistantMode && (
            <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
              <Text size="sm">
                Select the knowledge base collection you want to search from. Configure how many relevant documents to retrieve.
              </Text>
            </Alert>
          )}

          <Grid gutter="md">
            <Grid.Col span={6}>
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
                onChange={(value) => {
                  // Update collection name
                  // The useEffect hook will automatically fetch and populate embedding details
                  form.setFieldValue('collectionName', value || '');
                }}
                searchable
                disabled={collectionsLoading}
                required
                description="Knowledge base to search from"
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <NumberInput
                label="Search Results Limit (Top K)"
                placeholder="Number of documents"
                {...form.getInputProps('topK')}
                min={5}
                max={30}
                required
                description="Documents to retrieve (5-30)"
              />
            </Grid.Col>
          </Grid>

          {/* Embedding Provider Information - ALWAYS shown, derived from collection */}
          <Divider my="md" />
          <Alert
            icon={<IconDatabase size={16} />}
            color={form.values.embeddingProviderId ? "teal" : "gray"}
            variant="light"
          >
            <Stack gap="xs">
              <Group justify="space-between">
                <Text fw={600} size="sm">Query Embedding Configuration</Text>
                <Badge
                  size="sm"
                  color={form.values.embeddingProviderId ? "teal" : "gray"}
                >
                  {form.values.collectionName ? 'Derived from Collection' : 'Select collection to populate'}
                </Badge>
              </Group>
              <Text size="sm" c="dimmed">
                {form.values.collectionName
                  ? 'Your queries will be embedded using the same model as your vector database collection to ensure accurate retrieval.'
                  : 'Select a vector database collection above to see its embedding configuration.'}
              </Text>

              {form.values.collectionName && (
                <Group gap="md" mt="xs">
                  <div>
                    <Text size="xs" fw={500} c="dark">Embedding Provider</Text>
                    <Text size="sm" fw={600}>
                      {form.values.embeddingProviderName || '⏳ Loading...'}
                    </Text>
                  </div>
                  <div>
                    <Text size="xs" fw={500} c="dark">Embedding Model</Text>
                    <Text size="sm" fw={600}>
                      {form.values.embeddingModelName || '⏳ Loading...'}
                    </Text>
                  </div>
                  <div>
                    <Text size="xs" fw={500} c="dark">Vector Dimension</Text>
                    <Text size="sm" fw={600}>
                      {form.values.vectorDimension || 1536}
                    </Text>
                  </div>
                </Group>
              )}
            </Stack>
          </Alert>

          {/* Enhancement Strategy for Assistant mode - locked to custom_variants */}
          {isAssistantMode && (
            <>
              <Divider my="sm" label="Query Enhancement" labelPosition="center" />
              <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light" mb="sm">
                <Text size="sm">
                  Assistant mode uses <strong>Custom Variants</strong> strategy for query enhancement.
                  This generates intelligent query variations to improve search results.
                </Text>
              </Alert>
              <Select
                label="Enhancement Strategy"
                value="custom_variants"
                data={[{
                  value: 'custom_variants',
                  label: 'Custom Variants (Fixed for Assistant)',
                }]}
                disabled
                description="Strategy is fixed to Custom Variants for Assistant mode"
              />

              {/* Enhancement LLM - uses agent's primary LLM */}
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Stack gap="xs">
                  <Text size="sm" fw={600}>Query Enhancement LLM</Text>
                  <Group gap="md">
                    <div>
                      <Text size="xs" fw={500} c="dark">Provider</Text>
                      <Text size="sm">{providers?.find((p: any) => p.id === form.values.agentLlmProviderId)?.name || form.values.agentLlmProviderId || 'Not selected'}</Text>
                    </div>
                    <div>
                      <Text size="xs" fw={500} c="dark">Model</Text>
                      <Text size="sm">{form.values.agentLlmModel || 'Not selected'}</Text>
                    </div>
                  </Group>
                  <Text size="xs" c="dimmed">The agent's primary LLM is used to generate query variants for more comprehensive search results.</Text>
                </Stack>
              </Alert>
            </>
          )}

          {/* Reranker Configuration for Assistant mode */}
          {isAssistantMode && (
            <>
              <Divider my="sm" label="Reranker Configuration" labelPosition="center" />
              <Switch
                label="Enable Reranking"
                description="Use an LLM to re-rank retrieved documents by relevance"
                {...form.getInputProps('enableReranking', { type: 'checkbox' })}
              />

              {form.values.enableReranking && (
                <>
                  <Switch
                    label="Use Agent LLM as Judge"
                    description="Use the same LLM provider and model as the agent for reranking"
                    {...form.getInputProps('useAgentLlmAsJudge', { type: 'checkbox' })}
                    mb="md"
                  />

                  {form.values.useAgentLlmAsJudge && (
                    <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light" mb="md">
                      <Stack gap="xs">
                        <Text size="sm" fw={600}>Reranker Configuration</Text>
                        <Group gap="md">
                          <div>
                            <Text size="xs" fw={500} c="dark">Provider</Text>
                            <Text size="sm">{providers?.find((p: any) => p.id === form.values.agentLlmProviderId)?.name || form.values.agentLlmProviderId || 'Not selected'}</Text>
                          </div>
                          <div>
                            <Text size="xs" fw={500} c="dark">Model</Text>
                            <Text size="sm">{form.values.agentLlmModel || 'Not selected'}</Text>
                          </div>
                        </Group>
                        <Text size="xs" c="dimmed">Using the agent's LLM for reranking ensures consistent evaluation of document relevance.</Text>
                      </Stack>
                    </Alert>
                  )}

                  {!form.values.useAgentLlmAsJudge && (
                    <>
                      <Grid gutter="md">
                        <Grid.Col span={6}>
                          <Select
                            label="Reranker LLM Provider"
                            placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
                            data={
                              providers?.map((p: any) => ({
                                value: p.id,
                                label: `${p.name} (${p.provider_type})`,
                              })) || []
                            }
                            {...form.getInputProps('selectedRerankerId')}
                            searchable
                            disabled={providersLoading}
                            required
                            description="LLM for reranking documents"
                          />
                        </Grid.Col>
                        <Grid.Col span={6}>
                          {form.values.selectedRerankerId && providers ? (
                            <Select
                              label="Reranker Model"
                              placeholder="Select a model"
                              data={
                                providers
                                  .find((p: any) => p.id === form.values.selectedRerankerId)
                                  ?.generative?.models
                                  .filter((m: string) => {
                                    // Exclude the agent's model if same provider is selected
                                    if (form.values.selectedRerankerId === form.values.agentLlmProviderId && m === form.values.agentLlmModel) {
                                      return false;
                                    }
                                    return true;
                                  })
                                  .map((m: string) => ({
                                    value: m,
                                    label: m,
                                  })) || []
                              }
                              {...form.getInputProps('selectedRerankerModel')}
                              searchable
                              required
                              description={`Provider: ${providers.find((p: any) => p.id === form.values.selectedRerankerId)?.name || 'Unknown'}`}
                            />
                          ) : (
                            <Select
                              label="Reranker Model"
                              placeholder="Select provider first"
                              disabled
                              required
                              description="Select a provider first"
                            />
                          )}
                        </Grid.Col>
                      </Grid>
                    </>
                  )}

                  <NumberInput
                    label="Relevance Threshold"
                    placeholder="Minimum relevance score"
                    min={0}
                    max={1}
                    step={0.05}
                    {...form.getInputProps('relevanceThreshold')}
                    description="Minimum relevance score (0-1) for filtering documents"
                  />
                </>
              )}
            </>
          )}

          {/* Enhancement Strategy Info for RAG mode */}
          {!isAssistantMode && form.values.selectedStrategy !== 'native' &&
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

          {!isAssistantMode && form.values.selectedStrategy === 'hyde' && (
            <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
              <Text size="xs">
                <strong>{ENHANCEMENT_STRATEGIES.find((s) => s.value === 'hyde')?.label}:</strong> This strategy generates one enhanced query variant.
                The system will search using this single enhanced query (no RRF merging needed).
              </Text>
            </Alert>
          )}
        </>
      )}

      {/* Show message when Knowledge Expert is disabled */}
      {isAssistantMode && !form.values.useKnowledgeExpert && (
        <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
          <Text size="sm">
            Knowledge Expert is disabled. Your assistant will not have access to the vector database.
            You can still use other tools in the next step.
          </Text>
        </Alert>
      )}
    </Stack>
  );
}

function StepAgentLlmProvider({ form, providers, providersLoading }: StepProps & { providers?: any; providersLoading?: boolean }) {
  const isAssistantMode = form.values.agentType === 'assistant';

  return (
    <Stack gap="md">
      <Alert icon={<IconRobot size={16} />} color="grape" variant="light">
        <Text size="sm">
          {isAssistantMode ? (
            <>
              <strong>Primary Agent LLM</strong> - Select the main LLM that powers your assistant agent. This LLM will be used for reasoning, responding to users, and orchestrating tools.
            </>
          ) : (
            <>
              <strong>Primary Agent LLM</strong> - Select the main LLM provider and model for your RAG agent. This LLM can be used for query enhancement, reranking, and answer generation.
            </>
          )}
        </Text>
      </Alert>

      <Card withBorder p="md" style={{ background: 'linear-gradient(135deg, #f3e8ff 0%, #ffffff 100%)' }}>
        <Stack gap="md">
          <Select
            label="LLM Provider"
            placeholder={providersLoading ? 'Loading providers...' : 'Select a provider'}
            data={
              providers?.map((p: any) => ({
                value: p.id,
                label: `${p.name} (${p.provider_type})`,
              })) || []
            }
            {...form.getInputProps('agentLlmProviderId')}
            searchable
            disabled={providersLoading}
            required
            description={isAssistantMode ? "Choose the LLM provider that will power your assistant" : "Choose the primary LLM provider for your RAG agent"}
          />

          {form.values.agentLlmProviderId && providers ? (
            <Select
              label="Model"
              placeholder="Select a model"
              data={
                providers
                  .find((p: any) => p.id === form.values.agentLlmProviderId)
                  ?.generative?.models.map((m: string) => ({
                    value: m,
                    label: m,
                  })) || []
              }
              {...form.getInputProps('agentLlmModel')}
              searchable
              required
              description={isAssistantMode ? "Select the specific model for your assistant" : "Select the specific model for your RAG agent"}
            />
          ) : (
            <Select
              label="Model"
              placeholder="Select provider first"
              disabled
              required
            />
          )}
        </Stack>
      </Card>

      {form.values.agentLlmProviderId && form.values.agentLlmModel && (
        <Alert icon={<IconCheck size={16} />} color="green" variant="light">
          <Text size="sm">
            <strong>Selected:</strong> {providers?.find((p: any) => p.id === form.values.agentLlmProviderId)?.name} / {form.values.agentLlmModel}
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
      {isAssistantMode ? (
        // Assistant mode: Just show info about custom variants strategy
        <Alert icon={<IconRobot size={16} />} color="grape" variant="light">
          <Text size="sm">
            <strong>Enhancement Strategy: Custom Variants</strong> - Automatically generates 3-5 query variants before passing to RAG with parallel search &amp; RRF fusion.
          </Text>
        </Alert>
      ) : (
        // RAG mode: Show strategy selection and info
        <>
          <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
            <Text size="sm">
              Choose how your queries will be enhanced before searching the knowledge base.
            </Text>
          </Alert>

          <Group justify="space-between" align="flex-end">
            <div style={{ flex: 1 }}>
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
        </>
      )}

      {/* For RAG mode: show info that enhancement will use agent's primary LLM */}
      {/* For Assistant mode: skip LLM provider here - it's in Vector Database step (Step 3) */}
      {isNonNativeStrategy && !isAssistantMode && (
        <Alert icon={<IconInfoCircle size={16} />} color="cyan" variant="light">
          <Text size="sm">
            <strong>Using Agent LLM:</strong> Query enhancement and answer generation will use the primary LLM provider selected in Step 2. No additional provider configuration needed here.
          </Text>
        </Alert>
      )}

      {/* For Assistant mode: show info that enhancement LLM will be configured in next step */}
      {isAssistantMode && (
        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          <Text size="sm">
            The enhancement LLM will be configured in the Vector Database step.
          </Text>
        </Alert>
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

          <Switch
            label="Use Agent LLM as Judge"
            description="Use the same LLM provider and model as the agent for document reranking"
            {...form.getInputProps('useAgentLlmAsJudge', { type: 'checkbox' })}
            mb="md"
          />

          {form.values.useAgentLlmAsJudge && (
            <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light" mb="md">
              <Stack gap="xs">
                <Text size="sm" fw={600}>Judge Configuration</Text>
                <Group gap="md">
                  <div>
                    <Text size="xs" fw={500} c="dark">Provider</Text>
                    <Text size="sm">{providers?.find((p: any) => p.id === form.values.agentLlmProviderId)?.name || form.values.agentLlmProviderId || 'Not selected'}</Text>
                  </div>
                  <div>
                    <Text size="xs" fw={500} c="dark">Model</Text>
                    <Text size="sm">{form.values.agentLlmModel || 'Not selected'}</Text>
                  </div>
                </Group>
                <Text size="xs" c="dimmed">Using the agent's LLM for document ranking ensures consistent evaluation of relevance.</Text>
              </Stack>
            </Alert>
          )}

          {!form.values.useAgentLlmAsJudge && (
            <>
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
                      ? rerankerModels
                        .filter((m: string) => {
                          // Exclude agent's model if same provider is selected
                          if (form.values.selectedRerankerId === form.values.agentLlmProviderId && m === form.values.agentLlmModel) {
                            return false;
                          }
                          return true;
                        })
                        .map((m: string) => ({
                          value: m,
                          label: m,
                        }))
                      : generativeModels
                        .filter((m: string) => {
                          // Exclude agent's model if same provider is selected
                          if (form.values.selectedRerankerId === form.values.agentLlmProviderId && m === form.values.agentLlmModel) {
                            return false;
                          }
                          return true;
                        })
                        .map((m: string) => ({
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
            </>
          )}

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
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text size="sm">
                  <strong>Using Agent LLM:</strong> Answer generation will automatically use the primary LLM provider selected in Step 1. No additional provider configuration needed.
                </Text>
              </Alert>
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

      {/* STEP 1: ENHANCEMENT STRATEGY / LLM PROVIDER */}
      <Card withBorder p="md" bg="cyan.0">
        <Stack gap="sm">
          <Text fw={600}>Step 1: {form.values.agentType === 'assistant' ? 'LLM Provider' : 'Enhancement Strategy'}</Text>

          {form.values.agentType === 'assistant' ? (
            // Assistant mode: Show only LLM details
            <div>
              <Text size="sm" fw={500} mb="xs">
                LLM Configuration
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
          ) : (
            // RAG mode: Show strategy and LLM details
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
          )}
        </Stack>
      </Card>

      {/* STEP 2/3: KNOWLEDGE EXPERT SETTINGS (Assistant) / VECTOR DATABASE (RAG) */}
      <Card withBorder p="md" bg="teal.0">
        <Stack gap="sm">
          <Text fw={600}>
            {form.values.agentType === 'assistant' ? 'Knowledge Expert Settings' : 'Vector Database'}
          </Text>

          {/* For Assistant mode: Show Knowledge Expert toggle status */}
          {form.values.agentType === 'assistant' && (
            <Group gap="md" mb="xs">
              <div>
                <Text size="sm" fw={500} mb="xs" c="dark">
                  Knowledge Expert (RAG Tool)
                </Text>
                <Badge size="lg" color={form.values.useKnowledgeExpert ? 'green' : 'gray'}>
                  {form.values.useKnowledgeExpert ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
            </Group>
          )}

          {/* Vector DB config - show if RAG mode or (Assistant mode + Knowledge Expert enabled) */}
          {(form.values.agentType === 'rag' || form.values.useKnowledgeExpert) && (
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
                  {form.values.agentType === 'assistant' && (
                    <div>
                      <Text size="xs" fw={500} c="dark">Enhancement Strategy</Text>
                      <Text size="sm" fw={500} c="dark">Custom Variants (Fixed)</Text>
                    </div>
                  )}
                </Stack>
              </Grid.Col>

              {/* Enhancement LLM (always shown for Assistant mode - uses custom_variants) */}
              {form.values.agentType === 'assistant' && (
                <Grid.Col span={12}>
                  <Divider my="xs" label="Enhancement LLM" labelPosition="center" />
                  <Group gap="xl">
                    <div>
                      <Text size="xs" fw={500} c="dark">Provider</Text>
                      <Text size="sm" fw={500} c="dark">{selectedProvider?.name || 'Not selected'}</Text>
                    </div>
                    <div>
                      <Text size="xs" fw={500} c="dark">Model</Text>
                      <Text size="sm" fw={500} c="dark">{form.values.selectedModel || 'Not selected'}</Text>
                    </div>
                  </Group>
                </Grid.Col>
              )}

              {/* Reranker config for Assistant mode */}
              {form.values.agentType === 'assistant' && (
                <Grid.Col span={12}>
                  <Divider my="xs" label="Reranker" labelPosition="center" />
                  <Group gap="xl">
                    <div>
                      <Text size="xs" fw={500} c="dark">Reranking</Text>
                      <Badge size="sm" color={form.values.enableReranking ? 'green' : 'gray'}>
                        {form.values.enableReranking ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    {form.values.enableReranking && (
                      <>
                        <div>
                          <Text size="xs" fw={500} c="dark">Provider</Text>
                          <Text size="sm" fw={500} c="dark">{selectedRerankerProvider?.name || 'Not selected'}</Text>
                        </div>
                        <div>
                          <Text size="xs" fw={500} c="dark">Model</Text>
                          <Text size="sm" fw={500} c="dark">{form.values.selectedRerankerModel || 'Not selected'}</Text>
                        </div>
                        <div>
                          <Text size="xs" fw={500} c="dark">Threshold</Text>
                          <Text size="sm" fw={500} c="dark">{form.values.relevanceThreshold}</Text>
                        </div>
                      </>
                    )}
                  </Group>
                </Grid.Col>
              )}
            </Grid>
          )}

          {/* Message when Knowledge Expert is disabled */}
          {form.values.agentType === 'assistant' && !form.values.useKnowledgeExpert && (
            <Text size="sm" c="dimmed">
              Knowledge Expert is disabled. The assistant will not have access to vector database search.
            </Text>
          )}
        </Stack>
      </Card>

      {/* STEP 3: RERANKER (OPTIONAL) - RAG MODE ONLY */}
      {form.values.agentType === 'rag' && form.values.enableReranking && (
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

      {/* STEP 4: ANSWER GENERATION - RAG MODE ONLY */}
      {form.values.agentType === 'rag' && (
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
      )}

      {/* STEP 3/5: TOOLS BINDING (Assistant mode only - Step 3 in Assistant, Step 5 in overall flow) */}
      {form.values.agentType === 'assistant' && (
        <Card withBorder p="md" bg="violet.1" style={{ borderColor: '#a78bfa' }}>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text fw={600}>Step 3: Tools Binding</Text>
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
