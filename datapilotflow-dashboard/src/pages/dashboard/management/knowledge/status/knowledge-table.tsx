import { DataTable } from '@/components/data-table';
import { KnowledgeJob, useGetKnowledgeJobs } from '@/hooks/api/knowledge';
import { formatDate } from '@/utilities/date';
import {
  ActionIcon,
  Badge,
  Code,
  Group,
  Modal,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Tooltip,
} from '@mantine/core';
import { IconAlertCircle, IconCheck, IconClock, IconEye, IconFile, IconRefresh, IconX } from '@tabler/icons-react';
import { DataTableColumn } from 'mantine-datatable';
import { useMemo, useState } from 'react';

type SortableFields = Pick<KnowledgeJob, 'status' | 'upload_timestamp'>;

const STATUS_COLOR: Record<string, string> = {
  queued: 'yellow',
  processing: 'blue',
  completed: 'green',
  failed: 'red',
  error: 'red',
};

const STATUS_ICON: Record<string, typeof IconCheck> = {
  queued: IconClock,
  processing: IconRefresh,
  completed: IconCheck,
  failed: IconX,
  error: IconAlertCircle,
};

export function KnowledgeTable() {
  const { data: jobs, isLoading, refetch } = useGetKnowledgeJobs();
  const [selectedJob, setSelectedJob] = useState<KnowledgeJob | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { tabs, filters, sort } = DataTable.useDataTable<SortableFields>({
    sortConfig: { direction: 'desc', column: 'upload_timestamp' },
    tabsConfig: {
      tabs: [
        { value: '*',          label: 'All',        counter: jobs?.length },
        { value: 'completed',  label: 'Completed',  color: 'green',  counter: jobs?.filter(j => j.status === 'completed').length },
        { value: 'processing', label: 'Processing', color: 'blue',   counter: jobs?.filter(j => j.status === 'processing' || j.status === 'queued').length },
        { value: 'failed',     label: 'Failed',     color: 'red',    counter: jobs?.filter(j => j.status === 'failed' || j.status === 'error').length },
      ],
    },
  });

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];
    return jobs.filter(job => {
      if (tabs.value === '*') return true;
      if (tabs.value === 'completed')  return job.status === 'completed';
      if (tabs.value === 'processing') return job.status === 'processing' || job.status === 'queued';
      if (tabs.value === 'failed')     return job.status === 'failed' || job.status === 'error';
      return true;
    });
  }, [jobs, tabs.value]);

  const columns: DataTableColumn<KnowledgeJob>[] = useMemo(() => [
    {
      accessor: 'filename',
      title: 'File',
      render: (job) => (
        <Group gap="sm" wrap="nowrap">
          <ThemeIcon size="md" variant="light" color="blue" radius="sm" style={{ flexShrink: 0 }}>
            <IconFile size={14} />
          </ThemeIcon>
          <div style={{ minWidth: 0 }}>
            <Text size="sm" fw={600} truncate>{job.filename || '—'}</Text>
            <Text size="xs" c="dimmed" ff="monospace" truncate>{job.file_id}</Text>
          </div>
        </Group>
      ),
    },
    {
      accessor: 'job_type',
      title: 'Type',
      width: 120,
      render: (job) => (
        <Badge variant="light" size="sm" radius="sm">
          {job.job_type ? job.job_type.charAt(0).toUpperCase() + job.job_type.slice(1) : 'Knowledge'}
        </Badge>
      ),
    },
    {
      accessor: 'status',
      title: 'Status',
      width: 130,
      sortable: true,
      render: (job) => {
        const Icon = STATUS_ICON[job.status] || IconClock;
        return (
          <Badge
            color={STATUS_COLOR[job.status] || 'gray'}
            variant="dot"
            size="sm"
            leftSection={<Icon size={11} />}
          >
            {job.status}
          </Badge>
        );
      },
    },
    {
      accessor: 'message',
      title: 'Message',
      render: (job) => {
        const msg = job.status_history?.length
          ? job.status_history[job.status_history.length - 1].message
          : job.message || '';
        return (
          <Tooltip label={msg} withArrow multiline maw={320} disabled={!msg || msg.length < 60}>
            <Text size="xs" c="dimmed" lineClamp={2}>{msg || '—'}</Text>
          </Tooltip>
        );
      },
    },
    {
      accessor: 'upload_timestamp',
      title: 'Added',
      width: 160,
      sortable: true,
      render: (job) => {
        if (!job.upload_timestamp) return <Text size="xs" c="dimmed">—</Text>;
        const d = new Date(job.upload_timestamp);
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
      width: 48,
      textAlign: 'right',
      render: (job) => (
        <Tooltip label="View details" withArrow>
          <ActionIcon
            variant="subtle"
            size="sm"
            onClick={() => { setSelectedJob(job); setShowDetails(true); }}
          >
            <IconEye size={14} />
          </ActionIcon>
        </Tooltip>
      ),
    },
  ], []);

  return (
    <>
      <DataTable.Container>
        <DataTable.Title
          title="Knowledge Jobs"
          description="Monitor the status of your knowledge processing jobs"
          actions={
            <ActionIcon variant="subtle" size="sm" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={14} />
            </ActionIcon>
          }
        />
        <DataTable.Tabs tabs={tabs.tabs} onChange={tabs.change} />
        <DataTable.Filters filters={filters.filters} onClear={filters.clear} />
        <DataTable.Content>
          <DataTable.Table
            striped
            highlightOnHover
            minHeight={240}
            noRecordsText={DataTable.noRecordsText('jobs')}
            recordsPerPageLabel={DataTable.recordsPerPageLabel('jobs')}
            paginationText={DataTable.paginationText('jobs')}
            page={1}
            records={filteredJobs}
            fetching={isLoading}
            onPageChange={() => {}}
            recordsPerPage={10}
            totalRecords={filteredJobs.length}
            onRecordsPerPageChange={() => {}}
            recordsPerPageOptions={[5, 10, 20]}
            sortStatus={sort.status}
            onSortStatusChange={sort.change}
            columns={columns}
          />
        </DataTable.Content>
      </DataTable.Container>

      <Modal
        opened={showDetails}
        onClose={() => setShowDetails(false)}
        title={
          <Group gap="xs">
            <ThemeIcon size="sm" variant="light" color="blue" radius="sm">
              <IconEye size={12} />
            </ThemeIcon>
            <Text size="sm" fw={600}>Job Details</Text>
          </Group>
        }
        size="lg"
      >
        {selectedJob && (
          <Stack gap="md">
            <Paper withBorder p="md" radius="md">
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Job ID</Text>
                  <Text size="xs" ff="monospace">{selectedJob.file_id}</Text>
                </Group>
                {selectedJob.filename && (
                  <Group justify="space-between">
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Filename</Text>
                    <Text size="xs">{selectedJob.filename}</Text>
                  </Group>
                )}
                <Group justify="space-between">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Status</Text>
                  <Badge color={STATUS_COLOR[selectedJob.status] || 'gray'} variant="dot" size="sm">
                    {selectedJob.status}
                  </Badge>
                </Group>
                {selectedJob.upload_timestamp && (
                  <Group justify="space-between">
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Uploaded</Text>
                    <Text size="xs">{formatDate(selectedJob.upload_timestamp)}</Text>
                  </Group>
                )}
                {selectedJob.message && (
                  <Group justify="space-between" align="flex-start">
                    <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Message</Text>
                    <Text size="xs" style={{ maxWidth: '70%', textAlign: 'right' }}>{selectedJob.message}</Text>
                  </Group>
                )}
              </Stack>
            </Paper>

            {selectedJob.status_history && selectedJob.status_history.length > 0 && (
              <Paper withBorder p="md" radius="md">
                <Title order={6} mb="sm">Status History</Title>
                <Stack gap={4}>
                  {selectedJob.status_history.map((history: any, index: number) => (
                    <Group key={index} justify="space-between">
                      <Badge color={STATUS_COLOR[history.status] || 'gray'} variant="dot" size="sm">
                        {history.status}
                      </Badge>
                      <Text size="xs" c="dimmed">{formatDate(history.timestamp)}</Text>
                    </Group>
                  ))}
                </Stack>
              </Paper>
            )}

            {(selectedJob.processing_results || selectedJob.error_details) && (
              <Paper withBorder p="md" radius="md">
                <Title order={6} mb="sm">Details</Title>
                <Code block style={{ fontSize: 11 }}>
                  {JSON.stringify(selectedJob.processing_results || selectedJob.error_details, null, 2)}
                </Code>
              </Paper>
            )}
          </Stack>
        )}
      </Modal>
    </>
  );
}
