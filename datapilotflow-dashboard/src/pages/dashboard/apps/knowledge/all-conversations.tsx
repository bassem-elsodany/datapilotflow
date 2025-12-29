import { DataTable } from '@/components/data-table';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Grid,
  Group,
  Loader,
  Modal,
  Select,
  Stack,
  Switch,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconBrain,
  IconCalendar,
  IconEdit,
  IconMessages,
  IconPlus,
  IconRobot,
  IconTrash,
} from '@tabler/icons-react';
import { DataTableColumn } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Agent {
  id: string;
  name: string;
  agent_type: 'rag' | 'assistant';
}

interface Conversation {
  id: string;
  name: string;
  agent_id: string;
  description?: string;
  created_at: string;
  last_updated: string;
  last_message_at?: string;
  message_count: number;
}

type SortableFields = Pick<Conversation, 'name' | 'created_at' | 'last_updated' | 'message_count'>;

export default function AllConversationsPage() {
  const navigate = useNavigate();

  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [agentsList, setAgentsList] = useState<Agent[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<Conversation | null>(null);

  // Create conversation modal state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [newConversationName, setNewConversationName] = useState('');
  const [newConversationDescription, setNewConversationDescription] = useState('');
  const [newConversationTags, setNewConversationTags] = useState<string[]>([]);

  // Rename modal state
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [conversationToRename, setConversationToRename] = useState<Conversation | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  // Grouping state
  const [groupByAgent, setGroupByAgent] = useState(true);

  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  const breadcrumbs = useMemo(() => [
    { label: 'Dashboard', href: paths.dashboard.root },
    { label: 'Apps', href: paths.dashboard.apps.root },
    { label: 'Conversations' },
  ], []);

  useEffect(() => {
    loadAgents();
    loadConversations();
  }, []);

  const loadAgents = async () => {
    try {
      const token = localStorage.getItem('jwt_token');

      const response = await fetch(buildApiUrl('/agents'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const agentArray: Agent[] = (data.agents || []).map((agent: any) => ({
          id: agent.id,
          name: agent.name,
          agent_type: agent.agent_type,
        }));
        setAgentsList(agentArray);

        // Convert to lookup map
        const agentMap: Record<string, Agent> = {};
        agentArray.forEach((agent) => {
          agentMap[agent.id] = agent;
        });
        setAgents(agentMap);
      }
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('jwt_token');

      // Fetch ALL conversations (no agent_id filter)
      const response = await fetch(buildApiUrl('/conversations'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data.sessions || []);
      } else {
        console.error('Failed to load conversations:', response.status);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const openConversation = (conversationId: string) => {
    navigate(paths.dashboard.apps.conversation(conversationId));
  };

  const openCreateModal = () => {
    // Auto-populate default name with timestamp
    const defaultName = `Conversation - ${new Date().toLocaleString()}`;
    setNewConversationName(defaultName);
    setNewConversationDescription('');
    setNewConversationTags([]);
    setSelectedAgentId(null);
    setCreateModalOpen(true);
  };

  const closeCreateModal = () => {
    setCreateModalOpen(false);
    setNewConversationName('');
    setNewConversationDescription('');
    setNewConversationTags([]);
    setSelectedAgentId(null);
  };

  const handleAgentChange = (agentId: string | null) => {
    setSelectedAgentId(agentId);
    // Update conversation name with agent name prefix
    if (agentId && agents[agentId]) {
      const agentName = agents[agentId].name;
      setNewConversationName(`${agentName} - ${new Date().toLocaleString()}`);
    }
  };

  const createNewConversation = async () => {
    if (!selectedAgentId) {
      notifications.show({
        title: 'Validation Error',
        message: 'Please select an agent',
        color: 'red',
      });
      return;
    }

    if (!newConversationName.trim()) {
      notifications.show({
        title: 'Validation Error',
        message: 'Conversation name is required',
        color: 'red',
      });
      return;
    }

    try {
      setIsCreating(true);
      const token = localStorage.getItem('jwt_token');

      const response = await fetch(buildApiUrl('/conversations'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: selectedAgentId,
          name: newConversationName.trim(),
          description: newConversationDescription.trim() || undefined,
          tags: newConversationTags.length > 0 ? newConversationTags : undefined,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        notifications.show({
          title: 'Success',
          message: 'Conversation created successfully',
          color: 'green',
        });
        closeCreateModal();
        // Navigate to the conversation
        navigate(paths.dashboard.apps.conversation(data.id));
      } else {
        const errorData = await response.json();
        notifications.show({
          title: 'Error',
          message: errorData.detail || 'Failed to create conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error creating conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to create conversation',
        color: 'red',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const deleteConversation = async (conversationId: string) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(buildApiUrl(`/conversations/${conversationId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadConversations();
        setDeleteModalOpen(false);
        setConversationToDelete(null);
        notifications.show({
          title: 'Success',
          message: 'Conversation deleted successfully',
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to delete conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to delete conversation',
        color: 'red',
      });
    }
  };

  const openDeleteModal = (conversation: Conversation) => {
    setConversationToDelete(conversation);
    setDeleteModalOpen(true);
  };

  const openRenameModal = (conversation: Conversation) => {
    setConversationToRename(conversation);
    setRenameValue(conversation.name);
    setRenameModalOpen(true);
  };

  const renameConversation = async () => {
    if (!conversationToRename || !renameValue.trim()) return;

    setIsRenaming(true);
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(buildApiUrl(`/conversations/${conversationToRename.id}/name`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_name: renameValue.trim() }),
      });

      if (response.ok) {
        await loadConversations();
        setRenameModalOpen(false);
        setConversationToRename(null);
        setRenameValue('');
        notifications.show({
          title: 'Success',
          message: 'Conversation renamed successfully',
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to rename conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error renaming conversation:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to rename conversation',
        color: 'red',
      });
    } finally {
      setIsRenaming(false);
    }
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
      column: 'last_updated',
    },
    tabsConfig: {
      tabs: [
        {
          value: '*',
          label: 'All',
          counter: conversations?.length,
        },
      ],
    },
  });

  // Apply sorting to conversations
  const sortedConversations = useMemo(() => {
    if (!conversations) return [];

    if (!sort.status.columnAccessor) return conversations;

    const { columnAccessor, direction } = sort.status;
    return [...conversations].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (columnAccessor) {
        case 'name':
          aValue = a.name?.toLowerCase() || '';
          bValue = b.name?.toLowerCase() || '';
          break;
        case 'created_at':
          aValue = a.created_at ? new Date(a.created_at).getTime() : 0;
          bValue = b.created_at ? new Date(b.created_at).getTime() : 0;
          break;
        case 'last_updated':
          aValue = (a.last_message_at || a.last_updated) ? new Date(a.last_message_at || a.last_updated).getTime() : 0;
          bValue = (b.last_message_at || b.last_updated) ? new Date(b.last_message_at || b.last_updated).getTime() : 0;
          break;
        case 'message_count':
          aValue = a.message_count || 0;
          bValue = b.message_count || 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [conversations, sort.status]);

  // Group conversations by agent
  const groupedConversations = useMemo(() => {
    if (!groupByAgent || !conversations.length) return undefined;

    // Group by agent_id
    const groupMap: Record<string, Conversation[]> = {};
    conversations.forEach((conv) => {
      const agentId = conv.agent_id || 'unknown';
      if (!groupMap[agentId]) {
        groupMap[agentId] = [];
      }
      groupMap[agentId].push(conv);
    });

    // Convert to groups and sort
    const groups = Object.entries(groupMap).map(([agentId, items]) => {
      const agent = agents[agentId];

      // Sort conversations within group by last activity (newest first)
      const sortedItems = [...items].sort((a, b) => {
        const aTime = new Date(a.last_message_at || a.last_updated).getTime();
        const bTime = new Date(b.last_message_at || b.last_updated).getTime();
        return bTime - aTime;
      });

      return {
        id: agentId,
        agentName: agent?.name || 'Unknown Agent',
        agentType: agent?.agent_type || 'unknown',
        title: (
          <Group gap="xs">
            {agent?.agent_type === 'assistant' ? (
              <IconRobot size={18} color="var(--mantine-color-violet-6)" />
            ) : (
              <IconBrain size={18} color="var(--mantine-color-blue-6)" />
            )}
            <Text fw={600} size="sm">
              {agent?.name || 'Unknown Agent'}
            </Text>
            <Badge size="sm" variant="light" color={agent?.agent_type === 'assistant' ? 'violet' : 'blue'}>
              {agent?.agent_type?.toUpperCase() || 'UNKNOWN'}
            </Badge>
            <Badge size="sm" variant="outline" color="gray">
              {sortedItems.length} conversation{sortedItems.length !== 1 ? 's' : ''}
            </Badge>
          </Group>
        ),
        items: sortedItems,
      };
    });

    // Sort groups: RAG agents first, then Assistant, then alphabetically by name within each type
    groups.sort((a, b) => {
      // RAG comes before Assistant
      if (a.agentType === 'rag' && b.agentType === 'assistant') return -1;
      if (a.agentType === 'assistant' && b.agentType === 'rag') return 1;
      // Same type: sort alphabetically by name
      return a.agentName.localeCompare(b.agentName);
    });

    return groups;
  }, [conversations, groupByAgent, agents]);

  const columns: DataTableColumn<Conversation>[] = useMemo(
    () => {
      const baseColumns: DataTableColumn<Conversation>[] = [
        {
          accessor: 'name',
          title: 'Conversation',
          width: groupByAgent ? 400 : 300,
          sortable: !groupByAgent,
          render: (conversation) => (
            <Stack gap={2}>
              <Tooltip label="Click to open conversation">
                <Text
                  fw={500}
                  size="sm"
                  style={{
                    cursor: 'pointer',
                    color: 'var(--mantine-color-blue-6)',
                    textDecoration: 'none',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.textDecoration = 'underline';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.textDecoration = 'none';
                  }}
                  onClick={() => openConversation(conversation.id)}
                >
                  {conversation.name || `Conversation ${conversation.id.slice(0, 8)}`}
                </Text>
              </Tooltip>
              {conversation.description && (
                <Text size="xs" c="dimmed" lineClamp={2}>
                  {conversation.description}
                </Text>
              )}
            </Stack>
          ),
        },
      ];

      // Only show Agent column when not grouping
      if (!groupByAgent) {
        baseColumns.push({
          accessor: 'agent_id',
          title: 'Agent',
          width: 200,
          render: (conversation) => {
            const agent = agents[conversation.agent_id];
            if (!agent) {
              return (
                <Text size="sm" c="dimmed">Unknown Agent</Text>
              );
            }
            return (
              <Tooltip label={`View agent: ${agent.name}`}>
                <Group gap="xs" style={{ cursor: 'pointer' }} onClick={() => navigate(paths.dashboard.apps.agentConversations(agent.id))}>
                  {agent.agent_type === 'assistant' ? (
                    <IconRobot size={16} color="var(--mantine-color-violet-6)" />
                  ) : (
                    <IconBrain size={16} color="var(--mantine-color-blue-6)" />
                  )}
                  <Text size="sm" c="blue.6" style={{ textDecoration: 'none' }}
                    onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                    onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                  >
                    {agent.name}
                  </Text>
                  <Badge size="xs" variant="light" color={agent.agent_type === 'assistant' ? 'violet' : 'blue'}>
                    {agent.agent_type}
                  </Badge>
                </Group>
              </Tooltip>
            );
          },
        });
      }

      baseColumns.push(
        {
          accessor: 'message_count',
          title: 'Messages',
          width: 100,
          sortable: !groupByAgent,
          render: (conversation) => (
            <Group gap="xs">
              <IconMessages size={16} />
              <Text size="sm">{conversation.message_count || 0}</Text>
            </Group>
          ),
        },
        {
          accessor: 'created_at',
          title: 'Created',
          width: 180,
          sortable: !groupByAgent,
          render: (conversation) => (
            <Group gap="xs">
              <IconCalendar size={16} />
              <Text size="sm">{formatDate(conversation.created_at)}</Text>
            </Group>
          ),
        },
        {
          accessor: 'last_updated',
          title: 'Last Activity',
          width: 180,
          sortable: !groupByAgent,
          render: (conversation) => (
            <Text size="sm">{formatDate(conversation.last_message_at || conversation.last_updated)}</Text>
          ),
        },
        {
          accessor: 'actions',
          title: 'Actions',
          width: 100,
          render: (conversation) => (
            <Group gap="xs">
              <Tooltip label="Rename">
                <ActionIcon
                  variant="subtle"
                  color="blue"
                  onClick={(e) => {
                    e.stopPropagation();
                    openRenameModal(conversation);
                  }}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="Delete">
                <ActionIcon
                  variant="subtle"
                  color="red"
                  onClick={(e) => {
                    e.stopPropagation();
                    openDeleteModal(conversation);
                  }}
                >
                  <IconTrash size={16} />
                </ActionIcon>
              </Tooltip>
            </Group>
          ),
        }
      );

      return baseColumns;
    },
    [agents, groupByAgent]
  );

  if (isLoading) {
    return (
      <Page title="Conversations">
        <Box ta="center" py="xl">
          <Loader size="lg" />
          <Text mt="md" c="dimmed">Loading conversations...</Text>
        </Box>
      </Page>
    );
  }

  return (
    <Page title="Conversations">
      <PageHeader
        title="All Conversations"
        breadcrumbs={breadcrumbs}
      />

      <Grid mt="md">
        <Grid.Col span={12}>
          <DataTable.Container>
            <DataTable.Title
              title="Conversations"
              description="All conversation threads across all agents"
              actions={
                <Group gap="md">
                  <Group gap="xs">
                    <Text size="sm" c="dimmed">Group by Agent</Text>
                    <Switch
                      checked={groupByAgent}
                      onChange={(e) => setGroupByAgent(e.currentTarget.checked)}
                      size="sm"
                    />
                  </Group>
                  <Button
                    variant="default"
                    size="xs"
                    leftSection={<IconPlus size="1rem" />}
                    onClick={openCreateModal}
                    disabled={agentsList.length === 0}
                  >
                    New Conversation
                  </Button>
                </Group>
              }
            />
            <DataTable.Tabs tabs={tabs.tabs} onChange={tabs.change} />
            <DataTable.Filters filters={filters.filters} onClear={filters.clear} />
            <DataTable.Content>
              {conversations.length === 0 ? (
                <Box ta="center" py="xl">
                  <IconMessages size={48} color="var(--mantine-color-gray-4)" />
                  <Text size="lg" c="dimmed" mt="md">
                    No conversations yet
                  </Text>
                  <Text size="sm" c="dimmed" mb="lg">
                    Create an agent and start a conversation.
                  </Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => navigate(paths.dashboard.apps.agents)}
                    size="md"
                  >
                    Go to Agents
                  </Button>
                </Box>
              ) : groupByAgent && groupedConversations ? (
                // Grouped view - show conversations grouped by agent
                <Stack gap="xl">
                  {groupedConversations.map((group) => {
                    const isAssistant = agents[group.id]?.agent_type === 'assistant';
                    const borderColor = isAssistant ? 'var(--mantine-color-violet-5)' : 'var(--mantine-color-blue-5)';
                    const bgGradient = isAssistant 
                      ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(139, 92, 246, 0.02) 100%)'
                      : 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(59, 130, 246, 0.02) 100%)';
                    
                    return (
                      <Box
                        key={group.id}
                        style={{
                          border: '1px solid var(--mantine-color-gray-3)',
                          borderRadius: 'var(--mantine-radius-md)',
                          overflow: 'hidden',
                          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
                        }}
                      >
                        {/* Agent Header */}
                        <Box
                          py="md"
                          px="lg"
                          style={{
                            background: bgGradient,
                            borderBottom: '1px solid var(--mantine-color-gray-3)',
                            borderLeft: `4px solid ${borderColor}`,
                          }}
                        >
                          {group.title}
                        </Box>
                        
                        {/* Conversations Table */}
                        <Box p="xs" style={{ backgroundColor: 'var(--mantine-color-white)' }}>
                          <DataTable.Table
                            minHeight={80}
                            noRecordsText={DataTable.noRecordsText('conversations')}
                            records={group.items}
                            fetching={isLoading}
                            columns={columns}
                          />
                        </Box>
                      </Box>
                    );
                  })}
                </Stack>
              ) : (
                // Flat view - standard table
                <DataTable.Table
                  minHeight={240}
                  noRecordsText={DataTable.noRecordsText('conversations')}
                  recordsPerPageLabel={DataTable.recordsPerPageLabel('conversations')}
                  paginationText={DataTable.paginationText('conversations')}
                  page={1}
                  records={sortedConversations}
                  fetching={isLoading}
                  onPageChange={() => { }}
                  recordsPerPage={10}
                  totalRecords={sortedConversations.length}
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
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Conversation"
        centered
      >
        <Stack gap="md">
          <Alert icon={<IconTrash size={16} />} color="red" title="Warning">
            <Text size="sm">
              Are you sure you want to delete the conversation "{conversationToDelete?.name}"?
            </Text>
            <Text size="sm" c="dimmed" mt="xs">
              This action cannot be undone. All messages will be permanently deleted.
            </Text>
          </Alert>
          <Group justify="flex-end" gap="xs">
            <Button variant="subtle" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => conversationToDelete && deleteConversation(conversationToDelete.id)}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Rename Conversation Modal */}
      <Modal
        opened={renameModalOpen}
        onClose={() => {
          setRenameModalOpen(false);
          setConversationToRename(null);
          setRenameValue('');
        }}
        title="Rename Conversation"
        size="sm"
        centered
      >
        <Stack gap="md">
          <TextInput
            label="Conversation Name"
            placeholder="Enter new name"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            required
          />
          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setRenameModalOpen(false);
                setConversationToRename(null);
                setRenameValue('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={renameConversation}
              loading={isRenaming}
              disabled={!renameValue.trim() || renameValue === conversationToRename?.name}
            >
              Rename
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Create Conversation Modal */}
      <Modal
        opened={createModalOpen}
        onClose={closeCreateModal}
        title="New Conversation"
        size="md"
      >
        <Stack gap="md">
          <Select
            label="Agent"
            placeholder="Select an agent"
            value={selectedAgentId}
            onChange={handleAgentChange}
            data={agentsList.map(agent => ({
              value: agent.id,
              label: `${agent.name} (${agent.agent_type.toUpperCase()})`,
            }))}
            required
            searchable
            clearable
            leftSection={selectedAgentId && agents[selectedAgentId]?.agent_type === 'assistant'
              ? <IconRobot size={16} />
              : <IconBrain size={16} />
            }
          />
          <TextInput
            label="Conversation Name"
            placeholder="Enter conversation name"
            value={newConversationName}
            onChange={(e) => setNewConversationName(e.currentTarget.value)}
            required
          />
          <Textarea
            label="Description"
            placeholder="Optional description for this conversation"
            value={newConversationDescription}
            onChange={(e) => setNewConversationDescription(e.currentTarget.value)}
            rows={3}
          />
          <TagsInput
            label="Tags"
            placeholder="Press Enter to add tags"
            value={newConversationTags}
            onChange={setNewConversationTags}
            clearable
          />
          <Group justify="flex-end" gap="xs" mt="md">
            <Button variant="subtle" onClick={closeCreateModal}>
              Cancel
            </Button>
            <Button
              onClick={createNewConversation}
              loading={isCreating}
              disabled={!selectedAgentId || !newConversationName.trim()}
            >
              Create Conversation
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}

