/**
 * Real-Time Job Progress Component
 * 
 * This component displays real-time job progress with batch updates,
 * showing cumulative progress, current batch info, and live statistics.
 */

import { useState, useEffect, useCallback } from 'react';
import { Badge, Text, Stack, Group, Tooltip, Progress, Card, SimpleGrid, Divider, Alert } from '@mantine/core';
import { 
  IconClock, 
  IconCheck, 
  IconX, 
  IconAlertCircle,
  IconPlayerPlay,
  IconPlayerStop,
  IconDatabase,
  IconFileText,
  IconClockHour4,
  IconRefresh
} from '@tabler/icons-react';
import { useLatestJobTimelineEntry, useJobTimelineStatistics } from '@/api/resources/job-timelines';
import { JobTimeline } from '@/api/resources/job-timelines';

interface RealTimeJobProgressProps {
  jobId: string;
  showStatistics?: boolean;
  refreshInterval?: number; // in milliseconds, default 2000ms
}

interface BatchProgress {
  batch_number: number;
  total_processed: number;
  documents_in_batch: number;
  chunks_created: number;
  total_chunks: number;
  processing_time: number;
  timestamp: string;
}

export function RealTimeJobProgress({ 
  jobId, 
  showStatistics = true, 
  refreshInterval = 2000 
}: RealTimeJobProgressProps) {
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  
  // React Query hooks for initial data
  const { data: timelineEntries, isLoading: timelineLoading, refetch: refetchTimeline } = useLatestJobTimelineEntry(jobId);
  const { data: statistics, isLoading: statsLoading, refetch: refetchStats } = useJobTimelineStatistics(jobId);

  // Get the latest timeline entry
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

  // Simple polling for updates
  useEffect(() => {
    const interval = setInterval(() => {
      refetchTimeline();
      setLastUpdate(new Date().toLocaleTimeString());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refetchTimeline, refreshInterval]);


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

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  if (timelineLoading || statsLoading) {
    return <Text size="sm" c="dimmed">Loading...</Text>;
  }

  if (!latestTimeline) {
    return (
      <Badge color="gray" variant="light" leftSection={<IconClock size={12} />}>
        Never Executed
      </Badge>
    );
  }

  const isRunning = latestTimeline.status === 'running';
  const progressPercentage = isRunning && latestTimeline.documents_processed > 0 
    ? Math.min((latestTimeline.documents_processed / 1000) * 100, 100) // Estimate progress
    : latestTimeline.status === 'completed' ? 100 : 0;

  return (
    <Stack gap="md">
      {/* Connection Status */}
      {isRunning && (
        <Group gap="xs">
          <Badge 
            color={isConnected ? 'green' : 'red'} 
            variant="light" 
            leftSection={<IconRefresh size={10} />}
            size="xs"
          >
            {isConnected ? 'Live' : 'Disconnected'}
          </Badge>
          {lastUpdate && (
            <Text size="xs" c="dimmed">
              Last update: {lastUpdate}
            </Text>
          )}
        </Group>
      )}

      {/* Status Badge */}
      <Group gap="xs" align="center">
        <Badge 
          color={getStatusColor(latestTimeline.status)} 
          leftSection={getStatusIcon(latestTimeline.status)}
          variant="light"
        >
          {latestTimeline.status}
        </Badge>
        
        {/* Progress Bar */}
        {isRunning && (
          <Progress 
            value={progressPercentage} 
            size="sm" 
            style={{ width: 120 }}
            animated
            color="blue"
          />
        )}
        
        {latestTimeline.status === 'completed' && (
          <Progress value={100} size="sm" color="green" style={{ width: 120 }} />
        )}
      </Group>

      {/* Real-time Batch Progress */}
      {isRunning && batchProgress && (
        <Card withBorder p="sm" radius="md" style={{ backgroundColor: '#f8f9fa' }}>
          <Stack gap="xs">
            <Group justify="space-between" align="center">
              <Text size="sm" fw={500} c="blue">
                Batch {batchProgress.batch_number} Processing
              </Text>
              <Text size="xs" c="dimmed">
                {new Date(batchProgress.timestamp).toLocaleTimeString()}
              </Text>
            </Group>
            
            <SimpleGrid cols={2} spacing="xs">
              <Group gap="xs">
                <IconFileText size={14} color="#228be6" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(batchProgress.documents_in_batch)}</Text> docs in batch
                </Text>
              </Group>
              
              <Group gap="xs">
                <IconDatabase size={14} color="#51cf66" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(batchProgress.chunks_created)}</Text> chunks in batch
                </Text>
              </Group>
            </SimpleGrid>
          </Stack>
        </Card>
      )}

      {/* Cumulative Statistics */}
      {showStatistics && (latestTimeline.status === 'completed' || latestTimeline.status === 'running') && (
        <Card withBorder p="sm" radius="md">
          <Stack gap="xs">
            <Text size="sm" fw={500}>Cumulative Progress</Text>
            
            <SimpleGrid cols={2} spacing="xs">
              <Group gap="xs">
                <IconFileText size={14} color="#228be6" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(latestTimeline.documents_processed)}</Text> docs
                </Text>
              </Group>
              
              <Group gap="xs">
                <IconDatabase size={14} color="#51cf66" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(latestTimeline.chunks_created)}</Text> chunks
                </Text>
              </Group>
              
              <Group gap="xs">
                <IconClockHour4 size={14} color="#fab005" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatDuration(latestTimeline.processing_time_seconds)}</Text> elapsed
                </Text>
              </Group>
              
              {statistics && (
                <Group gap="xs">
                  <IconRefresh size={14} color="#868e96" />
                  <Text size="sm">
                    <Text component="span" fw={500}>{statistics?.statistics?.total_executions || 0}</Text> runs
                  </Text>
                </Group>
              )}
            </SimpleGrid>
          </Stack>
        </Card>
      )}

      {/* Error Message */}
      {latestTimeline.status === 'failed' && latestTimeline.error_message && (
        <Alert color="red" icon={<IconX size={16} />}>
          <Text size="sm">{latestTimeline.error_message}</Text>
        </Alert>
      )}

      {/* Execution Date */}
      <Text size="xs" c="dimmed">
        {latestTimeline.started_at 
          ? `Started: ${new Date(latestTimeline.started_at).toLocaleString()}`
          : 'Not started'
        }
        {latestTimeline.completed_at && (
          <Text component="span" ml="sm">
            • Completed: {new Date(latestTimeline.completed_at).toLocaleString()}
          </Text>
        )}
      </Text>
    </Stack>
  );
}
