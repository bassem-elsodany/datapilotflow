import { useCancelKnowledgeJob, useExecuteKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { JobWithStatus, useGetJobsWithStatus, useGetJobTimeline } from '@/hooks/api/job-status';
import { paths } from '@/routes/paths';
import { formatDate } from '@/utilities/date';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  Paper,
  Progress,
  RingProgress,
  ScrollArea,
  Select,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Timeline,
  Title,
  Tooltip,
  useMantineTheme
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconBriefcase,
  IconCheck,
  IconChecks,
  IconClock,
  IconCloudUpload,
  IconCpu,
  IconDatabase,
  IconEye,
  IconExternalLink,
  IconFileText,
  IconPlayerPause,
  IconPlayerPlay,
  IconPlayerStop,
  IconRefresh,
  IconRocket,
  IconX
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Pipeline step configuration for the new architecture
interface PipelineStep {
  name: string;
  icon: React.ElementType;
  color: string;
  description: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  { name: 'Extraction', icon: IconFileText, color: 'blue', description: 'Extracting documents' },
  { name: 'Chunking', icon: IconCpu, color: 'cyan', description: 'Splitting into chunks' },
  { name: 'Embedding', icon: IconRocket, color: 'violet', description: 'Generating embeddings' },
  { name: 'Storage', icon: IconDatabase, color: 'teal', description: 'Storing in vector DB' },
  { name: 'Timeline', icon: IconCloudUpload, color: 'green', description: 'Updating status' },
];

// Timeline component with enhanced visuals
function JobTimelineComponent({ jobId }: { jobId: string }) {
  const { data: timelineEntries, isLoading } = useGetJobTimeline(jobId);
  const theme = useMantineTheme();

  if (isLoading) {
    return (
      <Group justify="center" p="xl">
        <Loader size="md" variant="dots" />
        <Text size="sm" c="dimmed">Loading timeline...</Text>
      </Group>
    );
  }

  if (!timelineEntries || timelineEntries.length === 0) {
    return (
      <Paper withBorder p="xl" style={{
        background: 'linear-gradient(135deg, rgba(248, 249, 250, 0.5) 0%, rgba(228, 230, 235, 0.3) 100%)'
      }}>
        <Stack align="center" gap="md">
          <ThemeIcon size={60} radius="xl" variant="light" color="gray">
            <IconClock size={30} />
          </ThemeIcon>
          <Text size="sm" c="dimmed" ta="center">
            No timeline entries found
          </Text>
        </Stack>
      </Paper>
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
      'created': IconClock,
      'pending': IconPlayerPause,
      'running': IconPlayerPlay,
      'completed': IconCheck,
      'failed': IconX,
      'cancelled': IconPlayerStop,
    };
    return icons[status] || IconClock;
  };

  return (
    <Timeline
      active={timelineEntries.length - 1}
      bulletSize={32}
      lineWidth={3}
      styles={{
        item: {
          marginBottom: theme.spacing.lg,
        },
        itemBullet: {
          border: `3px solid ${theme.colors.gray[1]}`,
          boxShadow: theme.shadows.sm,
        }
      }}
    >
      {timelineEntries.map((entry) => {
        const StatusIcon = getStatusIcon(entry.status);
        const statusColor = getStatusColor(entry.status);

        return (
          <Timeline.Item
            key={entry.id}
            bullet={
              <ThemeIcon size={32} radius="xl" variant="light" color={statusColor}>
                <StatusIcon size={18} />
              </ThemeIcon>
            }
            title={
              <Group gap="xs" mb="xs">
                <Badge
                  color={statusColor}
                  variant="gradient"
                  gradient={{ from: statusColor, to: statusColor === 'blue' ? 'cyan' : statusColor, deg: 45 }}
                  size="lg"
                  style={{ textTransform: 'uppercase', fontWeight: 700 }}
                >
                  {entry.status}
                </Badge>
                <Text size="sm" c="dimmed" fw={500}>
                  {formatDate(entry.created_at)}
                </Text>
              </Group>
            }
          >
            <Paper withBorder p="md" style={{
              background: entry.status === 'failed'
                ? 'linear-gradient(135deg, rgba(255, 245, 245, 0.5) 0%, rgba(255, 235, 235, 0.3) 100%)'
                : entry.status === 'completed'
                ? 'linear-gradient(135deg, rgba(240, 255, 244, 0.5) 0%, rgba(230, 252, 235, 0.3) 100%)'
                : 'linear-gradient(135deg, rgba(248, 249, 250, 0.5) 0%, rgba(241, 243, 245, 0.3) 100%)'
            }}>
              <Stack gap="sm">
                <Text size="sm" fw={600}>
                  {entry.status === 'running' && '🔄 Processing documents...'}
                  {entry.status === 'completed' && '✅ Job completed successfully'}
                  {entry.status === 'failed' && '❌ Job failed with error'}
                  {entry.status === 'pending' && '⏳ Waiting to start'}
                  {entry.status === 'created' && '📝 Job created'}
                  {entry.status === 'cancelled' && '⏹️ Job was cancelled'}
                </Text>

                {(entry.documents_processed > 0 || entry.chunks_created > 0) && (
                  <Group gap="lg">
                    {entry.documents_processed > 0 && (
                      <Group gap="xs">
                        <ThemeIcon size="sm" radius="xl" variant="light" color="blue">
                          <IconFileText size={14} />
                        </ThemeIcon>
                        <Text size="sm" fw={500}>
                          {entry.documents_processed} documents
                        </Text>
                      </Group>
                    )}
                    {entry.chunks_created > 0 && (
                      <Group gap="xs">
                        <ThemeIcon size="sm" radius="xl" variant="light" color="cyan">
                          <IconCpu size={14} />
                        </ThemeIcon>
                        <Text size="sm" fw={500}>
                          {entry.chunks_created} chunks
                        </Text>
                      </Group>
                    )}
                  </Group>
                )}

                {entry.processing_time_seconds > 0 && (
                  <Group gap="xs">
                    <ThemeIcon size="sm" radius="xl" variant="light" color="violet">
                      <IconClock size={14} />
                    </ThemeIcon>
                    <Text size="sm" c="dimmed">
                      Completed in {entry.processing_time_seconds.toFixed(2)}s
                    </Text>
                  </Group>
                )}

                {entry.error_message && (
                  <Alert color="red" title="Error Details" icon={<IconAlertCircle size={20} />}>
                    <Text size="sm">{entry.error_message}</Text>
                  </Alert>
                )}

                <Group gap="lg" style={{ fontSize: '0.75rem', color: theme.colors.gray[6] }}>
                  {entry.started_at && (
                    <Text size="xs" c="dimmed">
                      ⏱️ Started: {new Date(entry.started_at).toLocaleString()}
                    </Text>
                  )}
                  {entry.completed_at && (
                    <Text size="xs" c="dimmed">
                      ✓ Finished: {new Date(entry.completed_at).toLocaleString()}
                    </Text>
                  )}
                </Group>
              </Stack>
            </Paper>
          </Timeline.Item>
        );
      })}
    </Timeline>
  );
}

// Enhanced Job Control Actions - Fixed to use job.current_status directly
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
  const navigate = useNavigate();
  const cancelJobMutation = useCancelKnowledgeJob();
  const queryClient = useQueryClient();

  // FIX: Use job.current_status from the table data instead of separate API call
  // This eliminates the race condition and data mismatch
  const currentStatus = job.current_status;

  // Helper functions using the correct data source
  const canExecuteJob = () => {
    if (!currentStatus) {
      return true; // Never executed, can execute
    }
    return ['completed', 'failed', 'cancelled'].includes(currentStatus.status);
  };

  const isJobRunning = () => {
    // Use job.is_running from table data for consistency
    return job.is_running || currentStatus?.status === 'running' || currentStatus?.status === 'pending';
  };

  const canRetryJob = () => {
    return currentStatus?.status === 'failed' || currentStatus?.status === 'cancelled';
  };

  const canExecute = canExecuteJob();
  const isRunning = isJobRunning();
  const canRetry = canRetryJob();

  return (
    <Group gap="xs">
      {/* View Job Details button - always visible */}
      <Tooltip label="View Job Details" withArrow>
        <ActionIcon
          variant="light"
          color="indigo"
          size="lg"
          radius="xl"
          onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}
        >
          <IconBriefcase size={18} />
        </ActionIcon>
      </Tooltip>

      {/* Timeline view button - always visible */}
      <Tooltip label="View Timeline" withArrow>
        <ActionIcon
          variant="light"
          color="blue"
          size="lg"
          radius="xl"
          onClick={() => onViewTimeline(job)}
        >
          <IconEye size={18} />
        </ActionIcon>
      </Tooltip>

      {/* Start/Re-run button - show when job can be executed (but not failed or cancelled) */}
      {canExecute && !canRetry && (
        <Tooltip label={currentStatus ? "Re-run Job" : "Start Processing"} withArrow>
          <ActionIcon
            variant="light"
            color="green"
            size="lg"
            radius="xl"
            onClick={() => onExecute(job.id)}
            loading={isExecuting}
          >
            <IconPlayerPlay size={18} />
          </ActionIcon>
        </Tooltip>
      )}

      {/* Cancel button - FIXED: Now properly shows when job is running */}
      {isRunning && (
        <Tooltip label="Cancel Job" withArrow>
          <ActionIcon
            variant="light"
            color="orange"
            size="lg"
            radius="xl"
            onClick={() => {
              cancelJobMutation.mutate({
                variables: {} as any,
                route: { jobId: job.id }
              }, {
                onSuccess: async () => {
                  notifications.show({
                    title: 'Job Cancelled',
                    message: 'Job has been cancelled successfully',
                    color: 'orange',
                    icon: <IconPlayerStop size={18} />,
                  });
                  onCancel(job.id);
                  await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
                },
                onError: async (error) => {
                  console.error('Failed to cancel job:', error);
                  notifications.show({
                    title: 'Cancellation Failed',
                    message: 'Failed to cancel job. Please try again.',
                    color: 'red',
                  });
                  await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
                }
              });
            }}
            loading={cancelJobMutation.isPending}
          >
            <IconPlayerStop size={18} />
          </ActionIcon>
        </Tooltip>
      )}

      {/* Retry button - show when job failed or cancelled */}
      {canRetry && (
        <Tooltip label={currentStatus?.status === 'cancelled' ? "Retry Cancelled Job" : "Retry Failed Job"} withArrow>
          <ActionIcon
            variant="light"
            color="violet"
            size="lg"
            radius="xl"
            onClick={() => onExecute(job.id)}
            loading={isExecuting}
          >
            <IconRefresh size={18} />
          </ActionIcon>
        </Tooltip>
      )}
    </Group>
  );
}

// Polling frequency options
const POLLING_OPTIONS = [
  { value: '2000', label: '⚡ 2 seconds (Fastest)' },
  { value: '3000', label: '🚀 3 seconds (Default)' },
  { value: '5000', label: '⏱️ 5 seconds' },
  { value: '10000', label: '🕐 10 seconds' },
  { value: 'off', label: '⏸️ Off (Manual only)' },
];

const POLLING_STORAGE_KEY = 'job-status-polling-frequency';

export function RealTimeJobTableImproved() {
  const [selectedJob, setSelectedJob] = useState<JobWithStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const executeJobMutation = useExecuteKnowledgeJob();
  const queryClient = useQueryClient();
  const theme = useMantineTheme();

  const [pollingFrequency, setPollingFrequency] = useState<string>(() => {
    try {
      return localStorage.getItem(POLLING_STORAGE_KEY) || '3000';
    } catch {
      return '3000';
    }
  });

  const pollingInterval = pollingFrequency === 'off' ? undefined : parseInt(pollingFrequency);

  const { data: jobs, isLoading, isFetching, refetch } = useGetJobsWithStatus();

  const hasRunningJobs = jobs?.some(job => job.is_running) || false;

  useEffect(() => {
    try {
      localStorage.setItem(POLLING_STORAGE_KEY, pollingFrequency);
    } catch (error) {
      console.error('Failed to save polling frequency:', error);
    }
  }, [pollingFrequency]);

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

  const handleExecuteJob = (jobId: string) => {
    executeJobMutation.mutate({
      variables: {} as any,
      route: { jobId }
    }, {
      onSuccess: async () => {
        notifications.show({
          title: '🚀 Job Started',
          message: 'Your knowledge processing job has been queued',
          color: 'green',
          icon: <IconRocket size={20} />,
        });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      },
      onError: async (error: any) => {
        let errorMessage = 'Failed to start job execution';
        if (error?.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        }
        notifications.show({
          title: '❌ Execution Failed',
          message: errorMessage,
          color: 'red',
          icon: <IconAlertCircle size={20} />,
        });
        await queryClient.refetchQueries({ queryKey: ['jobs-with-status'] });
      }
    });
  };

  const handleCancelJob = (jobId: string) => {
    // Handled by JobControlActions component
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

  const getStatusGradient = (status: string) => {
    const gradients: Record<string, { from: string; to: string; deg: number }> = {
      'running': { from: 'blue', to: 'cyan', deg: 45 },
      'completed': { from: 'green', to: 'teal', deg: 45 },
      'failed': { from: 'red', to: 'orange', deg: 45 },
      'pending': { from: 'yellow', to: 'orange', deg: 45 },
      'cancelled': { from: 'gray', to: 'dark', deg: 45 },
      'created': { from: 'cyan', to: 'blue', deg: 45 },
    };
    return gradients[status] || { from: 'gray', to: 'dark', deg: 45 };
  };

  const formatTimeAgo = (timestamp?: string) => {
    if (!timestamp) return 'Never';

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
    const isRunning = job.is_running;

    return (
      <Table.Tr
        key={job.id}
        style={{
          transition: 'all 0.2s ease',
          background: isRunning
            ? 'linear-gradient(90deg, rgba(59, 130, 246, 0.05) 0%, rgba(59, 130, 246, 0.02) 100%)'
            : undefined,
        }}
      >
        <Table.Td>
          <Group gap="sm">
            {isRunning && (
              <Loader size="xs" color="blue" type="dots" />
            )}
            <Box>
              <Text size="sm" fw={600} style={{ lineHeight: 1.3 }}>
                {job.name}
              </Text>
              {job.description && (
                <Text size="xs" c="dimmed" lineClamp={1}>
                  {job.description}
                </Text>
              )}
            </Box>
          </Group>
        </Table.Td>
        <Table.Td>
          <Badge
            size="lg"
            variant="gradient"
            gradient={getStatusGradient(status)}
            style={{ textTransform: 'uppercase', fontWeight: 700 }}
          >
            {status}
          </Badge>
        </Table.Td>
        <Table.Td>
          {!timeline ? (
            <Text size="sm" c="dimmed" fs="italic">Not executed yet</Text>
          ) : (
            <Group gap="md">
              <Group gap="xs">
                <ThemeIcon size="sm" radius="xl" variant="light" color="blue">
                  <IconFileText size={14} />
                </ThemeIcon>
                <Text size="sm" fw={500}>
                  {timeline.documents_processed}
                </Text>
              </Group>
              <Group gap="xs">
                <ThemeIcon size="sm" radius="xl" variant="light" color="cyan">
                  <IconCpu size={14} />
                </ThemeIcon>
                <Text size="sm" fw={500}>
                  {timeline.chunks_created}
                </Text>
              </Group>
            </Group>
          )}
        </Table.Td>
        <Table.Td>
          {timeline && timeline.started_at && timeline.completed_at ? (
            <Group gap="xs">
              <ThemeIcon size="sm" radius="xl" variant="light" color="violet">
                <IconClock size={14} />
              </ThemeIcon>
              <Text size="sm" fw={500}>
                {(() => {
                  const start = new Date(timeline.started_at);
                  const end = new Date(timeline.completed_at);
                  const durationMs = end.getTime() - start.getTime();
                  const durationSeconds = durationMs / 1000;
                  return `${durationSeconds.toFixed(1)}s`;
                })()}
              </Text>
            </Group>
          ) : timeline && timeline.started_at && !timeline.completed_at ? (
            <Badge color="blue" variant="dot" size="md">
              Running...
            </Badge>
          ) : (
            <Text size="sm" c="dimmed">-</Text>
          )}
        </Table.Td>
        <Table.Td>
          <Text size="sm" c="dimmed" fw={500}>
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
      <Card
        withBorder
        radius="lg"
        style={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 1) 0%, rgba(249, 250, 251, 1) 100%)',
          border: `1px solid ${theme.colors.gray[2]}`,
        }}
      >
        <Stack gap="lg">
          <Group justify="space-between" align="flex-start">
            <Box>
              <Group gap="sm" mb="xs">
                <Title order={3} style={{
                  background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}>
                  🚀 Job Status Dashboard
                </Title>
                {hasRunningJobs && pollingFrequency !== 'off' && (
                  <Badge
                    color="blue"
                    variant="light"
                    size="md"
                    leftSection={<Loader size="xs" type="dots" />}
                  >
                    Auto-refreshing every {parseInt(pollingFrequency) / 1000}s
                  </Badge>
                )}
                {isFetching && (
                  <Badge color="gray" variant="dot" size="md">
                    <Group gap={6}>
                      <Loader size="xs" />
                      <Text size="xs">Updating...</Text>
                    </Group>
                  </Badge>
                )}
              </Group>
              <Text size="sm" c="dimmed">
                Monitor your knowledge processing jobs in real-time with the new callback-free architecture
              </Text>
            </Box>

            <Group gap="xs">
              <Select
                size="sm"
                value={pollingFrequency}
                onChange={(value: string | null) => value && setPollingFrequency(value)}
                data={POLLING_OPTIONS}
                leftSection={<IconClock size="1rem" />}
                styles={{
                  input: { width: '220px', borderRadius: theme.radius.md }
                }}
                comboboxProps={{ withinPortal: true, position: 'bottom-start', zIndex: 1000 }}
              />

              <Button
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan', deg: 45 }}
                size="sm"
                leftSection={<IconRefresh size={16} />}
                onClick={() => refetch()}
                loading={isLoading}
                radius="md"
              >
                Refresh
              </Button>
            </Group>
          </Group>

          <ScrollArea>
            <Table
              highlightOnHover
              verticalSpacing="md"
              style={{
                opacity: isFetching && !isLoading ? 0.7 : 1,
                transition: 'opacity 0.2s'
              }}
            >
              <Table.Thead>
                <Table.Tr style={{
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
                }}>
                  <Table.Th>
                    <Text fw={700} size="sm">Job Name</Text>
                  </Table.Th>
                  <Table.Th>
                    <Text fw={700} size="sm">Status</Text>
                  </Table.Th>
                  <Table.Th>
                    <Text fw={700} size="sm">Progress</Text>
                  </Table.Th>
                  <Table.Th>
                    <Text fw={700} size="sm">Duration</Text>
                  </Table.Th>
                  <Table.Th>
                    <Text fw={700} size="sm">Last Run</Text>
                  </Table.Th>
                  <Table.Th>
                    <Text fw={700} size="sm">Actions</Text>
                  </Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {isLoading ? (
                  <Table.Tr>
                    <Table.Td colSpan={6} style={{ textAlign: 'center' }}>
                      <Group justify="center" gap="md" py="xl">
                        <Loader size="lg" variant="dots" />
                        <Stack gap={4} align="center">
                          <Text size="sm" fw={500}>Loading jobs...</Text>
                          <Text size="xs" c="dimmed">Fetching latest job status</Text>
                        </Stack>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ) : jobs && jobs.length > 0 ? (
                  jobs.map(renderJobRow)
                ) : (
                  <Table.Tr>
                    <Table.Td colSpan={6}>
                      <Paper withBorder p="xl" style={{
                        background: 'linear-gradient(135deg, rgba(248, 249, 250, 0.5) 0%, rgba(228, 230, 235, 0.3) 100%)'
                      }}>
                        <Stack align="center" gap="md">
                          <ThemeIcon size={80} radius="xl" variant="light" color="gray">
                            <IconRocket size={40} />
                          </ThemeIcon>
                          <Stack gap={4} align="center">
                            <Text size="md" fw={600}>No jobs found</Text>
                            <Text size="sm" c="dimmed">Create your first knowledge processing job to get started</Text>
                          </Stack>
                        </Stack>
                      </Paper>
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
        title={
          <Group gap="sm">
            <ThemeIcon size="lg" radius="xl" variant="gradient" gradient={{ from: 'blue', to: 'cyan', deg: 45 }}>
              <IconEye size={20} />
            </ThemeIcon>
            <Text fw={700} size="lg">Job Execution Timeline</Text>
          </Group>
        }
        size="xl"
        radius="lg"
        styles={{
          header: {
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
            borderBottom: `2px solid ${theme.colors.blue[2]}`,
            padding: theme.spacing.lg,
          },
          body: {
            padding: theme.spacing.xl,
          },
          content: {
            border: `1px solid ${theme.colors.gray[2]}`,
            boxShadow: theme.shadows.xl,
          }
        }}
      >
        {selectedJob && (
          <Stack gap="lg">
            {/* Job Info Header */}
            <Paper withBorder p="md" style={{
              background: 'linear-gradient(135deg, rgba(249, 250, 251, 0.8) 0%, rgba(255, 255, 255, 1) 100%)',
            }}>
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text fw={600} size="lg">{selectedJob.name}</Text>
                  <Badge
                    size="lg"
                    variant="gradient"
                    gradient={getStatusGradient(selectedJob.current_status?.status || 'created')}
                  >
                    {selectedJob.current_status?.status || 'created'}
                  </Badge>
                </Group>
                {selectedJob.description && (
                  <Text size="sm" c="dimmed">{selectedJob.description}</Text>
                )}
              </Stack>
            </Paper>

            {/* Execution Timeline */}
            <Paper withBorder p="lg" style={{
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 1) 0%, rgba(249, 250, 251, 0.5) 100%)',
            }}>
              <Title order={5} mb="lg" style={{
                background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                📊 Execution History
              </Title>
              <ScrollArea h={500}>
                <JobTimelineComponent jobId={selectedJob.id} />
              </ScrollArea>
            </Paper>
          </Stack>
        )}
      </Modal>
    </>
  );
}