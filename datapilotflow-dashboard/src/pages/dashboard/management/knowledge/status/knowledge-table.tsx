import { DataTable } from '@/components/data-table';
import { KnowledgeJob, useGetKnowledgeJobs } from '@/hooks/api/knowledge';
import { formatDate } from '@/utilities/date';
import {
  Badge,
  Button,
  Code,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconEye, IconRefresh } from '@tabler/icons-react';
import { DataTableColumn } from 'mantine-datatable';
import { useMemo, useState } from 'react';

type SortableFields = Pick<KnowledgeJob, 'status' | 'upload_timestamp'>;

export function KnowledgeTable() {
  const { data: jobs, isLoading, refetch } = useGetKnowledgeJobs();
  const [selectedJob, setSelectedJob] = useState<KnowledgeJob | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { tabs, filters, sort } = DataTable.useDataTable<SortableFields>({
    sortConfig: {
      direction: 'desc',
      column: 'upload_timestamp',
    },
    tabsConfig: {
      tabs: [
        {
          value: '*',
          label: 'All',
          counter: jobs?.length,
          rightSection: <Loader size="xs" />,
        },
        {
          value: 'completed',
          label: 'Completed',
          color: 'green',
          counter: jobs?.filter(job => job.status === 'completed').length,
          rightSection: <Loader size="xs" color="green" />,
        },
        {
          value: 'processing',
          label: 'Processing',
          color: 'orange',
          counter: jobs?.filter(job => job.status === 'processing' || job.status === 'queued').length,
          rightSection: <Loader size="xs" color="orange" />,
        },
        {
          value: 'failed',
          label: 'Failed',
          color: 'red',
          counter: jobs?.filter(job => job.status === 'failed' || job.status === 'error').length,
          rightSection: <Loader size="xs" color="red" />,
        },
      ],
    },
  });

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];

    return jobs.filter(job => {
      const statusMatch = tabs.value === '*' ||
        (tabs.value === 'completed' && job.status === 'completed') ||
        (tabs.value === 'processing' && (job.status === 'processing' || job.status === 'queued')) ||
        (tabs.value === 'failed' && (job.status === 'failed' || job.status === 'error'));

      return statusMatch;
    });
  }, [jobs, tabs.value]);

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'queued': 'orange',
      'processing': 'blue',
      'completed': 'green',
      'failed': 'red',
      'error': 'red',
    };
    return colors[status] || 'gray';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      'queued': '⏳',
      'processing': '🔄',
      'completed': '✅',
      'failed': '❌',
      'error': '❌',
    };
    return icons[status] || '❓';
  };

  const formatTimeAgo = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';

    const now = Date.now();
    const time = new Date(timestamp).getTime();
    const diff = Math.floor((now - time) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  const columns: DataTableColumn<KnowledgeJob>[] = useMemo(
    () => [
      {
        accessor: 'file_id',
        title: 'Job ID',
        width: 200,
        render: (job) => (
          <Text size="sm" style={{ fontFamily: 'monospace' }}>
            {job.file_id}
          </Text>
        ),
      },
      {
        accessor: 'filename',
        title: 'Filename',
        width: 250,
        render: (job) => (
          <Text truncate="end" size="sm">
            {job.filename || 'Unknown'}
          </Text>
        ),
      },
      {
        accessor: 'job_type',
        title: 'Type',
        width: 120,
        render: (job) => (
          <Badge variant="light" size="sm">
            {job.job_type ? job.job_type.charAt(0).toUpperCase() + job.job_type.slice(1) : 'Knowledge'}
          </Badge>
        ),
      },
      {
        accessor: 'upload_timestamp',
        title: 'Added',
        width: 150,
        sortable: true,
        render: (job) => (
          <Text size="sm" c="dimmed">
            {formatTimeAgo(job.upload_timestamp)}
          </Text>
        ),
      },
      {
        accessor: 'status',
        title: 'Status',
        width: 150,
        sortable: true,
        render: (job) => (
          <Badge
            color={getStatusColor(job.status)}
            variant="light"
            leftSection={getStatusIcon(job.status)}
          >
            {job.status}
          </Badge>
        ),
      },
      {
        accessor: 'message',
        title: 'Message',
        width: 300,
        render: (job) => (
          <Text size="sm" truncate="end">
            {job.status_history && job.status_history.length > 0
              ? job.status_history[job.status_history.length - 1].message
              : job.message || ''}
          </Text>
        ),
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 100,
        render: (job) => (
          <Group gap="xs">
            <Button
              variant="subtle"
              size="xs"
              leftSection={<IconEye size="1rem" />}
              onClick={() => {
                setSelectedJob(job);
                setShowDetails(true);
              }}
            >
              Details
            </Button>
          </Group>
        ),
      },
    ],
    []
  );

  return (
    <>
      <DataTable.Container>
        <DataTable.Title
          title="Knowledge Jobs"
          description="Monitor the status of your knowledge processing jobs"
          actions={
            <Button
              variant="default"
              size="xs"
              leftSection={<IconRefresh size="1rem" />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              Refresh
            </Button>
          }
        />
        <DataTable.Tabs tabs={tabs.tabs} onChange={tabs.change} />
        <DataTable.Filters filters={filters.filters} onClear={filters.clear} />
        <DataTable.Content>
          <DataTable.Table
            minHeight={240}
            noRecordsText={DataTable.noRecordsText('job')}
            recordsPerPageLabel={DataTable.recordsPerPageLabel('jobs')}
            paginationText={DataTable.paginationText('jobs')}
            page={1}
            records={filteredJobs}
            fetching={isLoading}
            onPageChange={() => { }}
            recordsPerPage={10}
            totalRecords={filteredJobs.length}
            onRecordsPerPageChange={() => { }}
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
        title="Job Details"
        size="lg"
      >
        {selectedJob && (
          <Stack gap="md">
            <Paper withBorder p="md">
              <Stack gap="xs">
                <Group>
                  <Text fw={500}>Job ID:</Text>
                  <Text style={{ fontFamily: 'monospace' }}>{selectedJob.file_id}</Text>
                </Group>
                {selectedJob.filename && (
                  <Group>
                    <Text fw={500}>Filename:</Text>
                    <Text>{selectedJob.filename}</Text>
                  </Group>
                )}
                <Group>
                  <Text fw={500}>Status:</Text>
                  <Badge
                    color={getStatusColor(selectedJob.status)}
                    leftSection={getStatusIcon(selectedJob.status)}
                  >
                    {selectedJob.status}
                  </Badge>
                </Group>
                {selectedJob.upload_timestamp && (
                  <Group>
                    <Text fw={500}>Uploaded:</Text>
                    <Text>{formatDate(selectedJob.upload_timestamp)}</Text>
                  </Group>
                )}
                {selectedJob.message && (
                  <Group>
                    <Text fw={500}>Message:</Text>
                    <Text>{selectedJob.message}</Text>
                  </Group>
                )}
              </Stack>
            </Paper>

            {selectedJob.status_history && selectedJob.status_history.length > 0 && (
              <Paper withBorder p="md">
                <Title order={5} mb="md">Status History</Title>
                <Stack gap="xs">
                  {selectedJob.status_history.map((history: any, index: number) => (
                    <Group key={index} justify="space-between">
                      <Badge
                        color={getStatusColor(history.status)}
                        leftSection={getStatusIcon(history.status)}
                      >
                        {history.status}
                      </Badge>
                      <Text size="sm" c="dimmed">
                        {formatDate(history.timestamp)}
                      </Text>
                    </Group>
                  ))}
                </Stack>
              </Paper>
            )}

            {(selectedJob.processing_results || selectedJob.error_details) && (
              <Paper withBorder p="md">
                <Title order={5} mb="md">Details</Title>
                <Code block>
                  {JSON.stringify(
                    selectedJob.processing_results || selectedJob.error_details,
                    null,
                    2
                  )}
                </Code>
              </Paper>
            )}
          </Stack>
        )}
      </Modal>
    </>
  );
}
