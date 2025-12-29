import { useLatestJobTimelineEntry } from '@/api/resources/job-timelines';
import { useCancelKnowledgeJob, useExecuteKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { JobWithStatus, useGetJobsWithStatus, useGetJobTimeline } from '@/hooks/api/job-status';
import { formatDate } from '@/utilities/date';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  Select,
  Stack,
  Table,
  Text,
  Timeline,
  Title,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconClock, IconEye, IconPlayerPlay, IconPlayerStop, IconRefresh } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

// Timeline component for job execution history
function JobTimelineComponent({ jobId }: { jobId: string }) {
  const { data: timelineEntries, isLoading } = useGetJobTimeline(jobId);

  if (isLoading) {
    return (
      <Group justify="center" p="md">
        <Loader size="sm" />
        <Text size="sm">Loading timeline...</Text>
      </Group>
    );
  }

  if (!timelineEntries || timelineEntries.length === 0) {
    return (
      <Text size="sm" c="dimmed" ta="center" p="md">
        No timeline entries found
      </Text>
    );
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'created': 'cyan',
      'pending': 'yellow',
      'running': 'blue',
      'completed': 'green',
      'failed': 'red',
      'cancelled': 'gray',
    };
    return colors[status] || 'gray';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ElementType> = {
      'created': IconRefresh,
      'pending': IconRefresh,
      'running': IconPlayerPlay,
      'completed': IconEye,
      'failed': IconEye,
      'cancelled': IconEye,
    };
    const IconComponent = icons[status];
    return IconComponent ? <IconComponent size={16} /> : <IconRefresh size={16} />;
  };

  return (
    <Timeline
      active={timelineEntries.length - 1}
      bulletSize={24}
      lineWidth={2}
    >
      {timelineEntries.map((entry, index) => (
        <Timeline.Item
          key={entry.id}
          bullet={getStatusIcon(entry.status)}
          title={
            <Group gap="xs">
              <Badge
                color={getStatusColor(entry.status)}
                variant="light"
                size="sm"
              >
                {entry.status}
              </Badge>
              <Text size="sm" c="dimmed">
                {formatDate(entry.created_at)}
              </Text>
            </Group>
          }
        >
          <Stack gap="xs">
            <Text size="sm" fw={500}>
              {entry.status === 'running' && 'Job is processing documents...'}
              {entry.status === 'completed' && 'Job completed successfully'}
              {entry.status === 'failed' && 'Job failed with error'}
              {entry.status === 'pending' && 'Job is waiting to start'}
              {entry.status === 'created' && 'Job was created'}
            </Text>

            {entry.documents_processed > 0 && (
              <Text size="sm" c="dimmed">
                Documents processed: {entry.documents_processed}
              </Text>
            )}

            {entry.chunks_created > 0 && (
              <Text size="sm" c="dimmed">
                Chunks created: {entry.chunks_created}
              </Text>
            )}

            {entry.processing_time_seconds > 0 && (
              <Text size="sm" c="dimmed">
                Processing time: {entry.processing_time_seconds.toFixed(1)}s
              </Text>
            )}

            {entry.error_message && (
              <Alert color="red" title="Error">
                <Text size="sm">{entry.error_message}</Text>
              </Alert>
            )}

            {entry.started_at && (
              <Text size="xs" c="dimmed">
                Started: {new Date(entry.started_at).toLocaleString()}
              </Text>
            )}

            {entry.completed_at && (
              <Text size="xs" c="dimmed">
                Completed: {new Date(entry.completed_at).toLocaleString()}
              </Text>
            )}

            {entry.updated_at && (
              <Text size="xs" c="dimmed" fw={500}>
                Last Updated: {new Date(entry.updated_at).toLocaleString()}
              </Text>
            )}
          </Stack>
        </Timeline.Item>
      ))}
    </Timeline>
  );
}

// Job Control Actions Component - Control buttons (start, stop, cancel, retry) + timeline view
function JobControlActions({
  job,
  onExecute,
  onCancel,
  onViewTimeline,
  isExecuting = false
}: {
  job: JobWithStatus;
  onExecute: (jobId: string) => void;
  onCancel: (jobId: string) => void;
  onViewTimeline: (job: JobWithStatus) => void;
  isExecuting?: boolean;
}) {
  const { data: timelineEntries } = useLatestJobTimelineEntry(job.id);
  const cancelJobMutation = useCancelKnowledgeJob();
  const queryClient = useQueryClient();

  // Get the first (latest) timeline entry from the array
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

  // Debug timeline data
  console.log(`Job ${job.id} control actions:`, {
    timelineEntries,
    latestTimeline,
    timelineEntriesLength: timelineEntries?.length,
    latestStatus: latestTimeline?.status
  });

  // Helper function to determine if a job can be executed (started/re-run)
  const canExecuteJob = () => {
    if (!latestTimeline) {
      return true; // Never executed, can execute
    }

    // Can execute if latest execution is completed, failed, or cancelled
    return ['completed', 'failed', 'cancelled'].includes(latestTimeline.status);
  };

  // Helper function to determine if a job is currently running or pending
  const isJobRunning = () => {
    return latestTimeline?.status === 'running' || latestTimeline?.status === 'pending';
  };

  // Helper function to determine if a job failed or cancelled and can be retried
  const canRetryJob = () => {
    return latestTimeline?.status === 'failed' || latestTimeline?.status === 'cancelled';
  };

  const canExecute = canExecuteJob();
  const isRunning = isJobRunning();
  const canRetry = canRetryJob();

  // Debug logging to troubleshoot missing cancel button
  console.log(`Job ${job.id} button debug:`, {
    status: latestTimeline?.status,
    isRunning,
    canExecute,
    canRetry,
    shouldShowCancel: isRunning,
    shouldShowExecute: canExecute && !canRetry,
    shouldShowRetry: canRetry
  });


  return (
    <Group gap="xs">
      {/* Timeline view button - always visible */}
      <Tooltip label="View Timeline">
        <ActionIcon
          variant="subtle"
          color="blue"
          onClick={() => onViewTimeline(job)}
        >
          <IconEye size={16} />
        </ActionIcon>
      </Tooltip>

      {/* Execute/Re-run button - show when job can be executed (but not failed or cancelled) */}
      {canExecute && !canRetry && (
        <Tooltip label={latestTimeline ? "Re-run Job" : "Start Processing"}>
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => onExecute(job.id)}
            loading={isExecuting}
          >
            <IconPlayerPlay size={16} />
          </ActionIcon>
        </Tooltip>
      )}

      {/* Cancel button - show when job is running or pending */}
      {isRunning && (
        <Tooltip label="Cancel Job">
          <ActionIcon
            variant="subtle"
            color="orange"
            onClick={() => {
              cancelJobMutation.mutate({
                variables: {} as any,
                route: { jobId: job.id }
              }, {
                onSuccess: async () => {
                  console.log('Job cancelled successfully');
                  onCancel(job.id);

                  // FORCE IMMEDIATE REFETCH of ALL job-related data
                  await Promise.all([
                    queryClient.refetchQueries({ queryKey: ['jobs-with-status'] }),
                    queryClient.refetchQueries({ queryKey: ['job-timeline-latest'] }),
                    queryClient.refetchQueries({ queryKey: ['job-timelines'] }),
                  ]);
                },
                onError: async (error) => {
                  console.error('Failed to cancel job:', error);

                  // FORCE IMMEDIATE REFETCH even on error (to show correct state)
                  await Promise.all([
                    queryClient.refetchQueries({ queryKey: ['jobs-with-status'] }),
                    queryClient.refetchQueries({ queryKey: ['job-timeline-latest'] }),
                    queryClient.refetchQueries({ queryKey: ['job-timelines'] }),
                  ]);
                }
              });
            }}
            loading={cancelJobMutation.isPending}
          >
            <IconPlayerStop size={16} />
          </ActionIcon>
        </Tooltip>
      )}

      {/* Retry button - show when job failed or cancelled */}
      {canRetry && (
        <Tooltip label={latestTimeline?.status === 'cancelled' ? "Retry Cancelled Job" : "Retry Failed Job"}>
          <ActionIcon
            variant="subtle"
            color="green"
            onClick={() => onExecute(job.id)}
            loading={isExecuting}
          >
            <IconRefresh size={16} />
          </ActionIcon>
        </Tooltip>
      )}
    </Group>
  );
}

// Polling frequency options
const POLLING_OPTIONS = [
  { value: '2000', label: '2 seconds (Fastest)' },
  { value: '3000', label: '3 seconds (Default)' },
  { value: '5000', label: '5 seconds' },
  { value: '10000', label: '10 seconds' },
  { value: '15000', label: '15 seconds' },
  { value: '30000', label: '30 seconds (Slowest)' },
  { value: 'off', label: 'Off (Manual only)' },
];

const POLLING_STORAGE_KEY = 'job-status-polling-frequency';

export function RealTimeJobTable() {
  const [selectedJob, setSelectedJob] = useState<JobWithStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const executeJobMutation = useExecuteKnowledgeJob();
  const queryClient = useQueryClient();

  // Get initial polling frequency from localStorage or use default
  const [pollingFrequency, setPollingFrequency] = useState<string>(() => {
    try {
      return localStorage.getItem(POLLING_STORAGE_KEY) || '3000';
    } catch {
      return '3000';
    }
  });

  // Parse polling interval (null means no polling)
  const pollingInterval = pollingFrequency === 'off' ? undefined : parseInt(pollingFrequency);

  const { data: jobs, isLoading, isFetching, refetch } = useGetJobsWithStatus();

  // Check if any jobs are running
  const hasRunningJobs = jobs?.some(job => job.is_running) || false;

  // Save polling frequency to localStorage when it changes
  useEffect(() => {
    try {
      localStorage.setItem(POLLING_STORAGE_KEY, pollingFrequency);
    } catch (error) {
      console.error('Failed to save polling frequency:', error);
    }
  }, [pollingFrequency]);

  // Dynamic polling: only poll when there are running jobs (unless user set specific interval)
  useEffect(() => {
    if (!hasRunningJobs || pollingFrequency === 'off') {
      return;
    }

    const interval = setInterval(() => {
      refetch();
      setLastUpdate(new Date());
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [hasRunningJobs, pollingInterval, pollingFrequency, refetch]);

  // Update timestamp when modal opens
  useEffect(() => {
    if (showDetails) {
      setLastUpdate(new Date());
    }
  }, [showDetails]);

  const handleExecuteJob = (jobId: string) => {
    executeJobMutation.mutate({
      variables: {} as any,
      route: { jobId }
    }, {
      onSuccess: async () => {
        notifications.show({
          title: 'Job Started',
          message: 'Job execution has been initiated',
          color: 'green'
        });

        // FORCE IMMEDIATE REFETCH of ALL job-related data
        await Promise.all([
          queryClient.refetchQueries({ queryKey: ['jobs-with-status'] }),
          queryClient.refetchQueries({ queryKey: ['job-timeline-latest'] }),
          queryClient.refetchQueries({ queryKey: ['job-timelines'] }),
        ]);
      },
      onError: async (error: any) => {
        console.error('Job execution error:', error);

        // Extract specific error message from the response
        let errorMessage = 'Failed to start job execution';
        let errorTitle = 'Execution Failed';

        if (error?.response?.data?.detail) {
          // Handle specific backend error messages
          const detail = error.response.data.detail;
          if (detail.includes('Job is already running')) {
            errorTitle = 'Job Already Running';
            errorMessage = 'This job is already running. Please wait for it to complete or cancel it first.';
          } else if (detail.includes('Job is in invalid state')) {
            errorTitle = 'Invalid Job State';
            errorMessage = 'This job cannot be executed in its current state.';
          } else {
            errorMessage = detail;
          }
        } else if (error?.message) {
          errorMessage = error.message;
        }

        notifications.show({
          title: errorTitle,
          message: errorMessage,
          color: 'red'
        });

        // FORCE IMMEDIATE REFETCH even on error (to show correct state)
        await Promise.all([
          queryClient.refetchQueries({ queryKey: ['jobs-with-status'] }),
          queryClient.refetchQueries({ queryKey: ['job-timeline-latest'] }),
          queryClient.refetchQueries({ queryKey: ['job-timelines'] }),
        ]);
      }
    });
  };


  const handleCancelJob = (jobId: string) => {
    // Job cancellation is handled by the JobControlActions component
    // NO MANUAL REFETCH - Automatic polling handles it
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'created': 'cyan',
      'pending': 'yellow',
      'running': 'blue',
      'completed': 'green',
      'failed': 'red',
      'cancelled': 'gray',
    };
    return colors[status] || 'gray';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      'created': '📝',
      'pending': '⏳',
      'running': '🔄',
      'completed': '✅',
      'failed': '❌',
      'cancelled': '⏹️',
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

  const renderJobRow = (job: JobWithStatus) => {
    const status = job.current_status?.status || 'created';
    const timeline = job.current_status;

    return (
      <Table.Tr key={job.id}>
        <Table.Td>
          <Text truncate="end" size="sm" fw={500}>
            {job.name}
          </Text>
        </Table.Td>
        <Table.Td>
          <Badge
            color={getStatusColor(status)}
            variant="light"
            leftSection={getStatusIcon(status)}
          >
            {status}
          </Badge>
        </Table.Td>
        <Table.Td>
          {!timeline ? (
            <Text size="sm" c="dimmed">No execution</Text>
          ) : timeline.status === 'running' ? (
            <Group gap="xs">
              <Text size="sm" c="blue" fw={500}>
                {timeline.documents_processed} docs
              </Text>
              <Text size="sm" c="blue" fw={500}>
                {timeline.chunks_created} chunks
              </Text>
            </Group>
          ) : timeline.status === 'completed' ? (
            <Text size="sm" c="green">
              {timeline.documents_processed} docs, {timeline.chunks_created} chunks
            </Text>
          ) : (
            <Text size="sm" c="dimmed">-</Text>
          )}
        </Table.Td>
        <Table.Td>
          {timeline && timeline.started_at && timeline.completed_at ? (
            <Text size="sm">
              {(() => {
                const start = new Date(timeline.started_at);
                const end = new Date(timeline.completed_at);
                const durationMs = end.getTime() - start.getTime();
                const durationSeconds = durationMs / 1000;
                return `${durationSeconds.toFixed(1)}s`;
              })()}
            </Text>
          ) : timeline && timeline.started_at && !timeline.completed_at ? (
            <Text size="sm" c="blue">Running...</Text>
          ) : (
            <Text size="sm" c="dimmed">-</Text>
          )}
        </Table.Td>
        <Table.Td>
          <Text size="sm" c="dimmed">
            {formatTimeAgo(job.last_execution)}
          </Text>
        </Table.Td>
        <Table.Td>
          <JobControlActions
            job={job}
            onExecute={handleExecuteJob}
            onCancel={handleCancelJob}
            onViewTimeline={(job) => {
              setSelectedJob(job);
              setShowDetails(true);
            }}
            isExecuting={executeJobMutation.isPending}
          />
        </Table.Td>
      </Table.Tr>
    );
  };

  return (
    <>
      <Card withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <div>
              <Group gap="xs" mb="xs">
                <Title order={4}>Job Status</Title>
                {hasRunningJobs && pollingFrequency !== 'off' && (
                  <Badge color="blue" variant="light" size="sm">
                    Auto-refreshing every {parseInt(pollingFrequency) / 1000}s
                  </Badge>
                )}
                {isFetching && (
                  <Badge color="gray" variant="dot" size="sm">
                    <Group gap={4}>
                      <Loader size="xs" />
                      <Text size="xs">Fetching...</Text>
                    </Group>
                  </Badge>
                )}
              </Group>
              <Text size="sm" c="dimmed">
                Monitor the current status and progress of your knowledge processing jobs
              </Text>
            </div>

            <Group gap="xs">
              {/* Polling Frequency Selector */}
              <Select
                size="xs"
                value={pollingFrequency}
                onChange={(value: string | null) => value && setPollingFrequency(value)}
                data={POLLING_OPTIONS}
                leftSection={<IconClock size="1rem" />}
                styles={{
                  input: { width: '200px' }
                }}
                placeholder="Auto-refresh rate"
                comboboxProps={{ withinPortal: true, position: 'bottom-start', zIndex: 1000 }}
              />

              {/* Manual Refresh Button */}
              <Button
                variant="default"
                size="xs"
                leftSection={<IconRefresh size="1rem" />}
                onClick={() => {
                  console.log('Refresh button clicked - forcing immediate refetch');
                  // Simple refetch - no cache invalidation needed with staleTime: 0
                  refetch();
                }}
                loading={isLoading}
              >
                Refresh
              </Button>
            </Group>
          </Group>

          <ScrollArea style={{ position: 'relative' }}>
            {/* Subtle loading overlay when fetching (but not initial load) */}
            {isFetching && !isLoading && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: 'rgba(255, 255, 255, 0.5)',
                  zIndex: 10,
                  pointerEvents: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Paper shadow="sm" p="xs" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Loader size="xs" />
                  <Text size="xs" c="dimmed">Updating...</Text>
                </Paper>
              </div>
            )}

            <Table style={{ opacity: isFetching && !isLoading ? 0.6 : 1, transition: 'opacity 0.2s' }}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Job Name</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Duration</Table.Th>
                  <Table.Th>Last Execution</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {isLoading ? (
                  <Table.Tr>
                    <Table.Td colSpan={6} style={{ textAlign: 'center' }}>
                      <Group justify="center" gap="xs">
                        <Loader size="sm" />
                        <Text size="sm">Loading jobs...</Text>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ) : jobs && jobs.length > 0 ? (
                  jobs.map(renderJobRow)
                ) : (
                  <Table.Tr>
                    <Table.Td colSpan={6} style={{ textAlign: 'center' }}>
                      <Text size="sm" c="dimmed">No jobs found</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Stack>
      </Card>

      <Modal
        opened={showDetails}
        onClose={() => setShowDetails(false)}
        title="Job Execution Timeline"
        size="xl"
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-blue-0)',
            borderBottom: '1px solid var(--mantine-color-gray-3)'
          },
          body: {
            padding: 'var(--mantine-spacing-lg)',
            backgroundColor: 'var(--mantine-color-white)'
          },
          content: {
            borderRadius: 'var(--mantine-radius-md)',
            border: '1px solid var(--mantine-color-gray-3)',
            boxShadow: 'var(--mantine-shadow-lg)'
          }
        }}
      >
        {selectedJob && (
          <Stack gap="md">
            {/* Execution Timeline */}
            <Paper withBorder p="md">
              <Title order={5} mb="md">Execution Timeline</Title>
              <ScrollArea h={400}>
                <JobTimelineComponent jobId={selectedJob.id} />
              </ScrollArea>
            </Paper>
          </Stack>
        )}
      </Modal>

    </>
  );
}
