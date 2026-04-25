import { useCancelKnowledgeJob, useExecuteKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { DataTable } from '@/components/data-table';
import { JobWithStatus, useGetJobsWithStatus, useGetJobTimeline } from '@/hooks/api/job-status';
import { paths } from '@/routes/paths';
import { formatDate } from '@/utilities/date';
import {
  ActionIcon,
  Alert,
  Badge,
  Code,
  Group,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  Timeline,
  Title,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconEye,
  IconFileText,
  IconPlayerPause,
  IconPlayerPlay,
  IconPlayerStop,
  IconRefresh,
  IconRocket,
  IconX,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { DataTableColumn } from 'mantine-datatable';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

type SortableFields = Pick<JobWithStatus, 'name' | 'last_execution'>;

const STATUS_COLOR: Record<string, string> = {
  created: 'cyan',
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};

const STATUS_ICON: Record<string, typeof IconCheck> = {
  created: IconClock,
  pending: IconPlayerPause,
  running: IconRefresh,
  completed: IconCheck,
  failed: IconX,
  cancelled: IconPlayerStop,
};

function JobTimelineModal({ jobId }: { jobId: string }) {
  const { data: entries, isLoading } = useGetJobTimeline(jobId);

  if (isLoading) {
    return (
      <Group justify="center" p="xl">
        <Loader size="sm" type="dots" />
        <Text size="sm" c="dimmed">Loading timeline…</Text>
      </Group>
    );
  }

  if (!entries || entries.length === 0) {
    return <Text size="sm" c="dimmed" ta="center" py="xl">No timeline entries found.</Text>;
  }

  return (
    <ScrollArea h={420}>
      <Timeline active={entries.length - 1} bulletSize={28} lineWidth={2}>
        {entries.map((entry) => {
          const Icon = STATUS_ICON[entry.status] || IconClock;
          const color = STATUS_COLOR[entry.status] || 'gray';
          return (
            <Timeline.Item
              key={entry.id}
              bullet={
                <ThemeIcon size={28} radius="xl" variant="light" color={color}>
                  <Icon size={14} />
                </ThemeIcon>
              }
              title={
                <Group gap="xs">
                  <Badge color={color} variant="light" size="sm" radius="sm">{entry.status}</Badge>
                  <Text size="xs" c="dimmed">{formatDate(entry.created_at)}</Text>
                </Group>
              }
            >
              <Paper withBorder p="xs" mt={4} radius="sm">
                <Stack gap={4}>
                  {(entry.documents_processed > 0 || entry.chunks_created > 0) && (
                    <Group gap="md">
                      <Group gap={4}>
                        <IconFileText size={12} />
                        <Text size="xs">{entry.documents_processed} docs</Text>
                      </Group>
                      <Group gap={4}>
                        <IconCpu size={12} />
                        <Text size="xs">{entry.chunks_created} chunks</Text>
                      </Group>
                      {entry.processing_time_seconds > 0 && (
                        <Group gap={4}>
                          <IconClock size={12} />
                          <Text size="xs">{entry.processing_time_seconds.toFixed(2)}s</Text>
                        </Group>
                      )}
                    </Group>
                  )}
                  {entry.error_message && (
                    <Alert color="red" p="xs" icon={<IconAlertCircle size={14} />}>
                      <Text size="xs">{entry.error_message}</Text>
                    </Alert>
                  )}
                </Stack>
              </Paper>
            </Timeline.Item>
          );
        })}
      </Timeline>
    </ScrollArea>
  );
}

export function RealTimeJobTableImproved() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedJob, setSelectedJob] = useState<JobWithStatus | null>(null);
  const [showTimeline, setShowTimeline] = useState(false);

  const executeJobMutation = useExecuteKnowledgeJob();
  const cancelJobMutation = useCancelKnowledgeJob();

  const { tabs, sort } = DataTable.useDataTable<SortableFields>({
    sortConfig: { direction: 'desc', column: 'last_execution' },
    tabsConfig: {
      tabs: [
        { value: '*',         label: 'All' },
        { value: 'running',   label: 'Running',   color: 'blue' },
        { value: 'completed', label: 'Completed', color: 'green' },
        { value: 'failed',    label: 'Failed',    color: 'red' },
      ],
    },
  });

  const { data: jobs, isLoading, refetch } = useGetJobsWithStatus();

  const tabsWithCounters = useMemo(() => tabs.tabs.map((tab) => ({
    ...tab,
    counter: tab.value === '*'
      ? jobs?.length
      : tab.value === 'running'
      ? jobs?.filter(j => j.is_running).length
      : jobs?.filter(j => (j.current_status?.status || 'created') === tab.value).length,
  })), [jobs, tabs.tabs]);

  const filtered = useMemo(() => {
    if (!jobs) return [];
    if (tabs.value === '*') return jobs;
    if (tabs.value === 'running') return jobs.filter(j => j.is_running);
    return jobs.filter(j => (j.current_status?.status || 'created') === tabs.value);
  }, [jobs, tabs.value]);

  const handleExecute = (jobId: string) => {
    executeJobMutation.mutate({ variables: {} as any, route: { jobId } }, {
      onSuccess: async () => {
        notifications.show({ title: 'Job Started', message: 'Knowledge processing job queued.', color: 'green', icon: <IconRocket size={16} /> });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      },
      onError: async (error: any) => {
        notifications.show({ title: 'Failed', message: error?.response?.data?.detail || 'Could not start job.', color: 'red' });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      },
    });
  };

  const handleCancel = (jobId: string) => {
    cancelJobMutation.mutate({ variables: {} as any, route: { jobId } }, {
      onSuccess: async () => {
        notifications.show({ title: 'Job Cancelled', message: 'Job has been cancelled.', color: 'orange', icon: <IconPlayerStop size={16} /> });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      },
      onError: async () => {
        notifications.show({ title: 'Failed', message: 'Could not cancel job.', color: 'red' });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      },
    });
  };

  const columns: DataTableColumn<JobWithStatus>[] = useMemo(() => [
    {
      accessor: 'name',
      title: 'Job',
      width: 220,
      sortable: true,
      render: (job) => (
        <Stack gap={0}>
          <Group gap={6} wrap="nowrap">
            {job.is_running && <Loader size="xs" type="dots" color="blue" />}
            <Text size="sm" fw={600} truncate>{job.name}</Text>
          </Group>
          {job.description && <Text size="xs" c="dimmed" truncate>{job.description}</Text>}
        </Stack>
      ),
    },
    {
      accessor: 'status',
      title: 'Status',
      width: 120,
      render: (job) => {
        const status = job.current_status?.status || 'created';
        return (
          <Badge color={STATUS_COLOR[status] || 'gray'} variant="light" size="sm" radius="sm">
            {status}
          </Badge>
        );
      },
    },
    {
      accessor: 'progress',
      title: 'Progress',
      width: 160,
      render: (job) => {
        const tl = job.current_status;
        if (!tl) return <Text size="xs" c="dimmed">Not executed</Text>;
        return (
          <Group gap="sm" wrap="nowrap">
            <Group gap={4}>
              <IconFileText size={12} />
              <Text size="xs">{tl.documents_processed} docs</Text>
            </Group>
            <Group gap={4}>
              <IconDatabase size={12} />
              <Text size="xs">{tl.chunks_created} chunks</Text>
            </Group>
          </Group>
        );
      },
    },
    {
      accessor: 'duration',
      title: 'Duration',
      width: 90,
      render: (job) => {
        const tl = job.current_status;
        if (!tl?.started_at) return <Text size="xs" c="dimmed">—</Text>;
        if (!tl.completed_at) return <Badge color="blue" variant="dot" size="sm">Running…</Badge>;
        const secs = (new Date(tl.completed_at).getTime() - new Date(tl.started_at).getTime()) / 1000;
        return <Text size="xs" fw={500}>{secs.toFixed(1)}s</Text>;
      },
    },
    {
      accessor: 'last_execution',
      title: 'Last Run',
      width: 160,
      sortable: true,
      render: (job) => {
        if (!job.last_execution) return <Text size="xs" c="dimmed">Never</Text>;
        const d = new Date(job.last_execution);
        const date = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' });
        const time = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        return (
          <Stack gap={0}>
            <Text size="xs" fw={500}>{date}</Text>
            <Text size="xs" c="dimmed">{time}</Text>
          </Stack>
        );
      },
    },
    {
      accessor: 'actions',
      title: '',
      width: 100,
      textAlign: 'right',
      render: (job) => {
        const status = job.current_status?.status || 'created';
        const canRun = !job.is_running;
        const canCancel = job.is_running;
        const canRetry = status === 'failed' || status === 'cancelled';
        return (
          <Group gap={4} wrap="nowrap" justify="flex-end">
            <Tooltip label="View details" withArrow>
              <ActionIcon variant="subtle" size="sm" onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}>
                <IconEye size={14} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="View timeline" withArrow>
              <ActionIcon variant="subtle" size="sm" onClick={() => { setSelectedJob(job); setShowTimeline(true); }}>
                <IconClock size={14} />
              </ActionIcon>
            </Tooltip>
            {canCancel && (
              <Tooltip label="Cancel job" withArrow>
                <ActionIcon variant="subtle" color="orange" size="sm" onClick={() => handleCancel(job.id)} loading={cancelJobMutation.isPending}>
                  <IconPlayerStop size={14} />
                </ActionIcon>
              </Tooltip>
            )}
            {canRun && !canRetry && (
              <Tooltip label="Run job" withArrow>
                <ActionIcon variant="subtle" color="green" size="sm" onClick={() => handleExecute(job.id)} loading={executeJobMutation.isPending}>
                  <IconPlayerPlay size={14} />
                </ActionIcon>
              </Tooltip>
            )}
            {canRetry && (
              <Tooltip label="Retry job" withArrow>
                <ActionIcon variant="subtle" color="violet" size="sm" onClick={() => handleExecute(job.id)} loading={executeJobMutation.isPending}>
                  <IconRefresh size={14} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        );
      },
    },
  ], [executeJobMutation.isPending, cancelJobMutation.isPending]);

  return (
    <>
      <DataTable.Container>
        <DataTable.Title
          title="Knowledge Jobs"
          description="Monitor and manage your knowledge processing jobs"
          actions={
            <ActionIcon variant="subtle" size="sm" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={14} />
            </ActionIcon>
          }
        />
        <DataTable.Tabs tabs={tabsWithCounters} onChange={tabs.change} />
        <DataTable.Content>
          <DataTable.Table
            striped
            highlightOnHover
            minHeight={240}
            noRecordsText={DataTable.noRecordsText('jobs')}
            recordsPerPageLabel={DataTable.recordsPerPageLabel('jobs')}
            paginationText={DataTable.paginationText('jobs')}
            page={1}
            records={filtered}
            fetching={isLoading}
            onPageChange={() => {}}
            recordsPerPage={10}
            totalRecords={filtered.length}
            onRecordsPerPageChange={() => {}}
            recordsPerPageOptions={[5, 10, 20]}
            sortStatus={sort.status}
            onSortStatusChange={sort.change}
            columns={columns}
          />
        </DataTable.Content>
      </DataTable.Container>

      <Modal
        opened={showTimeline}
        onClose={() => setShowTimeline(false)}
        title={
          <Group gap="xs">
            <ThemeIcon size="sm" variant="light" color="blue" radius="sm">
              <IconClock size={12} />
            </ThemeIcon>
            <Text size="sm" fw={600}>{selectedJob?.name} — Timeline</Text>
          </Group>
        }
        size="lg"
      >
        {selectedJob && (
          <Stack gap="md">
            <Paper withBorder p="sm" radius="sm">
              <Group gap="md" wrap="nowrap">
                <Stack gap={2} style={{ flex: 1 }}>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Job</Text>
                  <Text size="sm" fw={500}>{selectedJob.name}</Text>
                </Stack>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Status</Text>
                  <Badge color={STATUS_COLOR[selectedJob.current_status?.status || 'created']} variant="light" size="sm" radius="sm">
                    {selectedJob.current_status?.status || 'created'}
                  </Badge>
                </Stack>
                {selectedJob.current_status && (
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Docs / Chunks</Text>
                    <Text size="xs">{selectedJob.current_status.documents_processed} / {selectedJob.current_status.chunks_created}</Text>
                  </Stack>
                )}
              </Group>
            </Paper>
            <Title order={6}>Execution History</Title>
            <JobTimelineModal jobId={selectedJob.id} />
            {selectedJob.current_status?.error_message && (
              <Paper withBorder p="sm" radius="sm">
                <Title order={6} mb="xs">Error Details</Title>
                <Code block style={{ fontSize: 11 }}>
                  {selectedJob.current_status.error_message}
                </Code>
              </Paper>
            )}
          </Stack>
        )}
      </Modal>
    </>
  );
}
