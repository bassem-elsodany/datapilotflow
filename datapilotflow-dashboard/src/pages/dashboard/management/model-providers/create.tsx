import { ModelType, useCreateModelProvider, useGetAvailableProviderTypes, useTestModelProvider } from '@/api/resources/model-providers';
import { BrowseModelsModal } from '@/components/browse-models-modal';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  Button,
  Card,
  Group,
  Modal,
  MultiSelect,
  Paper,
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
import { IconBookmark } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Helper function to mask API key for display
const maskApiKey = (key: string | undefined): string => {
  if (!key) return '';
  if (key.length <= 8) return key; // Too short to mask
  // Show first 8 chars and mask the rest
  return key.substring(0, 8) + '•'.repeat(Math.min(key.length - 8, 20));
};


const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Model Providers', href: paths.dashboard.management.modelProviders.list },
  { label: 'Create' },
];


export default function CreateModelProvider() {
  const navigate = useNavigate();
  const createProviderMutation = useCreateModelProvider();
  const testProviderMutation = useTestModelProvider();
  const { data: providerTypes = [], isLoading: isLoadingProviderTypes } = useGetAvailableProviderTypes();

  const [isEditingApiKey, setIsEditingApiKey] = useState(false);
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testModalType, setTestModalType] = useState<ModelType | null>(null);
  const [testModalModel, setTestModalModel] = useState<string>('');
  const [testResult, setTestResult] = useState<{
    success: boolean;
    status_code?: number;
    duration_ms?: number;
    message?: string;
    body?: string;
  } | null>(null);

  // Browse models modal state
  const [browseModelsModalOpen, setBrowseModelsModalOpen] = useState(false);
  const [browseModelsType, setBrowseModelsType] = useState<ModelType | null>(null);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());

  // Get supported models hook
  const [providerId] = useState<string>(''); // Placeholder - not needed for browse feature

  const form = useForm({
    initialValues: {
      name: '',
      provider_type: '',
      endpoint: '',
      api_key: '',
      api_key_field_name: 'api_key',
      description: '',
      is_active: true,
      timeout: 60,
      supported_model_types: [] as ModelType[],
      embedding_models: [] as string[],
      generative_models: [] as string[],
      reranker_models: [] as string[],
      embedding_config: {} as Record<string, any>,
      generative_config: {} as Record<string, any>,
      reranker_config: {} as Record<string, any>,
      embedding_endpoint: '' as string,
      generative_endpoint: '' as string,
      reranker_endpoint: '' as string,
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      provider_type: (value) => (!value ? 'Provider type is required' : null),
      // Endpoint is optional - only required if using custom URL
    },
  });

  const buildProviderPayload = (values: typeof form.values) => ({
    name: values.name,
    provider_type: values.provider_type,
    endpoint: values.endpoint,
    api_key: values.api_key || undefined,
    api_key_field_name: values.api_key_field_name || 'api_key',
    description: values.description || undefined,
    is_active: values.is_active,
    timeout: values.timeout,
    embedding: values.embedding_models.length > 0
      ? {
        models: values.embedding_models,
        config: values.embedding_config,
        endpoint: values.embedding_endpoint || undefined,
      }
      : undefined,
    generative: values.generative_models.length > 0
      ? {
        models: values.generative_models,
        config: values.generative_config,
        endpoint: values.generative_endpoint || undefined,
      }
      : undefined,
    reranker: values.reranker_models.length > 0
      ? {
        models: values.reranker_models,
        config: values.reranker_config,
        endpoint: values.reranker_endpoint || undefined,
      }
      : undefined,
  });

  const handleBrowseModels = (modelType: ModelType) => {
    setBrowseModelsType(modelType);
    setSelectedModels(new Set());
    setBrowseModelsModalOpen(true);
  };

  const handleAddSelectedModels = () => {
    if (!browseModelsType || selectedModels.size === 0) {
      notifications.show({
        title: 'Error',
        message: 'Please select at least one model',
        color: 'red',
      });
      return;
    }

    const modelsToAdd = Array.from(selectedModels);

    if (browseModelsType === ModelType.EMBEDDING) {
      const newModels = [...form.values.embedding_models, ...modelsToAdd].filter((v, i, a) => a.indexOf(v) === i);
      form.setFieldValue('embedding_models', newModels);
    } else if (browseModelsType === ModelType.GENERATIVE) {
      const newModels = [...form.values.generative_models, ...modelsToAdd].filter((v, i, a) => a.indexOf(v) === i);
      form.setFieldValue('generative_models', newModels);
    } else if (browseModelsType === ModelType.RERANKER) {
      const newModels = [...form.values.reranker_models, ...modelsToAdd].filter((v, i, a) => a.indexOf(v) === i);
      form.setFieldValue('reranker_models', newModels);
    }

    setBrowseModelsModalOpen(false);
    setSelectedModels(new Set());

    notifications.show({
      title: 'Success',
      message: `Added ${modelsToAdd.length} model(s)`,
      color: 'green',
    });
  };

  const handleTest = async (testType: ModelType, modelName?: string) => {
    if (!modelName) {
      notifications.show({
        title: 'Error',
        message: `Please add at least one ${testType} model to test.`,
        color: 'red',
      });
      return;
    }

    try {
      const provider = buildProviderPayload(form.values);
      const payload = { provider, test_type: testType, model: modelName };

      const result = await testProviderMutation.mutateAsync({ variables: payload } as any);

      setTestResult({
        success: Boolean(result.success),
        status_code: result.status_code,
        duration_ms: result.duration_ms,
        message: result.message,
        body: result.body,
      });
    } catch (error: any) {
      // Extract detailed error message from API response
      let errorMessage = 'Failed to run test';
      
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

      setTestResult({
        success: false,
        status_code: error?.response?.status || error?.status,
        duration_ms: undefined,
        message: errorMessage,
        body: error?.response?.data ? JSON.stringify(error.response.data, null, 2) : undefined,
      });
    }
  };
  const openTestModal = (testType: ModelType, models: string[]) => {
    if (!models.length) return;
    setTestModalType(testType);
    setTestModalModel(models[0]);
    setTestModalOpen(true);
  };
  const handleSubmit = async (values: typeof form.values) => {
    try {
      const payload = buildProviderPayload(values);

      await createProviderMutation.mutateAsync({ variables: payload } as any);
      notifications.show({
        title: 'Success',
        message: 'Model provider created successfully',
        color: 'green',
      });
      navigate(paths.dashboard.management.modelProviders.list);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error?.message || 'Failed to create model provider',
        color: 'red',
      });
    }
  };

  return (
    <Page title="Create Model Provider">
      <PageHeader title="Create Model Provider" breadcrumbs={breadcrumbs}>
        <Group>
          <Button
            variant="light"
            onClick={() => navigate(paths.dashboard.management.modelProviders.list)}
          >
            Cancel
          </Button>
        </Group>
      </PageHeader>

      <Card withBorder shadow="sm" radius="md" p="xl">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="xl">

            <Paper withBorder p="lg" radius="md">
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Title order={4}>Basics</Title>
                    <Text size="sm" c="dimmed">
                      Core info to identify and reach your provider.
                    </Text>
                  </div>
                  <Switch
                    label="Active"
                    {...form.getInputProps('is_active', { type: 'checkbox' })}
                  />
                </Group>

                <SimpleGrid cols={2} spacing="md">
                  <TextInput
                    label="Name"
                    placeholder="Provider name"
                    description="Display name shown in the provider list."
                    required
                    {...form.getInputProps('name')}
                  />
                  <Select
                    label="Provider Type"
                    placeholder={isLoadingProviderTypes ? "Loading provider types..." : "Select the provider type"}
                    description="Choose the provider type from the list."
                    required
                    searchable
                    disabled={isLoadingProviderTypes}
                    data={providerTypes.map((type: string) => ({ value: type, label: type }))}
                    {...form.getInputProps('provider_type')}
                  />
                </SimpleGrid>

                <SimpleGrid cols={2} spacing="md">
                  <TextInput
                    label="Endpoint"
                    placeholder="https://api.example.com/v1"
                    description="Base API URL for the provider endpoint (optional - only needed for custom URLs)"
                    {...form.getInputProps('endpoint')}
                  />
                  <TextInput
                    label="Timeout (seconds)"
                    type="number"
                    min={1}
                    max={300}
                    description="Request timeout applied to this provider."
                    {...form.getInputProps('timeout')}
                  />
                </SimpleGrid>

                <Textarea
                  label="Description"
                  placeholder="Provider description"
                  description="Optional note to help you recognize this provider."
                  {...form.getInputProps('description')}
                />
              </Stack>
            </Paper>

            <Paper withBorder p="lg" radius="md">
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Title order={4}>Authentication</Title>
                    <Text size="sm" c="dimmed">Manage your API key.</Text>
                  </div>
                </Group>

                <Group grow align="flex-start">
                  <TextInput
                    label="API Key Field Name"
                    placeholder="api_key"
                    description="HTTP header name for the API key (e.g., 'api_key', 'Api-Key', 'X-API-Key', 'Authorization'). Defaults to 'api_key'."
                    value={form.values.api_key_field_name}
                    onChange={(e) => form.setFieldValue('api_key_field_name', e.currentTarget.value)}
                  />
                  <div>
                    <TextInput
                      label="API Key"
                      placeholder="Your API key (optional for custom providers)"
                      description="Secret key sent to the provider (kept encrypted)."
                      value={isEditingApiKey ? form.values.api_key : maskApiKey(form.values.api_key)}
                      onChange={(e) => {
                        if (!isEditingApiKey) {
                          setIsEditingApiKey(true);
                          form.setFieldValue('api_key', '');
                        } else {
                          form.setFieldValue('api_key', e.currentTarget.value);
                        }
                      }}
                      onFocus={() => {
                        if (!isEditingApiKey) {
                          setIsEditingApiKey(true);
                          form.setFieldValue('api_key', '');
                        }
                      }}
                    />
                  </div>
                </Group>
              </Stack>
            </Paper>

            <Paper withBorder p="lg" radius="md">
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Title order={4}>Models</Title>
                    <Text size="sm" c="dimmed">Add model names and configure provider-specific settings.</Text>
                  </div>
                </Group>

                <MultiSelect
                  label="Supported Model Types"
                  placeholder="Select model types"
                  description="Choose the model types that this provider will be used for."
                  required
                  data={[
                    { value: ModelType.EMBEDDING, label: 'Embedding' },
                    { value: ModelType.GENERATIVE, label: 'Generative' },
                    { value: ModelType.RERANKER, label: 'Reranker' },
                  ]}
                  {...form.getInputProps('supported_model_types')}
                />

                <Stack gap="md">
                  {/* Embedding group */}
                  {form.values.supported_model_types.includes(ModelType.EMBEDDING) && (
                    <Paper withBorder radius="md" p="md">
                      <Stack gap="xs">
                        <Group justify="space-between" align="center">
                          <div>
                            <Text fw={500}>Embedding models</Text>
                            <Text size="xs" c="dimmed">
                              Used for vector search and similarity.
                            </Text>
                          </div>
                          <Group gap="xs">
                            <Button
                              size="xs"
                              variant="default"
                              leftSection={<IconBookmark size={14} />}
                              onClick={() => handleBrowseModels(ModelType.EMBEDDING)}
                            >
                              Browse Models
                            </Button>
                            <Button
                              size="xs"
                              variant="light"
                              onClick={() => openTestModal(ModelType.EMBEDDING, form.values.embedding_models)}
                              disabled={
                                !form.values.embedding_models.length || testProviderMutation.isPending
                              }
                              loading={testProviderMutation.isPending}
                            >
                              Test embedding
                            </Button>
                          </Group>
                        </Group>

                        <TagsInput
                          label="Embedding Models"
                          placeholder="Add embedding models"
                          {...form.getInputProps('embedding_models')}
                        />
                        <TextInput
                          label="Embedding Endpoint (optional)"
                          placeholder="/v1/embeddings"
                          {...form.getInputProps('embedding_endpoint')}
                        />
                        <SimpleGrid cols={2} spacing="sm">
                          <TextInput
                            label="Max Input Tokens"
                            type="number"
                            placeholder="8191"
                            {...form.getInputProps('embedding_config.max_input_tokens')}
                          />
                          <TextInput
                            label="Batch Size"
                            type="number"
                            placeholder="100"
                            {...form.getInputProps('embedding_config.batch_size')}
                          />
                        </SimpleGrid>
                      </Stack>
                    </Paper>
                  )}

                  {/* Generative group */}
                  {form.values.supported_model_types.includes(ModelType.GENERATIVE) && (
                    <Paper withBorder radius="md" p="md">
                      <Stack gap="xs">
                        <Group justify="space-between" align="center">
                          <div>
                            <Text fw={500}>Generative models</Text>
                            <Text size="xs" c="dimmed">
                              Used for chat, completions, and reasoning.
                            </Text>
                          </div>
                          <Group gap="xs">
                            <Button
                              size="xs"
                              variant="default"
                              leftSection={<IconBookmark size={14} />}
                              onClick={() => handleBrowseModels(ModelType.GENERATIVE)}
                            >
                              Browse Models
                            </Button>
                            <Button
                              size="xs"
                              variant="light"
                              onClick={() => openTestModal(ModelType.GENERATIVE, form.values.generative_models)}
                              disabled={
                                !form.values.generative_models.length ||
                                testProviderMutation.isPending
                              }
                              loading={testProviderMutation.isPending}
                            >
                              Test generative
                            </Button>
                          </Group>
                        </Group>

                        <TagsInput
                          label="Generative Models"
                          placeholder="Add generative models"
                          {...form.getInputProps('generative_models')}
                        />
                        <TextInput
                          label="Generative Endpoint (optional)"
                          placeholder="/v1/chat/completions"
                          {...form.getInputProps('generative_endpoint')}
                        />
                        <SimpleGrid cols={3} spacing="sm">
                          <TextInput
                            label="Max Tokens"
                            type="number"
                            placeholder="4096"
                            {...form.getInputProps('generative_config.max_tokens')}
                          />
                          <TextInput
                            label="Temperature"
                            type="number"
                            step="0.1"
                            min={0}
                            max={2}
                            placeholder="0.7"
                            {...form.getInputProps('generative_config.temperature')}
                          />
                          <TextInput
                            label="Top P"
                            type="number"
                            step="0.1"
                            min={0}
                            max={1}
                            placeholder="1.0"
                            {...form.getInputProps('generative_config.top_p')}
                          />
                        </SimpleGrid>
                      </Stack>
                    </Paper>
                  )}

                  {/* Reranker group */}
                  {form.values.supported_model_types.includes(ModelType.RERANKER) && (
                    <Paper withBorder radius="md" p="md">
                      <Stack gap="xs">
                        <Group justify="space-between" align="center">
                          <div>
                            <Text fw={500}>Reranker models</Text>
                            <Text size="xs" c="dimmed">
                              Used to reorder documents by relevance.
                            </Text>
                          </div>
                          <Group gap="xs">
                            <Button
                              size="xs"
                              variant="default"
                              leftSection={<IconBookmark size={14} />}
                              onClick={() => handleBrowseModels(ModelType.RERANKER)}
                            >
                              Browse Models
                            </Button>
                            <Button
                              size="xs"
                              variant="light"
                              onClick={() => openTestModal(ModelType.RERANKER, form.values.reranker_models)}
                              disabled={
                                !form.values.reranker_models.length ||
                                testProviderMutation.isPending
                              }
                              loading={testProviderMutation.isPending}
                            >
                              Test reranker
                            </Button>
                          </Group>
                        </Group>

                        <TagsInput
                          label="Reranker Models"
                          placeholder="Add reranker models"
                          {...form.getInputProps('reranker_models')}
                        />
                        <TextInput
                          label="Reranker Endpoint (optional)"
                          placeholder="/v1/rerank"
                          {...form.getInputProps('reranker_endpoint')}
                        />
                        <SimpleGrid cols={2} spacing="sm">
                          <TextInput
                            label="Max Documents"
                            type="number"
                            placeholder="100"
                            {...form.getInputProps('reranker_config.max_documents')}
                          />
                          <TextInput
                            label="Top N"
                            type="number"
                            placeholder="10"
                            {...form.getInputProps('reranker_config.top_n')}
                          />
                        </SimpleGrid>
                      </Stack>
                    </Paper>
                  )}
                </Stack>
              </Stack>
            </Paper>

            <Group justify="flex-end" gap="sm">
              <Button
                variant="light"
                onClick={() => navigate(paths.dashboard.management.modelProviders.list)}
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
      </Card>

      <Modal
        opened={testModalOpen}
        onClose={() => {
          setTestModalOpen(false);
          setTestResult(null);
        }}
        title={`Test ${testModalType ? testModalType.charAt(0).toUpperCase() + testModalType.slice(1) : 'Model'}`}
        size="lg"
        centered
      >
        <Stack gap="lg">
          {/* Model Selection Section */}
          <Stack gap="sm">
            <Text size="sm" c="dimmed">
              {testModalType
                ? `Select a ${testModalType} model to run a live health check and inspect the response payload.`
                : 'Select a model to test.'}
            </Text>
            <Select
              label="Model"
              placeholder="Select model"
              data={
                testModalType === ModelType.EMBEDDING
                  ? form.values.embedding_models
                  : testModalType === ModelType.GENERATIVE
                    ? form.values.generative_models
                    : form.values.reranker_models
              }
              value={testModalModel}
              onChange={(value) => setTestModalModel(value || '')}
              searchable
            />
          </Stack>

          {/* Action Buttons */}
          <Group justify="flex-end" gap="sm">
            <Button
              variant="default"
              onClick={() => {
                setTestModalOpen(false);
                setTestResult(null);
              }}
            >
              Close
            </Button>
            <Button
              onClick={async () => {
                if (!testModalType || !testModalModel) return;
                await handleTest(testModalType, testModalModel);
              }}
              disabled={!testModalType || !testModalModel}
              loading={testProviderMutation.isPending}
            >
              Run test
            </Button>
          </Group>

          {/* Test Results Section */}
          {testResult && (
            <Stack gap="md" p="md" style={{ backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div>
                <Text size="sm" fw={600} mb="xs">
                  Test Result
                </Text>
                <Stack gap="xs" style={{ fontSize: '0.875rem' }}>
                  <Group justify="space-between">
                    <Text c="dimmed">Status Code:</Text>
                    <Text fw={500}>{testResult.status_code ?? 'N/A'}</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text c="dimmed">Duration:</Text>
                    <Text fw={500}>{testResult.duration_ms ?? 'N/A'} ms</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text c="dimmed">Message:</Text>
                    <Text fw={500} c={testResult.success ? 'green' : 'red'}>
                      {testResult.message ?? 'N/A'}
                    </Text>
                  </Group>
                </Stack>
              </div>

              <div>
                <Text size="sm" fw={600} mb="xs">
                  Response Body (JSON)
                </Text>
                <Paper withBorder radius="md" p="xs" style={{ backgroundColor: 'white' }}>
                  <Textarea
                    value={testResult.body ?? ''}
                    minRows={8}
                    maxRows={12}
                    autosize
                    readOnly
                    spellCheck={false}
                    styles={{
                      input: {
                        fontFamily: 'Menlo, Monaco, Consolas, monospace',
                        fontSize: 12,
                      },
                    }}
                  />
                </Paper>
              </div>
            </Stack>
          )}
        </Stack>
      </Modal>

      {/* Browse Models Modal */}
      <BrowseModelsModal
        isOpen={browseModelsModalOpen}
        modelType={browseModelsType}
        providerType={form.values.provider_type}
        selectedModels={selectedModels}
        onSelectedModelsChange={setSelectedModels}
        onClose={() => setBrowseModelsModalOpen(false)}
        onAdd={handleAddSelectedModels}
      />
    </Page>
  );
}
