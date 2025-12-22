import { client } from '@/api/axios';
import { ModelProviderResponse, useCreateModelProvider, useDeleteModelProvider, useGetModelProviders, useTestModelProvider, useUpdateModelProvider } from '@/api/resources/model-providers';
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
  Divider,
  Group,
  Loader,
  Modal,
  Select,
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
  IconPlayerPlay,
  IconPlus,
  IconRefresh,
  IconRobot,
  IconServer,
  IconSettings,
  IconToggleLeft,
  IconToggleRight,
  IconTrash
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

// Helper function to mask API key for display
const maskApiKey = (key: string | null | undefined): string => {
  if (!key) return '';
  if (key.length <= 8) return key;
  return key.substring(0, 8) + '•'.repeat(Math.min(key.length - 8, 20));
};

export default function ModelProviders() {
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({
    columnAccessor: 'name',
    direction: 'asc',
  });
  const [records, setRecords] = useState<ModelProviderResponse[]>([]);
  const [selectedRecords, setSelectedRecords] = useState<ModelProviderResponse[]>([]);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<ModelProviderResponse | null>(null);
  const [isEditingApiKey, setIsEditingApiKey] = useState(false);
  const [originalApiKey, setOriginalApiKey] = useState<string>('');
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
  const createProviderMutation = useCreateModelProvider();
  const testProviderMutation = useTestModelProvider();
  const deleteProviderMutation = useDeleteModelProvider(selectedProvider?.id || '');

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
      reranker: {
        models: [] as string[],
        config: {} as Record<string, any>,
      },
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      provider_type: (value) => (!value ? 'Provider type is required' : null),
      // Endpoint is optional - only required if using custom URL
      api_key: (value) => (!value ? 'API key is required' : null),
      timeout: (value) => (value < 1 || value > 300 ? 'Timeout must be between 1 and 300 seconds' : null),
    },
  });

  // Form for creating
  const createForm = useForm({
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
      reranker: {
        models: [] as string[],
        config: {} as Record<string, any>,
      },
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      provider_type: (value) => (!value ? 'Provider type is required' : null),
      endpoint: (value) => (!value ? 'Endpoint is required' : null),
      timeout: (value) => (value < 1 || value > 300 ? 'Timeout must be between 1 and 300 seconds' : null),
    },
  });
  const parseJsonField = (value: string, label: string): Record<string, any> | undefined => {
    if (value && typeof value === 'string' && value.trim()) {
      try {
        return JSON.parse(value);
      } catch (e) {
        notifications.show({
          title: 'Error',
          message: `Invalid JSON format for ${label}`,
          color: 'red',
        });
        throw new Error(`Invalid ${label}`);
      }
    }
    return undefined;
  };

  const buildProviderPayload = (values: typeof createForm.values) => {
    return {
      name: values.name,
      provider_type: values.provider_type,
      provider_category: 'custom' as const,
      endpoint: values.endpoint,
      api_key: values.api_key || undefined,
      description: values.description || undefined,
      is_active: values.is_active,
      timeout: values.timeout,
      embedding: values.embedding.models.length > 0 ? {
        models: values.embedding.models,
        config: values.embedding.config,
      } : undefined,
      generative: values.generative.models.length > 0 ? {
        models: values.generative.models,
        config: values.generative.config,
      } : undefined,
      reranker: values.reranker.models.length > 0 ? {
        models: values.reranker.models,
        config: values.reranker.config,
      } : undefined,
    };
  };


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
    setOriginalApiKey(provider.api_key || '');
    setIsEditingApiKey(false);
    editForm.setValues({
      name: provider.name,
      provider_type: provider.provider_type,
      endpoint: provider.endpoint,
      api_key: provider.api_key || '',
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

  const handleCreate = () => {
    createForm.reset();
    setCreateModalOpen(true);
  };

  const handleSaveCreate = async (values: typeof createForm.values) => {
    try {
      const payload = buildProviderPayload(values);
      await createProviderMutation.mutateAsync(payload as any);
      notifications.show({
        title: 'Success',
        message: 'Model provider created successfully',
        color: 'green',
      });
      setCreateModalOpen(false);
      createForm.reset();
      refetch();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error?.message || 'Failed to create model provider',
        color: 'red',
      });
    }
  };


  const handleDelete = (provider: ModelProviderResponse) => {
    setSelectedProvider(provider);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedProvider) return;

    try {
      await deleteProviderMutation.mutateAsync({ model: selectedProvider as any, route: { providerId: selectedProvider.id } });
      notifications.show({
        title: 'Success',
        message: `Model provider "${selectedProvider.name}" deleted successfully`,
        color: 'green',
      });
      setDeleteModalOpen(false);
      setSelectedProvider(null);
      refetch();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error?.message || 'Failed to delete model provider',
        color: 'red',
      });
    }
  };

  const handleTestProvider = async (type: 'embedding' | 'generative' | 'reranker') => {
    try {
      const payload = buildProviderPayload(createForm.values);
      const models = type === 'embedding'
        ? payload.embedding?.models
        : type === 'generative'
          ? payload.generative?.models
          : payload.reranker?.models;

      if (!models || models.length === 0) {
        notifications.show({
          title: 'Missing model',
          message: `Add at least one ${type} model to test`,
          color: 'red',
        });
        return;
      }

      const modelName = models[0];
      const result = await testProviderMutation.mutateAsync({
        variables: {
          provider: payload as any,
          test_type: type,
          model: modelName,
        },
      } as any);

      const success = Boolean(result?.success);
      notifications.show({
        title: success ? `${type} test succeeded` : `${type} test failed`,
        message: success
          ? `Status ${result.status_code ?? ''} in ${result.duration_ms ?? 0}ms`
          : result?.message || 'Test failed',
        color: success ? 'green' : 'red',
      });
    } catch (error: any) {
      // Extract detailed error message from API response
      let errorMessage = 'Failed to test provider';
      
      if (error?.response?.data?.detail) {
        // FastAPI standard error format
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (error?.detail) {
        errorMessage = error.detail;
      }

      notifications.show({
        title: 'Error',
        message: errorMessage,
        color: 'red',
      });
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
            onClick={() => navigate(paths.dashboard.management.modelProviders.providerEdit(provider.id))}
            title="Edit"
          >
            <IconEdit size={16} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color="red"
            onClick={() => handleDelete(provider)}
            title="Delete"
          >
            <IconTrash size={16} />
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
            Configure AI model providers to power embeddings, rerankers, and generative models. Set up API keys and endpoints to enable vector search, reranking, and AI responses across your apps.
          </Text>
          <Group gap="xs">
            <IconBrain size={16} color="var(--mantine-color-blue-6)" />
            <Text size="sm" fw={500}>Model Types:</Text>
            <Text size="sm" c="dimmed">Embedding models for vector search, Reranker models for relevance ordering, Generative models for AI responses.</Text>
          </Group>
          <Group gap="xs">
            <IconKey size={16} color="var(--mantine-color-green-6)" />
            <Text size="sm" fw={500}>Supported Providers:</Text>
            <Text size="sm" c="dimmed">OpenAI-compatible providers (e.g., OpenAI, Azure, OpenRouter, Groq, Fireworks, Together, Perplexity, DeepInfra, Cohere, AI21, Anthropic-compatible, Google-compatible, and other OpenAI-format providers).</Text>
          </Group>
          <Group gap="xs">
            <IconSettings size={16} color="var(--mantine-color-orange-6)" />
            <Text size="sm" fw={500}>Configuration:</Text>
            <Text size="sm" c="dimmed">API keys, endpoints, and model lists for embedding / reranker / generative types. Test models before saving to verify connectivity.</Text>
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
                description="Display name shown in the provider list."
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

            <div>
              <TextInput
                label="API Key"
                placeholder="Your API key"
                value={isEditingApiKey ? editForm.values.api_key : maskApiKey(editForm.values.api_key)}
                onChange={(e) => {
                  if (!isEditingApiKey) {
                    setIsEditingApiKey(true);
                    editForm.setFieldValue('api_key', '');
                  } else {
                    editForm.setFieldValue('api_key', e.currentTarget.value);
                  }
                }}
                onFocus={() => {
                  if (!isEditingApiKey) {
                    setIsEditingApiKey(true);
                    editForm.setFieldValue('api_key', '');
                  }
                }}
                rightSection={
                  isEditingApiKey && (
                    <Button
                      size="xs"
                      variant="subtle"
                      onClick={() => {
                        setIsEditingApiKey(false);
                        editForm.setFieldValue('api_key', originalApiKey);
                      }}
                    >
                      Cancel
                    </Button>
                  )
                }
              />
              {!isEditingApiKey && (
                <Text size="xs" c="dimmed" mt={4}>
                  Click to change API key
                </Text>
              )}
            </div>

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
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconBrain size={18} color="var(--mantine-color-green-6)" />
                  <Title order={6} c="green.8">Embedding Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('embedding')}
                  loading={testProviderMutation.isPending}
                >
                  Test embedding
                </Button>
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
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconRobot size={18} color="var(--mantine-color-purple-6)" />
                  <Title order={6} c="purple.8">Generative Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('generative')}
                  loading={testProviderMutation.isPending}
                >
                  Test generative
                </Button>
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
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                  <Title order={6} c="orange.8">Reranker Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('reranker')}
                  loading={testProviderMutation.isPending}
                >
                  Test reranker
                </Button>
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

      {/* Create Modal */}
      <Modal
        opened={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          createForm.reset();
        }}
        title={
          <Group gap="sm">
            <IconPlus size={20} />
            <Text fw={600} size="lg">Create Model Provider</Text>
          </Group>
        }
        size="xl"
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
        <form onSubmit={createForm.onSubmit(handleSaveCreate)}>
          <Stack gap="md">
            <Alert color="blue" title="Create Custom Provider">
              Configure a custom model provider for OpenAI-compatible APIs. All fields marked with * are required.
              <Text size="sm" mt="xs">
                <strong>Note:</strong> Custom providers must use OpenAI-compatible API formats.
                See <a href="https://docs.litellm.ai/docs/providers" target="_blank" rel="noopener noreferrer">LiteLLM Providers Documentation</a> for details.
              </Text>
            </Alert>

            <SimpleGrid cols={2}>
              <TextInput
                label="Name"
                placeholder="Provider name"
                description="Display name shown in the provider list."
                required
                {...createForm.getInputProps('name')}
              />
              <Select
                label="Provider Type"
                placeholder="Select OpenAI-compatible provider type"
                description="Choose from LiteLLM-supported OpenAI-compatible providers"
                required
                data={[
                  { value: 'openai', label: 'OpenAI' },
                  { value: 'azure', label: 'Azure OpenAI' },
                  { value: 'azure_ai', label: 'Azure AI' },
                  { value: 'openrouter', label: 'OpenRouter' },
                  { value: 'fireworks_ai', label: 'Fireworks AI' },
                  { value: 'groq', label: 'Groq' },
                  { value: 'together_ai', label: 'Together AI' },
                  { value: 'perplexity', label: 'Perplexity AI' },
                  { value: 'anyscale', label: 'Anyscale' },
                  { value: 'deepinfra', label: 'DeepInfra' },
                  { value: 'hyperbolic', label: 'Hyperbolic' },
                  { value: 'nscale', label: 'Nscale (EU Sovereign)' },
                  { value: 'codestral', label: 'Codestral (Mistral AI)' },
                  { value: 'datarobot', label: 'DataRobot' },
                  { value: 'predibase', label: 'Predibase' },
                  { value: 'cohere', label: 'Cohere' },
                  { value: 'ai21', label: 'AI21' },
                  { value: 'bedrock', label: 'AWS Bedrock (compat)' },
                  { value: 'vertex_ai', label: 'Vertex AI (compat)' },
                  { value: 'google_ai_studio', label: 'Google AI Studio' },
                  { value: 'gcp_vertex', label: 'GCP Vertex (compat)' },
                  { value: 'snowflake', label: 'Snowflake Cortex (compat)' },
                  { value: 'qwen_dashscope', label: 'Qwen Dashscope (compat)' },
                  { value: 'voyage', label: 'Voyage AI' },
                  { value: 'replicate', label: 'Replicate (compat)' },
                  { value: 'deepseek', label: 'DeepSeek (compat)' },
                  { value: 'sambanova', label: 'SambaNova (compat)' },
                  { value: 'xai', label: 'xAI (compat)' },
                  { value: 'openai_compatible', label: 'OpenAI Compatible (Generic)' },
                ]}
                searchable
                {...createForm.getInputProps('provider_type')}
              />
            </SimpleGrid>

            <TextInput
              label="Endpoint"
              placeholder="https://api.example.com/v1"
              description="Base API URL for the provider endpoint (optional - only needed for custom URLs)"
              {...createForm.getInputProps('endpoint')}
            />

            <SimpleGrid cols={2}>
              <TextInput
                label="API Key"
                type="password"
                placeholder="Your API key (optional)"
                description="Secret key sent to the provider (kept encrypted)."
                {...createForm.getInputProps('api_key')}
              />
            </SimpleGrid>

            <Textarea
              label="Description"
              placeholder="Provider description"
              {...createForm.getInputProps('description')}
            />

            <SimpleGrid cols={2}>
              <TextInput
                label="Timeout (seconds)"
                type="number"
                min={1}
                max={300}
                description="Request timeout applied to this provider."
                {...createForm.getInputProps('timeout')}
              />
              <Switch
                label="Active"
                {...createForm.getInputProps('is_active', { type: 'checkbox' })}
              />
            </SimpleGrid>

            <Divider label="Custom Provider Configuration" labelPosition="center" />

            <Alert color="blue" title="Advanced Settings">
              Configure advanced settings for custom/locally hosted providers. These settings are optional but recommended for better integration.
            </Alert>

            <SimpleGrid cols={2}>
              <Select
                label="Custom Authentication Type"
                placeholder="Select authentication type"
                description="How your custom provider handles authentication"
                data={[
                  { value: 'bearer', label: 'Bearer Token' },
                  { value: 'api_key', label: 'API Key' },
                  { value: 'basic', label: 'Basic Auth' },
                  { value: 'custom', label: 'Custom' },
                  { value: 'none', label: 'None' },
                ]}
                clearable
                {...createForm.getInputProps('custom_auth_type')}
              />
            </SimpleGrid>

            <Divider label="Model Configuration" labelPosition="center" />

            {/* Embedding Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconBrain size={18} color="var(--mantine-color-green-6)" />
                  <Title order={6} c="green.8">Embedding Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('embedding')}
                  loading={testProviderMutation.isPending}
                >
                  Test embedding
                </Button>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add embedding models"
                {...createForm.getInputProps('embedding.models')}
              />
              {createForm.values.embedding && createForm.values.embedding.models.length > 0 && (
                <>
                  <SimpleGrid cols={2} mt="md">
                    <TextInput
                      label="Max Input Tokens"
                      type="number"
                      placeholder="8191"
                      {...createForm.getInputProps('embedding.config.max_input_tokens')}
                    />
                    <TextInput
                      label="Batch Size"
                      type="number"
                      placeholder="100"
                      {...createForm.getInputProps('embedding.config.batch_size')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/embeddings"
                    mt="md"
                    {...createForm.getInputProps('embedding.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            {/* Generative Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconRobot size={18} color="var(--mantine-color-purple-6)" />
                  <Title order={6} c="purple.8">Generative Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('generative')}
                  loading={testProviderMutation.isPending}
                >
                  Test generative
                </Button>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add generative models"
                {...createForm.getInputProps('generative.models')}
              />
              {createForm.values.generative && createForm.values.generative.models.length > 0 && (
                <>
                  <SimpleGrid cols={3} mt="md">
                    <TextInput
                      label="Max Tokens"
                      type="number"
                      placeholder="4096"
                      {...createForm.getInputProps('generative.config.max_tokens')}
                    />
                    <TextInput
                      label="Temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      placeholder="0.7"
                      {...createForm.getInputProps('generative.config.temperature')}
                    />
                    <TextInput
                      label="Top P"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      placeholder="1.0"
                      {...createForm.getInputProps('generative.config.top_p')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/chat/completions"
                    mt="md"
                    {...createForm.getInputProps('generative.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            {/* Reranker Section */}
            <Card withBorder p="md" shadow="sm">
              <Group gap="sm" mb="md" justify="space-between">
                <Group gap="sm">
                  <IconFilter size={18} color="var(--mantine-color-orange-6)" />
                  <Title order={6} c="orange.8">Reranker Models</Title>
                </Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => handleTestProvider('reranker')}
                  loading={testProviderMutation.isPending}
                >
                  Test reranker
                </Button>
              </Group>
              <TagsInput
                label="Models"
                placeholder="Add reranker models"
                {...createForm.getInputProps('reranker.models')}
              />
              {createForm.values.reranker && createForm.values.reranker.models.length > 0 && (
                <>
                  <SimpleGrid cols={2} mt="md">
                    <TextInput
                      label="Max Documents"
                      type="number"
                      placeholder="100"
                      {...createForm.getInputProps('reranker.config.max_documents')}
                    />
                    <TextInput
                      label="Top N"
                      type="number"
                      placeholder="10"
                      {...createForm.getInputProps('reranker.config.top_n')}
                    />
                  </SimpleGrid>
                  <TextInput
                    label="Endpoint Suffix"
                    placeholder="/rerank"
                    mt="md"
                    {...createForm.getInputProps('reranker.config.endpoint_suffix')}
                  />
                </>
              )}
            </Card>

            <Group justify="flex-end">
              <Button
                variant="light"
                onClick={() => {
                  setCreateModalOpen(false);
                  createForm.reset();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={createProviderMutation.isPending}
              >
                Create Provider
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
                    <Text size="sm" fw={500}>Max Input Tokens</Text>
                    <Text>{selectedProvider.embedding.config?.max_input_tokens || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Batch Size</Text>
                    <Text>{selectedProvider.embedding.config?.batch_size || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Endpoint Suffix</Text>
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
                    <Text size="sm" fw={500}>Max Tokens</Text>
                    <Text>{selectedProvider.generative.config?.max_tokens || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Temperature</Text>
                    <Text>{selectedProvider.generative.config?.temperature || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Top P</Text>
                    <Text>{selectedProvider.generative.config?.top_p || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Endpoint Suffix</Text>
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
                    <Text size="sm" fw={500}>Max Documents</Text>
                    <Text>{selectedProvider.reranker.config?.max_documents || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Top N</Text>
                    <Text>{selectedProvider.reranker.config?.top_n || 'N/A'}</Text>
                  </div>
                  <div>
                    <Text size="sm" fw={500}>Endpoint Suffix</Text>
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

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setSelectedProvider(null);
        }}
        title={
          <Group gap="sm">
            <IconTrash size={20} color="var(--mantine-color-red-6)" />
            <Text fw={600} size="lg" c="red">Delete Model Provider</Text>
          </Group>
        }
        centered
      >
        <Stack gap="md">
          <Text>
            Are you sure you want to delete the model provider{' '}
            <Text component="span" fw={600}>
              "{selectedProvider?.name}"
            </Text>
            ? This action cannot be undone.
          </Text>
          <Group justify="flex-end" gap="sm">
            <Button
              variant="light"
              onClick={() => {
                setDeleteModalOpen(false);
                setSelectedProvider(null);
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              onClick={handleConfirmDelete}
              loading={deleteProviderMutation.isPending}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>

    </Page>
  );
}
