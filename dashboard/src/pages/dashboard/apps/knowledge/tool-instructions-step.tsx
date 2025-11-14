/**
 * Tool Instructions Configuration Step
 *
 * Allows users to specify how dynamically bound tools should work together.
 * This step appears after tool selection and before review.
 */

import { Card, Stack, Text, Textarea, Button, Badge, Paper, Group, ActionIcon, Loader, Alert } from '@mantine/core';
import { IconDots, IconSparkles, IconAlertCircle, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { UseFormReturnType } from '@mantine/form';
import { useState, useEffect } from 'react';
import { apiUtils } from '@/config';

interface ToolInstructionsStepProps {
  form: UseFormReturnType<any>;
  tools: any[];
  providers?: any[];
}

export function ToolInstructionsStep({ form, tools = [], providers }: ToolInstructionsStepProps) {
  const selectedToolIds = form.values.selectedTools || [];
  const selectedTools = (tools || [])?.filter((t) => selectedToolIds.includes(t.id)) || [];
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  // Auto-expand if there are existing instructions (edit mode)
  const [isExpanded, setIsExpanded] = useState(!!form.values.tool_instructions);

  // Update isExpanded whenever tool_instructions change (e.g., when loading existing conversation)
  useEffect(() => {
    console.log('[DEBUG ToolInstructionsStep] useEffect triggered, tool_instructions:', form.values.tool_instructions);
    if (form.values.tool_instructions) {
      console.log('[DEBUG ToolInstructionsStep] Setting isExpanded to true');
      setIsExpanded(true);
    }
  }, [form.values.tool_instructions]);

  const generateInstructions = async () => {
    setIsGenerating(true);
    setGenerationError(null);

    try {
      // Check if we have selected LLM provider and model
      const selectedProviderId = form.values.selectedProviderId;
      const selectedModel = form.values.selectedModel;

      if (!selectedProviderId || !selectedModel) {
        setGenerationError('Please select an LLM provider and model in the Enhancement Strategy step');
        setIsGenerating(false);
        return;
      }

      const token = localStorage.getItem('jwt_token');
      const response = await fetch(
        apiUtils.buildApiUrl('/tools/instructions/generate'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            tool_ids: selectedToolIds,
            llm_provider_id: selectedProviderId,
            llm_model_name: selectedModel,
            user_context: undefined,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        setGenerationError(error.detail || 'Failed to generate instructions');
        setIsGenerating(false);
        return;
      }

      const data = await response.json();

      // Set the generated instructions
      form.setFieldValue('tool_instructions', data.instructions);

      // Auto-expand to show generated content
      setIsExpanded(true);

      console.log('Generated instructions:', {
        pattern: data.pattern,
        reasoning: data.reasoning,
      });

      // Show success message in console
      console.log('✨ Tool instructions generated successfully!', {
        pattern: data.pattern,
        reasoning: data.reasoning,
      });
    } catch (error) {
      console.error('Error generating instructions:', error);
      setGenerationError(error instanceof Error ? error.message : 'Failed to generate instructions');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Stack gap="lg">
      {/* Header */}
      <div>
        <Text size="lg" fw={600} mb="xs">
          Tool Orchestration Instructions
        </Text>
        <Text size="sm" c="dimmed">
          Configure how your selected tools should work together. The agent will follow these instructions when deciding which tools to call and in what order.
        </Text>
      </div>

      {/* Selected Tools Summary */}
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

      {/* Instructions Input - Expandable */}
      <Card withBorder p={0} style={{ overflow: 'hidden' }}>
        {/* Header - Always visible */}
        <Group
          justify="space-between"
          align="center"
          p="md"
          style={{
            cursor: 'pointer',
            backgroundColor: isExpanded ? 'var(--mantine-color-gray-0)' : 'transparent',
            borderBottom: isExpanded ? '1px solid var(--mantine-color-gray-2)' : 'none',
          }}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div style={{ flex: 1 }}>
            <Group justify="space-between" align="center" mb="xs">
              <Text size="sm" fw={600}>
                Instructions
              </Text>
              {!isExpanded && form.values.tool_instructions && (
                <Text size="xs" c="dimmed">
                  {form.values.tool_instructions.split('\n').length} line{form.values.tool_instructions.split('\n').length !== 1 ? 's' : ''}
                </Text>
              )}
            </Group>
            {!isExpanded && form.values.tool_instructions && (
              <Paper
                p="xs"
                bg="gray.1"
                style={{
                  borderRadius: '4px',
                  border: '1px solid var(--mantine-color-gray-2)',
                  maxHeight: '80px',
                  overflowY: 'auto',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  lineHeight: '1.4',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  color: 'var(--mantine-color-gray-7)',
                }}
              >
                {form.values.tool_instructions}
              </Paper>
            )}
          </div>
          <Group gap="xs">
            <Button
              size="sm"
              variant="gradient"
              gradient={{ from: 'cyan', to: 'blue', deg: 135 }}
              leftSection={isGenerating ? <Loader size={14} /> : <IconSparkles size={14} />}
              onClick={(e) => {
                e.stopPropagation();
                generateInstructions();
              }}
              disabled={isGenerating || selectedToolIds.length === 0}
              loading={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate with AI'}
            </Button>
            <ActionIcon
              variant="subtle"
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
            >
              {isExpanded ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
            </ActionIcon>
          </Group>
        </Group>

        {/* Expanded Content */}
        {isExpanded && (
          <Stack gap="sm" p="md" pt={0}>
            {generationError && (
              <Alert icon={<IconAlertCircle size={16} />} color="red" variant="light">
                <Text size="sm">{generationError}</Text>
              </Alert>
            )}

            <Textarea
              {...form.getInputProps('tool_instructions')}
              placeholder="Describe how these tools should work together. Be specific about execution order and conditions."
              minRows={32}
              autoFocus
              styles={{
                input: {
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  minHeight: '600px',
                },
              }}
            />
            <Text size="xs" c="dimmed">
              Include details about: when to call each tool, which tools work together, how to accumulate knowledge from multiple tools
            </Text>
          </Stack>
        )}
      </Card>


      {/* Guidelines and Example - Side by Side */}
      <Group grow align="flex-start" gap="md">
        {/* Guidelines - Left */}
        <Card withBorder p="md" radius="md" bg="yellow.0">
          <Stack gap="sm">
            <Group gap="xs">
              <IconDots size={18} />
              <Text size="sm" fw={600}>
                Guidelines
              </Text>
            </Group>
            <Stack gap="xs">
              <Text size="sm">
                ✅ <strong>Be specific:</strong> Mention tool names and describe execution order
              </Text>
              <Text size="sm">
                ✅ <strong>Include conditions:</strong> When should tools be called based on user query
              </Text>
              <Text size="sm">
                ✅ <strong>Describe flow:</strong> How knowledge from one tool feeds into another
              </Text>
              <Text size="sm">
                ✅ <strong>Natural language:</strong> Write as if instructing a smart assistant
              </Text>
              <Text size="sm">
                ❌ <strong>Avoid:</strong> Technical implementation details or code
              </Text>
            </Stack>
          </Stack>
        </Card>

        {/* Example - Right */}
        <Card withBorder p="md" radius="md">
          <Stack gap="sm">
            <Text size="sm" fw={600}>
              Example Instructions
            </Text>
            <Paper p="md" bg="gray.0" style={{ borderRadius: '4px' }}>
              <Text size="xs" style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
{`For MuleSoft flow generation:

1. Error Handling First:
   - If user mentions "error handling", "errors", or "exceptions"
   - Call error_handler_tool to get error patterns

2. Configuration Next:
   - If user mentions "production", "configuration", or "setup"
   - Call configuration_tool to get setup patterns

3. Main Generation:
   - Call flow_generator with accumulated context from helper tools
   - Generator uses both error patterns and configuration guidance

4. Simple Queries:
   - For "Create simple flow" or one-off requests
   - Skip helpers, go directly to flow_generator

This ensures generated flows have proper error handling and production readiness.`}
              </Text>
            </Paper>
          </Stack>
        </Card>
      </Group>
    </Stack>
  );
}
