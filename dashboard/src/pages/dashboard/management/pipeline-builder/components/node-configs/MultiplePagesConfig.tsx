/**
 * Multiple Pages Source Node - Configuration
 *
 * Allows users to upload a file with URLs or paste URLs directly
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Textarea,
  Button,
  Group,
  Stack,
  Text,
  Alert,
  FileInput,
  Badge,
  Tabs,
} from '@mantine/core';
import { IconInfoCircle, IconCheck, IconFileUpload, IconList } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';
import { useState } from 'react';

interface MultiplePagesConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function MultiplePagesConfig({ node, onSave, onClose }: MultiplePagesConfigProps) {
  const [inputMethod, setInputMethod] = useState<'file' | 'paste'>(
    node.config?.file_name ? 'file' : 'paste'
  );

  const form = useForm({
    initialValues: {
      name: node.name || 'Multiple Pages Source',
      base_url: node.config?.base_url || '',
      file: null as File | null,
      file_name: node.config?.file_name || '',
      urls_text: node.config?.urls?.join('\n') || '',
    },

    validate: {
      base_url: (value) => {
        if (!value?.trim()) return 'Base URL is required';
        if (!value.startsWith('http')) return 'URL must start with http:// or https://';
        return null;
      },
      urls_text: (value, values) => {
        if (inputMethod === 'paste' && !value?.trim()) {
          return 'Please enter at least one URL';
        }
        return null;
      },
      file: (value, values) => {
        if (inputMethod === 'file' && !value && !values.file_name) {
          return 'Please upload a file';
        }
        return null;
      },
    },
  });

  const handleSave = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;

    // Parse URLs from textarea
    const urls = inputMethod === 'paste'
      ? form.values.urls_text
          .split('\n')
          .map(url => url.trim())
          .filter(url => url.length > 0)
      : [];

    const config = {
      name: form.values.name,
      base_url: form.values.base_url,
      urls: inputMethod === 'paste' ? urls : [],
      file_name: inputMethod === 'file' ? (form.values.file?.name || form.values.file_name) : undefined,
      configured: true,
    };

    onSave(node.id, config);
    onClose();
  };

  const urlCount = inputMethod === 'paste'
    ? form.values.urls_text.split('\n').filter(url => url.trim().length > 0).length
    : 0;

  return (
    <div style={{ padding: '1.5rem', maxWidth: '600px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#45c9bb" mb="xs">
            Multiple Pages Source Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Upload a file with URLs or paste URLs directly (one per line)
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Documentation Pages"
          description="A descriptive name for this source"
          {...form.getInputProps('name')}
        />

        <TextInput
          label="Base URL"
          placeholder="https://docs.company.com"
          description="The base domain for all URLs"
          required
          {...form.getInputProps('base_url')}
        />

        <Tabs value={inputMethod} onChange={(value) => setInputMethod(value as 'file' | 'paste')}>
          <Tabs.List>
            <Tabs.Tab value="file" leftSection={<IconFileUpload size={16} />}>
              Upload File
            </Tabs.Tab>
            <Tabs.Tab value="paste" leftSection={<IconList size={16} />}>
              Paste URLs
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="file" pt="md">
            <Stack gap="sm">
              <FileInput
                label="Upload URLs File"
                placeholder="Select a .txt file with URLs"
                description="Text file with one URL per line (max 50,000 URLs)"
                accept=".txt"
                leftSection={<IconFileUpload size={16} />}
                {...form.getInputProps('file')}
              />
              {form.values.file_name && !form.values.file && (
                <Badge color="green" variant="light">
                  Current file: {form.values.file_name}
                </Badge>
              )}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="paste" pt="md">
            <Stack gap="sm">
              <Textarea
                label="Paste URLs"
                placeholder="https://docs.company.com/page1&#10;https://docs.company.com/page2&#10;https://docs.company.com/page3"
                description="One URL per line (max 50,000 URLs)"
                rows={8}
                required={inputMethod === 'paste'}
                {...form.getInputProps('urls_text')}
              />
              {urlCount > 0 && (
                <Badge color="blue" variant="light">
                  {urlCount} URL{urlCount !== 1 ? 's' : ''} detected
                </Badge>
              )}
            </Stack>
          </Tabs.Panel>
        </Tabs>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> URLs will be processed in the order provided. Add{' '}
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
