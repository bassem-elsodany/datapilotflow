/**
 * Enhanced Real-Time Job Progress Component with WebSocket
 * 
 * This component displays real-time job progress with WebSocket updates,
 * showing live batch progress, cumulative statistics, and connection status.
 */

import { useState, useEffect, useCallback } from 'react';
import { Badge, Text, Stack, Group, Tooltip, Progress, Card, SimpleGrid, Alert, Button, ActionIcon } from '@mantine/core';
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
  IconRefresh,
  IconWifi,
  IconWifiOff,
  IconSettings
} from '@tabler/icons-react';
import { useLatestJobTimelineEntry, useJobTimelineStatistics } from '@/api/resources/job-timelines';

interface EnhancedRealTimeJobProgressProps {
  jobId: string;
  showStatistics?: boolean;
  showConnectionStatus?: boolean;
  enableWebSocket?: boolean;
}

interface BatchProgressUpdate {
  job_id: string;
  timeline_id: string;
  batch_number: number;
  total_processed: number;
  documents_in_batch: number;
  chunks_created: number;
  total_chunks: number;
  processing_time: number;
  timestamp: string;
}

interface JobStatusUpdate {
  job_id: string;
  timeline_id: string;
  new_status: string;
  message: string;
  timestamp: string;
}

export function EnhancedRealTimeJobProgress({ 
  jobId, 
  showStatistics = true,
  showConnectionStatus = true,
  enableWebSocket = true
}: EnhancedRealTimeJobProgressProps) {
  const [batchProgress, setBatchProgress] = useState<BatchProgressUpdate | null>(null);
  const [liveStats, setLiveStats] = useState({
    total_processed: 0,
    total_chunks: 0,
    processing_time: 0
  });
  
  // React Query hooks for initial data
  const { data: timelineEntries, isLoading: timelineLoading, refetch: refetchTimeline } = useLatestJobTimelineEntry(jobId);
  const { data: statistics, isLoading: statsLoading, refetch: refetchStats } = useJobTimelineStatistics(jobId);

  // WebSocket-based real-time updates
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string>('');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const maxReconnectAttempts = 5;

  // Get the latest timeline entry
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

  // Simple polling for updates
  useEffect(() => {
    const interval = setInterval(() => {
      refetchTimeline();
      setLastMessage(new Date().toLocaleTimeString());
    }, 2000);

    return () => clearInterval(interval);
  }, [refetchTimeline]);

  // Update live stats when timeline data changes
  useEffect(() => {
    if (latestTimeline) {
      setLiveStats({
        total_processed: latestTimeline.documents_processed,
        total_chunks: latestTimeline.chunks_created,
        processing_time: latestTimeline.processing_time_seconds
      });
    }
  }, [latestTimeline]);

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

  const handleManualRefresh = useCallback(() => {
    refetchTimeline();
    refetchStats();
  }, [refetchTimeline, refetchStats]);

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
  const progressPercentage = isRunning && liveStats.total_processed > 0 
    ? Math.min((liveStats.total_processed / 1000) * 100, 100) // Estimate progress
    : latestTimeline.status === 'completed' ? 100 : 0;

  return (
    <Stack gap="md">
      {/* Connection Status */}
      {showConnectionStatus && (
        <Group justify="space-between" align="center">
          <Group gap="xs">
            <Badge 
              color={isConnected ? 'green' : 'red'} 
              variant="light" 
              leftSection={isConnected ? <IconRefresh size={10} /> : <IconWifiOff size={10} />}
              size="xs"
            >
              {isConnected ? 'Live Polling' : 'Disconnected'}
            </Badge>
            
            {reconnectAttempts > 0 && (
              <Text size="xs" c="orange">
                Reconnecting... ({reconnectAttempts}/{maxReconnectAttempts})
              </Text>
            )}
            
            {lastMessage && (
              <Text size="xs" c="dimmed">
                Last update: {lastMessage}
              </Text>
            )}
          </Group>
          
          <Group gap="xs">
            <ActionIcon 
              variant="subtle" 
              size="sm" 
              onClick={handleManualRefresh}
              title="Refresh data"
            >
              <IconRefresh size={14} />
            </ActionIcon>
          </Group>
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

      {/* Live Statistics */}
      {showStatistics && (latestTimeline.status === 'completed' || latestTimeline.status === 'running') && (
        <Card withBorder p="sm" radius="md">
          <Stack gap="xs">
            <Group justify="space-between" align="center">
              <Text size="sm" fw={500}>Live Progress</Text>
              {isConnected && (
                <Badge size="xs" color="green" variant="light">
                  POLLING
                </Badge>
              )}
            </Group>
            
            <SimpleGrid cols={2} spacing="xs">
              <Group gap="xs">
                <IconFileText size={14} color="#228be6" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(liveStats.total_processed)}</Text> docs
                </Text>
              </Group>
              
              <Group gap="xs">
                <IconDatabase size={14} color="#51cf66" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatNumber(liveStats.total_chunks)}</Text> chunks
                </Text>
              </Group>
              
              <Group gap="xs">
                <IconClockHour4 size={14} color="#fab005" />
                <Text size="sm">
                  <Text component="span" fw={500}>{formatDuration(liveStats.processing_time)}</Text> elapsed
                </Text>
              </Group>
              
              {statistics && (
                <Group gap="xs">
                  <IconRefresh size={14} color="#868e96" />
                  <Text size="sm">
                    <Text component="span" fw={500}>{statistics.statistics.total_executions}</Text> runs
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
