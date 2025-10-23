/**
 * Website Source Node - Simple Configuration
 *
 * Just the essentials: URL + Crawl Depth
 * Other options (filtering, output) are handled by separate nodes in the pipeline
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Slider,
  Button,
  Group,
  Stack,
  Text,
  Alert,
} from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface WebsiteSourceConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function WebsiteSourceConfig({ node, onSave, onClose }: WebsiteSourceConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Website Source',
      url: node.config?.url || '',
      crawl_depth: node.config?.crawl_depth || 4,
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
    <div style={{ padding: '1rem' }}>
      <Stack gap="md">
        <Text size="xs" c="dimmed">
          Configure the website to crawl. Use additional filter nodes for advanced options.
        </Text>

        <TextInput
          label="Node Name"
          placeholder="Company Documentation"
          description="A descriptive name for this source"
          {...form.getInputProps('name')}
        />

        <TextInput
          label="Website URL"
          placeholder="https://docs.company.com"
          description="The base URL to start crawling from"
          required
          {...form.getInputProps('url')}
        />

        <div>
          <Text size="sm" fw={500} mb="xs">
            Crawl Depth
          </Text>
          <Text size="xs" c="dimmed" mb="md">
            How many levels of links to follow (0 = only the starting URL)
          </Text>
          <Slider
            min={0}
            max={10}
            step={1}
            marks={[
              { value: 0, label: '0' },
              { value: 2, label: '2' },
              { value: 4, label: '4' },
              { value: 6, label: '6' },
              { value: 8, label: '8' },
              { value: 10, label: '10' },
            ]}
            label={(value) => `${value} levels`}
            {...form.getInputProps('crawl_depth')}
          />
        </div>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> Start with depth 2-4 for documentation sites. Add{' '}
          <strong>Domain Filter</strong> and <strong>Content Filter</strong> nodes for more control.
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
