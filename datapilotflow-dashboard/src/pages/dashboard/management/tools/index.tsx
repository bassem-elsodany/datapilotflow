import { MCPServerConfig, MCPToolDiscovery, useCreateMCPServer, useDeleteMCPServer, useDiscoverMCPTools, useGetMCPServers, useTestMCPConnection, useUpdateMCPServer } from '@/api/resources/mcp-servers';
import { Tool, useCreateTool, useDeleteTool, useGetTools, useUpdateTool } from '@/api/resources/tools';
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
  Checkbox,
  Divider,
  Group,
  Loader,
  Modal,
  NumberInput,
  PasswordInput,
  Select,
  Stack,
  Table,
  Tabs,
  TagsInput,
  Text,
  TextInput,
  ThemeIcon,
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
  IconTrash,
  IconZoomScan
} from '@tabler/icons-react';
import sortBy from 'lodash/sortBy';
import { DataTableTable as DataTable } from '@/components/data-table/data-table-table';
import { DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '@/hooks/use-permissions';

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
  const { hasPermission, isAdmin } = usePermissions();
  const canManage = isAdmin() || hasPermission('tools:manage');

  // MCP Servers state
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
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
  const [selectedToolIds, setSelectedToolIds] = useState<Set<string>>(new Set());

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
  const createToolMutation = useCreateTool();

  // State for testing connection
  const [discoveredTools, setDiscoveredTools] = useState<MCPToolDiscovery[]>([]);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  // Rediscover state
  const [rediscoverModalOpened, { open: openRediscoverModal, close: closeRediscoverModal }] = useDisclosure(false);
  const [rediscoverServerId, setRediscoverServerId] = useState<string | null>(null);
  const [rediscoverResults, setRediscoverResults] = useState<MCPToolDiscovery[]>([]);
  const [rediscoverRemovedTools, setRediscoverRemovedTools] = useState<Tool[]>([]);
  const [isRediscovering, setIsRediscovering] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedNewTools, setSelectedNewTools] = useState<Set<string>>(new Set());

  const closeRediscover = () => {
    closeRediscoverModal();
    setRediscoverResults([]);
    setRediscoverRemovedTools([]);
    setSelectedNewTools(new Set());
    setRediscoverServerId(null);
  };

  const handleRediscover = async (server: MCPServerConfig) => {
    setRediscoverServerId(server.id);
    setRediscoverResults([]);
    setRediscoverRemovedTools([]);
    setSelectedNewTools(new Set());
    setIsRediscovering(true);
    openRediscoverModal();
    try {
      const result = await discoverMCPMutation.mutateAsync({ serverId: server.id });
      const serverTools = tools.filter(t => t.tool_type === 'mcp_remote' && t.mcp_server_id === server.id);
      const returnedNames = new Set(result.map((t: MCPToolDiscovery) => t.name));

      // Tools that no longer exist on the server
      const removed = serverTools.filter(t => !returnedNames.has(t.mcp_tool_name || t.name));
      // Tools that are new (not yet in DB)
      const existingNames = new Set(serverTools.map(t => t.mcp_tool_name || t.name));
      const newOnes = result.filter((t: MCPToolDiscovery) => !existingNames.has(t.name));

      setRediscoverResults(result);
      setRediscoverRemovedTools(removed);
      setSelectedNewTools(new Set(newOnes.map((t: MCPToolDiscovery) => t.name)));
    } catch (error: any) {
      notifications.show({
        title: 'Rediscover Failed',
        message: error.response?.data?.detail || 'Failed to discover tools from server',
        color: 'red',
      });
      closeRediscover();
    } finally {
      setIsRediscovering(false);
    }
  };

  const handleSyncTools = async () => {
    if (!rediscoverServerId) return;
    setIsSyncing(true);
    try {
      const toAdd = rediscoverResults.filter(t => selectedNewTools.has(t.name));

      await Promise.all([
        // Add new tools
        ...toAdd.map(tool =>
          createToolMutation.mutateAsync({
            name: tool.name,
            display_name: tool.name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            description: tool.description || '',
            tool_type: 'mcp_remote',
            is_active: true,
            tags: ['mcp', 'auto-discovered'],
            mcp_server_id: rediscoverServerId,
            mcp_tool_name: tool.name,
          } as any)
        ),
        // Delete removed tools
        ...rediscoverRemovedTools.map(tool =>
          deleteToolMutation.mutateAsync({ toolId: tool.id })
        ),
      ]);

      const addedCount = toAdd.length;
      const deletedCount = rediscoverRemovedTools.length;
      notifications.show({
        title: 'Sync Complete',
        message: [
          addedCount > 0 && `Added ${addedCount} new tool(s)`,
          deletedCount > 0 && `Removed ${deletedCount} stale tool(s)`,
        ].filter(Boolean).join('. ') || 'Already up to date',
        color: 'green',
      });
      closeRediscover();
      refetchTools();
    } catch (error: any) {
      notifications.show({
        title: 'Sync Failed',
        message: error.response?.data?.detail || 'Failed to sync tools',
        color: 'red',
      });
    } finally {
      setIsSyncing(false);
    }
  };

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

  // Clear selections when filters change
  useEffect(() => {
    setSelectedToolIds(new Set());
  }, [selectedServerId, searchQuery, filterActive]);

  // Ensure a valid selected tab whenever server list changes
  useEffect(() => {
    if (!mcpServers.length) {
      setSelectedServerId(null);
      return;
    }

    if (!selectedServerId || !mcpServers.some((server) => server.id === selectedServerId)) {
      setSelectedServerId(mcpServers[0].id);
    }
  }, [mcpServers, selectedServerId]);

  const selectedServerConfig = useMemo(
    () => mcpServers.find((server) => server.id === selectedServerId) || null,
    [mcpServers, selectedServerId]
  );

  // Filter and sort tools
  const getFilteredToolsForServer = (serverId: string) => {
    let filtered = tools.filter(
      (tool) => tool.tool_type === 'mcp_remote' && tool.mcp_server_id === serverId
    );

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
  };

  const filteredTools = useMemo(() => {
    if (!selectedServerId) return [];
    return getFilteredToolsForServer(selectedServerId);
  }, [tools, selectedServerId, searchQuery, filterActive, sortStatus]);

  const handleDeleteTool = async () => {
    if (!selectedTool && selectedToolIds.size === 0) return;

    try {
      // Bulk delete
      if (selectedToolIds.size > 0) {
        const deletePromises = Array.from(selectedToolIds).map(toolId =>
          deleteToolMutation.mutateAsync({ toolId })
        );
        await Promise.all(deletePromises);

        notifications.show({
          title: 'Success',
          message: `${selectedToolIds.size} tool(s) deleted successfully`,
          color: 'green',
        });

        setSelectedToolIds(new Set());
      }
      // Single delete
      else if (selectedTool) {
        await deleteToolMutation.mutateAsync({
          toolId: selectedTool.id,
        });

        notifications.show({
          title: 'Success',
          message: 'Tool deleted successfully',
          color: 'green',
        });

        setSelectedTool(null);
      }

      closeDeleteModal();
      refetchTools();
    } catch (error: any) {
      console.error('Failed to delete tool(s):', error);

      // Handle 409 Conflict - tool is bound to conversations (referential integrity)
      if (error.response?.status === 409) {
        notifications.show({
          title: 'Cannot Delete Tool',
          message: error.response?.data?.detail || 'This tool is bound to one or more conversation agents. Please unbind it first.',
          color: 'orange',
          autoClose: 10000, // Show longer for users to read the conversation names
        });
      } else {
        notifications.show({
          title: 'Error',
          message: error.response?.data?.detail || 'Failed to delete tool(s)',
          color: 'red',
        });
      }
    }
  };

  const handleToggleToolSelection = (toolId: string) => {
    const newSelected = new Set(selectedToolIds);
    if (newSelected.has(toolId)) {
      newSelected.delete(toolId);
    } else {
      newSelected.add(toolId);
    }
    setSelectedToolIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedToolIds.size === filteredTools.length) {
      setSelectedToolIds(new Set());
    } else {
      setSelectedToolIds(new Set(filteredTools.map(tool => tool.id)));
    }
  };

  const handleBulkDelete = () => {
    if (selectedToolIds.size === 0) return;
    openDeleteModal();
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
      const errorDetail = error.response?.data?.detail || 'Failed to connect to MCP server';
      notifications.show({
        title: 'Connection Failed',
        message: errorDetail,
        color: 'red',
        autoClose: 10000, // Keep visible for 10 seconds so user can read the error
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

  const columns: DataTableColumn<Tool>[] = [
    {
      accessor: 'checkbox',
      title: (
        <Checkbox
          checked={selectedToolIds.size === filteredTools.length && filteredTools.length > 0}
          indeterminate={selectedToolIds.size > 0 && selectedToolIds.size < filteredTools.length}
          onChange={handleSelectAll}
        />
      ),
      render: (tool) => (
        <Checkbox
          checked={selectedToolIds.has(tool.id)}
          onChange={() => handleToggleToolSelection(tool.id)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
      width: 40,
    },
    {
      accessor: 'name',
      title: 'Tool',
      sortable: true,
      render: (tool) => (
        <Group gap="sm" wrap="nowrap">
          <ThemeIcon
            size="md"
            variant="light"
            color={tool.tool_type === 'prompt_based' ? 'violet' : 'blue'}
            radius="sm"
          >
            {getToolIcon(tool.tool_type)}
          </ThemeIcon>
          <div style={{ minWidth: 0 }}>
            <Text size="sm" fw={600} truncate>{tool.display_name}</Text>
            <Text size="xs" c="dimmed" truncate>{tool.name}</Text>
          </div>
        </Group>
      ),
    },
    {
      accessor: 'description',
      title: 'Description',
      render: (tool) => (
        <Tooltip label={tool.description} multiline maw={360} withArrow disabled={!tool.description || tool.description.length < 60}>
          <Text size="sm" c="dimmed" lineClamp={1}>{tool.description || '—'}</Text>
        </Tooltip>
      ),
    },
    {
      accessor: 'tool_type',
      title: 'Type',
      sortable: true,
      width: 140,
      render: (tool) => getToolTypeBadge(tool.tool_type),
    },
    {
      accessor: 'is_active',
      title: 'Status',
      sortable: true,
      width: 110,
      render: (tool) => (
        <Tooltip label="Click to toggle" withArrow>
          <Badge
            size="sm"
            variant="dot"
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
      width: 140,
      render: (tool) => {
        if (!tool.tags || tool.tags.length === 0) return <Text size="xs" c="dimmed">—</Text>;
        return (
          <Tooltip
            label={tool.tags.join(', ')}
            withArrow
            disabled={tool.tags.length <= 2}
          >
            <Group gap={4} wrap="nowrap">
              {tool.tags.slice(0, 2).map((tag, idx) => (
                <Badge key={idx} size="xs" variant="light" radius="sm">{tag}</Badge>
              ))}
              {tool.tags.length > 2 && (
                <Badge size="xs" variant="light" color="gray" radius="sm">+{tool.tags.length - 2}</Badge>
              )}
            </Group>
          </Tooltip>
        );
      },
    },
    {
      accessor: 'actions',
      title: '',
      width: 72,
      textAlign: 'right',
      render: (tool) => (
        <Group gap={4} justify="flex-end" wrap="nowrap">
          {canManage && (
            <Tooltip label="Edit" withArrow>
              <ActionIcon
                variant="subtle"
                color="blue"
                size="sm"
                onClick={() => navigate(paths.dashboard.management.tools.edit(tool.id))}
              >
                <IconEdit size={14} />
              </ActionIcon>
            </Tooltip>
          )}
          {canManage && (
            <Tooltip label="Delete" withArrow>
              <ActionIcon
                variant="subtle"
                color="red"
                size="sm"
                onClick={() => {
                  setSelectedTool(tool);
                  openDeleteModal();
                }}
              >
                <IconTrash size={14} />
              </ActionIcon>
            </Tooltip>
          )}
        </Group>
      ),
    },
  ];

  // Derived stats
  const totalTools = tools.length;
  const activeTools = tools.filter(t => t.is_active).length;
  const mcpTools = tools.filter(t => t.tool_type === 'mcp_remote').length;
  const promptTools = tools.filter(t => t.tool_type === 'prompt_based').length;

  return (
    <Page title="Tools Management">
      <PageHeader
        title="Tools Management"
        breadcrumbs={breadcrumbs}
      />

      <Stack gap="md">
        {/* Stat pills */}


        {/* MCP Servers Tabs + Selected Server Details */}
        <Card>
          <Stack gap="md">
            <Group justify="space-between">
              <div>
                <Title order={5}>MCP Servers</Title>
                <Text size="sm" c="dimmed">
                  Select a server tab to view and manage its tools
                </Text>
              </div>
              <Group gap="xs" ml="auto">
                <ActionIcon variant="subtle" size="sm" onClick={() => refetchServers()} loading={serversLoading}>
                  <IconRefresh size={14} />
                </ActionIcon>
                {canManage && (
                  <Button
                    leftSection={<IconPlus size={14} />}
                    size="xs"
                    variant="default"
                    onClick={() => {
                      setEditingServerId(null);
                      openServerFormModal();
                    }}
                  >
                    Add MCP Server
                  </Button>
                )}
                {canManage && (
                  <Button
                    leftSection={<IconPlus size={14} />}
                    size="xs"
                    variant="default"
                    onClick={() => navigate(paths.dashboard.management.tools.create)}
                  >
                    Create MCP Tool
                  </Button>
                )}
              </Group>
            </Group>

            {serversLoading ? (
              <Center py="xl">
                <Loader />
              </Center>
            ) : mcpServers.length === 0 ? (
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
              <Tabs
                value={selectedServerId || undefined}
                onChange={(value) => setSelectedServerId(value)}
              >
                <Tabs.List>
                  {mcpServers.map((server) => {
                    const serverTools = tools.filter(
                      (tool) => tool.tool_type === 'mcp_remote' && tool.mcp_server_id === server.id
                    ).length;
                    const isSelected = selectedServerId === server.id;
                    return (
                      <Tabs.Tab
                        key={server.id}
                        value={server.id}
                        leftSection={<IconServer size={14} />}
                      >
                        <Group gap={6} wrap="nowrap">
                          <Text size="sm" fw={500}>{server.name}</Text>
                          <Badge size="xs" variant="light" color={serverTools > 0 ? 'teal' : 'gray'}>
                            {serverTools}
                          </Badge>
                          {isSelected && (
                            <>
                              <Tooltip label="Edit server" withArrow>
                                <ActionIcon
                                  variant="subtle"
                                  size="xs"
                                  color="blue"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditingServerId(server.id);
                                    openServerFormModal();
                                  }}
                                >
                                  <IconEdit size={12} />
                                </ActionIcon>
                              </Tooltip>
                              <Tooltip label="Rediscover tools" withArrow>
                                <ActionIcon
                                  variant="subtle"
                                  size="xs"
                                  color="teal"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleRediscover(server);
                                  }}
                                >
                                  <IconZoomScan size={12} />
                                </ActionIcon>
                              </Tooltip>
                              <Tooltip label="Delete server" withArrow>
                                <ActionIcon
                                  variant="subtle"
                                  size="xs"
                                  color="red"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedServer(server);
                                    openDeleteServerModal();
                                  }}
                                >
                                  <IconTrash size={12} />
                                </ActionIcon>
                              </Tooltip>
                            </>
                          )}
                        </Group>
                      </Tabs.Tab>
                    );
                  })}
                </Tabs.List>

                {mcpServers.map((server) => {
                  const panelTools = getFilteredToolsForServer(server.id);
                  return (
                    <Tabs.Panel key={server.id} value={server.id} pt="md">
                      <Stack gap="md">
                        {toolsLoading ? (
                          <Center py="xl">
                            <Loader />
                          </Center>
                        ) : panelTools.length === 0 ? (
                          <Center py="xl">
                            <Stack align="center" gap="md">
                              <IconTool size={48} stroke={1.5} color="gray" />
                              <div>
                                <Text size="lg" fw={500} ta="center">
                                  No tools under this server
                                </Text>
                                <Text size="sm" c="dimmed" ta="center">
                                  Create a tool for this MCP server.
                                </Text>
                              </div>
                            </Stack>
                          </Center>
                        ) : (
                          <DataTable
                            columns={columns}
                            records={panelTools}
                            sortStatus={sortStatus}
                            onSortStatusChange={setSortStatus}
                            highlightOnHover
                            striped
                          />
                        )}
                      </Stack>
                    </Tabs.Panel>
                  );
                })}
              </Tabs>
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
        title={selectedToolIds.size > 0 ? "Delete Multiple Tools" : "Delete Tool"}
      >
        <Stack gap="md">
          {selectedToolIds.size > 0 ? (
            <Text>
              Are you sure you want to delete <strong>{selectedToolIds.size} tool(s)</strong>?
              This action cannot be undone.
            </Text>
          ) : selectedTool ? (
            <Text>
              Are you sure you want to delete <strong>{selectedTool.display_name}</strong>?
              This action cannot be undone.
            </Text>
          ) : null}

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
              {selectedToolIds.size > 0 ? `Delete ${selectedToolIds.size} Tool(s)` : 'Delete Tool'}
            </Button>
          </Group>
        </Stack>
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

      {/* Rediscover Tools Modal */}
      <Modal
        opened={rediscoverModalOpened}
        onClose={closeRediscover}
        title={
          <Group gap="xs">
            <IconZoomScan size={18} />
            <Text size="sm" fw={600}>Sync Tools — {mcpServers.find(s => s.id === rediscoverServerId)?.name}</Text>
          </Group>
        }
        size="lg"
      >
        <Stack gap="md">
          {isRediscovering ? (
            <Center py="xl">
              <Stack align="center" gap="sm">
                <Loader />
                <Text size="sm" c="dimmed">Connecting to MCP server...</Text>
              </Stack>
            </Center>
          ) : (
            <>
              {/* Summary alert */}
              {rediscoverResults.length === 0 && !isRediscovering ? (
                <Alert color="yellow" icon={<IconAlertCircle size={16} />}>
                  No tools returned by the server. All existing tools will be removed on sync.
                </Alert>
              ) : (
                <Alert color="blue" icon={<IconInfoCircle size={16} />} p="xs">
                  <Text size="xs">
                    Server returned <strong>{rediscoverResults.length}</strong> tool(s).
                    {selectedNewTools.size > 0 && <> <strong>{selectedNewTools.size}</strong> new to add.</>}
                    {rediscoverRemovedTools.length > 0 && <> <strong style={{ color: 'var(--mantine-color-red-6)' }}>{rediscoverRemovedTools.length}</strong> stale to remove.</>}
                  </Text>
                </Alert>
              )}

              {/* Stale tools to be deleted */}
              {rediscoverRemovedTools.length > 0 && (
                <>
                  <Text size="xs" fw={600} c="red">Stale Tools — will be deleted</Text>
                  <Table withTableBorder>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Tool Name</Table.Th>
                        <Table.Th>Description</Table.Th>
                        <Table.Th w={90}>Action</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {rediscoverRemovedTools.map(tool => (
                        <Table.Tr key={tool.id} style={{ background: 'var(--mantine-color-red-0)' }}>
                          <Table.Td><Text size="sm" fw={500} c="red">{tool.display_name}</Text></Table.Td>
                          <Table.Td><Text size="xs" c="dimmed" lineClamp={1}>{tool.description || '—'}</Text></Table.Td>
                          <Table.Td><Badge size="xs" color="red" variant="light">Remove</Badge></Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </>
              )}

              {/* New + existing tools returned by server */}
              {rediscoverResults.length > 0 && (
                <>
                  <Text size="xs" fw={600} c="dimmed">Tools returned by server</Text>
                  <Table highlightOnHover withTableBorder>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th w={40}>
                          <Checkbox
                            checked={selectedNewTools.size > 0 && selectedNewTools.size === rediscoverResults.filter(t => {
                              const existing = tools.filter(ex => ex.tool_type === 'mcp_remote' && ex.mcp_server_id === rediscoverServerId);
                              return !existing.some(ex => (ex.mcp_tool_name || ex.name) === t.name);
                            }).length}
                            indeterminate={selectedNewTools.size > 0 && selectedNewTools.size < rediscoverResults.filter(t => {
                              const existing = tools.filter(ex => ex.tool_type === 'mcp_remote' && ex.mcp_server_id === rediscoverServerId);
                              return !existing.some(ex => (ex.mcp_tool_name || ex.name) === t.name);
                            }).length}
                            onChange={(e) => {
                              const newable = rediscoverResults
                                .filter(t => !tools.filter(ex => ex.tool_type === 'mcp_remote' && ex.mcp_server_id === rediscoverServerId).some(ex => (ex.mcp_tool_name || ex.name) === t.name))
                                .map(t => t.name);
                              setSelectedNewTools(e.currentTarget.checked ? new Set(newable) : new Set());
                            }}
                          />
                        </Table.Th>
                        <Table.Th>Tool Name</Table.Th>
                        <Table.Th>Description</Table.Th>
                        <Table.Th w={90}>Status</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {rediscoverResults.map((tool) => {
                        const alreadyAdded = tools
                          .filter(ex => ex.tool_type === 'mcp_remote' && ex.mcp_server_id === rediscoverServerId)
                          .some(ex => (ex.mcp_tool_name || ex.name) === tool.name);
                        return (
                          <Table.Tr key={tool.name} style={{ opacity: alreadyAdded ? 0.55 : 1 }}>
                            <Table.Td>
                              <Checkbox
                                checked={selectedNewTools.has(tool.name)}
                                disabled={alreadyAdded}
                                onChange={() => {
                                  const next = new Set(selectedNewTools);
                                  next.has(tool.name) ? next.delete(tool.name) : next.add(tool.name);
                                  setSelectedNewTools(next);
                                }}
                              />
                            </Table.Td>
                            <Table.Td><Text size="sm" fw={500}>{tool.name}</Text></Table.Td>
                            <Table.Td><Text size="xs" c="dimmed" lineClamp={2}>{tool.description || '—'}</Text></Table.Td>
                            <Table.Td>
                              {alreadyAdded
                                ? <Badge size="xs" color="gray" variant="light">Exists</Badge>
                                : <Badge size="xs" color="teal" variant="light">New</Badge>
                              }
                            </Table.Td>
                          </Table.Tr>
                        );
                      })}
                    </Table.Tbody>
                  </Table>
                </>
              )}

              <Group justify="flex-end" gap="xs">
                <Button variant="subtle" size="sm" onClick={closeRediscover}>Cancel</Button>
                <Button
                  size="sm"
                  leftSection={<IconRefresh size={14} />}
                  color={rediscoverRemovedTools.length > 0 ? 'orange' : 'teal'}
                  disabled={selectedNewTools.size === 0 && rediscoverRemovedTools.length === 0}
                  loading={isSyncing}
                  onClick={handleSyncTools}
                >
                  Sync ({selectedNewTools.size > 0 ? `+${selectedNewTools.size}` : ''}{selectedNewTools.size > 0 && rediscoverRemovedTools.length > 0 ? ' ' : ''}{rediscoverRemovedTools.length > 0 ? `−${rediscoverRemovedTools.length}` : ''})
                </Button>
              </Group>
            </>
          )}
        </Stack>
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
