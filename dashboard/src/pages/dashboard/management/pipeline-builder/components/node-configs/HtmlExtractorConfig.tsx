/**
 * HTML Extractor Node Configuration
 *
 * Extracts raw HTML content with content filter threshold
 */

import { Stack, Text, TextInput, NumberInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { PipelineNode } from '@/api/resources/pipelines';
import { NodeConfigFooter } from './NodeConfigFooter';

interface HtmlExtractorConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function HtmlExtractorConfig({ node, onSave, onClose }: HtmlExtractorConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'HTML Extractor',
      content_filter_threshold: node.config?.content_filter_threshold || 0.6,
    },
    validate: {
      content_filter_threshold: (value) =>
        (value < 0 || value > 1 ? 'Threshold must be between 0 and 1' : null),
    },
  });

  const handleSave = () => {
    const validation = form.validate();
    if (!validation.hasErrors) {
      const config = {
        ...form.values,
        configured: true,
      };
      onSave(node.id, config);
      onClose();
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <Stack gap="md">
        <Text size="xs" c="dimmed">
          Extract raw HTML content as-is
        </Text>

        <TextInput
          label="Node Name"
          placeholder="HTML Extractor"
          description="A descriptive name for this node"
          {...form.getInputProps('name')}
        />

        <NumberInput
          label="Content Filter Threshold"
          placeholder="0.6"
          min={0}
          max={1}
          step={0.1}
          decimalScale={1}
          description="Lower → more content retained, higher → more content pruned (0.0 to 1.0)"
          required
          {...form.getInputProps('content_filter_threshold')}
        />

        <NodeConfigFooter onSave={handleSave} onClose={onClose} />
      </Stack>
    </div>
  );
}
