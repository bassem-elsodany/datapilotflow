/**
 * RAG Pipeline Template Selector
 *
 * Modal for selecting pre-built RAG pipeline templates.
 * Shows template overview and allows customization by selecting optional nodes.
 */

import {
  Modal,
  Button,
  Card,
  Group,
  Stack,
  Text,
  Badge,
  Checkbox,
  Paper,
  Title,
  Divider,
  Grid,
  ThemeIcon,
} from '@mantine/core';
import { IconCheck, IconX, IconChevronRight } from '@tabler/icons-react';
import { useState } from 'react';
import { RAG_TEMPLATES, RagTemplate } from '../templates/ragTemplates';

interface TemplateSelectorProps {
  opened: boolean;
  onClose: () => void;
  onSelectTemplate: (template: RagTemplate, selectedOptionalNodes: string[]) => void;
}

export function TemplateSelector({ opened, onClose, onSelectTemplate }: TemplateSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<RagTemplate | null>(null);
  const [selectedOptionalNodes, setSelectedOptionalNodes] = useState<Set<string>>(new Set());

  const handleTemplateSelect = (template: RagTemplate) => {
    setSelectedTemplate(template);
    setSelectedOptionalNodes(new Set());
  };

  const handleOptionalNodeToggle = (nodeId: string) => {
    const newSelected = new Set(selectedOptionalNodes);
    if (newSelected.has(nodeId)) {
      newSelected.delete(nodeId);
    } else {
      newSelected.add(nodeId);
    }
    setSelectedOptionalNodes(newSelected);
  };

  const handleConfirmTemplate = () => {
    if (selectedTemplate) {
      onSelectTemplate(selectedTemplate, Array.from(selectedOptionalNodes));
      setSelectedTemplate(null);
      setSelectedOptionalNodes(new Set());
      onClose();
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={selectedTemplate ? `Customize: ${selectedTemplate.name}` : 'Select RAG Pipeline Template'}
      size="xl"
      centered
    >
      <Stack gap="lg">
        {!selectedTemplate ? (
          // Template Selection View
          <Stack gap="md">
            <Text size="sm" c="dimmed">
              Choose a pre-built template as a starting point for your RAG pipeline. You can customize it by adding or removing optional nodes.
            </Text>

            <Grid gutter="md">
              {RAG_TEMPLATES.map((template) => (
                <Grid.Col span={{ base: 12, sm: 6 }} key={template.id}>
                  <Card
                    withBorder
                    padding="sm"
                    radius="md"
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      border: '2px solid transparent',
                      height: '100%',
                      '&:hover': {
                        borderColor: '#228be6',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      }
                    }}
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <Stack gap="xs" h="100%">
                      <Group justify="space-between" gap="xs" wrap="nowrap">
                        <Group gap="xs" wrap="nowrap">
                          <Text size="lg">{template.icon}</Text>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <Title order={5} size="h6" style={{ marginBottom: 2 }}>{template.name}</Title>
                            <Text size="xs" c="dimmed" style={{ marginBottom: 0 }}>{template.id}</Text>
                          </div>
                        </Group>
                        <IconChevronRight size={18} style={{ color: '#228be6', flexShrink: 0 }} />
                      </Group>
                      <Text size="xs" style={{ lineHeight: 1.3 }}>{template.description}</Text>
                      <Group gap={4}>
                        <Badge size="xs" color="blue" variant="light">
                          {template.requiredNodes.length} req
                        </Badge>
                        {template.optionalNodes.length > 0 && (
                          <Badge size="xs" color="gray" variant="light">
                            +{template.optionalNodes.length}
                          </Badge>
                        )}
                      </Group>
                    </Stack>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </Stack>
        ) : (
          // Template Customization View
          <Stack gap="md">
            <div>
              <Button
                variant="subtle"
                leftSection={<IconX size={16} />}
                onClick={() => setSelectedTemplate(null)}
                mb="md"
              >
                Back to Templates
              </Button>

              <Title order={3}>{selectedTemplate.name}</Title>
              <Text size="sm" c="dimmed" mt="xs">
                {selectedTemplate.description}
              </Text>
            </div>

            <Divider />

            {/* Required Nodes */}
            <div>
              <Title order={4} size="h6" mb="sm">
                Required Nodes
              </Title>
              <Stack gap="xs">
                {selectedTemplate.requiredNodes.map((node) => (
                  <Paper key={node.id} p="sm" withBorder radius="md" style={{ backgroundColor: '#f9f9f9' }}>
                    <Group justify="space-between">
                      <div style={{ flex: 1 }}>
                        <Text fw={500} size="sm">
                          {node.label}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {node.description}
                        </Text>
                      </div>
                      <ThemeIcon size="sm" color="green" radius="md">
                        <IconCheck size={14} />
                      </ThemeIcon>
                    </Group>
                  </Paper>
                ))}
              </Stack>
            </div>

            {/* Optional Nodes */}
            {selectedTemplate.optionalNodes.length > 0 && (
              <div>
                <Title order={4} size="h6" mb="sm">
                  Optional Nodes
                </Title>
                <Text size="xs" c="dimmed" mb="sm">
                  Select which optional nodes to include in your pipeline
                </Text>
                <Stack gap="xs">
                  {selectedTemplate.optionalNodes.map((node) => (
                    <Paper key={node.id} p="sm" withBorder radius="md">
                      <Group justify="space-between">
                        <div style={{ flex: 1 }}>
                          <Text fw={500} size="sm">
                            {node.label}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {node.description}
                          </Text>
                        </div>
                        <Checkbox
                          checked={selectedOptionalNodes.has(node.id)}
                          onChange={() => handleOptionalNodeToggle(node.id)}
                        />
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </div>
            )}

            <Divider />

            <Group justify="flex-end">
              <Button variant="subtle" onClick={() => setSelectedTemplate(null)}>
                Cancel
              </Button>
              <Button onClick={handleConfirmTemplate} color="blue">
                Use This Template
              </Button>
            </Group>
          </Stack>
        )}
      </Stack>
    </Modal>
  );
}
