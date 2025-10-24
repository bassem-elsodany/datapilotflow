import { useResetConversationMessages } from '@/api/resources/conversations';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { StreamingMessage } from '@/components/streaming-message';
import { TypingIndicator } from '@/components/typing-indicator';
import { apiEndpoints, apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Divider,
  Grid,
  Group,
  LoadingOverlay,
  Modal,
  Paper,
  ScrollArea,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconEdit,
  IconFilter,
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
}

// Query enhancement strategies
const ENHANCEMENT_STRATEGIES = [
  { value: 'native', label: 'Native RAG (Recommended)' },
  { value: 'augmented', label: 'Augmented (Best Coverage)' },
  { value: 'step_back', label: 'Step-Back' },
  { value: 'multi_query', label: 'Multi-Query' },
  { value: 'hyde', label: 'HyDE' },
  { value: 'decomposition', label: 'Decomposition' },
  { value: 'rag_fusion', label: 'RAG Fusion' },
];

export default function ConversationWindow() {
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
  const [enableReranking, setEnableReranking] = useState(true);
  const [selectedRerankerId, setSelectedRerankerId] = useState<string | null>(null);
  const [selectedRerankerModel, setSelectedRerankerModel] = useState<string | null>(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const resetMessagesMutation = useResetConversationMessages();

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

  // Scroll to bottom when new messages arrive (but not during initial load)
  useEffect(() => {
    // Only auto-scroll if we're not loading history and there are messages
    // Also check if the last message is recent (within last 5 seconds) to avoid scrolling on history load
    if (!isLoadingHistory && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      const now = new Date();
      const messageTime = new Date(lastMessage.timestamp);
      const timeDiff = now.getTime() - messageTime.getTime();

      // Only auto-scroll if the message is very recent (within 5 seconds) or if it's streaming
      if (timeDiff < 5000 || lastMessage.isStreaming) {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
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

      const fetchPromise = apiUtils.apiRequest(`/conversations/${sessionId}`);

      const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

      if (response.ok) {
        const data = await response.json();
        setSessionName(data.session?.name || 'Conversation');

        // Load conversation settings
        if (data.session) {
          setSelectedProviderId(data.session.llm_provider_id || null);
          setSelectedModel(data.session.llm_model_name || null);
          setSelectedStrategy(data.session.enhancement_config?.strategy || 'native');
          setCollectionName(data.session.collection_name || 'LongTermMemory');
          setEnableReranking(data.session.enable_reranking !== undefined ? data.session.enable_reranking : true);
          setSelectedRerankerId(data.session.reranker_provider_id || null);
          setSelectedRerankerModel(data.session.reranker_model_name || null);
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

    // Debug logging
    console.log('WebSocket message:', { stage, message, hasResponse: !!response, hasChunk: !!chunk });

    switch (stage) {
      case 'starting':
        // Show starting status
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: '🤖 Starting conversation...',
            timestamp: new Date(),
            isStreaming: true
          }
        ]);
        break;

      case 'query_enhancement':
      case 'query_enhancement_complete':
        // Show query enhancement status
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
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
        break;

      case 'document_retrieval':
      case 'document_retrieval_complete':
        // Show document retrieval status
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
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
        break;

      case 'document_judging':
        // Show document judging status
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
        break;

      case 'response_generation':
        // Show AI generation status
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
        break;

      case 'streaming_response':
        // Handle streaming response chunks from agent
        if (chunk) {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              // Update existing streaming message
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: lastMessage.content + chunk,
                  isStreaming: true
                }
              ];
            } else {
              // Create new streaming message
              return [
                ...prev,
                {
                  role: 'assistant',
                  content: chunk,
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
        if (response) {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              // Update the streaming message to final
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: response,
                  isStreaming: false
                }
              ];
            } else {
              // Add new final message
              return [
                ...prev,
                {
                  role: 'assistant',
                  content: response,
                  timestamp: new Date(),
                  isStreaming: false
                }
              ];
            }
          });
        }
        setIsLoading(false);
        finalizeStreamingMessages();
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

    try:
    setIsSavingSettings(true);
    const token = localStorage.getItem('jwt_token');

    const payload: any = {
      llm_provider_id: selectedProviderId,
      llm_model_name: selectedModel,
      enhancement_strategy: selectedStrategy !== 'none' ? selectedStrategy : null,
      collection_name: collectionName,
      enable_reranking: enableReranking,
      reranker_provider_id: enableReranking ? selectedRerankerId : null,
      reranker_model_name: enableReranking ? selectedRerankerModel : null,
    };

    const response = await fetch(apiUtils.buildApiUrl(`/conversations/${sessionId}/config`), {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
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
  <Box display="flex" style={{ flexDirection: 'column', flex: 1, minHeight: 0 }}>
    {/* Header */}
    <Paper p="md" withBorder style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
      <Group justify="space-between">
        <Group>
          <ActionIcon variant="subtle" onClick={handleBack}>
            <IconArrowLeft size={20} />
          </ActionIcon>
          <div>
            <Title order={3}>{sessionName}</Title>
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

    {/* Messages Area */}
    <ScrollArea style={{ flex: 1 }} p="md">
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
              <StreamingMessage
                key={index}
                content={message.content}
                isStreaming={message.isStreaming || false}
                timestamp={message.timestamp}
                showSender={!message.isStreaming || !message.content.startsWith('🤖') && !message.content.startsWith('🔍') && !message.content.startsWith('🧠')}
              />
            ) : (
              <Paper
                key={index}
                p="md"
                style={{
                  backgroundColor: 'var(--mantine-color-blue-0)',
                  alignSelf: 'flex-end',
                  maxWidth: '80%',
                  animation: 'fadeIn 0.3s ease-out',
                }}
              >
                <Text size="sm" fw={500} mb="xs">
                  You
                </Text>
                <Text size="sm">{message.content}</Text>
                <Text size="xs" c="dimmed" mt="xs">
                  {formatTimestamp(message.timestamp)}
                </Text>
              </Paper>
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
          <Paper p="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
            <TypingIndicator message="Assistant is thinking..." />
          </Paper>
        )}
        <div ref={messagesEndRef} />
      </Stack>
    </ScrollArea>

    {/* Input Area */}
    <Paper p="md" withBorder style={{ borderTop: '1px solid var(--mantine-color-gray-3)' }}>
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
              onClick={() => setSettingsModalOpen(true)}
              disabled={isLoading || isLoadingHistory}
            >
              <IconSettings size={18} />
            </ActionIcon>
          </Tooltip>
        </Group>

        {/* Current Settings Display */}
        <Group gap="md" px="xs">
          <Text size="xs" c="dimmed">
            Provider: {selectedProviderId ?
              providers?.find(p => p.id === selectedProviderId)?.name || 'Unknown' :
              'Default'}
            {selectedModel && ` (${selectedModel})`}
          </Text>
          <Text size="xs" c="dimmed">•</Text>
          <Text size="xs" c="dimmed">
            Strategy: {ENHANCEMENT_STRATEGIES.find(s => s.value === selectedStrategy)?.label || 'None'}
          </Text>
          <Text size="xs" c="dimmed">•</Text>
          <Text size="xs" c="dimmed">
            Collection: {collectionName}
          </Text>
        </Group>
      </Stack>
    </Paper>

    {/* Settings Modal */}
    <Modal
      opened={settingsModalOpen}
      onClose={() => setSettingsModalOpen(false)}
      title={
        <Group gap="xs">
          <IconSettings size={20} />
          <Text fw={600}>Conversation Settings</Text>
        </Group>
      }
      size="lg"
    >
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          Configure LLM provider, query enhancement strategy, and vector database collection for this conversation.
        </Text>

        <Divider label="LLM Provider" labelPosition="left" />

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

        {selectedProviderId && providers && (
          <Select
            label="Model"
            placeholder="Select a model (optional)"
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
            clearable
            description="Leave empty to use provider's default model"
          />
        )}

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
            }
          }}
        />

        {enableReranking && (
          <>
            <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light" size="sm">
              <Text size="sm">
                <strong>No Reranker:</strong> Uses LLM judging (slower)
                <br />
                <strong>Dedicated Reranker:</strong> Uses Cohere/Voyage AI (faster, more accurate)
              </Text>
            </Alert>

            <Grid gutter="md">
              <Grid.Col span={6}>
                <Select
                  label="Reranker Provider (Optional)"
                  placeholder="Select a reranker"
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
                  disabled={providersLoading}
                  description="Leave empty to use LLM"
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
                  description="Choose the model"
                />
              </Grid.Col>
            </Grid>
          </>
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


