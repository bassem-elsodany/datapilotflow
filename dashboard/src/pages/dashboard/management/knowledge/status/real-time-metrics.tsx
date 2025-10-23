import {
  PiCheckCircleDuotone,
  PiClockDuotone,
  PiFileTextDuotone,
  PiXCircleDuotone,
  PiPlayCircleDuotone,
} from 'react-icons/pi';
import { Group, Loader, SimpleGrid, Text } from '@mantine/core';
import { MetricCard } from '@/components/metric-card';
import { useGetJobsWithStatus } from '@/hooks/api/job-status';
import { formatInt } from '@/utilities/number';

export function RealTimeMetrics() {
  const { data: jobs, isLoading } = useGetJobsWithStatus();

  const totalJobs = jobs?.length || 0;
  const runningJobs = jobs?.filter(job => job.is_running).length || 0;
  const completedJobs = jobs?.filter(job => job.current_status?.status === 'completed').length || 0;
  const failedJobs = jobs?.filter(job => job.current_status?.status === 'failed').length || 0;
  const pendingJobs = jobs?.filter(job => job.current_status?.status === 'pending').length || 0;

  // Calculate total documents processed and chunks created
  const totalDocumentsProcessed = jobs?.reduce((sum, job) => {
    return sum + (job.current_status?.documents_processed || 0);
  }, 0) || 0;

  const totalChunksCreated = jobs?.reduce((sum, job) => {
    return sum + (job.current_status?.chunks_created || 0);
  }, 0) || 0;

  const cards = [
    { 
      icon: PiFileTextDuotone, 
      title: 'Total Jobs', 
      value: totalJobs, 
      color: 'blue',
      description: 'All knowledge processing jobs'
    },
    { 
      icon: PiPlayCircleDuotone, 
      title: 'Running', 
      value: runningJobs, 
      color: 'blue',
      description: 'Currently executing'
    },
    { 
      icon: PiCheckCircleDuotone, 
      title: 'Completed', 
      value: completedJobs, 
      color: 'green',
      description: 'Successfully finished'
    },
    { 
      icon: PiClockDuotone, 
      title: 'Pending', 
      value: pendingJobs, 
      color: 'yellow',
      description: 'Waiting to start'
    },
    { 
      icon: PiXCircleDuotone, 
      title: 'Failed', 
      value: failedJobs, 
      color: 'red',
      description: 'Execution failed'
    },
  ];

  return (
    <SimpleGrid cols={{ base: 1, sm: 2, xl: 5 }}>
      {cards.map((card) => (
        <MetricCard.Root key={card.title}>
          <Group>
            <MetricCard.Icon c={card.color}>
              <card.icon size="2rem" />
            </MetricCard.Icon>
            <div>
              <MetricCard.TextMuted>{card.title}</MetricCard.TextMuted>
              <MetricCard.TextEmphasis>
                {isLoading ? <Loader size="sm" color={card.color} /> : formatInt(card.value)}
              </MetricCard.TextEmphasis>
              <Text size="xs" c="dimmed" mt={2}>
                {card.description}
              </Text>
            </div>
          </Group>
        </MetricCard.Root>
      ))}
    </SimpleGrid>
  );
}

