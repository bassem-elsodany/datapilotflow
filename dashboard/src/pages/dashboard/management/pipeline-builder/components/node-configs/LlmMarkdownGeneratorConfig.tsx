/**
 * LLM Markdown Generator Node Configuration
 *
 * Uses AI to intelligently convert and structure content into markdown
 */

import { useState } from 'react';
import { Stack, Text, TextInput, Select, Alert, Button, Center, Loader } from '@mantine/core';
import { IconInfoCircle, IconPlus } from '@tabler/icons-react';
import { useForm } from '@mantine/form';
import { PipelineNode } from '@/api/resources/pipelines';
import { NodeConfigFooter } from './NodeConfigFooter';
import { useGetContentFilters } from '@/api/resources/content-filters';
import { CreateContentFilterModal } from '../modals/CreateContentFilterModal';

interface LlmMarkdownGeneratorConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function LlmMarkdownGeneratorConfig({ node, onSave, onClose }: LlmMarkdownGeneratorConfigProps) {
  const [createFilterModalOpened, setCreateFilterModalOpened] = useState(false);

  const { data: contentFilters, isLoading: filtersLoading } = useGetContentFilters();

  const form = useForm({
    initialValues: {
      name: node.name || 'LLM Markdown Generator',
      llm_content_filter_id: node.config?.llm_content_filter_id || null,
    },
  });

  const handleSave = () => {
    const config = {
      ...form.values,
      configured: true,
    };
    onSave(node.id, config);
    onClose();
  };

  return (
    <div style={{ padding: '1rem' }}>
      <Stack gap="md">
        <Text size="xs" c="dimmed">
          Uses AI to intelligently convert and structure content
        </Text>

        <TextInput
          label="Node Name"
          placeholder="LLM Markdown Generator"
          description="A descriptive name for this node"
          {...form.getInputProps('name')}
        />

        <Alert icon={<IconInfoCircle />} color="yellow" title="Cost Notice">
          <Text size="sm">
            <strong>Note:</strong> Using LLM Content Filters will incur additional costs as each page
            will be processed by an LLM. The cost depends on the model used and number of pages.
          </Text>
        </Alert>

        {filtersLoading ? (
          <Center p="xl">
            <Loader />
          </Center>
        ) : (
          <>
            <Select
              label="LLM Content Filter"
              placeholder="None (skip filtering)"
              description="Select a filter configuration to apply"
              data={[
                { value: '', label: 'None' },
                ...(contentFilters || []).map((filter: any) => ({
                  value: filter.id,
                  label: filter.name,
                })),
              ]}
              value={form.values.llm_content_filter_id || ''}
              onChange={(value) => form.setFieldValue('llm_content_filter_id', value || null)}
              clearable
            />

            {form.values.llm_content_filter_id && (
              <Alert icon={<IconInfoCircle />} color="blue" variant="light">
                <Text size="sm">
                  Content filters use AI to extract only relevant content, removing navigation, ads,
                  footers, and other noise to improve knowledge base quality.
                </Text>
              </Alert>
            )}

            <Button
              variant="light"
              leftSection={<IconPlus />}
              onClick={() => setCreateFilterModalOpened(true)}
            >
              Create New Filter
            </Button>
          </>
        )}

        <NodeConfigFooter onSave={handleSave} onClose={onClose} />
      </Stack>

      {/* Create Content Filter Modal */}
      <CreateContentFilterModal
        opened={createFilterModalOpened}
        onClose={() => setCreateFilterModalOpened(false)}
        onFilterCreated={(filterId) => {
          // Automatically select the newly created filter
          form.setFieldValue('llm_content_filter_id', filterId);
          setCreateFilterModalOpened(false);
        }}
      />
    </div>
  );
}
