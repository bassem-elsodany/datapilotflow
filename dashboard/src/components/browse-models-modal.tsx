import { Button, Center, Checkbox, Group, Loader, Modal, ScrollArea, Stack, Text } from '@mantine/core';
import { ModelType, useGetAvailableModels } from '@/api/resources/model-providers';

export interface BrowseModelsModalProps {
  isOpen: boolean;
  modelType: ModelType | null;
  providerType: string; // The provider type (e.g., 'openai', 'anthropic')
  selectedModels: Set<string>;
  onSelectedModelsChange: (models: Set<string>) => void;
  onClose: () => void;
  onAdd: () => void;
}

export function BrowseModelsModal({
  isOpen,
  modelType,
  providerType,
  selectedModels,
  onSelectedModelsChange,
  onClose,
  onAdd,
}: BrowseModelsModalProps) {
  // Fetch available models from backend using LiteLLM SDK
  const { data: availableModels = [], isLoading, error } = useGetAvailableModels(providerType, modelType || undefined);

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
      title={`Browse ${modelType ? modelType.charAt(0).toUpperCase() + modelType.slice(1) : 'Model'} Models - ${providerType}`}
      size="lg"
      centered
    >
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          Select {modelType} models to add to your {providerType} provider. These models are supported by LiteLLM SDK.
        </Text>

        {isLoading ? (
          <Center py="xl">
            <Stack align="center" gap="sm">
              <Loader size="lg" />
              <Text size="sm" c="dimmed">
                Loading available models from LiteLLM SDK...
              </Text>
            </Stack>
          </Center>
        ) : error ? (
          <Stack gap="sm">
            <Text size="sm" c="red">
              Error loading models: {error instanceof Error ? error.message : 'Unknown error'}
            </Text>
            <Button size="sm" variant="light" onClick={onClose}>
              Close
            </Button>
          </Stack>
        ) : availableModels.length === 0 ? (
          <Stack gap="sm">
            <Text size="sm" c="yellow">
              No models found for this provider type. The provider may not be supported by LiteLLM SDK.
            </Text>
            <Button size="sm" variant="light" onClick={onClose}>
              Close
            </Button>
          </Stack>
        ) : (
          <>
            <Group>
              <Button
                size="xs"
                variant="light"
                onClick={handleSelectAll}
              >
                {selectedModels.size === availableModels.length ? 'Deselect All' : 'Select All'}
              </Button>
              <Text size="xs" c="dimmed">
                {selectedModels.size} of {availableModels.length} selected
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
          </>
        )}
      </Stack>
    </Modal>
  );
}
