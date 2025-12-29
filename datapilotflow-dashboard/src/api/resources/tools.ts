/**
 * API resource hooks for conversation tools management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { client } from '../axios';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export type ToolType = 'prompt_based' | 'mcp_remote';

export interface PromptBasedToolConfig {
  system_prompt: string;
  llm_provider_id?: string | null;
  llm_model_name?: string | null;
  temperature?: number;
  instructions?: string | null;
}

export interface Tool {
  id: string;
  name: string;
  display_name: string;
  description: string;
  tool_type: ToolType;
  is_active: boolean;
  prompt_config?: PromptBasedToolConfig | null;
  mcp_server_id?: string | null;
  mcp_tool_name?: string | null;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CreateToolRequest {
  name: string;
  display_name: string;
  description: string;
  tool_type: ToolType;
  is_active?: boolean;
  prompt_config?: PromptBasedToolConfig | null;
  mcp_server_id?: string | null;
  mcp_tool_name?: string | null;
  tags?: string[];
}

export interface UpdateToolRequest {
  name?: string;
  display_name?: string;
  description?: string;
  is_active?: boolean;
  prompt_config?: PromptBasedToolConfig | null;
  mcp_server_id?: string | null;
  mcp_tool_name?: string | null;
  tags?: string[];
}

// ============================================================================
// QUERY KEYS
// ============================================================================

export const toolsKeys = {
  all: ['tools'] as const,
  lists: () => [...toolsKeys.all, 'list'] as const,
  list: () => [...toolsKeys.lists()] as const,
  details: () => [...toolsKeys.all, 'detail'] as const,
  detail: (toolId: string) => [...toolsKeys.details(), toolId] as const,
};

// ============================================================================
// API FUNCTIONS
// ============================================================================

async function getTools(): Promise<Tool[]> {
  const response = await client.get<Tool[]>(`/tools`);
  return response.data;
}

async function getTool(toolId: string): Promise<Tool> {
  const response = await client.get<Tool>(`/tools/${toolId}`);
  return response.data;
}

async function createTool(data: CreateToolRequest): Promise<Tool> {
  const response = await client.post<Tool>('/tools', data);
  return response.data;
}

async function updateTool(
  toolId: string,
  data: UpdateToolRequest
): Promise<Tool> {
  const response = await client.put<Tool>(`/tools/${toolId}`, data);
  return response.data;
}

async function deleteTool(toolId: string): Promise<void> {
  await client.delete(`/tools/${toolId}`);
}

// ============================================================================
// REACT QUERY HOOKS
// ============================================================================

/**
 * Fetch all tools for the current user
 */
export function useGetTools(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: toolsKeys.list(),
    queryFn: () => getTools(),
    enabled: options?.enabled !== false,
  });
}

/**
 * Fetch a single tool
 */
export function useGetTool(toolId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: toolsKeys.detail(toolId),
    queryFn: () => getTool(toolId),
    enabled: options?.enabled !== false && !!toolId,
  });
}

/**
 * Create a new tool
 */
export function useCreateTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTool,
    onSuccess: () => {
      // Invalidate the tools list
      queryClient.invalidateQueries({
        queryKey: toolsKeys.list(),
      });
    },
  });
}

/**
 * Update an existing tool
 */
export function useUpdateTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ toolId, data }: {
      toolId: string;
      data: UpdateToolRequest;
    }) => updateTool(toolId, data),
    onSuccess: (_, variables) => {
      // Invalidate both the list and the specific tool
      queryClient.invalidateQueries({
        queryKey: toolsKeys.list(),
      });
      queryClient.invalidateQueries({
        queryKey: toolsKeys.detail(variables.toolId),
      });
    },
  });
}

/**
 * Delete a tool
 */
export function useDeleteTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ toolId }: { toolId: string }) =>
      deleteTool(toolId),
    onSuccess: () => {
      // Invalidate the tools list
      queryClient.invalidateQueries({
        queryKey: toolsKeys.list(),
      });
    },
  });
}

