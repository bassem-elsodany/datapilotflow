import { DataTable } from '@/components/data-table';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import { ActionIcon, Alert, Badge, Box, Button, Grid, Group, Modal, Stack, Text, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconBrain,
  IconCalendar,
  IconClock,
  IconEdit,
  IconMessages,
  IconPlus,
  IconRobot,
  IconTool,
  IconTrash
} from '@tabler/icons-react';
import { DataTableColumn } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ExpandedTool {
  id: string;
  name: string;
  display_name: string;
  description: string;
  tool_type: string;
  is_active: boolean;
  tags: string[];
}

interface Agent {
  id: string;
  name: string;
  description?: string;
  agent_type: 'rag' | 'assistant';
  conversation_count?: number;
  assistant_config?: {
    enabled: boolean;
    tools?: ExpandedTool[] | string[];  // Can be expanded objects or IDs
    instructions?: string;
  };
  created_at?: string;
  updated_at?: string;
}

type SortableFields = Pick<Agent, 'name' | 'agent_type' | 'created_at' | 'updated_at'>;

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Apps', href: paths.dashboard.apps.root },
  { label: 'Agents', href: paths.dashboard.apps.agents },
];

export default function AgentsPage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);

  // API functions using centralized config
  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  // Load agents list
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('jwt_token');

      const response = await fetch(buildApiUrl('/agents?expand=tools'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
      } else {
        console.error('❌ Failed to load agents:', response.status);
        const errorText = await response.text();
        console.error('📄 Error response:', errorText);
      }
    } catch (error) {
      console.error('💥 Error loading agents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToCreateAgent = () => {
    navigate(paths.dashboard.apps.agentCreate);
  };

  const viewAgentConversations = (agentId: string) => {
    navigate(paths.dashboard.apps.agentConversations(agentId));
  };

  const editAgent = (agentId: string) => {
    navigate(paths.dashboard.apps.agentEdit(agentId));
  };

  const deleteAgent = async (agentId: string) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(buildApiUrl(`/agents/${agentId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAgents();
        setDeleteModalOpen(false);
        setAgentToDelete(null);
        notifications.show({
          title: 'Success',
          message: 'Agent deleted successfully',
          color: 'green',
        });
      } else if (response.status === 409) {
        // Agent has conversations
        const data = await response.json();
        notifications.show({
          title: 'Cannot Delete',
          message: data.detail || 'Agent has conversations. Delete conversations first.',
          color: 'orange',
        });
        setDeleteModalOpen(false);
        setAgentToDelete(null);
      } else {
        console.error('Failed to delete agent:', response.status);
        notifications.show({
          title: 'Error',
          message: 'Failed to delete agent',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error deleting agent:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to delete agent',
        color: 'red',
      });
    }
  };

  const openDeleteModal = (agent: Agent) => {
    setAgentToDelete(agent);
    setDeleteModalOpen(true);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
    } catch {
      return 'Invalid date';
    }
  };

  const { tabs, filters, sort } = DataTable.useDataTable<SortableFields>({
    sortConfig: {
      direction: 'desc',
      column: 'updated_at',
    },
    tabsConfig: {
      tabs: [
        {
          value: '*',
          label: 'All',
          counter: agents?.length,
        },
        {
          value: 'rag',
          label: 'RAG',
          color: 'blue',
          counter: agents?.filter(a => a.agent_type === 'rag').length,
        },
        {
          value: 'assistant',
          label: 'Assistant',
          color: 'violet',
          counter: agents?.filter(a => a.agent_type === 'assistant').length,
        },
      ],
    },
  });

  const filteredAgents = useMemo(() => {
    if (!agents) return [];

    // Filter by tab
    let filtered = agents.filter(agent => {
      if (tabs.value === '*') return true;
      return agent.agent_type === tabs.value;
    });

    // Apply sorting
    if (sort.status.columnAccessor) {
      const { columnAccessor, direction } = sort.status;
      filtered = [...filtered].sort((a, b) => {
        let aValue: any;
        let bValue: any;

        switch (columnAccessor) {
          case 'name':
            aValue = a.name?.toLowerCase() || '';
            bValue = b.name?.toLowerCase() || '';
            break;
          case 'agent_type':
            aValue = a.agent_type || '';
            bValue = b.agent_type || '';
            break;
          case 'created_at':
            aValue = a.created_at ? new Date(a.created_at).getTime() : 0;
            bValue = b.created_at ? new Date(b.created_at).getTime() : 0;
            break;
          case 'updated_at':
            aValue = a.updated_at ? new Date(a.updated_at).getTime() : 0;
            bValue = b.updated_at ? new Date(b.updated_at).getTime() : 0;
            break;
          default:
            return 0;
        }

        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [agents, tabs.value, sort.status]);

  const columns: DataTableColumn<Agent>[] = useMemo(
    () => [
      {
        accessor: 'name',
        title: 'Name',
        width: 300,
        sortable: true,
        render: (agent) => (
          <Group gap="xs" align="flex-start">
            <Stack gap={2} style={{ flex: 1 }}>
              <Tooltip label="Click to view conversations">
                <Text
                  fw={500}
                  size="sm"
                  style={{
                    cursor: 'pointer',
                    color: 'var(--mantine-color-blue-6)',
                    textDecoration: 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.textDecoration = 'underline';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.textDecoration = 'none';
                  }}
                  onClick={() => viewAgentConversations(agent.id)}
                >
                  {agent.name}
                </Text>
              </Tooltip>
              {agent.description && (
                <Text size="xs" c="dimmed" lineClamp={2}>
                  {agent.description}
                </Text>
              )}
            </Stack>
          </Group>
        ),
      },
      {
        accessor: 'agent_type',
        title: 'Type',
        width: 150,
        sortable: true,
        render: (agent) => {
          const isAssistant = agent.agent_type === 'assistant';
          return (
            <Badge
              variant="light"
              color={isAssistant ? 'violet' : 'blue'}
              leftSection={isAssistant ? <IconRobot size={14} /> : <IconBrain size={14} />}
            >
              {isAssistant ? 'Assistant' : 'RAG'}
            </Badge>
          );
        },
      },
      {
        accessor: 'conversation_count',
        title: 'Conversations',
        width: 120,
        sortable: false,
        render: (agent) => (
          <Group gap="xs">
            <IconMessages size={16} />
            <Text size="sm">{agent.conversation_count || 0}</Text>
          </Group>
        ),
      },
      {
        accessor: 'tools',
        title: 'Tools',
        width: 100,
        render: (agent) => {
          if (agent.agent_type !== 'assistant') {
            return <Text size="sm" c="dimmed">—</Text>;
          }
          const tools = agent.assistant_config?.tools || [];
          const toolsCount = tools.length;

          // Get display names from expanded tools
          const toolNames = tools.map((tool) => {
            if (typeof tool === 'string') return tool;
            return tool.display_name || tool.name;
          });

          const tooltipContent = toolsCount > 0
            ? toolNames.map((name, idx) => <div key={idx} style={{ whiteSpace: 'nowrap' }}>{name}</div>)
            : 'No tools bound';
          return (
            <Tooltip label={tooltipContent} multiline>
              <Group gap="xs">
                <IconTool size={16} color={toolsCount > 0 ? 'var(--mantine-color-green-6)' : 'var(--mantine-color-gray-5)'} />
                <Text size="sm" c={toolsCount > 0 ? undefined : 'dimmed'}>{toolsCount}</Text>
              </Group>
            </Tooltip>
          );
        },
      },
      {
        accessor: 'created_at',
        title: 'Created',
        width: 160,
        sortable: true,
        render: (agent) => (
          <Group gap="xs">
            <IconCalendar size={16} />
            <Text size="sm">{formatDate(agent.created_at)}</Text>
          </Group>
        ),
      },
      {
        accessor: 'updated_at',
        title: 'Updated',
        width: 160,
        sortable: true,
        render: (agent) => (
          <Group gap="xs">
            <IconClock size={16} />
            <Text size="sm">{formatDate(agent.updated_at)}</Text>
          </Group>
        ),
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 150,
        render: (agent) => (
          <Group gap="xs" wrap="nowrap">
            <Tooltip label="View Conversations">
              <ActionIcon
                variant="light"
                color="blue"
                size="md"
                onClick={() => viewAgentConversations(agent.id)}
              >
                <IconMessages size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Edit Agent">
              <ActionIcon
                variant="light"
                color="gray"
                size="md"
                onClick={() => editAgent(agent.id)}
              >
                <IconEdit size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete">
              <ActionIcon
                variant="light"
                color="red"
                size="md"
                onClick={() => openDeleteModal(agent)}
              >
                <IconTrash size={18} />
              </ActionIcon>
            </Tooltip>
          </Group>
        ),
      },
    ],
    []
  );

  return (
    <Page title="Agents">
      <PageHeader title="AI Agents" breadcrumbs={breadcrumbs} />

      <Grid>
        <Grid.Col span={12}>
          <DataTable.Container>
            <DataTable.Title
              title="Manage Agents"
              description="Create and manage reusable AI agents for knowledge search and assistance"
              actions={
                <Button
                  variant="default"
                  size="xs"
                  leftSection={<IconPlus size="1rem" />}
                  onClick={navigateToCreateAgent}
                  loading={isLoading}
                >
                  New Agent
                </Button>
              }
            />
            <DataTable.Tabs tabs={tabs.tabs} onChange={tabs.change} />
            <DataTable.Filters filters={filters.filters} onClear={filters.clear} />
            <DataTable.Content>
              {filteredAgents.length === 0 && !isLoading ? (
                <Box ta="center" py="xl">
                  <IconRobot size={48} color="var(--mantine-color-gray-4)" />
                  <Text size="lg" c="dimmed" mt="md">
                    No agents found
                  </Text>
                  <Text size="sm" c="dimmed" mb="lg">
                    Create your first agent to start building conversations with your knowledge base.
                  </Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={navigateToCreateAgent}
                    size="md"
                  >
                    Create New Agent
                  </Button>
                </Box>
              ) : (
                <DataTable.Table
                  minHeight={240}
                  noRecordsText={DataTable.noRecordsText('agents')}
                  recordsPerPageLabel={DataTable.recordsPerPageLabel('agents')}
                  paginationText={DataTable.paginationText('agents')}
                  page={1}
                  records={filteredAgents}
                  fetching={isLoading}
                  onPageChange={() => { }}
                  recordsPerPage={10}
                  totalRecords={filteredAgents.length}
                  onRecordsPerPageChange={() => { }}
                  recordsPerPageOptions={[5, 10, 20]}
                  sortStatus={sort.status}
                  onSortStatusChange={sort.change}
                  columns={columns}
                />
              )}
            </DataTable.Content>
          </DataTable.Container>
        </Grid.Col>
      </Grid>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setAgentToDelete(null);
        }}
        title="Delete Agent"
        size="md"
      >
        <Stack gap="md">
          {(agentToDelete?.conversation_count || 0) > 0 ? (
            // Agent has conversations - show blocking warning
            <Alert icon={<IconMessages size={16} />} title="Cannot Delete Agent" color="orange">
              <Text size="sm">
                The agent "<Text span fw={600}>{agentToDelete?.name}</Text>" has{' '}
                <Text span fw={600} c="orange">{agentToDelete?.conversation_count} conversation(s)</Text>.
              </Text>
              <Text size="sm" mt="xs">
                You must delete all conversations before deleting this agent.
              </Text>
            </Alert>
          ) : (
            // No conversations - allow deletion
            <Alert icon={<IconTrash size={16} />} title="Confirm Deletion" color="red">
              <Text size="sm">
                Are you sure you want to delete the agent "<Text span fw={600}>{agentToDelete?.name}</Text>"?
              </Text>
              <Text size="sm" mt="xs">
                This action cannot be undone. The agent and its configuration will be permanently deleted.
              </Text>
            </Alert>
          )}
          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setDeleteModalOpen(false);
                setAgentToDelete(null);
              }}
            >
              Cancel
            </Button>
            {(agentToDelete?.conversation_count || 0) > 0 ? (
              <Button
                color="blue"
                leftSection={<IconMessages size={16} />}
                onClick={() => {
                  setDeleteModalOpen(false);
                  if (agentToDelete) {
                    viewAgentConversations(agentToDelete.id);
                  }
                }}
              >
                View Conversations
              </Button>
            ) : (
              <Button
                color="red"
                onClick={() => {
                  if (agentToDelete) {
                    deleteAgent(agentToDelete.id);
                  }
                }}
              >
                Delete Agent
              </Button>
            )}
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}
