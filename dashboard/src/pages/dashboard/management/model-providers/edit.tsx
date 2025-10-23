import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { 
  Card, 
  Button, 
  Group, 
  Stack,
  TextInput,
  Textarea,
  Switch,
  SimpleGrid,
  TagsInput,
  MultiSelect,
  Alert,
  Loader,
  Center
} from '@mantine/core';
import { paths } from '@/routes/paths';
import { useGetModelProvider, useUpdateModelProvider } from '@/api/resources/model-providers';
import { ModelType } from '@/api/resources/model-providers';
import { notifications } from '@mantine/notifications';
import { useForm } from '@mantine/form';

export default function EditModelProvider() {
  const { providerId } = useParams<{ providerId: string }>();
  const navigate = useNavigate();
  
  const { data: provider, isLoading, error } = useGetModelProvider(providerId || '');
  const updateProviderMutation = useUpdateModelProvider(providerId || '');

  const form = useForm({
    initialValues: {
      name: '',
      provider_type: '',
      endpoint: '',
      api_key: '',
      description: '',
      is_active: true,
      supported_model_types: [] as ModelType[],
      embedding_models: [] as string[],
      generative_models: [] as string[],
      provider_config: {} as Record<string, any>,
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      provider_type: (value) => (!value ? 'Provider type is required' : null),
      endpoint: (value) => (!value ? 'Endpoint is required' : null),
      api_key: (value) => (!value ? 'API key is required' : null),
    },
  });

  // Update form when provider data loads
  useEffect(() => {
    if (provider) {
      form.setValues({
        name: provider.name,
        provider_type: provider.provider_type,
        endpoint: provider.endpoint,
        api_key: provider.api_key,
        description: provider.description || '',
        is_active: provider.is_active,
        supported_model_types: provider.supported_model_types,
        embedding_models: provider.embedding_models,
        generative_models: provider.generative_models,
        provider_config: provider.provider_config,
      });
    }
  }, [provider]);

  const handleSubmit = async (values: typeof form.values) => {
    try {
      await updateProviderMutation.mutateAsync(values);
      notifications.show({
        title: 'Success',
        message: 'Model provider updated successfully',
        color: 'green',
      });
      navigate(paths.dashboard.management.modelProviders.list);
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update model provider',
        color: 'red',
      });
    }
  };

  if (isLoading) {
    return (
      <Page title="Edit Model Provider">
        <PageHeader title="Edit Model Provider" breadcrumbs={[]} />
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (error || !provider) {
    return (
      <Page title="Edit Model Provider">
        <PageHeader title="Edit Model Provider" breadcrumbs={[]} />
        <Alert color="red" title="Error">
          Failed to load model provider. Please try again.
        </Alert>
      </Page>
    );
  }

  const breadcrumbs = [
    { label: 'Dashboard', href: paths.dashboard.root },
    { label: 'Management', href: paths.dashboard.management.root },
    { label: 'Model Providers', href: paths.dashboard.management.modelProviders.list },
    { label: provider.name },
  ];

  return (
    <Page title="Edit Model Provider">
      <PageHeader 
        title={`Edit ${provider.name}`}
        breadcrumbs={breadcrumbs}
        action={
          <Group>
            <Button
              variant="light"
              onClick={() => navigate(paths.dashboard.management.modelProviders.list)}
            >
              Cancel
            </Button>
          </Group>
        }
      />

      <Card>
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <SimpleGrid cols={2}>
              <TextInput
                label="Name"
                placeholder="Provider name"
                required
                {...form.getInputProps('name')}
              />
              <TextInput
                label="Provider Type"
                placeholder="e.g., openai, anthropic"
                required
                {...form.getInputProps('provider_type')}
              />
            </SimpleGrid>

            <TextInput
              label="Endpoint"
              placeholder="https://api.example.com/v1"
              required
              {...form.getInputProps('endpoint')}
            />

            <TextInput
              label="API Key"
              type="password"
              placeholder="Your API key"
              required
              {...form.getInputProps('api_key')}
            />

            <Textarea
              label="Description"
              placeholder="Provider description"
              {...form.getInputProps('description')}
            />

            <MultiSelect
              label="Supported Model Types"
              placeholder="Select model types"
              required
              data={[
                { value: 'embedding', label: 'Embedding' },
                { value: 'generative', label: 'Generative' },
                { value: 'both', label: 'Both' },
              ]}
              {...form.getInputProps('supported_model_types')}
            />

            <SimpleGrid cols={2}>
              <TagsInput
                label="Embedding Models"
                placeholder="Add embedding models"
                {...form.getInputProps('embedding_models')}
              />
              <TagsInput
                label="Generative Models"
                placeholder="Add generative models"
                {...form.getInputProps('generative_models')}
              />
            </SimpleGrid>

            <Switch
              label="Active"
              {...form.getInputProps('is_active', { type: 'checkbox' })}
            />

            <Group justify="flex-end">
              <Button
                variant="light"
                onClick={() => navigate(paths.dashboard.management.modelProviders.list)}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                loading={updateProviderMutation.isPending}
              >
                Save Changes
              </Button>
            </Group>
          </Stack>
        </form>
      </Card>
    </Page>
  );
}
