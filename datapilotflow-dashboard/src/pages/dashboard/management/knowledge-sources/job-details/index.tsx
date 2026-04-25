import { useJobTimelineEntries, useJobTimelineStatistics } from '@/api/resources/job-timelines';
import { useGetKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { useGetModelProviders } from '@/api/resources/model-providers';
import { useGetKnowledgeVectorDBCollection } from '@/api/resources/vectordb-collections';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Button,
  Center,
  Code,
  Divider,
  Grid,
  Group,
  Loader,
  Paper,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  Timeline,
  Tooltip,
} from '@mantine/core';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconEdit,
  IconFileText,
  IconNetwork,
  IconPlayerPlay,
  IconRefresh,
  IconScissors,
  IconSettings,
  IconX,
} from '@tabler/icons-react';
import { Link, useParams } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Processing Jobs', href: paths.dashboard.management.knowledgeSources.jobs },
  { label: 'Job Details' },
];

const statusColors: Record<string, string> = {
  created: 'cyan',
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};

const statusIcons: Record<string, typeof IconCheck> = {
  created: IconCheck,
  pending: IconClock,
  running: IconPlayerPlay,
  completed: IconCheck,
  failed: IconX,
  cancelled: IconAlertCircle,
};

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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Group justify="space-between" gap="xs" wrap="nowrap" py={4}>
      <Text size="xs" c="dimmed" fw={500} style={{ flexShrink: 0 }}>{label}</Text>
      <div style={{ textAlign: 'right' }}>{children}</div>
    </Group>
  );
}

function BoolField({ label, value }: { label: string; value: boolean }) {
  return (
    <Field label={label}>
      <Badge size="sm" variant="dot" color={value ? 'green' : 'gray'}>{value ? 'Yes' : 'No'}</Badge>
    </Field>
  );
}

export default function KnowledgeSourceJobDetails() {
  const { jobId } = useParams<{ jobId: string }>();

  const { data: job, isLoading, error, refetch } = useGetKnowledgeJob(jobId || '', {
    query: { expand: 'document_splitter,vectordb_collection,knowledge_source_config' }
  });
  const { data: configs } = useGetKnowledgeSourceConfigs();
  const { data: modelProviders } = useGetModelProviders();
  const { data: vectordbCollection } = useGetKnowledgeVectorDBCollection(
    job?.vectordb_collection_id || '',
    { enabled: !!job?.vectordb_collection_id }
  );
  const { data: timelineEntries, error: timelineError } = useJobTimelineEntries(jobId || '', { limit: 10 });
  const { data: timelineStats, error: statsError } = useJobTimelineStatistics(jobId || '');

  const getConfigName = (configId: string) =>
    configs?.find(c => c.id === configId)?.name || 'Unknown';

  const getProviderName = (providerId: string) =>
    modelProviders?.find(p => p.id === providerId)?.name || 'Unknown';

  const formatDate = (d: string) => {
    const date = new Date(d);
    return isNaN(date.getTime()) ? '—' : date.toLocaleString();
  };

  if (isLoading) {
    return (
      <Page title="Job Details">
        <PageHeader title="Job Details" breadcrumbs={breadcrumbs} />
        <Center h={200}><Loader size="lg" /></Center>
      </Page>
    );
  }

  if (error || !job) {
    return (
      <Page title="Job Details">
        <PageHeader title="Job Details" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error">{error?.message || 'Job not found'}</Alert>
      </Page>
    );
  }

  const latestStatus = timelineEntries?.length ? timelineEntries[0].status : 'created';
  const StatusIcon = statusIcons[latestStatus] || IconCheck;
  const hasTimeline = !!timelineEntries && !timelineError;
  const hasStats = !!timelineStats && !statsError;

  const latest = timelineEntries?.[0];
  const docsProcessed = latest?.documents_processed ?? 0;
  const chunksCreated = latest?.chunks_created ?? 0;
  const totalExec = timelineStats?.statistics?.total_executions ?? 0;
  const successExec = timelineStats?.statistics?.successful_executions ?? 0;
  const failedExec = timelineStats?.statistics?.failed_executions ?? 0;

  return (
    <Page title={job.name}>
      <PageHeader title={job.name} breadcrumbs={breadcrumbs}>
        <Group gap="sm">
          <Button component={Link} to={paths.dashboard.management.knowledgeSources.jobs} leftSection={<IconArrowLeft size={14} />} variant="subtle" size="sm">
            Back
          </Button>
          <Button variant="subtle" size="sm" leftSection={<IconRefresh size={14} />} onClick={() => refetch()}>
            Refresh
          </Button>
          <Button component={Link} to={`/dashboard/management/knowledge-sources/job-edit/${jobId}`} leftSection={<IconEdit size={14} />} variant="light" size="sm">
            Edit
          </Button>
        </Group>
      </PageHeader>

      <Stack gap="md">
        {/* Summary bar */}
        <Paper withBorder radius="md" p="md">
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <Stack gap={4} style={{ minWidth: 0 }}>
              {job.description && <Text size="sm" c="dimmed" lineClamp={2}>{job.description}</Text>}
              <Group gap="xs" mt={2}>
                <Badge size="sm" leftSection={<StatusIcon size={10} />} color={statusColors[latestStatus]} variant="light">
                  {latestStatus}
                </Badge>
                <Badge size="sm" variant="light" color="gray">
                  {getConfigName(job.knowledge_source_config_id)}
                </Badge>
              </Group>
            </Stack>
            <Link to={`/dashboard/management/knowledge-sources/configs/${job.knowledge_source_config_id}`} style={{ textDecoration: 'none', flexShrink: 0 }}>
              <Button variant="subtle" size="xs" rightSection={<IconSettings size={12} />}>View Config</Button>
            </Link>
          </Group>
        </Paper>

        {/* Stat pills */}
        <Group gap="md" grow>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Documents</Text>
            <Text size="xl" fw={700}>{docsProcessed}</Text>
          </Paper>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Chunks Created</Text>
            <Text size="xl" fw={700}>{chunksCreated}</Text>
          </Paper>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Total Executions</Text>
            <Text size="xl" fw={700}>{totalExec}</Text>
          </Paper>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Successful</Text>
            <Text size="xl" fw={700} c="green">{successExec}</Text>
          </Paper>
          {failedExec > 0 && (
            <Paper withBorder p="md" radius="md">
              <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Failed</Text>
              <Text size="xl" fw={700} c="red">{failedExec}</Text>
            </Paper>
          )}
        </Group>

        {/* Two-column detail grid */}
        <Grid gutter="md">
          {/* Left */}
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Stack gap="md">
              {vectordbCollection && (
                <Section title="Vector Database" icon={<IconDatabase size={12} />}>
                  <Field label="Collection"><Text size="sm" fw={500} truncate>{vectordbCollection.collection_name}</Text></Field>
                  <Field label="Dimension"><Text size="sm">{vectordbCollection.vector_dimension}</Text></Field>
                  <Field label="Provider"><Text size="sm">{getProviderName(vectordbCollection.embedding_model_provider_id)}</Text></Field>
                  <Field label="Model"><Text size="sm">{vectordbCollection.embedding_model_name}</Text></Field>
                  {vectordbCollection.description && (
                    <Field label="Description"><Text size="xs" c="dimmed">{vectordbCollection.description}</Text></Field>
                  )}
                </Section>
              )}

              <Section title="Document Splitting" icon={<IconScissors size={12} />}>
                <Field label="Type">
                  <Badge size="sm" variant="light" color="orange">{job.document_splitter?.splitter_type || 'text'}</Badge>
                </Field>
                {(job.document_splitter?.splitter_type === 'text' || job.document_splitter?.splitter_type === 'document' || !job.document_splitter?.splitter_type) && (
                  <>
                    <Field label="Chunk Size"><Text size="sm">{job.document_splitter?.chunk_size ?? 256} tokens</Text></Field>
                    <Field label="Overlap"><Text size="sm">{job.document_splitter?.chunk_overlap ?? 32} tokens</Text></Field>
                  </>
                )}
                {job.document_splitter?.headers_to_split_on?.length > 0 && (
                  <>
                    <Divider my={6} />
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb={4}>Headers</Text>
                    <Text size="xs" c="dimmed">{job.document_splitter.headers_to_split_on.map(([p, n]: [string, string]) => `${p} (${n})`).join(', ')}</Text>
                  </>
                )}
              </Section>
            </Stack>
          </Grid.Col>

          {/* Right */}
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Stack gap="md">
              <Section title="Processing Settings" icon={<IconCpu size={12} />}>
                <Field label="Batch Size"><Text size="sm">{job.batch_size} documents</Text></Field>
                <BoolField label="Save to File" value={!!job.save_to_file} />
                <BoolField label="Consolidated File" value={!!job.write_consolidated_file} />
                <BoolField label="Clear Collection" value={!!job.clear_collection_before_start} />
                <BoolField label="Check Duplicates" value={!!job.check_duplicates_before_insert} />
              </Section>

              <Section title="Metadata" icon={<IconSettings size={12} />}>
                <Stack gap={2} mb={6}>
                  <Text size="xs" c="dimmed" fw={600} tt="uppercase">Job ID</Text>
                  <Code style={{ fontSize: 11, wordBreak: 'break-all' }}>{job.id}</Code>
                </Stack>
                {job.vectordb_collection_id && (
                  <Stack gap={2} mb={6}>
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">Collection ID</Text>
                    <Code style={{ fontSize: 11, wordBreak: 'break-all' }}>{job.vectordb_collection_id}</Code>
                  </Stack>
                )}
                <Field label="Created"><Text size="xs">{formatDate(job.created_at)}</Text></Field>
                {job.created_by && <Field label="Created By"><Text size="xs">{job.created_by}</Text></Field>}
                {latest?.started_at && <Field label="Last Started"><Text size="xs">{formatDate(latest.started_at)}</Text></Field>}
                {latest?.completed_at && <Field label="Last Completed"><Text size="xs">{formatDate(latest.completed_at)}</Text></Field>}
              </Section>
            </Stack>
          </Grid.Col>
        </Grid>

        {/* Execution Timeline — full width */}
        <Section title="Execution Timeline" icon={<IconClock size={12} />}>
          {hasStats && timelineStats && (
            <Group gap="xs" mb="md">
              <Badge variant="light" color="blue" size="sm">{totalExec} total</Badge>
              <Badge variant="light" color="green" size="sm">{successExec} successful</Badge>
              {failedExec > 0 && <Badge variant="light" color="red" size="sm">{failedExec} failed</Badge>}
            </Group>
          )}

          {hasTimeline && timelineEntries && timelineEntries.length > 0 ? (
            <ScrollArea h={400} scrollbarSize={6}>
              <Timeline active={timelineEntries.length - 1} pr={8}>
                {timelineEntries.map((entry, index) => {
                  const EntryIcon = statusIcons[entry.status] || IconCheck;
                  return (
                    <Timeline.Item
                      key={entry.id}
                      bullet={<EntryIcon size={12} />}
                      color={statusColors[entry.status]}
                      title={
                        <Group gap="xs">
                          <Text size="sm" fw={600}>Execution #{timelineEntries.length - index}</Text>
                          <Badge size="xs" color={statusColors[entry.status]} variant="light">{entry.status}</Badge>
                        </Group>
                      }
                    >
                      <Stack gap={4} mt={4}>
                        <Group gap="md">
                          <Text size="xs" c="dimmed">{entry.documents_processed} docs · {entry.chunks_created} chunks</Text>
                          {entry.processing_time_seconds > 0 && (
                            <Text size="xs" c="dimmed">{entry.processing_time_seconds}s</Text>
                          )}
                        </Group>
                        <Group gap="md">
                          {entry.started_at && (
                            <Tooltip label="Started" withArrow>
                              <Text size="xs" c="dimmed">{formatDate(entry.started_at)}</Text>
                            </Tooltip>
                          )}
                          {entry.completed_at && (
                            <Tooltip label="Completed" withArrow>
                              <Text size="xs" c="dimmed">→ {formatDate(entry.completed_at)}</Text>
                            </Tooltip>
                          )}
                        </Group>
                        {entry.error_message && (
                          <Alert color="red" variant="light" p="xs" mt={4}>
                            <Text size="xs">{entry.error_message}</Text>
                          </Alert>
                        )}
                      </Stack>
                    </Timeline.Item>
                  );
                })}
              </Timeline>
            </ScrollArea>
          ) : (
            <Text size="sm" c="dimmed">No executions yet — run this job to see timeline entries.</Text>
          )}
        </Section>
      </Stack>
    </Page>
  );
}
