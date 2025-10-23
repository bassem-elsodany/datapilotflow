/**
 * Vector Database Node - Simple Configuration
 *
 * Configure vector database collection settings
 */

import { useForm } from '@mantine/form';
import { TextInput, Button, Group, Stack, Text, Alert, Switch, Paper } from '@mantine/core';
import { IconInfoCircle, IconCheck, IconAlertCircle } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface VectorDatabaseConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function VectorDatabaseConfig({ node, onSave, onClose }: VectorDatabaseConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Vector Database',
      collection_name: node.config?.collection_name || '',
      collection_description: node.config?.collection_description || '',
      clear_collection_before_start: node.config?.clear_collection_before_start || false,
      check_duplicates_before_insert: node.config?.check_duplicates_before_insert || false,
    },

    validate: {
      collection_name: (value) => {
        if (!value?.trim()) return 'Collection name is required';
        if (!/^[a-z0-9_]+$/.test(value)) {
          return 'Only lowercase letters, numbers, and underscores allowed';
        }
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
    <div style={{ padding: '1.5rem', maxWidth: '500px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#45c9bb" mb="xs">
            Vector Database Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Configure collection for storing vector embeddings
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Documentation Collection"
          description="A descriptive name for this storage"
          {...form.getInputProps('name')}
        />

        <TextInput
          label="Collection Name"
          placeholder="company_docs_v1"
          description="Unique name for the collection (lowercase, numbers, underscores only)"
          required
          {...form.getInputProps('collection_name')}
        />

        <TextInput
          label="Description"
          placeholder="Company documentation knowledge base"
          description="Optional description of what this collection contains"
          {...form.getInputProps('collection_description')}
        />

        <Paper p="md" withBorder>
          <Stack gap="md">
            <div>
              <Switch
                label="Clear collection before starting"
                description="Remove all existing data before adding new documents"
                {...form.getInputProps('clear_collection_before_start', { type: 'checkbox' })}
              />
            </div>

            <div>
              <Switch
                label="Check for duplicates"
                description="Skip documents that are already in the collection (slower but prevents duplicates)"
                {...form.getInputProps('check_duplicates_before_insert', { type: 'checkbox' })}
              />
            </div>
          </Stack>
        </Paper>

        {form.values.clear_collection_before_start && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="red"
            variant="light"
            title="Warning"
          >
            Clearing the collection will <strong>permanently delete all existing data</strong>. Make
            sure you have backups if needed.
          </Alert>
        )}

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Auto-configured:</strong> Embedding model and vector dimensions will be
          inherited from the Embedding Generator node
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
