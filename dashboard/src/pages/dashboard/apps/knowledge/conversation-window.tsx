import { useDeleteConversation, useResetConversationMessages } from '@/api/resources/conversations';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { KnowledgeAssistantModal } from '@/components/knowledge-assistant-modal';
import { RAGPipelineModal } from '@/components/rag-pipeline-modal';
import { StreamingMessage } from '@/components/streaming-message';
import { TypingIndicator } from '@/components/typing-indicator';
import { apiEndpoints, apiUtils } from '@/config';
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
  collectionName?: string
): string => {
  const parts: string[] = [];

  // Strategy description with RRF info
  const strategyLabel = ENHANCEMENT_STRATEGIES.find(s => s.value === strategy)?.label || 'Unknown';

  if (strategy === 'native') {
    parts.push(`Using ${strategyLabel} (direct search)`);
  } else if (strategy === 'augmented' || strategy === 'multi_query' || strategy === 'decomposition') {
    parts.push(`Using ${strategyLabel} with RRF fusion`);
  } else if (strategy === 'hyde') {
    parts.push(`Using ${strategyLabel} (single enhanced query)`);
  } else {
    parts.push(`Using ${strategyLabel}`);
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

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

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

        // Load conversation settings - NO FALLBACKS, USE EXACT DB VALUES
        if (data.session) {
          setSelectedProviderId(data.session.llm_provider_id || null);
          setSelectedModel(data.session.llm_model_name || null);
          setSelectedStrategy(data.session.enhancement_config?.strategy || 'native');
          setCollectionName(data.session.collection_name || 'LongTermMemory');

          // Load reranking settings - exact values from DB
          const newEnableReranking = data.session.enable_reranking !== undefined ? data.session.enable_reranking : false;
          setEnableReranking(newEnableReranking);

          setSelectedRerankerId(data.session.reranker_provider_id || null);
          setSelectedRerankerModel(data.session.reranker_model_name || null);

          // Load LLM generation setting - exact value from DB
          const newEnableLLMGeneration = data.session.enable_llm_generation !== undefined ? data.session.enable_llm_generation : false;
          setEnableLLMGeneration(newEnableLLMGeneration);

          // Load top_k - exact value from DB
          setTopK(data.session.top_k);

          // Load supervisor setting - exact value from DB
          const newEnableKnowledgeAssistant = data.session.enable_knowledge_assistant !== undefined ? data.session.enable_knowledge_assistant : true;
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
        setIsConnected(true); // Reset to connected state since we connect on-demand
        setIsLoading(false);
        finalizeStreamingMessages();
      };

      wsRef.current.onerror = (error) => {
        setIsConnected(true); // Reset to connected state since we connect on-demand
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
            currentStage: null,
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
          // GUARD: Skip if using supervisor - these events are now handled in supervisor_progress
          if (enableKnowledgeAssistant) {
            console.log('⏭️ Skipping old query_enhancement handler - using supervisor instead');
            break;
          }

          console.log('✨ QUERY ENHANCEMENT MESSAGE RECEIVED:', {
            enhanced_queries: data?.data?.enhanced_queries,
            strategy: data?.data?.strategy || data?.strategy
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
          // GUARD: Skip if using supervisor - these events are now handled in supervisor_progress
          if (enableKnowledgeAssistant) {
            console.log('⏭️ Skipping old document_retrieval handler - using supervisor instead');
            break;
          }

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
          // GUARD: Skip if using supervisor - these events are now handled in supervisor_progress
          if (enableKnowledgeAssistant) {
            console.log('⏭️ Skipping old document_judging handler - using supervisor instead');
            break;
          }

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
          // GUARD: Skip if using supervisor - these events are now handled in supervisor_progress
          if (enableKnowledgeAssistant) {
            console.log('⏭️ Skipping old response_generation handler - using supervisor instead');
            break;
          }

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

          if (textChunk) {
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
                // Check if this is the placeholder "Starting" message - replace it instead of appending
                const isPlaceholder = lastMessage.content.includes('🤖 Starting conversation');

                // Update existing streaming message
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: isPlaceholder ? textChunk : lastMessage.content + textChunk,
                    isStreaming: true
                  }
                ];
              } else {
                // Create new streaming message
                return [
                  ...prev,
                  {
                    role: 'assistant',
                    content: textChunk,
                    timestamp: new Date(),
                    isStreaming: true
                  }
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

        case 'workflow_progress': {
          // Handle RAG substage progress events from LangGraph node execution
          // Backend sends current_node and stage (start and complete events)
          const currentNode = data?.current_node || '';
          const stageFromEvent = data?.stage || '';

          // Check if this is a COMPLETE event (has query_variants, document_count, etc.)
          const isCompleteEvent = stageFromEvent.endsWith('_complete');

          // Extract data from complete events
          const queryVariants = data?.data?.query_variants || [];
          const strategyFromData = data?.data?.strategy || '';
          const documentCount = data?.data?.document_count || 0;
          const relevantCount = data?.data?.relevant_documents || 0;
          const avgScore = data?.data?.avg_score;

          console.log(`🔄 [WORKFLOW PROGRESS] stage=${stageFromEvent}, current_node=${currentNode}, isComplete=${isCompleteEvent}, queryVariants=${queryVariants.length}, documentCount=${documentCount}`);

          // Map LangGraph node names to UI stage names
          const nodeToStageMap: Record<string, string> = {
            'augmented_strategy_node': 'query_enhancement',
            'multi_query_strategy_node': 'query_enhancement',
            'hyde_strategy_node': 'query_enhancement',
            'decomposition_strategy_node': 'query_enhancement',
            'document_retriever': 'document_retrieval',
            'document_judger': 'document_judging',
            'answer_generator': 'answer_generation',
            'raw_response_formatter': 'answer_generation',
          };

          // Use stage from event if available, otherwise map from node name
          let mappedStage = stageFromEvent.replace('_complete', '');
          if (!mappedStage) {
            mappedStage = nodeToStageMap[currentNode] || currentNode;
          }

          setWorkflowState(prev => {
            // Check if we actually need to update state
            const newCompleted = [...prev.completedStages];
            const newRagSubstages = [...(prev.ragSubstages || [])];
            const newStageDetails = { ...prev.stageDetails };

            let hasChanges = false;

            // Add this substage to ragSubstages if it's a RAG-related stage (only once per stage)
            if (mappedStage === 'query_enhancement' && !newRagSubstages.includes('query_enhancement')) {
              newRagSubstages.push('query_enhancement');
              hasChanges = true;
            } else if (mappedStage === 'document_retrieval' && !newRagSubstages.includes('document_retrieval')) {
              newRagSubstages.push('document_retrieval');
              hasChanges = true;
            } else if (mappedStage === 'document_judging' && !newRagSubstages.includes('document_judging')) {
              newRagSubstages.push('document_judging');
              hasChanges = true;
            } else if (mappedStage === 'answer_generation' && !newRagSubstages.includes('answer_generation')) {
              newRagSubstages.push('answer_generation');
              hasChanges = true;
            }

            // Build updated state only if there are changes
            if (isCompleteEvent) {
              if (!newCompleted.includes(mappedStage)) {
                newCompleted.push(mappedStage);
                hasChanges = true;
              }

              // Store detailed data for the completed stage
              newStageDetails[mappedStage] = {
                message: data?.message || '',
                data: data?.data || {},
                timestamp: new Date().toISOString(),
                execution_time_ms: data?.execution_time_ms || 0,
              };
              hasChanges = true;

              // Extract and capture data based on stage
              const newState: any = {
                ...prev,
                ragSubstages: newRagSubstages,
                completedStages: newCompleted,
                stageDetails: newStageDetails,
              };

              if (mappedStage === 'query_enhancement' && queryVariants.length > 0) {
                newState.enhancedQueries = queryVariants;
                newState.strategy = strategyFromData || prev.strategy;
                console.log(`✨ Enhanced queries captured from complete event:`, queryVariants);
              } else if (mappedStage === 'document_retrieval' && documentCount > 0) {
                newState.documentCount = documentCount;
                console.log(`📚 Document count captured:`, documentCount);
              } else if (mappedStage === 'document_judging' && relevantCount >= 0) {
                newState.relevantCount = relevantCount;
                console.log(`⚖️ Relevant count captured:`, relevantCount);
              }

              return hasChanges ? newState : prev;
            } else {
              // START event - check if stage actually changed
              if (prev.currentStage !== mappedStage) {
                console.log(`▶️ Starting stage:`, mappedStage);
                return {
                  ...prev,
                  currentStage: mappedStage,
                  ragSubstages: newRagSubstages,
                };
              }
            }

            // Return prev if no changes (don't call setState)
            return prev;
          });
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

              if (completedStage === 'query_enhancement' && data?.data?.query_variants) {
                updateState.enhancedQueries = data.data.query_variants;
                updateState.strategy = data.data.strategy || prev.strategy;
                console.log(`✨ Enhanced queries captured:`, data.data.query_variants);
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
          const errorMessage: Message = {
            role: 'assistant',
            content: message || error || 'An error occurred during the conversation.',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMessage]);
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

    try {
      setIsSavingSettings(true);
      const token = localStorage.getItem('jwt_token');

      // Validate LLM provider and model when generative answer is enabled
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

      const payload: any = {
        llm_provider_id: enableLLMGeneration ? selectedProviderId : null,
        llm_model_name: enableLLMGeneration ? selectedModel : null,
        enhancement_strategy: selectedStrategy !== 'none' ? selectedStrategy : null,
        collection_name: collectionName,
        enable_reranking: enableReranking,
        relevance_threshold: relevanceThreshold,
        reranker_provider_id: enableReranking ? selectedRerankerId : null,
        reranker_model_name: enableReranking ? selectedRerankerModel : null,
        enable_llm_generation: enableLLMGeneration,
        top_k: topK,
        enable_knowledge_assistant: enableKnowledgeAssistant,
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
              <Group gap="xs">
                <Text size="sm" c="dimmed">Session ID: {sessionId}</Text>
                <Tooltip label="Real-time WebSocket connection for streaming AI responses">
                  <Badge
                    size="xs"
                    color="green"
                    variant="light"
                    leftSection={
                      <Box style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }} />
                    }
                  >
                    Ready
                  </Badge>
                </Tooltip>
              </Group>
              {/* RAG Configuration Description */}
              <Stack gap="xs">
                <Tooltip
                  label="This describes your RAG agent configuration: query enhancement strategy, search settings, reranking, and answer generation mode"
                  multiline
                >
                  <Text size="xs" c="blue.6" style={{ fontStyle: 'italic' }}>
                    <IconInfoCircle size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    {generateRagDescription(selectedStrategy, enableReranking, enableLLMGeneration, topK, collectionName)}
                  </Text>
                </Tooltip>
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
              }}
              disabled={isLoading || isLoadingHistory}
              rightSection={
                isLoading ? (
                  <IconLoader size={18} className="animate-spin" style={{ marginRight: '12px' }} />
                ) : !isConnected ? (
                  <IconLoader size={18} className="animate-spin" style={{ color: 'var(--mantine-color-orange-6)', marginRight: '12px' }} />
                ) : (
                  <Button
                    onClick={sendMessage}
                    disabled={!inputMessage.trim()}
                    variant="filled"
                    size="sm"
                    color="blue"
                    radius="md"
                    style={{ marginRight: '4px' }}
                    leftSection={<IconSend size={16} />}
                  >
                    Send
                  </Button>
                )
              }
            />
          </Box>

          {/* Settings Bar - Bottom */}
          <Stack gap="xs">
            {/* Settings Row: Mode, Strategy, Model, Settings */}
            <Group gap="sm" justify="flex-start" align="flex-end" grow={false}>
              {/* Mode */}
              <Select
                placeholder="Mode"
                value={messageMode}
                onChange={(value) => setMessageMode((value as 'agent' | 'rag') || 'agent')}
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
                onChange={(value) => setSelectedStrategy(value || 'native')}
                data={ENHANCEMENT_STRATEGIES.map(s => ({
                  value: s.value,
                  label: s.label
                }))}
                disabled={isLoading || isLoadingHistory}
                searchable={false}
                clearable={false}
                maxDropdownHeight={120}
                size="xs"
                w={220}
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

              {/* Model - Always visible, shows all available models */}
              <Select
                placeholder="Model"
                value={selectedModel}
                onChange={(value) => setSelectedModel(value)}
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

              {/* Spacer */}
              <Box style={{ flex: 1 }} />

              {/* Settings Icon */}
              <Tooltip label="Advanced Settings">
                <ActionIcon
                  size="md"
                  variant="light"
                  onClick={async () => {
                    await loadConversationHistory();
                    setSettingsModalOpen(true);
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

      {/* Workflow Progress Modal - Show correct modal based on messageMode */}
      {messageMode === 'agent' ? (
        <KnowledgeAssistantModal
          opened={workflowState.isActive}
          onClose={() => { }}
          currentStage={workflowState.currentStage}
          completedStages={workflowState.completedStages}
          enableLLMGeneration={enableLLMGeneration}
          metadata={{
            intent: workflowState.intent || undefined,
            strategy: workflowState.strategy || undefined,
            documentCount: workflowState.documentCount,
            relevantCount: workflowState.relevantCount,
            stageDetails: workflowState.stageDetails,
            ragSubstages: workflowState.ragSubstages,
          }}
        />
      ) : (
        <RAGPipelineModal
          opened={workflowState.isActive}
          onClose={() => { }}
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
            stageDetails: workflowState.stageDetails,
            ragSubstages: workflowState.ragSubstages,
          }}
        />
      )}

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
            <Alert icon={<IconInfoCircle size={16} />} color="grape" variant="light">
              <Text size="sm">
                <strong>Knowledge Assistant Mode:</strong> AI searches your knowledge base AND performs tasks using what it finds.
                <br />
                <strong>How it works:</strong> Finds relevant info → Uses it to complete your task
                <br />
                <strong>Best for:</strong> "Write a summary...", "Generate code using our docs", "Create a plan..."
              </Text>
            </Alert>
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


