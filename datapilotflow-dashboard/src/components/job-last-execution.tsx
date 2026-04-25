/**
 * Job Last Execution Component
 * 
 * Simple component that shows the last execution timestamp for a job
 * without any real-time updates or polling.
 */

import { Badge, Text, Stack, Group, Tooltip, Anchor } from '@mantine/core';
import { 
  IconClock, 
  IconCheck, 
  IconX, 
  IconAlertCircle,
  IconPlayerPlay,
  IconPlayerStop,
  IconExternalLink
} from '@tabler/icons-react';
import { useLatestJobTimelineEntry } from '@/api/resources/job-timelines';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

interface JobLastExecutionProps {
  jobId: string;
  refreshTrigger?: number; // Add refresh trigger prop
}

export function JobLastExecution({ jobId, refreshTrigger }: JobLastExecutionProps) {
  const { data: timelineEntries, isLoading, refetch } = useLatestJobTimelineEntry(jobId);
  const navigate = useNavigate();

  // Refetch when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      refetch();
    }
  }, [refreshTrigger, refetch]);

  if (isLoading) {
    return <Text size="sm" c="dimmed">Loading...</Text>;
  }

  // Get the first (latest) timeline entry from the array
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
  };

  const handleClick = () => {
    navigate('/dashboard/management/knowledge/status');
  };

  return (
    <Stack gap={4}>
      <Badge
        color={getStatusColor(latestTimeline.status)}
        leftSection={getStatusIcon(latestTimeline.status)}
        variant="light"
        size="sm"
        style={{ alignSelf: 'flex-start' }}
      >
        {latestTimeline.status}
      </Badge>
      <Group gap={4} wrap="nowrap" align="center">
        <Anchor
          size="xs"
          c="dimmed"
          style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}
          onClick={handleClick}
        >
          {latestTimeline.completed_at
            ? `Completed ${formatDate(latestTimeline.completed_at)}`
            : latestTimeline.started_at
            ? `Started ${formatDate(latestTimeline.started_at)}`
            : `Created ${formatDate(latestTimeline.created_at)}`}
        </Anchor>
        <IconExternalLink size={10} style={{ flexShrink: 0 }} />
      </Group>
    </Stack>
  );
}
