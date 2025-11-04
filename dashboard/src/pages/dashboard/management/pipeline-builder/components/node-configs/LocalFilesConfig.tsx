/**
 * Local Files Source Node - Configuration
 *
 * Allows users to upload local files (PDF, Markdown, HTML, DOCX, TXT, etc.)
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Button,
  Group,
  Stack,
  Text,
  Alert,
  FileInput,
  Badge,
  MultiSelect,
} from '@mantine/core';
import { IconInfoCircle, IconCheck, IconFileUpload } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';
import { useState } from 'react';

interface LocalFilesConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

const SUPPORTED_FILE_TYPES = [
  { value: 'html', label: 'HTML' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'pdf', label: 'PDF' },
  { value: 'docx', label: 'DOCX' },
  { value: 'txt', label: 'Text' },
];

export function LocalFilesConfig({ node, onSave, onClose }: LocalFilesConfigProps) {
  const [files, setFiles] = useState<File[]>([]);

  const form = useForm({
    initialValues: {
      name: node.name || 'Local Files Source',
      file_types: node.config?.file_types || ['html', 'markdown', 'pdf', 'docx', 'txt'],
      output_format: node.config?.output_format || 'markdown',
    },

    validate: {
      file_types: (value) => {
        if (!value || value.length === 0) {
          return 'Please select at least one file type';
        }
        return null;
      },
      output_format: (value) => {
        if (!value?.trim()) {
          return 'Output format is required';
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
      file_types: form.values.file_types,
      output_format: form.values.output_format,
      local_files: node.config?.local_files || [],
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
            Local Files Source Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Configure local file processing options
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Local Documents"
          description="A descriptive name for this source"
          {...form.getInputProps('name')}
        />

        <MultiSelect
          label="Supported File Types"
          placeholder="Select file types to support"
          description="Which file formats should be processed"
          data={SUPPORTED_FILE_TYPES}
          searchable
          clearable
          required
          {...form.getInputProps('file_types')}
        />

        <TextInput
          label="Output Format"
          placeholder="markdown"
          description="Format for extracted content (e.g., markdown, html, text)"
          {...form.getInputProps('output_format')}
        />

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Tip:</strong> Files will be processed in the order provided. Add{' '}
          <strong>Splitter</strong> and <strong>Embeddings</strong> nodes to complete the pipeline.
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
