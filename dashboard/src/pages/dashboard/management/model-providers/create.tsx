import { useState } from 'react';
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
  Alert
} from '@mantine/core';
import { paths } from '@/routes/paths';
import { useCreateModelProvider } from '@/api/resources/model-providers';
import { ModelType } from '@/api/resources/model-providers';
import { notifications } from '@mantine/notifications';
import { useForm } from '@mantine/form';
import { useNavigate } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Model Providers', href: paths.dashboard.management.modelProviders.list },
  { label: 'Create' },
];

const predefinedProviders = [
  {
    name: 'OpenAI',
    provider_type: 'openai',
    endpoint: 'https://api.openai.com/v1',
    supported_model_types: ['embedding', 'generative'] as ModelType[],
    embedding_models: [
      'text-embedding-3-small',
      'text-embedding-3-large', 
      'text-embedding-ada-002'
    ],
    generative_models: [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4-turbo',
      'gpt-4',
      'gpt-3.5-turbo'
    ],
    description: 'OpenAI\'s unified provider for both embedding and generative models',
    provider_config: {
      embedding_endpoint: '/embeddings',
      generative_endpoint: '/chat/completions',
      max_tokens: 4096,
      temperature: 0.7
    }
  },
  {
    name: 'Anthropic',
    provider_type: 'anthropic',
    endpoint: 'https://api.anthropic.com/v1',
    supported_model_types: ['embedding', 'generative'] as ModelType[],
    embedding_models: [
      'claude-3-5-sonnet-embedding',
      'claude-3-opus-embedding',
      'claude-3-sonnet-embedding'
    ],
    generative_models: [
      'claude-3-5-sonnet-20241022',
      'claude-3-5-haiku-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229',
      'claude-3-haiku-20240307'
    ],
    description: 'Anthropic\'s unified provider for both embedding and generative models',
    provider_config: {
      embedding_endpoint: '/embeddings',
      generative_endpoint: '/messages',
      max_tokens: 4096,
      temperature: 0.7
    }
  },
  {
    name: 'Google',
    provider_type: 'google',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta',
    supported_model_types: ['embedding', 'generative'] as ModelType[],
    embedding_models: [
      'text-embedding-004',
      'text-multilingual-embedding-002'
    ],
    generative_models: [
      'gemini-1.5-pro',
      'gemini-1.5-flash',
      'gemini-1.0-pro'
    ],
    description: 'Google\'s unified provider for both embedding and generative models',
    provider_config: {
      embedding_endpoint: '/models',
      generative_endpoint: '/models',
      max_tokens: 4096,
      temperature: 0.7
    }
  },
  {
    name: 'Ollama',
    provider_type: 'ollama',
    endpoint: 'http://localhost:11434/api',
    supported_model_types: ['embedding', 'generative'] as ModelType[],
    embedding_models: [
      'nomic-embed-text',
      'mxbai-embed-large',
      'all-minilm',
      'bge-large-en',
      'bge-base-en'
    ],
    generative_models: [
      'llama3.1:8b',
      'llama3.1:70b',
      'mistral:7b',
      'codellama:7b',
      'phi3:3.8b'
    ],
    description: 'Ollama\'s unified provider for local embedding and generative models',
    provider_config: {
      embedding_endpoint: '/embeddings',
      generative_endpoint: '/generate',
      max_tokens: 4096,
      temperature: 0.7
    }
  },
  {
    name: 'Hugging Face',
    provider_type: 'huggingface',
    endpoint: 'https://api-inference.huggingface.co/models',
    supported_model_types: ['embedding', 'generative'] as ModelType[],
    embedding_models: [
      'sentence-transformers/all-MiniLM-L6-v2',
      'sentence-transformers/all-mpnet-base-v2',
      'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
      'sentence-transformers/distilbert-base-nli-mean-tokens'
    ],
    generative_models: [
      'microsoft/DialoGPT-medium',
      'facebook/blenderbot-400M-distill',
      'google/flan-t5-base'
    ],
    description: 'Hugging Face\'s unified provider for both embedding and generative models',
    provider_config: {
      embedding_endpoint: '/',
      generative_endpoint: '/',
      max_tokens: 4096,
      temperature: 0.7
    }
  },
  {
    name: 'Groq',
    provider_type: 'groq',
    endpoint: 'https://api.groq.com/openai/v1',
    supported_model_types: ['generative'] as ModelType[],
    embedding_models: [],
    generative_models: [
      'llama-3.1-70b-versatile',
      'llama-3.1-8b-instant',
      'mixtral-8x7b-32768',
      'gemma-7b-it'
    ],
    description: 'Groq\'s high-performance generative model provider',
    provider_config: {
      generative_endpoint: '/chat/completions',
      max_tokens: 4096,
      temperature: 0.7
    }
  }
];

export default function CreateModelProvider() {
  const navigate = useNavigate();
  const createProviderMutation = useCreateModelProvider();

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

  const handlePredefinedProviderSelect = (providerName: string) => {
    const provider = predefinedProviders.find(p => p.name === providerName);
    if (provider) {
      form.setValues({
        name: provider.name,
        provider_type: provider.provider_type,
        endpoint: provider.endpoint,
        api_key: '',
        description: provider.description,
        is_active: true,
        supported_model_types: provider.supported_model_types,
        embedding_models: provider.embedding_models,
        generative_models: provider.generative_models,
        provider_config: provider.provider_config,
      });
    }
  };

  const handleSubmit = async (values: typeof form.values) => {
    try {
      await createProviderMutation.mutateAsync(values);
      notifications.show({
        title: 'Success',
        message: 'Model provider created successfully',
        color: 'green',
      });
      navigate(paths.dashboard.management.modelProviders.list);
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to create model provider',
        color: 'red',
      });
    }
  };

  return (
    <Page title="Create Model Provider">
      <PageHeader 
        title="Create Model Provider" 
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
            <Alert color="blue" title="Quick Setup">
              Select a predefined provider below to automatically fill in the configuration, or create a custom provider manually.
            </Alert>

            <MultiSelect
              label="Predefined Providers"
              placeholder="Select a predefined provider (optional)"
              data={predefinedProviders.map(p => ({ value: p.name, label: p.name }))}
              onChange={(value) => {
                if (value.length > 0) {
                  handlePredefinedProviderSelect(value[0]);
                }
              }}
              clearable
            />

            <Divider />

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
                loading={createProviderMutation.isPending}
              >
                Create Provider
              </Button>
            </Group>
          </Stack>
        </form>
      </Card>
    </Page>
  );
}
