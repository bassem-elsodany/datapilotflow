/**
 * LLM Content Filter Node Configuration
 *
 * Configures LLM-based filtering during crawling/extraction
 * This allows fine-grained control over content quality and relevance
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Textarea,
  Slider,
  Button,
  Group,
  Stack,
  Text,
  Alert,
  NumberInput,
  Select,
} from '@mantine/core';
import { IconInfoCircle, IconCheck, IconBrain } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface LlmContentFilterConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function LlmContentFilterConfig({ node, onSave, onClose }: LlmContentFilterConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'LLM Content Filter',
      llm_model_name: node.config?.llm_model_name || 'gpt-4o-mini',
      instruction: node.config?.instruction || 'Keep content that is relevant and well-structured. Remove noise, ads, and irrelevant sections.',
      temperature: node.config?.temperature || 0.0,
      chunk_token_threshold: node.config?.chunk_token_threshold || 500,
    },

    validate: {
      llm_model_name: (value) => {
        if (!value?.trim()) return 'LLM model name is required';
        return null;
      },
      instruction: (value) => {
        if (!value?.trim()) return 'Filtering instruction is required';
        if (value.length < 20) return 'Instruction should be at least 20 characters';
        return null;
      },
      temperature: (value) => {
        if (value < 0 || value > 2) return 'Temperature must be between 0 and 2';
        return null;
      },
      chunk_token_threshold: (value) => {
        if (value < 100) return 'Token threshold must be at least 100';
        if (value > 4000) return 'Token threshold must not exceed 4000';
        return null;
      },
    },
  });

  const handleSave = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;

    const config = {
      ...form.values,
      configured: true,
    };
    onSave(node.id, config);
    onClose();
  };

  return (
    <div style={{ padding: '1rem' }}>
      <Stack gap="md">
        <Alert icon={<IconBrain size={16} />} color="violet" variant="light">
          <Text size="sm" fw={500}>LLM-Powered Content Filtering</Text>
          <Text size="xs" c="dimmed" mt="xs">
            Use an LLM to intelligently filter content based on semantic relevance and quality.
            This runs during extraction to improve content quality.
          </Text>
        </Alert>

        <TextInput
          label="Node Name"
          placeholder="Quality Filter"
          description="A descriptive name for this filter"
          {...form.getInputProps('name')}
        />

        <Select
          label="LLM Model"
          placeholder="Select model"
          description="The LLM model to use for filtering"
          data={[
            { value: 'gpt-4o-mini', label: 'GPT-4O Mini' },
            { value: 'gpt-4o', label: 'GPT-4O' },
            { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
            { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
            { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
          ]}
          {...form.getInputProps('llm_model_name')}
        />

        <Textarea
          label="Filtering Instruction"
          placeholder="Describe what content to keep and what to remove..."
          description="Natural language instruction for the LLM. Be specific about what makes good content."
          rows={4}
          required
          {...form.getInputProps('instruction')}
        />

        <div>
          <Text size="sm" fw={500} mb="xs">
            Temperature ({form.values.temperature.toFixed(1)})
          </Text>
          <Text size="xs" c="dimmed" mb="md">
            Lower values (0) = more deterministic. Higher values (1-2) = more creative
          </Text>
          <Slider
            min={0}
            max={2}
            step={0.1}
            marks={[
              { value: 0, label: 'Deterministic' },
              { value: 1, label: 'Balanced' },
              { value: 2, label: 'Creative' },
            ]}
            {...form.getInputProps('temperature')}
          />
        </div>

        <NumberInput
          label="Token Threshold"
          description="Minimum tokens per chunk (100-4000). Chunks below this are filtered."
          placeholder="500"
          min={100}
          max={4000}
          step={50}
          required
          {...form.getInputProps('chunk_token_threshold')}
        />

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> Start with a general instruction like "Keep relevant, high-quality content"
          and adjust temperature based on results. Lower temperature is recommended for consistency.
        </Alert>

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            color="violet"
            leftSection={<IconCheck size={16} />}
            onClick={handleSave}
          >
            Save Filter Configuration
          </Button>
        </Group>
      </Stack>
    </div>
  );
}
