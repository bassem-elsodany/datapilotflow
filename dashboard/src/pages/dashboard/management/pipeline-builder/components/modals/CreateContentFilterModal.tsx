/**
 * Create Content Filter Modal
 *
 * Reusable modal for creating LLM content filters
 */

import { Modal, Stack, Alert, Text, TextInput, Textarea, Select, NumberInput, Divider, Group, Button } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconInfoCircle, IconFilter, IconCheck } from '@tabler/icons-react';
import { useGetModelProviders } from '@/api/resources/model-providers';
import { useCreateContentFilter, LLMContentFilterConfigCreate } from '@/api/resources/content-filters';
import { notifications } from '@mantine/notifications';
import { useQueryClient } from '@tanstack/react-query';

interface CreateContentFilterModalProps {
  opened: boolean;
  onClose: () => void;
  onFilterCreated?: (filterId: string) => void;
}

export function CreateContentFilterModal({ opened, onClose, onFilterCreated }: CreateContentFilterModalProps) {
  const queryClient = useQueryClient();
  const { data: providers, isLoading: providersLoading } = useGetModelProviders();
  const createFilter = useCreateContentFilter();

  // Filter for generative providers only
  const generativeProviders = (providers || []).filter(
    (p: any) => p.is_active && p.generative?.enabled
  );

  const form = useForm<Partial<LLMContentFilterConfigCreate>>({
    initialValues: {
      name: '',
      description: '',
      llm_provider_id: '',
      llm_model_name: '',
      temperature: 0,
      max_retries: 3,
      timeout_seconds: 30,
      instruction: `# Content Extraction Instructions

## Objective
Extract all relevant technical documentation content from the page while preserving markdown structure.

## Content to Include

### Headers and Structure
- All headings and subheadings (H1, H2, H3, etc.)
- Maintain hierarchical structure
- Preserve header relationships

### Technical Content
- Paragraphs with technical information
- Code examples and snippets
- Configuration details
- API documentation
- Step-by-step instructions
- Troubleshooting information
- Feature descriptions
- Requirements and prerequisites

## Formatting Requirements
- Keep the content structure intact
- Preserve markdown formatting
- Maintain header hierarchy
- Use proper markdown syntax

## Content to Exclude
- Navigation elements
- Advertisements
- Unrelated content
- Footer information
- Sidebar content`,
    },
    validate: {
      name: (value) => (!value?.trim() ? 'Name is required' : null),
      llm_provider_id: (value) => (!value ? 'LLM provider is required' : null),
      llm_model_name: (value) => (!value ? 'Model name is required' : null),
    },
  });

  const handleSubmit = async (values: Partial<LLMContentFilterConfigCreate>) => {
    try {
      const result = await createFilter.mutateAsync(values as LLMContentFilterConfigCreate);

      notifications.show({
        title: 'Success',
        message: 'Content filter created successfully',
        color: 'green',
        icon: <IconCheck />,
      });

      // Invalidate content filters query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['content-filters'] });

      // Call the callback with the new filter ID
      if (onFilterCreated && result.id) {
        onFilterCreated(result.id);
      }

      form.reset();
      onClose();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error?.message || 'Failed to create content filter',
        color: 'red',
      });
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={() => {
        form.reset();
        onClose();
      }}
      title={
        <Group gap="sm">
          <IconFilter size={20} color="var(--mantine-color-blue-6)" />
          <Text fw={600} size="sm">Create Content Filter</Text>
        </Group>
      }
      centered
      size="xl"
      radius="md"
      shadow="xl"
      styles={{
        header: {
          backgroundColor: 'var(--mantine-color-blue-0)',
          borderBottom: '1px solid var(--mantine-color-blue-2)',
          paddingBottom: '16px',
          marginBottom: '16px',
        },
        body: {
          maxHeight: '85vh',
          overflowY: 'auto',
        },
      }}
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="md">
          <Alert icon={<IconInfoCircle />} color="yellow">
            <Text size="sm">
              <strong>Cost Notice:</strong> Using LLM Content Filters will process each crawled page through an LLM,
              incurring additional API costs based on the model and page count.
            </Text>
          </Alert>

          <TextInput
            label="Filter Name"
            placeholder="e.g., Documentation Content Filter"
            required
            {...form.getInputProps('name')}
          />

          <Textarea
            label="Description"
            placeholder="Describe what this filter does (optional)"
            minRows={2}
            {...form.getInputProps('description')}
          />

          <Divider label={<Text size="xs" c="dimmed">LLM Configuration</Text>} labelPosition="center" />

          {!providersLoading && generativeProviders.length === 0 && (
            <Alert icon={<IconInfoCircle />} color="orange" title="No LLM Providers Available">
              <Text size="sm">
                You need to configure at least one LLM provider with generative capabilities before creating content filters.
              </Text>
            </Alert>
          )}

          <Select
            label="LLM Provider"
            placeholder={generativeProviders.length === 0 ? "No providers available" : "Select a provider"}
            required
            description="Only active LLM providers with generative capabilities are shown"
            data={generativeProviders.map((provider: any) => ({
              value: provider.id,
              label: provider.name,
            }))}
            {...form.getInputProps('llm_provider_id')}
            disabled={providersLoading || generativeProviders.length === 0}
            searchable
          />

          {form.values.llm_provider_id && (
            <Select
              label="Model Name"
              placeholder="Select a model"
              required
              data={(() => {
                const provider = generativeProviders?.find((p: any) => p.id === form.values.llm_provider_id);
                return provider?.generative?.models?.map((model: string) => ({
                  value: model,
                  label: model,
                })) || [];
              })()}
              {...form.getInputProps('llm_model_name')}
              searchable
            />
          )}

          <Divider label={<Text size="xs" c="dimmed">Advanced Settings</Text>} labelPosition="center" />

          <Group grow>
            <NumberInput
              label="Temperature"
              placeholder="0.0"
              min={0}
              max={2}
              step={0.1}
              decimalScale={1}
              description="LLM temperature (0 = deterministic)"
              {...form.getInputProps('temperature')}
            />

            <NumberInput
              label="Max Retries"
              placeholder="3"
              min={1}
              max={10}
              description="Maximum number of API retries"
              {...form.getInputProps('max_retries')}
            />

            <NumberInput
              label="Timeout (seconds)"
              placeholder="30"
              min={10}
              max={300}
              description="API call timeout"
              {...form.getInputProps('timeout_seconds')}
            />
          </Group>

          <Divider label={<Text size="xs" c="dimmed">Filtering Instructions</Text>} labelPosition="center" />

          <Stack gap="xs">
            <Text size="sm" c="dimmed">
              Choose a template or write custom instructions for content filtering:
            </Text>

            <Select
              label="Instruction Template"
              placeholder="Select a template or choose 'Custom'"
              data={[
                { value: 'technical-docs', label: '📚 Technical Documentation' },
                { value: 'api-reference', label: '🔌 API Reference & Guides' },
                { value: 'tutorial-content', label: '🎓 Tutorials & How-to Guides' },
                { value: 'release-notes', label: '📋 Release Notes & Changelogs' },
                { value: 'troubleshooting', label: '🔧 Troubleshooting & FAQ' },
                { value: 'blog-articles', label: '✍️ Blog Articles & Posts' },
                { value: 'product-docs', label: '📦 Product Documentation' },
                { value: 'custom', label: '✏️ Custom Instructions' }
              ]}
              onChange={(value) => {
                if (!value || value === 'custom') return;

                const templates: Record<string, string> = {
                  'technical-docs': `# Technical Documentation Extraction

## Objective
Extract all relevant technical documentation content while preserving markdown structure.

## Content to Include

### Headers and Structure
- All headings and subheadings (H1, H2, H3, etc.)
- Maintain hierarchical structure
- Preserve header relationships

### Technical Content
- Paragraphs with technical information
- Code examples and snippets
- Configuration details
- API documentation
- Step-by-step instructions
- Troubleshooting information
- Feature descriptions
- Requirements and prerequisites

## Formatting Requirements
- Keep the content structure intact
- Preserve markdown formatting
- Maintain header hierarchy
- Use proper markdown syntax

## Content to Exclude
- Navigation elements
- Advertisements
- Unrelated content
- Footer information
- Sidebar content`,

                  'api-reference': `# API Reference Extraction

## Objective
Extract API documentation including endpoints, methods, parameters, and examples.

## Content to Include

### API Endpoints
- Endpoint paths and URLs
- HTTP methods (GET, POST, PUT, DELETE, etc.)
- Request parameters (path, query, body)
- Response formats and status codes
- Authentication requirements

### Code Examples
- Request examples in multiple languages
- Response examples
- Error handling examples

### Documentation Elements
- Method descriptions
- Parameter descriptions and types
- Response schema
- Error codes and messages
- Rate limits and quotas

## Formatting Requirements
- Preserve code blocks with language tags
- Maintain parameter tables
- Keep example requests and responses together

## Content to Exclude
- Navigation menus
- Sidebar content
- Footer information
- Advertisements`,

                  'tutorial-content': `# Tutorial & How-to Guide Extraction

## Objective
Extract step-by-step tutorials and educational content.

## Content to Include

### Tutorial Structure
- Tutorial title and description
- Prerequisites and requirements
- Learning objectives
- Step-by-step instructions with numbering

### Educational Content
- Code examples with explanations
- Screenshots and diagrams descriptions
- Tips and best practices
- Common pitfalls and warnings
- Summary and next steps

### Supporting Elements
- Code snippets and commands
- Configuration files
- Expected output examples

## Formatting Requirements
- Maintain step numbering and hierarchy
- Keep code blocks with proper formatting
- Preserve warnings and notes

## Content to Exclude
- Navigation elements
- Author bio sections
- Related articles sidebars
- Comment sections`,

                  'release-notes': `# Release Notes & Changelog Extraction

## Objective
Extract version information, changes, and release notes.

## Content to Include

### Version Information
- Version numbers and dates
- Release type (major, minor, patch)
- Breaking changes highlighted

### Changes Documentation
- New features and enhancements
- Bug fixes and improvements
- Deprecated features
- Security updates
- Performance improvements

### Migration Information
- Upgrade instructions
- Breaking change details
- Migration guides
- Compatibility notes

## Formatting Requirements
- Preserve version hierarchy
- Maintain categorization (features, fixes, etc.)
- Keep code examples for migrations

## Content to Exclude
- Navigation menus
- Download buttons
- Social sharing elements`,

                  'troubleshooting': `# Troubleshooting & FAQ Extraction

## Objective
Extract problem-solution pairs and frequently asked questions.

## Content to Include

### Problem Descriptions
- Error messages and symptoms
- Issue descriptions
- Common problems

### Solutions
- Step-by-step solutions
- Code fixes and workarounds
- Configuration changes
- Commands to run

### FAQ Content
- Questions and answers
- Common misconceptions
- Best practices

## Formatting Requirements
- Keep Q&A pairs together
- Preserve code blocks in solutions
- Maintain problem-solution structure

## Content to Exclude
- Navigation elements
- Search boxes
- "Was this helpful?" sections
- Sidebar content`,

                  'blog-articles': `# Blog Article Extraction

## Objective
Extract blog post content including main article, code examples, and key points.

## Content to Include

### Article Content
- Article title and subtitle
- Author name and date
- Main article body paragraphs
- Headings and subheadings

### Supporting Content
- Code snippets and examples
- Quotes and highlights
- Lists and bullet points
- Key takeaways and conclusions

### Technical Elements
- Code blocks with syntax highlighting
- Configuration examples
- Command-line instructions

## Formatting Requirements
- Preserve markdown formatting
- Keep code blocks intact
- Maintain heading hierarchy

## Content to Exclude
- Navigation menus
- Author bio sidebars
- Related articles sections
- Comment sections
- Social sharing buttons
- Newsletter signup forms`,

                  'product-docs': `# Product Documentation Extraction

## Objective
Extract product features, usage guides, and reference documentation.

## Content to Include

### Feature Documentation
- Feature descriptions and benefits
- Use cases and scenarios
- Configuration options
- Integration guides

### Usage Instructions
- Getting started guides
- Setup and installation
- Configuration steps
- Best practices

### Reference Material
- Settings and options reference
- Command reference
- UI element descriptions
- Keyboard shortcuts

## Formatting Requirements
- Preserve hierarchical structure
- Maintain tables and lists
- Keep screenshots/image descriptions

## Content to Exclude
- Navigation elements
- Pricing information (unless specifically requested)
- Marketing content
- Footer content`
                };

                if (templates[value]) {
                  form.setFieldValue('instruction', templates[value]);
                }
              }}
            />

            <Textarea
              label="Instructions"
              placeholder="Write instructions for the LLM on what content to extract..."
              minRows={10}
              required
              {...form.getInputProps('instruction')}
              description="Customize the instructions above or write your own from scratch"
            />
          </Stack>

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={createFilter.isPending}
              leftSection={<IconCheck size={16} />}
            >
              Create Filter
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
