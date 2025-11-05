/**
 * System Prompt Manager Component
 *
 * Allows users to:
 * - Create new system prompts
 * - Edit existing prompts
 * - Delete prompts
 * - Use quick presets
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Button,
  TextInput,
  Textarea,
  Stack,
  Group,
  Card,
  Text,
  Badge,
  ActionIcon,
  Alert,
  Tabs,
  ThemeIcon,
  Divider,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconPlus,
  IconEdit,
  IconTrash,
  IconCheck,
  IconX,
  IconAlertCircle,
  IconWand,
  IconBook,
  IconSettings,
} from '@tabler/icons-react';
import { apiUtils } from '@/config';

interface SystemPrompt {
  id: string;
  name: string;
  description?: string;
  system_prompt: string;
  tags: string[];
  is_active: boolean;
  usage_count: number;
  version: number;
}

interface SystemPromptManagerProps {
  conversationId: string;
  selectedPromptId?: string;
  onPromptSelected?: (prompt: SystemPrompt) => void;
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
  onPromptSelected,
}: SystemPromptManagerProps) {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(false);
  const [managerModalOpen, setManagerModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', system_prompt: '' });
  const [expandedPresetIndex, setExpandedPresetIndex] = useState<number | null>(null);
  const [fromPreset, setFromPreset] = useState(false);

  // Load prompts when manager opens
  useEffect(() => {
    if (managerModalOpen && conversationId) {
      loadPrompts();
    }
  }, [managerModalOpen, conversationId]);

  const loadPrompts = async () => {
    if (!conversationId) return;
    try {
      setLoading(true);
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(
        apiUtils.buildApiUrl(`/conversations/${conversationId}/system-prompts?active_only=true`),
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPrompts(data.data || []);
      }
    } catch (error) {
      console.error('Error loading prompts:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to load system prompts',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdate = async () => {
    if (!formData.name.trim() || !formData.system_prompt.trim()) {
      notifications.show({
        title: 'Error',
        message: 'Name and prompt are required',
        color: 'red',
      });
      return;
    }

    // If no conversation ID, we're in conversation creation mode
    // Just store the prompt locally and select it, don't call API
    if (!conversationId) {
      const tempPrompt: SystemPrompt = {
        id: `temp-${Date.now()}`,
        name: formData.name,
        description: formData.description,
        system_prompt: formData.system_prompt,
        tags: [],
        is_active: true,
        usage_count: 0,
        version: 1,
      };

      notifications.show({
        title: 'Success',
        message: 'Prompt saved! It will be created when you create the conversation.',
        color: 'green',
      });
      onPromptSelected?.(tempPrompt);
      setFormData({ name: '', description: '', system_prompt: '' });
      setCreateModalOpen(false);
      if (fromPreset) {
        setFromPreset(false);
        setManagerModalOpen(true);
      }
      return;
    }

    try {
      const token = localStorage.getItem('jwt_token');

      if (editingPrompt) {
        // Update
        const response = await fetch(
          apiUtils.buildApiUrl(`/conversations/${conversationId}/system-prompts/${editingPrompt.id}`),
          {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: formData.name,
              description: formData.description,
              system_prompt: formData.system_prompt,
            }),
          }
        );

        if (response.ok) {
          notifications.show({
            title: 'Success',
            message: 'Prompt updated successfully',
            color: 'green',
          });
          await loadPrompts();
          setEditingPrompt(null);
          setFormData({ name: '', description: '', system_prompt: '' });
          setCreateModalOpen(false);
        }
      } else {
        // Create
        const response = await fetch(
          apiUtils.buildApiUrl(`/conversations/${conversationId}/system-prompts`),
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: formData.name,
              description: formData.description,
              system_prompt: formData.system_prompt,
              tags: [],
            }),
          }
        );

        if (response.ok) {
          const newPrompt = await response.json();
          notifications.show({
            title: 'Success',
            message: 'Prompt created successfully',
            color: 'green',
          });
          onPromptSelected?.(newPrompt.data);
          await loadPrompts();
          setFormData({ name: '', description: '', system_prompt: '' });
          setCreateModalOpen(false);
          if (fromPreset) {
            setFromPreset(false);
            setManagerModalOpen(true);
          }
        }
      }
    } catch (error) {
      console.error('Error saving prompt:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to save prompt',
        color: 'red',
      });
    }
  };

  const handleDelete = async (promptId: string) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return;

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(
        apiUtils.buildApiUrl(`/conversations/${conversationId}/system-prompts/${promptId}`),
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        notifications.show({
          title: 'Success',
          message: 'Prompt deleted successfully',
          color: 'green',
        });
        await loadPrompts();
      }
    } catch (error) {
      console.error('Error deleting prompt:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to delete prompt',
        color: 'red',
      });
    }
  };

  const handleUsePreset = async (preset: typeof QUICK_PRESETS[0]) => {
    // If no conversation ID, we're in conversation creation mode
    // Just select the preset without API call
    if (!conversationId) {
      const tempPrompt: SystemPrompt = {
        id: `temp-${Date.now()}`,
        name: preset.name,
        description: preset.description,
        system_prompt: preset.system_prompt,
        tags: preset.tags,
        is_active: true,
        usage_count: 0,
        version: 1,
      };

      notifications.show({
        title: 'Success',
        message: `${preset.name} preset selected! It will be created when you create the conversation.`,
        color: 'green',
      });
      onPromptSelected?.(tempPrompt);
      setManagerModalOpen(false);
      return;
    }

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(
        apiUtils.buildApiUrl(`/conversations/${conversationId}/system-prompts`),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: preset.name,
            description: preset.description,
            system_prompt: preset.system_prompt,
            tags: preset.tags,
          }),
        }
      );

      if (response.ok) {
        const newPrompt = await response.json();
        notifications.show({
          title: 'Success',
          message: `${preset.name} preset added`,
          color: 'green',
        });
        onPromptSelected?.(newPrompt.data);
        await loadPrompts();
      }
    } catch (error) {
      console.error('Error using preset:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to add preset',
        color: 'red',
      });
    }
  };

  return (
    <>
      <Button
        variant="light"
        leftSection={<IconSettings size={16} />}
        onClick={() => setManagerModalOpen(true)}
        fullWidth
      >
        Manage System Prompts
      </Button>

      <Modal
        opened={managerModalOpen}
        onClose={() => setManagerModalOpen(false)}
        title="System Prompt Manager"
        size="lg"
      >
        <Tabs defaultValue="my-prompts">
          <Tabs.List>
            <Tabs.Tab value="my-prompts">My Prompts ({prompts.length})</Tabs.Tab>
            <Tabs.Tab value="presets">Quick Presets</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="my-prompts" pt="md">
            <Stack gap="md">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  Create and manage custom system prompts for this conversation
                </Text>
                <Button
                  size="sm"
                  leftSection={<IconPlus size={14} />}
                  onClick={() => {
                    setEditingPrompt(null);
                    setFormData({ name: '', description: '', system_prompt: '' });
                    setCreateModalOpen(true);
                  }}
                >
                  New Prompt
                </Button>
              </Group>

              {prompts.length === 0 ? (
                <Alert icon={<IconAlertCircle size={16} />} color="blue" variant="light">
                  No prompts yet. Create one or use a quick preset.
                </Alert>
              ) : (
                <Stack gap="sm">
                  {prompts.map((prompt) => (
                    <Card key={prompt.id} p="md" withBorder>
                      <Group justify="space-between" mb="xs">
                        <div>
                          <Text fw={600} size="sm">{prompt.name}</Text>
                          {prompt.description && (
                            <Text size="xs" c="dimmed">{prompt.description}</Text>
                          )}
                        </div>
                        <Group gap="xs">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="blue"
                            onClick={() => {
                              setEditingPrompt(prompt);
                              setFormData({
                                name: prompt.name,
                                description: prompt.description || '',
                                system_prompt: prompt.system_prompt,
                              });
                              setCreateModalOpen(true);
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

                      <Group gap="xs" mb="sm">
                        {selectedPromptId === prompt.id && (
                          <Badge size="sm" leftSection={<IconCheck size={12} />}>
                            Selected
                          </Badge>
                        )}
                        <Badge size="sm" variant="dot">
                          v{prompt.version}
                        </Badge>
                      </Group>

                      <Text size="xs" c="dimmed" lineClamp={2} mb="sm">
                        {prompt.system_prompt}
                      </Text>

                      <Button
                        size="xs"
                        variant="subtle"
                        onClick={() => onPromptSelected?.(prompt)}
                      >
                        {selectedPromptId === prompt.id ? 'Selected' : 'Select'}
                      </Button>
                    </Card>
                  ))}
                </Stack>
              )}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="presets" pt="md">
            <Stack gap="md">
              <Text size="sm" c="dimmed">
                Quick presets for common use cases. Click "Expand" to view full content, or "Customize & Save" to modify before adding.
              </Text>

              {QUICK_PRESETS.map((preset, index) => (
                <Card key={preset.name} p="md" withBorder>
                  <Group justify="space-between" align="flex-start" mb="xs">
                    <div style={{ flex: 1 }}>
                      <Text fw={600} size="sm">{preset.name}</Text>
                      <Text size="xs" c="dimmed">{preset.description}</Text>
                    </div>
                    <ThemeIcon variant="light" size="lg" radius="md">
                      {preset.name.includes('Code') && <IconSettings size={18} />}
                      {preset.name.includes('Document') && <IconBook size={18} />}
                      {preset.name.includes('Technical') && <IconWand size={18} />}
                    </ThemeIcon>
                  </Group>

                  {/* Preview or Full Content */}
                  <Text size="xs" c="dimmed" mb="sm" style={{ whiteSpace: 'pre-wrap' }}>
                    {expandedPresetIndex === index
                      ? preset.system_prompt
                      : preset.system_prompt.substring(0, 150) + '...'}
                  </Text>

                  <Group gap="xs" mb="sm">
                    {preset.tags.map((tag) => (
                      <Badge key={tag} size="xs" variant="dot">
                        {tag}
                      </Badge>
                    ))}
                  </Group>

                  <Group gap="xs">
                    <Button
                      size="xs"
                      variant="light"
                      onClick={() =>
                        setExpandedPresetIndex(
                          expandedPresetIndex === index ? null : index
                        )
                      }
                    >
                      {expandedPresetIndex === index ? 'Collapse' : 'Expand'}
                    </Button>

                    <Button
                      size="xs"
                      variant="light"
                      color="blue"
                      onClick={() => {
                        setEditingPrompt(null);
                        setFormData({
                          name: preset.name,
                          description: preset.description,
                          system_prompt: preset.system_prompt,
                        });
                        setFromPreset(true);
                        setCreateModalOpen(true);
                      }}
                    >
                      Customize & Save
                    </Button>

                    <Button
                      size="xs"
                      variant="light"
                      onClick={() => handleUsePreset(preset)}
                    >
                      Use as-is
                    </Button>
                  </Group>
                </Card>
              ))}
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Modal>

      <Modal
        opened={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          setEditingPrompt(null);
          if (fromPreset) {
            setFromPreset(false);
            setManagerModalOpen(true);
          }
        }}
        title={editingPrompt ? 'Edit System Prompt' : (fromPreset ? 'Customize Preset' : 'Create System Prompt')}
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="Prompt Name"
            placeholder="e.g., Code Reviewer, Document Summarizer"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.currentTarget.value })}
          />

          <Textarea
            label="Description (Optional)"
            placeholder="Brief description of what this prompt does"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.currentTarget.value })}
            rows={2}
          />

          <Textarea
            label="System Prompt"
            placeholder="Enter the system prompt instructions..."
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.currentTarget.value })}
            rows={6}
            required
          />

          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setCreateModalOpen(false);
                setEditingPrompt(null);
              }}
            >
              Cancel
            </Button>
            <Button
              leftSection={editingPrompt ? <IconCheck size={16} /> : <IconPlus size={16} />}
              onClick={handleCreateOrUpdate}
            >
              {editingPrompt ? 'Update' : 'Create'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
