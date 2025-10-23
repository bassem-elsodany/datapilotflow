/**
 * VectorDB API Resource
 *
 * This module provides React Query hooks and Zod schemas for interacting
 * with the Vector Database collections API.
 */

import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createGetQueryHook } from '../helpers';

// ===========================
// Zod Schemas
// ===========================

/**
 * Schema for a field in a collection
 */
export const FieldSchemaSchema = z.object({
  name: z.string(),
  type: z.string(),
  is_primary: z.boolean().optional().default(false),
  auto_id: z.boolean().optional().default(false),
  dimension: z.number().optional().nullable(),
  max_length: z.number().optional().nullable(),
  indexed: z.boolean().optional().default(false),
});

export type FieldSchema = z.infer<typeof FieldSchemaSchema>;

/**
 * Schema for collection information
 */
export const CollectionInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional().nullable(),
  dimension: z.number(),
  record_count: z.number(),
  metric_type: z.string().optional().nullable(),
  index_type: z.string().optional().nullable(),
  created_at: z.string().optional().nullable(),
  updated_at: z.string().optional().nullable(),
});

export type CollectionInfo = z.infer<typeof CollectionInfoSchema>;

/**
 * Schema for collection schema
 */
export const CollectionSchemaSchema = z.object({
  collection_id: z.string(),
  fields: z.array(FieldSchemaSchema),
});

export type CollectionSchema = z.infer<typeof CollectionSchemaSchema>;

/**
 * Schema for collection statistics
 */
export const CollectionStatsSchema = z.object({
  collection_id: z.string(),
  total_records: z.number(),
  records_by_job: z.record(z.string(), z.number()).optional().default({}),
  date_range: z
    .object({
      earliest: z.string(),
      latest: z.string(),
    })
    .optional()
    .nullable(),
  avg_content_length: z.number().optional().nullable(),
  unique_sources: z.number().optional().nullable(),
});

export type CollectionStats = z.infer<typeof CollectionStatsSchema>;

/**
 * Schema for a vector record (without the vector)
 */
export const VectorRecordSchema = z.object({
  id: z.string(),
  source_url: z.string().optional().nullable(),
  job_id: z.string().optional().nullable(),
  title: z.string().optional().nullable(),
  page_content: z.string().optional().nullable(),
  chunk_index: z.number().optional().nullable(),
  total_chunks: z.number().optional().nullable(),
  created_at: z.string().optional().nullable(),
  metadata: z.record(z.string(), z.any()).optional().default({}),
});

export type VectorRecord = z.infer<typeof VectorRecordSchema>;

/**
 * Schema for paginated records response
 */
export const RecordResponseSchema = z.object({
  collection_id: z.string(),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
  records: z.array(VectorRecordSchema),
});

export type RecordResponse = z.infer<typeof RecordResponseSchema>;

// ===========================
// React Query Hooks
// ===========================

/**
 * Hook to get all vector collections
 */
export const useGetCollections = () =>
  createGetQueryHook<z.ZodArray<typeof CollectionInfoSchema>, {}, {}>({
    endpoint: apiEndpoints.vectordb.collections,
    responseSchema: z.array(CollectionInfoSchema),
    rQueryParams: {
      queryKey: ['vectordb-collections'],
    },
  })({});

/**
 * Hook to get a specific collection
 */
export const useGetCollection = (collectionId: string, enabled = true) =>
  createGetQueryHook<typeof CollectionInfoSchema, {}, {}>({
    endpoint: apiEndpoints.vectordb.collection(collectionId),
    responseSchema: CollectionInfoSchema,
    rQueryParams: {
      queryKey: ['vectordb-collection', { collectionId }],
    },
  })({ enabled: enabled && !!collectionId });

/**
 * Hook to get collection schema
 */
export const useGetCollectionSchema = (collectionId: string, enabled = true) =>
  createGetQueryHook<typeof CollectionSchemaSchema, {}, {}>({
    endpoint: apiEndpoints.vectordb.schema(collectionId),
    responseSchema: CollectionSchemaSchema,
    rQueryParams: {
      queryKey: ['vectordb-collection-schema', { collectionId }],
    },
  })({ enabled: enabled && !!collectionId });

/**
 * Hook to get collection statistics
 */
export const useGetCollectionStats = (collectionId: string, enabled = true) =>
  createGetQueryHook<typeof CollectionStatsSchema, {}, {}>({
    endpoint: apiEndpoints.vectordb.stats(collectionId),
    responseSchema: CollectionStatsSchema,
    rQueryParams: {
      queryKey: ['vectordb-collection-stats', { collectionId }],
    },
  })({ enabled: enabled && !!collectionId });

/**
 * Hook to get collection records
 */
export const useGetCollectionRecords = (
  collectionId: string,
  params?: {
    limit?: number;
    offset?: number;
    job_id?: string;
    source_url?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  },
  enabled = true
) => {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.set('limit', params.limit.toString());
  if (params?.offset) queryParams.set('offset', params.offset.toString());
  if (params?.job_id) queryParams.set('job_id', params.job_id);
  if (params?.source_url) queryParams.set('source_url', params.source_url);
  if (params?.search) queryParams.set('search', params.search);
  if (params?.sort_by) queryParams.set('sort_by', params.sort_by);
  if (params?.sort_order) queryParams.set('sort_order', params.sort_order);

  const url = `${apiEndpoints.vectordb.records(collectionId)}${queryParams.toString() ? `?${queryParams.toString()}` : ''
    }`;

  return createGetQueryHook<typeof RecordResponseSchema, {}, {}>({
    endpoint: url,
    responseSchema: RecordResponseSchema,
    rQueryParams: {
      queryKey: ['vectordb-collection-records', { collectionId, ...params }],
    },
  })({ enabled: enabled && !!collectionId });
};
