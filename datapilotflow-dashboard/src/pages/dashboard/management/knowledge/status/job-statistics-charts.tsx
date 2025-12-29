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
      <Card withBorder p="xl">
        <Group justify="center">
          <Loader size="lg" />
          <Text>Loading statistics...</Text>
        </Group>
      </Card>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center">No job data available for charts</Text>
      </Card>
    );
  }

  return (
    <Grid>
      {/* Status Distribution Pie Chart */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder p="md">
          <Stack gap="md">
            <Title order={5}>Status Distribution</Title>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={statusDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Processing Activity Over Time */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder p="md">
          <Stack gap="md">
            <Group justify="space-between">
              <Title order={5}>Processing Activity</Title>
              <Select
                value={timeRange}
                onChange={(value) => setTimeRange(value || '7')}
                data={[
                  { value: '7', label: 'Last 7 days' },
                  { value: '14', label: 'Last 14 days' },
                  { value: '30', label: 'Last 30 days' },
                ]}
                w={140}
                size="xs"
              />
            </Group>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={documentsProcessedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" style={{ fontSize: '12px' }} />
                <YAxis yAxisId="left" style={{ fontSize: '12px' }} />
                <YAxis yAxisId="right" orientation="right" style={{ fontSize: '12px' }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <Card withBorder p="xs" shadow="sm">
                          <Text size="sm" fw={500}>{payload[0].payload.date}</Text>
                          <Text size="sm" c="blue">Documents: {payload[0].value}</Text>
                          <Text size="sm" c="green">Chunks: {payload[1]?.value}</Text>
                        </Card>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="documents"
                  stroke="#228be6"
                  fill="#228be6"
                  fillOpacity={0.3}
                  name="Documents"
                />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="chunks"
                  stroke="#40c057"
                  fill="#40c057"
                  fillOpacity={0.3}
                  name="Chunks"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );
}

