/**
 * TodoList Component for Deep Agent
 *
 * Displays agent's planning tasks with status indicators.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import { CheckCircle, Circle, Clock, ListTodo, ChevronDown, ChevronRight } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { TodoItem } from '@/types/deep-agent';
import { Box, Card, Group, Stack, Text, Badge, Container, Center, ScrollArea, Divider, ActionIcon } from '@mantine/core';

interface TodoListProps {
  todos: TodoItem[];
}

const getStatusIcon = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle size={16} color="#16a34a" />;
    case 'in_progress':
      return <Clock size={16} color="#ca8a04" style={{ animation: 'spin 1s linear infinite' }} />;
    default:
      return <Circle size={16} color="#d1d5db" />;
  }
};

const getStatusColor = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return 'green';
    case 'in_progress':
      return 'yellow';
    default:
      return 'gray';
  }
};

const getBgColor = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return '#f0fdf4';
    case 'in_progress':
      return '#fefce8';
    default:
      return '#f9fafb';
  }
};

export function TodoList({ todos }: TodoListProps) {
  const [expandedSections, setExpandedSections] = useState({
    in_progress: true,
    pending: true,
    completed: false,
  });

  const groupedTodos = useMemo(() => {
    return {
      in_progress: todos.filter((t) => t.status === 'in_progress'),
      pending: todos.filter((t) => t.status === 'pending'),
      completed: todos.filter((t) => t.status === 'completed'),
    };
  }, [todos]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  if (todos.length === 0) {
    return (
      <Center style={{ height: '100%' }}>
        <Stack align="center" gap="md">
          <ListTodo size={48} color="#d1d5db" />
          <Text size="lg" fw={500} c="dimmed">
            No tasks yet. The agent will create a plan when needed.
          </Text>
        </Stack>
      </Center>
    );
  }

  return (
    <ScrollArea style={{ height: '100%' }} type="auto">
      <Container size="lg" py="xl">
        <Card shadow="sm" p="md" radius="md" withBorder mb="lg">
          <Group gap="md">
            <Box style={{ backgroundColor: '#fef3c7', padding: 8, borderRadius: 8 }}>
              <ListTodo size={22} color="#d97706" />
            </Box>
            <Stack gap={0}>
              <Text fw={700} size="lg">
                Tasks
              </Text>
              <Text size="sm" c="dimmed">
                {todos.length} {todos.length === 1 ? 'task' : 'tasks'}
              </Text>
            </Stack>
          </Group>
        </Card>

        <Stack gap="lg">
          {/* In Progress */}
          {groupedTodos.in_progress.length > 0 && (
            <div>
              <Group
                gap="sm"
                mb="md"
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('in_progress')}
              >
                <Box style={{ display: 'flex', alignItems: 'center' }}>
                  {expandedSections.in_progress ? (
                    <ChevronDown size={18} color="#ca8a04" />
                  ) : (
                    <ChevronRight size={18} color="#ca8a04" />
                  )}
                </Box>
                <Clock size={18} color="#ca8a04" />
                <Text fw={700} size="md" c="var(--mantine-color-dark-9)">
                  IN PROGRESS ({groupedTodos.in_progress.length})
                </Text>
              </Group>
              {expandedSections.in_progress && (
                <Stack gap="md">
                  {groupedTodos.in_progress.map((todo) => (
                    <Card key={todo.id} padding="md" radius="md" withBorder style={{ backgroundColor: getBgColor(todo.status) }}>
                      <Group gap="md" align="flex-start">
                        <Box style={{ paddingTop: 4 }}>
                          {getStatusIcon(todo.status)}
                        </Box>
                        <Stack gap={0} style={{ flex: 1 }}>
                          <Text size="sm" fw={600} c="var(--mantine-color-dark-9)">
                            {todo.content}
                          </Text>
                          <Badge size="sm" color={getStatusColor(todo.status)} variant="light">
                            {todo.status.toUpperCase().replace(/_/g, ' ')}
                          </Badge>
                        </Stack>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              )}
            </div>
          )}

          {/* Pending */}
          {groupedTodos.pending.length > 0 && (
            <div>
              <Group
                gap="sm"
                mb="md"
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('pending')}
              >
                <Box style={{ display: 'flex', alignItems: 'center' }}>
                  {expandedSections.pending ? (
                    <ChevronDown size={18} color="#6b7280" />
                  ) : (
                    <ChevronRight size={18} color="#6b7280" />
                  )}
                </Box>
                <Circle size={18} color="#d1d5db" />
                <Text fw={700} size="md" c="var(--mantine-color-dark-9)">
                  PENDING ({groupedTodos.pending.length})
                </Text>
              </Group>
              {expandedSections.pending && (
                <Stack gap="md">
                  {groupedTodos.pending.map((todo) => (
                    <Card key={todo.id} padding="md" radius="md" withBorder style={{ backgroundColor: getBgColor(todo.status) }}>
                      <Group gap="md" align="flex-start">
                        <Box style={{ paddingTop: 4 }}>
                          {getStatusIcon(todo.status)}
                        </Box>
                        <Stack gap={0} style={{ flex: 1 }}>
                          <Text size="sm" fw={600} c="var(--mantine-color-dark-9)">
                            {todo.content}
                          </Text>
                          <Badge size="sm" color={getStatusColor(todo.status)} variant="light">
                            {todo.status.toUpperCase().replace(/_/g, ' ')}
                          </Badge>
                        </Stack>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              )}
            </div>
          )}

          {/* Completed */}
          {groupedTodos.completed.length > 0 && (
            <div>
              <Group
                gap="sm"
                mb="md"
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('completed')}
              >
                <Box style={{ display: 'flex', alignItems: 'center' }}>
                  {expandedSections.completed ? (
                    <ChevronDown size={18} color="#16a34a" />
                  ) : (
                    <ChevronRight size={18} color="#16a34a" />
                  )}
                </Box>
                <CheckCircle size={18} color="#16a34a" />
                <Text fw={700} size="md" c="var(--mantine-color-dark-9)">
                  COMPLETED ({groupedTodos.completed.length})
                </Text>
              </Group>
              {expandedSections.completed && (
                <Stack gap="md">
                  {groupedTodos.completed.map((todo) => (
                    <Card key={todo.id} padding="md" radius="md" withBorder style={{ backgroundColor: getBgColor(todo.status) }}>
                      <Group gap="md" align="flex-start">
                        <Box style={{ paddingTop: 4 }}>
                          {getStatusIcon(todo.status)}
                        </Box>
                        <Stack gap={0} style={{ flex: 1 }}>
                          <Text size="sm" fw={600} c="var(--mantine-color-dark-9)" style={{ textDecoration: 'line-through' }}>
                            {todo.content}
                          </Text>
                          <Badge size="sm" color={getStatusColor(todo.status)} variant="light">
                            {todo.status.toUpperCase().replace(/_/g, ' ')}
                          </Badge>
                        </Stack>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              )}
            </div>
          )}
        </Stack>
      </Container>
    </ScrollArea>
  );
}

