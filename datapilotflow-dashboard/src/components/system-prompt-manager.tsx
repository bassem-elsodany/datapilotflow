/**
 * System Prompt Manager Component
 *
 * Manages system prompts as part of the conversation (no backend API calls)
 * - Create new system prompts
 * - Edit existing prompts
 * - Delete prompts from conversation
 * - Use quick presets
 */

import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Divider,
  Group,
  Modal,
  Stack,
  Tabs,
  Text,
  TextInput,
  Textarea,
  ThemeIcon,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconBook,
  IconCheck,
  IconEdit,
  IconPlus,
  IconSettings,
  IconTrash,
  IconWand
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';

interface SystemPrompt {
  id: string;
  title?: string;
  name?: string;
  description?: string;
  content?: string;
  system_prompt?: string;
  tags?: string[];
  is_active?: boolean;
}

interface SystemPromptManagerProps {
  conversationId: string;
  selectedPromptId?: string;
  selectedPromptData?: SystemPrompt | null;
  existingPrompts?: SystemPrompt[]; // Prompts from the conversation
  onPromptSelected?: (prompt: SystemPrompt) => void;
  onPromptsChanged?: (prompts: SystemPrompt[]) => void; // Notify parent of prompt list changes
}

const QUICK_PRESETS = [
  {
    name: 'Code Reviewer',
    description: 'Reviews code for quality, performance, and best practices',
    system_prompt: `You are an expert code reviewer. Your role is to:
1. Assess code quality, clarity, and adherence to best practices
2. Identify performance bottlenecks and optimization opportunities
3. Flag security vulnerabilities
4. Suggest improvements to test coverage
5. Ensure proper documentation

When reviewing:
- Be constructive and educational
- Provide specific, actionable feedback
- Include code examples for improvements
- Explain the reasoning behind suggestions`,
    tags: ['code-review', 'quality'],
  },
  {
    name: 'Document Summarizer',
    description: 'Summarizes documents into concise, actionable summaries',
    system_prompt: `You are an expert document summarizer. Your task is to:
1. Extract the most important information
2. Provide necessary background context
3. Identify recommended actions or next steps
4. Highlight important decisions or conclusions

When summarizing:
- Be concise and clear
- Use bullet points for readability
- Include relevant metrics and dates
- Provide actionable insights`,
    tags: ['summarization', 'documentation'],
  },
  {
    name: 'Technical Writer',
    description: 'Creates clear technical documentation and guides',
    system_prompt: `You are a technical writing expert. Your role is to:
1. Create clear, user-friendly technical documentation
2. Break down complex concepts into simple explanations
3. Provide step-by-step instructions
4. Include relevant examples and use cases
5. Ensure consistency in terminology

When writing:
- Use clear, simple language
- Organize information logically
- Include visuals descriptions when helpful
- Anticipate common questions`,
    tags: ['documentation', 'guides'],
  },
];

export function SystemPromptManager({
  conversationId,
  selectedPromptId,
  selectedPromptData,
  existingPrompts = [],
  onPromptSelected,
  onPromptsChanged,
}: SystemPromptManagerProps) {
  const [prompts, setPrompts] = useState<SystemPrompt[]>(existingPrompts);
  const [managerModalOpen, setManagerModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', system_prompt: '' });
  const [expandedPresetIndex, setExpandedPresetIndex] = useState<number | null>(null);
  const [fromPreset, setFromPreset] = useState(false);

  // Update local prompts when existingPrompts changes
  useEffect(() => {
    setPrompts(existingPrompts);
  }, [existingPrompts]);

  const handleSave = () => {
    if (!formData.name || !formData.system_prompt) {
      notifications.show({
        title: 'Validation Error',
        message: 'Name and prompt content are required',
        color: 'red',
      });
      return;
    }

    let updatedPrompts: SystemPrompt[];

    if (editingPrompt) {
      // Update existing prompt
      updatedPrompts = prompts.map(p =>
        p.id === editingPrompt.id
          ? {
            ...p,
            name: formData.name,
            title: formData.name,
            description: formData.description,
            system_prompt: formData.system_prompt,
            content: formData.system_prompt,
          }
          : p
      );

      notifications.show({
        title: 'Success',
        message: 'Prompt updated successfully',
        color: 'green',
      });
    } else {
      // Create new prompt
      const newPrompt: SystemPrompt = {
        id: `temp-${Date.now()}`,
        name: formData.name,
        title: formData.name,
        description: formData.description,
        system_prompt: formData.system_prompt,
        content: formData.system_prompt,
        tags: [],
        is_active: true,
      };

      updatedPrompts = [newPrompt, ...prompts];

      notifications.show({
        title: 'Success',
        message: 'Prompt created successfully',
        color: 'green',
      });

      // Auto-select the new prompt
      onPromptSelected?.(newPrompt);
    }

    setPrompts(updatedPrompts);
    onPromptsChanged?.(updatedPrompts);
    setEditingPrompt(null);
    setFormData({ name: '', description: '', system_prompt: '' });
    setCreateModalOpen(false);
    if (fromPreset) {
      setFromPreset(false);
      setManagerModalOpen(true);
    }
  };

  const handleDelete = (promptId: string) => {
    if (!confirm('Are you sure you want to delete this prompt from the conversation?')) return;

    const updatedPrompts = prompts.filter(p => p.id !== promptId);
    setPrompts(updatedPrompts);
    onPromptsChanged?.(updatedPrompts);

    notifications.show({
      title: 'Success',
      message: 'Prompt deleted successfully',
      color: 'green',
    });

    // If the deleted prompt was selected, clear selection
    if (selectedPromptId === promptId) {
      onPromptSelected?.(null as any);
    }
  };

  const handleUsePreset = (preset: typeof QUICK_PRESETS[0]) => {
    const tempPrompt: SystemPrompt = {
      id: `temp-${Date.now()}`,
      name: preset.name,
      title: preset.name,
      description: preset.description,
      system_prompt: preset.system_prompt,
      content: preset.system_prompt,
      tags: preset.tags,
      is_active: true,
    };

    const updatedPrompts = [tempPrompt, ...prompts];
    setPrompts(updatedPrompts);
    onPromptsChanged?.(updatedPrompts);

    notifications.show({
      title: 'Preset Selected',
      message: `${preset.name} preset added to conversation`,
      color: 'green',
    });

    onPromptSelected?.(tempPrompt);
    setManagerModalOpen(false);
  };

  return (
    <>
      <Button
        variant="light"
        leftSection={<IconSettings size={16} />}
        onClick={() => setManagerModalOpen(true)}
      >
        Manage System Prompts {prompts.length > 0 && `(${prompts.length})`}
      </Button>

      {/* Manager Modal */}
      <Modal
        opened={managerModalOpen}
        onClose={() => setManagerModalOpen(false)}
        title={
          <Group gap="xs">
            <ThemeIcon size="md" variant="light" color="blue">
              <IconBook size={18} />
            </ThemeIcon>
            <Text fw={600}>System Prompt Manager</Text>
          </Group>
        }
        size="xl"
      >
        <Stack gap="lg">
          <Alert icon={<IconAlertCircle size={16} />} color="blue" variant="light">
            <Text size="sm">
              Manage system prompts for this conversation. Changes will be saved when you update the conversation.
            </Text>
          </Alert>

          <Tabs defaultValue="my-prompts">
            <Tabs.List>
              <Tabs.Tab value="my-prompts" leftSection={<IconBook size={16} />}>
                My Prompts ({prompts.length})
              </Tabs.Tab>
              <Tabs.Tab value="presets" leftSection={<IconWand size={16} />}>
                Quick Presets
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="my-prompts" pt="md">
              <Stack gap="md">
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    {prompts.length === 0 ? 'No prompts yet' : `${prompts.length} prompt${prompts.length !== 1 ? 's' : ''}`}
                  </Text>
                  <Button
                    size="xs"
                    leftSection={<IconPlus size={14} />}
                    onClick={() => {
                      setEditingPrompt(null);
                      setFormData({ name: '', description: '', system_prompt: '' });
                      setCreateModalOpen(true);
                      setManagerModalOpen(false);
                    }}
                  >
                    Create New
                  </Button>
                </Group>

                {prompts.length === 0 ? (
                  <Alert icon={<IconAlertCircle size={16} />} color="gray" variant="light">
                    <Text size="sm">
                      No prompts yet. Create a new prompt or use a preset to get started.
                    </Text>
                  </Alert>
                ) : (
                  <Stack gap="sm">
                    {prompts.map((prompt) => (
                      <Card key={prompt.id} withBorder p="md">
                        <Group justify="space-between" align="flex-start">
                          <div style={{ flex: 1 }}>
                            <Group gap="xs" mb="xs">
                              {selectedPromptId === prompt.id && (
                                <Badge size="sm" leftSection={<IconCheck size={12} />}>
                                  Selected
                                </Badge>
                              )}
                            </Group>
                            <Text fw={600} size="md">
                              {prompt.title || prompt.name}
                            </Text>
                            {prompt.description && (
                              <Text size="sm" c="dimmed" mt={4}>
                                {prompt.description}
                              </Text>
                            )}
                          </div>

                          <Group gap="xs">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              onClick={() => {
                                setEditingPrompt(prompt);
                                setFormData({
                                  name: prompt.name || prompt.title || '',
                                  description: prompt.description || '',
                                  system_prompt: prompt.system_prompt || prompt.content || '',
                                });
                                setCreateModalOpen(true);
                                setManagerModalOpen(false);
                              }}
                            >
                              <IconEdit size={14} />
                            </ActionIcon>
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="red"
                              onClick={() => handleDelete(prompt.id)}
                            >
                              <IconTrash size={14} />
                            </ActionIcon>
                          </Group>
                        </Group>

                        <Group justify="flex-end" mt="sm">
                          <Button
                            size="xs"
                            variant="subtle"
                            onClick={() => onPromptSelected?.(prompt)}
                          >
                            {selectedPromptId === prompt.id ? 'Selected' : 'Select'}
                          </Button>
                        </Group>
                      </Card>
                    ))}
                  </Stack>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="presets" pt="md">
              <Stack gap="md">
                <Text size="sm" c="dimmed">
                  Quick presets to get started
                </Text>

                {QUICK_PRESETS.map((preset, index) => (
                  <Card key={index} withBorder p="md">
                    <Stack gap="sm">
                      <Group justify="space-between" align="flex-start">
                        <div>
                          <Text fw={600} size="md">
                            {preset.name}
                          </Text>
                          <Text size="sm" c="dimmed" mt={4}>
                            {preset.description}
                          </Text>
                        </div>
                        <Button
                          size="xs"
                          variant="light"
                          color="green"
                          leftSection={<IconCheck size={14} />}
                          onClick={() => handleUsePreset(preset)}
                        >
                          Use This
                        </Button>
                      </Group>

                      {expandedPresetIndex === index && (
                        <>
                          <Divider />
                          <Text size="xs" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', background: '#f8f9fa', padding: '8px', borderRadius: '4px' }}>
                            {preset.system_prompt}
                          </Text>
                        </>
                      )}

                      <Button
                        size="xs"
                        variant="subtle"
                        onClick={() => setExpandedPresetIndex(expandedPresetIndex === index ? null : index)}
                      >
                        {expandedPresetIndex === index ? 'Hide' : 'Show'} Prompt
                      </Button>
                    </Stack>
                  </Card>
                ))}
              </Stack>
            </Tabs.Panel>
          </Tabs>
        </Stack>
      </Modal>

      {/* Create/Edit Modal */}
      <Modal
        opened={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          setEditingPrompt(null);
          setFormData({ name: '', description: '', system_prompt: '' });
        }}
        title={
          <Group gap="xs">
            <ThemeIcon size="md" variant="light" color={editingPrompt ? 'blue' : 'green'}>
              {editingPrompt ? <IconEdit size={18} /> : <IconPlus size={18} />}
            </ThemeIcon>
            <Text fw={600}>{editingPrompt ? 'Edit' : 'Create'} System Prompt</Text>
          </Group>
        }
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="Prompt Name"
            placeholder="e.g., SQL Query Expert"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />

          <Textarea
            label="Description (Optional)"
            placeholder="Brief description of what this prompt does"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={2}
          />

          <Textarea
            label="System Prompt"
            placeholder="You are an expert... Your role is to..."
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            rows={10}
            required
            description="Define how the assistant should behave and what it should do"
          />

          <Group justify="flex-end">
            <Button
              variant="subtle"
              onClick={() => {
                setCreateModalOpen(false);
                setEditingPrompt(null);
                setFormData({ name: '', description: '', system_prompt: '' });
                setManagerModalOpen(true);
              }}
            >
              Cancel
            </Button>
            <Button
              color={editingPrompt ? 'blue' : 'green'}
              leftSection={editingPrompt ? <IconEdit size={16} /> : <IconPlus size={16} />}
              onClick={handleSave}
            >
              {editingPrompt ? 'Update' : 'Create'} Prompt
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
