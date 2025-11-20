/**
 * Assistant Instructions & Tools Configuration Step
 *
 * Allows users to define assistant behavior and select tools.
 * This step appears in Assistant mode only.
 */

import { Alert, Badge, Card, Group, Stack, Text, Textarea } from '@mantine/core';
import { UseFormReturnType } from '@mantine/form';
import { IconSparkles } from '@tabler/icons-react';

interface ToolInstructionsStepProps {
  form: UseFormReturnType<any>;
  tools: any[];
  providers?: any[];
}

export function ToolInstructionsStep({ form, tools = [] }: ToolInstructionsStepProps) {
  const selectedToolIds = form.values.selectedTools || [];
  const selectedTools = (tools || [])?.filter((t) => selectedToolIds.includes(t.id)) || [];

  return (
    <Stack gap="lg">
      {/* Header */}
      <div>
        <Text size="lg" fw={600} mb="xs">
          Assistant Instructions
        </Text>
        <Text size="sm" c="dimmed">
          Define how your assistant should behave. These instructions control the overall agent behavior and guide how all tools are used.
        </Text>
      </div>

      {/* Selected Tools Summary (if any) */}
      {selectedTools.length > 0 && (
        <Card withBorder p="md" radius="md" bg="blue.0">
          <Stack gap="xs">
            <Text size="sm" fw={600}>
              Selected Tools ({selectedTools.length})
            </Text>
            <Group gap="xs">
              {selectedTools.map((tool) => (
                <Badge
                  key={tool.id}
                  variant="light"
                  color={tool.tool_type === 'prompt_based' ? 'blue' : 'green'}
                  leftSection={<Text size="xs">{tool.tool_type === 'prompt_based' ? 'LLM' : 'MCP'}</Text>}
                >
                  {tool.display_name || tool.name}
                </Badge>
              ))}
            </Group>
          </Stack>
        </Card>
      )}

      {/* Assistant Instructions */}
      <Card withBorder p="md" radius="md" bg="grape.0">
        <Stack gap="md">
          <div>
            <Text size="sm" fw={600} mb="xs" c="grape">
              Instructions
            </Text>
            <Text size="xs" c="dimmed">
              <strong>Control the overall agent behavior and all tools.</strong> Define personality, response style, approach to tasks, and how to use tools effectively.
            </Text>
          </div>

          <Textarea
            {...form.getInputProps('instructions')}
            placeholder={`Example:
You are a helpful assistant specialized in customer support.
- Always be friendly and professional
- Provide clear, step-by-step solutions
- Ask clarifying questions when needed
- Suggest relevant documentation when appropriate
- Use all available tools effectively to help users
- When multiple tools are available, evaluate which ones are most relevant
- Combine information from multiple tools when necessary`}
            minRows={15}
            styles={{
              input: {
                fontFamily: 'monospace',
                fontSize: '12px',
              },
            }}
          />

          <Alert icon={<IconSparkles size={16} />} color="grape" variant="light">
            <Text size="xs">
              <strong>Note:</strong> These instructions control the overall agent behavior and guide how ALL tools are used. Works even with 0 tools selected.
            </Text>
          </Alert>
        </Stack>
      </Card>
    </Stack>
  );
}
