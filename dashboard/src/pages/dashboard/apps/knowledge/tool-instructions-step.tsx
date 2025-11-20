/**
 * Assistant Instructions & Tools Configuration Step
 *
 * Allows users to define assistant behavior and select tools.
 * This step appears in Assistant mode only.
 */

import { apiUtils } from '@/config';
import { Alert, Badge, Button, Card, Group, Loader, Modal, Select, Stack, Text, Textarea } from '@mantine/core';
import { useForm, UseFormReturnType } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconSparkles, IconWand } from '@tabler/icons-react';
import { useState } from 'react';

interface ToolInstructionsStepProps {
  form: UseFormReturnType<any>;
  tools: any[];
  providers?: any[];
}

export function ToolInstructionsStep({ form, tools = [], providers = [] }: ToolInstructionsStepProps) {
  const selectedToolIds = form.values.selectedTools || [];
  const selectedTools = (tools || [])?.filter((t) => selectedToolIds.includes(t.id)) || [];

  const [generatorModalOpen, setGeneratorModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const generatorForm = useForm({
    initialValues: {
      persona: '',
      personality: '',
      agentType: '',
      providerId: '',
      modelName: '',
    },
    validate: {
      persona: (value) => (!value?.trim() ? 'Persona is required' : null),
      personality: (value) => (!value?.trim() ? 'Personality is required' : null),
      agentType: (value) => (!value?.trim() ? 'Agent Type is required' : null),
      providerId: (value) => (!value?.trim() ? 'LLM Provider is required' : null),
      modelName: (value) => (!value?.trim() ? 'Model is required' : null),
    },
  });

  // Get available models for selected provider
  const selectedProvider = providers?.find((p: any) => p.id === generatorForm.values.providerId);
  const availableModels = selectedProvider?.generative?.models || [];

  const handleGenerateInstructions = async () => {
    if (!generatorForm.validate().hasErrors) {
      setIsGenerating(true);
      try {
        const response = await fetch(apiUtils.buildApiUrl('/tools/generate-instructions'), {
          method: 'POST',
          headers: {
            ...apiUtils.getAuthHeaders(),
          },
          body: JSON.stringify({
            tool_ids: selectedToolIds,
            llm_provider_id: generatorForm.values.providerId,
            model_name: generatorForm.values.modelName,
            context: {
              persona: generatorForm.values.persona,
              personality: generatorForm.values.personality,
              agent_type: generatorForm.values.agentType,
              selected_tools: selectedTools.map((t: any) => ({
                name: t.display_name || t.name,
                description: t.description,
                type: t.tool_type,
              })),
            },
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to generate instructions');
        }

        const data = await response.json();

        // Set generated instructions in the main form
        form.setFieldValue('instructions', data.instructions);

        notifications.show({
          title: 'Success!',
          message: 'Instructions generated successfully',
          color: 'green',
        });

        setGeneratorModalOpen(false);
        generatorForm.reset();
      } catch (error) {
        notifications.show({
          title: 'Error',
          message: 'Failed to generate instructions. Please try again.',
          color: 'red',
        });
      } finally {
        setIsGenerating(false);
      }
    }
  };

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
          <Group justify="space-between" align="center">
            <div>
              <Text size="sm" fw={600} mb="xs" c="grape">
                Instructions
              </Text>
              <Text size="xs" c="dimmed">
                <strong>Control the overall agent behavior and all tools.</strong> Define personality, response style, approach to tasks, and how to use tools effectively.
              </Text>
            </div>
            <Button
              leftSection={<IconWand size={16} />}
              variant="gradient"
              gradient={{ from: 'grape', to: 'violet', deg: 135 }}
              onClick={() => setGeneratorModalOpen(true)}
            >
              Generate with AI
            </Button>
          </Group>

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

      {/* AI Instructions Generator Modal */}
      <Modal
        opened={generatorModalOpen}
        onClose={() => setGeneratorModalOpen(false)}
        title={
          <Group gap="xs">
            <IconWand size={20} />
            <Text fw={600}>Generate Assistant Instructions with AI</Text>
          </Group>
        }
        size="lg"
      >
        <Stack gap="md">
          <Alert color="blue" variant="light">
            <Text size="sm">
              Answer a few questions to help AI generate personalized instructions for your assistant.
            </Text>
          </Alert>

          {/* Show selected tools */}
          {selectedTools.length > 0 && (
            <Card withBorder padding="sm" bg="gray.0">
              <Stack gap="xs">
                <Text size="sm" fw={600} c="dimmed">
                  Selected Tools ({selectedTools.length})
                </Text>
                <Stack gap={4}>
                  {selectedTools.map((tool: any) => (
                    <Group key={tool.id} gap="xs">
                      <Badge size="sm" variant="light" color="violet">
                        {tool.tool_type}
                      </Badge>
                      <Text size="xs" fw={500}>
                        {tool.display_name || tool.name}
                      </Text>
                      <Text size="xs" c="dimmed" lineClamp={1}>
                        - {tool.description}
                      </Text>
                    </Group>
                  ))}
                </Stack>
              </Stack>
            </Card>
          )}

          <Textarea
            label="Persona"
            description="Who is this assistant? What role does it play?"
            placeholder="E.g., A helpful customer support specialist for a SaaS company"
            required
            minRows={3}
            {...generatorForm.getInputProps('persona')}
          />

          <Select
            label="Personality"
            description="How should the assistant communicate?"
            placeholder="Select personality style"
            required
            data={[
              { value: 'professional', label: 'Professional & Formal' },
              { value: 'friendly', label: 'Friendly & Casual' },
              { value: 'technical', label: 'Technical & Precise' },
              { value: 'empathetic', label: 'Empathetic & Supportive' },
              { value: 'concise', label: 'Concise & Direct' },
            ]}
            {...generatorForm.getInputProps('personality')}
          />

          <Textarea
            label="Agent Type & Workflow"
            description="Describe how this agent should interact with users and what workflow it follows"
            placeholder="E.g., A booking agent that first queries the knowledge base for available options, then asks the user clarifying questions about their preferences, and finally helps them complete the booking"
            required
            minRows={4}
            {...generatorForm.getInputProps('agentType')}
          />

          <Select
            label="LLM Provider"
            description="Select the LLM provider"
            placeholder="Select provider"
            required
            data={providers?.map((p: any) => ({
              value: p.id,
              label: p.name,
            })) || []}
            {...generatorForm.getInputProps('providerId')}
            onChange={(value) => {
              generatorForm.setFieldValue('providerId', value || '');
              generatorForm.setFieldValue('modelName', ''); // Reset model when provider changes
            }}
          />

          {/* Model selection - only show when provider is selected */}
          {generatorForm.values.providerId && availableModels.length > 0 && (
            <Select
              label="Model"
              description="Select which model to use for generation"
              placeholder="Select model"
              required
              data={availableModels.map((model: string) => ({
                value: model,
                label: model,
              }))}
              {...generatorForm.getInputProps('modelName')}
            />
          )}

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => setGeneratorModalOpen(false)}
              disabled={isGenerating}
            >
              Cancel
            </Button>
            <Button
              leftSection={isGenerating ? <Loader size="xs" /> : <IconSparkles size={16} />}
              variant="gradient"
              gradient={{ from: 'grape', to: 'violet', deg: 135 }}
              onClick={handleGenerateInstructions}
              loading={isGenerating}
            >
              Generate Instructions
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
