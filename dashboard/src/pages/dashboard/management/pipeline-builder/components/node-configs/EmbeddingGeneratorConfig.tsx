/**
 * Embedding Generator Node - Simple Configuration
 *
 * Select embedding model provider and model
 */

import { useForm } from '@mantine/form';
import { TextInput, Select, Button, Group, Stack, Text, Alert, Badge, Paper } from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface EmbeddingGeneratorConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function EmbeddingGeneratorConfig({ node, onSave, onClose }: EmbeddingGeneratorConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Embedding Generator',
      model_provider_id: node.config?.model_provider_id || '',
      model_name: node.config?.model_name || '',
      vector_dimension: node.config?.vector_dimension || 1536,
      batch_size: node.config?.batch_size || 100,
    },

    validate: {
      model_provider_id: (value) => (!value ? 'Provider is required' : null),
      model_name: (value) => (!value ? 'Model is required' : null),
    },
  });

  // Mock data - in real app, fetch from API
  const providers = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'azure_openai', label: 'Azure OpenAI' },
    { value: 'cohere', label: 'Cohere' },
  ];

  const models: Record<string, { value: string; label: string; dimension: number; cost: string }[]> = {
    openai: [
      { value: 'text-embedding-3-small', label: 'text-embedding-3-small', dimension: 1536, cost: '$0.02/1M tokens' },
      { value: 'text-embedding-3-large', label: 'text-embedding-3-large', dimension: 3072, cost: '$0.13/1M tokens' },
      { value: 'text-embedding-ada-002', label: 'text-embedding-ada-002 (legacy)', dimension: 1536, cost: '$0.10/1M tokens' },
    ],
    azure_openai: [
      { value: 'text-embedding-ada-002', label: 'text-embedding-ada-002', dimension: 1536, cost: 'Custom pricing' },
    ],
    cohere: [
      { value: 'embed-english-v3.0', label: 'embed-english-v3.0', dimension: 1024, cost: '$0.10/1M tokens' },
      { value: 'embed-multilingual-v3.0', label: 'embed-multilingual-v3.0', dimension: 1024, cost: '$0.10/1M tokens' },
    ],
  };

  const availableModels = form.values.model_provider_id ? models[form.values.model_provider_id] : [];

  const handleModelChange = (value: string | null) => {
    if (value) {
      form.setFieldValue('model_name', value);
      const model = availableModels.find((m) => m.value === value);
      if (model) {
        form.setFieldValue('vector_dimension', model.dimension);
      }
    }
  };

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

  const selectedModel = availableModels.find((m) => m.value === form.values.model_name);

  return (
    <div style={{ padding: '1.5rem', maxWidth: '500px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#45c9bb" mb="xs">
            Embedding Generator Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Select the model to generate vector embeddings
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="OpenAI Embeddings"
          description="A descriptive name for this generator"
          {...form.getInputProps('name')}
        />

        <Select
          label="Embedding Provider"
          placeholder="Select provider"
          description="Choose your embedding model provider"
          data={providers}
          required
          {...form.getInputProps('model_provider_id')}
        />

        {form.values.model_provider_id && (
          <Select
            label="Embedding Model"
            placeholder="Select model"
            description="Choose the specific model to use"
            data={availableModels.map((m) => ({
              value: m.value,
              label: m.label,
            }))}
            required
            value={form.values.model_name}
            onChange={handleModelChange}
          />
        )}

        {selectedModel && (
          <Paper p="md" withBorder style={{ backgroundColor: '#f0fdf4' }}>
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" fw={500}>
                  Vector Dimension:
                </Text>
                <Badge color="blue">{selectedModel.dimension}</Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm" fw={500}>
                  Cost:
                </Text>
                <Badge color="green">{selectedModel.cost}</Badge>
              </Group>
            </Stack>
          </Paper>
        )}

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> text-embedding-3-small offers the best balance of quality and
          cost for most use cases
        </Alert>

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button color="green" leftSection={<IconCheck size={16} />} onClick={handleSave}>
            Save Configuration
          </Button>
        </Group>
      </Stack>
    </div>
  );
}
