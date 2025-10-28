import { apiEndpoints } from '@/config';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook } from '../helpers';

// ============================================================================
// KNOWLEDGE SOURCE CONFIGURATION SCHEMAS
// ============================================================================

// URL Source Configuration Schema (separate collection)
// Note: One-way relationship only (config.url_source_id → url_source.id)
export const UrlSourceConfigSchema = z.object({
  id: z.string(),
  file_name: z.string(),
  urls: z.array(z.string()).max(50000, 'Too many URLs (max 50,000)'), // 50,000 URL limit
  created_at: z.string(),
  updated_at: z.string(),
});

// URL Source Configuration Create Schema
export const UrlSourceConfigCreateSchema = z.object({
  file_name: z.string(),
  urls: z.array(z.string()).max(50000, 'Too many URLs (max 50,000)'),
});

// Content Source Type Schema
export const ContentSourceTypeSchema = z.enum(['web_scraping', 'local_files']);

// Scraping Mode Schema (updated with local files modes)
export const ScrapingModeSchema = z.enum([
  'single_page',
  'multiple_pages',
  'website',
  'html_files',
  'markdown_files',
  'pdf_files',
  'docx_files',
  'txt_files'
]);

// Local File Schema
export const LocalFileSchema = z.object({
  file_id: z.string(),
  original_filename: z.string(),
  file_path: z.string(),
  file_type: z.string(),
  file_size: z.number(),
  upload_timestamp: z.string(),
});

// Knowledge Source Configuration Schema
export const KnowledgeSourceConfigSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional().default(""),
  content_source_type: ContentSourceTypeSchema,
  url: z.string().nullable().optional(),
  scraping_mode: ScrapingModeSchema.nullable().optional(),
  url_source_id: z.string().nullable().optional(),
  allowed_subdomains: z.array(z.string()).nullable().optional(),
  blocked_subdomains: z.array(z.string()).nullable().optional(),
  url_patterns: z.array(z.record(z.any())).nullable().optional(),
  crawl_depth: z.number().nullable().optional(),
  target_elements: z.array(z.string()),
  content_filter_threshold: z.number(),
  output_format: z.enum(['html', 'markdown', 'llm_markdown']),
  llm_content_filter_id: z.string().nullable().optional(),
  local_files: z.array(LocalFileSchema).nullable().optional(),
  file_types: z.array(z.string()).nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string(),
  updated_by: z.string(),
});

export type ContentSourceType = z.infer<typeof ContentSourceTypeSchema>;
export type ScrapingMode = z.infer<typeof ScrapingModeSchema>;
export type LocalFile = z.infer<typeof LocalFileSchema>;
export type UrlSourceConfig = z.infer<typeof UrlSourceConfigSchema>;
export type UrlSourceConfigCreate = z.infer<typeof UrlSourceConfigCreateSchema>;
export type KnowledgeSourceConfig = z.infer<typeof KnowledgeSourceConfigSchema>;

// Knowledge Source Configuration Expanded Schema (with related data)
export const KnowledgeSourceConfigExpandedSchema = KnowledgeSourceConfigSchema.extend({
  content_filter: z.record(z.any()).nullable().optional(),
  model_provider: z.record(z.any()).nullable().optional(),
  url_source: z.record(z.any()).nullable().optional(),
});

export type KnowledgeSourceConfigExpanded = z.infer<typeof KnowledgeSourceConfigExpandedSchema>;

// Knowledge Source Configuration Create Schema
export const KnowledgeSourceConfigCreateSchema = z.object({
  name: z.string(),
  description: z.string().optional().default(""),
  content_source_type: ContentSourceTypeSchema.default('web_scraping'),
  url: z.string().optional(),
  scraping_mode: ScrapingModeSchema.optional(),
  url_source: UrlSourceConfigCreateSchema.optional(),
  allowed_subdomains: z.array(z.string()).nullable().optional(),
  blocked_subdomains: z.array(z.string()).nullable().optional(),
  url_patterns: z.array(z.record(z.any())).nullable().optional(),
  crawl_depth: z.number().nullable().optional(),
  target_elements: z.array(z.string()).default([]),
  content_filter_threshold: z.number().default(0.6),
  output_format: z.enum(['html', 'markdown', 'llm_markdown']).default('html'),
  llm_content_filter_id: z.string().nullable().optional(),
  local_files: z.array(LocalFileSchema).nullable().optional(),
  file_types: z.array(z.string()).nullable().optional(),
});

export type KnowledgeSourceConfigCreate = z.infer<typeof KnowledgeSourceConfigCreateSchema>;

// Knowledge Source Configuration Update Schema
export const KnowledgeSourceConfigUpdateSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  content_source_type: ContentSourceTypeSchema.optional(),
  url: z.string().optional(),
  scraping_mode: ScrapingModeSchema.optional(),
  file_name: z.string().optional(),
  urls: z.array(z.string()).max(50000).optional(),
  url_source_id: z.string().nullable().optional(),
  allowed_subdomains: z.array(z.string()).nullable().optional(),
  blocked_subdomains: z.array(z.string()).nullable().optional(),
  url_patterns: z.array(z.record(z.any())).nullable().optional(),
  crawl_depth: z.number().nullable().optional(),
  target_elements: z.array(z.string()).optional(),
  content_filter_threshold: z.number().optional(),
  output_format: z.enum(['html', 'markdown', 'llm_markdown']).optional(),
  llm_content_filter_id: z.string().nullable().optional(),
  local_files: z.array(LocalFileSchema).nullable().optional(),
  file_types: z.array(z.string()).nullable().optional(),
});

export type KnowledgeSourceConfigUpdate = z.infer<typeof KnowledgeSourceConfigUpdateSchema>;

// Knowledge Job Schema
export const KnowledgeJobSchema = z.object({
  id: z.string(),
  knowledge_source_config_id: z.string(),
  user_id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  status: z.enum(['created', 'pending', 'running', 'completed', 'failed', 'cancelled']),

  // Document splitter configuration
  splitter_id: z.string(),
  custom_chunk_size: z.number().nullable().optional(),
  custom_chunk_overlap: z.number().nullable().optional(),

  // Embedding model configuration
  embedding_model_provider_id: z.string(),
  embedding_model_name: z.string(),

  // Job processing configuration
  batch_size: z.number(),
  save_to_file: z.boolean(),
  write_consolidated_file: z.boolean(),

  // Job execution details
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),

  // Job results
  documents_processed: z.number(),
  chunks_created: z.number(),

  // Metadata
  created_at: z.string(),
  created_by: z.string(),
});

export type KnowledgeJob = z.infer<typeof KnowledgeJobSchema>;

// Knowledge Job Create Schema
export const KnowledgeJobCreateSchema = z.object({
  name: z.string(),
  description: z.string().optional(),

  // Document splitter configuration
  splitter_id: z.string(),
  custom_chunk_size: z.number().min(64).optional(),
  custom_chunk_overlap: z.number().min(0).optional(),

  embedding_model_provider_id: z.string(),
  embedding_model_name: z.string(),
  batch_size: z.number().min(1).max(1000),
  save_to_file: z.boolean(),
  write_consolidated_file: z.boolean(),
});

export type KnowledgeJobCreate = z.infer<typeof KnowledgeJobCreateSchema>;

// ============================================================================
// KNOWLEDGE SOURCE CONFIGURATION API HOOKS
// ============================================================================

// List knowledge source configurations
export const useGetKnowledgeSourceConfigs = createGetQueryHook({
  endpoint: apiEndpoints.knowledgeSources.configs,
  responseSchema: z.array(KnowledgeSourceConfigSchema),
  rQueryParams: { queryKey: ['knowledge-source-configs'] },
});

// Get specific knowledge source configuration
export const useGetKnowledgeSourceConfig = (configId: string) => createGetQueryHook({
  endpoint: apiEndpoints.knowledgeSources.config(configId),
  responseSchema: KnowledgeSourceConfigSchema,
  rQueryParams: { queryKey: ['knowledge-source-config', { configId }] },
})();

// Get specific knowledge source configuration with expanded data
export const useGetKnowledgeSourceConfigExpanded = (configId: string, expand?: string) => {
  const endpoint = expand
    ? `${apiEndpoints.knowledgeSources.config(configId)}?expand=${encodeURIComponent(expand)}`
    : apiEndpoints.knowledgeSources.config(configId);

  return createGetQueryHook({
    endpoint,
    responseSchema: KnowledgeSourceConfigExpandedSchema,
    rQueryParams: {
      queryKey: ['knowledge-source-config-expanded', { configId, expand }]
    },
  })();
};

// Create knowledge source configuration (unified - supports both JSON and FormData with files)
export const useCreateKnowledgeSourceConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      configData,
      files
    }: {
      configData: KnowledgeSourceConfigCreate,
      files?: File[]
    }) => {
      // Use the same axios client as other endpoints for consistent authentication
      const { client } = await import('../axios');

      // If files are provided, use FormData; otherwise use standard JSON
      if (files && files.length > 0) {
        console.log('📤 Creating config with files:', {
          configName: configData.name,
          filesCount: files.length,
          contentSourceType: configData.content_source_type,
          allKeys: Object.keys(configData)
        });

        // configData should already be clean from the wizard
        // Just stringify and send it
        const jsonString = JSON.stringify(configData);
        console.log('📤 JSON being sent to backend:', jsonString);

        const formData = new FormData();
        formData.append('config_data_json', jsonString);

        files.forEach((file) => {
          formData.append('files', file);
        });

        console.log('📤 FormData prepared with config_data_json and', files.length, 'files');

        const response = await client.post(apiEndpoints.knowledgeSources.configs, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        return KnowledgeSourceConfigSchema.parse(response.data);
      } else {
        console.log('📤 Creating config without files:', {
          configName: configData.name,
          contentSourceType: configData.content_source_type
        });

        // Standard JSON request for web scraping configs
        const response = await client.post(
          apiEndpoints.knowledgeSources.configs,
          configData
        );

        return KnowledgeSourceConfigSchema.parse(response.data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-source-configs'] });
    },
  });
};

// Update knowledge source configuration
export const useUpdateKnowledgeSourceConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      configId,
      updateData,
      files
    }: {
      configId: string,
      updateData: KnowledgeSourceConfigUpdate,
      files?: File[]
    }) => {
      // Use the same axios client as other endpoints for consistent authentication
      const { client } = await import('../axios');

      // If files are provided, use FormData; otherwise use standard JSON
      if (files && files.length > 0) {
        console.log('📤 Updating config with files:', {
          configId,
          filesCount: files.length,
          existingFiles: updateData.local_files?.length || 0
        });

        const jsonString = JSON.stringify(updateData);
        console.log('📤 Update JSON being sent to backend:', jsonString);

        const formData = new FormData();
        formData.append('config_data_json', jsonString);

        files.forEach((file) => {
          formData.append('files', file);
        });

        console.log('📤 FormData prepared with config_data_json and', files.length, 'new files');

        const response = await client.put(
          apiEndpoints.knowledgeSources.config(configId),
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        return KnowledgeSourceConfigSchema.parse(response.data);
      } else {
        console.log('📤 Updating config without new files:', { configId });

        // Standard JSON request
        const response = await client.put(
          apiEndpoints.knowledgeSources.config(configId),
          updateData
        );

        return KnowledgeSourceConfigSchema.parse(response.data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-source-configs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-source-config'] });
      queryClient.invalidateQueries({ queryKey: ['url-source-config'] });
    },
  });
};

// Delete knowledge source configuration
export const useDeleteKnowledgeSourceConfig = createDeleteMutationHook({
  endpoint: apiEndpoints.knowledgeSources.config(':configId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-source-configs'] });
    },
  },
});

// Get URL source configuration
export const useGetUrlSourceConfig = (configId: string, urlSourceId: string, options?: { enabled?: boolean }) => createGetQueryHook<typeof UrlSourceConfigSchema, {}, {}>({
  endpoint: apiEndpoints.knowledgeSources.urlSource(configId, urlSourceId),
  responseSchema: UrlSourceConfigSchema,
  rQueryParams: {
    queryKey: ['url-source-config', { configId, urlSourceId }],
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
})({ enabled: options?.enabled !== false && !!configId && !!urlSourceId });

// ============================================================================
// KNOWLEDGE JOB API HOOKS
// ============================================================================

// List knowledge jobs for a specific configuration
export const useGetKnowledgeJobsForConfig = (configId: string) => createGetQueryHook({
  endpoint: apiEndpoints.knowledgeSources.configJobs(configId),
  responseSchema: z.array(KnowledgeJobSchema),
  rQueryParams: { queryKey: ['knowledge-jobs-for-config', { configId }] },
})();

// Create knowledge job
export const useCreateKnowledgeJob = createPostMutationHook({
  endpoint: apiEndpoints.knowledgeSources.configJobs(':configId'),
  bodySchema: KnowledgeJobCreateSchema,
  responseSchema: KnowledgeJobSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs-for-config'] });
    },
  },
});
