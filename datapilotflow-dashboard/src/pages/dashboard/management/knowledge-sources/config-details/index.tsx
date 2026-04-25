import { useGetKnowledgeSourceConfigExpanded } from '@/api/resources/knowledge-sources';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Button,
  Center,
  Code,
  CopyButton,
  Divider,
  Grid,
  Group,
  List,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Tooltip,
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
  IconX,
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

// Reusable section block inside a Paper card
function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Paper withBorder radius="md" p="md">
      <Group gap="xs" mb="sm">
        <ThemeIcon size="sm" variant="light" color="gray" radius="sm">{icon}</ThemeIcon>
        <Text size="xs" fw={700} tt="uppercase" c="dimmed" lts={0.5}>{title}</Text>
      </Group>
      <Divider mb="sm" />
      {children}
    </Paper>
  );
}

// Label + value row
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Group justify="space-between" gap="xs" wrap="nowrap" py={4}>
      <Text size="xs" c="dimmed" fw={500} style={{ flexShrink: 0 }}>{label}</Text>
      <div style={{ textAlign: 'right' }}>{children}</div>
    </Group>
  );
}

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
    <Page title={config.name}>
      <PageHeader title={config.name} breadcrumbs={breadcrumbs}>
        <Group gap="sm">
          <Button component={Link} to={paths.dashboard.management.knowledgeSources.configs} leftSection={<IconArrowLeft size={14} />} variant="subtle" size="sm">
            Back
          </Button>
          <Button component={Link} to={paths.dashboard.management.knowledgeSources.configEdit(configId || '')} leftSection={<IconEdit size={14} />} variant="light" size="sm">
            Edit
          </Button>
        </Group>
      </PageHeader>

      <Stack gap="md">
        {/* Summary header */}
        <Paper withBorder radius="md" p="md">
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <Stack gap={4} style={{ minWidth: 0 }}>
              {config.description && <Text size="sm" c="dimmed" lineClamp={2}>{config.description}</Text>}
              <Group gap="xs" mt={2}>
                <Badge size="sm" variant="dot" color="green">Active</Badge>
                <Badge size="sm" variant="light" color="blue">{config.content_source_type === 'web_scraping' ? 'Web Scraping' : config.content_source_type === 'confluence' ? 'Confluence' : 'Local Files'}</Badge>
                <Badge size="sm" variant="outline" color="gray">{config.scraping_mode?.replace(/_/g, ' ')}</Badge>
              </Group>
            </Stack>
            {config.url && (
              <Group gap={4} wrap="nowrap" style={{ flexShrink: 0 }}>
                <Text size="xs" c="dimmed" truncate style={{ maxWidth: 260 }}>{config.url}</Text>
                <CopyButton value={config.url}>
                  {({ copied, copy }) => (
                    <Tooltip label={copied ? 'Copied!' : 'Copy'} withArrow>
                      <ActionIcon variant="subtle" size="xs" onClick={copy}>
                        {copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
                      </ActionIcon>
                    </Tooltip>
                  )}
                </CopyButton>
                <ActionIcon component="a" href={config.url} target="_blank" variant="subtle" size="xs">
                  <IconExternalLink size={12} />
                </ActionIcon>
              </Group>
            )}
          </Group>
        </Paper>

        {/* Stat pills */}
        <Grid gutter="md">
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Paper withBorder p="md" radius="md">
              <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Source Type</Text>
              <Text size="sm" fw={700}>{config.content_source_type === 'web_scraping' ? 'Web Scraping' : config.content_source_type === 'confluence' ? 'Confluence' : 'Local Files'}</Text>
            </Paper>
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Paper withBorder p="md" radius="md">
              <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Mode</Text>
              <Text size="sm" fw={700}>{config.scraping_mode?.replace(/_/g, ' ') || '—'}</Text>
            </Paper>
          </Grid.Col>
          {config.content_source_type === 'web_scraping' && (
            <>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Crawl Depth</Text>
                  <Text size="xl" fw={700}>{config.crawl_depth ?? '—'}</Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>URL Patterns</Text>
                  <Text size="xl" fw={700}>{config.url_patterns?.length ?? 0}</Text>
                </Paper>
              </Grid.Col>
            </>
          )}
          {config.content_source_type === 'local_files' && (
            <>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Files</Text>
                  <Text size="xl" fw={700}>{config.local_files?.length ?? 0}</Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Total Size</Text>
                  <Text size="sm" fw={700}>{((config.local_files?.reduce((s: number, f: any) => s + f.file_size, 0) || 0) / 1024).toFixed(1)} KB</Text>
                </Paper>
              </Grid.Col>
            </>
          )}
          {config.content_source_type === 'confluence' && (
            <>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Instance</Text>
                  <Text size="sm" fw={700}>{config.confluence_config?.is_cloud_instance ? 'Cloud' : 'Self-Hosted'}</Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <Paper withBorder p="md" radius="md">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Cloud URL</Text>
                  <Text size="xs" fw={600} c={config.confluence_config?.cloud_url ? 'dark' : 'dimmed'} truncate>{config.confluence_config?.cloud_url || 'Not set'}</Text>
                </Paper>
              </Grid.Col>
            </>
          )}
        </Grid>

        {/* Detail sections — two column layout */}
        <Grid gutter="md">
          {/* Left column: source-specific config */}
          <Grid.Col span={{ base: 12, md: 6 }}>
            {config.content_source_type === 'web_scraping' && (
              <Stack gap="md">
                <Section title="Scraping Configuration" icon={<IconSettings size={12} />}>
                  <Field label="Mode"><Badge size="sm" variant="light" color="blue">{config.scraping_mode}</Badge></Field>
                  <Field label="Crawl Depth"><Text size="sm" fw={500}>{config.crawl_depth ?? '—'}</Text></Field>
                </Section>

                <Section title="Domain Filtering" icon={<IconFilter size={12} />}>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Allowed</Text>
                    {config.allowed_subdomains?.length ? (
                      <Group gap={4} wrap="wrap">
                        {config.allowed_subdomains.map((s: string, i: number) => <Badge key={i} size="xs" color="green" variant="light">{s}</Badge>)}
                      </Group>
                    ) : <Text size="xs" c="dimmed">None</Text>}
                    <Divider my={4} />
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Blocked</Text>
                    {config.blocked_subdomains?.length ? (
                      <Group gap={4} wrap="wrap">
                        {config.blocked_subdomains.map((s: string, i: number) => <Badge key={i} size="xs" color="red" variant="light">{s}</Badge>)}
                      </Group>
                    ) : <Text size="xs" c="dimmed">None</Text>}
                  </Stack>
                </Section>

                <Section title="Content Extraction" icon={<IconCode size={12} />}>
                  <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb={6}>Target Elements</Text>
                  {config.target_elements?.length ? (
                    <Group gap={4} wrap="wrap">
                      {config.target_elements.map((el: string, i: number) => <Badge key={i} size="xs" variant="light">{el}</Badge>)}
                    </Group>
                  ) : <Text size="xs" c="dimmed">None configured</Text>}
                </Section>

                {config.url_patterns?.length > 0 && (
                  <Section title="URL Patterns" icon={<IconForms size={12} />}>
                    <Stack gap={6}>
                      {config.url_patterns.map((p: any, i: number) => (
                        <Group key={i} justify="space-between" px="xs" py={6} style={{ background: 'var(--mantine-color-gray-0)', borderRadius: 6 }}>
                          <Code style={{ fontSize: 11 }}>{p.pattern}</Code>
                          <Badge size="xs" color={p.reverse ? 'red' : 'green'} variant="light">{p.reverse ? 'Exclude' : 'Include'}</Badge>
                        </Group>
                      ))}
                    </Stack>
                  </Section>
                )}
              </Stack>
            )}

            {config.content_source_type === 'confluence' && (
              <Stack gap="md">
                <Section title="Credentials" icon={<IconSettings size={12} />}>
                  <Field label="Cloud URL"><Text size="xs" ff="monospace" truncate style={{ maxWidth: 200 }}>{config.confluence_config?.cloud_url || '—'}</Text></Field>
                  <Field label="Username"><Text size="sm">{config.confluence_config?.username_or_email || '—'}</Text></Field>
                  <Field label="Instance"><Badge size="sm" variant="light" color="indigo">{config.confluence_config?.is_cloud_instance ? 'Cloud' : 'Self-Hosted'}</Badge></Field>
                </Section>

                <Section title="Extraction" icon={<IconFilter size={12} />}>
                  <Field label="Mode">
                    <Badge size="sm" variant="light" color="indigo">
                      {config.scraping_mode === 'space_pages' ? 'Space Pages' :
                        config.scraping_mode === 'specific_pages' ? 'Specific Pages' :
                        config.scraping_mode === 'pages_with_label' ? 'Pages with Label' :
                        config.scraping_mode === 'recently_modified' ? 'Recently Modified' : config.scraping_mode}
                    </Badge>
                  </Field>
                  {config.confluence_config?.space_keys?.length > 0 && (
                    <>
                      <Divider my={6} />
                      <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb={4}>Spaces</Text>
                      <Group gap={4} wrap="wrap">
                        {config.confluence_config.space_keys.map((s: string, i: number) => <Badge key={i} size="xs" variant="light">{s}</Badge>)}
                      </Group>
                    </>
                  )}
                  {config.confluence_config?.labels?.length > 0 && (
                    <>
                      <Divider my={6} />
                      <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb={4}>Labels</Text>
                      <Group gap={4} wrap="wrap">
                        {config.confluence_config.labels.map((l: string, i: number) => <Badge key={i} size="xs" variant="light">{l}</Badge>)}
                      </Group>
                    </>
                  )}
                </Section>

                <Section title="Processing Options" icon={<IconCode size={12} />}>
                  <Field label="Include Attachments"><Badge size="sm" variant="dot" color={config.confluence_config?.include_attachments ? 'green' : 'gray'}>{config.confluence_config?.include_attachments ? 'Yes' : 'No'}</Badge></Field>
                  <Field label="Include Comments"><Badge size="sm" variant="dot" color={config.confluence_config?.include_comments ? 'green' : 'gray'}>{config.confluence_config?.include_comments ? 'Yes' : 'No'}</Badge></Field>
                  <Field label="Expand Child Pages"><Badge size="sm" variant="dot" color={config.confluence_config?.expand_child_pages ? 'green' : 'gray'}>{config.confluence_config?.expand_child_pages ? 'Yes' : 'No'}</Badge></Field>
                </Section>
              </Stack>
            )}

            {config.content_source_type === 'local_files' && (
              <Section title={`Uploaded Files (${config.local_files?.length ?? 0})`} icon={<IconFileText size={12} />}>
                {config.local_files?.length ? (
                  <ScrollArea h={360} scrollbarSize={6}>
                    <Stack gap={6} pr={4}>
                      {config.local_files.map((file: any, i: number) => (
                        <Group key={i} justify="space-between" px="sm" py={8} style={{ background: 'var(--mantine-color-gray-0)', borderRadius: 6, border: '1px solid var(--mantine-color-gray-2)' }}>
                          <Group gap="sm">
                            <ThemeIcon size="sm" variant="light" color="blue" radius="sm"><IconFile size={11} /></ThemeIcon>
                            <Stack gap={1}>
                              <Text size="xs" fw={500} lineClamp={1}>{file.original_filename}</Text>
                              <Text size="xs" c="dimmed">{(file.file_size / 1024).toFixed(1)} KB</Text>
                            </Stack>
                          </Group>
                          <Badge size="xs" variant="light" color="blue">{file.file_type?.toUpperCase()}</Badge>
                        </Group>
                      ))}
                    </Stack>
                  </ScrollArea>
                ) : <Text size="sm" c="dimmed">No files uploaded</Text>}
              </Section>
            )}
          </Grid.Col>

          {/* Right column: LLM filter + URL list + metadata */}
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Stack gap="md">
              <Section title="LLM Content Filter" icon={<IconRobot size={12} />}>
                <Field label="Output Format">
                  <Badge size="sm" variant="light" color="violet">
                    {config.output_format === 'html' ? 'Raw HTML' : config.output_format === 'llm_markdown' ? 'LLM Markdown' : 'Markdown'}
                  </Badge>
                </Field>
                {config.output_format !== 'html' && (
                  <Field label="Generation">
                    <Badge size="sm" variant="light" color={config.output_format === 'llm_markdown' ? 'orange' : 'blue'}>
                      {config.output_format === 'llm_markdown' ? 'LLM-Powered' : 'Standard'}
                    </Badge>
                  </Field>
                )}
                {config.output_format === 'markdown' && config.content_filter_threshold != null && (
                  <Field label="Filter Threshold"><Text size="sm" fw={500}>{config.content_filter_threshold}</Text></Field>
                )}
                {config.output_format === 'llm_markdown' && contentFilter && (
                  <>
                    <Divider my={8} />
                    <Field label="Filter"><Text size="sm" fw={500}>{contentFilter.name}</Text></Field>
                    <Field label="Model"><Text size="sm">{contentFilter.llm_model_name}</Text></Field>
                    <Field label="Provider"><Text size="sm">{provider?.name || `ID: ${contentFilter.llm_provider_id}`}</Text></Field>
                    {contentFilter.instruction && (
                      <>
                        <Divider my={8} />
                        <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb={4}>Instructions</Text>
                        <ScrollArea h={90} scrollbarSize={6}>
                          <Text size="xs" c="dimmed" style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', lineHeight: 1.5 }}>
                            {contentFilter.instruction}
                          </Text>
                        </ScrollArea>
                      </>
                    )}
                  </>
                )}
                {config.output_format === 'llm_markdown' && !contentFilter && !config.llm_content_filter_id && (
                  <Text size="xs" c="dimmed" mt={4}>No LLM filter configured</Text>
                )}
              </Section>

              {config.url_source_id && (
                <Section title="URL List" icon={<IconLink size={12} />}>
                  {urlSourceData ? (
                    <Stack gap="sm">
                      <Field label="Source File"><Text size="sm">{urlSourceData.file_name || '—'}</Text></Field>
                      <Field label="Total URLs"><Text size="sm" fw={600}>{urlSourceData.urls?.length ?? 0}</Text></Field>
                      <Button size="xs" variant="light" leftSection={<IconLink size={12} />} onClick={() => setUrlsModalOpen(true)}>
                        View All URLs ({urlSourceData.urls?.length ?? 0})
                      </Button>
                    </Stack>
                  ) : <Text size="xs" c="dimmed">No URL source configured</Text>}
                </Section>
              )}

              <Section title="Metadata" icon={<IconDatabase size={12} />}>
                <Stack gap={2} mb={8}>
                  <Text size="xs" c="dimmed" fw={600} tt="uppercase">Config ID</Text>
                  <Code style={{ fontSize: 11, wordBreak: 'break-all' }}>{config.id}</Code>
                </Stack>
                <Field label="Created"><Text size="xs">{new Date(config.created_at).toLocaleString()}</Text></Field>
                <Field label="Updated"><Text size="xs">{new Date(config.updated_at).toLocaleString()}</Text></Field>
              </Section>
            </Stack>
          </Grid.Col>
        </Grid>
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
