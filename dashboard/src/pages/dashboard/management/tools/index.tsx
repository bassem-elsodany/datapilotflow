import { MCPServerConfig, MCPToolDiscovery, useCreateMCPServer, useDeleteMCPServer, useDiscoverMCPTools, useGetMCPServers, useTestMCPConnection, useUpdateMCPServer } from '@/api/resources/mcp-servers';
import { Tool, useDeleteTool, useGetTools, useUpdateTool } from '@/api/resources/tools';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Modal,
  NumberInput,
  PasswordInput,
  Select,
  Stack,
  Table,
  TagsInput,
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconBrain,
  IconCheck,
  IconEdit,
  IconInfoCircle,
  IconPlus,
  IconRefresh,
  IconServer,
  IconTool,
  IconTrash
} from '@tabler/icons-react';
import sortBy from 'lodash/sortBy';
import { DataTable, DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Tools' },
];

const getToolIcon = (toolType: string) => {
  switch (toolType) {
    case 'prompt_based':
      return <IconBrain size={16} />;
    case 'mcp_remote':
      return <IconServer size={16} />;
    default:
      return <IconTool size={16} />;
  }
};

const getToolTypeBadge = (toolType: string) => {
  switch (toolType) {
    case 'prompt_based':
      return <Badge color="purple" size="sm" leftSection={<IconBrain size={12} />}>Prompt-Based</Badge>;
    case 'mcp_remote':
      return <Badge color="blue" size="sm" leftSection={<IconServer size={12} />}>MCP Remote</Badge>;
    default:
      return <Badge color="gray" size="sm">Unknown</Badge>;
  }
};

export default function ToolsManagementPage() {
  const navigate = useNavigate();

  // MCP Servers state
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
  const [serverSortStatus, setServerSortStatus] = useState<DataTableSortStatus<MCPServerConfig>>({
    columnAccessor: 'name',
    direction: 'asc',
  });
  const [deleteServerModalOpened, { open: openDeleteServerModal, close: closeDeleteServerModal }] = useDisclosure(false);
  const [serverFormModalOpened, { open: openServerFormModal, close: closeServerFormModal }] = useDisclosure(false);
  const [selectedServer, setSelectedServer] = useState<MCPServerConfig | null>(null);
  const [editingServerId, setEditingServerId] = useState<string | null>(null);

  // Tools state
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus<Tool>>({
    columnAccessor: 'name',
    direction: 'asc',
  });
  const [deleteModalOpened, { open: openDeleteModal, close: closeDeleteModal }] = useDisclosure(false);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  // Fetch MCP servers and tools
  const { data: mcpServers = [], isLoading: serversLoading, refetch: refetchServers } = useGetMCPServers();
  const { data: tools = [], isLoading: toolsLoading, refetch: refetchTools } = useGetTools();

  const updateToolMutation = useUpdateTool();
  const deleteToolMutation = useDeleteTool();
  const deleteMCPServerMutation = useDeleteMCPServer();
  const createMCPServerMutation = useCreateMCPServer();
  const updateMCPServerMutation = useUpdateMCPServer();
  const discoverMCPMutation = useDiscoverMCPTools();
  const testConnectionMutation = useTestMCPConnection();

  // State for testing connection
  const [discoveredTools, setDiscoveredTools] = useState<MCPToolDiscovery[]>([]);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  // MCP Server form
  const serverForm = useForm({
    initialValues: {
      name: '',
      server_url: 'http://localhost:8880/mcp',
      server_type: 'http_sse',
      auth_type: 'bearer',
      api_key: '',
      bearer_token: '',
      basic_username: '',
      basic_password: '',
      timeout: 60,
      tags: [] as string[],
      is_active: true,
    },
    validate: {
      name: (value) => (!value ? 'Server name is required' : null),
      server_url: (value) => {
        if (!value) return 'Server URL is required';
        try {
          new URL(value);
          return null;
        } catch {
          return 'Please enter a valid URL (e.g., http://localhost:8880/mcp)';
        }
      },
      bearer_token: (value, values) =>
        values.auth_type === 'bearer' && !value ? 'Bearer token is required' : null,
      api_key: (value, values) =>
        values.auth_type === 'api_key' && !value ? 'API key is required' : null,
      basic_username: (value, values) =>
        values.auth_type === 'basic' && !value ? 'Username is required' : null,
      basic_password: (value, values) =>
        values.auth_type === 'basic' && !value ? 'Password is required' : null,
      timeout: (value) => {
        if (!value) return 'Timeout is required';
        if (value < 1 || value > 600) return 'Timeout must be between 1 and 600 seconds';
        return null;
      },
    },
  });

  // Reset and populate form when editing
  useEffect(() => {
    if (editingServerId && serverFormModalOpened) {
      const server = mcpServers.find(s => s.id === editingServerId);
      if (server) {
        const authCreds = server.auth_credentials || {};
        serverForm.setValues({
          name: server.name,
          server_url: server.server_url,
          server_type: server.server_type,
          auth_type: server.auth_type || 'none',
          api_key: authCreds.api_key || '',
          bearer_token: authCreds.bearer_token || '',
          basic_username: authCreds.username || '',
          basic_password: authCreds.password || '',
          timeout: server.timeout || 60,
          tags: server.tags || [],
          is_active: server.is_active,
        });
      }
    } else if (!serverFormModalOpened && !editingServerId) {
      serverForm.reset();
      setDiscoveredTools([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editingServerId, serverFormModalOpened]);

  // Sort MCP servers
  const sortedServers = useMemo(() => {
    const sorted = sortBy(mcpServers, serverSortStatus.columnAccessor);
    return serverSortStatus.direction === 'desc' ? sorted.reverse() : sorted;
  }, [mcpServers, serverSortStatus]);

  // Filter and sort tools
  const filteredTools = useMemo(() => {
    let filtered = tools;

    // Filter by selected MCP server
    if (selectedServerId) {
      filtered = filtered.filter((tool) =>
        tool.tool_type === 'mcp_remote' && tool.mcp_server_id === selectedServerId
      );
    }

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter((tool) =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Active filter
    if (filterActive !== null) {
      filtered = filtered.filter((tool) => tool.is_active === filterActive);
    }

    // Sort
    const sorted = sortBy(filtered, sortStatus.columnAccessor);
    return sortStatus.direction === 'desc' ? sorted.reverse() : sorted;
  }, [tools, selectedServerId, searchQuery, filterActive, sortStatus]);

  const handleDeleteTool = async () => {
    if (!selectedTool) return;

    try {
      await deleteToolMutation.mutateAsync({
        toolId: selectedTool.id,
      });

      notifications.show({
        title: 'Success',
        message: 'Tool deleted successfully',
        color: 'green',
      });

      closeDeleteModal();
      setSelectedTool(null);
      refetchTools();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to delete tool',
        color: 'red',
      });
    }
  };

  const handleQuickToggle = async (tool: Tool) => {
    try {
      await updateToolMutation.mutateAsync({
        toolId: tool.id,
        data: { is_active: !tool.is_active },
      });

      refetchTools();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: 'Failed to toggle tool status',
        color: 'red',
      });
    }
  };

  const handleDeleteMCPServer = async () => {
    if (!selectedServer) return;

    try {
      await deleteMCPServerMutation.mutateAsync({
        serverId: selectedServer.id,
      });

      notifications.show({
        title: 'Success',
        message: 'MCP server deleted successfully',
        color: 'green',
      });

      closeDeleteServerModal();
      setSelectedServer(null);
      if (selectedServerId === selectedServer.id) {
        setSelectedServerId(null);
      }
      refetchServers();
      refetchTools();
    } catch (error: any) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      
      // 409 Conflict means server has related tools
      if (status === 409) {
        notifications.show({
          title: 'Cannot Delete Server',
          message: detail || 'This server has tools associated with it. Delete the tools first.',
          color: 'orange',
          autoClose: 10000, // Show longer for this important message
        });
      } else {
        notifications.show({
          title: 'Error',
          message: detail || 'Failed to delete MCP server',
          color: 'red',
        });
      }
    }
  };

  const handleTestConnection = async () => {
    const values = serverForm.values;

    if (!values.server_url) {
      notifications.show({
        title: 'Error',
        message: 'Please enter a server URL',
        color: 'red',
      });
      return;
    }

    setIsTestingConnection(true);
    setDiscoveredTools([]);

    try {
      const auth_credentials: Record<string, string> = {};

      // Build auth_credentials based on auth_type - ONLY if values are non-empty
      if (values.auth_type === 'bearer') {
        const token = values.bearer_token || values.api_key;
        if (token && token.trim()) {
          auth_credentials.bearer_token = token.trim();
        }
      } else if (values.auth_type === 'api_key') {
        if (values.api_key && values.api_key.trim()) {
          auth_credentials.api_key = values.api_key.trim();
        }
      } else if (values.auth_type === 'basic') {
        if (values.basic_username && values.basic_username.trim()) {
          auth_credentials.username = values.basic_username.trim();
        }
        if (values.basic_password && values.basic_password.trim()) {
          auth_credentials.password = values.basic_password.trim();
        }
      }

      const result = await testConnectionMutation.mutateAsync({
        server_url: values.server_url.trim(),
        server_type: values.server_type || 'http_sse',
        auth_type: values.auth_type && values.auth_type !== 'none' ? values.auth_type : undefined,
        auth_credentials: Object.keys(auth_credentials).length > 0 ? auth_credentials : undefined,
        timeout: values.timeout || 60,
      });

      setDiscoveredTools(result);
      notifications.show({
        title: 'Success',
        message: `Connection successful! Discovered ${result.length} tool(s)`,
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Connection Failed',
        message: error.response?.data?.detail || 'Failed to connect to MCP server',
        color: 'red',
      });
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSubmitMCPServer = async (values: typeof serverForm.values) => {
    try {
      const auth_credentials: Record<string, string> = {};

      // Build auth_credentials based on auth_type - ONLY if values are non-empty
      if (values.auth_type === 'bearer') {
        const token = values.bearer_token || values.api_key;
        if (token && token.trim()) {
          auth_credentials.bearer_token = token.trim();
        }
      } else if (values.auth_type === 'api_key') {
        if (values.api_key && values.api_key.trim()) {
          auth_credentials.api_key = values.api_key.trim();
        }
      } else if (values.auth_type === 'basic') {
        if (values.basic_username && values.basic_username.trim()) {
          auth_credentials.username = values.basic_username.trim();
        }
        if (values.basic_password && values.basic_password.trim()) {
          auth_credentials.password = values.basic_password.trim();
        }
      }

      const payload: any = {
        name: values.name.trim(),
        server_url: values.server_url.trim(),
        server_type: values.server_type,
        auth_type: values.auth_type && values.auth_type !== 'none' ? values.auth_type : undefined,
        auth_credentials: Object.keys(auth_credentials).length > 0 ? auth_credentials : undefined,
        timeout: values.timeout,
        tags: values.tags.filter(t => t.trim()).map(t => t.trim()),
        is_active: values.is_active,
      };

      if (editingServerId) {
        await updateMCPServerMutation.mutateAsync({
          serverId: editingServerId,
          data: payload,
        });
        notifications.show({
          title: 'Success',
          message: 'MCP server updated successfully',
          color: 'green',
        });
      } else {
        await createMCPServerMutation.mutateAsync(payload);
        notifications.show({
          title: 'Success',
          message: 'MCP server created successfully',
          color: 'green',
        });
      }

      closeServerFormModal();
      setEditingServerId(null);
      refetchServers();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || `Failed to ${editingServerId ? 'update' : 'create'} MCP server`,
        color: 'red',
      });
    }
  };

  // MCP Servers table columns
  const serverColumns: DataTableColumn<MCPServerConfig>[] = [
    {
      accessor: 'name',
      title: 'Server Name',
      sortable: true,
      render: (server) => (
        <Group gap="sm">
          <IconServer size={16} />
          <div>
            <Text size="sm" fw={500}>{server.name}</Text>
            <Text size="xs" c="dimmed">{server.server_url}</Text>
          </div>
        </Group>
      ),
    },
    {
      accessor: 'server_type',
      title: 'Type',
      render: () => <Badge size="sm">HTTP</Badge>,
    },
    {
      accessor: 'is_active',
      title: 'Status',
      sortable: true,
      render: (server) => (
        <Badge color={server.is_active ? 'green' : 'gray'} size="sm">
          {server.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      accessor: 'tools_count',
      title: 'Tools',
      render: (server) => {
        const toolsCount = tools.filter(t => t.mcp_server_id === server.id).length;
        return <Badge size="sm" variant="light">{toolsCount} tool(s)</Badge>;
      },
    },
    {
      accessor: 'actions',
      title: 'Actions',
      textAlign: 'right',
      render: (server) => (
        <Group gap={4} justify="flex-end">
          <Tooltip label="Edit">
            <ActionIcon
              variant="subtle"
              color="blue"
              onClick={(e) => {
                e.stopPropagation();
                setEditingServerId(server.id);
                openServerFormModal();
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
                setSelectedServer(server);
                openDeleteServerModal();
              }}
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      ),
    },
  ];

  const columns: DataTableColumn<Tool>[] = [
    {
      accessor: 'name',
      title: 'Tool Name',
      sortable: true,
      render: (tool) => (
        <Group gap="sm">
          {getToolIcon(tool.tool_type)}
          <div>
            <Text size="sm" fw={500}>{tool.display_name}</Text>
            <Text size="xs" c="dimmed">{tool.name}</Text>
          </div>
        </Group>
      ),
    },
    {
      accessor: 'description',
      title: 'Description',
      render: (tool) => (
        <Text size="sm" lineClamp={2}>{tool.description}</Text>
      ),
    },
    {
      accessor: 'tool_type',
      title: 'Type',
      sortable: true,
      render: (tool) => getToolTypeBadge(tool.tool_type),
    },
    {
      accessor: 'is_active',
      title: 'Status',
      sortable: true,
      render: (tool) => (
        <Tooltip label="Click to toggle">
          <Badge
            color={tool.is_active ? 'green' : 'gray'}
            style={{ cursor: 'pointer' }}
            onClick={() => handleQuickToggle(tool)}
          >
            {tool.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </Tooltip>
      ),
    },
    {
      accessor: 'tags',
      title: 'Tags',
      render: (tool) => (
        <Group gap={4}>
          {tool.tags?.slice(0, 2).map((tag, idx) => (
            <Badge key={idx} size="xs" variant="light">{tag}</Badge>
          ))}
          {tool.tags && tool.tags.length > 2 && (
            <Badge size="xs" variant="light">+{tool.tags.length - 2}</Badge>
          )}
        </Group>
      ),
    },
    {
      accessor: 'actions',
      title: 'Actions',
      textAlign: 'right',
      render: (tool) => (
        <Group gap={4} justify="flex-end">
          <Tooltip label="Edit">
            <ActionIcon
              variant="subtle"
              color="blue"
              onClick={() => navigate(paths.dashboard.management.tools.edit(tool.id))}
            >
              <IconEdit size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Delete">
            <ActionIcon
              variant="subtle"
              color="red"
              onClick={() => {
                setSelectedTool(tool);
                openDeleteModal();
              }}
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      ),
    },
  ];

  return (
    <Page title="Tools Management">
      <PageHeader
        title="Tools Management"
        breadcrumbs={breadcrumbs}
      />

      <Stack gap="md">
        {/* MCP Servers Table */}
        <Card>
          <Stack gap="md">
            <Group justify="apart">
              <div>
                <Title order={5}>MCP Servers ({mcpServers.length})</Title>
                <Text size="sm" c="dimmed">
                  {selectedServerId
                    ? `Selected: ${mcpServers.find(s => s.id === selectedServerId)?.name}`
                    : 'Click a row to filter tools by server'}
                </Text>
              </div>
              <Group>
                {selectedServerId && (
                  <Button
                    variant="subtle"
                    size="sm"
                    onClick={() => setSelectedServerId(null)}
                  >
                    Clear Selection
                  </Button>
                )}
                <ActionIcon
                  variant="subtle"
                  onClick={() => refetchServers()}
                  loading={serversLoading}
                >
                  <IconRefresh size={16} />
                </ActionIcon>
                <Button
                  leftSection={<IconPlus size={16} />}
                  onClick={() => {
                    setEditingServerId(null);
                    openServerFormModal();
                  }}
                >
                  Add MCP Server
                </Button>
              </Group>
            </Group>

            {serversLoading ? (
              <Center py="xl">
                <Loader />
              </Center>
            ) : sortedServers.length === 0 ? (
              <Center py="xl">
                <Stack align="center" gap="md">
                  <IconServer size={48} stroke={1.5} color="gray" />
                  <div>
                    <Text size="lg" fw={500} ta="center">No MCP servers configured</Text>
                    <Text size="sm" c="dimmed" ta="center">
                      Add an MCP server to discover and use remote tools
                    </Text>
                  </div>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => {
                      setEditingServerId(null);
                      openServerFormModal();
                    }}
                  >
                    Add MCP Server
                  </Button>
                </Stack>
              </Center>
            ) : (
              <DataTable
                columns={serverColumns}
                records={sortedServers}
                sortStatus={serverSortStatus}
                onSortStatusChange={setServerSortStatus}
                highlightOnHover
                striped
                onRowClick={({ record }) => {
                  if (selectedServerId === record.id) {
                    setSelectedServerId(null);
                  } else {
                    setSelectedServerId(record.id);
                  }
                }}
                rowStyle={(server) => ({
                  cursor: 'pointer',
                  backgroundColor: selectedServerId === server.id ? 'var(--mantine-color-blue-light-hover)' : undefined,
                })}
              />
            )}
          </Stack>
        </Card>

        {/* Tools Table */}
        <Card>
          <Stack gap="md">
            <Group justify="apart">
              <div>
                <Title order={5}>
                  {selectedServerId
                    ? `Tools from ${mcpServers.find(s => s.id === selectedServerId)?.name}`
                    : `All Tools`} ({filteredTools.length})
                </Title>
                <Text size="sm" c="dimmed">
                  {selectedServerId
                    ? 'Showing MCP tools from the selected server'
                    : 'Showing all tools (prompt-based and MCP remote)'}
                </Text>
              </div>
              <Group>
                <TextInput
                  placeholder="Search tools..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.currentTarget.value)}
                  style={{ width: 250 }}
                />
                <Select
                  placeholder="Filter by status"
                  data={[
                    { value: '', label: 'All' },
                    { value: 'true', label: 'Active' },
                    { value: 'false', label: 'Inactive' },
                  ]}
                  value={filterActive === null ? '' : String(filterActive)}
                  onChange={(value) => setFilterActive(value === '' ? null : value === 'true')}
                  style={{ width: 150 }}
                />
                <ActionIcon
                  variant="subtle"
                  onClick={() => refetchTools()}
                  loading={toolsLoading}
                >
                  <IconRefresh size={16} />
                </ActionIcon>
                <Button
                  leftSection={<IconPlus size={16} />}
                  onClick={() => navigate(paths.dashboard.management.tools.create)}
                >
                  Create Tool
                </Button>
              </Group>
            </Group>

            {toolsLoading ? (
              <Center py="xl">
                <Loader />
              </Center>
            ) : filteredTools.length === 0 ? (
              <Center py="xl">
                <Stack align="center" gap="md">
                  <IconTool size={48} stroke={1.5} color="gray" />
                  <div>
                    <Text size="lg" fw={500} ta="center">
                      {selectedServerId ? 'No tools from this server' : 'No tools configured'}
                    </Text>
                    <Text size="sm" c="dimmed" ta="center">
                      {selectedServerId
                        ? 'Create a tool from this MCP server or select a different server'
                        : 'Create your first tool to get started'}
                    </Text>
                  </div>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => navigate(paths.dashboard.management.tools.create)}
                  >
                    Create Tool
                  </Button>
                </Stack>
              </Center>
            ) : (
              <DataTable
                columns={columns}
                records={filteredTools}
                sortStatus={sortStatus}
                onSortStatusChange={setSortStatus}
                highlightOnHover
                striped
              />
            )}
          </Stack>
        </Card>
      </Stack>

      {/* Delete Tool Confirmation Modal */}
      <Modal
        opened={deleteModalOpened}
        onClose={() => {
          closeDeleteModal();
          setSelectedTool(null);
        }}
        title="Delete Tool"
      >
        {selectedTool && (
          <Stack gap="md">
            <Text>
              Are you sure you want to delete <strong>{selectedTool.display_name}</strong>?
              This action cannot be undone.
            </Text>

            <Group justify="flex-end">
              <Button
                variant="subtle"
                onClick={() => {
                  closeDeleteModal();
                  setSelectedTool(null);
                }}
              >
                Cancel
              </Button>
              <Button
                color="red"
                onClick={handleDeleteTool}
                loading={deleteToolMutation.isPending}
              >
                Delete Tool
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>

      {/* Delete MCP Server Confirmation Modal */}
      <Modal
        opened={deleteServerModalOpened}
        onClose={() => {
          closeDeleteServerModal();
          setSelectedServer(null);
        }}
        title="Delete MCP Server"
      >
        {selectedServer && (
          <Stack gap="md">
            <Text>
              Are you sure you want to delete <strong>{selectedServer.name}</strong>?
            </Text>
            
            <Alert color="yellow" icon={<IconAlertCircle />}>
              Note: You cannot delete a server that has tools associated with it. 
              Please delete all related tools first.
            </Alert>

            <Group justify="flex-end">
              <Button
                variant="subtle"
                onClick={() => {
                  closeDeleteServerModal();
                  setSelectedServer(null);
                }}
              >
                Cancel
              </Button>
              <Button
                color="red"
                onClick={handleDeleteMCPServer}
                loading={deleteMCPServerMutation.isPending}
              >
                Delete Server
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>

      {/* MCP Server Form Modal */}
      <Modal
        opened={serverFormModalOpened}
        onClose={() => {
          closeServerFormModal();
          setEditingServerId(null);
          setDiscoveredTools([]);
        }}
        title={
          <Group gap="xs">
            <IconServer size={18} />
            <Text size="sm" fw={600}>{editingServerId ? 'Edit MCP Server' : 'Add MCP Server'}</Text>
          </Group>
        }
        size="lg"
        padding="md"
      >
        <form onSubmit={serverForm.onSubmit(handleSubmitMCPServer)}>
          <Stack gap="sm">
            <Alert color="blue" icon={<IconInfoCircle size={16} />} p="xs">
              <Text size="xs" c="dimmed">
                {editingServerId
                  ? 'Only HTTP Transport (Streamable/SSE) supported'
                  : 'Configure your MCP server. Only HTTP Streamable/SSE transport supported. Test connection before saving.'}
              </Text>
            </Alert>

            <TextInput
              label="Server Name"
              placeholder="My MCP Server"
              description="Friendly name to identify this server"
              required
              size="sm"
              {...serverForm.getInputProps('name')}
            />

            <TextInput
              label="Server URL"
              placeholder="http://localhost:8880/mcp"
              description="HTTP Streamable/SSE endpoint only"
              required
              size="sm"
              {...serverForm.getInputProps('server_url')}
            />

            <Select
              label="Authentication"
              description="How to authenticate with the server"
              data={[
                { value: 'none', label: 'None' },
                { value: 'bearer', label: 'Bearer Token' },
                { value: 'api_key', label: 'API Key' },
                { value: 'basic', label: 'Basic Auth' },
              ]}
              required
              size="sm"
              {...serverForm.getInputProps('auth_type')}
            />

            {serverForm.values.auth_type === 'bearer' && (
              <PasswordInput
                label="Bearer Token"
                placeholder="mcp-secret-key-12345"
                description="Sent as 'Authorization: Bearer YOUR_TOKEN'"
                required
                size="sm"
                {...serverForm.getInputProps('bearer_token')}
              />
            )}

            {serverForm.values.auth_type === 'api_key' && (
              <PasswordInput
                label="API Key"
                placeholder="mcp-secret-key-12345"
                description="Sent as 'X-API-Key' header"
                required
                size="sm"
                {...serverForm.getInputProps('api_key')}
              />
            )}

            {serverForm.values.auth_type === 'basic' && (
              <Group grow>
                <TextInput
                  label="Username"
                  placeholder="admin"
                  description="Basic auth username"
                  required
                  size="sm"
                  {...serverForm.getInputProps('basic_username')}
                />
                <PasswordInput
                  label="Password"
                  placeholder="••••••••"
                  description="Basic auth password"
                  required
                  size="sm"
                  {...serverForm.getInputProps('basic_password')}
                />
              </Group>
            )}

            <Group grow>
              <NumberInput
                label="Timeout (sec)"
                description="Request timeout (1-600 sec)"
                min={1}
                max={600}
                size="sm"
                {...serverForm.getInputProps('timeout')}
              />
              <TagsInput
                label="Tags (Optional)"
                placeholder="Press Enter to add"
                description="Organize servers with tags"
                size="sm"
                {...serverForm.getInputProps('tags')}
              />
            </Group>

            <Divider label="Test Connection" labelPosition="center" my="xs" />

            <Button
              onClick={handleTestConnection}
              loading={isTestingConnection}
              leftSection={<IconServer size={16} />}
              variant="light"
              fullWidth
              size="sm"
            >
              {isTestingConnection ? 'Testing...' : 'Test Connection & Discover Tools'}
            </Button>

            {discoveredTools.length > 0 && (
              <>
                <Alert color="green" icon={<IconCheck size={16} />} p="xs">
                  <Text size="xs">
                    <strong>✓ Connected!</strong> Found {discoveredTools.length} tool(s). You can now save and import them.
                  </Text>
                </Alert>

                <Stack gap={4}>
                  <Text size="xs" fw={500} c="dimmed">Available Tools ({discoveredTools.length}):</Text>
                  <Table highlightOnHover withTableBorder withColumnBorders={false}>
                    <Table.Tbody>
                      {discoveredTools.slice(0, 5).map((tool) => (
                        <Table.Tr key={tool.name}>
                          <Table.Td style={{ padding: '6px 8px' }}>
                            <Text fw={500} size="xs">{tool.name}</Text>
                          </Table.Td>
                          <Table.Td style={{ padding: '6px 8px' }}>
                            <Text size="xs" c="dimmed" lineClamp={1}>
                              {tool.description || 'No description'}
                            </Text>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                  {discoveredTools.length > 5 && (
                    <Text size="xs" c="dimmed" ta="center">
                      + {discoveredTools.length - 5} more tool(s)
                    </Text>
                  )}
                </Stack>
              </>
            )}

            <Divider my="xs" />

            <Group justify="flex-end" gap="xs">
              <Button
                variant="subtle"
                size="sm"
                onClick={() => {
                  closeServerFormModal();
                  setEditingServerId(null);
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                loading={createMCPServerMutation.isPending || updateMCPServerMutation.isPending}
              >
                {editingServerId ? 'Update' : 'Save'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Page>
  );
}
