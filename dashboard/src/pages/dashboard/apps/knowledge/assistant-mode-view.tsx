/**
 * Assistant Mode View
 * 
 * Deep Agent conversation interface with WebSocket streaming.
 * Shows real-time todos, files, and tool calls.
 */

import { useResetConversationMessages } from '@/api/resources/conversations';
import { FilesGrid, TodoList, ToolCallsList } from '@/components/deep-agent';
import { DeepAgentPipelineModal } from '@/components/deep-agent-pipeline-modal';
import { EnhancedCodeBlock } from '@/components/enhanced-code-block';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import type { FileContent, TodoItem, ToolCall } from '@/types/deep-agent';
import { detectTextDirection } from '@/utilities/text-direction';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Divider,
  Group,
  Paper,
  ScrollArea,
  Stack,
  Tabs,
  Text,
  Textarea,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheckbox,
  IconChevronLeft,
  IconChevronRight,
  IconEdit,
  IconFileText,
  IconPlayerStop,
  IconRefresh,
  IconRobot,
  IconSend,
  IconTool,
  IconUser,
} from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';

interface AssistantModeViewProps {
  sessionId: string;
  sessionName: string;
}

export function AssistantModeView({
  sessionId,
  sessionName,
}: AssistantModeViewProps) {
  const navigate = useNavigate();
  const resetMessagesMutation = useResetConversationMessages();

  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [files, setFiles] = useState<Record<string, FileContent>>({});
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentChunk, setCurrentChunk] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [modalOpened, setModalOpened] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionRetries, setConnectionRetries] = useState(0);
  const [agentId, setAgentId] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const accumulatedResponseRef = useRef<string>('');

  // Markdown components for proper rendering with smaller font
  const markdownComponents = useMemo(() => ({
    code({ inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const code = String(children).replace(/\n$/, '');
      return <EnhancedCodeBlock code={code} language={match ? match[1] : undefined} inline={inline} />;
    },
    h1: ({ children }: any) => (
      <Text size="16px" fw={700} mt="md" mb="xs" c="gray.9" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h2: ({ children }: any) => (
      <Text size="15px" fw={600} mt="md" mb="xs" c="gray.9" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h3: ({ children }: any) => (
      <Text size="14px" fw={600} mt="sm" mb="xs" c="gray.8" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h4: ({ children }: any) => (
      <Text size="13px" fw={600} mt="sm" mb="xs" c="gray.8" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    ul: ({ children }: any) => (
      <ul style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '24px', fontSize: '13px' }}>
        {children}
      </ul>
    ),
    ol: ({ children }: any) => (
      <ol style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '24px', fontSize: '13px' }}>
        {children}
      </ol>
    ),
    li: ({ children }: any) => (
      <li style={{ marginTop: '4px', marginBottom: '4px', lineHeight: '1.6' }}>
        {children}
      </li>
    ),
    p: ({ children }: any) => (
      <Text component="div" style={{ marginTop: '8px', marginBottom: '8px', lineHeight: '1.6', fontSize: '13px', direction: 'inherit', textAlign: 'inherit' }}>
        {children}
      </Text>
    ),
    strong: ({ children }: any) => (
      <Text component="strong" fw={600} c="gray.9">
        {children}
      </Text>
    ),
    em: ({ children }: any) => (
      <Text component="em" fs="italic" c="gray.8">
        {children}
      </Text>
    ),
    a: ({ href, children }: any) => (
      <Text
        component="a"
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        c="blue.6"
        style={{
          textDecoration: 'underline',
          fontSize: '13px'
        }}
      >
        {children}
      </Text>
    ),
    blockquote: ({ children }: any) => (
      <Box
        style={{
          borderLeft: '4px solid var(--mantine-color-indigo-5)',
          paddingLeft: '16px',
          paddingTop: '8px',
          paddingBottom: '8px',
          marginTop: '12px',
          marginBottom: '12px',
          backgroundColor: 'var(--mantine-color-indigo-0)',
          borderRadius: '0 4px 4px 0',
          fontSize: '13px'
        }}
      >
        <Text c="gray.8" fs="italic">
          {children}
        </Text>
      </Box>
    ),
    hr: () => (
      <Box
        style={{
          height: '1px',
          backgroundColor: 'var(--mantine-color-gray-3)',
          margin: '16px 0',
          border: 'none',
        }}
      />
    ),
    table: ({ children }: any) => (
      <Box style={{ overflowX: 'auto', marginTop: '16px', marginBottom: '16px', direction: 'inherit' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '12px',
            border: '1px solid var(--mantine-color-gray-3)',
            direction: 'inherit',
          }}
        >
          {children}
        </table>
      </Box>
    ),
    thead: ({ children }: any) => (
      <thead style={{ backgroundColor: 'var(--mantine-color-gray-1)' }}>
        {children}
      </thead>
    ),
    tbody: ({ children }: any) => (
      <tbody>
        {children}
      </tbody>
    ),
    tr: ({ children }: any) => (
      <tr style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
        {children}
      </tr>
    ),
    th: ({ children }: any) => (
      <th
        style={{
          padding: '10px 12px',
          textAlign: 'inherit',
          fontWeight: 600,
          color: 'var(--mantine-color-gray-9)',
          borderRight: '1px solid var(--mantine-color-gray-3)',
        }}
      >
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td
        style={{
          padding: '10px 12px',
          borderRight: '1px solid var(--mantine-color-gray-3)',
          color: 'var(--mantine-color-gray-8)',
          textAlign: 'inherit',
        }}
      >
        {children}
      </td>
    ),
  }), []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentChunk]);

  // Load existing messages on mount
  useEffect(() => {
    const loadExistingMessages = async () => {
      try {
        const token = localStorage.getItem('jwt_token');
        if (!token) return;

        const response = await fetch(
          apiUtils.buildApiUrl(`/conversations/${sessionId}?expand=messages,agent&t=${Date.now()}`),
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
            },
          }
        );

        if (response.ok) {
          const data = await response.json();

          // Capture agent ID for navigation
          if (data.agent?.id) {
            setAgentId(data.agent.id);
          } else if (data.session?.agent_id) {
            setAgentId(data.session.agent_id);
          }

          if (data.messages && data.messages.length > 0) {
            // Convert timestamps to Date objects
            const messagesWithDates = data.messages.map((msg: any) => ({
              ...msg,
              timestamp: typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp
            }));
            setMessages(messagesWithDates);
            console.log(`✅ Loaded ${messagesWithDates.length} existing messages`);
          }
        }
      } catch (err) {
        console.error('Failed to load existing messages:', err);
      }
    };

    loadExistingMessages();
  }, [sessionId]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // WebSocket message handler
  const handleWebSocketMessage = (data: any) => {
    try {
      switch (data.type) {
        case 'start':
          setIsLoading(true);
          setCurrentChunk('');
          accumulatedResponseRef.current = '';
          setModalOpened(true);
          // Reset progress state
          setTodos([]);
          setFiles({});
          setToolCalls([]);
          break;

        case 'chunk':
          accumulatedResponseRef.current += data.data.content;
          setCurrentChunk((prev) => prev + data.data.content);
          break;

        case 'todos':
          setTodos(data.data);
          break;

        case 'files':
          console.log('📁 [FILES RECEIVED]', data.data);
          console.log('📁 [FILE COUNT]', Object.keys(data.data || {}).length);
          const entries = Object.entries(data.data || {});
          console.log('📁 [FILES OBJECT ENTRIES]', entries);
          if (entries.length > 0) {
            console.log('📁 [SAMPLE FILE PATH]', entries[0][0]);
            console.log('📁 [SAMPLE FILE CONTENT TYPE]', typeof entries[0][1]);
            console.log('📁 [SAMPLE FILE CONTENT]', entries[0][1]);
          }
          setFiles(data.data);

          // Show notification when files are created
          const fileCount = Object.keys(data.data || {}).length;
          if (fileCount > 0) {
            console.log(`✅ ${fileCount} file(s) created by agent - Check the Files tab!`);
          }
          break;

        case 'tool_call':
          if (data.data.status === 'started') {
            setToolCalls((prev) => [
              ...prev,
              {
                id: String(Date.now()),
                name: data.data.name,
                args: data.data.inputs || {},
                status: 'pending',
              },
            ]);
          } else if (data.data.status === 'completed') {
            setToolCalls((prev) =>
              prev.map((tc) =>
                tc.name === data.data.name
                  ? { ...tc, result: JSON.stringify(data.data.output), status: 'completed' }
                  : tc
              )
            );
          }
          break;

        case 'done':
          if (accumulatedResponseRef.current) {
            setMessages((prev) => [
              ...prev,
              { role: 'assistant', content: accumulatedResponseRef.current },
            ]);
            setCurrentChunk('');
            accumulatedResponseRef.current = '';
          }
          setIsLoading(false);
          setModalOpened(false); // Close modal when response is complete
          break;

        case 'error':
          setError(data.data.message);
          setIsLoading(false);
          setModalOpened(false); // Close modal on error
          break;
      }
    } catch (err) {
      console.error('Failed to handle WebSocket message:', err);
    }
  };

  // Connect to WebSocket
  const connectWebSocket = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token available');
      }

      if (!sessionId) {
        throw new Error('Session ID is required for WebSocket connection');
      }

      const wsUrl = apiUtils.buildWebSocketUrl('/ws/agent/query/assistant', token);
      console.log('🔌 [WS CONNECTING] Mode: ASSISTANT AGENT | Endpoint: /ws/agent/query/assistant');

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
        console.log('✅ Assistant Agent WebSocket connected');
        setIsConnected(true);
        setConnectionRetries(0);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`📥 [WS MESSAGE RECEIVED] type=${data.type}`);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('❌ [WS MESSAGE ERROR] Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        clearTimeout(connectionTimeout);
        setIsConnected(false);
        console.log(`🔌 WebSocket closed: code=${event.code}, reason=${event.reason || 'No reason provided'}`);
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
        setIsLoading(false);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);

      // Retry connection if under max retries
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

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // Add user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: inputMessage }]);
    const queryToSend = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      // Connect to WebSocket if not already connected
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setIsConnected(false); // Show connecting state
        await connectWebSocket();

        // Wait for the connection to be fully established
        let waitCount = 0;
        while (wsRef.current?.readyState !== WebSocket.OPEN && waitCount < 50) {
          await new Promise(resolve => setTimeout(resolve, 100));
          waitCount++;
        }

        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          console.error('❌ WebSocket did not reach OPEN state after 5 seconds');
          throw new Error('WebSocket connection timeout');
        }
      }

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // Send query to WebSocket
        const message = {
          query: queryToSend,
          conversation_id: sessionId,
        };

        console.log(`📤 [QUERY SENT] Mode: ASSISTANT AGENT | Query: ${queryToSend.substring(0, 100)}${queryToSend.length > 100 ? '...' : ''}`);
        wsRef.current.send(JSON.stringify(message));
      } else {
        throw new Error('WebSocket is not connected');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I cannot connect to the chat service. Please check your connection and try again.',
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleResetMessages = async () => {
    if (!sessionId) return;

    try {
      await resetMessagesMutation.mutateAsync({
        model: {},
        route: { conversationId: sessionId },
      });

      // Clear local state
      setMessages([]);
      setTodos([]);
      setFiles({});
      setToolCalls([]);
      setCurrentChunk('');
      accumulatedResponseRef.current = '';
      setModalOpened(false); // Close modal when resetting

      // Show success notification
      notifications.show({
        title: 'Success',
        message: 'Conversation reset successfully. Starting fresh!',
        color: 'green',
      });
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to reset conversation',
        color: 'red',
      });
    }
  };

  return (
    <Box style={{ display: 'flex', flexDirection: 'column', height: 'calc(98vh - 80px)' }}>
      {/* Header */}
      <Paper p="md" withBorder style={{ borderBottom: '1px solid var(--mantine-color-gray-3)', flexShrink: 0 }}>
        <Group justify="space-between">
          <Group>
            <ActionIcon variant="subtle" onClick={() => navigate(paths.dashboard.apps.agents)}>
              <IconArrowLeft size={20} />
            </ActionIcon>
            <div>
              <Text size="lg" fw={600}>
                {sessionName}
              </Text>
              <Text size="xs" c="dimmed">
                Assistant Agent • Real-time thought process tracking
              </Text>
            </div>
          </Group>

          <Group gap="xs">
            <Button
              size="xs"
              variant="light"
              color="grape"
              leftSection={<IconTool size={16} />}
              onClick={() => setModalOpened(true)}
            >
              View Thought Process
            </Button>
            <Button
              size="xs"
              variant="subtle"
              color="gray"
              leftSection={sidebarVisible ? <IconChevronRight size={16} /> : <IconChevronLeft size={16} />}
              onClick={() => setSidebarVisible(!sidebarVisible)}
            >
              {sidebarVisible ? 'Hide Panel' : 'Show Panel'}
            </Button>

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

            <Tooltip label="Edit Agent">
              <ActionIcon
                variant="subtle"
                color="blue"
                onClick={() => {
                  if (agentId) {
                    navigate(paths.dashboard.apps.agentEdit(agentId));
                  }
                }}
                disabled={!agentId}
              >
                <IconEdit size={16} />
              </ActionIcon>
            </Tooltip>

            {isLoading && (
              <Button
                size="xs"
                color="red"
                leftSection={<IconPlayerStop size={16} />}
                onClick={() => wsRef.current?.close()}
              >
                Stop
              </Button>
            )}
          </Group>
        </Group>
      </Paper>

      {error && (
        <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red" m="md">
          {error}
        </Alert>
      )}

      {/* Main Content */}
      <Box style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>
        {/* Left: Chat */}
        <Box style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--mantine-color-gray-3)' }}>
          <ScrollArea style={{ flex: 1 }} p="md">
            <Stack gap="md">
              {messages.length === 0 && !currentChunk && (
                <Box ta="center" py="xl">
                  <Text size="lg" c="dimmed">
                    Start a conversation with your deep agent
                  </Text>
                  <Text size="sm" c="dimmed" mt="xs">
                    The agent will plan, use tools, and maintain files automatically
                  </Text>
                </Box>
              )}

              {messages.map((message, index) => {
                const textDirection = detectTextDirection(message.content);
                const isUser = message.role === 'user';
                return (
                  <Box
                    key={index}
                    style={{
                      display: 'flex',
                      justifyContent: isUser ? 'flex-end' : 'flex-start',
                      gap: '12px',
                      alignItems: 'flex-start',
                    }}
                  >
                    {/* Assistant Avatar */}
                    {!isUser && (
                      <Box
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
                        }}
                      >
                        <IconRobot size={20} color="white" />
                      </Box>
                    )}

                    <Paper
                      p="md"
                      radius="lg"
                      shadow="sm"
                      style={{
                        maxWidth: '75%',
                        background: isUser
                          ? 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)'
                          : 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                        border: isUser ? 'none' : '1px solid #e2e8f0',
                        borderTopRightRadius: isUser ? 4 : 16,
                        borderTopLeftRadius: isUser ? 16 : 4,
                      }}
                    >
                      <Box
                        style={{
                          fontSize: '14px',
                          lineHeight: 1.6,
                          direction: textDirection,
                          textAlign: textDirection === 'rtl' ? 'right' : 'left',
                          color: isUser ? '#ffffff' : '#1e293b',
                        }}
                      >
                        {isUser ? (
                          <Text style={{ whiteSpace: 'pre-wrap' }} c="white">
                            {message.content}
                          </Text>
                        ) : (
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                            components={markdownComponents}
                          >
                            {message.content}
                          </ReactMarkdown>
                        )}
                      </Box>
                    </Paper>

                    {/* User Avatar */}
                    {isUser && (
                      <Box
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          boxShadow: '0 2px 8px rgba(14, 165, 233, 0.3)',
                        }}
                      >
                        <IconUser size={20} color="white" />
                      </Box>
                    )}
                  </Box>
                );
              })}

              {currentChunk && (() => {
                const textDirection = detectTextDirection(currentChunk);
                return (
                  <Box
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-start',
                      gap: '12px',
                      alignItems: 'flex-start',
                    }}
                  >
                    {/* Assistant Avatar */}
                    <Box
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
                        animation: 'pulse 2s infinite',
                      }}
                    >
                      <IconRobot size={20} color="white" />
                    </Box>

                    <Paper
                      p="md"
                      radius="lg"
                      shadow="sm"
                      style={{
                        maxWidth: '75%',
                        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                        border: '1px solid #e2e8f0',
                        borderTopLeftRadius: 4,
                        position: 'relative',
                      }}
                    >
                      <Badge
                        size="xs"
                        variant="light"
                        color="grape"
                        mb="xs"
                        leftSection={
                          <Box component="span" style={{ animation: 'pulse 1.5s infinite' }}>●</Box>
                        }
                      >
                        Typing...
                      </Badge>
                      <Text
                        style={{
                          whiteSpace: 'pre-wrap',
                          lineHeight: 1.6,
                          fontSize: '14px',
                          direction: textDirection,
                          textAlign: textDirection === 'rtl' ? 'right' : 'left',
                          color: '#1e293b',
                        }}
                      >
                        {currentChunk}
                      </Text>
                    </Paper>
                  </Box>
                );
              })()}

              <div ref={messagesEndRef} />
            </Stack>
          </ScrollArea>

          {/* Input Area - Enhanced */}
          <Paper
            p="md"
            withBorder
            shadow="sm"
            style={{
              borderTop: '2px solid #e5e7eb',
              background: 'linear-gradient(to top, #ffffff, #f9fafb)',
            }}
          >
            <Group gap="sm" align="flex-end">
              <Textarea
                style={{ flex: 1 }}
                placeholder="Ask the deep agent for help..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                size="md"
                radius="md"
                minRows={1}
                maxRows={8}
                autosize
                styles={{
                  input: {
                    borderWidth: '2px',
                    '&:focus': {
                      borderColor: '#a855f7',
                    },
                  },
                }}
              />
              <ActionIcon
                size={42}
                variant="gradient"
                gradient={{ from: 'grape', to: 'violet', deg: 45 }}
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                radius="md"
              >
                <IconSend size={20} />
              </ActionIcon>
            </Group>
          </Paper>
        </Box>

        {/* Right: Agent State - Enhanced UI */}
        {sidebarVisible && (
          <Paper
            withBorder
            radius="md"
            style={{
              width: '420px',
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
              borderLeft: '3px solid #4c6ef5',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
            }}
          >
            <Tabs
              defaultValue="tasks"
              variant="pills"
              style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
            >
              <Box p="md" pb="sm" style={{ borderBottom: '1px solid #e9ecef' }}>
                <Group justify="space-between" mb="md">
                  <Group gap="xs">
                    <IconRobot size={18} color="#4c6ef5" />
                    <Text size="sm" fw={700} c="gray.9">
                      Workflow State
                    </Text>
                  </Group>
                  <ActionIcon
                    size="sm"
                    variant="subtle"
                    color="gray"
                    onClick={() => setSidebarVisible(false)}
                    title="Hide sidebar"
                  >
                    <IconChevronRight size={16} />
                  </ActionIcon>
                </Group>
                <Tabs.List grow>
                  <Tabs.Tab
                    value="tasks"
                    leftSection={<IconCheckbox size={16} />}
                    style={{
                      fontWeight: 600,
                      fontSize: '0.875rem',
                    }}
                  >
                    Tasks
                    {todos.length > 0 && (
                      <Badge size="xs" ml="xs" variant="gradient" gradient={{ from: 'violet', to: 'grape' }}>
                        {todos.length}
                      </Badge>
                    )}
                  </Tabs.Tab>
                  <Tabs.Tab
                    value="files"
                    leftSection={<IconFileText size={16} />}
                    style={{
                      fontWeight: 600,
                      fontSize: '0.875rem',
                    }}
                  >
                    Files
                    {Object.keys(files).length > 0 && (
                      <Badge size="xs" ml="xs" variant="gradient" gradient={{ from: 'teal', to: 'green' }}>
                        {Object.keys(files).length}
                      </Badge>
                    )}
                  </Tabs.Tab>
                  <Tabs.Tab
                    value="tools"
                    leftSection={<IconTool size={16} />}
                    style={{
                      fontWeight: 600,
                      fontSize: '0.875rem',
                    }}
                  >
                    Tools
                    {toolCalls.length > 0 && (
                      <Badge size="xs" ml="xs" variant="gradient" gradient={{ from: 'cyan', to: 'blue' }}>
                        {toolCalls.length}
                      </Badge>
                    )}
                  </Tabs.Tab>
                </Tabs.List>
              </Box>

              <Box style={{ flex: 1, overflow: 'hidden' }} px="md" pb="md">
                <Tabs.Panel value="tasks" style={{ height: '100%' }}>
                  <ScrollArea h="100%">
                    {todos.length > 0 ? (
                      <TodoList todos={todos} />
                    ) : (
                      <Box ta="center" py="xl">
                        <IconCheckbox size={32} color="gray" style={{ opacity: 0.3 }} />
                        <Text size="sm" c="dimmed" mt="sm">
                          No tasks yet
                        </Text>
                      </Box>
                    )}
                  </ScrollArea>
                </Tabs.Panel>

                <Tabs.Panel value="files" style={{ height: '100%' }}>
                  <ScrollArea h="100%">
                    {Object.keys(files).length > 0 ? (
                      <FilesGrid files={files} editDisabled />
                    ) : (
                      <Box ta="center" py="xl">
                        <IconFileText size={32} color="gray" style={{ opacity: 0.3 }} />
                        <Text size="sm" c="dimmed" mt="sm">
                          No files generated yet
                        </Text>
                      </Box>
                    )}
                  </ScrollArea>
                </Tabs.Panel>

                <Tabs.Panel value="tools" style={{ height: '100%' }}>
                  <ScrollArea h="100%">
                    {toolCalls.length > 0 ? (
                      <ToolCallsList toolCalls={toolCalls} />
                    ) : (
                      <Box ta="center" py="xl">
                        <IconTool size={32} color="gray" style={{ opacity: 0.3 }} />
                        <Text size="sm" c="dimmed" mt="sm">
                          No tool calls yet
                        </Text>
                      </Box>
                    )}
                  </ScrollArea>
                </Tabs.Panel>
              </Box>
            </Tabs>
          </Paper>
        )}
      </Box>

      {/* Deep Agent Pipeline Modal */}
      <DeepAgentPipelineModal
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
        toolCalls={toolCalls}
        todos={todos}
        files={files}
        isActive={isLoading}
      />
    </Box>
  );
}
