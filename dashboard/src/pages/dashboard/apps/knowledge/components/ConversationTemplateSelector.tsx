/**
 * Conversation Template Selector
 *
 * Modal for selecting a conversation RAG pipeline template and customizing optional nodes
 */

import {
  Badge,
  Box,
  Button,
  Card,
  Checkbox,
  Divider,
  Group,
  Modal,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { useState } from 'react';
import { CONVERSATION_TEMPLATES, ConversationTemplate } from './conversationTemplates';

interface ConversationTemplateSelectorProps {
  opened: boolean;
  onClose: () => void;
  onSelectTemplate: (template: ConversationTemplate, selectedOptionals: string[]) => void;
}

export function ConversationTemplateSelector({
  opened,
  onClose,
  onSelectTemplate,
}: ConversationTemplateSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<ConversationTemplate | null>(null);
  const [selectedOptionals, setSelectedOptionals] = useState<string[]>([]);

  const handleSelectTemplate = (template: ConversationTemplate) => {
    setSelectedTemplate(template);
    // Pre-select all optional nodes by default
    setSelectedOptionals(template.optionalNodes.map(n => n.id));
  };

  const handleToggleOptional = (nodeId: string) => {
    setSelectedOptionals(prev =>
      prev.includes(nodeId)
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  const handleConfirm = () => {
    if (selectedTemplate) {
      onSelectTemplate(selectedTemplate, selectedOptionals);
      setSelectedTemplate(null);
      setSelectedOptionals([]);
      // Don't call onClose() - let parent handle closing the modal via onSelectTemplate
    }
  };

  const handleCancel = () => {
    setSelectedTemplate(null);
    setSelectedOptionals([]);
    onClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleCancel}
      title="Select Conversation Agent Pipeline Template"
      size="xl"
      centered
    >
      <Stack gap="md">
        {!selectedTemplate ? (
          // Template Selection View
          <>
            <Text size="sm" c="dimmed">
              Choose a pre-built conversation agent pipeline template and customize it by enabling/disabling optional components
            </Text>
            <Stack gap="md">
              {CONVERSATION_TEMPLATES.map(template => {
                const getTemplateColor = (id: string) => {
                  const colors: Record<string, string> = {
                    'basic-rag': '#f0f4ff',
                    'augmented-rag': '#fff4f0',
                    'advanced-rag': '#f0fff4',
                    'decomposition-rag': '#f4f0ff',
                    'hyde-rag': '#fff0f4',
                  };
                  return colors[id] || '#f9f9f9';
                };

                const getTemplateBorderColor = (id: string) => {
                  const colors: Record<string, string> = {
                    'basic-rag': '#4c6ef5',
                    'augmented-rag': '#ff922b',
                    'advanced-rag': '#51cf66',
                    'decomposition-rag': '#9c36b5',
                    'hyde-rag': '#e64980',
                  };
                  return colors[id] || '#ccc';
                };

                const getTemplateDetails = (id: string) => {
                  const details: Record<string, { definition: string; example: string; whenToUse: string }> = {
                    'basic-rag': {
                      definition: 'Direct search without query transformation. Your question goes straight to the vector database.',
                      example: 'User: "What is SSL?"\nSearches for documents containing "SSL" directly.',
                      whenToUse: 'Use when: Questions are clear & well-formed, fast responses needed, simple domains'
                    },
                    'augmented-rag': {
                      definition: 'Transforms query 4 ways (synonym, expanded, contracted, technical) and searches all variants, then merges results using RRF.',
                      example: 'User: "SSL config in Apache"\nSearches: "secure socket layer", "SSL setup", "SSL", "TLS security"\nMerges all results for maximum coverage.',
                      whenToUse: 'Use when: Need maximum coverage, complex domains, varied document styles, critical information needed'
                    },
                    'advanced-rag': {
                      definition: 'Rephrases your question 3-5 ways with different wording and perspectives, searches each variant, merges results using RRF.',
                      example: 'User: "How to configure Salesforce listeners?"\nSearches: "Salesforce event handler setup", "Platform event subscription", "Listener configuration"\nCombines all results.',
                      whenToUse: 'Use when: Documents use varied terminology, need linguistic flexibility, handling different writing styles'
                    },
                    'decomposition-rag': {
                      definition: 'Breaks complex questions into sub-questions, searches for each independently, then synthesizes answers together.',
                      example: 'User: "How do I set up SSL and configure Apache?"\nDecomposes to: "How to set up SSL?" + "How to configure Apache?"\nSearches & combines both.',
                      whenToUse: 'Use when: Questions are multi-part, dealing with complex topics, need comprehensive answers'
                    },
                    'hyde-rag': {
                      definition: 'Generates a hypothetical answer to your question first, then searches for documents similar to that answer.',
                      example: 'User: "How to configure SSL?"\nGenerates: "Create VirtualHost, add SSLEngine on, set certificate paths..."\nSearches for documents similar to this.',
                      whenToUse: 'Use when: Want semantic similarity matching, answer-seeking queries, documents match answer patterns'
                    },
                  };
                  return details[id] || { definition: '', example: '', whenToUse: '' };
                };

                const details = getTemplateDetails(template.id);

                return (
                  <Card
                    key={template.id}
                    p="md"
                    radius="md"
                    withBorder
                    style={{
                      cursor: 'pointer',
                      backgroundColor: getTemplateColor(template.id),
                      borderColor: getTemplateBorderColor(template.id),
                      borderWidth: '2px',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                    onClick={() => handleSelectTemplate(template)}
                  >
                    <Stack gap="md">
                      {/* Header */}
                      <div>
                        <Title order={4} style={{ fontSize: '18px', marginBottom: '4px' }}>
                          {template.icon} {template.name}
                        </Title>
                      </div>

                      {/* Definition */}
                      <div>
                        <Text size="sm" fw={600} mb="xs" c="blue.7">What it does:</Text>
                        <Text size="sm" c="dimmed" style={{ lineHeight: 1.4 }}>
                          {details.definition}
                        </Text>
                      </div>

                      {/* Example */}
                      <div>
                        <Text size="sm" fw={600} mb="xs" c="green.7">Example:</Text>
                        <Box
                          p="xs"
                          bg="white"
                          style={{
                            borderRadius: '4px',
                            border: '1px solid var(--mantine-color-gray-2)',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            lineHeight: '1.4',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            color: '#333'
                          }}
                        >
                          {details.example}
                        </Box>
                      </div>

                      {/* When to Use */}
                      <div>
                        <Text size="sm" fw={600} mb="xs" c="orange.7">When to use:</Text>
                        <Text size="sm" c="dimmed" style={{ lineHeight: 1.4 }}>
                          {details.whenToUse}
                        </Text>
                      </div>

                      <Text size="xs" c="dimmed" ta="center" mt="xs">
                        Click to select this template →
                      </Text>
                    </Stack>
                  </Card>
                );
              })}
            </Stack>
          </>
        ) : (
          // Template Customization View
          <>
            <Group justify="space-between" align="center">
              <div>
                <Title order={4}>
                  {selectedTemplate.icon} {selectedTemplate.name}
                </Title>
                <Text size="sm" c="dimmed">
                  {selectedTemplate.description}
                </Text>
              </div>
              <Button
                variant="default"
                size="sm"
                onClick={() => setSelectedTemplate(null)}
              >
                Change Template
              </Button>
            </Group>

            <Divider />

            <div>
              <Title order={5}>Conversation Agent Pipeline Configuration</Title>
              <Stack gap="sm" mt="md">
                {selectedTemplate.requiredNodes
                  .filter(node => node.id !== 'config') // Exclude Conversation Settings
                  .map(node => (
                    <Card key={node.id} p="sm" withBorder>
                      <Group justify="space-between">
                        <div>
                          <Text fw={500}>{node.name}</Text>
                          <Text size="sm" c="dimmed">{node.description}</Text>
                        </div>
                        <Badge color="blue">Required</Badge>
                      </Group>
                    </Card>
                  ))}
              </Stack>
            </div>

            {selectedTemplate.optionalNodes.length > 0 && (
              <div>
                <Title order={5}>Optional Components</Title>
                <Text size="sm" c="dimmed" mb="md">
                  Select which optional components to include
                </Text>
                <Stack gap="sm">
                  {selectedTemplate.optionalNodes.map(node => (
                    <Card
                      key={node.id}
                      p="sm"
                      withBorder
                      style={{
                        borderColor: selectedOptionals.includes(node.id) ? 'var(--mantine-color-blue-6)' : undefined,
                        backgroundColor: selectedOptionals.includes(node.id) ? 'var(--mantine-color-blue-0)' : undefined,
                      }}
                    >
                      <Group justify="space-between">
                        <div>
                          <Text fw={500}>{node.name}</Text>
                          <Text size="sm" c="dimmed">{node.description}</Text>
                        </div>
                        <Checkbox
                          checked={selectedOptionals.includes(node.id)}
                          onChange={() => handleToggleOptional(node.id)}
                          aria-label={`Toggle ${node.name}`}
                        />
                      </Group>
                    </Card>
                  ))}
                </Stack>
              </div>
            )}

            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={handleCancel}>
                Cancel
              </Button>
              <Button color="blue" onClick={handleConfirm}>
                Use This Template
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>
  );
}
