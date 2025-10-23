/**
 * Domain Filter Node - Simple Configuration
 *
 * Filter which domains to include or exclude during crawling
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

interface DomainFilterConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function DomainFilterConfig({ node, onSave, onClose }: DomainFilterConfigProps) {
  const form = useForm({
    initialValues: {
      name: node.name || 'Domain Filter',
      allowed_subdomains: node.config?.allowed_subdomains || [],
      blocked_subdomains: node.config?.blocked_subdomains || [],
    },
  });

  const handleSave = () => {
    const config = {
      ...form.values,
      // Filter out empty strings
      allowed_subdomains: form.values.allowed_subdomains.filter((s: string) => s.trim()),
      blocked_subdomains: form.values.blocked_subdomains.filter((s: string) => s.trim()),
      configured: true,
    };
    onSave(node.id, config);
    onClose();
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '500px' }}>
      <Stack gap="lg">
        <div>
          <Text size="lg" fw={600} c="#bbe773" mb="xs">
            Domain Filter Configuration
          </Text>
          <Text size="sm" c="dimmed">
            Control which domains and subdomains to crawl
          </Text>
        </div>

        <TextInput
          label="Node Name"
          placeholder="Documentation Domain Filter"
          description="A descriptive name for this filter"
          {...form.getInputProps('name')}
        />

        <Paper p="md" withBorder>
          <Text size="sm" fw={500} mb="xs">
            Allowed Subdomains
          </Text>
          <Text size="xs" c="dimmed" mb="sm">
            Only crawl these subdomains (leave empty to allow all)
          </Text>
          <Stack gap="xs">
            {form.values.allowed_subdomains.map((subdomain: string, index: number) => (
              <Group key={index} gap="xs">
                <TextInput
                  placeholder="docs.company.com"
                  style={{ flex: 1 }}
                  value={subdomain}
                  onChange={(e) => {
                    const newSubdomains = [...form.values.allowed_subdomains];
                    newSubdomains[index] = e.currentTarget.value;
                    form.setFieldValue('allowed_subdomains', newSubdomains);
                  }}
                />
                <ActionIcon
                  color="red"
                  variant="light"
                  onClick={() => {
                    const newSubdomains = form.values.allowed_subdomains.filter(
                      (_: string, i: number) => i !== index
                    );
                    form.setFieldValue('allowed_subdomains', newSubdomains);
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
                form.setFieldValue('allowed_subdomains', [...form.values.allowed_subdomains, ''])
              }
            >
              Add Subdomain
            </Button>
          </Stack>
        </Paper>

        <Paper p="md" withBorder>
          <Text size="sm" fw={500} mb="xs">
            Blocked Subdomains
          </Text>
          <Text size="xs" c="dimmed" mb="sm">
            Skip these subdomains during crawling
          </Text>
          <Stack gap="xs">
            {form.values.blocked_subdomains.map((subdomain: string, index: number) => (
              <Group key={index} gap="xs">
                <TextInput
                  placeholder="blog.company.com"
                  style={{ flex: 1 }}
                  value={subdomain}
                  onChange={(e) => {
                    const newSubdomains = [...form.values.blocked_subdomains];
                    newSubdomains[index] = e.currentTarget.value;
                    form.setFieldValue('blocked_subdomains', newSubdomains);
                  }}
                />
                <ActionIcon
                  color="red"
                  variant="light"
                  onClick={() => {
                    const newSubdomains = form.values.blocked_subdomains.filter(
                      (_: string, i: number) => i !== index
                    );
                    form.setFieldValue('blocked_subdomains', newSubdomains);
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
                form.setFieldValue('blocked_subdomains', [...form.values.blocked_subdomains, ''])
              }
            >
              Add Subdomain
            </Button>
          </Stack>
        </Paper>

        <Alert icon={<IconInfoCircle size={16} />} color="gray" variant="light">
          ℹ️ Leave both sections empty to crawl all subdomains under the base URL
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
