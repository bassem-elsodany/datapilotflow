import { client } from '@/api/axios';
import { ModelProviderResponse, useGetModelProviders, useUpdateModelProvider } from '@/api/resources/model-providers';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Switch,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconBrain,
  IconBrandGoogle,
  IconBrandOpenai,
  IconDatabase,
  IconEdit,
  IconFilter,
  IconKey,
  IconPlus,
  IconRefresh,
  IconRobot,
  IconServer,
  IconSettings,
  IconToggleLeft,
  IconToggleRight
} from '@tabler/icons-react';
import sortBy from 'lodash/sortBy';
import { DataTable, DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Model Providers' },
];

const getProviderIcon = (providerType: string) => {
  switch (providerType.toLowerCase()) {
    case 'openai':
      return <IconBrandOpenai size={16} />;
    case 'anthropic':
      return <IconBrain size={16} />;
    case 'google':
      return <IconBrandGoogle size={16} />;
    case 'ollama':
      return <IconServer size={16} />;
    case 'huggingface':
      return <IconBrain size={16} />;
    case 'groq':
      return <IconServer size={16} />;
    case 'cohere':
      return <IconFilter size={16} />;
    case 'voyage':
      return <IconFilter size={16} />;
    default:
      return <IconDatabase size={16} />;
  }
};

const getModelTypeBadge = (provider: ModelProviderResponse) => {
  const badges = [];

  if (provider.embedding) {
    badges.push(<Badge key="embedding" color="green" size="sm">Embedding</Badge>);
  }
  if (provider.generative) {
    badges.push(<Badge key="generative" color="purple" size="sm">Generative</Badge>);
  }
  if (provider.reranker) {
    badges.push(<Badge key="reranker" color="orange" size="sm">Reranker</Badge>);
  }

  if (badges.length === 0) {
    return <Badge color="gray" size="sm">Unknown</Badge>;
  }

  return badges;
};

export default function ModelProviders() {
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({
    columnAccessor: 'name',
    direction: 'asc',
  });
  const [records, setRecords] = useState<ModelProviderResponse[]>([]);
  const [selectedRecords, setSelectedRecords] = useState<ModelProviderResponse[]>([]);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<ModelProviderResponse | null>(null);
  const navigate = useNavigate();

  // API hooks
  const { data: providers, isLoading, error, refetch, isFetching, isError } = useGetModelProviders();

  // Debug logging
  console.log('Model Providers Query State:', {
    providers,
    isLoading,
    isFetching,
    isError,
    error,
    dataLength: providers?.length || 0
  });
  console.log('JWT Token:', localStorage.getItem('jwt_token'));
  const updateProviderMutation = useUpdateModelProvider(selectedProvider?.id || '');

  // Form for editing
  const editForm = useForm({
    initialValues: {
      name: '',
      provider_type: '',
      endpoint: '',
      api_key: '',
      description: '',
      is_active: true,
      timeout: 60,
      embedding: {
        models: [] as string[],
        config: {} as Record<string, any>,
      },
      generative: {
        models: [] as string[],
        config: {} as Record<string, any>,
      },
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      provider_type: (value) => (!value ? 'Provider type is required' : null),
      endpoint: (value) => (!value ? 'Endpoint is required' : null),
      api_key: (value) => (!value ? 'API key is required' : null),
      timeout: (value) => (value < 1 || value > 300 ? 'Timeout must be between 1 and 300 seconds' : null),
    },
  });

  // Update records when data changes
  useEffect(() => {
    if (providers && Array.isArray(providers)) {
      setRecords(providers);
    } else {
      setRecords([]);
    }
  }, [providers]);

  // Sort records when needed
  const sortedRecords = useMemo(() => {
    if (records.length === 0) return records;
    const data = sortBy(records, sortStatus.columnAccessor);
    return sortStatus.direction === 'desc' ? data.reverse() : data;
  }, [records, sortStatus]);

  const handleEdit = (provider: ModelProviderResponse) => {
    setSelectedProvider(provider);
    editForm.setValues({
      name: provider.name,
      provider_type: provider.provider_type,
      endpoint: provider.endpoint,
      api_key: '••••••••••••••••',
      description: provider.description || '',
      is_active: provider.is_active,
      timeout: provider.timeout,
      embedding: provider.embedding || { models: [], config: {} },
      generative: provider.generative || { models: [], config: {} },
      reranker: provider.reranker || { models: [], config: {} },
    });
    setEditModalOpen(true);
  };

  const handleViewDetails = (provider: ModelProviderResponse) => {
    setSelectedProvider(provider);
    setDetailsModalOpen(true);
  };

  const handleToggleActive = async (provider: ModelProviderResponse) => {
    try {
      await client.put(`/model-providers/${provider.id}`, {
        name: provider.name,
        provider_type: provider.provider_type,
        endpoint: provider.endpoint,
        description: provider.description,
        timeout: provider.timeout,
        embedding: provider.embedding,
        generative: provider.generative,
        reranker: provider.reranker,
        is_active: !provider.is_active
      });
      notifications.show({
        title: 'Success',
        message: `Model provider ${!provider.is_active ? 'activated' : 'deactivated'} successfully`,
        color: 'green',
      });
      refetch();
    } catch (error) {
      console.error('Toggle error:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to update model provider status',
        color: 'red',
      });
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedProvider || !editForm.validate().hasErrors) {
      try {
        await updateProviderMutation.mutateAsync({ variables: editForm.values });
        notifications.show({
          title: 'Success',
          message: 'Model provider updated successfully',
          color: 'green',
        });
        setEditModalOpen(false);
        refetch();
      } catch (error) {
        notifications.show({
          title: 'Error',
          message: 'Failed to update model provider',
          color: 'red',
        });
      }
    }
  };


  const columns: DataTableColumn<ModelProviderResponse>[] = useMemo(() => [
    {
      accessor: 'name',
      title: 'Provider',
      sortable: true,
      render: (provider) => (
        <Group gap="sm">
          {getProviderIcon(provider.provider_type)}
          <div>
            <Text fw={500}>{provider.name}</Text>
            <Text size="xs" c="dimmed">{provider.provider_type}</Text>
          </div>
        </Group>
      ),
    },
    {
      accessor: 'model_types',
      title: 'Model Types',
      render: (provider) => (
        <Group gap="xs">
          {getModelTypeBadge(provider)}
        </Group>
      ),
    },
    {
      accessor: 'embedding_models',
      title: 'Embedding Models',
      render: (provider) => (
        <Stack gap="xs">
          <Text size="sm" fw={500}>{provider.embedding?.models.length || 0} models</Text>
          {provider.embedding && (
            <Stack gap={4}>
              <Text size="xs" c="dimmed">
                Max tokens: {provider.embedding.config?.max_input_tokens || 'N/A'}
              </Text>
              <Text size="xs" c="dimmed">
                Batch size: {provider.embedding.config?.batch_size || 'N/A'}
              </Text>
            </Stack>
          )}
        </Stack>
      ),
    },
    {
      accessor: 'generative_models',
      title: 'Generative Models',
      render: (provider) => (
        <Stack gap="xs">
          <Text size="sm" fw={500}>{provider.generative?.models.length || 0} models</Text>
          {provider.generative && (
            <Stack gap={4}>
              <Text size="xs" c="dimmed">
                Max tokens: {provider.generative.config?.max_tokens || 'N/A'}
              </Text>
              <Text size="xs" c="dimmed">
                Temperature: {provider.generative.config?.temperature || 'N/A'}
              </Text>
              <Text size="xs" c="dimmed">
                Top P: {provider.generative.config?.top_p || 'N/A'}
              </Text>
            </Stack>
          )}
        </Stack>
      ),
    },
    {
      accessor: 'reranker_models',
      title: 'Reranker Models',
      render: (provider) => (
        <Stack gap="xs">
          <Text size="sm" fw={500}>{provider.reranker?.models.length || 0} models</Text>
          {provider.reranker && (
            <Stack gap={4}>
              <Text size="xs" c="dimmed">
                Max docs: {provider.reranker.config?.max_documents || 'N/A'}
              </Text>
              <Text size="xs" c="dimmed">
                Top N: {provider.reranker.config?.top_n || 'N/A'}
              </Text>
            </Stack>
          )}
        </Stack>
      ),
    },
    {
      accessor: 'is_active',
      title: 'Status',
      render: (provider) => (
        <Badge color={provider.is_active ? 'green' : 'red'} size="sm">
          {provider.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      accessor: 'actions',
      title: 'Actions',
      textAlign: 'right',
      render: (provider) => (
        <Group gap="xs" justify="flex-end">
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={() => handleViewDetails(provider)}
            title="View Details"
          >
            <IconSettings size={16} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color={provider.is_active ? "green" : "gray"}
            onClick={() => handleToggleActive(provider)}
            title={provider.is_active ? "Deactivate" : "Activate"}
          >
            {provider.is_active ? <IconToggleRight size={16} /> : <IconToggleLeft size={16} />}
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => handleEdit(provider)}
            title="Edit"
          >
            <IconEdit size={16} />
          </ActionIcon>
        </Group>
      ),
    },
  ], []);


  if (isLoading || isFetching) {
    return (
      <Page title="Model Providers">
        <PageHeader title="Model Providers" breadcrumbs={breadcrumbs} />
        <Center h={200}>
          <Stack align="center" gap="md">
            <Loader size="lg" />
            <Text size="sm" c="dimmed">
              {isLoading ? 'Loading model providers...' : 'Fetching model providers...'}
            </Text>
          </Stack>
        </Center>
      </Page>
    );
  }

  if (error || isError) {
    return (
      <Page title="Model Providers">
        <PageHeader title="Model Providers" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error Loading Model Providers">
          <Stack gap="sm">
            <Text>Failed to load model providers. Please check your authentication and try again.</Text>
            <Text size="sm" c="dimmed">
              Error: {error?.message || 'Unknown error occurred'}
            </Text>
            <Button
              variant="light"
              size="sm"
              onClick={() => refetch()}
              leftSection={<IconRefresh size={16} />}
            >
              Retry
            </Button>
          </Stack>
        </Alert>
      </Page>
    );
  }

  // Don't render DataTable if we don't have valid data
  if (!providers || !Array.isArray(providers)) {
    return (
      <Page title="Model Providers">
        <PageHeader title="Model Providers" breadcrumbs={breadcrumbs} />
        <Alert color="yellow" title="No Data">
          <Stack gap="sm">
            <Text>No model providers found or data is not in the expected format.</Text>
            <Text size="sm" c="dimmed">
              Providers: {providers ? 'Not an array' : 'Undefined'}
            </Text>
            <Button
              variant="light"
              size="sm"
              onClick={() => refetch()}
              leftSection={<IconRefresh size={16} />}
            >
              Refresh
            </Button>
          </Stack>
        </Alert>
      </Page>
    );
  }

  return (
    <Page title="Model Providers">
      <PageHeader
        title="Model Providers"
        breadcrumbs={breadcrumbs}
      >
        <Group>
          <Button
            variant="light"
            leftSection={<IconRefresh size={16} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => navigate(paths.dashboard.management.modelProviders.providerCreate)}
          >
            Add Provider
          </Button>
        </Group>
      </PageHeader>

      <Card mb="md">
        <Stack gap="sm">
          <Text size="sm" c="dimmed">
            Configure AI model providers to power your embedding and generative AI capabilities.
            Set up API keys and endpoints for different providers to enable content processing,
            vector embeddings, and AI-powered responses.
          </Text>
          <Group gap="xs">
            <IconBrain size={16} color="var(--mantine-color-blue-6)" />
            <Text size="sm" fw={500}>Model Types:</Text>
            <Text size="sm" c="dimmed">Embedding models for vector search, Generative models for AI responses</Text>
          </Group>
          <Group gap="xs">
            <IconKey size={16} color="var(--mantine-color-green-6)" />
            <Text size="sm" fw={500}>Supported Providers:</Text>
            <Text size="sm" c="dimmed">OpenAI, Anthropic, Google, Ollama, Hugging Face, Groq</Text>
          </Group>
          <Group gap="xs">
            <IconSettings size={16} color="var(--mantine-color-orange-6)" />
            <Text size="sm" fw={500}>Configuration:</Text>
            <Text size="sm" c="dimmed">API keys, endpoints, model selection, and provider-specific settings</Text>
          </Group>
        </Stack>
      </Card>

      <Card>
        <DataTable
          columns={columns as any}
          records={Array.isArray(sortedRecords) ? sortedRecords : []}
          selectedRecords={Array.isArray(selectedRecords) ? selectedRecords : []}
          onSelectedRecordsChange={setSelectedRecords as any}
          sortStatus={sortStatus}
          onSortStatusChange={setSortStatus}
          minHeight={200}
          striped
          highlightOnHover
        />
      </Card>

      {/* Edit Modal */}
      <Modal
        opened={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title={
          <Group gap="sm">
            <IconEdit size={20} />
            <Text fw={600} size="lg">Edit Model Provider</Text>
          </Group>
        }
        size="lg"
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-blue-0)',
            borderBottom: '1px solid var(--mantine-color-blue-2)',
            padding: 'var(--mantine-spacing-md)',
          },
          title: {
            color: 'var(--mantine-color-blue-8)',
          }
        }}
      >
        <form onSubmit={editForm.onSubmit(handleSaveEdit)}>
          <Stack gap="md">
            <SimpleGrid cols={2}>
              <TextInput
                label="Name"
                placeholder="Provider name"
                readOnly
                {...editForm.getInputProps('name')}
              />
              <TextInput
                label="Provider Type"
                placeholder="e.g., openai, anthropic"
                readOnly
                {...editForm.getInputProps('provider_type')}
              />
            </SimpleGrid>

            <TextInput
              label="Endpoint"
              placeholder="https://api.example.com/v1"
              {...editForm.getInputProps('endpoint')}
            />

            <TextInput
              label="API Key"
              type="password"
              placeholder="Your API key"
              {...editForm.getInputProps('api_key')}
            />

            <SimpleGrid cols={2}>
              <Textarea
                label="Description"
                placeholder="Provider description"
                readOnly
                {...editForm.getInputProps('description')}
              />
              <TextInput
                label="Timeout (seconds)"
                type="number"
                min={1}
                max={300}
                {...editForm.getInputProps('timeout')}
              />
            </SimpleGrid>

            {/* Embedding Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md">
                <IconBrain size={18} color="var(--mantine-color-green-6)" />
                <Title order={6} c="green.8">Embedding Models</Title>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add embedding models"
                {...editForm.getInputProps('embedding.models')}
              />
              {editForm.values.embedding && editForm.values.embedding.models.length > 0 && (
                <>
                  <SimpleGrid cols={2} mt="md">
                    <TextInput
                      label="Max Input Tokens"
                      type="number"
                      placeholder="8191"
                      {...editForm.getInputProps('embedding.config.max_input_tokens')}
                    />
                    <TextInput
                      label="Batch Size"
                      type="number"
                      placeholder="100"
                      {...editForm.getInputProps('embedding.config.batch_size')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/embeddings"
                    mt="md"
                    {...editForm.getInputProps('embedding.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            {/* Generative Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md">
                <IconRobot size={18} color="var(--mantine-color-purple-6)" />
                <Title order={6} c="purple.8">Generative Models</Title>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add generative models"
                {...editForm.getInputProps('generative.models')}
              />
              {editForm.values.generative && editForm.values.generative.models.length > 0 && (
                <>
                  <SimpleGrid cols={3} mt="md">
                    <TextInput
                      label="Max Tokens"
                      type="number"
                      placeholder="4096"
                      {...editForm.getInputProps('generative.config.max_tokens')}
                    />
                    <TextInput
                      label="Temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      placeholder="0.7"
                      {...editForm.getInputProps('generative.config.temperature')}
                    />
                    <TextInput
                      label="Top P"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      placeholder="1.0"
                      {...editForm.getInputProps('generative.config.top_p')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/chat/completions"
                    mt="md"
                    {...editForm.getInputProps('generative.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            {/* Reranker Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md">
                <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                <Title order={6} c="orange.8">Reranker Models</Title>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add reranker models"
                {...editForm.getInputProps('reranker.models')}
              />
              {editForm.values.reranker && editForm.values.reranker.models.length > 0 && (
                <>
                  <SimpleGrid cols={2} mt="md">
                    <TextInput
                      label="Max Documents"
                      type="number"
                      placeholder="100"
                      {...editForm.getInputProps('reranker.config.max_documents')}
                    />
                    <TextInput
                      label="Top N"
                      type="number"
                      placeholder="10"
                      {...editForm.getInputProps('reranker.config.top_n')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/rerank"
                    mt="md"
                    {...editForm.getInputProps('reranker.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            <Switch
              label="Active"
              {...editForm.getInputProps('is_active', { type: 'checkbox' })}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={() => setEditModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={updateProviderMutation.isPending}>
                Save Changes
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Details Modal */}
      <Modal
        opened={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title={
          <Group gap="sm">
            <IconSettings size={20} />
            <Text fw={600} size="lg">Model Provider Details</Text>
          </Group>
        }
        size="lg"
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-green-0)',
            borderBottom: '1px solid var(--mantine-color-green-2)',
            padding: 'var(--mantine-spacing-md)',
          },
          title: {
            color: 'var(--mantine-color-green-8)',
          }
        }}
      >
        {selectedProvider && (
          <Stack gap="md">
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md">
                <IconDatabase size={18} color="var(--mantine-color-blue-6)" />
                <Title order={5} c="blue.8">Basic Information</Title>
              </Group>
              <SimpleGrid cols={2}>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Name</Text>
                  <Text>{selectedProvider.name}</Text>
                </div>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Type</Text>
                  <Text>{selectedProvider.provider_type}</Text>
                </div>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Endpoint</Text>
                  <Text>{selectedProvider.endpoint}</Text>
                </div>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Timeout</Text>
                  <Text>{selectedProvider.timeout} seconds</Text>
                </div>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Status</Text>
                  <Badge color={selectedProvider.is_active ? 'green' : 'red'} size="sm">
                    {selectedProvider.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </SimpleGrid>
              {selectedProvider.description && (
                <div>
                  <Text size="sm" fw={500} c="dimmed" mt="md">Description</Text>
                  <Text>{selectedProvider.description}</Text>
                </div>
              )}
            </Card>

            {selectedProvider.embedding && (
              <Card withBorder p="md" shadow="sm">
                <Group gap="sm" mb="md">
                  <IconBrain size={18} color="var(--mantine-color-green-6)" />
                  <Title order={5} c="green.8">Embedding Configuration</Title>
                </Group>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Models ({selectedProvider.embedding.models.length})</Text>
                  <Group gap="xs" mt="xs">
                    {selectedProvider.embedding.models.map((model, index) => (
                      <Badge key={index} variant="light" size="sm">{model}</Badge>
                    ))}
                  </Group>
                </div>
                <SimpleGrid cols={2} mt="md">
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Max Input Tokens</Text>
                    <Text>{selectedProvider.embedding.config?.max_input_tokens || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Batch Size</Text>
                    <Text>{selectedProvider.embedding.config?.batch_size || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Endpoint Suffix</Text>
                    <Text>{selectedProvider.embedding.config?.endpoint_suffix || 'N/A'}</Text>
                  </div>
                </SimpleGrid>
              </Card>
            )}

            {selectedProvider.generative && (
              <Card withBorder p="md" shadow="sm">
                <Group gap="sm" mb="md">
                  <IconRobot size={18} color="var(--mantine-color-purple-6)" />
                  <Title order={5} c="purple.8">Generative Configuration</Title>
                </Group>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Models ({selectedProvider.generative.models.length})</Text>
                  <Group gap="xs" mt="xs">
                    {selectedProvider.generative.models.map((model, index) => (
                      <Badge key={index} variant="light" size="sm">{model}</Badge>
                    ))}
                  </Group>
                </div>
                <SimpleGrid cols={2} mt="md">
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Max Tokens</Text>
                    <Text>{selectedProvider.generative.config?.max_tokens || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Temperature</Text>
                    <Text>{selectedProvider.generative.config?.temperature || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Top P</Text>
                    <Text>{selectedProvider.generative.config?.top_p || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Endpoint Suffix</Text>
                    <Text>{selectedProvider.generative.config?.endpoint_suffix || 'N/A'}</Text>
                  </div>
                </SimpleGrid>
              </Card>
            )}

            {selectedProvider.reranker && (
              <Card withBorder p="md" shadow="sm">
                <Group gap="sm" mb="md">
                  <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                  <Title order={5} c="orange.8">Reranker Configuration</Title>
                </Group>
                <div>
                  <Text size="sm" fw={500} c="dimmed">Models ({selectedProvider.reranker.models.length})</Text>
                  <Group gap="xs" mt="xs">
                    {selectedProvider.reranker.models.map((model, index) => (
                      <Badge key={index} variant="light" color="orange" size="sm">{model}</Badge>
                    ))}
                  </Group>
                </div>
                <SimpleGrid cols={2} mt="md">
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Max Documents</Text>
                    <Text>{selectedProvider.reranker.config?.max_documents || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Top N</Text>
                    <Text>{selectedProvider.reranker.config?.top_n || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500} c="dimmed">Endpoint Suffix</Text>
                    <Text>{selectedProvider.reranker.config?.endpoint_suffix || 'N/A'}</Text>
                  </div>
                </SimpleGrid>
              </Card>
            )}

            <Group justify="flex-end">
              <Button variant="light" onClick={() => setDetailsModalOpen(false)}>
                Close
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>

    </Page>
  );
}
