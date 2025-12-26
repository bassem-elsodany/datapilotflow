/**
 * Unified Model Providers API Resources
 * 
 * This module provides Zod schemas and React Query hooks for unified model provider-related API interactions.
 * These providers support both embedding and generative models with a single API key.
 */

import { useQueryClient } from '@tanstack/react-query';
import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '../helpers';

// ============================================================================
// Zod Schemas
// ============================================================================

export const ModelTypeSchema = z.enum(['embedding', 'generative', 'reranker', 'both']);
// Runtime enum-like helper for UI usage
export const ModelType = {
  EMBEDDING: 'embedding',
  GENERATIVE: 'generative',
  RERANKER: 'reranker',
  BOTH: 'both',
} as const;

export const ModelTypeConfigSchema = z.object({
  models: z.array(z.string()),
  config: z.record(z.any()),
  endpoint: z.string().optional().nullable(),
});

export const ModelProviderSchema = z.object({
  id: z.string(),
  name: z.string(),
  provider_type: z.string(),
  endpoint: z.string().optional(),
  api_key: z.string().nullable(),
  description: z.string().nullable(),
  is_active: z.boolean(),
  timeout: z.number(),
  embedding: ModelTypeConfigSchema.nullable(),
  generative: ModelTypeConfigSchema.nullable(),
  reranker: ModelTypeConfigSchema.nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string(),
  updated_by: z.string(),
});

export const ModelProviderResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  provider_type: z.string(),
  endpoint: z.string().optional(),
  api_key: z.string().nullable(),
  api_key_field_name: z.string().default('api_key'),
  description: z.string().nullable(),
  is_active: z.boolean(),
  timeout: z.number(),
  embedding: ModelTypeConfigSchema.nullable(),
  generative: ModelTypeConfigSchema.nullable(),
  reranker: ModelTypeConfigSchema.nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string(),
  updated_by: z.string(),
});

export const ModelProviderCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  provider_type: z.string().min(1, 'Provider type is required'),
  endpoint: z.string().optional().or(z.literal('')),
  api_key: z.string().optional(),
  api_key_field_name: z.string().default('api_key'),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
  timeout: z.number().min(1).max(300).default(60),
  embedding: ModelTypeConfigSchema.optional(),
  generative: ModelTypeConfigSchema.optional(),
  reranker: ModelTypeConfigSchema.optional(),
});

export const ModelProviderUpdateSchema = z.object({
  name: z.string().min(1, 'Name is required').optional(),
  provider_type: z.string().min(1, 'Provider type is required').optional(),
  endpoint: z.string().optional().or(z.literal('')),
  api_key: z.string().optional(),
  api_key_field_name: z.string().optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
  timeout: z.number().min(1).max(300).optional(),
  embedding: ModelTypeConfigSchema.optional(),
  generative: ModelTypeConfigSchema.optional(),
  reranker: ModelTypeConfigSchema.optional(),
});

// ============================================================================
// TypeScript Types
// ============================================================================

export type ModelType = z.infer<typeof ModelTypeSchema>;
export type ModelTypeConfig = z.infer<typeof ModelTypeConfigSchema>;
export type ModelProvider = z.infer<typeof ModelProviderSchema>;
export type ModelProviderResponse = z.infer<typeof ModelProviderResponseSchema>;
export type ModelProviderCreate = z.infer<typeof ModelProviderCreateSchema>;
export type ModelProviderUpdate = z.infer<typeof ModelProviderUpdateSchema>;
export const ModelProviderTestResponseSchema = z.object({
  success: z.boolean(),
  status_code: z.number().optional(),
  duration_ms: z.number().optional(),
  body: z.string().optional(),
  message: z.string().optional(),
});

// ============================================================================
// React Query Hooks
// ============================================================================

// List model providers
export const useGetModelProviders = createGetQueryHook({
  endpoint: apiEndpoints.modelProviders.list,
  responseSchema: z.array(ModelProviderResponseSchema),
  rQueryParams: {
    queryKey: ['model-providers'],
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 3,
    retryDelay: 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  },
});

// Get single model provider
export const useGetModelProvider = (providerId: string) =>
  createGetQueryHook({
    endpoint: apiEndpoints.modelProviders.get(providerId),
    responseSchema: ModelProviderResponseSchema,
    rQueryParams: {
      queryKey: ['model-providers', { providerId }],
      staleTime: 0,
      gcTime: 0,
      refetchOnMount: true,
      refetchOnWindowFocus: true,
    },
  })();

// Get active model providers (uses query param on main list endpoint)
export const useGetActiveModelProviders = createGetQueryHook({
  endpoint: `${apiEndpoints.modelProviders.list}?is_active=true`,
  responseSchema: z.array(ModelProviderResponseSchema),
  rQueryParams: {
    queryKey: ['model-providers', { status: 'active' }],
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  },
});

// Get providers by model type (uses query param on main list endpoint)
export const useGetProvidersByType = (modelType: ModelType) =>
  createGetQueryHook({
    endpoint: `${apiEndpoints.modelProviders.list}?supported_model_type=${modelType}`,
    responseSchema: z.array(ModelProviderResponseSchema),
    rQueryParams: { queryKey: ['model-providers', { type: 'by-type', modelType }] },
  })();

// Create model provider
export const useCreateModelProvider = createPostMutationHook({
  endpoint: apiEndpoints.modelProviders.create,
  bodySchema: ModelProviderCreateSchema,
  responseSchema: ModelProviderResponseSchema,
});

// Update model provider
export const useUpdateModelProvider = (providerId: string) =>
  createPutMutationHook({
    endpoint: apiEndpoints.modelProviders.update(providerId),
    bodySchema: ModelProviderUpdateSchema,
    responseSchema: ModelProviderResponseSchema,
  })();

// Test model provider before creation (live call without saving)
export const useTestModelProvider = createPostMutationHook({
  endpoint: apiEndpoints.modelProviders.test,
  bodySchema: z.object({
    provider: ModelProviderCreateSchema,
    test_type: z.enum(['embedding', 'generative', 'reranker']),
    model: z.string(),
  }),
  responseSchema: ModelProviderTestResponseSchema,
});

// Test existing model provider by ID
export const useTestModelProviderById = (providerId: string) =>
  createPostMutationHook({
    endpoint: apiEndpoints.modelProviders.testById(providerId),
    bodySchema: z.object({
      test_type: z.enum(['embedding', 'generative', 'reranker']),
      model: z.string(),
    }),
    responseSchema: ModelProviderTestResponseSchema,
  })();

// Get supported models for a provider
export const useGetSupportedModels = (providerId: string, modelType?: string) =>
  createGetQueryHook({
    endpoint: apiEndpoints.modelProviders.models(providerId, modelType),
    responseSchema: z.array(z.string()),
    rQueryParams: {
      queryKey: ['model-providers', { providerId, modelType: modelType || '' }],
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      enabled: !!providerId,
      retry: 2,
      retryDelay: 1000,
      refetchOnWindowFocus: false,
    },
  })();

// Get available models for a provider name from LiteLLM SDK
export const useGetAvailableModels = (providerName: string, modelType?: string) => {
  // Normalize and validate provider name
  const validProviderName = (providerName || '').trim();
  const isEnabled = validProviderName.length > 0;

  return createGetQueryHook({
    endpoint: apiEndpoints.litellmProviders.models(validProviderName, modelType),
    responseSchema: z.array(z.string()),
    rQueryParams: {
      queryKey: ['litellm-providers', { providerName: validProviderName, modelType: modelType || '', type: 'models' }],
      staleTime: 30 * 60 * 1000, // 30 minutes (LiteLLM data changes infrequently)
      gcTime: 60 * 60 * 1000, // 60 minutes (formerly cacheTime)
      enabled: isEnabled,
      retry: 2,
      retryDelay: 1000,
      refetchOnWindowFocus: false,
    },
  })();
};

// Get all available provider names from LiteLLM SDK
export const useGetAvailableProviderTypes = createGetQueryHook({
  endpoint: apiEndpoints.litellmProviders.list,
  responseSchema: z.array(z.string()),
  rQueryParams: {
    queryKey: ['litellm-providers', { type: 'list' }],
    staleTime: 30 * 60 * 1000, // 30 minutes (LiteLLM data changes infrequently)
    gcTime: 60 * 60 * 1000, // 60 minutes
    retry: 2,
    retryDelay: 1000,
    refetchOnWindowFocus: false,
  },
});

// Delete model provider
export const useDeleteModelProvider = (providerId: string) => {
  const queryClient = useQueryClient();
  
  return createDeleteMutationHook<typeof ModelProviderResponseSchema, { providerId: string }>({
    endpoint: apiEndpoints.modelProviders.delete(providerId),
    rMutationParams: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['model-providers'] });
      },
    },
  })({ route: { providerId } });
};
