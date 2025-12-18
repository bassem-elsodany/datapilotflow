import { Button, Checkbox, Group, Modal, ScrollArea, Stack, Text } from '@mantine/core';
import { ModelType } from '@/api/resources/model-providers';

// Mock LiteLLM models list - in production, this would come from backend
export const LITELLM_MODELS_BY_TYPE: Record<'embedding' | 'generative' | 'reranker', string[]> = {
  embedding: [
    'text-embedding-3-small',
    'text-embedding-3-large',
    'text-embedding-ada-002',
    'text-embedding-ada-001',
    'text-search-davinci-doc-001',
    'voyage-3',
    'voyage-3-lite',
    'voyage-large-2-instruct',
    'voyage-large-2',
    'voyage-lite-02-instruct',
    'voyage-2',
    'voyage-lite-02',
    'voyage-lite-01-instruct',
    'voyage-lite-01',
    'voyage-code-2',
    'voyage-finance-2',
    'voyage-large-3',
    'voyage-large-3-instruct',
    'mistral-embed',
    'multilingual-e5-large',
    'multilingual-e5-small',
    'multilingual-e5-base',
    'gtx-embedding-1',
    'uae-large-v1',
    'bge-large-en-v1.5',
  ],
  generative: [
    'gpt-5',
    'gpt-5-mini',
    'gpt-5-nano',
    'gpt-5-chat-latest',
    'gpt-4o',
    'gpt-4o-2024-11-20',
    'gpt-4o-2024-08-06',
    'gpt-4o-mini',
    'gpt-4o-mini-2024-07-18',
    'gpt-4-turbo',
    'gpt-4-turbo-2024-04-09',
    'gpt-4',
    'gpt-4-32k',
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-16k',
    'claude-opus-4.5',
    'claude-opus-4',
    'claude-sonnet-4',
    'claude-haiku-4.5',
    'claude-3-haiku',
    'mistral-large-latest',
    'mistral-medium-latest',
    'mistral-small-latest',
    'groq-mixtral-8x7b-32768',
    'groq-llama3-70b-8192',
    'groq-llama3-8b-8192',
    'gemini-pro',
    'gemini-pro-vision',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
    'command-light',
    'command',
    'command-r',
    'command-r-plus',
    'command-r-v1:104b',
    'llama-2-70b-chat',
    'llama-2-13b-chat',
    'llama-2-7b-chat',
    'llama-3-70b',
    'llama-3-8b',
    'perplexity-sonar-small-chat',
    'perplexity-sonar-small-online',
    'perplexity-sonar-medium-chat',
    'perplexity-sonar-medium-online',
  ],
  reranker: [
    'cohere-rerank-3.5',
    'cohere-rerank-3-lite',
    'cohere-rerank-2',
    'jina-reranker-v2-base-multilingual',
    'jina-reranker-v1-base-en',
    'voyage-rerank-2',
    'bge-reranker-v2-m3',
    'bge-reranker-v2-gemma',
    'rankgpt-4-turbo',
    'rankgpt-4o',
    'rankgpt-3.5-turbo',
  ],
};

export interface BrowseModelsModalProps {
  isOpen: boolean;
  modelType: ModelType | null;
  selectedModels: Set<string>;
  onSelectedModelsChange: (models: Set<string>) => void;
  onClose: () => void;
  onAdd: () => void;
}

export function BrowseModelsModal({
  isOpen,
  modelType,
  selectedModels,
  onSelectedModelsChange,
  onClose,
  onAdd,
}: BrowseModelsModalProps) {
  const availableModels = (modelType && (modelType === ModelType.EMBEDDING || modelType === ModelType.GENERATIVE || modelType === ModelType.RERANKER))
    ? LITELLM_MODELS_BY_TYPE[modelType]
    : [];

  const handleToggleModel = (model: string) => {
    const newSelected = new Set(selectedModels);
    if (newSelected.has(model)) {
      newSelected.delete(model);
    } else {
      newSelected.add(model);
    }
    onSelectedModelsChange(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedModels.size === availableModels.length) {
      onSelectedModelsChange(new Set());
    } else {
      onSelectedModelsChange(new Set(availableModels));
    }
  };

  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title={`Browse ${modelType ? modelType.charAt(0).toUpperCase() + modelType.slice(1) : 'Model'} Models`}
      size="lg"
      centered
    >
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          Select models to add to your provider configuration. All available {modelType} models from LiteLLM SDK are listed below.
        </Text>

        <Group>
          <Button
            size="xs"
            variant="light"
            onClick={handleSelectAll}
          >
            {selectedModels.size === availableModels.length ? 'Deselect All' : 'Select All'}
          </Button>
          <Text size="xs" c="dimmed">
            {selectedModels.size} selected
          </Text>
        </Group>

        <ScrollArea style={{ height: 400 }}>
          <Stack gap="xs" p="xs">
            {availableModels.map((model: string) => (
              <Group key={model} gap="xs">
                <Checkbox
                  checked={selectedModels.has(model)}
                  onChange={() => handleToggleModel(model)}
                />
                <Text size="sm" style={{ flex: 1 }}>
                  {model}
                </Text>
              </Group>
            ))}
          </Stack>
        </ScrollArea>

        <Group justify="flex-end" gap="xs">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={onAdd}
            disabled={selectedModels.size === 0}
          >
            Add Selected ({selectedModels.size})
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
