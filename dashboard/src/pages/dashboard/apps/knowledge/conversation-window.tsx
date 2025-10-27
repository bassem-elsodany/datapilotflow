import { useResetConversationMessages } from '@/api/resources/conversations';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { StreamingMessage } from '@/components/streaming-message';
import { TypingIndicator } from '@/components/typing-indicator';
import { WorkflowProgressModal } from '@/components/workflow-progress-modal';
import { apiEndpoints, apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Collapse,
  Divider,
  Grid,
  Group,
  LoadingOverlay,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  ThemeIcon,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconChevronDown,
  IconEdit,
  IconExternalLink,
  IconInfoCircle,
  IconLoader,
  IconMessageCircle,
  IconRefresh,
  IconSend,
  IconSettings,
  IconTrash
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
    enhanced_query?: string;
  };
}

// Query enhancement strategies
const ENHANCEMENT_STRATEGIES = [
  { value: 'native', label: 'Native RAG' },
  { value: 'augmented', label: 'Augmented (Best Coverage)' },
  { value: 'step_back', label: 'Step-Back' },
  { value: 'multi_query', label: 'Multi-Query' },
  { value: 'hyde', label: 'HyDE' },
  { value: 'decomposition', label: 'Decomposition' },
  { value: 'rag_fusion', label: 'RAG Fusion' },
];

export default function ConversationWindow() {
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

  // Settings modal state
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('native');
  const [collectionName, setCollectionName] = useState('LongTermMemory');
  const [enableReranking, setEnableReranking] = useState(false);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [enableLLMGeneration, setEnableLLMGeneration] = useState(true);
  const [topK, setTopK] = useState<number | undefined>(undefined);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [expandedMetadata, setExpandedMetadata] = useState<Set<number>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const resetMessagesMutation = useResetConversationMessages();

  // Update reranker defaults when LLM provider or model changes
  useEffect(() => {
    if (enableReranking && selectedProviderId && selectedModel) {
      setSelectedRerankerId(selectedProviderId);
      setSelectedRerankerModel(selectedModel);
    }
  }, [selectedProviderId, selectedModel, enableReranking]);

  // Enhanced workflow visualization state
  const [workflowState, setWorkflowState] = useState<{
    currentStage: string | null;
    completedStages: string[];
    originalQuery: string | null;
    enhancedQuery: string | null;
    strategy: string | null;
    documentCount: number;
    relevantCount: number;
    rerankingEnabled: boolean;
    indexType: string;
    vectorDimension: number;
    searchTime: number;
    isActive: boolean;
  }>({
    currentStage: null,
    completedStages: [],
    originalQuery: null,
    enhancedQuery: null,
    strategy: null,
    documentCount: 0,
    relevantCount: 0,
    rerankingEnabled: enableReranking,
    indexType: 'HNSW',
    vectorDimension: 1536,
    searchTime: 0,
    isActive: false,
  });

  // Fetch data
  const { data: providers, isLoading: providersLoading } = useGetActiveModelProviders();
  const { data: collections, isLoading: collectionsLoading } = useGetCollections();

  // Helper function to finalize streaming messages
  const finalizeStreamingMessages = () => {
    setMessages(prev => {
      const updatedMessages = [...prev];
      const lastMessage = updatedMessages[updatedMessages.length - 1];
      if (lastMessage && lastMessage.isStreaming) {
        lastMessage.isStreaming = false;
      }
      return updatedMessages;
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
          
          console.log('✅ Loaded conversation settings:', {
            enableReranking: newEnableReranking,
            enableLLMGeneration: newEnableLLMGeneration,
            topK: data.session.top_k,
            strategy: data.session.enhancement_config?.strategy
          });
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
      const wsEndpoint = apiEndpoints.agent.websocket.query;
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
          handleWebSocketMessage(data);
        } catch (error) {
          // Silently handle parsing errors
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
    const { stage, message, error, chunk } = data;
    const response = data.response || data.data?.response;

    switch (stage) {
      case 'starting':
      case 'workflow_started':
        // Initialize enhanced workflow visualization
        console.log('🔍 Initializing workflow state:', {
          strategy: data?.data?.strategy || data?.strategy || selectedStrategy,
          rerankingEnabled: enableReranking,
          enableLLMGeneration: enableLLMGeneration
        });

        setWorkflowState({
          currentStage: null,
          completedStages: [],
          originalQuery: inputMessage,
          enhancedQuery: null,
          strategy: data?.data?.strategy || data?.strategy || selectedStrategy,
          documentCount: 0,
          relevantCount: 0,
          rerankingEnabled: enableReranking,
          indexType: 'HNSW',
          vectorDimension: 1536,
          searchTime: 0,
          isActive: true,
        });
        break;

      case 'query_enhancement':
      case 'query_enhancement_complete':
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

        // Update workflow state for query enhancement
        setWorkflowState(prev => ({
          ...prev,
          currentStage: 'query_enhancement',
          enhancedQuery: data?.data?.enhanced_query || data?.enhanced_query || null,
        }));
        break;

      case 'document_retrieval':
      case 'document_retrieval_complete':
        console.log('🔄 DOCUMENT RETRIEVAL - Current messages count:', messages.length);
        // Create or update the streaming message with document retrieval status
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          console.log('🔄 Last message:', lastMessage?.content, 'isStreaming:', lastMessage?.isStreaming);

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

          // Add current stage to completed if not already there
          if (prev.currentStage === 'document_judging' && !newCompleted.includes('document_judging')) {
            newCompleted.push('document_judging');
          } else if (prev.currentStage === 'document_retrieval' && !newCompleted.includes('document_retrieval')) {
            newCompleted.push('document_retrieval');
          } else if (prev.currentStage === 'query_enhancement' && !newCompleted.includes('query_enhancement')) {
            newCompleted.push('query_enhancement');
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
        }
        break;

      case 'completed':
        // Handle completion from agent WebSocket
        const metadata = data.data ? {
          source_urls: data.data.source_urls || [],
          correlation_ids: data.data.correlation_ids || [],
          chunk_ids: data.data.chunk_ids || [],
          document_count: data.data.document_count || 0,
          enhancement_strategy: data.data.enhancement_strategy,
          enhanced_query: data.data.enhanced_query,
        } : undefined;

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

        setIsLoading(false);
        finalizeStreamingMessages();

        // Mark workflow as complete
        setWorkflowState(prev => ({
          ...prev,
          currentStage: null,
          completedStages: [...prev.completedStages, 'response_generation'],
          isActive: false,
        }));
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
        console.log('Unknown stage:', stage, data);
        break;
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
        reranker_provider_id: enableReranking ? selectedRerankerId : null,
        reranker_model_name: enableReranking ? selectedRerankerModel : null,
        enable_llm_generation: enableLLMGeneration,
        top_k: topK,
      };

      console.log('💾 Saving conversation settings:', payload);

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

        notifications.show({
          title: 'Success',
          message: 'Conversation settings updated successfully',
          color: 'green',
          icon: <IconCheck size={16} />,
        });
        setSettingsModalOpen(false);

        // Reload conversation data to reflect new settings
        await loadConversationHistory();
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
      height: 'calc(100vh - 80px)',
      maxHeight: 'calc(100vh - 80px)',
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
                <Text size="xs" c="dimmed">•</Text>
                <Text size="xs" c="dimmed">Endpoint: {apiEndpoints.agent.websocket.query}</Text>
              </Group>
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
              <ActionIcon variant="subtle" color="red">
                <IconTrash size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Paper>

      {/* Messages Area - Full Width */}
      <Box
        ref={viewportRef}
        style={{
          flexGrow: 1,
          flexShrink: 1,
          flexBasis: 0,
          overflowY: 'scroll',
          padding: 'var(--mantine-spacing-md)'
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
                      maxWidth: '85%',
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
                      />

                      {/* Metadata Section */}
                      {message.metadata && !message.isStreaming && (
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
                                  {message.metadata.document_count && (
                                    <Badge size="xs" variant="light" color="blue">
                                      {message.metadata.document_count} docs
                                    </Badge>
                                  )}
                                  {message.metadata.enhancement_strategy && (
                                    <Badge size="xs" variant="light" color="purple">
                                      {message.metadata.enhancement_strategy}
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
                                {/* Source URLs with Correlation IDs */}
                                {message.metadata.source_urls && message.metadata.source_urls.length > 0 && (
                                  <Box>
                                    <Text size="xs" fw={500} c="dimmed" mb="xs">
                                      Sources ({message.metadata.source_urls.length}):
                                    </Text>
                                    <Stack gap="xs">
                                      {(() => {
                                        // Group sources by URL and collect chunk IDs
                                        const urlGroups: { [url: string]: string[] } = {};

                                        console.log('🔍 Frontend source_urls:', message.metadata.source_urls);
                                        console.log('🔍 Frontend chunk_ids:', message.metadata.chunk_ids);

                                        message.metadata.source_urls.forEach((url, urlIndex) => {
                                          const chunkId = message.metadata?.chunk_ids?.[urlIndex];
                                          if (!urlGroups[url]) {
                                            urlGroups[url] = [];
                                          }
                                          if (chunkId) {
                                            urlGroups[url].push(chunkId);
                                          }
                                        });

                                        console.log('🔍 Frontend urlGroups:', urlGroups);

                                        return Object.entries(urlGroups).map(([url, chunkIds], groupIndex) => (
                                          <Group key={groupIndex} gap="xs" align="flex-start">
                                            <ThemeIcon size="xs" variant="light" color="green">
                                              <IconExternalLink size={12} />
                                            </ThemeIcon>
                                            <Box style={{ flex: 1 }}>
                                              <Anchor
                                                href={url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                size="xs"
                                                style={{ wordBreak: 'break-all' }}
                                              >
                                                {url}
                                              </Anchor>
                                              {chunkIds.length > 0 && (
                                                <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace', marginTop: '2px' }}>
                                                  ({chunkIds.join(', ')})
                                                </Text>
                                              )}
                                            </Box>
                                          </Group>
                                        ));
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
                      maxWidth: '85%',
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
                  maxWidth: '85%',
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

      {/* Input Area - Full Width Below Both Columns */}
      <Paper p="md" withBorder style={{ borderTop: '1px solid var(--mantine-color-gray-3)', flexShrink: 0 }}>
        <Stack gap="xs">
          <Group gap="md" align="flex-end">
            <Box style={{ flex: 1 }}>
              <TextInput
                placeholder="Type your message..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                style={{
                  borderColor: isConnected ? undefined : 'var(--mantine-color-orange-4)',
                  transition: 'border-color 0.3s ease',
                }}
                disabled={isLoading || isLoadingHistory}
                rightSection={
                  !isConnected && (
                    <IconLoader size={16} className="animate-spin" style={{ color: 'var(--mantine-color-orange-6)' }} />
                  )
                }
              />
            </Box>
            <Button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || isLoadingHistory}
              leftSection={
                isLoading ? (
                  <IconLoader size={16} className="animate-spin" />
                ) : (
                  <IconSend size={16} />
                )
              }
              loading={isLoading}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </Button>
            <Tooltip label="Conversation Settings">
              <ActionIcon
                size="lg"
                variant="light"
                color="blue"
                onClick={async () => {
                  // Reload conversation data to get latest settings FIRST
                  await loadConversationHistory();
                  // Then open the modal
                  setSettingsModalOpen(true);
                }}
                disabled={isLoading || isLoadingHistory}
              >
                <IconSettings size={18} />
              </ActionIcon>
            </Tooltip>
          </Group>

          {/* Current Settings Display */}
          <Group gap="md" px="xs">
            {enableLLMGeneration && (
              <>
                <Text size="xs" c="dimmed">
                  Provider: {selectedProviderId ?
                    providers?.find(p => p.id === selectedProviderId)?.name || 'Unknown' :
                    'Default'}
                  {selectedModel && ` (${selectedModel})`}
                </Text>
                <Text size="xs" c="dimmed">•</Text>
              </>
            )}
            <Text size="xs" c="dimmed">
              Strategy: {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.label || 'None'}
            </Text>
            <Text size="xs" c="dimmed">•</Text>
            <Text size="xs" c="dimmed">
              Collection: {collectionName}
            </Text>
            <Text size="xs" c="dimmed">•</Text>
            <Text size="xs" c="dimmed">
              Reranking: {enableReranking ? (
                selectedRerankerId ?
                  `${providers?.find(p => p.id === selectedRerankerId)?.name || 'Unknown'}${selectedRerankerModel ? ` (${selectedRerankerModel})` : ''}` :
                  'LLM Judging'
              ) : 'Disabled'}
            </Text>
            <Text size="xs" c="dimmed">•</Text>
            <Text size="xs" c="dimmed">
              Answer: {enableLLMGeneration ? 'Generative' : 'Raw Results'}
            </Text>
          </Group>
        </Stack>
      </Paper>

      {/* Enhanced Workflow Progress Modal */}
      <WorkflowProgressModal
        opened={workflowState.isActive}
        onClose={() => { }}
        currentStage={workflowState.currentStage}
        completedStages={workflowState.completedStages}
        rerankingEnabled={enableReranking}
        enableLLMGeneration={enableLLMGeneration}
        metadata={{
          originalQuery: workflowState.originalQuery || undefined,
          enhancedQuery: workflowState.enhancedQuery || undefined,
          strategy: workflowState.strategy || undefined,
          documentCount: workflowState.documentCount,
          relevantCount: workflowState.relevantCount,
          indexType: workflowState.indexType,
          vectorDimension: workflowState.vectorDimension,
          searchTime: workflowState.searchTime,
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
        size="lg"
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
                  console.log('🔍 NumberInput onChange:', value, 'current topK state:', topK);
                  setTopK(typeof value === 'number' ? value : undefined);
                }}
                min={3}
                max={10}
                description="Top K to retrieve from vector database (3-10)"
              />
            </Grid.Col>
          </Grid>

          <Divider label="Document Reranking" labelPosition="left" />

          <Switch
            label="Enable Document Reranking"
            description="Rerank retrieved documents to improve relevance"
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
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text size="sm">
                  <strong>Dedicated Reranker:</strong> Specialized models (Cohere, Voyage AI)
                  <br />
                  <strong>LLM as Reranker:</strong> Any generative LLM for judging
                  <br />
                  <strong>No Provider:</strong> Uses conversation's main LLM (default)
                  <br />
                  <strong>Disabled:</strong> No reranking, direct retrieval → answer
                </Text>
              </Alert>

              <Grid gutter="md">
                <Grid.Col span={6}>
                  <Select
                    label="Reranker Provider (Optional)"
                    placeholder="Select a provider"
                    data={[
                      {
                        group: 'Specialized Rerankers',
                        items: providers
                          ?.filter((p) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
                          .map((p) => ({
                            value: p.id,
                            label: `${p.name} (Dedicated)`,
                          })) || []
                      },
                      {
                        group: 'LLMs as Rerankers',
                        items: providers
                          ?.filter((p) => p.generative && p.generative.models && p.generative.models.length > 0 && (!p.reranker || !p.reranker.models || p.reranker.models.length === 0))
                          .map((p) => ({
                            value: p.id,
                            label: `${p.name} (LLM)`,
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
                    description="Choose reranker or LLM"
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
                    description="Choose the model"
                  />
                </Grid.Col>
              </Grid>
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
    </Box>
  );
}


