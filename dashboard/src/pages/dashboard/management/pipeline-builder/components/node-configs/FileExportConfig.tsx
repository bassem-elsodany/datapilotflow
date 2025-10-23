/**
 * File Export Node - Simple Configuration
 *
 * Configure file export settings
 */

import { useForm } from '@mantine/form';
import { Button, Group, Stack, Text, Radio, Paper, Switch, Alert } from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface FileExportConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function FileExportConfig({ node, onSave, onClose }: FileExportConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'File Export',
      file_format: node.config?.file_format || 'json',
      save_individual_files: node.config?.save_individual_files !== false,
      write_consolidated_file: node.config?.write_consolidated_file || false,
      include_metadata: node.config?.include_metadata !== false,
    },
  });

  const handleSave = () => {
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
          <Text size="lg" fw={600} c="#3bc57d" mb="xs">
            File Export Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Configure how to export processed documents to files
          </Text>
        </div>

        <Radio.Group
          label="File Format"
          description="Choose the export format"
          {...form.getInputProps('file_format')}
        >
          <Stack gap="sm" mt="sm">
            <Paper
              p="sm"
              withBorder
              style={{
                cursor: 'pointer',
                backgroundColor: form.values.file_format === 'json' ? '#f0fdf4' : 'transparent',
                borderColor: form.values.file_format === 'json' ? '#3bc57d' : '#e0e0e0',
              }}
              onClick={() => form.setFieldValue('file_format', 'json')}
            >
              <Radio
                value="json"
                label="JSON (Structured)"
                description="Best for programmatic access"
              />
            </Paper>

            <Paper
              p="sm"
              withBorder
              style={{
                cursor: 'pointer',
                backgroundColor: form.values.file_format === 'csv' ? '#f0fdf4' : 'transparent',
                borderColor: form.values.file_format === 'csv' ? '#3bc57d' : '#e0e0e0',
              }}
              onClick={() => form.setFieldValue('file_format', 'csv')}
            >
              <Radio value="csv" label="CSV (Tabular)" description="Easy to open in Excel" />
            </Paper>

            <Paper
              p="sm"
              withBorder
              style={{
                cursor: 'pointer',
                backgroundColor:
                  form.values.file_format === 'markdown' ? '#f0fdf4' : 'transparent',
                borderColor: form.values.file_format === 'markdown' ? '#3bc57d' : '#e0e0e0',
              }}
              onClick={() => form.setFieldValue('file_format', 'markdown')}
            >
              <Radio
                value="markdown"
                label="Markdown (Readable)"
                description="Human-readable format"
              />
            </Paper>

            <Paper
              p="sm"
              withBorder
              style={{
                cursor: 'pointer',
                backgroundColor: form.values.file_format === 'text' ? '#f0fdf4' : 'transparent',
                borderColor: form.values.file_format === 'text' ? '#3bc57d' : '#e0e0e0',
              }}
              onClick={() => form.setFieldValue('file_format', 'text')}
            >
              <Radio value="text" label="Plain Text" description="Simple text format" />
            </Paper>
          </Stack>
        </Radio.Group>

        <Paper p="md" withBorder>
          <Stack gap="md">
            <div>
              <Switch
                label="Save individual files"
                description="Create a separate file for each document"
                {...form.getInputProps('save_individual_files', { type: 'checkbox' })}
              />
            </div>

            <div>
              <Switch
                label="Create consolidated file"
                description="Combine all documents into one file (can be large)"
                {...form.getInputProps('write_consolidated_file', { type: 'checkbox' })}
              />
            </div>

            <div>
              <Switch
                label="Include metadata"
                description="Add source URL, timestamps, and other metadata"
                {...form.getInputProps('include_metadata', { type: 'checkbox' })}
              />
            </div>
          </Stack>
        </Paper>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 Files will be saved to: <code>./output/</code>
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
