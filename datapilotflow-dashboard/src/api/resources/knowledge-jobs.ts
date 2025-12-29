import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook, createPutMutationHook } from '../helpers';

// ============================================================================
// KNOWLEDGE JOB SCHEMAS
// ============================================================================

// Splitter Type Enum
export const SplitterTypeSchema = z.enum(['text', 'document']);

// Knowledge Job Schema
export const KnowledgeJobSchema = z.object({
  id: z.string(),
  knowledge_source_config_id: z.string(),
  vectordb_collection_id: z.string(),
  splitter_id: z.string().optional(), // Reference to document splitter configuration
  user_id: z.string(),
  name: z.string(),
  description: z.string().optional(),

  // Document splitting configuration (deprecated fields, use splitter_id + document_splitter instead)
  splitter_type: SplitterTypeSchema.optional(),
  chunk_size: z.number().nullable().optional(),
  chunk_overlap: z.number().nullable().optional(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),

  // Job processing configuration
  batch_size: z.number(),
  save_to_file: z.boolean(),
  write_consolidated_file: z.boolean(),

  // Collection management
  clear_collection_before_start: z.boolean(),
  check_duplicates_before_insert: z.boolean(),

  // Metadata
  created_at: z.string(),
  created_by: z.string(),

  // Optional expanded fields (populated when using expand parameter)
  knowledge_source_config: z.any().optional(),
  vectordb_collection: z.any().optional(),
  document_splitter: z.any().optional(),
  timeline: z.array(z.any()).nullable().optional(),
  execution_stats: z.any().optional(),
});

export type KnowledgeJob = z.infer<typeof KnowledgeJobSchema>;
export type SplitterType = z.infer<typeof SplitterTypeSchema>;

// Knowledge Job Create Schema
export const KnowledgeJobCreateSchema = z.object({
  name: z.string(),
  description: z.string().optional(),

  // Vector DB Collection Configuration (embedded in job creation)
  vectordb_collection_description: z.string().optional(),
  embedding_model_provider_id: z.string().optional(),
  embedding_model_name: z.string().optional(),
  vector_dimension: z.number().min(1).max(4096).optional(),
  collection_name: z.string().optional(),

  // Document splitter configuration reference (use existing splitter)
  splitter_id: z.string().optional(),

  // Inline splitter creation (alternative to splitter_id)
  splitter_name: z.string().optional(),
  splitter_description: z.string().optional(),
  splitter_type: SplitterTypeSchema.optional(),

  // Optional overrides for splitter configuration (for text splitters)
  custom_chunk_size: z.number().min(64).nullable().optional(),
  custom_chunk_overlap: z.number().min(0).nullable().optional(),

  // Legacy document splitting configuration (deprecated, kept for backward compatibility)
  chunk_size: z.number().min(64).default(256).nullable(),
  chunk_overlap: z.number().min(0).default(32).nullable(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),

  // Existing collection option
  existing_collection_id: z.string().optional(),

  // Job processing configuration
  batch_size: z.number().min(1).max(1000).default(100),
  save_to_file: z.boolean().default(false),
  write_consolidated_file: z.boolean().default(false),

  // Collection management
  clear_collection_before_start: z.boolean().default(false),
  check_duplicates_before_insert: z.boolean().default(false),
});

export type KnowledgeJobCreate = z.infer<typeof KnowledgeJobCreateSchema>;

// Knowledge Job Update Schema
export const KnowledgeJobUpdateSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),

  // Vector DB Collection Configuration (can be updated)
  vectordb_collection_description: z.string().optional(),
  embedding_model_provider_id: z.string().optional(),
  embedding_model_name: z.string().optional(),
  vector_dimension: z.number().min(1).max(4096).optional(),
  collection_name: z.string().optional(),

  // Document splitting configuration
  splitter_type: SplitterTypeSchema.optional(),
  chunk_size: z.number().min(64).nullable().optional(),
  chunk_overlap: z.number().min(0).nullable().optional(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),

  // Job processing configuration
  batch_size: z.number().min(1).max(1000).optional(),
  save_to_file: z.boolean().optional(),
  write_consolidated_file: z.boolean().optional(),

  // Collection management
  clear_collection_before_start: z.boolean().optional(),
  check_duplicates_before_insert: z.boolean().optional(),
});

export type KnowledgeJobUpdate = z.infer<typeof KnowledgeJobUpdateSchema>;

// ============================================================================
// KNOWLEDGE JOB API HOOKS
// ============================================================================

// List all knowledge jobs
export const useGetKnowledgeJobs = createGetQueryHook({
  endpoint: apiEndpoints.knowledgeJobs.list,
  responseSchema: z.array(KnowledgeJobSchema),
  rQueryParams: {
    queryKey: ['knowledge-jobs'],
    staleTime: 0, // NO CACHING - Always treat data as stale
    gcTime: 0, // NO CACHE TIME - Clear cache immediately
    refetchOnMount: 'always', // Always refetch on mount
    refetchOnWindowFocus: true, // Refetch when window regains focus
    refetchOnReconnect: true, // Refetch when network reconnects
  },
});

// Create knowledge job
export const useCreateKnowledgeJob = createPostMutationHook({
  endpoint: apiEndpoints.knowledgeJobs.create(':configId'),
  bodySchema: KnowledgeJobCreateSchema,
  responseSchema: KnowledgeJobSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-vectordb-collection'] });
    },
  },
});

// Get specific knowledge job
export const useGetKnowledgeJob = (jobId: string | undefined, options?: { enabled?: boolean; query?: { expand?: string } }) => {
  // Only create the endpoint if we have a valid jobId
  // Otherwise, React Query might still try to fetch even with enabled: false
  const shouldFetch = options?.enabled !== false && !!jobId;
  const safeJobId = jobId || 'invalid-placeholder-do-not-fetch';

  const hook = createGetQueryHook<typeof KnowledgeJobSchema, {}, { expand?: string }>({
    endpoint: apiEndpoints.knowledgeJobs.job(safeJobId),
    responseSchema: KnowledgeJobSchema,
    rQueryParams: {
      queryKey: ['knowledge-job', { jobId: safeJobId, expand: options?.query?.expand }],
      retry: false, // Never retry failed placeholder requests
      refetchOnMount: false, // Never refetch on mount
      refetchOnWindowFocus: false, // Never refetch on window focus
      refetchOnReconnect: false, // Never refetch on reconnect
      staleTime: Infinity, // Never consider data stale
    },
  });

  // IMPORTANT: Pass the enabled flag through to the hook call
  // helpers.ts line 192 uses params?.enabled, NOT rQueryParams.enabled!
  return hook({
    query: options?.query,
    enabled: shouldFetch, // This is what actually controls the query execution
  });
};

// Update knowledge job
export const useUpdateKnowledgeJob = createPutMutationHook({
  endpoint: apiEndpoints.knowledgeJobs.update(':jobId'),
  bodySchema: KnowledgeJobUpdateSchema,
  responseSchema: KnowledgeJobSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-job'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-vectordb-collection'] });
    },
  },
});

// Delete knowledge job
export const useDeleteKnowledgeJob = createDeleteMutationHook({
  endpoint: apiEndpoints.knowledgeJobs.delete(':jobId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
    },
  },
});

// Execute knowledge job
export const useExecuteKnowledgeJob = createPostMutationHook({
  endpoint: apiEndpoints.knowledgeJobs.execute(':jobId'),
  bodySchema: z.object({}), // Empty body for execute endpoint
  responseSchema: z.object({
    message: z.string(),
    job_id: z.string(),
    status: z.string(),
    event_id: z.string().optional(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-job'] });
    },
  },
});

export const useCancelKnowledgeJob = createPostMutationHook({
  endpoint: apiEndpoints.knowledgeJobs.cancel(':jobId'),
  bodySchema: z.object({}), // Empty body for cancel endpoint
  responseSchema: z.object({
    message: z.string(),
    job_id: z.string(),
    status: z.string(),
    timeline_id: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-job'] });
    },
  },
});
