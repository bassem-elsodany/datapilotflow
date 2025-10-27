/**
 * Unified Model Providers API Resources
 * 
 * This module provides Zod schemas and React Query hooks for unified model provider-related API interactions.
 * These providers support both embedding and generative models with a single API key.
 */

import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook } from '../helpers';

// ============================================================================
// Zod Schemas
// ============================================================================

export const ModelTypeSchema = z.enum(['embedding', 'generative', 'both']);

export const ModelTypeConfigSchema = z.object({
  models: z.array(z.string()),
  config: z.record(z.any()),
});

export const ModelProviderSchema = z.object({
  id: z.string(),
  name: z.string(),
  provider_type: z.string(),
  endpoint: z.string(),
  api_key: z.string(),
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
  endpoint: z.string(),
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
  endpoint: z.string().url('Must be a valid URL'),
  api_key: z.string().min(1, 'API key is required'),
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
  endpoint: z.string().url('Must be a valid URL').optional(),
  api_key: z.string().min(1, 'API key is required').optional(),
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
    rQueryParams: { queryKey: ['model-providers', providerId] },
  })();

// Get active model providers
export const useGetActiveModelProviders = createGetQueryHook({
  endpoint: apiEndpoints.modelProviders.active,
  responseSchema: z.array(ModelProviderResponseSchema),
  rQueryParams: { queryKey: ['model-providers', 'active'] },
});

// Get providers by model type
export const useGetProvidersByType = (modelType: ModelType) =>
  createGetQueryHook({
    endpoint: apiEndpoints.modelProviders.byType(modelType),
    responseSchema: z.array(ModelProviderResponseSchema),
    rQueryParams: { queryKey: ['model-providers', 'by-type', modelType] },
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

