/**
 * Pipeline Runner Component
 * 
 * Execution monitoring and control panel for pipeline runs.
 * Displays real-time status, logs, and statistics.
 */

import React from 'react';
import { 
  Paper, 
  Title, 
  Text, 
  ScrollArea, 
  Badge, 
  Button, 
  Group, 
  Stack,
  Progress,
  Alert
} from '@mantine/core';
import { 
  IconPlayerPlay, 
  IconPlayerStop, 
  IconCheck, 
  IconX, 
  IconClock, 
  IconRefresh,
  IconDownload,
  IconAlertCircle
} from '@tabler/icons-react';

interface PipelineRunnerProps {
  isRunning: boolean;
}

export function PipelineRunner({ isRunning }: PipelineRunnerProps) {
  // Mock data for demonstration
  const logs = [
    "2023-10-27 10:00:00 - INFO: Pipeline started...",
    "2023-10-27 10:00:05 - DEBUG: Web Crawler node started.",
    "2023-10-27 10:00:15 - INFO: Extracted 10 documents from URL.",
    "2023-10-27 10:00:20 - DEBUG: Text Chunker node started.",
    "2023-10-27 10:00:30 - INFO: Created 100 chunks.",
    "2023-10-27 10:00:35 - DEBUG: Embedding Generator node started.",
    "2023-10-27 10:00:45 - INFO: Generated embeddings for 100 chunks.",
    "2023-10-27 10:00:50 - DEBUG: Vector Database node started.",
    "2023-10-27 10:01:00 - INFO: Stored 100 chunks in vector database.",
    "2023-10-27 10:01:05 - SUCCESS: Pipeline completed successfully!",
  ];

  const statistics = {
    totalNodes: 5,
    completedNodes: isRunning ? 3 : 5,
    failedNodes: 0,
    processingTime: isRunning ? '45s' : '1m 5s',
    documentsProcessed: isRunning ? 7 : 10,
    chunksCreated: isRunning ? 70 : 100,
  };

  return (
    <Paper shadow="xs" p="md" withBorder>
      <Title order={4} mb="md">
        Pipeline Status & Logs{' '}
        <Badge
          variant="light"
          color={isRunning ? 'blue' : 'gray'}
          leftSection={isRunning ? <IconPlayerPlay size={12} /> : <IconPlayerStop size={12} />}
        >
          {isRunning ? 'Running' : 'Idle'}
        </Badge>
      </Title>
      
      <Stack gap="md">
        {/* Statistics */}
        <Group justify="space-between">
          <Group>
            <Text size="sm" fw={500}>Progress:</Text>
            <Text size="sm" c="dimmed">
              {statistics.completedNodes}/{statistics.totalNodes} nodes completed
            </Text>
          </Group>
          <Group>
            <Text size="sm" fw={500}>Time:</Text>
            <Text size="sm" c="dimmed">{statistics.processingTime}</Text>
          </Group>
        </Group>
        
        <Progress 
          value={(statistics.completedNodes / statistics.totalNodes) * 100} 
          size="sm" 
          color={isRunning ? 'blue' : 'green'}
        />
        
        {/* Statistics Grid */}
        <Group justify="space-between">
          <Group>
            <Text size="sm" fw={500}>Documents:</Text>
            <Text size="sm" c="dimmed">{statistics.documentsProcessed}</Text>
          </Group>
          <Group>
            <Text size="sm" fw={500}>Chunks:</Text>
            <Text size="sm" c="dimmed">{statistics.chunksCreated}</Text>
          </Group>
          <Group>
            <Text size="sm" fw={500}>Failed:</Text>
            <Text size="sm" c="dimmed">{statistics.failedNodes}</Text>
          </Group>
        </Group>
        
        {/* Logs */}
        <div>
          <Group justify="space-between" mb="xs">
            <Text size="sm" fw={500}>Execution Logs</Text>
            <Group gap="xs">
              <Button size="xs" variant="light" leftSection={<IconDownload size={12} />}>
                Export
              </Button>
              <Button size="xs" variant="light" leftSection={<IconRefresh size={12} />}>
                Refresh
              </Button>
            </Group>
          </Group>
          
          <ScrollArea h={200} style={{ border: '1px solid #e0e0e0', borderRadius: '4px' }} p="xs">
            <Stack gap={4}>
              {logs.map((log, index) => (
                <Text key={index} size="xs" style={{ fontFamily: 'monospace' }}>
                  {log}
                </Text>
              ))}
              {!isRunning && logs.length === 0 && (
                <Text size="sm" c="dimmed">No logs available. Run a pipeline to see output.</Text>
              )}
            </Stack>
          </ScrollArea>
        </div>
      </Stack>
    </Paper>
  );
}