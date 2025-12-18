/**
 * ToolCallsList Component for Deep Agent
 *
 * Displays agent's tool execution history with expandable details.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { ChevronDown, ChevronUp, Terminal, AlertCircle, Loader2, CheckCircle, Copy } from 'lucide-react';
import { useState, useMemo } from 'react';
import {
  Box,
  Button,
  Card,
  CopyButton,
  Flex,
  Group,
  Stack,
  Text,
  Badge,
  ActionIcon,
  Tooltip,
  Container,
  ScrollArea,
  Center,
  Paper,
} from '@mantine/core';
import type { ToolCall } from '@/types/deep-agent';

interface ToolCallsListProps {
  toolCalls: ToolCall[];
}

interface ToolCallItemProps {
  toolCall: ToolCall;
}

interface CodeBlockProps {
  content: string;
  label: string;
  color: 'blue' | 'green' | 'red';
}

function CodeBlock({ content, label, color }: CodeBlockProps) {
  const colorMap = {
    blue: { bg: '#f0f6ff', text: '#1971c2' },
    green: { bg: '#f0fdf4', text: '#15803d' },
    red: { bg: '#fef2f2', text: '#991b1b' },
  };

  const codeBgMap = {
    blue: '#001f3f',
    green: '#0f1e0a',
    red: '#1e0a0a',
  };

  return (
    <Box style={{ overflow: 'hidden' }}>
      <Group justify="space-between" p="md" style={{ backgroundColor: colorMap[color].bg, borderRadius: '8px 8px 0 0' }}>
        <Flex gap="xs" align="center">
          <Box style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: colorMap[color].text }} />
          <Text fw={700} size="md" style={{ color: colorMap[color].text }}>
            {label}
          </Text>
        </Flex>
        <CopyButton value={content} timeout={2000}>
          {({ copied, copy }) => (
            <Tooltip label={copied ? 'Copied' : 'Copy'} withArrow position="left">
              <ActionIcon color={copied ? 'green' : 'gray'} variant="subtle" onClick={copy}>
                <Copy size={16} />
              </ActionIcon>
            </Tooltip>
          )}
        </CopyButton>
      </Group>
      <ScrollArea style={{ backgroundColor: codeBgMap[color], borderRadius: '0 0 8px 8px', maxHeight: 400, width: '100%' }}>
        <Box
          component="pre"
          style={{
            color: '#e5e7eb',
            fontFamily: 'monospace',
            fontSize: 13,
            lineHeight: 1.7,
            letterSpacing: '0.3px',
            margin: 0,
            padding: '16px',
            whiteSpace: 'pre',
            overflowX: 'auto',
            overflowY: 'auto',
            minWidth: '100%',
          }}
        >
          {content}
        </Box>
      </ScrollArea>
    </Box>
  );
}

function ToolCallItem({ toolCall }: ToolCallItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusIcon = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return <CheckCircle size={20} color="#16a34a" />;
      case 'error':
        return <AlertCircle size={20} color="#dc2626" />;
      case 'pending':
        return <Loader2 size={20} color="#2563eb" style={{ animation: 'spin 1s linear infinite' }} />;
      case 'interrupted':
        return <Terminal size={20} color="#d97706" />;
      default:
        return <Terminal size={20} color="#9ca3af" />;
    }
  }, [toolCall.status]);

  const statusColor = useMemo(() => {
    switch (toolCall.status) {
      case 'completed':
        return 'green';
      case 'error':
        return 'red';
      case 'pending':
        return 'blue';
      default:
        return 'gray';
    }
  }, [toolCall.status]);

  const jsonInputStr = JSON.stringify(toolCall.args, null, 2);
  const jsonOutputStr =
    typeof toolCall.result === 'string'
      ? toolCall.result
      : JSON.stringify(toolCall.result, null, 2);

  return (
    <Card shadow="sm" padding="md" radius="md" withBorder>
      <Card.Section inheritPadding py="md" style={{ backgroundColor: statusColor === 'green' ? '#f0fdf4' : statusColor === 'red' ? '#fef2f2' : statusColor === 'blue' ? '#f0f6ff' : '#f9fafb' }}>
        <Group justify="space-between">
          <Group gap="md">
            {statusIcon}
            <Stack gap={0}>
              <Text fw={700} size="md">
                {toolCall.name}
              </Text>
              <Badge size="sm" color={statusColor} variant="light">
                {toolCall.status.toUpperCase()}
              </Badge>
            </Stack>
          </Group>
          <ActionIcon variant="subtle" onClick={() => setIsExpanded(!isExpanded)}>
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </ActionIcon>
        </Group>
      </Card.Section>

      {isExpanded && (
        <Card.Section inheritPadding py="md">
          <Stack gap="lg">
            {Object.keys(toolCall.args).length > 0 && (
              <CodeBlock content={jsonInputStr} label="Input Parameters" color="blue" />
            )}

            {toolCall.result && (
              <CodeBlock content={jsonOutputStr} label="Output Result" color="green" />
            )}

            {toolCall.status === 'error' && toolCall.errorMessage && (
              <Paper p="md" radius="md" style={{ backgroundColor: '#fef2f2', borderLeft: '4px solid #dc2626' }}>
                <Group gap="sm">
                  <AlertCircle size={18} color="#991b1b" />
                  <Stack gap={0}>
                    <Text fw={700} size="sm" style={{ color: '#7f1d1d' }}>
                      Error Details
                    </Text>
                    <Text size="sm" style={{ color: '#991b1b' }}>
                      {toolCall.errorMessage}
                    </Text>
                  </Stack>
                </Group>
              </Paper>
            )}
          </Stack>
        </Card.Section>
      )}
    </Card>
  );
}

export function ToolCallsList({ toolCalls }: ToolCallsListProps) {
  if (toolCalls.length === 0) {
    return (
      <Center style={{ height: '100%' }}>
        <Stack align="center" gap="md">
          <Terminal size={48} color="#d1d5db" />
          <Text size="lg" fw={500} c="dimmed">
            No tool calls yet. The agent will execute tools as needed.
          </Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Container size="lg" py="xl">
      <Card shadow="sm" p="md" radius="md" withBorder mb="lg">
        <Group gap="md">
          <Box style={{ backgroundColor: '#dbeafe', padding: 8, borderRadius: 8 }}>
            <Terminal size={22} color="#1e40af" />
          </Box>
          <Stack gap={0}>
            <Text fw={700} size="lg">
              Tool Executions
            </Text>
            <Text size="sm" c="dimmed">
              {toolCalls.length} {toolCalls.length === 1 ? 'execution' : 'executions'}
            </Text>
          </Stack>
        </Group>
      </Card>

      <Stack gap="md">
        {toolCalls.map((toolCall) => (
          <ToolCallItem key={toolCall.id} toolCall={toolCall} />
        ))}
      </Stack>
    </Container>
  );
}
