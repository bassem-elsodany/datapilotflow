/**
 * Single Page Source Node - Configuration
 *
 * Just a single URL to process
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Button,
  Group,
  Stack,
  Text,
  Alert,
} from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface SinglePageConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function SinglePageConfig({ node, onSave, onClose }: SinglePageConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Single Page Source',
      url: node.config?.url || '',
    },

    validate: {
      url: (value) => {
        if (!value?.trim()) return 'URL is required';
        if (!value.startsWith('http')) return 'URL must start with http:// or https://';
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
            Single Page Source Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Process a single web page (no crawling)
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Homepage"
          description="A descriptive name for this source"
          {...form.getInputProps('name')}
        />

        <TextInput
          label="Page URL"
          placeholder="https://company.com/about"
          description="The exact URL of the page to process"
          required
          {...form.getInputProps('url')}
        />

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> Only this single page will be processed (no link following).
          Add <strong>Content Filter</strong> and <strong>Output Format</strong> nodes for more control.
        </Alert>

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            color="green"
            leftSection={<IconCheck size={16} />}
            onClick={handleSave}
          >
            Save Configuration
          </Button>
        </Group>
      </Stack>
    </div>
  );
}
