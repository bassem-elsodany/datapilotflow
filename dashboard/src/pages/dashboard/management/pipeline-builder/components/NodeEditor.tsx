/**
 * Node Editor Component
 * 
 * Configuration panel for selected pipeline nodes.
 * Provides form fields for customizing node properties.
 */

import { ActionIcon, Button, Group, NumberInput, Paper, SimpleGrid, Stack, Stepper, Text, TextInput, Textarea, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconCheck, IconChevronDown, IconChevronUp, IconSettings, IconX } from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import { Node } from 'reactflow';

interface NodeEditorProps {
  node: Node | null;
  updateNode: (id: string, data: any) => void;
  opened: boolean;
  onClose: () => void;
  onExpandedChange?: (expanded: boolean) => void;
}

export function NodeEditor({ node, updateNode, opened, onClose, onExpandedChange }: NodeEditorProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeStep, setActiveStep] = useState(0);

  // Initialize form with node data
  const form = useForm({
    initialValues: {
      name: node?.data?.name || '',
      description: node?.data?.description || '',
      type: node?.data?.type || '',
      status: node?.data?.status || 'pending',
      url: node?.data?.url || '',
      scraping_mode: node?.data?.scraping_mode || 'website',
      url_source: node?.data?.url_source || { file_name: undefined, urls: [] },
      allowed_subdomains: node?.data?.allowed_subdomains || [],
      blocked_subdomains: node?.data?.blocked_subdomains || [],
      url_patterns: node?.data?.url_patterns || [],
      crawl_depth: node?.data?.crawl_depth || 4,
      css_selector: node?.data?.css_selector || 'main > article',
      css_selector_parts: node?.data?.css_selector_parts || [
        { type: 'main', selector: '' },
        { type: 'article', selector: '' }
      ],
      content_filter_threshold: node?.data?.content_filter_threshold || 0.6,
      chunk_size: node?.data?.chunk_size || 1000,
      chunk_overlap: node?.data?.chunk_overlap || 200,
      batch_size: node?.data?.batch_size || 100,
    },
    validate: {
      name: (value) => (!value ? 'Name is required' : null),
      description: (value) => (!value ? 'Description is required' : null),
      url: (value, values) => {
        if (values.scraping_mode === 'multiple_pages') {
          return null; // URL not required for multiple_pages mode
        }
        return (!value ? 'URL is required' : null);
      },
    },
  });

  const handleStepChange = useCallback((step: number) => {
    setActiveStep(step);
  }, []);

  const handleSubmit = useCallback(() => {
    if (node) {
      const formData = form.values;
      // Mark node as configured with success status
      updateNode(node.id, { ...formData, status: 'completed', configured: true });
      onClose();
    }
  }, [node, form.values, updateNode, onClose]);

  const getStepDescription = useCallback((step: number): string => {
    if (node?.data.type === 'textSplitter') {
      switch (step) {
        case 0: return 'Basic information for the document splitter';
        case 1: return 'Configure document splitting parameters';
        case 2: return 'Review your configuration';
        default: return '';
      }
    } else {
      switch (step) {
        case 0: return 'Basic information for the data source';
        case 1: return 'Configure scraping and content extraction';
        case 2: return 'Set up domain and URL filtering';
        case 3: return 'Review your configuration';
        default: return '';
      }
    }
  }, [node?.data.type]);

  const getTotalSteps = useCallback((): number => {
    if (node?.data.type === 'textSplitter') {
      return 3;
    }
    return 4;
  }, [node?.data.type]);

  if (!node) return null;

  return (
    <Paper
      shadow="xl"
      radius="lg"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        height: isExpanded ? 'auto' : '60px',
        maxHeight: isExpanded ? '80vh' : '60px',
        overflow: 'visible',
        border: '2px solid #45c9bb',
        borderBottom: 'none',
        borderBottomLeftRadius: '0',
        borderBottomRightRadius: '0',
        backgroundColor: '#f8fffe',
        display: 'flex',
        flexDirection: 'column',
        transition: 'height 0.3s ease'
      }}
    >
      <div style={{ padding: '8px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Stack gap="xs" style={{ flex: 1 }}>
          {/* Header */}
          <div style={{
            padding: '8px 0',
            borderBottom: '1px solid #45c9bb',
            backgroundColor: '#f8fffe'
          }}>
            <Group justify="space-between" align="center">
              <Group gap="sm">
                <IconSettings size={18} color="#45c9bb" />
                <div>
                  <Title order={6} style={{ margin: 0, color: '#0f0e0e' }}>
                    Configure {node.data.name}
                  </Title>
                  <Text size="xs" c="dimmed" style={{ marginTop: '1px', color: '#45c9bb' }}>
                    {node.data.type} • {node.data.configured ? 'Configured' : 'Pending'}
                  </Text>
                </div>
              </Group>
              <Group gap="xs">
                <ActionIcon
                  variant="subtle"
                  onClick={() => {
                    const newExpanded = !isExpanded;
                    setIsExpanded(newExpanded);
                    onExpandedChange?.(newExpanded);
                  }}
                  size="sm"
                  style={{
                    color: '#45c9bb',
                    '&:hover': { backgroundColor: '#e6fffa' }
                  }}
                >
                  {isExpanded ? <IconChevronDown size={16} /> : <IconChevronUp size={16} />}
                </ActionIcon>
                <ActionIcon
                  variant="subtle"
                  onClick={onClose}
                  size="sm"
                  style={{
                    color: '#45c9bb',
                    '&:hover': { backgroundColor: '#f8d7da', color: '#721c24' }
                  }}
                >
                  <IconX size={16} />
                </ActionIcon>
              </Group>
            </Group>
          </div>

          {/* Stepper */}
          {isExpanded && (
            <Paper withBorder radius="sm" p="xs" style={{ backgroundColor: '#ffffff', border: '1px solid #45c9bb', flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Stepper
                active={activeStep}
                onStepClick={handleStepChange}
                allowNextStepsSelect={false}
                size="xs"
                color="teal"
                orientation="horizontal"
                styles={{
                  stepIcon: {
                    backgroundColor: '#45c9bb',
                    borderColor: '#45c9bb',
                    color: '#ffffff'
                  },
                  steps: {
                    flexWrap: 'nowrap'
                  }
                }}
              >
                <Stepper.Step
                  label="Basic Info"
                  description={getStepDescription(0)}
                  icon={<IconCheck size={12} />}
                >
                  <Stack gap="xs" style={{}}>
                    <TextInput
                      label="Node Name"
                      placeholder="Enter node name"
                      required
                      size="sm"
                      styles={{
                        input: {
                          borderColor: '#45c9bb',
                          '&:focus': {
                            borderColor: '#45c9bb',
                            boxShadow: '0 0 0 1px #45c9bb'
                          }
                        }
                      }}
                      {...form.getInputProps('name')}
                    />
                    <Textarea
                      label="Description"
                      placeholder="Enter node description"
                      required
                      rows={2}
                      size="sm"
                      styles={{
                        input: {
                          borderColor: '#45c9bb',
                          '&:focus': {
                            borderColor: '#45c9bb',
                            boxShadow: '0 0 0 1px #45c9bb'
                          }
                        }
                      }}
                      {...form.getInputProps('description')}
                    />
                  </Stack>
                </Stepper.Step>

                <Stepper.Step
                  label={node.data.type === 'textSplitter' ? 'Splitter Config' : 'Scraping Config'}
                  description={getStepDescription(1)}
                  icon={<IconCheck size={12} />}
                >
                  {/* Text Splitter Configuration */}
                  {node.data.type === 'textSplitter' && (
                    <Stack gap="xs" style={{}}>
                      <Title order={7} mb="xs">Document Splitting Configuration</Title>
                      <Text c="dimmed" size="xs" mb="xs">
                        Configure document splitting parameters.
                      </Text>

                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xs">
                        <NumberInput
                          label="Chunk Size (Tokens)"
                          placeholder="256"
                          required
                          size="sm"
                          description="Size of text chunks in tokens. Tokens are the units that language models use to process text. Recommended: 256-512 tokens"
                          min={64}
                          max={4096}
                          {...form.getInputProps('chunk_size')}
                        />

                        <NumberInput
                          label="Chunk Overlap (Tokens)"
                          placeholder="32"
                          required
                          size="sm"
                          description="Overlap between chunks in tokens. Recommended: 10-20% of chunk size"
                          min={0}
                          max={512}
                          {...form.getInputProps('chunk_overlap')}
                        />
                      </SimpleGrid>

                      <NumberInput
                        label="Batch Size"
                        placeholder="100"
                        min={1}
                        max={1000}
                        required
                        size="sm"
                        description="Documents per batch"
                        {...form.getInputProps('batch_size')}
                      />
                    </Stack>
                  )}

                  {/* Data Source Configuration */}
                  {(node.data.type === 'website' || node.data.type === 'multiple_pages' || node.data.type === 'single_page' || node.data.type === 'confluence') && (
                    <Stack gap="xs" style={{}}>
                      <Title order={7} mb="xs">Content Extraction Configuration</Title>
                      <Text c="dimmed" size="xs" mb="xs">
                        Configure content extraction settings.
                      </Text>

                      <TextInput
                        label="Target URL"
                        placeholder="https://example.com"
                        required={node.data.type !== 'multiple_pages'}
                        description={node.data.type === 'multiple_pages' ? 'URL not required for multiple pages mode' : 'Enter the URL to scrape'}
                        {...form.getInputProps('url')}
                      />

                      <NumberInput
                        label="Crawl Depth"
                        placeholder="4"
                        min={1}
                        max={10}
                        description="Maximum depth to crawl (1-10)"
                        {...form.getInputProps('crawl_depth')}
                      />

                      <NumberInput
                        label="Content Filter Threshold"
                        placeholder="0.6"
                        min={0}
                        max={1}
                        step={0.1}
                        description="Minimum content quality threshold (0-1)"
                        {...form.getInputProps('content_filter_threshold')}
                      />
                    </Stack>
                  )}
                </Stepper.Step>

                {/* Domain & URL Filtering - Only for data source nodes */}
                {node.data.type !== 'textSplitter' && (
                  <Stepper.Step
                    label="Domain Filtering"
                    description={getStepDescription(2)}
                    icon={<IconCheck size={12} />}
                  >
                    <Stack gap="xs" style={{}}>
                      <Title order={7} mb="xs">Domain & URL Filtering</Title>
                      <Text c="dimmed" size="xs" mb="xs">
                        Configure domain and URL filtering rules.
                      </Text>

                      <Group grow align="flex-start">
                        <div style={{ flex: 1 }}>
                          <Text size="sm" fw={500} mb="xs">Allowed Subdomains</Text>
                          <Text size="xs" c="dimmed" mb="md">
                            Add subdomains to allow for crawling. Leave empty to allow all subdomains.
                          </Text>

                          {form.values.allowed_subdomains.map((domain: string, index: number) => (
                            <Group key={index} mb="xs">
                              <TextInput
                                value={domain}
                                onChange={(e) => {
                                  const newDomains = [...form.values.allowed_subdomains];
                                  newDomains[index] = e.target.value;
                                  form.setFieldValue('allowed_subdomains', newDomains);
                                }}
                                placeholder="example.com"
                                style={{ flex: 1 }}
                              />
                              <ActionIcon
                                color="red"
                                variant="subtle"
                                onClick={() => {
                                  const newDomains = form.values.allowed_subdomains.filter((_: string, i: number) => i !== index);
                                  form.setFieldValue('allowed_subdomains', newDomains);
                                }}
                              >
                                <IconX size={16} />
                              </ActionIcon>
                            </Group>
                          ))}

                          <Button
                            variant="light"
                            size="xs"
                            onClick={() => {
                              form.setFieldValue('allowed_subdomains', [...form.values.allowed_subdomains, '']);
                            }}
                          >
                            Add Domain
                          </Button>
                        </div>

                        <div style={{ flex: 1 }}>
                          <Text size="sm" fw={500} mb="xs">Blocked Subdomains</Text>
                          <Text size="xs" c="dimmed" mb="md">
                            Add subdomains to block from crawling.
                          </Text>

                          {form.values.blocked_subdomains.map((domain: string, index: number) => (
                            <Group key={index} mb="xs">
                              <TextInput
                                value={domain}
                                onChange={(e) => {
                                  const newDomains = [...form.values.blocked_subdomains];
                                  newDomains[index] = e.target.value;
                                  form.setFieldValue('blocked_subdomains', newDomains);
                                }}
                                placeholder="admin.example.com"
                                style={{ flex: 1 }}
                              />
                              <ActionIcon
                                color="red"
                                variant="subtle"
                                onClick={() => {
                                  const newDomains = form.values.blocked_subdomains.filter((_: string, i: number) => i !== index);
                                  form.setFieldValue('blocked_subdomains', newDomains);
                                }}
                              >
                                <IconX size={16} />
                              </ActionIcon>
                            </Group>
                          ))}

                          <Button
                            variant="light"
                            size="xs"
                            onClick={() => {
                              form.setFieldValue('blocked_subdomains', [...form.values.blocked_subdomains, '']);
                            }}
                          >
                            Add Domain
                          </Button>
                        </div>
                      </Group>
                    </Stack>
                  </Stepper.Step>
                )}

                <Stepper.Step
                  label="Review"
                  description={getStepDescription(node.data.type === 'textSplitter' ? 2 : 3)}
                  icon={<IconCheck size={12} />}
                >
                  <Stack gap="xs" style={{}}>
                    <Title order={7} mb="xs">Review Configuration</Title>
                    <Text c="dimmed" size="xs" mb="xs">
                      Review your configuration before applying.
                    </Text>

                    <Paper withBorder p="xs">
                      <Stack gap="xs">
                        <Group>
                          <Text fw={500}>Name:</Text>
                          <Text>{form.values.name}</Text>
                        </Group>
                        <Group>
                          <Text fw={500}>Description:</Text>
                          <Text>{form.values.description}</Text>
                        </Group>
                        <Group>
                          <Text fw={500}>Type:</Text>
                          <Text>{form.values.type}</Text>
                        </Group>

                        {node.data.type === 'textSplitter' && (
                          <>
                            <Group>
                              <Text fw={500}>Chunk Size:</Text>
                              <Text>{form.values.chunk_size}</Text>
                            </Group>
                            <Group>
                              <Text fw={500}>Chunk Overlap:</Text>
                              <Text>{form.values.chunk_overlap}</Text>
                            </Group>
                            <Group>
                              <Text fw={500}>Batch Size:</Text>
                              <Text>{form.values.batch_size}</Text>
                            </Group>
                          </>
                        )}

                        {(node.data.type === 'website' || node.data.type === 'multiple_pages' || node.data.type === 'single_page' || node.data.type === 'confluence') && (
                          <>
                            <Group>
                              <Text fw={500}>URL:</Text>
                              <Text>{form.values.url || 'Not specified'}</Text>
                            </Group>
                            <Group>
                              <Text fw={500}>Scraping Mode:</Text>
                              <Text>{form.values.scraping_mode}</Text>
                            </Group>
                            <Group>
                              <Text fw={500}>Crawl Depth:</Text>
                              <Text>{form.values.crawl_depth}</Text>
                            </Group>
                          </>
                        )}
                      </Stack>
                    </Paper>
                  </Stack>
                </Stepper.Step>
              </Stepper>
            </Paper>
          )}

          {/* Action Buttons */}
          {isExpanded && (
            <div style={{
              padding: '8px 0',
              borderTop: '1px solid #45c9bb',
              backgroundColor: '#f8fffe',
              flexShrink: 0
            }}>
              <Group justify="space-between">
                <Group>
                  {activeStep > 0 && (
                    <Button
                      variant="light"
                      onClick={() => handleStepChange(activeStep - 1)}
                      size="xs"
                    >
                      Previous
                    </Button>
                  )}
                </Group>

                <Group>
                  {activeStep < getTotalSteps() - 1 ? (
                    <Button
                      onClick={() => handleStepChange(activeStep + 1)}
                      size="xs"
                      color="teal"
                    >
                      Next
                    </Button>
                  ) : (
                    <Button
                      onClick={handleSubmit}
                      leftSection={<IconCheck size={12} />}
                      size="xs"
                      color="green"
                      style={{ backgroundColor: '#9dd245', borderColor: '#9dd245' }}
                    >
                      Apply Changes
                    </Button>
                  )}
                </Group>
              </Group>
            </div>
          )}
        </Stack>
      </div>
    </Paper>
  );
}