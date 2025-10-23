/**
 * Content Filter Node - Simple Configuration
 *
 * Specify which HTML elements to extract using CSS selectors
 */

import { useForm } from '@mantine/form';
import {
  TextInput,
  Button,
  Group,
  Stack,
  Text,
  Paper,
  ActionIcon,
  Alert,
} from '@mantine/core';
import { IconInfoCircle, IconPlus, IconTrash, IconCheck } from '@tabler/icons-react';
import { PipelineNode } from '@/api/resources/pipelines';

interface ContentFilterConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function ContentFilterConfig({ node, onSave, onClose }: ContentFilterConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Content Filter',
      target_elements: node.config?.target_elements || [],
    },
  });

  const handleSave = () => {
    const config = {
      ...form.values,
      // Filter out empty strings
      target_elements: form.values.target_elements.filter((s: string) => s.trim()),
      configured: true,
    };
    onSave(node.id, config);
    onClose();
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '500px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#ddde65" mb="xs">
            Content Filter Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Specify which parts of the page to extract using CSS selectors
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Main Content Filter"
          description="A descriptive name for this filter"
          {...form.getInputProps('name')}
        />

        <Paper p="md" withBorder>
          <Text size="sm" fw={500} mb="xs">
            Target HTML Elements
          </Text>
          <Text size="xs" c="dimmed" mb="sm">
            Use CSS selectors like: main, article, .content, #documentation
          </Text>
          <Stack gap="xs">
            {form.values.target_elements.map((element: string, index: number) => (
              <Group key={index} gap="xs">
                <TextInput
                  placeholder="main"
                  style={{ flex: 1 }}
                  value={element}
                  onChange={(e) => {
                    const newElements = [...form.values.target_elements];
                    newElements[index] = e.currentTarget.value;
                    form.setFieldValue('target_elements', newElements);
                  }}
                />
                <ActionIcon
                  color="red"
                  variant="light"
                  onClick={() => {
                    const newElements = form.values.target_elements.filter(
                      (_: string, i: number) => i !== index
                    );
                    form.setFieldValue('target_elements', newElements);
                  }}
                >
                  <IconTrash size={16} />
                </ActionIcon>
              </Group>
            ))}
            <Button
              variant="light"
              size="sm"
              leftSection={<IconPlus size={16} />}
              onClick={() =>
                form.setFieldValue('target_elements', [...form.values.target_elements, ''])
              }
            >
              Add Selector
            </Button>
          </Stack>
        </Paper>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          💡 <strong>Common selectors:</strong>
          <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
            <li><code>main</code> - Main content area</li>
            <li><code>article</code> - Article elements</li>
            <li><code>.content</code> - Elements with class "content"</li>
            <li><code>#docs</code> - Element with id "docs"</li>
          </ul>
        </Alert>

        <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
          ℹ️ Leave empty to extract the entire page content
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
