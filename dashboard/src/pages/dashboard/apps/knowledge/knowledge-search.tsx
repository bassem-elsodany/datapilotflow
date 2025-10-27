import { DataTable } from '@/components/data-table';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import { ActionIcon, Alert, Badge, Box, Button, Grid, Group, Menu, Modal, Stack, Text, TextInput, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconCalendar,
  IconDots,
  IconEdit,
  IconEye,
  IconMessageCircle,
  IconMessages,
  IconPlus,
  IconTrash
} from '@tabler/icons-react';
import { DataTableColumn } from 'mantine-datatable';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Conversation {
  id: string; // MongoDB _id
  sessionName: string;
  messageCount: number;
  messages?: Message[];
  createdAt?: string;
  updatedAt?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

type SortableFields = Pick<Conversation, 'sessionName' | 'messageCount' | 'createdAt' | 'updatedAt'>;

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Apps', href: paths.dashboard.apps.root },
  { label: 'Knowledge Conversations' },
];

export default function KnowledgeSearch() {
  const navigate = useNavigate();
  const [conversationHistory, setConversationHistory] = useState<Conversation[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [sessionToRename, setSessionToRename] = useState<Conversation | null>(null);
  const [newSessionName, setNewSessionName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<Conversation | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // API functions using centralized config
  const buildApiUrl = (endpoint: string) => {
    return apiUtils.buildApiUrl(endpoint);
  };

  // Load conversation history
  useEffect(() => {
    loadConversationHistory();
  }, []);

  const loadConversationHistory = async () => {
    try {
      setIsLoading(true);
      console.log('🔄 Loading conversation history...');
      const token = localStorage.getItem('jwt_token');
      console.log('🔑 Token available:', !!token);

      const response = await fetch(buildApiUrl('/conversations'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('📡 Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('📦 API Response:', data);

        // Map backend response to frontend interface
        const mappedSessions = (data.sessions || []).map((session: any) => ({
          id: session.id,
          sessionName: session.name,
          messageCount: session.message_count,
          createdAt: session.created_at,
          updatedAt: session.created_at, // Backend doesn't provide updated_at, use created_at
        }));

        console.log('🗺️ Mapped sessions:', mappedSessions);
        setConversationHistory(mappedSessions);
      } else {
        console.error('❌ Failed to load conversation history:', response.status);
        const errorText = await response.text();
        console.error('📄 Error response:', errorText);
      }
    } catch (error) {
      console.error('💥 Error loading conversation history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToCreateConversation = () => {
    navigate(paths.dashboard.apps.conversationCreate);
  };

  const selectConversation = async (sessionId: string) => {
    // Navigate to the conversation window
    navigate(paths.dashboard.apps.conversation(sessionId));
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(buildApiUrl(`/conversations/${sessionId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadConversationHistory();
        // If the deleted session was the current one, create a new session
        if (sessionId === currentSessionId) {
          await createNewConversation();
        }
        // Close the delete modal
        setDeleteModalOpen(false);
        setSessionToDelete(null);
        // Show success notification
        notifications.show({
          title: 'Success',
          message: 'Conversation deleted successfully',
          color: 'green',
        });
      } else {
        console.error('Failed to delete session:', response.status);
        notifications.show({
          title: 'Error',
          message: 'Failed to delete conversation',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to delete conversation',
        color: 'red',
      });
    }
  };

  const renameSession = async (sessionToRename: { sessionId: string; newName: string }) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(buildApiUrl(`/conversations/${sessionToRename.sessionId}/name`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_name: sessionToRename.newName }),
      });

      if (response.ok) {
        await loadConversationHistory();
        setRenameModalOpen(false);
        setSessionToRename(null);
      } else {
        console.error('Failed to rename session:', response.status);
      }
    } catch (error) {
      console.error('Error renaming session:', error);
    }
  };

  const openRenameModal = (session: Conversation) => {
    setSessionToRename(session);
    setNewSessionName(session.sessionName);
    setRenameModalOpen(true);
  };

  const openDeleteModal = (session: Conversation) => {
    setSessionToDelete(session);
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
      column: 'updatedAt',
    },
    tabsConfig: {
      tabs: [
        {
          value: '*',
          label: 'All',
          counter: conversationHistory?.length,
        },
        {
          value: 'current',
          label: 'Current',
          color: 'blue',
          counter: conversationHistory?.filter(session => session.id === currentSessionId).length,
        },
      ],
    },
  });

  const filteredSessions = useMemo(() => {
    if (!conversationHistory) return [];

    return conversationHistory.filter(session => {
      const currentMatch = tabs.value === '*' ||
        (tabs.value === 'current' && session.id === currentSessionId);

      return currentMatch;
    }).map(session => ({
      ...session,
      id: session.id // Use MongoDB _id
    }));
  }, [conversationHistory, tabs.value, currentSessionId]);

  const columns: DataTableColumn<Conversation>[] = useMemo(
    () => [
      {
        accessor: 'sessionName',
        title: 'Session Name',
        width: 300,
        sortable: true,
        render: (session) => (
          <Group gap="xs">
            <Tooltip label="Click to open conversation">
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
                onClick={() => navigate(paths.dashboard.apps.conversation(session.id))}
              >
                {session.sessionName}
              </Text>
            </Tooltip>
            {session.id === currentSessionId && (
              <Badge size="xs" color="blue">Current</Badge>
            )}
          </Group>
        ),
      },
      {
        accessor: 'messageCount',
        title: 'Messages',
        width: 120,
        sortable: true,
        render: (session) => (
          <Group gap="xs">
            <IconMessages size={16} />
            <Text size="sm">{session.messageCount || 0}</Text>
          </Group>
        ),
      },
      {
        accessor: 'createdAt',
        title: 'Created',
        width: 200,
        sortable: true,
        render: (session) => (
          <Group gap="xs">
            <IconCalendar size={16} />
            <Text size="sm">{formatDate(session.createdAt)}</Text>
          </Group>
        ),
      },
      {
        accessor: 'updatedAt',
        title: 'Updated',
        width: 200,
        sortable: true,
        render: (session) => (
          <Group gap="xs">
            <IconCalendar size={16} />
            <Text size="sm">{formatDate(session.updatedAt)}</Text>
          </Group>
        ),
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 150,
        render: (session) => (
          <Group gap="xs">
            <Button
              variant="subtle"
              size="xs"
              leftSection={<IconEye size="1rem" />}
              onClick={() => selectConversation(session.id)}
            >
              Open
            </Button>
            <Menu>
              <Menu.Target>
                <ActionIcon variant="light" size="sm">
                  <IconDots size={16} />
                </ActionIcon>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item
                  leftSection={<IconEdit size={16} />}
                  onClick={() => openRenameModal(session)}
                >
                  Rename
                </Menu.Item>
                <Menu.Item
                  leftSection={<IconTrash size={16} />}
                  color="red"
                  onClick={() => openDeleteModal(session)}
                >
                  Delete
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        ),
      },
    ],
    [currentSessionId]
  );

  return (
    <Page title="Knowledge Conversations">
      <PageHeader title="Knowledge Conversations" breadcrumbs={breadcrumbs} />

      <Grid>
        <Grid.Col span={12}>
          <DataTable.Container>
            <DataTable.Title
              title="Conversation Sessions"
              description="Manage your conversation sessions and search knowledge base"
              actions={
                <Button
                  variant="default"
                  size="xs"
                  leftSection={<IconPlus size="1rem" />}
                  onClick={navigateToCreateConversation}
                  loading={isLoading}
                >
                  New Session
                </Button>
              }
            />
            <DataTable.Tabs tabs={tabs.tabs} onChange={tabs.change} />
            <DataTable.Filters filters={filters.filters} onClear={filters.clear} />
            <DataTable.Content>
              {filteredSessions.length === 0 && !isLoading ? (
                <Box ta="center" py="xl">
                  <IconMessageCircle size={48} color="var(--mantine-color-gray-4)" />
                  <Text size="lg" c="dimmed" mt="md">
                    No conversation sessions found
                  </Text>
                  <Text size="sm" c="dimmed" mb="lg">
                    Start your first conversation to search and interact with the knowledge base.
                  </Text>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={navigateToCreateConversation}
                    size="md"
                  >
                    Start New Conversation
                  </Button>
                </Box>
              ) : (
                <DataTable.Table
                  minHeight={240}
                  noRecordsText={DataTable.noRecordsText('session')}
                  recordsPerPageLabel={DataTable.recordsPerPageLabel('sessions')}
                  paginationText={DataTable.paginationText('sessions')}
                  page={1}
                  records={filteredSessions}
                  fetching={isLoading}
                  onPageChange={() => { }}
                  recordsPerPage={10}
                  totalRecords={filteredSessions.length}
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

      {/* Rename Modal */}
      <Modal
        opened={renameModalOpen}
        onClose={() => {
          setRenameModalOpen(false);
          setSessionToRename(null);
        }}
        title="Rename Conversation"
        size="md"
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Enter a new name for the conversation "{sessionToRename?.sessionName}".
          </Text>
          <TextInput
            label="New Name"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            placeholder="Enter conversation name"
            maxLength={100}
          />
          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setRenameModalOpen(false);
                setSessionToRename(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (sessionToRename && newSessionName.trim()) {
                  renameSession({
                    sessionId: sessionToRename.id,
                    newName: newSessionName.trim()
                  });
                }
              }}
              disabled={!newSessionName.trim()}
            >
              Rename
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setSessionToDelete(null);
        }}
        title="Delete Conversation"
        size="md"
      >
        <Stack gap="md">
          <Alert icon={<IconTrash size={16} />} title="Warning" color="red">
            <Text size="sm">
              Are you sure you want to delete the conversation "{sessionToDelete?.sessionName}"?
            </Text>
            <Text size="sm" mt="xs">
              This action cannot be undone. All messages and conversation history will be permanently deleted.
            </Text>
          </Alert>
          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              onClick={() => {
                setDeleteModalOpen(false);
                setSessionToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => {
                if (sessionToDelete) {
                  deleteSession(sessionToDelete.id);
                }
              }}
            >
              Delete Conversation
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}


