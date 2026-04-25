import { useGetJobsWithStatus } from '@/hooks/api/job-status';
import { Card, Grid, Group, Loader, Select, Stack, Text, Title } from '@mantine/core';
import { useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const STATUS_COLORS: Record<string, string> = {
  running: '#228be6',
  completed: '#40c057',
  failed: '#fa5252',
  pending: '#fab005',
  cancelled: '#868e96',
  created: '#15aabf',
};

export function JobStatisticsCharts() {
  const { data: jobs, isLoading } = useGetJobsWithStatus();
  const [timeRange, setTimeRange] = useState('7');

  // Status distribution data for pie chart
  const statusDistributionData = useMemo(() => {
    if (!jobs) return [];

    const statusCounts: Record<string, number> = {};
    jobs.forEach((job) => {
      const status = job.current_status?.status || 'unknown';
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });

    return Object.entries(statusCounts).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      value: count,
      color: STATUS_COLORS[status] || '#868e96',
    }));
  }, [jobs]);

  // Documents processed over time (last 7 days)
  const documentsProcessedData = useMemo(() => {
    if (!jobs) return [];

    const daysAgo = parseInt(timeRange);
    const now = new Date();
    const dataByDate: Record<string, { documents: number; chunks: number }> = {};

    // Initialize last N days
    for (let i = daysAgo - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      dataByDate[dateStr] = { documents: 0, chunks: 0 };
    }

    // Aggregate data by date
    jobs.forEach((job) => {
      if (job.current_status?.completed_at) {
        const completedDate = new Date(job.current_status.completed_at);
        const daysDiff = Math.floor((now.getTime() - completedDate.getTime()) / (1000 * 60 * 60 * 24));

        if (daysDiff < daysAgo && daysDiff >= 0) {
          const dateStr = completedDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          if (dataByDate[dateStr]) {
            dataByDate[dateStr].documents += job.current_status.documents_processed || 0;
            dataByDate[dateStr].chunks += job.current_status.chunks_created || 0;
          }
        }
      }
    });

    return Object.entries(dataByDate).map(([date, data]) => ({
      date,
      documents: data.documents,
      chunks: data.chunks,
    }));
  }, [jobs, timeRange]);

  if (isLoading) {
    return (
      <Group gap="xs">
        <Loader size="xs" />
        <Text size="xs" c="dimmed">Loading statistics…</Text>
      </Group>
    );
  }

  if (!jobs || jobs.length === 0) return null;

  return (
    <Grid gutter="sm">
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder p="sm" radius="sm">
          <Stack gap={4}>
            <Text size="xs" fw={600} tt="uppercase" c="dimmed">Status Distribution</Text>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={statusDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={60}
                  dataKey="value"
                >
                  {statusDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </Stack>
        </Card>
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder p="sm" radius="sm">
          <Stack gap={4}>
            <Group justify="space-between" align="center">
              <Text size="xs" fw={600} tt="uppercase" c="dimmed">Processing Activity</Text>
              <Select
                value={timeRange}
                onChange={(value) => setTimeRange(value || '7')}
                data={[
                  { value: '7', label: 'Last 7 days' },
                  { value: '14', label: 'Last 14 days' },
                  { value: '30', label: 'Last 30 days' },
                ]}
                w={120}
                size="xs"
              />
            </Group>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={documentsProcessedData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" style={{ fontSize: 10 }} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="left" style={{ fontSize: 10 }} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="right" orientation="right" style={{ fontSize: 10 }} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ fontSize: 11 }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <Card withBorder p="xs" shadow="sm">
                          <Text size="xs" fw={500}>{payload[0].payload.date}</Text>
                          <Text size="xs" c="blue">Docs: {payload[0].value}</Text>
                          <Text size="xs" c="green">Chunks: {payload[1]?.value}</Text>
                        </Card>
                      );
                    }
                    return null;
                  }}
                />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                <Area yAxisId="left" type="monotone" dataKey="documents" stroke="#228be6" fill="#228be6" fillOpacity={0.2} name="Docs" />
                <Area yAxisId="right" type="monotone" dataKey="chunks" stroke="#40c057" fill="#40c057" fillOpacity={0.2} name="Chunks" />
              </AreaChart>
            </ResponsiveContainer>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );
}

