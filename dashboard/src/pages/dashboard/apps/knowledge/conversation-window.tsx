import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Text,
  Button,
  Group,
  Stack,
  Title,
  Badge,
  TextInput,
  ScrollArea,
  LoadingOverlay,
  Alert,
  ActionIcon,
  Tooltip,
} from '@mantine/core';
import { 
  IconSend, 
  IconArrowLeft,
  IconMessageCircle,
  IconTrash,
  IconEdit,
  IconRefresh,
  IconBrain,
  IconLoader,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { paths } from '@/routes/paths';
import { apiUtils, apiEndpoints } from '@/config';
import { useResetConversationMessages } from '@/api/resources/conversations';
import { MarkdownRenderer } from '@/components/markdown-renderer';
import { TypingIndicator } from '@/components/typing-indicator';
import { StreamingMessage } from '@/components/streaming-message';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date | string;
  isStreaming?: boolean;
}

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
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const resetMessagesMutation = useResetConversationMessages();

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

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        const message = {
          query: inputMessage,
          use_llm: true,
          session_id: sessionId,
          create_new_session: false
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
      const wsEndpoint = apiEndpoints.conversations.websocket.search(sessionId);
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
    const { stage, message, response, error, chunk } = data;
    
    // Debug logging for streaming
    if (stage === 'llm_response_chunk' && chunk) {
      console.log('Received chunk:', chunk);
    }

    switch (stage) {
      case 'starting':
        // Show starting status with enhanced UX
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
      
      case 'searching':
        // Show searching status
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
            return [
              ...prev.slice(0, -1),
              {
                ...lastMessage,
                content: '🔍 Searching knowledge base...'
              }
            ];
          }
          return prev;
        });
        break;
      
      case 'llm_synthesis':
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
      
      case 'llm_response_chunk':
        // Handle streaming response chunks
        if (chunk) {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              // Update existing streaming message with new chunk
              // Ensure proper line break handling during concatenation
              const newContent = lastMessage.content + chunk;
              
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: newContent,
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
      
      case 'llm_response_complete':
        // Finalize the streaming message
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
        break;
      
      case 'completed':
        // Handle completion
        setIsLoading(false);
        finalizeStreamingMessages();
        break;
      
      case 'error':
        // Handle errors
        finalizeStreamingMessages();
        
        const errorMessage: Message = {
          role: 'assistant',
          content: error || 'An error occurred during the conversation.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
        break;
      
      default:
        // Silently handle unknown stages
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

  const handleBack = () => {
    navigate(paths.dashboard.apps.knowledgeSearch);
  };

  return (
    <Box h="100vh" display="flex" style={{ flexDirection: 'column' }}>
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
                <Text size="xs" c="dimmed">Endpoint: {apiEndpoints.conversations.websocket.search(sessionId || '')}</Text>
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
        <Group gap="md">
          <TextInput
            placeholder="Type your message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            style={{ 
              flex: 1,
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
        </Group>
      </Paper>
    </Box>
  );
}


