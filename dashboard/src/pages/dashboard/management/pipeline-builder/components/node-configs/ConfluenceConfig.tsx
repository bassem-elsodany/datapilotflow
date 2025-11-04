/**
 * Confluence Source Node - Configuration
 *
 * Allows users to configure Confluence space crawling
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Button,
  Group,
  Stack,
  Text,
  Alert,
  NumberInput,
} from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface ConfluenceConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function ConfluenceConfig({ node, onSave, onClose }: ConfluenceConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Confluence Source',
      url: node.config?.url || '',
      crawl_depth: node.config?.crawl_depth || 4,
      css_selector: node.config?.css_selector || 'main > article',
      content_filter_threshold: node.config?.content_filter_threshold || 0.6,
    },

    validate: {
      url: (value) => {
        if (!value?.trim()) return 'Confluence URL is required';
        if (!value.startsWith('http')) return 'URL must start with http:// or https://';
        return null;
      },
      crawl_depth: (value) => {
        if (!value || value < 1 || value > 10) {
          return 'Crawl depth must be between 1 and 10';
        }
        return null;
      },
    },
  });

  const handleSave = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;

    const config = {
      name: form.values.name,
      url: form.values.url,
      crawl_depth: form.values.crawl_depth,
      css_selector: form.values.css_selector,
      content_filter_threshold: form.values.content_filter_threshold,
      configured: true,
    };

    onSave(node.id, config);
    onClose();
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '600px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#45c9bb" mb="xs">
            Confluence Source Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Configure Confluence space crawling settings
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Confluence Docs"
          description="A descriptive name for this source"
          {...form.getInputProps('name')}
        />

        <TextInput
          label="Confluence URL"
          placeholder="https://company.atlassian.net/wiki"
          description="Your Confluence space URL"
          required
          {...form.getInputProps('url')}
        />

        <NumberInput
          label="Crawl Depth"
          placeholder="4"
          description="How many levels deep to crawl (1-10)"
          min={1}
          max={10}
          required
          {...form.getInputProps('crawl_depth')}
        />

        <TextInput
          label="CSS Selector"
          placeholder="main > article"
          description="CSS selector to extract content"
          {...form.getInputProps('css_selector')}
        />

        <NumberInput
          label="Content Filter Threshold"
          placeholder="0.6"
          description="Threshold for filtering content (0-1)"
          min={0}
          max={1}
          step={0.1}
          {...form.getInputProps('content_filter_threshold')}
        />

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> Make sure you have proper access to the Confluence space. Add{' '}
          <strong>Content Filter</strong> and <strong>Output Format</strong> nodes for more control.
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
