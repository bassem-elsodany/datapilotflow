import { useGetKnowledgeSourceConfigExpanded } from '@/api/resources/knowledge-sources';
import { InfoItem, InfoSectionCard } from '@/components/info-section-card';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { StatCard } from '@/components/stat-card';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Center,
  Code,
  CopyButton,
  Group,
  List,
  Loader,
  Modal,
  ScrollArea,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Tooltip
} from '@mantine/core';
import {
  IconArrowLeft,
  IconCheck,
  IconCode,
  IconCopy,
  IconDatabase,
  IconEdit,
  IconExternalLink,
  IconFile,
  IconFileText,
  IconFilter,
  IconForms,
  IconLink,
  IconRobot,
  IconSearch,
  IconSettings,
  IconUpload,
  IconWorld,
  IconX
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Knowledge Sources', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Configurations', href: paths.dashboard.management.knowledgeSources.configs },
  { label: 'Configuration Details' }
];

export default function ConfigDetailsPage() {
  const { configId } = useParams<{ configId: string }>();
  const [urlsModalOpen, setUrlsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch configuration data with all related data in a single call
  const { data: config, isLoading: configLoading, error: configError } = useGetKnowledgeSourceConfigExpanded(
    configId || '',
    'content_filter,model_provider,url_source'
  );

  // Extract related data from the expanded response
  const contentFilter = config?.content_filter;
  const provider = config?.model_provider;
  const urlSourceData = config?.url_source;

  // Filter URLs based on search query
  const filteredUrls = useMemo(() => {
    if (!urlSourceData?.urls || !searchQuery.trim()) {
      return urlSourceData?.urls || [];
    }
    return urlSourceData.urls.filter((url: string) =>
      url.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [urlSourceData?.urls, searchQuery]);

  if (configLoading) {
    return (
      <Page title="Configuration Details">
        <Center py="xl">
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (configError || !config) {
    return (
      <Page title="Configuration Details">
        <Alert color="red" title="Error">
          Failed to load configuration details.
        </Alert>
      </Page>
    );
  }

  return (
    <Page title="Configuration Details">
      <PageHeader
        title="Configuration Details"
        breadcrumbs={breadcrumbs}
      >
        <Group gap="sm">
          <Button
            component={Link}
            to={paths.dashboard.management.knowledgeSources.configs}
            leftSection={<IconArrowLeft size={16} />}
            variant="light"
          >
            Back to Source List
          </Button>
          <Button
            component={Link}
            to={paths.dashboard.management.knowledgeSources.configEdit(configId || '')}
            leftSection={<IconEdit size={16} />}
            variant="light"
          >
            Edit Configuration
          </Button>
        </Group>
      </PageHeader>

      <Stack gap="xl">
        {/* Hero Header */}
        <Box
          style={{
            background: `linear-gradient(135deg, #45c9bb15 0%, #87cbbc20 100%)`,
            border: '1px solid #45c9bb30',
            borderRadius: '16px',
            padding: '20px',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <Box
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(90deg, #45c9bb 0%, #87cbbc 100%)'
            }}
          />
          <Group justify="space-between" align="flex-start">
            <Stack gap="xs">
              <Text size="24px" fw={700} style={{ color: '#45c9bb' }}>
                {config.name}
              </Text>
              {config.description && (
                <Text size="sm" c="dimmed" style={{ maxWidth: '600px' }}>
                  {config.description}
                </Text>
              )}
              <Group gap="sm" mt={4}>
                <Badge color="green" size="sm" variant="light">
                  Active
                </Badge>
                {config.url && (
                  <Group gap="xs">
                    <Anchor
                      href={config.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      size="xs"
                      style={{ color: '#45c9bb' }}
                    >
                      {config.url}
                    </Anchor>
                    <CopyButton value={config.url}>
                      {({ copied, copy }) => (
                        <Tooltip label={copied ? 'Copied!' : 'Copy URL'}>
                          <ActionIcon variant="subtle" onClick={copy} size="xs">
                            {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </CopyButton>
                    <ActionIcon
                      component="a"
                      href={config.url}
                      target="_blank"
                      variant="subtle"
                      size="xs"
                    >
                      <IconExternalLink size={14} />
                    </ActionIcon>
                  </Group>
                )}
              </Group>
            </Stack>
          </Group>
        </Box>

        {/* Stats Cards - Adapt based on content source type */}
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg">
          <StatCard
            title="Content Source"
            value={config.content_source_type === 'web_scraping' ? 'Web Scraping' : 'Local Files'}
            icon={config.content_source_type === 'web_scraping' ? <IconWorld size={24} /> : <IconFileText size={24} />}
            color="#45c9bb"
            gradientFrom="#45c9bb"
            gradientTo="#87cbbc"
          />
          <StatCard
            title="File Type"
            value={config.scraping_mode ? config.scraping_mode.replace('_', ' ') : 'N/A'}
            icon={<IconFile size={24} />}
            color="#bbe773"
            gradientFrom="#bbe773"
            gradientTo="#9dd245"
            description={config.content_source_type === 'local_files' ? 'Uploaded file type' : 'Scraping mode'}
          />
          {config.content_source_type === 'web_scraping' ? (
            <>
              <StatCard
                title="Crawl Depth"
                value={config.crawl_depth || 0}
                icon={<IconExternalLink size={24} />}
                color="#ddde65"
                gradientFrom="#ddde65"
                gradientTo="#bbe773"
                description="Maximum depth"
              />
              <StatCard
                title="URL Patterns"
                value={config.url_patterns?.length || 0}
                icon={<IconForms size={24} />}
                color="#3bc57d"
                gradientFrom="#3bc57d"
                gradientTo="#45c9bb"
                description="Include/Exclude rules"
              />
            </>
          ) : (
            <>
              <StatCard
                title="Files Uploaded"
                value={config.local_files?.length || 0}
                icon={<IconUpload size={24} />}
                color="#ddde65"
                gradientFrom="#ddde65"
                gradientTo="#bbe773"
                description="Total files"
              />
              <StatCard
                title="Total Size"
                value={`${((config.local_files?.reduce((sum: number, f: any) => sum + f.file_size, 0) || 0) / 1024).toFixed(1)} KB`}
                icon={<IconDatabase size={24} />}
                color="#3bc57d"
                gradientFrom="#3bc57d"
                gradientTo="#45c9bb"
                description="Combined size"
              />
            </>
          )}
        </SimpleGrid>

        {/* Configuration Cards - Adapt based on content source type */}
        {config.content_source_type === 'web_scraping' ? (
          <>
            <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="lg">
              {/* Scraping Configuration */}
              <InfoSectionCard
                title="Scraping Configuration"
                icon={<IconSettings size={20} />}
                color="#45c9bb"
                gradientFrom="#45c9bb"
                gradientTo="#87cbbc"
              >
                <Group gap="md" style={{ flexWrap: 'wrap' }}>
                  <InfoItem label="Mode" value={<Badge color="blue" variant="light">{config.scraping_mode}</Badge>} />
                  <InfoItem label="Crawl Depth" value={config.crawl_depth || 0} />
                </Group>
              </InfoSectionCard>

              {/* Domain Filtering */}
              <InfoSectionCard
                title="Domain Filtering"
                icon={<IconFilter size={20} />}
                color="#bbe773"
                gradientFrom="#bbe773"
                gradientTo="#9dd245"
              >
                <Stack gap="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Allowed Subdomains</Text>
                    {config.allowed_subdomains && config.allowed_subdomains.length > 0 ? (
                      <Group gap="xs">
                        {config.allowed_subdomains.map((subdomain, index) => (
                          <Badge key={index} size="sm" color="green" variant="light">
                            {subdomain}
                          </Badge>
                        ))}
                      </Group>
                    ) : (
                      <Text size="sm" c="dimmed">None</Text>
                    )}
                  </Stack>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Blocked Subdomains</Text>
                    {config.blocked_subdomains && config.blocked_subdomains.length > 0 ? (
                      <Group gap="xs">
                        {config.blocked_subdomains.map((subdomain, index) => (
                          <Badge key={index} size="sm" color="red" variant="light">
                            {subdomain}
                          </Badge>
                        ))}
                      </Group>
                    ) : (
                      <Text size="sm" c="dimmed">None</Text>
                    )}
                  </Stack>
                </Stack>
              </InfoSectionCard>

              {/* Content Extraction */}
              <InfoSectionCard
                title="Content Extraction"
                icon={<IconCode size={20} />}
                color="#ddde65"
                gradientFrom="#ddde65"
                gradientTo="#bbe773"
              >
                <Stack gap="xs">
                  <Text size="xs" c="dimmed" fw={600} tt="uppercase">Target Elements</Text>
                  {config.target_elements && config.target_elements.length > 0 ? (
                    <Group gap="xs">
                      {config.target_elements.map((element, index) => (
                        <Badge key={index} color="blue" variant="light">
                          {element}
                        </Badge>
                      ))}
                    </Group>
                  ) : (
                    <Text size="sm" c="dimmed">No target elements configured</Text>
                  )}
                </Stack>
              </InfoSectionCard>
            </SimpleGrid>

            {/* URL Patterns */}
            {config.url_patterns && config.url_patterns.length > 0 && (
              <InfoSectionCard
                title="URL Patterns"
                icon={<IconForms size={20} />}
                color="#3bc57d"
                gradientFrom="#3bc57d"
                gradientTo="#45c9bb"
              >
                <Stack gap="sm">
                  {config.url_patterns.map((pattern, index) => (
                    <Group key={index} justify="space-between" p="sm" style={{ background: 'var(--mantine-color-gray-0)', borderRadius: '8px' }}>
                      <Code>{pattern.pattern}</Code>
                      <Badge color={pattern.reverse ? "red" : "green"} variant="light" size="sm">
                        {pattern.reverse ? "Exclude" : "Include"}
                      </Badge>
                    </Group>
                  ))}
                </Stack>
              </InfoSectionCard>
            )}
          </>
        ) : (
          /* Local Files Configuration */
          <InfoSectionCard
            title="Uploaded Files"
            icon={<IconFileText size={20} />}
            color="#45c9bb"
            gradientFrom="#45c9bb"
            gradientTo="#87cbbc"
          >
            <Stack gap="sm">
              {config.local_files && config.local_files.length > 0 ? (
                <>
                  {/* Show total file count */}
                  <Text size="xs" c="dimmed">
                    Total files: {config.local_files.length}
                  </Text>

                  {/* Scrollable area - max height shows ~10 items, rest are scrollable */}
                  <ScrollArea h={500} type="auto" scrollbarSize={8}>
                    <Stack gap="sm" pr="sm">
                      {config.local_files.map((file: any, index: number) => (
                        <Group key={index} justify="space-between" p="md" style={{
                          background: 'var(--mantine-color-gray-0)',
                          borderRadius: '8px',
                          border: '1px solid var(--mantine-color-gray-3)'
                        }}>
                          <Group gap="sm">
                            <IconFile size={20} color="var(--mantine-color-blue-6)" />
                            <Stack gap={2}>
                              <Text size="sm" fw={500}>{file.original_filename}</Text>
                              <Text size="xs" c="dimmed">{file.file_path}</Text>
                            </Stack>
                          </Group>
                          <Group gap="md">
                            <Badge color="blue" variant="light" size="sm">
                              {file.file_type.toUpperCase()}
                            </Badge>
                            <Text size="xs" c="dimmed">
                              {(file.file_size / 1024).toFixed(1)} KB
                            </Text>
                          </Group>
                        </Group>
                      ))}
                    </Stack>
                  </ScrollArea>
                </>
              ) : (
                <Text size="sm" c="dimmed">No files uploaded</Text>
              )}
            </Stack>
          </InfoSectionCard>
        )}

        {/* LLM Content Filter & Generation */}
        <InfoSectionCard
          title="LLM Content Filter & Generation"
          icon={<IconRobot size={20} />}
          color="#ae89ae"
          gradientFrom="#ae89ae"
          gradientTo="#87cbbc"
        >
          <Stack gap="lg">
            <Group gap="md" style={{ flexWrap: 'wrap' }}>
              <InfoItem
                label="Output Format"
                value={
                  <Badge color="purple" variant="light">
                    {config.output_format === 'html' ? 'Raw HTML' :
                      config.output_format === 'llm_markdown' ? 'LLM Markdown' : 'Markdown'}
                  </Badge>
                }
              />
              {(config.output_format === 'markdown' || config.output_format === 'llm_markdown') && (
                <InfoItem
                  label="Generation Method"
                  value={
                    <Badge color={config.output_format === 'llm_markdown' ? 'orange' : 'blue'} variant="light">
                      {config.output_format === 'llm_markdown' ? 'LLM-Powered' : 'Standard'}
                    </Badge>
                  }
                />
              )}
              {config.output_format === 'markdown' && (
                <InfoItem
                  label="Filter Threshold"
                  value={config.content_filter_threshold}
                />
              )}
            </Group>

            {config.output_format === 'llm_markdown' ? (
              !config.llm_content_filter_id ? (
                <Text size="sm" c="dimmed">No LLM filtering configured</Text>
              ) : configLoading ? (
                <Center py="md"><Loader size="sm" /></Center>
              ) : contentFilter ? (
                <Stack gap="md">
                  {contentFilter.description && (
                    <InfoItem label="Description" value={contentFilter.description} fullWidth />
                  )}
                  <Group gap="md" style={{ flexWrap: 'wrap' }}>
                    <InfoItem label="Filter Name" value={contentFilter.name} />
                    <InfoItem label="Model" value={contentFilter.llm_model_name} />
                    <InfoItem
                      label="Provider"
                      value={configLoading ? <Loader size="xs" /> : provider ? provider.name : `Provider ID: ${contentFilter.llm_provider_id}`}
                    />
                  </Group>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Instructions</Text>
                    <Text
                      size="sm"
                      c="dimmed"
                      style={{
                        maxHeight: '100px',
                        overflow: 'auto',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        backgroundColor: 'var(--mantine-color-gray-0)',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid var(--mantine-color-gray-2)'
                      }}
                    >
                      {contentFilter.instruction}
                    </Text>
                  </Stack>
                </Stack>
              ) : (
                <Text size="sm" c="dimmed">Failed to load filter details</Text>
              )
            ) : (
              <Text size="sm" c="dimmed">Standard markdown generation - no LLM filtering required</Text>
            )}
          </Stack>
        </InfoSectionCard>

        {/* URL List */}
        {config.url_source_id && (
          <InfoSectionCard
            title="URL List"
            icon={<IconLink size={20} />}
            color="#45c9bb"
            gradientFrom="#45c9bb"
            gradientTo="#3bc57d"
          >
            <Stack gap="md">
              {configLoading ? (
                <Center py="md"><Loader size="sm" /></Center>
              ) : urlSourceData ? (
                <>
                  <Group gap="md" style={{ flexWrap: 'wrap' }}>
                    <InfoItem label="Source File" value={urlSourceData.file_name || 'N/A'} />
                    <InfoItem label="Total URLs" value={urlSourceData.urls?.length || 0} />
                  </Group>
                  <Button
                    variant="light"
                    leftSection={<IconLink size={16} />}
                    onClick={() => setUrlsModalOpen(true)}
                    fullWidth
                  >
                    View All URLs ({urlSourceData?.urls?.length || 0})
                  </Button>
                </>
              ) : (
                <Text size="sm" c="dimmed">No URL source configured</Text>
              )}
            </Stack>
          </InfoSectionCard>
        )}

        {/* Metadata */}
        <InfoSectionCard
          title="Metadata"
          icon={<IconDatabase size={20} />}
          color="#3bc57d"
          gradientFrom="#3bc57d"
          gradientTo="#45c9bb"
        >
          <Group gap="md" style={{ flexWrap: 'wrap' }}>
            <InfoItem label="Configuration ID" value={<Code>{config.id}</Code>} fullWidth />
            <InfoItem
              label="Created"
              value={(() => {
                const date = new Date(config.created_at);
                return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
              })()}
            />
            <InfoItem
              label="Last Updated"
              value={(() => {
                const date = new Date(config.updated_at);
                return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
              })()}
            />
          </Group>
        </InfoSectionCard>
      </Stack>

      {/* URL List Modal */}
      <Modal
        opened={urlsModalOpen}
        onClose={() => setUrlsModalOpen(false)}
        title="URL List"
        size="lg"
        centered
      >
        <Stack gap="md">
          <TextInput
            placeholder="Search URLs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftSection={<IconSearch size={16} />}
            rightSection={
              searchQuery && (
                <ActionIcon variant="subtle" onClick={() => setSearchQuery('')}>
                  <IconX size={16} />
                </ActionIcon>
              )
            }
          />

          <ScrollArea h={400}>
            <List spacing="xs">
              {filteredUrls.map((url: string, index: number) => (
                <List.Item key={index}>
                  <Group justify="space-between">
                    <Anchor
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      size="sm"
                      style={{ flex: 1 }}
                    >
                      {url}
                    </Anchor>
                    <CopyButton value={url}>
                      {({ copied, copy }) => (
                        <Tooltip label={copied ? 'Copied!' : 'Copy URL'}>
                          <ActionIcon variant="subtle" onClick={copy} size="sm">
                            {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </CopyButton>
                  </Group>
                </List.Item>
              ))}
            </List>
          </ScrollArea>

          <Text size="sm" c="dimmed" ta="center">
            Showing {filteredUrls.length} of {urlSourceData?.urls?.length || 0} URLs
          </Text>
        </Stack>
      </Modal>
    </Page>
  );
}
