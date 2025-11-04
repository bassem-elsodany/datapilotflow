/**
 * Conversation Pipeline Builder
 *
 * Visual graph-based interface for building conversation configurations
 * Allows advanced users to design custom conversation pipelines with full control
 */

import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import {
  Box,
  Button,
  Container,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
  IconCheck,
  IconDatabase,
  IconBrain,
  IconFilter,
  IconMessageCircle,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Apps', href: paths.dashboard.apps.root },
  { label: 'Knowledge Conversations', href: paths.dashboard.apps.conversationCreate },
  { label: 'Pipeline Builder' },
];

// Enhancement strategies
const ENHANCEMENT_STRATEGIES = [
  { value: 'native', label: 'Native RAG' },
  { value: 'augmented', label: 'Augmented (Best Coverage)' },
  { value: 'multi_query', label: 'Multi-Query' },
  { value: 'hyde', label: 'HyDE' },
];

interface ConversationNode {
  id: string;
  type: 'retrieval' | 'reranking' | 'llm' | 'enhancement';
  label: string;
  configured: boolean;
  config?: any;
}

export function ConversationPipelineBuilder() {
  const navigate = useNavigate();
  const { data: providers } = useGetActiveModelProviders();
  const { data: collections } = useGetCollections();

  const [conversationName, setConversationName] = useState('');
  const [nodes, setNodes] = useState<ConversationNode[]>([
    {
      id: '1',
      type: 'enhancement',
      label: 'Query Enhancement',
      configured: false,
      config: { strategy: 'native' },
    },
    {
      id: '2',
      type: 'retrieval',
      label: 'Document Retrieval',
      configured: false,
      config: { collection: null, topK: 5 },
    },
    {
      id: '3',
      type: 'llm',
      label: 'Generative Answer',
      configured: false,
      config: { provider: null, model: null },
    },
  ]);

  // Modal states
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const handleConfigureNode = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    setConfigModalOpen(true);
  };

  const handleSaveNodeConfig = (nodeId: string, config: any) => {
    setNodes(nodes.map(node =>
      node.id === nodeId
        ? { ...node, config, configured: true }
        : node
    ));
    setConfigModalOpen(false);
    setSelectedNodeId(null);
    notifications.show({
      title: 'Node Configured',
      message: `Configuration saved successfully`,
      color: 'green',
      icon: <IconCheck size={16} />,
    });
  };

  const handleBackToWizard = () => {
    navigate(paths.dashboard.apps.conversationCreate);
  };

  const handleSaveConversation = async () => {
    // Validate all nodes are configured
    const unconfiguredNodes = nodes.filter(n => !n.configured);
    if (unconfiguredNodes.length > 0) {
      notifications.show({
        title: 'Incomplete Configuration',
        message: `Please configure all nodes. Unconfigured: ${unconfiguredNodes.map(n => n.label).join(', ')}`,
        color: 'red',
      });
      return;
    }

    // TODO: Send configuration to backend
    notifications.show({
      title: 'Success',
      message: 'Conversation configuration saved!',
      color: 'green',
      icon: <IconCheck size={16} />,
    });

    // Navigate to conversation window
    // navigate(paths.dashboard.apps.conversation(conversationId));
  };

  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  return (
    <Page title="Conversation Pipeline Builder">
      <PageHeader
        title="Conversation Pipeline Builder"
        breadcrumbs={breadcrumbs}
      />

      <Container fluid my="md" style={{ display: 'flex', flexDirection: 'column' }}>
        <Stack gap="md">
          {/* Header */}
          <Paper shadow="sm" p="md">
            <Group justify="space-between" align="flex-end">
              <div>
                <Title order={4}>Configure Your Conversation Pipeline</Title>
                <Text size="sm" c="dimmed" mt="xs">
                  Design a custom conversation pipeline by configuring each component
                </Text>
              </div>
              <Button
                variant="default"
                leftSection={<IconArrowLeft size={16} />}
                onClick={handleBackToWizard}
              >
                Back to Wizard
              </Button>
            </Group>
          </Paper>

          {/* Canvas Area */}
          <Paper
            withBorder
            p="md"
            radius="md"
            style={{
              backgroundColor: '#f8f9fa',
              minHeight: '400px',
              position: 'relative',
            }}
          >
            <Stack gap="md">
              <Text fw={600} size="sm">
                Pipeline Configuration
              </Text>

              {/* Pipeline Nodes Visualization */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '20px',
                }}
              >
                {nodes.map((node, index) => {
                  let icon = IconMessageCircle;
                  let color = 'blue';

                  switch (node.type) {
                    case 'enhancement':
                      icon = IconFilter;
                      color = 'violet';
                      break;
                    case 'retrieval':
                      icon = IconDatabase;
                      color = 'cyan';
                      break;
                    case 'reranking':
                      icon = IconFilter;
                      color = 'orange';
                      break;
                    case 'llm':
                      icon = IconBrain;
                      color = 'green';
                      break;
                  }

                  const NodeIcon = icon;

                  return (
                    <Box key={node.id}>
                      <Paper
                        p="md"
                        radius="md"
                        withBorder
                        style={{
                          borderColor: node.configured
                            ? `var(--mantine-color-${color}-3)`
                            : 'var(--mantine-color-gray-3)',
                          backgroundColor: node.configured
                            ? `var(--mantine-color-${color}-0)`
                            : '#fff',
                          cursor: 'pointer',
                          transition: 'all 0.3s ease',
                        }}
                      >
                        <Group justify="space-between">
                          <Group gap="md">
                            <Box
                              style={{
                                width: 40,
                                height: 40,
                                borderRadius: 8,
                                background: `var(--mantine-color-${color}-1)`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              <NodeIcon size={20} color={`var(--mantine-color-${color}-6)`} />
                            </Box>
                            <div>
                              <Text fw={600} size="sm">
                                {node.label}
                              </Text>
                              <Text size="xs" c="dimmed">
                                {node.configured ? '✓ Configured' : 'Not configured'}
                              </Text>
                            </div>
                          </Group>
                          <Button
                            size="xs"
                            variant="light"
                            onClick={() => handleConfigureNode(node.id)}
                          >
                            {node.configured ? 'Edit' : 'Configure'}
                          </Button>
                        </Group>
                      </Paper>

                      {index < nodes.length - 1 && (
                        <Box
                          style={{
                            height: '20px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--mantine-color-gray-4)',
                          }}
                        >
                          ↓
                        </Box>
                      )}
                    </Box>
                  );
                })}
              </div>

              <Text size="xs" c="dimmed" ta="center">
                {nodes.filter(n => n.configured).length} of {nodes.length} components configured
              </Text>
            </Stack>
          </Paper>

          {/* Action Buttons */}
          <Group justify="flex-end">
            <Button variant="default" onClick={handleBackToWizard}>
              Cancel
            </Button>
            <Button
              color="green"
              leftSection={<IconCheck size={16} />}
              onClick={handleSaveConversation}
            >
              Create Conversation
            </Button>
          </Group>
        </Stack>
      </Container>

      {/* Configuration Modal */}
      {selectedNode && (
        <ConfigurationModal
          node={selectedNode}
          opened={configModalOpen}
          onClose={() => setConfigModalOpen(false)}
          onSave={(config) => handleSaveNodeConfig(selectedNode.id, config)}
          providers={providers || []}
          collections={collections || []}
        />
      )}
    </Page>
  );
}

interface ConfigurationModalProps {
  node: ConversationNode;
  opened: boolean;
  onClose: () => void;
  onSave: (config: any) => void;
  providers: any[];
  collections: any[];
}

function ConfigurationModal({
  node,
  opened,
  onClose,
  onSave,
  providers,
  collections,
}: ConfigurationModalProps) {
  const [formConfig, setFormConfig] = useState(node.config || {});

  const handleSave = () => {
    // Validate required fields based on node type
    if (node.type === 'enhancement' && !formConfig.strategy) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please select an enhancement strategy',
        color: 'red',
      });
      return;
    }

    if (node.type === 'retrieval' && !formConfig.collection) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please select a collection',
        color: 'red',
      });
      return;
    }

    if (node.type === 'llm' && (!formConfig.provider || !formConfig.model)) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please select both provider and model',
        color: 'red',
      });
      return;
    }

    onSave(formConfig);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`Configure: ${node.label}`}
      size="md"
      centered
    >
      <Stack gap="md">
        {/* Enhancement Strategy Configuration */}
        {node.type === 'enhancement' && (
          <>
            <Select
              label="Enhancement Strategy"
              placeholder="Select a strategy"
              data={ENHANCEMENT_STRATEGIES}
              value={formConfig.strategy || null}
              onChange={(value) =>
                setFormConfig({ ...formConfig, strategy: value })
              }
            />
            <Text size="xs" c="dimmed">
              {ENHANCEMENT_STRATEGIES.find(s => s.value === formConfig.strategy)?.label === 'Native RAG'
                ? 'Traditional RAG without query enhancement. Best for simple, well-formed questions.'
                : 'Apply systematic transformations to your query for better coverage.'}
            </Text>
          </>
        )}

        {/* Document Retrieval Configuration */}
        {node.type === 'retrieval' && (
          <>
            <Select
              label="Vector DB Collection"
              placeholder="Select a collection"
              data={(collections || []).map((c: any) => ({ value: c.name, label: c.name }))}
              value={formConfig.collection || null}
              onChange={(value) =>
                setFormConfig({ ...formConfig, collection: value })
              }
            />
            <Select
              label="Top K Results"
              placeholder="Select number of results"
              data={[
                { value: '3', label: '3 results' },
                { value: '5', label: '5 results (default)' },
                { value: '10', label: '10 results' },
                { value: '20', label: '20 results' },
              ]}
              value={(formConfig.topK || 5).toString()}
              onChange={(value) =>
                setFormConfig({ ...formConfig, topK: parseInt(value || '5') })
              }
            />
          </>
        )}

        {/* LLM Configuration */}
        {node.type === 'llm' && (
          <>
            <Select
              label="LLM Provider"
              placeholder="Select a provider"
              data={(providers || []).map((p: any) => ({ value: p.id, label: p.name }))}
              value={formConfig.provider || null}
              onChange={(value) =>
                setFormConfig({ ...formConfig, provider: value })
              }
            />
            {formConfig.provider && (
              <Select
                label="Model"
                placeholder="Select a model"
                data={
                  providers
                    ?.find((p: any) => p.id === formConfig.provider)
                    ?.models?.map((m: any) => ({
                      value: m.name,
                      label: m.name,
                    })) || []
                }
                value={formConfig.model || null}
                onChange={(value) =>
                  setFormConfig({ ...formConfig, model: value })
                }
              />
            )}
          </>
        )}

        {/* Save Button */}
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button color="green" onClick={handleSave}>
            Save Configuration
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
