/**
 * Job Timeline API Resources
 * 
 * This module provides React Query hooks and Zod schemas for job timeline management.
 */

import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createGetQueryHook, createPutMutationHook } from '../helpers';

// Job Timeline Schema
export const JobTimelineSchema = z.object({
  id: z.string(),
  job_id: z.string(),
  user_id: z.string(),
  status: z.enum(['created', 'pending', 'running', 'completed', 'failed', 'cancelled']),
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  documents_processed: z.number(),
  chunks_created: z.number(),
  processing_time_seconds: z.number(),
  error_message: z.string().nullable().optional(),
  error_traceback: z.string().nullable().optional(),
  execution_context: z.record(z.any()).nullable().optional(),
  triggered_by: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type JobTimeline = z.infer<typeof JobTimelineSchema>;

// Job Timeline Create Schema
export const JobTimelineCreateSchema = z.object({
  job_id: z.string(),
  user_id: z.string(),
  status: z.enum(['created', 'pending', 'running', 'completed', 'failed', 'cancelled']),
  started_at: z.string().nullable().optional(),
  documents_processed: z.number().default(0),
  chunks_created: z.number().default(0),
  processing_time_seconds: z.number().default(0),
  error_message: z.string().nullable().optional(),
  error_traceback: z.string().nullable().optional(),
  execution_context: z.record(z.any()).nullable().optional(),
  triggered_by: z.string().nullable().optional(),
});

export type JobTimelineCreate = z.infer<typeof JobTimelineCreateSchema>;

// Job Timeline Update Schema
export const JobTimelineUpdateSchema = z.object({
  status: z.enum(['created', 'pending', 'running', 'completed', 'failed', 'cancelled']).optional(),
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  documents_processed: z.number().optional(),
  chunks_created: z.number().optional(),
  processing_time_seconds: z.number().optional(),
  error_message: z.string().nullable().optional(),
  error_traceback: z.string().nullable().optional(),
  execution_context: z.record(z.any()).nullable().optional(),
  triggered_by: z.string().nullable().optional(),
});

export type JobTimelineUpdate = z.infer<typeof JobTimelineUpdateSchema>;

// Job Timeline Statistics Schema
export const JobTimelineStatisticsSchema = z.object({
  job_id: z.string(),
  statistics: z.object({
    total_executions: z.number(),
    successful_executions: z.number(),
    failed_executions: z.number(),
    total_documents_processed: z.number(),
    total_chunks_created: z.number(),
    total_processing_time: z.number(),
    last_execution: z.string().nullable().optional(),
  }),
});

// Fallback schema that handles both object and array responses
export const JobTimelineStatisticsFallbackSchema = z.union([
  JobTimelineStatisticsSchema,
  z.array(z.any()).transform(() => ({
    // Transform array response to expected object format
    job_id: '',
    statistics: {
      total_executions: 0,
      successful_executions: 0,
      failed_executions: 0,
      total_documents_processed: 0,
      total_chunks_created: 0,
      total_processing_time: 0,
      last_execution: null,
    },
  })),
  z.object({
    // Handle case where backend returns partial object
    job_id: z.string().optional(),
    statistics: z.object({
      total_executions: z.number().default(0),
      successful_executions: z.number().default(0),
      failed_executions: z.number().default(0),
      total_documents_processed: z.number().default(0),
      total_chunks_created: z.number().default(0),
      total_processing_time: z.number().default(0),
      last_execution: z.string().nullable().optional(),
    }).default({}),
  }),
]);

export type JobTimelineStatistics = z.infer<typeof JobTimelineStatisticsSchema>;

// React Query Hooks

// List timeline entries for a job
export const useJobTimelineEntries = (jobId: string, options?: {
  status?: string;
  limit?: number;
  skip?: number;
}) => {
  const queryParams: Record<string, string | number> = {};
  if (options?.status) queryParams.status = options.status;
  if (options?.limit) queryParams.limit = options.limit;
  if (options?.skip) queryParams.skip = options.skip;

  return createGetQueryHook<z.ZodArray<typeof JobTimelineSchema>, {}, {}>({
    endpoint: apiEndpoints.jobTimelines.listByJob(jobId),
    responseSchema: z.array(JobTimelineSchema),
    rQueryParams: {
      queryKey: ['job-timelines', { jobId }],
      staleTime: 0, // NO CACHING - Always treat data as stale
      gcTime: 0, // NO CACHE TIME - Clear cache immediately
      refetchOnMount: 'always', // Always refetch on mount
      refetchOnWindowFocus: true, // Refetch when window regains focus
      refetchOnReconnect: true, // Refetch when network reconnects
      retry: false, // Disable retries for faster updates
    },
  })({ query: queryParams });
};

// Get specific timeline entry
export const useJobTimelineEntry = (timelineId: string) => createGetQueryHook<typeof JobTimelineSchema, {}, {}>({
  endpoint: apiEndpoints.jobTimelines.get(timelineId),
  responseSchema: JobTimelineSchema,
  rQueryParams: { queryKey: ['job-timeline', { timelineId }] },
})();

// Get latest timeline entry for a job
export const useLatestJobTimelineEntry = (jobId: string) => createGetQueryHook<z.ZodArray<typeof JobTimelineSchema>, {}, {}>({
  endpoint: apiEndpoints.jobTimelines.getLatest(jobId),
  responseSchema: z.array(JobTimelineSchema),
  rQueryParams: {
    queryKey: ['job-timeline-latest', { jobId }],
    staleTime: 0, // NO CACHING - Always treat data as stale
    gcTime: 0, // NO CACHE TIME - Clear cache immediately
    refetchOnMount: 'always', // Always refetch on mount
    refetchOnWindowFocus: true, // Refetch when window regains focus
    refetchOnReconnect: true, // Refetch when network reconnects
    retry: false, // Disable retries for faster updates
  },
})();

// Get job timeline statistics
export const useJobTimelineStatistics = (jobId: string) => createGetQueryHook<typeof JobTimelineStatisticsFallbackSchema, {}, {}>({
  endpoint: apiEndpoints.jobTimelines.getStatistics(jobId),
  responseSchema: JobTimelineStatisticsFallbackSchema,
  rQueryParams: {
    queryKey: ['job-timeline-statistics', { jobId }],
    retry: false, // Disable retries completely to avoid repeated failures
    enabled: !!jobId, // Only fetch if jobId exists
  },
})();

// Update timeline entry
export const useUpdateJobTimelineEntry = createPutMutationHook({
  endpoint: apiEndpoints.jobTimelines.update(':timelineId'),
  bodySchema: JobTimelineUpdateSchema,
  responseSchema: JobTimelineSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['job-timeline', data.id] });
      queryClient.invalidateQueries({ queryKey: ['job-timelines', data.job_id] });
      queryClient.invalidateQueries({ queryKey: ['job-timeline-latest', data.job_id] });
      queryClient.invalidateQueries({ queryKey: ['job-timeline-statistics', data.job_id] });
    },
  },
});
