import { useDeleteConversation, useResetConversationMessages } from '@/api/resources/conversations';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { StreamingMessage } from '@/components/streaming-message';
import { SystemPromptManager } from '@/components/system-prompt-manager';
import { TypingIndicator } from '@/components/typing-indicator';
import { WorkflowProgressModal } from '@/components/workflow-progress-modal';
import { apiEndpoints, apiUtils } from '@/config';
import { useRAGWorkflowProgress } from '@/hooks/useRAGWorkflowProgress';
import { useSupervisorWorkflowProgress } from '@/hooks/useSupervisorWorkflowProgress';
import { paths } from '@/routes/paths';
import {
  Accordion,
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Checkbox,
  Collapse,
  Divider,
  Grid,
  Group,
  List,
  LoadingOverlay,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  ThemeIcon,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconArrowsLeftRight,
  IconCheck,
  IconChevronDown,
  IconEdit,
  IconHelp,
  IconInfoCircle,
  IconLoader,
  IconMessageCircle,
  IconRefresh,
  IconSend,
  IconSettings,
  IconTrash,
  IconX
} from '@tabler/icons-react';
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date | string;
  isStreaming?: boolean;
  metadata?: {
    source_urls?: string[];
    correlation_ids?: string[];
    chunk_ids?: string[];
    document_count?: number;
    enhancement_strategy?: string;
    enhanced_queries?: string[];  // ALWAYS array - even for single queries
  };
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

// Helper function to generate RAG configuration description
const generateRagDescription = (
  strategy: string,
  enableReranking: boolean,
  enableLLMGeneration: boolean,
  topK?: number,
  collectionName?: string,
  enhancementProvider?: { id: string, model_name: string } | null,
  providers?: any[]
): string => {
  const parts: string[] = [];

  // Strategy description with RRF info
  const strategyLabel = ENHANCEMENT_STRATEGIES.find(s => s.value === strategy)?.label || 'Unknown';

  if (strategy === 'native') {
    parts.push(`Using ${strategyLabel} (direct search)`);
  } else {
    // Non-native strategy - include provider/model info if available
    let strategyPart = `Using ${strategyLabel}`;
    if (enhancementProvider) {
      // Get provider name from providers list
      const providerName = providers?.find((p: any) => p.id === enhancementProvider.id)?.name || enhancementProvider.id;
      strategyPart += ` (${providerName}/${enhancementProvider.model_name})`;
    }

    if (strategy === 'augmented' || strategy === 'multi_query' || strategy === 'decomposition') {
      strategyPart += ' with RRF fusion';
    } else if (strategy === 'hyde') {
      strategyPart += ' (single enhanced query)';
    }

    parts.push(strategyPart);
  }

  // Collection and top-k
  if (collectionName && topK) {
    parts.push(`searching ${collectionName} (top ${topK})`);
  }

  // Reranking
  if (enableReranking) {
    parts.push(`with LLM reranking`);
  }

  // Generation mode
  if (enableLLMGeneration) {
    parts.push(`generating natural language answers`);
  } else {
    parts.push(`returning raw results`);
  }

  return parts.join(', ') + '.';
};

export default function ConversationWindow() {
  const deleteConversationMutation = useDeleteConversation();
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  const handleDeleteSession = async () => {
    if (!sessionId) return;
    try {
      await deleteConversationMutation.mutateAsync({ model: {}, route: { conversationId: sessionId } });
      notifications.show({ title: 'Deleted', message: 'Conversation deleted', color: 'green' });
      setDeleteModalOpen(false);
      navigate(paths.dashboard.apps.knowledgeSearch);
    } catch (err: any) {
      notifications.show({ title: 'Error', message: 'Failed to delete conversation', color: 'red' });
    }
  };
  // CSS animations for smooth chat experience
  const chatAnimations = `
    @keyframes fadeIn {
      0% { opacity: 0; transform: translateY(10px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInLeft {
      0% { opacity: 0; transform: translateX(-20px); }
      100% { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInRight {
      0% { opacity: 0; transform: translateX(20px); }
      100% { opacity: 1; transform: translateX(0); }
    }
  `;

  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [sessionName, setSessionName] = useState('Conversation');
  const [isConnected, setIsConnected] = useState(true); // Start as connected since we connect on-demand
  const [connectionRetries, setConnectionRetries] = useState(0);
  const [messageMode, setMessageMode] = useState<'agent' | 'rag'>('rag'); // Mode selector for current message

  // Settings modal state
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('native');
  const [collectionName, setCollectionName] = useState('LongTermMemory');
  const [enableReranking, setEnableReranking] = useState(false);
  const [relevanceThreshold, setRelevanceThreshold] = useState(0.5);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [enableLLMGeneration, setEnableLLMGeneration] = useState(true);
  const [topK, setTopK] = useState<number | undefined>(undefined);
  const [enableKnowledgeAssistant, setEnableKnowledgeAssistant] = useState(true);
  const [selectedSystemPromptId, setSelectedSystemPromptId] = useState<string | undefined>();
  const [systemPromptTasks, setSystemPromptTasks] = useState<any[]>([]);
  const [savedEnhancementProvider, setSavedEnhancementProvider] = useState<{ id: string, model_name: string } | null>(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [expandedMetadata, setExpandedMetadata] = useState<Set<number>>(new Set());

  // Strategies info modal state
  const [strategiesInfoModalOpen, setStrategiesInfoModalOpen] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const resetMessagesMutation = useResetConversationMessages();
  const lastProcessedCompletionRef = useRef<string | null>(null);
  const isProcessingMessageRef = useRef<boolean>(false);
  const lastProcessedStreamRef = useRef<string>('');

  // Update reranker defaults when LLM provider or model changes
  useEffect(() => {
    if (enableReranking && selectedProviderId && selectedModel) {
      // Only update if values are different to prevent infinite loops
      setSelectedRerankerId(prev => prev !== selectedProviderId ? selectedProviderId : prev);
      setSelectedRerankerModel(prev => prev !== selectedModel ? selectedModel : prev);
    }
  }, [selectedProviderId, selectedModel, enableReranking]);

  // Enhanced workflow visualization state
  const [workflowState, setWorkflowState] = useState<{
    currentStage: string | null;
    completedStages: string[];
    originalQuery: string | null;
    enhancedQueries: string[] | null;  // ALWAYS an array of query variants (including single queries)
    strategy: string | null;
    documentCount: number;
    relevantCount: number;
    rerankingEnabled: boolean;
    indexType: string;
    vectorDimension: number | undefined;
    searchTime: number;
    isActive: boolean;
    intent: string | null;  // NEW: Supervisor detected intent
    stageDetails: Record<string, any>;  // NEW: Store detailed data for each completed stage
    ragSubstages: string[];  // NEW: Track completed RAG substages (query_enhancement, document_retrieval, document_judging)
  }>({
    currentStage: null,
    completedStages: [],
    originalQuery: null,
    enhancedQueries: null,
    strategy: null,
    documentCount: 0,
    relevantCount: 0,
    rerankingEnabled: enableReranking,
    indexType: 'HNSW',
    vectorDimension: undefined,
    searchTime: 0,
    isActive: false,
    intent: null,
    stageDetails: {},  // Initialize empty details
    ragSubstages: [],  // Initialize empty substages
  });

  // Initialize workflow progress handlers for both RAG and Supervisor modes
  const { handleRAGWorkflowProgress, cleanup: cleanupRAG } = useRAGWorkflowProgress();
  const { handleSupervisorWorkflowProgress, cleanup: cleanupSupervisor } = useSupervisorWorkflowProgress();

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // Helper function to finalize streaming messages
  const finalizeStreamingMessages = () => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage && lastMessage.isStreaming) {
        // Create a new array with a new last message object (immutable update)
        return [
          ...prev.slice(0, -1),
          { ...lastMessage, isStreaming: false }
        ];
      }
      return prev;
    });
  };

  // Auto-scroll to show most recent messages (like a chat app)
  useEffect(() => {
    // Always scroll to bottom when messages change (except during initial history load)
    if (!isLoadingHistory && messages.length > 0) {
      // Use requestAnimationFrame + setTimeout to ensure DOM is fully rendered
      requestAnimationFrame(() => {
        setTimeout(() => {
          if (viewportRef.current) {
            const el = viewportRef.current;
            el.scrollTop = el.scrollHeight;
          } else {
            console.warn('⚠️ Viewport ref not available');
          }
        }, 200);
      });
    }
  }, [messages, isLoadingHistory]);

  // Load conversation history
  useEffect(() => {
    if (sessionId) {
      loadConversationHistory();
    }
  }, [sessionId]);

  // Reload settings when modal opens to ensure fresh data
  const isLoadingRef = useRef(false);
  useEffect(() => {
    if (settingsModalOpen && sessionId && !isLoadingRef.current) {
      isLoadingRef.current = true;
      loadConversationHistory().finally(() => {
        isLoadingRef.current = false;
      });
    }
  }, [settingsModalOpen, sessionId]);

  // Sync messageMode with enableKnowledgeAssistant setting
  // When user enables/disables Agent Mode in settings, update the message mode
  useEffect(() => {
    setMessageMode(enableKnowledgeAssistant ? 'agent' : 'rag');
    console.log(`🔄 [MESSAGE MODE SYNC] Set messageMode to: ${enableKnowledgeAssistant ? 'agent' : 'rag'}`);
  }, [enableKnowledgeAssistant]);

  // Cleanup WebSocket on unmount and pending timeouts
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      // Clean up any pending completion timeouts from both handlers
      cleanupRAG();
      cleanupSupervisor();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps: Only run cleanup on unmount, not when cleanup functions change

  const loadConversationHistory = async () => {
    try {
      setIsLoadingHistory(true);

      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );

      // Force fresh data - no caching
      const token = localStorage.getItem('jwt_token');
      const fetchPromise = fetch(apiUtils.buildApiUrl(`/conversations/${sessionId}?t=${Date.now()}`), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });

      const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

      if (response.ok) {
        const data = await response.json();

        setSessionName(data.session?.name || 'Conversation');

        // Load conversation settings from nested structure
        if (data.session) {
          // Extract from nested answer_generation config
          if (data.session.answer_generation?.provider) {
            setSelectedProviderId(data.session.answer_generation.provider.id || null);
            setSelectedModel(data.session.answer_generation.provider.model_name || null);
          } else {
            setSelectedProviderId(null);
            setSelectedModel(null);
          }

          // Extract from nested enhancement config
          setSelectedStrategy(data.session.enhancement?.strategy || 'native');
          if (data.session.enhancement?.provider) {
            setSavedEnhancementProvider({
              id: data.session.enhancement.provider.id,
              model_name: data.session.enhancement.provider.model_name
            });
          }

          // Extract from nested vector_database config
          setCollectionName(data.session.vector_database?.collection_name || 'LongTermMemory');
          setTopK(data.session.vector_database?.top_k || 5);

          // Extract from nested reranker config
          const hasReranker = data.session.reranker?.provider ? true : false;
          setEnableReranking(hasReranker);
          setSelectedRerankerId(data.session.reranker?.provider?.id || null);
          setSelectedRerankerModel(data.session.reranker?.provider?.model_name || null);

          // Determine LLM generation enabled (true if answer_generation has provider)
          const newEnableLLMGeneration = data.session.answer_generation?.provider ? true : false;
          setEnableLLMGeneration(newEnableLLMGeneration);

          // Load supervisor setting from assistant_config
          let newEnableKnowledgeAssistant = false;
          if (data.session.assistant_config) {
            // Use nested assistant_config structure
            newEnableKnowledgeAssistant = data.session.assistant_config.enabled ?? false;
            // Load system_prompt_tasks
            if (data.session.assistant_config.system_prompt_tasks) {
              setSystemPromptTasks(data.session.assistant_config.system_prompt_tasks);
            }
          }
          setEnableKnowledgeAssistant(newEnableKnowledgeAssistant);
        }

        // Optimize timestamp conversion - only process if messages exist
        if (data.messages && Array.isArray(data.messages)) {
          const messagesWithDates = data.messages.map((msg: any) => ({
            ...msg,
            timestamp: typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp
          }));
          setMessages(messagesWithDates);
        } else {
          setMessages([]);
        }
      } else {
        // Silently handle failed conversation load
        setMessages([]);
      }
    } catch (error) {
      // Silently handle conversation load errors
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Connect to WebSocket if not already connected
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setIsConnected(false); // Show connecting state
      await connectWebSocket();
      // Wait a bit for the connection to be established
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        // Send only query and conversation_id
        // Backend will load provider, model, strategy, and collection from conversation settings
        const message = {
          query: inputMessage,
          conversation_id: sessionId,
        };

        // Log the message being sent with mode/endpoint info
        const modeLabel = messageMode === 'agent' ? '∞ ASSISTANT AGENT' : '📚 RAG AGENT';
        const endpointLabel = messageMode === 'agent' ? '/ws/agent/query/supervisor' : '/ws/agent/query/rag';
        console.log(`📤 [QUERY SENT] Mode: ${modeLabel} | Endpoint: ${endpointLabel} | Query: ${inputMessage.substring(0, 100)}${inputMessage.length > 100 ? '...' : ''}`);

        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        const errorMessage: Message = {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
      }
    } else {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I cannot connect to the chat service. Please check your connection and try again. If the problem persists, contact support.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const connectWebSocket = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      let token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token available');
      }

      // Check if token is valid by making a test API call
      try {
        const testResponse = await apiUtils.apiRequest('/users/me');
        if (!testResponse.ok) {
          throw new Error('Token validation failed');
        }
      } catch (error) {
        // Try to refresh token
        try {
          const refreshResponse = await apiUtils.apiRequest('/auth/refresh', { method: 'POST' });
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            localStorage.setItem('jwt_token', refreshData.access_token);
            token = refreshData.access_token || '';
          } else {
            throw new Error('Token refresh failed');
          }
        } catch (refreshError) {
          window.location.href = '/auth/login';
          return;
        }
      }

      // Build WebSocket URL using config
      if (!sessionId) {
        throw new Error('Session ID is required for WebSocket connection');
      }
      // Select endpoint based on message mode selector
      // messageMode='agent' → /ws/agent/query/supervisor (multi-agent with intent routing)
      // messageMode='rag'   → /ws/agent/query/rag (RAG-only mode with START/COMPLETE events)
      const wsEndpoint = messageMode === 'agent'
        ? apiEndpoints.agent.websocket.supervisor
        : apiEndpoints.agent.websocket.rag;
      const wsUrl = apiUtils.buildWebSocketUrl(wsEndpoint, token || undefined);

      // Log the endpoint being invoked
      const modeLabel = messageMode === 'agent' ? '∞ ASSISTANT AGENT' : '📚 RAG AGENT';
      const endpointLabel = messageMode === 'agent' ? '/ws/agent/query/supervisor' : '/ws/agent/query/rag';
      console.log(`🔌 [WS CONNECTING] Mode: ${modeLabel} | Endpoint: ${endpointLabel}`);

      wsRef.current = new WebSocket(wsUrl);

      // Add connection timeout
      const connectionTimeout = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
          wsRef.current.close();
          setIsConnected(false);
          setIsLoading(false);
        }
      }, 10000); // 10 second timeout

      wsRef.current.onopen = () => {
        clearTimeout(connectionTimeout);
        setIsConnected(true);
        setConnectionRetries(0); // Reset retry counter on successful connection
        const modeLabel = messageMode === 'agent' ? '∞ ASSISTANT AGENT' : '📚 RAG AGENT';
        console.log(`✅ [WS CONNECTED] Mode: ${modeLabel} | Connection established successfully`);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`📥 [WS MESSAGE RECEIVED] type=${data.type}, stage=${data.stage}, message=${data.message}`);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('❌ [WS MESSAGE ERROR] Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        clearTimeout(connectionTimeout);
        setIsConnected(false); // Mark as disconnected when connection closes
        setIsLoading(false);
        finalizeStreamingMessages();

        // Log close reason for debugging
        console.log(`🔌 WebSocket closed: code=${event.code}, reason=${event.reason || 'No reason provided'}`);
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false); // Mark as disconnected on error
        setIsLoading(false);
        finalizeStreamingMessages();
      };

    } catch (error) {
      setIsConnected(false);
      setIsLoading(false);

      // Retry connection up to 3 times
      if (connectionRetries < 3) {
        setConnectionRetries(prev => prev + 1);
        setTimeout(() => {
          connectWebSocket();
        }, 2000); // Wait 2 seconds before retry
      } else {
        setConnectionRetries(0);
      }
    }
  };

  const handleWebSocketMessage = (data: any) => {
    const { stage, message, error, chunk, type } = data;
    const response = data.response || data.data?.response;

    // CRITICAL: Prevent re-entrant calls during state updates
    if (isProcessingMessageRef.current) {
      console.log('⏸️ Skipping message processing (already processing)');
      return;
    }

    try {
      isProcessingMessageRef.current = true;

      // Use type for supervisor events, stage for regular RAG events
      const eventKey = type || stage;

      switch (eventKey) {
        case 'starting':
        case 'workflow_started':
          // Initialize enhanced workflow visualization
          const initialStrategy = data?.data?.strategy || data?.strategy || selectedStrategy;

          // Get the original query from the data or from the last user message
          const originalUserQuery = data?.data?.query || data?.query ||
            (messages.length > 0 && messages[messages.length - 1].role === 'user'
              ? messages[messages.length - 1].content
              : inputMessage);

          console.log('🚀 Workflow starting with query:', originalUserQuery);

          setWorkflowState({
            currentStage: 'query_enhancement',  // ← Start with first stage immediately, don't wait for backend
            completedStages: [],
            originalQuery: originalUserQuery,
            enhancedQueries: null,
            strategy: initialStrategy,
            documentCount: 0,
            relevantCount: 0,
            rerankingEnabled: enableReranking,
            indexType: 'HNSW',
            vectorDimension: undefined,
            searchTime: 0,
            isActive: true,
            intent: null,
            stageDetails: {},
            ragSubstages: [],
          });
          break;

        case 'query_enhancement':
        case 'query_enhancement_complete':
          // Handle both RAG mode and Supervisor mode (Supervisor emits RAG sub-stage events)
          console.log('✨ QUERY ENHANCEMENT MESSAGE RECEIVED:', {
            enhanced_queries: data?.data?.enhanced_queries,
            strategy: data?.data?.strategy || data?.strategy,
            messageMode
          });

          // In supervisor mode, track this as a RAG substage, not skip it
          // Update workflow state to track RAG substages within rag_agent_executing
          setWorkflowState(prev => {
            const newRagSubstages = [...(prev.ragSubstages || [])];
            const stageName = stage === 'query_enhancement_complete' ? 'query_enhancement' : stage;
            if (!newRagSubstages.includes(stageName)) {
              newRagSubstages.push(stageName);
            }
            return {
              ...prev,
              ragSubstages: newRagSubstages,
            };
          });

          // Create or update the streaming message with query enhancement status
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];

            // If no assistant message exists, create one
            if (!lastMessage || lastMessage.role !== 'assistant') {
              return [
                ...prev,
                {
                  role: 'assistant',
                  content: '✨ Enhancing query...',
                  timestamp: new Date(),
                  isStreaming: true
                }
              ];
            }

            // Update existing streaming message
            if (lastMessage.isStreaming) {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: '✨ Enhancing query...'
                }
              ];
            }

            return prev;
          });

          // Update workflow state for query enhancement - ONLY use enhanced_queries (array)
          const newEnhancedQueries = data?.data?.enhanced_queries || null;
          const newStrategy = data?.data?.strategy || data?.strategy;

          console.log('🔄 Updating workflowState with enhanced_queries:', newEnhancedQueries);

          setWorkflowState(prev => {
            // Only update if something actually changed
            if (prev.currentStage === 'query_enhancement' &&
              JSON.stringify(prev.enhancedQueries) === JSON.stringify(newEnhancedQueries) &&
              (!newStrategy || prev.strategy === newStrategy)) {
              console.log('⏭️ Skipping workflowState update - no changes');
              return prev;
            }
            console.log('✅ Updating workflowState with new enhanced_queries');

            // Mark previous stage as completed when transitioning to query_enhancement
            const newCompleted = [...prev.completedStages];
            if (prev.currentStage && prev.currentStage !== 'query_enhancement' && !newCompleted.includes(prev.currentStage)) {
              newCompleted.push(prev.currentStage);
            }

            return {
              ...prev,
              currentStage: 'query_enhancement',
              completedStages: newCompleted,
              enhancedQueries: newEnhancedQueries,
              strategy: newStrategy || prev.strategy,
            };
          });
          break;

        case 'document_retrieval':
        case 'document_retrieval_complete':
          // Handle both RAG mode and Supervisor mode (Supervisor emits RAG sub-stage events)
          // In supervisor mode, track this as a RAG substage
          setWorkflowState(prev => {
            const newRagSubstages = [...(prev.ragSubstages || [])];
            const stageName = stage === 'document_retrieval_complete' ? 'document_retrieval' : stage;
            if (!newRagSubstages.includes(stageName)) {
              newRagSubstages.push(stageName);
            }
            return {
              ...prev,
              ragSubstages: newRagSubstages,
            };
          });

          // Create or update the streaming message with document retrieval status
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];

            // If no assistant message exists, create one
            if (!lastMessage || lastMessage.role !== 'assistant') {
              return [
                ...prev,
                {
                  role: 'assistant',
                  content: '🔍 Retrieving relevant documents...',
                  timestamp: new Date(),
                  isStreaming: true
                }
              ];
            }

            // Update existing streaming message
            if (lastMessage.isStreaming) {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: '🔍 Retrieving relevant documents...'
                }
              ];
            }

            return prev;
          });

          // Update workflow state for document retrieval
          setWorkflowState(prev => {
            const newCompleted = prev.currentStage === 'query_enhancement' && !prev.completedStages.includes('query_enhancement')
              ? [...prev.completedStages, 'query_enhancement']
              : prev.completedStages;

            return {
              ...prev,
              currentStage: 'document_retrieval',
              completedStages: newCompleted,
              documentCount: data?.data?.document_count || data?.document_count || 0,
            };
          });
          break;

        case 'document_judging':
        case 'document_reranking':
          // Handle both RAG mode and Supervisor mode (Supervisor emits RAG sub-stage events)
          // In supervisor mode, track this as a RAG substage
          setWorkflowState(prev => {
            const newRagSubstages = [...(prev.ragSubstages || [])];
            const stageName = 'document_judging';
            if (!newRagSubstages.includes(stageName)) {
              newRagSubstages.push(stageName);
            }
            return {
              ...prev,
              ragSubstages: newRagSubstages,
            };
          });

          // Update the existing streaming message with document judging status
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: '⚖️ Evaluating document relevance...'
                }
              ];
            }
            return prev;
          });

          // Update workflow state for document judging/reranking
          setWorkflowState(prev => {
            const newCompleted = prev.currentStage === 'document_retrieval' && !prev.completedStages.includes('document_retrieval')
              ? [...prev.completedStages, 'document_retrieval']
              : prev.completedStages;

            return {
              ...prev,
              currentStage: 'document_judging',
              completedStages: newCompleted,
              relevantCount: data?.data?.relevant_count || data?.relevant_count || 0,
            };
          });
          break;

        case 'response_generation':
          // GUARD: Skip if using supervisor/agent mode - only handle for RAG mode
          if (messageMode === 'agent') {
            console.log('⏭️ Skipping response_generation handler - using agent/supervisor mode instead');
            break;
          }
          console.log('📤 [RESPONSE GENERATION] Processing response generation for RAG mode');

          // Update the existing streaming message with response generation status
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: '🧠 Generating response...'
                }
              ];
            }
            return prev;
          });

          // Update workflow state for response generation
          setWorkflowState(prev => {
            const newCompleted = [...prev.completedStages];

            // If Knowledge Assistant is enabled, mark all supervisor stages as completed
            if (enableKnowledgeAssistant) {
              if (!newCompleted.includes('supervisor_init')) {
                newCompleted.push('supervisor_init');
              }
              if (!newCompleted.includes('intent_detection')) {
                newCompleted.push('intent_detection');
              }
              if (!newCompleted.includes('rag_agent_executing')) {
                newCompleted.push('rag_agent_executing');
              }
              // Only mark task_agent_executing as completed if intent is rag_then_task
              if (prev.intent === 'rag_then_task' && !newCompleted.includes('task_agent_executing')) {
                newCompleted.push('task_agent_executing');
              }
            } else {
              // Regular RAG flow - mark previous stage as completed
              if (prev.currentStage === 'document_judging' && !newCompleted.includes('document_judging')) {
                newCompleted.push('document_judging');
              } else if (prev.currentStage === 'document_retrieval' && !newCompleted.includes('document_retrieval')) {
                newCompleted.push('document_retrieval');
              } else if (prev.currentStage === 'query_enhancement' && !newCompleted.includes('query_enhancement')) {
                newCompleted.push('query_enhancement');
              }
            }

            return {
              ...prev,
              currentStage: 'response_generation',
              completedStages: newCompleted,
            };
          });
          break;

        case 'streaming_response':
          // Handle streaming response chunks from agent
          // Extract chunk from data.chunk or chunk property
          const textChunk = data?.data?.chunk || data?.chunk || chunk;
          const chunkMetadata = data?.metadata || data?.data?.metadata;

          if (textChunk) {
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
                // Check if this is the placeholder "Starting" message - replace it instead of appending
                const isPlaceholder = lastMessage.content.includes('🤖 Starting conversation');

                // Update existing streaming message
                const updatedMessage = {
                  ...lastMessage,
                  content: isPlaceholder ? textChunk : lastMessage.content + textChunk,
                  isStreaming: true
                };

                // Attach metadata if provided (usually on first chunk)
                if (chunkMetadata) {
                  updatedMessage.metadata = chunkMetadata;
                }

                return [
                  ...prev.slice(0, -1),
                  updatedMessage
                ];
              } else {
                // Create new streaming message
                const newMessage: Message = {
                  role: 'assistant',
                  content: textChunk,
                  timestamp: new Date(),
                  isStreaming: true
                };

                // Attach metadata if provided (usually on first chunk)
                if (chunkMetadata) {
                  newMessage.metadata = chunkMetadata;
                }

                return [
                  ...prev,
                  newMessage
                ];
              }
            });

            // Mark response_generation as completed when first streaming chunk arrives
            // Use a ref to prevent multiple updates
            setWorkflowState(prev => {
              // Only update if response_generation is not already in completed stages
              if (!prev.completedStages.includes('response_generation')) {
                const newCompleted = [...prev.completedStages, 'response_generation'];
                return {
                  ...prev,
                  completedStages: newCompleted,
                  currentStage: 'response_generation' // Keep showing as current while streaming
                };
              }
              // Don't update if already completed - return same reference
              return prev;
            });
          }
          break;

        case 'workflow_complete':
          // Handle workflow completion - close the modal and finalize streaming message
          console.log('✅ [WORKFLOW COMPLETE] Closing RAG pipeline modal');

          // Stop loading indicator
          setIsLoading(false);

          // Finalize the streaming message to apply markdown formatting
          finalizeStreamingMessages();

          // Close the modal
          setWorkflowState(prev => ({
            ...prev,
            isActive: false,
            currentStage: null,
          }));
          break;

        case 'workflow_error':
          // Handle workflow error - show actual error message from backend
          console.log('❌ [WORKFLOW ERROR] Workflow failed:', data);

          // Stop loading indicator
          setIsLoading(false);

          // Add error message to conversation
          const errorContent = data.response || data.error || 'An error occurred during the workflow. Please try again.';
          const errorMessage: Message = {
            role: 'assistant',
            content: errorContent,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMessage]);

          // Close the modal
          setWorkflowState(prev => ({
            ...prev,
            isActive: false,
            currentStage: null,
          }));
          break;

        case 'workflow_progress': {
          // Route to appropriate handler based on mode
          if (enableKnowledgeAssistant) {
            // Supervisor mode - use supervisor handler
            console.log('🤖 Routing to SUPERVISOR workflow handler');
            handleSupervisorWorkflowProgress(data, workflowState, setWorkflowState);
          } else {
            // RAG mode - use RAG handler
            console.log('🎭 Routing to RAG workflow handler');
            handleRAGWorkflowProgress(data, workflowState, setWorkflowState);
          }
          break;
        }

        case 'supervisor_started':
        case 'supervisor_init':
          // Handle supervisor initialization
          console.log('🤖 Supervisor agent started');
          setWorkflowState(prev => ({
            ...prev,
            currentStage: 'supervisor_init',
            completedStages: [],
            isActive: true,
            ragSubstages: [],  // Reset substages on new workflow
          }));
          break;

        case 'supervisor_progress':
          // Handle ALL supervisor progress events (intent_detection, intent_detected, rag_agent_executing, task_agent_executing, response_generation)
          const supervisorStage = data?.stage || stage;
          console.log(`🔄 [SUPERVISOR EVENT] stage=${supervisorStage}, type=${type}`, data);

          setWorkflowState(prev => {
            const newCompleted = [...prev.completedStages];
            const newStageDetails = { ...prev.stageDetails };

            // Extract intent from data if available
            const detectedIntent = data?.data?.intent || prev.intent;

            // Handle COMPLETE events - these mark a stage as done and move to next
            if (supervisorStage.endsWith('_complete')) {
              const completedStage = supervisorStage.replace('_complete', '');

              // Store detailed data for the completed stage
              newStageDetails[completedStage] = {
                message: data?.message || '',
                data: data?.data || {},
                timestamp: new Date().toISOString(),
                execution_time_ms: data?.execution_time_ms || 0,
              };
              console.log(`✅ ${completedStage} COMPLETED, stored details:`, newStageDetails[completedStage]);

              // Mark the stage as completed
              if (!newCompleted.includes(completedStage)) {
                newCompleted.push(completedStage);
              }

              // Determine NEXT active stage based on what just completed
              let nextActiveStage = null;

              if (completedStage === 'supervisor_init') {
                nextActiveStage = 'intent_detection';
              } else if (completedStage === 'intent_detection') {
                // Move to RAG or Task based on intent
                if (detectedIntent === 'rag_only' || detectedIntent === 'rag_then_task') {
                  nextActiveStage = 'rag_agent_executing';
                } else if (detectedIntent === 'task_only') {
                  nextActiveStage = 'task_agent_executing';
                } else {
                  nextActiveStage = 'rag_agent_executing'; // Default to RAG
                }
              } else if (completedStage === 'rag_agent_executing') {
                // Move to Task or Response Generation based on intent
                if (detectedIntent === 'rag_then_task') {
                  nextActiveStage = 'task_agent_executing';
                } else {
                  nextActiveStage = 'response_generation';
                }
              } else if (completedStage === 'task_agent_executing') {
                nextActiveStage = 'response_generation';
              } else if (completedStage === 'response_generation') {
                nextActiveStage = 'completed';
              } else {
                nextActiveStage = completedStage; // Stay on current if unknown
              }

              console.log(`✅ ${completedStage} COMPLETED → moving to ${nextActiveStage}`);

              // Capture enhanced queries if this is query_enhancement_complete
              let updateState: any = {
                ...prev,
                currentStage: nextActiveStage,
                completedStages: newCompleted,
                intent: detectedIntent,
                stageDetails: newStageDetails,
              };

              // Capture from query_enhancement_complete event
              if (completedStage === 'query_enhancement' && data?.data?.query_variants) {
                updateState.enhancedQueries = data.data.query_variants;
                updateState.strategy = data.data.strategy || prev.strategy;
                console.log(`✨ Enhanced queries captured from query_enhancement_complete:`, data.data.query_variants);
              }

              // Also capture from rag_agent_executing_complete event (for supervisor mode)
              if (completedStage === 'rag_agent_executing' && data?.data?.query_variants) {
                updateState.enhancedQueries = data.data.query_variants;
                updateState.strategy = data.data.strategy_used || prev.strategy;
                console.log(`✨ Enhanced queries captured from rag_agent_executing_complete:`, data.data.query_variants);
              }

              return updateState;
            } else {
              // For START events (e.g. 'intent_detection', 'rag_agent_executing')
              // These directly become the current active stage
              console.log(`🟢 ${supervisorStage} STARTED`);

              return {
                ...prev,
                currentStage: supervisorStage,
                completedStages: newCompleted,
                intent: detectedIntent,
                stageDetails: newStageDetails,
              };
            }
          });
          break;

        case 'completed':
          // GUARD: Prevent processing the same completion multiple times
          // Use response content as key since it's unique per completion
          const completionKey = `completed-${data.data?.response?.substring(0, 100) || Date.now()}`;
          if (lastProcessedCompletionRef.current === completionKey) {
            console.log('⏭️ SKIPPING duplicate completion message');
            return; // Already processed this completion
          }
          lastProcessedCompletionRef.current = completionKey;
          console.log('✅ Processing NEW completion:', completionKey);

          // Handle completion from agent WebSocket - ONLY use enhanced_queries (array)
          console.log('🔍 COMPLETED MESSAGE RECEIVED:', {
            has_data: !!data.data,
            enhanced_queries: data.data?.enhanced_queries,
            enhanced_queries_is_array: Array.isArray(data.data?.enhanced_queries),
            enhanced_queries_length: data.data?.enhanced_queries?.length,
          });

          const metadata = data.data ? {
            source_urls: data.data.source_urls || [],
            correlation_ids: data.data.correlation_ids || [],
            chunk_ids: data.data.chunk_ids || [],
            document_count: data.data.document_count || 0,
            enhancement_strategy: data.data.enhancement_strategy,
            enhanced_queries: data.data.enhanced_queries || [],  // ALWAYS array
          } : undefined;

          console.log('📦 Final metadata being stored:', metadata);
          console.log('📦 enhanced_queries:', metadata?.enhanced_queries);

          // Consolidate ALL state updates into a single batch
          setIsLoading(false);

          // Update workflow state - CONSOLIDATED single call
          setWorkflowState(prev => {
            // Check if state actually needs to change
            const needsCompletionMarking = !prev.completedStages.includes('response_generation');
            const currentStageAlreadyNull = prev.currentStage === null;
            const alreadyInactive = !prev.isActive;

            // Check if enhanced queries would actually change
            let queriesChanged = false;
            if (metadata?.enhanced_queries && Array.isArray(metadata.enhanced_queries) && metadata.enhanced_queries.length > 0) {
              const queriesStr = JSON.stringify(metadata.enhanced_queries);
              queriesChanged = JSON.stringify(prev.enhancedQueries) !== queriesStr;
            }

            // Only update if something actually changed
            if (!needsCompletionMarking && currentStageAlreadyNull && alreadyInactive && !queriesChanged) {
              // Nothing changed, return prev to avoid unnecessary re-render
              return prev;
            }

            // Build updated state
            const newCompleted = prev.completedStages.includes('response_generation')
              ? prev.completedStages
              : [...prev.completedStages, 'response_generation'];

            let updatedState: any = {
              ...prev,
              currentStage: null,
              completedStages: newCompleted,
              isActive: false,
            };

            // Add enhanced_queries if available and different from current state
            if (queriesChanged) {
              updatedState.enhancedQueries = metadata?.enhanced_queries || [];
            }

            return updatedState;
          });

          // Update messages - SINGLE consolidated call
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              // Finalize the streaming message (keep existing content, just mark as complete)
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: response || lastMessage.content, // Use response as fallback, prefer streamed content
                  isStreaming: false,
                  metadata: metadata
                }
              ];
            } else if (response) {
              // Only add new message if no streaming message exists
              return [
                ...prev,
                {
                  role: 'assistant',
                  content: response,
                  timestamp: new Date(),
                  isStreaming: false,
                  metadata: metadata
                }
              ];
            }
            return prev;
          });

          // Note: finalizeStreamingMessages() call removed - already handled in setMessages above by setting isStreaming: false
          break;

        case 'error':
          // Handle errors
          finalizeStreamingMessages();
          const genericErrorMessage: Message = {
            role: 'assistant',
            content: message || error || 'An error occurred during the conversation.',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, genericErrorMessage]);
          setIsLoading(false);
          break;

        default:
          // Log unknown stages for debugging
          // Unknown stage
          break;
      }
    } finally {
      // Always reset the processing flag
      isProcessingMessageRef.current = false;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp: Date | string): string => {
    try {
      const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
      return date.toLocaleTimeString();
    } catch (error) {
      return 'Invalid time';
    }
  };

  const handleResetMessages = async () => {
    if (!sessionId) return;

    try {
      await resetMessagesMutation.mutateAsync({
        model: {},
        route: { conversationId: sessionId }
      });

      // Clear local messages
      setMessages([]);

      // Show success notification
      notifications.show({
        title: 'Success',
        message: 'Conversation messages have been reset',
        color: 'green',
      });
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to reset conversation messages',
        color: 'red',
      });
    }
  };

  const handleSaveSettings = async () => {
    if (!sessionId) return;

    // Validate BEFORE setting loading state
    if (enableLLMGeneration && !selectedProviderId) {
      notifications.show({
        title: 'Error',
        message: 'Please select an LLM provider when Generative Answer is enabled',
        color: 'red',
      });
      return;
    }

    if (enableLLMGeneration && !selectedModel) {
      notifications.show({
        title: 'Error',
        message: 'Please select an LLM model when Generative Answer is enabled',
        color: 'red',
      });
      return;
    }

    try {
      setIsSavingSettings(true);
      const token = localStorage.getItem('jwt_token');

      // Determine final strategy - force to native if provider/model not set
      const finalSaveStrategy = selectedStrategy !== 'native' && selectedProviderId && selectedModel
        ? selectedStrategy
        : 'native';

      // Warn if strategy was forced back to native
      if (selectedStrategy !== 'native' && finalSaveStrategy === 'native') {
        notifications.show({
          title: 'Strategy Reset',
          message: `Cannot use "${selectedStrategy}" strategy without LLM provider and model. Strategy has been reset to "native".`,
          color: 'yellow',
          icon: <IconAlertCircle size={16} />,
          autoClose: 7000,
        });
      }

      // Build nested configuration structure
      const payload: any = {
        // Enhancement configuration
        enhancement: {
          strategy: finalSaveStrategy,
          provider: finalSaveStrategy !== 'native' && selectedProviderId && selectedModel ? {
            id: selectedProviderId,
            model_name: selectedModel,
          } : null,
        },
        // Vector database configuration
        vector_database: {
          collection_name: collectionName,
          top_k: topK,
        },
        // Reranker configuration
        reranker: {
          enabled: enableReranking,
          provider: enableReranking && selectedRerankerId && selectedRerankerModel ? {
            id: selectedRerankerId,
            model_name: selectedRerankerModel,
          } : null,
          relevance_threshold: relevanceThreshold,
        },
        // Answer generation configuration
        answer_generation: {
          enabled: enableLLMGeneration && selectedProviderId && selectedModel ? true : false,
          provider: enableLLMGeneration && selectedProviderId && selectedModel ? {
            id: selectedProviderId,
            model_name: selectedModel,
          } : null,
        },
        enable_knowledge_assistant: enableKnowledgeAssistant,
        // NOTE: assistant_config intentionally NOT included in manual save
        // We only update it explicitly when user edits system prompts in the wizard
        // Including it with null would overwrite existing system_prompt_tasks
      };


      const response = await fetch(apiUtils.buildApiUrl(`/conversations/${sessionId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const responseData = await response.json();

        // Reload conversation data FIRST to reflect new settings
        await loadConversationHistory();

        notifications.show({
          title: 'Success',
          message: 'Conversation settings updated successfully',
          color: 'green',
          icon: <IconCheck size={16} />,
        });

        setSettingsModalOpen(false);
      } else {
        const errorData = await response.json().catch(() => ({}));
        notifications.show({
          title: 'Error',
          message: errorData.detail || 'Failed to update settings',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
      }
    } catch (error) {
      console.error('Error updating conversation settings:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to update conversation settings',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setIsSavingSettings(false);
    }
  };


  const handleQuickUpdate = async (updates: {
    mode?: 'agent' | 'rag',
    strategy?: string,
    model?: string,
    disableLLMGeneration?: boolean,
  }) => {
    if (!sessionId) return;

    try {
      const token = localStorage.getItem('jwt_token');

      // Determine the provider ID from the model
      let providerId = selectedProviderId;
      let modelName = selectedModel;
      if (updates.model) {
        const provider = providers?.find(p =>
          p.generative?.models?.includes(updates.model!)
        );
        if (provider) {
          providerId = provider.id;
          modelName = updates.model;
        }
      }

      // When model/provider changes, update the saved enhancement provider
      if (updates.model && providerId && modelName) {
        const newProvider = { id: providerId, model_name: modelName };
        setSavedEnhancementProvider(newProvider);
      }

      // Determine which provider to use - when model changes, use the new provider for BOTH enhancement and answer_generation
      let providerToUse = providerId && modelName ? { id: providerId, model_name: modelName } : null;

      // If model is NOT being updated, use the saved enhancement provider
      if (!updates.model && savedEnhancementProvider) {
        providerToUse = savedEnhancementProvider;
      }

      // Determine final strategy - if strategy is being changed to non-native but no provider exists, force to native
      const requestedStrategy = updates.strategy || selectedStrategy;
      const finalStrategy = requestedStrategy !== 'native' && !providerToUse ? 'native' : requestedStrategy;

      // If we had to force strategy back to native, warn the user
      if (requestedStrategy !== 'native' && !providerToUse && updates.strategy) {
        notifications.show({
          title: 'Strategy Reset to Native',
          message: 'Non-native enhancement strategies require an LLM provider and model. Please configure these in settings first.',
          color: 'yellow',
          icon: <IconAlertCircle size={16} />,
          autoClose: 7000,
        });
        setSelectedStrategy('native'); // Update UI
      }

      // Build nested configuration structure with current values + updates
      const payload: any = {
        // Enhancement configuration - uses the same provider as answer_generation
        enhancement: {
          strategy: finalStrategy,
          provider: finalStrategy !== 'native' ? providerToUse : null,
        },
        // Vector database configuration
        vector_database: {
          collection_name: collectionName,
          top_k: topK,
        },
        // Reranker configuration
        reranker: {
          enabled: enableReranking,
          provider: enableReranking && selectedRerankerId && selectedRerankerModel ? {
            id: selectedRerankerId,
            model_name: selectedRerankerModel,
          } : null,
          relevance_threshold: relevanceThreshold,
        },
        // Answer generation configuration - uses the same provider as enhancement
        answer_generation: {
          enabled: updates.disableLLMGeneration === true ? false : (enableLLMGeneration && providerToUse ? true : false),
          provider: updates.disableLLMGeneration === true ? null : (enableLLMGeneration && providerToUse ? providerToUse : null),
        },
        // Assistant config - preserve existing system_prompt_tasks
        assistant_config: {
          enabled: updates.mode === 'agent' ? true : (updates.mode === 'rag' ? false : enableKnowledgeAssistant),
          system_prompt_tasks: systemPromptTasks.length > 0 ? systemPromptTasks : null,
        },
      };

      console.log('🔄 [QUICK UPDATE] Payload:', JSON.stringify(payload, null, 2));
      console.log('🔄 [QUICK UPDATE] System Prompt Tasks:', systemPromptTasks);
      console.log('🔄 [QUICK UPDATE] Provider (Enhancement & Answer Gen):', providerToUse);

      const response = await fetch(apiUtils.buildApiUrl(`/conversations/${sessionId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        console.log('✅ Quick update saved successfully');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ Failed to save quick update:', errorData);
      }
    } catch (error) {
      console.error('❌ Error saving quick update:', error);
    }
  };

  const handleBack = () => {
    navigate(paths.dashboard.apps.knowledgeSearch);
  };

  return (
    <Box style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(98vh - 80px)',
      maxHeight: 'calc(98vh - 80px)',
      overflow: 'hidden'
    }}>
      {/* CSS Animations */}
      <style>{chatAnimations}</style>

      {/* Header */}
      <Paper p="md" withBorder style={{ borderBottom: '1px solid var(--mantine-color-gray-3)', flexShrink: 0 }}>
        <Group justify="space-between">
          <Group>
            <ActionIcon variant="subtle" onClick={handleBack}>
              <IconArrowLeft size={20} />
            </ActionIcon>
            <div>
              <Tooltip label="Click to go to Knowledge Search">
                <Anchor
                  component="button"
                  onClick={() => navigate(paths.dashboard.apps.knowledgeSearch)}
                  style={{
                    fontSize: 'var(--mantine-h3-font-size)',
                    fontWeight: 'var(--mantine-h3-font-weight)',
                    lineHeight: 'var(--mantine-h3-line-height)',
                    color: 'var(--mantine-color-blue-6)',
                    textDecoration: 'none',
                    cursor: 'pointer',
                    background: 'none',
                    border: 'none',
                    padding: 0
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.textDecoration = 'underline';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.textDecoration = 'none';
                  }}
                >
                  {sessionName}
                </Anchor>
              </Tooltip>

              {/* RAG Configuration Description */}
              <Stack gap="xs">
                <Tooltip
                  label="This describes your RAG agent configuration: query enhancement strategy, search settings, reranking, and answer generation mode"
                  multiline
                >
                  <Text size="xs" c="blue.6" style={{ fontStyle: 'italic' }}>
                    <IconInfoCircle size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    {generateRagDescription(selectedStrategy, enableReranking, enableLLMGeneration, topK, collectionName, savedEnhancementProvider, providers)}
                  </Text>
                </Tooltip>

              </Stack>
            </div>
          </Group>
          <Group>
            <Tooltip label="Reset messages">
              <ActionIcon
                variant="subtle"
                color="orange"
                onClick={handleResetMessages}
                loading={resetMessagesMutation.isPending}
              >
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Edit session name">
              <ActionIcon variant="subtle">
                <IconEdit size={16} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete session">
              <ActionIcon variant="subtle" color="red" onClick={() => setDeleteModalOpen(true)}>
                <IconTrash size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Paper>
      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Conversation"
        size="md"
        centered
      >
        <Stack gap="md">
          <Alert icon={<IconTrash size={16} />} title="Warning" color="red">
            <Text size="sm">
              Are you sure you want to delete this conversation?
            </Text>
            <Text size="sm" mt="xs">
              This action cannot be undone. All messages and conversation history will be permanently deleted.
            </Text>
          </Alert>
          <Group justify="flex-end" gap="xs">
            <Button variant="subtle" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button color="red" onClick={handleDeleteSession} loading={deleteConversationMutation.isPending}>
              Delete Conversation
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Messages Area - Full Width */}
      <Box
        ref={viewportRef}
        style={{
          flexGrow: 1,
          flexShrink: 1,
          flexBasis: 0,
          overflowY: 'scroll',
          padding: '16px 0' // No horizontal padding - let messages control their own margins
        }}
      >
        <Stack gap="md">
          {messages.length === 0 && !isLoadingHistory ? (
            <Box ta="center" py="xl">
              <IconMessageCircle size={48} color="var(--mantine-color-gray-4)" />
              <Text size="lg" c="dimmed" mt="md">
                Start a conversation
              </Text>
              <Text size="sm" c="dimmed">
                Ask questions about your knowledge base
              </Text>
            </Box>
          ) : (
            messages.map((message, index) => (
              message.role === 'assistant' ? (
                <Box
                  key={index}
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: '16px',
                    animation: 'slideInLeft 0.4s ease-out',
                  }}
                >
                  <Box
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      width: '92%',
                      marginLeft: '16px',
                      marginRight: 'auto',
                    }}
                  >
                    {/* Assistant Avatar */}
                    <Box
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--mantine-color-blue-6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '4px',
                      }}
                    >
                      <Text size="xs" c="white" fw={600}>
                        AI
                      </Text>
                    </Box>

                    {/* Message Content */}
                    <Box style={{ flex: 1 }}>
                      <StreamingMessage
                        content={message.content}
                        isStreaming={message.isStreaming || false}
                        timestamp={message.timestamp}
                        showSender={false}
                        senderName="Assistant"
                        metadata={message.metadata}
                      />

                      {/* Old Metadata Section - Now handled by EnhancedMessageRenderer */}
                      {false && message.metadata && !message.isStreaming && (
                        <Box mt="sm">
                          <Paper
                            p="sm"
                            radius="md"
                            style={{
                              backgroundColor: 'var(--mantine-color-gray-0)',
                              border: '1px solid var(--mantine-color-gray-2)',
                            }}
                          >
                            <Stack gap="xs">
                              <Group gap="xs" justify="space-between">
                                <Group gap="xs">
                                  <ThemeIcon size="sm" variant="light" color="blue">
                                    <IconInfoCircle size={14} />
                                  </ThemeIcon>
                                  <Text size="xs" fw={600} c="dimmed">Response Metadata</Text>
                                </Group>
                                <Group gap="xs">
                                  {message.metadata && (message.metadata as any).document_count && (
                                    <Badge size="xs" variant="light" color="blue">
                                      {(message.metadata as any).document_count} docs
                                    </Badge>
                                  )}
                                  {message.metadata && (message.metadata as any).enhancement_strategy && (
                                    <Badge size="xs" variant="light" color="purple">
                                      {(message.metadata as any).enhancement_strategy}
                                    </Badge>
                                  )}
                                  <ActionIcon
                                    size="xs"
                                    variant="subtle"
                                    color="dimmed"
                                    onClick={() => {
                                      const newExpanded = new Set(expandedMetadata);
                                      if (newExpanded.has(index)) {
                                        newExpanded.delete(index);
                                      } else {
                                        newExpanded.add(index);
                                      }
                                      setExpandedMetadata(newExpanded);
                                    }}
                                  >
                                    <IconChevronDown
                                      size={12}
                                      style={{
                                        transform: expandedMetadata.has(index) ? 'rotate(180deg)' : 'rotate(0deg)',
                                        transition: 'transform 0.2s ease'
                                      }}
                                    />
                                  </ActionIcon>
                                </Group>
                              </Group>

                              <Collapse in={expandedMetadata.has(index)}>
                                {/* Query Variants Used */}
                                {(() => {
                                })()}
                                {message.metadata?.enhanced_queries && (message.metadata as any).enhanced_queries.length > 0 && (
                                  <Box mb="sm">
                                    <Group gap="xs" mb={4}>
                                      <Text size="xs" fw={500} c="dimmed">
                                        Query Variants ({(message.metadata as any).enhanced_queries.length}):
                                      </Text>
                                      {(message.metadata as any).enhancement_strategy &&
                                        ((message.metadata as any).enhancement_strategy === 'augmented' ||
                                          (message.metadata as any).enhancement_strategy === 'multi_query' ||
                                          (message.metadata as any).enhancement_strategy === 'decomposition') && (
                                          <Badge size="xs" color="blue" variant="light">RRF Fusion</Badge>
                                        )}
                                    </Group>
                                    <Text component="div" size="xs" c="dimmed" p="xs" style={{ backgroundColor: 'var(--mantine-color-gray-0)', borderRadius: '4px', border: '1px solid var(--mantine-color-gray-2)', lineHeight: 1.4 }}>
                                      {(message.metadata as any).enhanced_queries.map((query: string, qIdx: number) => (
                                        <span key={qIdx}>
                                          <Badge size="xs" color="grape" variant="dot" style={{ marginRight: '4px' }}>
                                            {qIdx + 1}
                                          </Badge>
                                          {query}
                                          {qIdx < (message.metadata as any).enhanced_queries.length - 1 && ' • '}
                                        </span>
                                      ))}
                                    </Text>
                                  </Box>
                                )}

                                {/* Source URLs with Correlation IDs */}
                                {message.metadata?.source_urls && (message.metadata as any).source_urls.length > 0 && (
                                  <Box>
                                    <Text size="xs" fw={500} c="dimmed" mb="xs">
                                      Sources ({(message.metadata as any).source_urls.length}):
                                    </Text>
                                    <Stack gap="xs">
                                      {(() => {
                                      })()}
                                    </Stack>
                                  </Box>
                                )}
                              </Collapse>
                            </Stack>
                          </Paper>
                        </Box>
                      )}
                    </Box>
                  </Box>
                </Box>
              ) : (
                <Box
                  key={index}
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    marginBottom: '16px',
                    animation: 'slideInRight 0.4s ease-out',
                  }}
                >
                  <Box
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      width: '92%',
                      marginLeft: 'auto',
                      marginRight: '16px',
                      flexDirection: 'row-reverse',
                    }}
                  >
                    {/* User Avatar */}
                    <Box
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--mantine-color-green-6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '4px',
                      }}
                    >
                      <Text size="xs" c="white" fw={600}>
                        U
                      </Text>
                    </Box>

                    {/* Message Content */}
                    <Paper
                      p="md"
                      style={{
                        backgroundColor: 'var(--mantine-color-blue-6)',
                        color: 'white',
                        borderRadius: '18px 18px 4px 18px',
                        maxWidth: '100%',
                        wordWrap: 'break-word',
                      }}
                    >
                      <Text size="xs" c="white" style={{ lineHeight: '1.5' }}>
                        {message.content}
                      </Text>
                      <Text size="xs" c="rgba(255,255,255,0.7)" mt="xs">
                        {formatTimestamp(message.timestamp)}
                      </Text>
                    </Paper>
                  </Box>
                </Box>
              )
            ))
          )}
          {isLoadingHistory && (
            <Box ta="center" py="xl">
              <LoadingOverlay visible={true} />
              <Text size="sm" c="dimmed">Loading conversation history...</Text>
            </Box>
          )}
          {isLoading && !isLoadingHistory && (
            <Box
              style={{
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '16px',
                animation: 'slideInLeft 0.4s ease-out',
              }}
            >
              <Box
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  width: '92%',
                  marginLeft: '16px',
                  marginRight: 'auto',
                }}
              >
                {/* Assistant Avatar */}
                <Box
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--mantine-color-blue-6)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '4px',
                  }}
                >
                  <Text size="xs" c="white" fw={600}>
                    AI
                  </Text>
                </Box>

                {/* Typing Indicator */}
                <Paper
                  p="md"
                  style={{
                    backgroundColor: 'var(--mantine-color-gray-1)',
                    borderRadius: '18px 18px 18px 4px',
                    border: '1px solid var(--mantine-color-gray-3)',
                  }}
                >
                  <TypingIndicator message="Assistant is thinking..." />
                </Paper>
              </Box>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Stack>
      </Box>

      {/* Input Area - Cursor Style */}
      <Paper
        p="sm"
        withBorder
        style={{
          borderTop: '2px solid var(--mantine-color-blue-2)',
          flexShrink: 0,
          backgroundColor: '#fafbfc'
        }}
      >
        <Stack gap="sm">
          {/* Query Input - Top */}
          <Box>
            <Group gap="xs" align="center">
              <TextInput
                placeholder={messageMode === 'agent'
                  ? "Ask the agent to help with tasks or answer questions..."
                  : "Ask about your knowledge base or refine your query..."}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                size="md"
                radius="md"
                style={{
                  borderColor: isConnected ? undefined : 'var(--mantine-color-orange-4)',
                  transition: 'all 0.2s ease',
                  flex: 1,
                }}
                disabled={isLoading || isLoadingHistory}
                rightSection={
                  isLoading ? (
                    <IconLoader size={18} className="animate-spin" />
                  ) : !isConnected ? (
                    <IconLoader size={18} className="animate-spin" style={{ color: 'var(--mantine-color-orange-6)' }} />
                  ) : null
                }
              />
              {isConnected && !isLoading && (
                <Button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim()}
                  variant="filled"
                  size="md"
                  color="blue"
                  radius="md"
                  style={{ minWidth: '80px' }}
                  leftSection={<IconSend size={18} />}
                >
                  Send
                </Button>
              )}
            </Group>
          </Box>

          {/* Settings Bar - Bottom */}
          <Stack gap="xs">
            {/* Settings Row: Mode, Strategy, Model, Settings */}
            <Group gap="sm" justify="flex-start" align="flex-end" grow={false}>
              {/* Mode */}
              <Select
                placeholder="Mode"
                value={messageMode}
                onChange={(value) => {
                  const newMode = (value as 'agent' | 'rag') || 'agent';
                  setMessageMode(newMode);
                  // When user selects a mode, also update the enableKnowledgeAssistant setting
                  const newEnableKA = newMode === 'agent';
                  setEnableKnowledgeAssistant(newEnableKA);
                  console.log(`🔄 [MODE CHANGED] User selected: ${newMode} → enableKnowledgeAssistant=${newEnableKA}`);

                  // Auto-configure settings for Assistant Agent mode
                  let strategyUpdate = undefined;
                  let disableLLM = false;
                  let changesMessage = [];

                  if (newMode === 'agent') {
                    // 1. Set strategy to decomposition
                    if (selectedStrategy !== 'decomposition') {
                      const previousStrategy = selectedStrategy;
                      setSelectedStrategy('decomposition');
                      strategyUpdate = 'decomposition';
                      changesMessage.push(`• Strategy: "${previousStrategy || 'native'}" → "decomposition"`);
                      console.log(`🔄 [STRATEGY AUTO-CHANGED] ${previousStrategy || 'native'} → decomposition (Assistant Agent mode)`);
                    }

                    // 2. Disable LLM generation (supervisor handles everything)
                    if (enableLLMGeneration) {
                      setEnableLLMGeneration(false);
                      disableLLM = true;
                      changesMessage.push(`• LLM Generation: "enabled" → "disabled"`);
                      console.log(`🔄 [LLM GENERATION DISABLED] Supervisor agent handles response generation (Assistant Agent mode)`);
                    }

                    // Show notification if any changes were made
                    if (changesMessage.length > 0) {
                      notifications.show({
                        title: 'Settings Auto-Optimized for Assistant Agent',
                        message: (
                          <div>
                            <div style={{ marginBottom: '8px' }}>
                              Configuration automatically adjusted for optimal performance:
                            </div>
                            {changesMessage.map((msg, idx) => (
                              <div key={idx} style={{ fontSize: '12px', marginLeft: '4px' }}>{msg}</div>
                            ))}
                            <div style={{ marginTop: '8px', fontSize: '11px', opacity: 0.8 }}>
                              Assistant Agent uses full context from vector search and handles response generation internally.
                            </div>
                          </div>
                        ),
                        color: 'blue',
                        icon: <IconInfoCircle size={16} />,
                        autoClose: 10000,
                      });
                    }
                  }

                  // Save to database (include strategy and LLM generation settings if changed)
                  handleQuickUpdate({
                    mode: newMode,
                    ...(strategyUpdate && { strategy: strategyUpdate }),
                    ...(disableLLM && { disableLLMGeneration: true })
                  });
                }}
                data={[
                  { value: 'agent', label: '∞ Assistant Agent' },
                  { value: 'rag', label: '📚 RAG Agent' }
                ]}
                disabled={isLoading || isLoadingHistory}
                searchable={false}
                clearable={false}
                maxDropdownHeight={120}
                size="xs"
                w={120}
                styles={{
                  input: {
                    backgroundColor: messageMode === 'agent' ? '#ebf4ff' : '#f0f9ff',
                    border: messageMode === 'agent' ? '1px solid #4c6ef5' : '1px solid #339af0',
                    color: messageMode === 'agent' ? '#1971c2' : '#1094f1',
                    fontWeight: 600,
                    paddingLeft: '8px',
                    paddingRight: '4px',
                    height: '28px',
                    fontSize: '12px',
                    borderRadius: '6px',
                  },
                  dropdown: {
                    minWidth: '140px'
                  }
                }}
              />

              {/* Strategy */}
              <Select
                placeholder="Strategy"
                value={selectedStrategy}
                onChange={(value) => {
                  const newStrategy = value || 'native';
                  setSelectedStrategy(newStrategy);
                  // Save to database
                  handleQuickUpdate({ strategy: newStrategy });
                }}
                data={ENHANCEMENT_STRATEGIES.map(s => {
                  let label = s.label;
                  // For non-native strategies, append provider/model info if available
                  if (s.value !== 'native' && savedEnhancementProvider) {
                    // Get provider name from providers list
                    const providerName = providers?.find((p: any) => p.id === savedEnhancementProvider.id)?.name || savedEnhancementProvider.id;
                    label = `${s.label} (${providerName}/${savedEnhancementProvider.model_name})`;
                  }
                  return {
                    value: s.value,
                    label: label
                  };
                })}
                disabled={isLoading || isLoadingHistory}
                searchable={false}
                clearable={false}
                maxDropdownHeight={120}
                size="xs"
                w={280}
                styles={{
                  input: {
                    backgroundColor: '#f3e5f5',
                    border: '1px solid #9c27b0',
                    color: '#6a1b9a',
                    fontWeight: 600,
                    paddingLeft: '8px',
                    paddingRight: '4px',
                    height: '28px',
                    fontSize: '12px',
                    borderRadius: '6px',
                  },
                  dropdown: {
                    minWidth: '240px'
                  }
                }}
              />

              {/* Model - Only visible if LLM generation is enabled */}
              {enableLLMGeneration && (
                <Select
                  placeholder="Model"
                  value={selectedModel}
                  onChange={(value) => {
                    setSelectedModel(value);
                    // Update provider ID based on selected model
                    if (value) {
                      const provider = providers?.find(p =>
                        p.generative?.models?.includes(value)
                      );
                      if (provider) {
                        setSelectedProviderId(provider.id);
                      }
                      // Save to database
                      handleQuickUpdate({ model: value });
                    }
                  }}
                  data={providers?.flatMap(p =>
                    p.generative?.models?.map((m: string) => ({
                      value: m,
                      label: m.split('/').pop() || m
                    })) || []
                  ) || []}
                  disabled={isLoading || isLoadingHistory}
                  searchable
                  clearable
                  maxDropdownHeight={120}
                  size="xs"
                  w={140}
                  styles={{
                    input: {
                      backgroundColor: '#fff3e0',
                      border: '1px solid #ff9800',
                      color: '#e65100',
                      fontWeight: 600,
                      paddingLeft: '8px',
                      paddingRight: '4px',
                      height: '28px',
                      fontSize: '12px',
                      borderRadius: '6px',
                    },
                    dropdown: {
                      minWidth: '150px'
                    }
                  }}
                />
              )}

              {/* Spacer */}
              <Box style={{ flex: 1 }} />

              {/* Settings Icon */}
              <Tooltip label="Edit Conversation Settings">
                <ActionIcon
                  size="md"
                  variant="light"
                  onClick={() => {
                    navigate(paths.dashboard.apps.conversationCreate, {
                      state: { editingConversationId: sessionId }
                    });
                  }}
                  disabled={isLoading || isLoadingHistory}
                >
                  <IconSettings size={18} />
                </ActionIcon>
              </Tooltip>
            </Group>
          </Stack>
        </Stack>
      </Paper>

      {/* Workflow Progress Modal - Router dispatches to appropriate modal */}
      <WorkflowProgressModal
        opened={workflowState.isActive}
        onClose={() => { }}
        enableKnowledgeAssistant={messageMode === 'agent'}
        currentStage={workflowState.currentStage}
        completedStages={workflowState.completedStages}
        rerankingEnabled={enableReranking}
        enableLLMGeneration={enableLLMGeneration}
        metadata={{
          originalQuery: workflowState.originalQuery || undefined,
          enhancedQueries: workflowState.enhancedQueries || undefined,
          strategy: workflowState.strategy || selectedStrategy || undefined,
          documentCount: workflowState.documentCount,
          relevantCount: workflowState.relevantCount,
          indexType: workflowState.indexType,
          vectorDimension: workflowState.vectorDimension,
          searchTime: workflowState.searchTime,
          intent: workflowState.intent || undefined,
          stageDetails: workflowState.stageDetails,
          ragSubstages: workflowState.ragSubstages,
        }}
      />

      {/* Settings Modal */}
      <Modal
        opened={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        title={
          <Group gap="xs">
            <ThemeIcon
              size="md"
              variant="filled"
              style={{
                background: 'linear-gradient(135deg, #45c9bb 0%, #9dd245 100%)',
              }}
            >
              <IconSettings size={18} />
            </ThemeIcon>
            <Text fw={600}>Conversation Settings</Text>
          </Group>
        }
        size="xl"
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Configure query enhancement strategy, vector database collection, and answer generation for this conversation.
          </Text>

          <Divider label="Query Enhancement" labelPosition="left" />

          <Select
            label="Enhancement Strategy"
            placeholder="Select strategy"
            data={ENHANCEMENT_STRATEGIES.map((s) => ({
              value: s.value,
              label: s.label,
            }))}
            value={selectedStrategy}
            onChange={(value) => setSelectedStrategy(value || 'native')}
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
                  <List.Item>Return your configured Search Results Limit (the best matches after merging)</List.Item>
                </List>
                <Text size="xs" c="dimmed">
                  Example: With 5 query variants and limit=10, the system retrieves ~15 documents per variant, merges them via RRF, and returns your final 10 best documents.
                </Text>
              </Stack>
            </Alert>
          )}

          {/* Single query info for HyDE */}
          {selectedStrategy === 'hyde' && (
            <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
              <Text size="xs">
                <strong>Single Enhanced Query:</strong> This strategy generates one enhanced query variant.
                The system will search using this single enhanced query (no RRF merging needed).
              </Text>
            </Alert>
          )}

          <Divider label="Vector Database" labelPosition="left" />

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
                clearable
                disabled={collectionsLoading}
                description="Choose the vector database collection to search"
              />
            </Grid.Col>

            <Grid.Col span={6}>
              <NumberInput
                label="Search Results Limit"
                placeholder="Number of documents to retrieve"
                value={topK || undefined}
                onChange={(value) => {
                  setTopK(typeof value === 'number' ? value : undefined);
                }}
                min={5}
                max={30}
                description="Top K to retrieve from vector database (5-30)"
              />
            </Grid.Col>
          </Grid>

          <Divider label="Judge Ranker" labelPosition="left" />

          <Switch
            label="Enable Judge Ranker"
            description="Evaluate and rank retrieved documents to improve relevance"
            checked={enableReranking}
            onChange={(event) => {
              setEnableReranking(event.currentTarget.checked);
              if (!event.currentTarget.checked) {
                setSelectedRerankerId(null);
                setSelectedRerankerModel(null);
              } else {
                // When enabling judge ranker, default to LLM provider and model
                setSelectedRerankerId(selectedProviderId);
                setSelectedRerankerModel(selectedModel);
              }
            }}
          />

          {enableReranking && (
            <>
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text size="sm">
                  <strong>Dedicated Judge:</strong> Specialized models (Cohere, Voyage AI)
                  <br />
                  <strong>LLM as Judge:</strong> Any generative LLM for evaluation
                  <br />
                  <strong>No Provider:</strong> Uses conversation's main LLM (default)
                  <br />
                  <strong>Disabled:</strong> No judging, direct retrieval → answer
                </Text>
              </Alert>

              <Grid gutter="md">
                <Grid.Col span={6}>
                  <Select
                    label="Judge Provider (Optional)"
                    placeholder="Select a provider"
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
                            label: `${p.name} (LLM Judge)`,
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
                    disabled={providersLoading}
                    description="Choose a judge or LLM"
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
                    description="Choose the model"
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

          <Divider label="Generative Answer" labelPosition="left" />

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
                    renderOption={(item) => {
                      const provider = providers?.find(p => p.id === item.option.value);
                      const getProviderColor = (providerType: string) => {
                        switch (providerType) {
                          case 'openai': return 'green';
                          case 'anthropic': return 'orange';
                          case 'google': return 'blue';
                          case 'cohere': return 'red';
                          case 'voyage': return 'violet';
                          default: return 'gray';
                        }
                      };

                      return (
                        <Group gap="xs">
                          <ThemeIcon
                            size="sm"
                            variant="filled"
                            color={getProviderColor(provider?.provider_type || '')}
                          >
                            <Text size="xs" fw={700}>
                              {provider?.name?.charAt(0) || '?'}
                            </Text>
                          </ThemeIcon>
                          <Text size="sm">{item.option.label}</Text>
                        </Group>
                      );
                    }}
                  />
                </Grid.Col>

                <Grid.Col span={6}>
                  {selectedProviderId && providers ? (
                    <Select
                      label="LLM Provider Model"
                      placeholder="Select a model"
                      data={
                        providers
                          .find((p) => p.id === selectedProviderId)
                          ?.generative?.models.map((model) => ({
                            value: model,
                            label: model,
                          })) || []
                      }
                      value={selectedModel}
                      onChange={setSelectedModel}
                      searchable
                      required
                      description="Choose the LLM provider model for this conversation"
                    />
                  ) : (
                    <Select
                      label="Model"
                      placeholder="Select a provider first"
                      disabled
                      description="Choose a provider first to select a model"
                    />
                  )}
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

          <Divider label="Knowledge Assistant" labelPosition="left" />

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
                  <strong>How it works:</strong> Finds relevant info → Uses it to complete your task
                  <br />
                  <strong>Best for:</strong> "Write a summary...", "Generate code using our docs", "Create a plan..."
                </Text>
              </Alert>

              <SystemPromptManager
                conversationId={sessionId || ''}
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

          <Divider />

          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              color="gray"
              onClick={() => setSettingsModalOpen(false)}
              disabled={isSavingSettings}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              loading={isSavingSettings}
              leftSection={<IconCheck size={16} />}
              color="blue"
            >
              Save Settings
            </Button>
          </Group>
        </Stack>
      </Modal>

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
    </Box>
  );
}


