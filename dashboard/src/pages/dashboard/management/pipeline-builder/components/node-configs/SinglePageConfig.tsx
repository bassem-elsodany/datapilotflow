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
  Textarea,
  Tabs,
} from '@mantine/core';
import { IconInfoCircle, IconCheck, IconAlertCircle } from '@tabler/icons-react';
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
      target_elements: node.config?.target_elements || '',
      exclude_elements: node.config?.exclude_elements || '',
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
        <Tabs defaultValue="basic" orientation="vertical">
          <Tabs.List style={{ minWidth: '150px' }}>
            <Tabs.Tab value="basic">Basic</Tabs.Tab>
            <Tabs.Tab value="selectors">CSS Selectors (Optional)</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="basic">
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
                Use the CSS Selectors tab for precise element selection.
              </Alert>
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="selectors">
            <Stack gap="md">
              <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
                <Text size="xs">
                  <strong>CSS Selectors for Content Extraction</strong>
                  <br />
                  Specify CSS selectors to include or exclude content. Separate multiple selectors with commas.
                  <br />
                  Example: <code>.article, main &gt; p</code>
                </Text>
              </Alert>

              <Textarea
                label="Target Elements (Include)"
                placeholder=".content, main, article"
                description="CSS selectors for content to include. Leave empty to include all content."
                rows={3}
                {...form.getInputProps('target_elements')}
              />

              <Textarea
                label="Exclude Elements"
                placeholder=".nav, footer, .sidebar, script"
                description="CSS selectors for content to exclude. This takes priority over target elements."
                rows={3}
                {...form.getInputProps('exclude_elements')}
              />

              <Alert icon={<IconAlertCircle size={16} />} color="orange" variant="light">
                <Text size="xs">
                  <strong>Note:</strong> If you specify target elements, only those will be extracted.
                  If you specify exclude elements, they will be removed from extraction.
                </Text>
              </Alert>
            </Stack>
          </Tabs.Panel>
        </Tabs>

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
