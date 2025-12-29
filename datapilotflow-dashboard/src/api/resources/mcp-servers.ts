import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { client } from '../axios';

export interface MCPServerConfig {
  id: string;
  user_id: string;
  name: string;
  server_url: string;
  server_type: string;
  auth_type?: string | null;
  auth_credentials?: Record<string, string> | null;
  is_active: boolean;
  timeout: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateMCPServerRequest {
  name: string;
  server_url: string;
  server_type?: string;
  auth_type?: string;
  auth_credentials?: Record<string, string>;
  timeout?: number;
  tags?: string[];
}

export interface UpdateMCPServerRequest {
  name?: string;
  server_url?: string;
  auth_type?: string;
  auth_credentials?: Record<string, string>;
  is_active?: boolean;
  timeout?: number;
  tags?: string[];
}

export interface MCPToolDiscovery {
  name: string;
  description: string;
  schema?: any;
}

// ============================================================================
// QUERY KEYS
// ============================================================================

export const mcpServersKeys = {
  all: ['mcp-servers'] as const,
  lists: () => [...mcpServersKeys.all, 'list'] as const,
  list: () => [...mcpServersKeys.lists()] as const,
  details: () => [...mcpServersKeys.all, 'detail'] as const,
  detail: (serverId: string) => [...mcpServersKeys.details(), serverId] as const,
};

// ============================================================================
// API FUNCTIONS
// ============================================================================

async function getMCPServers(isActive?: boolean): Promise<MCPServerConfig[]> {
  const params = new URLSearchParams();
  if (isActive !== undefined) {
    params.append('is_active', String(isActive));
  }

  const response = await client.get<MCPServerConfig[]>(
    `/mcp-servers?${params.toString()}`
  );
  return response.data;
}

async function getMCPServer(serverId: string): Promise<MCPServerConfig> {
  const response = await client.get<MCPServerConfig>(`/mcp-servers/${serverId}`);
  return response.data;
}

async function createMCPServer(data: CreateMCPServerRequest): Promise<MCPServerConfig> {
  const response = await client.post<MCPServerConfig>('/mcp-servers', data);
  return response.data;
}

async function updateMCPServer(
  serverId: string,
  data: UpdateMCPServerRequest
): Promise<MCPServerConfig> {
  const response = await client.put<MCPServerConfig>(
    `/mcp-servers/${serverId}`,
    data
  );
  return response.data;
}

async function deleteMCPServer(serverId: string): Promise<void> {
  await client.delete(`/mcp-servers/${serverId}`);
}

async function discoverMCPTools(serverId: string): Promise<MCPToolDiscovery[]> {
  const response = await client.post<MCPToolDiscovery[]>(
    `/mcp-servers/${serverId}/discover`
  );
  return response.data;
}

export interface DiscoverToolsRequest {
  server_url: string;
  server_type?: string;
  auth_type?: string;
  auth_credentials?: Record<string, string>;
  timeout?: number;
}

async function testMCPConnection(request: DiscoverToolsRequest): Promise<MCPToolDiscovery[]> {
  const response = await client.post<MCPToolDiscovery[]>(
    '/mcp-servers/discover',
    request
  );
  return response.data;
}

// ============================================================================
// REACT QUERY HOOKS
// ============================================================================

/**
 * Fetch all MCP servers for the current user
 */
export function useGetMCPServers(isActive?: boolean, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: mcpServersKeys.list(),
    queryFn: () => getMCPServers(isActive),
    enabled: options?.enabled !== false,
  });
}

/**
 * Fetch a single MCP server
 */
export function useGetMCPServer(serverId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: mcpServersKeys.detail(serverId),
    queryFn: () => getMCPServer(serverId),
    enabled: options?.enabled !== false && !!serverId,
  });
}

/**
 * Create a new MCP server
 */
export function useCreateMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMCPServer,
    onSuccess: () => {
      // Invalidate the MCP servers list
      queryClient.invalidateQueries({
        queryKey: mcpServersKeys.list(),
      });
    },
  });
}

/**
 * Update an existing MCP server
 */
export function useUpdateMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ serverId, data }: {
      serverId: string;
      data: UpdateMCPServerRequest;
    }) => updateMCPServer(serverId, data),
    onSuccess: (_, variables) => {
      // Invalidate both the list and the specific server
      queryClient.invalidateQueries({
        queryKey: mcpServersKeys.list(),
      });
      queryClient.invalidateQueries({
        queryKey: mcpServersKeys.detail(variables.serverId),
      });
    },
  });
}

/**
 * Delete an MCP server
 */
export function useDeleteMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ serverId }: { serverId: string }) =>
      deleteMCPServer(serverId),
    onSuccess: () => {
      // Invalidate the MCP servers list
      queryClient.invalidateQueries({
        queryKey: mcpServersKeys.list(),
      });
    },
  });
}

/**
 * Discover tools from an MCP server
 */
export function useDiscoverMCPTools() {
  return useMutation({
    mutationFn: ({ serverId }: { serverId: string }) =>
      discoverMCPTools(serverId),
  });
}

/**
 * Test MCP server connection and discover tools (without saving)
 */
export function useTestMCPConnection() {
  return useMutation({
    mutationFn: testMCPConnection,
  });
}

