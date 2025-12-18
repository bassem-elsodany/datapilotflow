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
  Stack,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
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
import { useNavigate, useParams } from 'react-router-dom';

interface Agent {
  id: string;
  name: string;
  description?: string;
  agent_type: 'rag' | 'assistant';
  tags?: string[];
}

interface Conversation {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  last_updated: string;
  last_message_at?: string;
  message_count: number;
}

type SortableFields = Pick<Conversation, 'name' | 'created_at' | 'last_updated' | 'message_count'>;

export default function AgentConversationsPage() {
  const navigate = useNavigate();
  const { agentId } = useParams<{ agentId: string }>();

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<Conversation | null>(null);

  // Create conversation modal state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newConversationName, setNewConversationName] = useState('');
  const [newConversationDescription, setNewConversationDescription] = useState('');
  const [newConversationTags, setNewConversationTags] = useState<string[]>([]);

  // Rename modal state
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [conversationToRename, setConversationToRename] = useState<Conversation | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  const breadcrumbs = useMemo(() => [
    { label: 'Dashboard', href: paths.dashboard.root },
    { label: 'Apps', href: paths.dashboard.apps.root },
    { label: 'Agents', href: paths.dashboard.apps.agents },
    { label: agent?.name || 'Loading...', href: agentId ? paths.dashboard.apps.agentConversations(agentId) : undefined },
    { label: 'Conversations' },
  ], [agent?.name, agentId]);

  useEffect(() => {
    if (agentId) {
      loadAgent();
      loadConversations();
    }
  }, [agentId]);

  const loadAgent = async () => {
    try {
      const token = localStorage.getItem('jwt_token');

      const response = await fetch(buildApiUrl(`/agents/${agentId}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAgent({
          id: data.id,
          name: data.name,
          description: data.description,
          agent_type: data.agent_type,
          tags: data.tags,
        });
      } else if (response.status === 404) {
        notifications.show({
          title: 'Not Found',
          message: 'Agent not found',
          color: 'red',
        });
        navigate(paths.dashboard.apps.agents);
      } else {
        console.error('❌ Failed to load agent:', response.status);
      }
    } catch (error) {
      console.error('💥 Error loading agent:', error);
    }
  };

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('jwt_token');

      // Fetch conversations filtered by agent_id
      const response = await fetch(buildApiUrl(`/conversations?agent_id=${agentId}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data.sessions || []);
      } else {
        console.error('❌ Failed to load conversations:', response.status);
      }
    } catch (error) {
      console.error('💥 Error loading conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const openCreateModal = () => {
    // Auto-populate default name with agent name and timestamp
    const defaultName = `${agent?.name || 'Agent'} - ${new Date().toLocaleString()}`;
    setNewConversationName(defaultName);
    setNewConversationDescription('');
    setNewConversationTags([]);
    setCreateModalOpen(true);
  };

  const closeCreateModal = () => {
    setCreateModalOpen(false);
    setNewConversationName('');
    setNewConversationDescription('');
    setNewConversationTags([]);
  };

  const createNewConversation = async () => {
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
          agent_id: agentId,
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

  const openConversation = (conversationId: string) => {
    navigate(paths.dashboard.apps.conversation(conversationId));
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

  const columns: DataTableColumn<Conversation>[] = useMemo(
    () => [
      {
        accessor: 'name',
        title: 'Conversation',
        width: 350,
        sortable: true,
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
      {
        accessor: 'message_count',
        title: 'Messages',
        width: 120,
        sortable: true,
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
        sortable: true,
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
        sortable: true,
        render: (conversation) => (
          <Group gap="xs">
            <IconCalendar size={16} />
            <Text size="sm">{formatDate(conversation.last_message_at || conversation.last_updated)}</Text>
          </Group>
        ),
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 120,
        render: (conversation) => (
          <Group gap="xs" wrap="nowrap">
            <Tooltip label="Rename">
              <ActionIcon
                variant="light"
                color="blue"
                size="md"
                onClick={() => openRenameModal(conversation)}
              >
                <IconEdit size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete">
              <ActionIcon
                variant="light"
                color="red"
                size="md"
                onClick={() => openDeleteModal(conversation)}
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

  if (isLoading) {
    return (
      <Page title="Loading...">
        <Box ta="center" py="xl">
          <Loader size="lg" />
          <Text mt="md" c="dimmed">Loading agent conversations...</Text>
        </Box>
      </Page>
    );
  }

  const isAssistant = agent?.agent_type === 'assistant';

  return (
    <Page title={`${agent?.name || 'Agent'} - Conversations`}>
      <PageHeader
        title={
          <Group gap="sm">
            <Badge
              variant="light"
              color={isAssistant ? 'violet' : 'blue'}
              size="lg"
              leftSection={isAssistant ? <IconRobot size={14} /> : <IconBrain size={14} />}
            >
              {isAssistant ? 'Assistant' : 'RAG'}
            </Badge>
            <Text size="xl" fw={600}>{agent?.name}</Text>
          </Group>
        }
        breadcrumbs={breadcrumbs}
      />

      <Grid>
        <Grid.Col span={12}>
          <DataTable.Container>
            <DataTable.Title
              title="Conversations"
              description={agent?.description || 'Manage conversations for this agent'}
              actions={
                <Group gap="xs">
                  <Button
                    variant="subtle"
                    size="xs"
                    leftSection={<IconArrowLeft size="1rem" />}
                    onClick={() => navigate(paths.dashboard.apps.agents)}
                  >
                    Back to Agents
                  </Button>
                  <Button
                    variant="default"
                    size="xs"
                    leftSection={<IconPlus size="1rem" />}
                    onClick={openCreateModal}
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
                    Start your first conversation with this agent.
                  </Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={openCreateModal}
                    size="md"
                  >
                    Start New Conversation
                  </Button>
                </Box>
              ) : (
                <DataTable.Table
                  minHeight={240}
                  noRecordsText={DataTable.noRecordsText('conversations')}
                  recordsPerPageLabel={DataTable.recordsPerPageLabel('conversations')}
                  paginationText={DataTable.paginationText('conversations')}
                  page={1}
                  records={conversations}
                  fetching={isLoading}
                  onPageChange={() => { }}
                  recordsPerPage={10}
                  totalRecords={conversations.length}
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
          setConversationToDelete(null);
        }}
        title="Delete Conversation"
        size="md"
      >
        <Stack gap="md">
          <Alert icon={<IconTrash size={16} />} title="Warning" color="red">
            <Text size="sm">
              Are you sure you want to delete the conversation "{conversationToDelete?.name}"?
            </Text>
            <Text size="sm" mt="xs">
              This action cannot be undone. All messages will be permanently deleted.
            </Text>
          </Alert>
          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setDeleteModalOpen(false);
                setConversationToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => {
                if (conversationToDelete) {
                  deleteConversation(conversationToDelete.id);
                }
              }}
            >
              Delete Conversation
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
          <TextInput
            label="Conversation Name"
            placeholder="Enter conversation name"
            value={newConversationName}
            onChange={(e) => setNewConversationName(e.currentTarget.value)}
            required
            data-autofocus
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
              disabled={!newConversationName.trim()}
            >
              Create Conversation
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}

