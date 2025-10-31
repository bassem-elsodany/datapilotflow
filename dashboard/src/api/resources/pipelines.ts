import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook, createPutMutationHook } from '../helpers';

// ============================================================================
// PIPELINE SCHEMAS
// ============================================================================

// Node Types
export const NodeTypeSchema = z.enum([
  // Data Sources
  'website',
  'multiple_pages',
  'single_page',
  'local_files',
  // Filters & Transforms
  'domainFilter',
  'contentFilter',
  'urlPatternFilter',
  // Output Formats
  'htmlExtractor',
  'markdownGenerator',
  'llmMarkdownGenerator',
  'llmContentFilter',
  // Processing
  'textSplitter',
  // AI Tools
  'embeddingGenerator',
  // Storage/Output
  'vectorDatabase',
  'fileExport',
]);

export const NodeStatusSchema = z.enum(['pending', 'running', 'completed', 'failed']);
export const PipelineStatusSchema = z.enum(['draft', 'ready', 'running', 'completed', 'failed', 'cancelled']);

// Pipeline Node Schema
export const PipelineNodeSchema = z.object({
  id: z.string(),
  type: NodeTypeSchema,
  name: z.string(),
  position: z.object({
    x: z.number(),
    y: z.number(),
  }),
  status: NodeStatusSchema.default('pending'),
  configured: z.boolean().default(false),
  config: z.record(z.any()).default({}),
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
});

// Pipeline Edge Schema
export const PipelineEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  type: z.string().default('arrow'),
});

// Pipeline Schema
export const PipelineSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  nodes: z.array(PipelineNodeSchema).default([]),
  edges: z.array(PipelineEdgeSchema).default([]),
  status: PipelineStatusSchema.default('draft'),
  last_executed_at: z.string().nullable().optional(),
  execution_count: z.number().default(0),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string(),
  updated_by: z.string(),
});

// Pipeline Create Schema
export const PipelineCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  nodes: z.array(PipelineNodeSchema).default([]),
  edges: z.array(PipelineEdgeSchema).default([]),
});

// Pipeline Update Schema
export const PipelineUpdateSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  nodes: z.array(PipelineNodeSchema).optional(),
  edges: z.array(PipelineEdgeSchema).optional(),
  status: PipelineStatusSchema.optional(),
});

// Pipeline Execution Request Schema
export const PipelineExecutionRequestSchema = z.object({
  pipeline_id: z.string(),
  async_execution: z.boolean().default(true),
});

// Pipeline Execution Response Schema
export const PipelineExecutionResponseSchema = z.object({
  pipeline_id: z.string(),
  job_id: z.string(),
  knowledge_source_id: z.string(),
  status: z.string(),
  message: z.string(),
});

// Pipeline Execution Status Schema
export const PipelineExecutionStatusSchema = z.object({
  pipeline_id: z.string(),
  status: PipelineStatusSchema,
  current_node: z.string().nullable().optional(),
  progress: z.number().min(0).max(100).default(0),
  nodes_status: z.array(PipelineNodeSchema).default([]),
  started_at: z.string().nullable().optional(),
  estimated_completion: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
});

// Type exports
export type NodeType = z.infer<typeof NodeTypeSchema>;
export type NodeStatus = z.infer<typeof NodeStatusSchema>;
export type PipelineStatus = z.infer<typeof PipelineStatusSchema>;
export type PipelineNode = z.infer<typeof PipelineNodeSchema>;
export type PipelineEdge = z.infer<typeof PipelineEdgeSchema>;
export type Pipeline = z.infer<typeof PipelineSchema>;
export type PipelineCreate = z.infer<typeof PipelineCreateSchema>;
export type PipelineUpdate = z.infer<typeof PipelineUpdateSchema>;
export type PipelineExecutionRequest = z.infer<typeof PipelineExecutionRequestSchema>;
export type PipelineExecutionResponse = z.infer<typeof PipelineExecutionResponseSchema>;
export type PipelineExecutionStatus = z.infer<typeof PipelineExecutionStatusSchema>;

// ============================================================================
// PIPELINE API HOOKS
// ============================================================================

// List all pipelines
export const useGetPipelines = createGetQueryHook({
  endpoint: apiEndpoints.pipelines.list,
  responseSchema: z.array(PipelineSchema),
  rQueryParams: {
    queryKey: ['pipelines'],
    staleTime: 1000 * 60 * 5, // 5 minutes
  },
});

// Get specific pipeline
export const useGetPipeline = (pipelineId: string) =>
  createGetQueryHook({
    endpoint: apiEndpoints.pipelines.pipeline(pipelineId),
    responseSchema: PipelineSchema,
    rQueryParams: {
      queryKey: ['pipeline', { pipelineId }],
      enabled: !!pipelineId,
    },
  })();

// Create pipeline
export const useCreatePipeline = createPostMutationHook({
  endpoint: apiEndpoints.pipelines.create,
  bodySchema: PipelineCreateSchema,
  responseSchema: PipelineSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  },
});

// Update pipeline
export const useUpdatePipeline = createPutMutationHook({
  endpoint: apiEndpoints.pipelines.update(':pipelineId'),
  bodySchema: PipelineUpdateSchema,
  responseSchema: PipelineSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  },
});

// Delete pipeline
export const useDeletePipeline = createDeleteMutationHook({
  endpoint: apiEndpoints.pipelines.delete(':pipelineId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  },
});

// Execute pipeline
export const useExecutePipeline = createPostMutationHook({
  endpoint: apiEndpoints.pipelines.execute(':pipelineId'),
  bodySchema: z.object({}), // No body needed, pipelineId is in path
  responseSchema: PipelineExecutionResponseSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
    },
  },
});

// Get pipeline execution status
export const useGetPipelineStatus = (pipelineId: string, options?: { enabled?: boolean; refetchInterval?: number }) =>
  createGetQueryHook({
    endpoint: apiEndpoints.pipelines.status(pipelineId),
    responseSchema: PipelineExecutionStatusSchema,
    rQueryParams: {
      queryKey: ['pipeline-status', { pipelineId }],
      enabled: options?.enabled !== false && !!pipelineId,
      refetchInterval: options?.refetchInterval || 5000, // Default: poll every 5 seconds
      staleTime: 0, // Always fetch fresh data
    },
  })();

// Get job as pipeline (for job-to-pipeline visualization conversion)
export const useGetJobAsPipeline = (jobId: string, options?: { enabled?: boolean }) =>
  createGetQueryHook({
    endpoint: `/knowledge/jobs/${jobId}/pipeline`,
    responseSchema: PipelineSchema,
    rQueryParams: {
      queryKey: ['job-pipeline', { jobId }],
      enabled: options?.enabled !== false && !!jobId,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  })();
