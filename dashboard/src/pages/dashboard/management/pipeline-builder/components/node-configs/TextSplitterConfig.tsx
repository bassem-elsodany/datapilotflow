/**
 * Text Splitter Node - Simple Configuration
 *
 * Configure how to split text into chunks
 */

import { useForm } from '@mantine/form';
import { TextInput, Slider, Button, Group, Stack, Text, Alert, Badge } from '@mantine/core';
import { IconInfoCircle, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface TextSplitterConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function TextSplitterConfig({ node, onSave, onClose }: TextSplitterConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Text Splitter',
      chunk_size: node.config?.chunk_size || 512,
      chunk_overlap: node.config?.chunk_overlap || 64,
    },
  });

  // Auto-calculate overlap as 12.5% of chunk size
  const handleChunkSizeChange = (value: number) => {
    form.setFieldValue('chunk_size', value);
    form.setFieldValue('chunk_overlap', Math.round(value * 0.125));
  };

  const handleSave = () => {
    const config = {
      ...form.values,
      splitter_type: 'TEXT',
      separators: ['\n\n', '\n', ' ', ''],
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
            Text Splitter Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Configure how to split documents into chunks for processing
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Documentation Splitter"
          description="A descriptive name for this splitter"
          {...form.getInputProps('name')}
        />

        <div>
          <Group justify="space-between" mb="xs">
            <Text size="sm" fw={500}>
              Chunk Size
            </Text>
            <Badge color="blue" variant="light">
              {form.values.chunk_size} characters
            </Badge>
          </Group>
          <Text size="xs" c="dimmed" mb="md">
            Size of each text chunk in characters
          </Text>
          <Slider
            min={64}
            max={4096}
            step={64}
            marks={[
              { value: 64, label: '64' },
              { value: 512, label: '512' },
              { value: 1024, label: '1K' },
              { value: 2048, label: '2K' },
              { value: 4096, label: '4K' },
            ]}
            value={form.values.chunk_size}
            onChange={handleChunkSizeChange}
          />
        </div>

        <div>
          <Group justify="space-between" mb="xs">
            <Text size="sm" fw={500}>
              Chunk Overlap
            </Text>
            <Badge color="green" variant="light">
              {form.values.chunk_overlap} characters (auto)
            </Badge>
          </Group>
          <Text size="xs" c="dimmed" mb="md">
            Overlap between chunks (auto-calculated as 12.5% of chunk size)
          </Text>
          <Slider
            min={0}
            max={512}
            step={8}
            marks={[
              { value: 0, label: '0' },
              { value: 128, label: '128' },
              { value: 256, label: '256' },
              { value: 512, label: '512' },
            ]}
            {...form.getInputProps('chunk_overlap')}
          />
        </div>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Recommended settings:</strong>
          <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
            <li><strong>512-1024 chars:</strong> Best for most documentation</li>
            <li><strong>256-512 chars:</strong> For short-form content</li>
            <li><strong>1024-2048 chars:</strong> For long-form articles</li>
          </ul>
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
