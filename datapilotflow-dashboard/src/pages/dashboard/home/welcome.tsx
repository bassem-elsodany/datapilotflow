import { useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { useGetKnowledgeJobs } from '@/api/resources/knowledge-jobs';
import { useGetVectorDBCollections } from '@/api/resources/vectordb-collections';
import { useGetConversations } from '@/api/resources/conversations';
import { useGetTools } from '@/api/resources/tools';
import { useGetMCPServers } from '@/api/resources/mcp-servers';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Card,
  Divider,
  Grid,
  Group,
  Loader,
  RingProgress,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Tooltip,
} from '@mantine/core';
import {
  IconArrowRight,
  IconBrain,
  IconChartBar,
  IconChevronRight,
  IconCircleCheck,
  IconCircleX,
  IconClock,
  IconDatabase,
  IconFileText,
  IconMessageCircle,
  IconPlayerPlay,
  IconRefresh,
  IconServer,
  IconTool,
  IconUsers,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

// ─── Helpers ────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function getJobStatus(job: any): { label: string; color: string } {
  const timeline = job.timeline || [];
  if (!timeline.length) return { label: 'Pending', color: 'gray' };
  const last = timeline[timeline.length - 1];
  const status = (last?.status || last?.event || '').toLowerCase();
  if (status.includes('complet') || status.includes('success') || status.includes('done'))
    return { label: 'Completed', color: 'green' };
  if (status.includes('fail') || status.includes('error'))
    return { label: 'Failed', color: 'red' };
  if (status.includes('run') || status.includes('progress') || status.includes('execut'))
    return { label: 'Running', color: 'blue' };
  if (status.includes('cancel'))
    return { label: 'Cancelled', color: 'orange' };
  return { label: 'Pending', color: 'gray' };
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
  loading?: boolean;
  error?: boolean;
}

function StatCard({ label, value, sub, icon, color, onClick, loading, error }: StatCardProps) {
  return (
    <Card
      withBorder
      padding="md"
      radius="md"
      style={{ cursor: onClick ? 'pointer' : 'default', transition: 'box-shadow 0.15s' }}
      onClick={onClick}
    >
      <Group justify="space-between" wrap="nowrap">
        <div>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>{label}</Text>
          {loading ? (
            <Skeleton height={28} width={48} />
          ) : error ? (
            <Title order={2} fw={700} c="dimmed">—</Title>
          ) : (
            <Title order={2} fw={700}>{value}</Title>
          )}
          {sub && !loading && !error && <Text size="xs" c="dimmed" mt={2}>{sub}</Text>}
        </div>
        <ThemeIcon size={44} radius="md" variant="light" color={error ? 'gray' : color}>
          {icon}
        </ThemeIcon>
      </Group>
      {onClick && !error && (
        <Text size="xs" c={color} mt="xs" fw={500}>
          View all <IconChevronRight size={10} style={{ verticalAlign: 'middle' }} />
        </Text>
      )}
    </Card>
  );
}

// ─── Quick Action ─────────────────────────────────────────────────────────────

interface QuickActionProps {
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
}

function QuickAction({ label, description, icon, color, onClick }: QuickActionProps) {
  return (
    <Card withBorder padding="sm" radius="md" style={{ cursor: 'pointer' }} onClick={onClick}>
      <Group gap="sm" wrap="nowrap">
        <ThemeIcon size={36} radius="md" variant="light" color={color} style={{ flexShrink: 0 }}>
          {icon}
        </ThemeIcon>
        <div style={{ minWidth: 0 }}>
          <Text size="sm" fw={600} truncate>{label}</Text>
          <Text size="xs" c="dimmed" lineClamp={1}>{description}</Text>
        </div>
        <ActionIcon variant="subtle" color="gray" ml="auto" style={{ flexShrink: 0 }}>
          <IconArrowRight size={14} />
        </ActionIcon>
      </Group>
    </Card>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function Welcome() {
  const navigate = useNavigate();

  const { data: sources = [], isLoading: loadingSources } = useGetKnowledgeSourceConfigs();
  const { data: jobs = [], isLoading: loadingJobs, refetch: refetchJobs } = useGetKnowledgeJobs();
  const { data: collections = [], isLoading: loadingCollections, isError: errorCollections } = useGetVectorDBCollections({ retry: 1 } as any);
  const { data: conversationsData, isLoading: loadingConversations } = useGetConversations();
  const conversationCount = conversationsData?.total_count ?? conversationsData?.sessions?.length ?? 0;
  const { data: tools = [], isLoading: loadingTools } = useGetTools();
  const { data: mcpServers = [], isLoading: loadingMCP } = useGetMCPServers();

  const activeTools = tools.filter(t => t.is_active).length;
  const activeMCP = mcpServers.filter(s => s.is_active).length;

  const recentJobs = [...jobs]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 6);

  const completedJobs = jobs.filter(j => getJobStatus(j).color === 'green').length;
  const failedJobs = jobs.filter(j => getJobStatus(j).color === 'red').length;
  const runningJobs = jobs.filter(j => getJobStatus(j).color === 'blue').length;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <Stack gap="xl" py="md">

      {/* ── Header ── */}
      <Group justify="space-between" align="flex-end">
        <div>
          <Text size="sm" c="dimmed" fw={500}>{greeting}</Text>
          <Title order={2} fw={700}>DataPilotFlow</Title>
          <Text size="sm" c="dimmed" mt={2}>
            End-to-end RAG platform — from ingestion and indexing to retrieval and querying
          </Text>
        </div>
        <Group gap="xs">
          <Button
            size="xs"
            variant="default"
            leftSection={<IconPlayerPlay size={13} />}
            onClick={() => navigate(paths.dashboard.apps.conversations)}
          >
            New Conversation
          </Button>
          <Button
            size="xs"
            variant="filled"
            leftSection={<IconDatabase size={13} />}
            onClick={() => navigate(paths.dashboard.management.knowledgeSources.configs)}
          >
            Manage Knowledge
          </Button>
        </Group>
      </Group>

      {/* ── KPI Strip ── */}
      <SimpleGrid cols={{ base: 2, sm: 3, lg: 6 }} spacing="sm">
        <StatCard
          label="Knowledge Sources"
          value={loadingSources ? '—' : sources.length}
          icon={<IconFileText size={20} />}
          color="blue"
          loading={loadingSources}
          onClick={() => navigate(paths.dashboard.management.knowledgeSources.configs)}
        />
        <StatCard
          label="Ingestion Jobs"
          value={loadingJobs ? '—' : jobs.length}
          sub={runningJobs > 0 ? `${runningJobs} running` : `${completedJobs} completed`}
          icon={<IconChartBar size={20} />}
          color="violet"
          loading={loadingJobs}
          onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs)}
        />
        <StatCard
          label="Collections"
          value={collections.length}
          icon={<IconDatabase size={20} />}
          color="teal"
          loading={loadingCollections}
          error={errorCollections}
          onClick={() => navigate(paths.dashboard.management.knowledge.vectorStatus)}
        />
        <StatCard
          label="Conversations"
          value={conversationCount}
          icon={<IconMessageCircle size={20} />}
          color="cyan"
          loading={loadingConversations}
          onClick={() => navigate(paths.dashboard.apps.conversations)}
        />
        <StatCard
          label="Active Tools"
          value={loadingTools ? '—' : `${activeTools}/${tools.length}`}
          icon={<IconTool size={20} />}
          color="orange"
          loading={loadingTools}
          onClick={() => navigate(paths.dashboard.management.tools.list)}
        />
        <StatCard
          label="MCP Servers"
          value={loadingMCP ? '—' : `${activeMCP}/${mcpServers.length}`}
          icon={<IconServer size={20} />}
          color="grape"
          loading={loadingMCP}
          onClick={() => navigate(paths.dashboard.management.tools.list)}
        />
      </SimpleGrid>

      {/* ── Main Body ── */}
      <Grid gutter="md">

        {/* ── Recent Jobs ── */}
        <Grid.Col span={{ base: 12, lg: 8 }}>
          <Card withBorder padding="md" radius="md" h="100%">
            <Group justify="space-between" mb="md">
              <div>
                <Text fw={600} size="sm">Recent Ingestion Jobs</Text>
                <Text size="xs" c="dimmed">Latest knowledge processing activity</Text>
              </div>
              <Group gap="xs">
                {jobs.length > 0 && (
                  <Group gap={6}>
                    {completedJobs > 0 && (
                      <Badge size="xs" color="green" variant="light" leftSection={<IconCircleCheck size={10} />}>
                        {completedJobs} done
                      </Badge>
                    )}
                    {failedJobs > 0 && (
                      <Badge size="xs" color="red" variant="light" leftSection={<IconCircleX size={10} />}>
                        {failedJobs} failed
                      </Badge>
                    )}
                    {runningJobs > 0 && (
                      <Badge size="xs" color="blue" variant="light">
                        {runningJobs} running
                      </Badge>
                    )}
                  </Group>
                )}
                <Tooltip label="Refresh" withArrow>
                  <ActionIcon variant="subtle" size="sm" onClick={() => refetchJobs()}>
                    <IconRefresh size={14} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            </Group>

            {loadingJobs ? (
              <Stack gap="xs">
                {[1, 2, 3, 4].map(i => <Skeleton key={i} height={44} radius="sm" />)}
              </Stack>
            ) : recentJobs.length === 0 ? (
              <Stack align="center" py="xl" gap="sm">
                <ThemeIcon size={48} variant="light" color="gray" radius="xl">
                  <IconChartBar size={24} />
                </ThemeIcon>
                <Text size="sm" c="dimmed">No ingestion jobs yet</Text>
                <Button
                  size="xs"
                  variant="light"
            onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs)}
            >
              Create first job
            </Button>
              </Stack>
            ) : (
              <Stack gap={6}>
                {recentJobs.map(job => {
                  const status = getJobStatus(job);
                  return (
                    <Box
                      key={job.id}
                      px="sm"
                      py="xs"
                      style={{
                        borderRadius: 'var(--mantine-radius-sm)',
                        cursor: 'pointer',
                        transition: 'background 0.1s',
                      }}
                      bg="var(--mantine-color-default-hover)"
                      onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs)}
                    >
                      <Group justify="space-between" wrap="nowrap">
                        <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
                          <ThemeIcon size={28} radius="sm" variant="light" color={status.color} style={{ flexShrink: 0 }}>
                            {status.color === 'blue' ? <Loader size={12} /> : <IconChartBar size={14} />}
                          </ThemeIcon>
                          <div style={{ minWidth: 0 }}>
                            <Text size="sm" fw={500} truncate>{job.name}</Text>
                            <Text size="xs" c="dimmed" truncate>
                              {job.description || 'No description'}
                            </Text>
                          </div>
                        </Group>
                        <Group gap="sm" wrap="nowrap" style={{ flexShrink: 0 }}>
                          <Badge size="xs" color={status.color} variant="light">{status.label}</Badge>
                          <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                            <IconClock size={10} style={{ verticalAlign: 'middle', marginRight: 2 }} />
                            {timeAgo(job.created_at)}
                          </Text>
                        </Group>
                      </Group>
                    </Box>
                  );
                })}
                <Button
                  variant="subtle"
                  size="xs"
                  rightSection={<IconArrowRight size={12} />}
                  mt="xs"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs)}
                >
                  View all jobs
                </Button>
              </Stack>
            )}
          </Card>
        </Grid.Col>

        {/* ── Right Column ── */}
        <Grid.Col span={{ base: 12, lg: 4 }}>
          <Stack gap="md" h="100%">

            {/* Job Health Ring */}
            {jobs.length > 0 && (
              <Card withBorder padding="md" radius="md">
                <Text fw={600} size="sm" mb="sm">Job Health</Text>
                <Group justify="center" gap="lg">
                  <RingProgress
                    size={90}
                    thickness={10}
                    roundCaps
                    sections={[
                      { value: jobs.length > 0 ? (completedJobs / jobs.length) * 100 : 0, color: 'green' },
                      { value: jobs.length > 0 ? (failedJobs / jobs.length) * 100 : 0, color: 'red' },
                      { value: jobs.length > 0 ? (runningJobs / jobs.length) * 100 : 0, color: 'blue' },
                    ]}
                    label={
                      <Text ta="center" size="xs" fw={700}>
                        {jobs.length > 0 ? Math.round((completedJobs / jobs.length) * 100) : 0}%
                      </Text>
                    }
                  />
                  <Stack gap={4}>
                    <Group gap={6}><Box w={8} h={8} style={{ borderRadius: 2, background: 'var(--mantine-color-green-6)' }} /><Text size="xs" c="dimmed">Completed ({completedJobs})</Text></Group>
                    <Group gap={6}><Box w={8} h={8} style={{ borderRadius: 2, background: 'var(--mantine-color-red-6)' }} /><Text size="xs" c="dimmed">Failed ({failedJobs})</Text></Group>
                    <Group gap={6}><Box w={8} h={8} style={{ borderRadius: 2, background: 'var(--mantine-color-blue-6)' }} /><Text size="xs" c="dimmed">Running ({runningJobs})</Text></Group>
                    <Group gap={6}><Box w={8} h={8} style={{ borderRadius: 2, background: 'var(--mantine-color-gray-4)' }} /><Text size="xs" c="dimmed">Other ({jobs.length - completedJobs - failedJobs - runningJobs})</Text></Group>
                  </Stack>
                </Group>
              </Card>
            )}

            {/* Quick Actions */}
            <Card withBorder padding="md" radius="md" style={{ flex: 1 }}>
              <Text fw={600} size="sm" mb="sm">Quick Actions</Text>
              <Stack gap="xs">
                <QuickAction
                  label="Add Knowledge Source"
                  description="Web, files, or Confluence"
                  icon={<IconFileText size={18} />}
                  color="blue"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.configs)}
                />
                <QuickAction
                  label="Run Ingestion Job"
                  description="Process and embed content"
                  icon={<IconPlayerPlay size={18} />}
                  color="violet"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs)}
                />
                <QuickAction
                  label="Start Conversation"
                  description="Chat with your knowledge base"
                  icon={<IconMessageCircle size={18} />}
                  color="cyan"
                  onClick={() => navigate(paths.dashboard.apps.conversations)}
                />
                <QuickAction
                  label="Manage AI Models"
                  description="Configure LLM providers"
                  icon={<IconBrain size={18} />}
                  color="orange"
                  onClick={() => navigate(paths.dashboard.management.modelProviders.list)}
                />
                <QuickAction
                  label="Manage Tools & MCP"
                  description="Tools and MCP server registry"
                  icon={<IconTool size={18} />}
                  color="grape"
                  onClick={() => navigate(paths.dashboard.management.tools.list)}
                />
                <QuickAction
                  label="User Management"
                  description="Roles, users, and permissions"
                  icon={<IconUsers size={18} />}
                  color="teal"
                  onClick={() => navigate(paths.dashboard.management.users.list)}
                />
              </Stack>
            </Card>
          </Stack>
        </Grid.Col>
      </Grid>

      {/* ── Platform Modules ── */}
      <Divider label={<Text size="xs" c="dimmed" fw={500}>Platform Modules</Text>} labelPosition="left" />

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="sm">
        {[
          {
            title: 'Knowledge Pipeline',
            desc: 'Ingest, chunk, and embed documents into vector collections.',
            color: 'blue',
            icon: <IconDatabase size={18} />,
            path: paths.dashboard.management.knowledgeSources.configs,
            stat: `${sources.length} source${sources.length !== 1 ? 's' : ''} · ${collections.length} collection${collections.length !== 1 ? 's' : ''}`,
          },
          {
            title: 'AI Conversations',
            desc: 'Context-aware RAG conversations backed by your knowledge base.',
            color: 'cyan',
            icon: <IconMessageCircle size={18} />,
            path: paths.dashboard.apps.conversations,
            stat: `${conversationCount} conversation${conversationCount !== 1 ? 's' : ''}`,
          },
          {
            title: 'Tool Ecosystem',
            desc: 'Prompt-based tools and MCP remote tool integrations.',
            color: 'orange',
            icon: <IconTool size={18} />,
            path: paths.dashboard.management.tools.list,
            stat: `${activeTools} active tools · ${activeMCP} MCP server${activeMCP !== 1 ? 's' : ''}`,
          },
          {
            title: 'Model Registry',
            desc: 'Manage LLM and embedding model providers across the platform.',
            color: 'violet',
            icon: <IconBrain size={18} />,
            path: paths.dashboard.management.modelProviders.list,
            stat: 'Multi-provider support',
          },
        ].map(({ title, desc, color, icon, path, stat }) => (
          <Card
            key={title}
            withBorder
            padding="md"
            radius="md"
            style={{ cursor: 'pointer' }}
            onClick={() => navigate(path)}
          >
            <Group mb="xs" justify="space-between">
              <ThemeIcon size={32} radius="sm" variant="light" color={color}>
                {icon}
              </ThemeIcon>
              <ActionIcon variant="subtle" color="gray" size="sm">
                <IconArrowRight size={14} />
              </ActionIcon>
            </Group>
            <Text fw={600} size="sm" mb={4}>{title}</Text>
            <Text size="xs" c="dimmed" mb="sm" lineClamp={2}>{desc}</Text>
            <Text size="xs" c={color} fw={500}>{stat}</Text>
          </Card>
        ))}
      </SimpleGrid>

    </Stack>
  );
}
