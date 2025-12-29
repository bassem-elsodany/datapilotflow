/**
 * Job Timeline Status Component
 * 
 * This component displays the latest timeline entry status for a job,
 * showing execution history and statistics with real-time updates.
 */

import { Badge, Text, Stack, Group, Tooltip, Progress, Switch } from '@mantine/core';
import { 
  IconClock, 
  IconCheck, 
  IconX, 
  IconAlertCircle,
  IconPlayerPlay,
  IconPlayerStop
} from '@tabler/icons-react';
import { useLatestJobTimelineEntry, useJobTimelineStatistics } from '@/api/resources/job-timelines';
import { JobTimeline } from '@/api/resources/job-timelines';
import { EnhancedRealTimeJobProgress } from './enhanced-real-time-job-progress';

interface JobTimelineStatusProps {
  jobId: string;
  showStatistics?: boolean;
  enableRealTime?: boolean;
  showConnectionStatus?: boolean;
}

export function JobTimelineStatus({ 
  jobId, 
  showStatistics = false, 
  enableRealTime = true,
  showConnectionStatus = true 
}: JobTimelineStatusProps) {
  // Use enhanced real-time component if enabled
  if (enableRealTime) {
    return (
      <EnhancedRealTimeJobProgress 
        jobId={jobId}
        showStatistics={showStatistics}
        showConnectionStatus={showConnectionStatus}
        enableWebSocket={false}  // Disable WebSocket, use polling instead
      />
    );
  }

  // Fallback to original implementation
  const { data: timelineEntries, isLoading: timelineLoading } = useLatestJobTimelineEntry(jobId);
  const { data: statistics, isLoading: statsLoading } = useJobTimelineStatistics(jobId);

  if (timelineLoading || statsLoading) {
    return <Text size="sm" c="dimmed">Loading...</Text>;
  }

  // Get the first (latest) timeline entry from the array
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

  // Debug logging
  console.log('JobTimelineStatus Debug:', {
    jobId,
    timelineEntries,
    latestTimeline,
    hasTimeline: !!latestTimeline
  });

  if (!latestTimeline) {
    return (
      <Badge color="gray" variant="light" leftSection={<IconClock size={12} />}>
        Never Executed
      </Badge>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'failed': return 'red';
      case 'running': return 'blue';
      case 'pending': return 'yellow';
      case 'created': return 'gray';
      case 'cancelled': return 'orange';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <IconCheck size={12} />;
      case 'failed': return <IconX size={12} />;
      case 'running': return <IconPlayerPlay size={12} />;
      case 'pending': return <IconClock size={12} />;
      case 'created': return <IconClock size={12} />;
      case 'cancelled': return <IconPlayerStop size={12} />;
      default: return <IconAlertCircle size={12} />;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
  };

  return (
    <Stack gap="xs">
      {/* Latest Execution Status */}
      <Group gap="xs" align="center">
        <Badge 
          color={getStatusColor(latestTimeline.status)} 
          leftSection={getStatusIcon(latestTimeline.status)}
          variant="light"
        >
          {latestTimeline.status}
        </Badge>
        
        {latestTimeline.status === 'running' && (
          <Progress value={50} size="sm" style={{ width: 60 }} />
        )}
        
        {latestTimeline.status === 'completed' && (
          <Progress value={100} size="sm" color="green" style={{ width: 60 }} />
        )}
      </Group>

      {/* Latest Execution Results */}
      {latestTimeline.status === 'completed' && (
        <Stack gap={2}>
          <Text size="sm">
            <Text component="span" fw={500}>{latestTimeline.documents_processed}</Text> docs
          </Text>
          <Text size="sm">
            <Text component="span" fw={500}>{latestTimeline.chunks_created}</Text> chunks
          </Text>
          {latestTimeline.processing_time_seconds > 0 && (
            <Text size="sm" c="dimmed">
              {formatDuration(latestTimeline.processing_time_seconds)}
            </Text>
          )}
        </Stack>
      )}

      {/* Error Message */}
      {latestTimeline.status === 'failed' && latestTimeline.error_message && (
        <Tooltip label={latestTimeline.error_message} multiline w={300}>
          <Text size="sm" c="red" style={{ cursor: 'help' }}>
            {latestTimeline.error_message.length > 50 
              ? `${latestTimeline.error_message.substring(0, 50)}...`
              : latestTimeline.error_message
            }
          </Text>
        </Tooltip>
      )}

      {/* Execution Date */}
      <Text size="xs" c="dimmed">
        {(() => {
          console.log('Date fields debug:', {
            completed_at: latestTimeline.completed_at,
            started_at: latestTimeline.started_at,
            created_at: latestTimeline.created_at,
            status: latestTimeline.status
          });
          
          if (latestTimeline.completed_at) {
            return `Completed ${formatDate(latestTimeline.completed_at)}`;
          } else if (latestTimeline.started_at) {
            return `Started ${formatDate(latestTimeline.started_at)}`;
          } else {
            return `Created ${formatDate(latestTimeline.created_at)}`;
          }
        })()}
      </Text>

      {/* Statistics (if requested) */}
      {showStatistics && statistics && (
        <Stack gap={2}>
          <Text size="xs" c="dimmed" fw={500}>All Time:</Text>
          <Text size="xs" c="dimmed">
            {statistics.statistics.total_executions} executions
          </Text>
          <Text size="xs" c="dimmed">
            {statistics.statistics.successful_executions} successful
          </Text>
          {statistics.statistics.failed_executions > 0 && (
            <Text size="xs" c="red">
              {statistics.statistics.failed_executions} failed
            </Text>
          )}
        </Stack>
      )}
    </Stack>
  );
}
