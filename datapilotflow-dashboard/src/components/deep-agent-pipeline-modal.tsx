/**
 * Deep Agent Pipeline Modal
 * 
 * Rich UI modal that displays Deep Agent execution progress including:
 * - Tool calls (with inputs/outputs)
 * - Tasks (todos)
 * - Files generated
 */

import {
  Badge,
  Box,
  Card,
  Collapse,
  Group,
  Modal,
  Paper,
  Progress,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  useMantineTheme
} from '@mantine/core';
import {
  IconCheck,
  IconCheckbox,
  IconChevronDown,
  IconChevronRight,
  IconClock,
  IconFile,
  IconFileText,
  IconLoader,
  IconTool,
} from '@tabler/icons-react';
import { useState } from 'react';

import type { TodoItem, ToolCall, FileContent } from '@/types/deep-agent';

/**
 * Pretty format JSON or string data with syntax highlighting
 */
function PrettyData({ data, title }: { data: any; title: string }) {
  const isString = typeof data === 'string';
  const isObject = typeof data === 'object' && data !== null;

  // Try to parse string as JSON
  let displayData = data;
  let isJSON = false;

  if (isString) {
    try {
      displayData = JSON.parse(data);
      isJSON = true;
    } catch {
      // Not JSON, display as string
      displayData = data;
    }
  }

  // Format for display
  const formattedData = isObject || isJSON
    ? JSON.stringify(displayData, null, 2)
    : String(displayData);

  // Truncate if too long
  const shouldTruncate = formattedData.length > 1000;
  const displayText = shouldTruncate
    ? formattedData.substring(0, 1000) + '\n...(truncated)'
    : formattedData;

  return (
    <Box>
      <Text size="xs" fw={500} c="dimmed" mb={4}>
        {title}
      </Text>
      <Paper
        withBorder
        p="xs"
        radius="md"
        style={{
          backgroundColor: 'var(--mantine-color-gray-0)',
          maxHeight: '200px',
          overflow: 'auto',
          fontFamily: 'monospace',
          fontSize: '11px',
          lineHeight: '1.5',
        }}
      >
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {displayText}
        </pre>
      </Paper>
      {shouldTruncate && (
        <Text size="xs" c="dimmed" mt={4}>
          Full output truncated for readability
        </Text>
      )}
    </Box>
  );
}

interface DeepAgentPipelineModalProps {
  opened: boolean;
  onClose: () => void;
  toolCalls: ToolCall[];
  todos: TodoItem[];
  files: Record<string, FileContent>;
  isActive: boolean;
}

export function DeepAgentPipelineModal({
  opened,
  onClose,
  toolCalls,
  todos,
  files,
  isActive,
}: DeepAgentPipelineModalProps) {
  const theme = useMantineTheme();
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());

  const toggleToolExpanded = (toolId: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  };

  const completedToolsCount = toolCalls.filter((t) => t.status === 'completed').length;
  const completedTodosCount = todos.filter((t) => t.status === 'completed').length;
  const fileCount = Object.keys(files).length;

  const progress = isActive && toolCalls.length > 0
    ? (completedToolsCount / toolCalls.length) * 100
    : 0;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="xl"
      title={
        <Group gap="sm">
          <ThemeIcon size="lg" radius="md" gradient={{ from: 'grape', to: 'violet', deg: 45 }}>
            <IconTool size={20} />
          </ThemeIcon>
          <div>
            <Text fw={600} size="lg">
              Agent Thought Process
            </Text>
            <Text size="xs" c="dimmed">
              Real-time thought process tracking
            </Text>
          </div>
        </Group>
      }
      styles={{
        root: {
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          margin: 0,
        },
        inner: {
          alignItems: 'flex-end',
        },
        content: {
          borderRadius: '16px 16px 0 0',
          maxHeight: '80vh',
        },
      }}
    >
      <Stack gap="md">
        {/* Progress Bar */}
        {isActive && (
          <Box>
            <Group justify="space-between" mb="xs">
              <Text size="sm" fw={500}>
                Overall Progress
              </Text>
              <Text size="sm" c="dimmed">
                {completedToolsCount} / {toolCalls.length} tools completed
              </Text>
            </Group>
            <Progress
              value={progress}
              size="sm"
              radius="xl"
              striped={isActive}
              animated={isActive}
              color="grape"
            />
          </Box>
        )}

        {/* Summary Cards */}
        <Group grow>
          <Card withBorder p="sm" radius="md">
            <Group gap="xs">
              <ThemeIcon size="md" radius="md" color="blue" variant="light">
                <IconTool size={16} />
              </ThemeIcon>
              <div style={{ flex: 1 }}>
                <Text size="xs" c="dimmed">
                  Tool Calls
                </Text>
                <Text size="lg" fw={600}>
                  {toolCalls.length}
                </Text>
              </div>
            </Group>
          </Card>

          <Card withBorder p="sm" radius="md">
            <Group gap="xs">
              <ThemeIcon size="md" radius="md" color="violet" variant="light">
                <IconCheckbox size={16} />
              </ThemeIcon>
              <div style={{ flex: 1 }}>
                <Text size="xs" c="dimmed">
                  Tasks
                </Text>
                <Text size="lg" fw={600}>
                  {todos.length}
                </Text>
              </div>
            </Group>
          </Card>

          <Card withBorder p="sm" radius="md">
            <Group gap="xs">
              <ThemeIcon size="md" radius="md" color="green" variant="light">
                <IconFileText size={16} />
              </ThemeIcon>
              <div style={{ flex: 1 }}>
                <Text size="xs" c="dimmed">
                  Files
                </Text>
                <Text size="lg" fw={600}>
                  {fileCount}
                </Text>
              </div>
            </Group>
          </Card>
        </Group>

        <ScrollArea h={400} offsetScrollbars>
          <Stack gap="lg">
            {/* Tool Calls Section */}
            {toolCalls.length > 0 && (
              <Box>
                <Group gap="xs" mb="sm">
                  <ThemeIcon size="sm" radius="md" color="blue" variant="light">
                    <IconTool size={14} />
                  </ThemeIcon>
                  <Text fw={600} size="sm">
                    Tool Calls ({toolCalls.length})
                  </Text>
                </Group>

                <Stack gap="xs">
                  {toolCalls.map((tool) => {
                    const statusColor =
                      tool.status === 'completed' ? 'green' :
                        tool.status === 'running' ? 'blue' :
                          tool.status === 'error' ? 'red' :
                            'gray';

                    const statusIcon =
                      tool.status === 'completed' ? <IconCheck size={14} /> :
                        tool.status === 'error' ? <Text size="xs" fw={600}>✕</Text> :
                          <IconLoader size={14} className="animate-spin" />;

                    return (
                      <Card
                        key={tool.id}
                        withBorder
                        p="sm"
                        radius="md"
                        style={{
                          borderLeft: `3px solid var(--mantine-color-${statusColor}-6)`,
                          backgroundColor: expandedTools.has(tool.id)
                            ? 'var(--mantine-color-gray-0)'
                            : undefined,
                          transition: 'all 0.2s ease',
                        }}
                      >
                        <Group justify="space-between" wrap="nowrap">
                          <Group gap="xs" style={{ flex: 1, minWidth: 0 }}>
                            <ThemeIcon
                              size="md"
                              radius="xl"
                              color={statusColor}
                              variant="light"
                            >
                              {statusIcon}
                            </ThemeIcon>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <Text fw={500} size="sm" truncate title={tool.name}>
                                {tool.name}
                              </Text>
                              <Group gap={4} mt={2}>
                                <Badge size="xs" color={statusColor} variant="light">
                                  {tool.status}
                                </Badge>
                                {tool.duration && (
                                  <Badge size="xs" color="gray" variant="outline">
                                    {tool.duration}ms
                                  </Badge>
                                )}
                              </Group>
                            </div>
                          </Group>
                          <ThemeIcon
                            size="sm"
                            radius="md"
                            variant="subtle"
                            color="gray"
                            style={{ cursor: 'pointer' }}
                            onClick={() => toggleToolExpanded(tool.id)}
                          >
                            {expandedTools.has(tool.id) ? (
                              <IconChevronDown size={14} />
                            ) : (
                              <IconChevronRight size={14} />
                            )}
                          </ThemeIcon>
                        </Group>

                        <Collapse in={expandedTools.has(tool.id)}>
                          <Stack gap="sm" mt="sm">
                            {/* Tool Arguments */}
                            {tool.args && Object.keys(tool.args).length > 0 ? (
                              <PrettyData data={tool.args} title="📥 Input Arguments" />
                            ) : (
                              <Paper withBorder p="xs" radius="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                                <Text size="xs" c="dimmed" fs="italic">
                                  No arguments provided
                                </Text>
                              </Paper>
                            )}

                            {/* Tool Result */}
                            {tool.result ? (
                              <PrettyData data={tool.result} title="📤 Output Result" />
                            ) : tool.status === 'running' ? (
                              <Paper withBorder p="xs" radius="md" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                                <Group gap="xs">
                                  <IconLoader size={14} className="animate-spin" />
                                  <Text size="xs" c="blue" fs="italic">
                                    Tool execution in progress...
                                  </Text>
                                </Group>
                              </Paper>
                            ) : null}
                          </Stack>
                        </Collapse>
                      </Card>
                    );
                  })}
                </Stack>
              </Box>
            )}

            {/* Tasks Section */}
            {todos.length > 0 && (
              <Box>
                <Group gap="xs" mb="sm">
                  <ThemeIcon size="sm" radius="md" color="violet" variant="light">
                    <IconCheckbox size={14} />
                  </ThemeIcon>
                  <Text fw={600} size="sm">
                    Tasks ({completedTodosCount}/{todos.length})
                  </Text>
                </Group>

                <Stack gap="xs">
                  {todos.map((todo) => (
                    <Card key={todo.id} withBorder p="xs" radius="md">
                      <Group gap="xs" wrap="nowrap">
                        <ThemeIcon
                          size="sm"
                          radius="xl"
                          color={
                            todo.status === 'completed'
                              ? 'green'
                              : todo.status === 'in_progress'
                                ? 'blue'
                                : 'gray'
                          }
                          variant="light"
                        >
                          {todo.status === 'completed' ? (
                            <IconCheck size={14} />
                          ) : todo.status === 'in_progress' ? (
                            <IconClock size={14} />
                          ) : (
                            <IconCheckbox size={14} />
                          )}
                        </ThemeIcon>
                        <Text size="sm" style={{ flex: 1 }}>
                          {todo.content}
                        </Text>
                        <Badge
                          size="xs"
                          color={
                            todo.status === 'completed'
                              ? 'green'
                              : todo.status === 'in_progress'
                                ? 'blue'
                                : 'gray'
                          }
                        >
                          {todo.status}
                        </Badge>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              </Box>
            )}

            {/* Files Section */}
            {fileCount > 0 && (
              <Box>
                <Group gap="xs" mb="sm">
                  <ThemeIcon size="sm" radius="md" color="green" variant="light">
                    <IconFileText size={14} />
                  </ThemeIcon>
                  <Text fw={600} size="sm">
                    Generated Files ({fileCount})
                  </Text>
                </Group>

                <Stack gap="xs">
                  {Object.entries(files).map(([filename, content]) => (
                    <Card key={filename} withBorder p="xs" radius="md">
                      <Group gap="xs" wrap="nowrap">
                        <ThemeIcon size="sm" radius="md" color="green" variant="light">
                          <IconFile size={14} />
                        </ThemeIcon>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <Text size="sm" fw={500} truncate>
                            {filename}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {content.length} characters
                          </Text>
                        </div>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              </Box>
            )}

            {/* Empty State */}
            {toolCalls.length === 0 && todos.length === 0 && fileCount === 0 && (
              <Box ta="center" py="xl">
                <ThemeIcon size="xl" radius="xl" color="gray" variant="light" mx="auto" mb="sm">
                  <IconLoader size={24} className="animate-spin" />
                </ThemeIcon>
                <Text size="sm" c="dimmed">
                  Waiting for agent activity...
                </Text>
              </Box>
            )}
          </Stack>
        </ScrollArea>
      </Stack>
    </Modal>
  );
}

