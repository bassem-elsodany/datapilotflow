/**
 * Output Format Node Configuration
 *
 * Selects the output format for extracted content
 */

import { useForm } from '@mantine/form';
import {
  RadioGroup,
  Radio,
  Button,
  Group,
  Stack,
  Text,
  Card,
  Alert,
} from '@mantine/core';
import { IconCheck, IconFileText } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface OutputFormatConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function OutputFormatConfig({ node, onSave, onClose }: OutputFormatConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Output Format',
      format: node.config?.format || 'markdown',
    },

    validate: {
      format: (value) => {
        if (!value) return 'Output format is required';
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
        <div>
          <Text size="sm" c="dimmed">
            Choose how the extracted content should be formatted.
            This affects readability and processing in downstream nodes.
          </Text>
        </div>

        <RadioGroup
          label="Output Format"
          description="Select the format for extracted content"
          {...form.getInputProps('format')}
        >
          <Stack gap="md" mt="md">
            <Card withBorder p="md" radius="md" style={{ cursor: 'pointer' }}>
              <Radio
                value="html"
                label={
                  <div>
                    <Text fw={500} size="sm">HTML</Text>
                    <Text size="xs" c="dimmed">
                      Raw HTML with structure. Best for precise element selection.
                    </Text>
                  </div>
                }
              />
            </Card>

            <Card withBorder p="md" radius="md" style={{ cursor: 'pointer' }}>
              <Radio
                value="markdown"
                label={
                  <div>
                    <Text fw={500} size="sm">Markdown</Text>
                    <Text size="xs" c="dimmed">
                      Structured markdown format. Best for readability and downstream processing.
                    </Text>
                  </div>
                }
              />
            </Card>

            <Card withBorder p="md" radius="md" style={{ cursor: 'pointer' }}>
              <Radio
                value="llm_markdown"
                label={
                  <div>
                    <Text fw={500} size="sm">LLM-Enhanced Markdown</Text>
                    <Text size="xs" c="dimmed">
                      LLM-powered markdown with semantic understanding. Best for quality content extraction.
                    </Text>
                  </div>
                }
              />
            </Card>
          </Stack>
        </RadioGroup>

        <Alert title="Format Selection Impact" color="blue">
          <Text size="xs">
            The output format affects how content is extracted and processed in downstream nodes.
            Use markdown for most cases, HTML for precise selection, and LLM-enhanced for highest quality.
          </Text>
        </Alert>

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            color="blue"
            leftSection={<IconCheck size={16} />}
            onClick={handleSave}
          >
            Save Format
          </Button>
        </Group>
      </Stack>
    </div>
  );
}
