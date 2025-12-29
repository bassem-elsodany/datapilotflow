import {
  PiArchiveDuotone,
  PiCheckCircleDuotone,
  PiClockDuotone,
  PiFileTextDuotone,
  PiXCircleDuotone,
} from 'react-icons/pi';
import { Group, Loader, SimpleGrid } from '@mantine/core';
import { MetricCard } from '@/components/metric-card';
import { useGetKnowledgeJobs } from '@/hooks/api/knowledge';
import { formatInt } from '@/utilities/number';

export function KnowledgeMetrics() {
  const { data: jobs, isLoading } = useGetKnowledgeJobs();

  const totalJobs = jobs?.length || 0;
  const completedJobs = jobs?.filter(job => job.status === 'completed').length || 0;
  const processingJobs = jobs?.filter(job => job.status === 'processing' || job.status === 'queued').length || 0;
  const failedJobs = jobs?.filter(job => job.status === 'failed' || job.status === 'error').length || 0;

  const cards = [
    { 
      icon: PiFileTextDuotone, 
      title: 'Total Jobs', 
      value: totalJobs, 
      color: 'blue' 
    },
    { 
      icon: PiCheckCircleDuotone, 
      title: 'Completed', 
      value: completedJobs, 
      color: 'green' 
    },
    { 
      icon: PiClockDuotone, 
      title: 'Processing', 
      value: processingJobs, 
      color: 'orange' 
    },
    { 
      icon: PiXCircleDuotone, 
      title: 'Failed', 
      value: failedJobs, 
      color: 'red' 
    },
  ];

  return (
    <SimpleGrid cols={{ base: 1, sm: 2, xl: 4 }}>
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
            </div>
          </Group>
        </MetricCard.Root>
      ))}
    </SimpleGrid>
  );
}
