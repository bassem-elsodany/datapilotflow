import { client } from '@/api/axios';
import { useGetKnowledgeJobs } from '@/api/resources/knowledge-jobs';
import { useQuery } from '@tanstack/react-query';

export interface JobTimeline {
  id: string;
  job_id: string;
  user_id: string;
  status: 'created' | 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  documents_processed: number;
  chunks_created: number;
  processing_time_seconds: number;
  error_message?: string;
  error_traceback?: string;
  execution_context?: any;
  triggered_by?: string;
  created_at: string;
  updated_at: string;
}

export interface JobWithStatus {
  id: string;
  name: string;
  description?: string;
  knowledge_source_config_id: string;
  vectordb_collection_id: string;
  user_id: string;
  created_at: string;
  created_by: string;
  // Job processing configuration
  batch_size: number;
  save_to_file: boolean;
  write_consolidated_file: boolean;
  clear_collection_before_start: boolean;
  check_duplicates_before_insert: boolean;
  // Status from latest timeline entry
  current_status?: JobTimeline;
  is_running: boolean;
  last_execution?: string;
}

// Get all jobs with their current status
export function useGetJobsWithStatus() {
  const { data: jobs, isLoading: jobsLoading, error: jobsError } = useGetKnowledgeJobs();

  return useQuery({
    queryKey: ['jobs-with-status', jobs?.length],
    queryFn: async (): Promise<JobWithStatus[]> => {
      if (!jobs) return [];

      // Get timeline entries for each job to determine current status
      const jobsWithStatus = await Promise.all(
        jobs.map(async (job) => {
          try {
            // Get latest timeline entry for current status
            const latestTimelineResponse = await client.get(`/knowledge/jobs/${job.id}/timelines?latest=true`);
            const latestTimeline = latestTimelineResponse.data && latestTimelineResponse.data.length > 0 ? latestTimelineResponse.data[0] : null;

            // Only return jobs that have timeline records
            if (!latestTimeline) {
              return null;
            }

            return {
              ...job,
              current_status: latestTimeline,
              is_running: latestTimeline?.status === 'running',
              last_execution: latestTimeline?.started_at || job.created_at
            };
          } catch (error) {
            // If timeline fetch fails, return null to filter out this job
            return null;
          }
        })
      );

      // Filter out jobs that don't have timeline records (null values)
      return jobsWithStatus.filter((job) => job !== null) as JobWithStatus[];
    },
    staleTime: 0, // NO CACHING - Always treat data as stale
    gcTime: 0, // NO CACHE TIME - Clear cache immediately (formerly cacheTime)
    refetchInterval: false, // DISABLED - Polling is now handled manually in the component
    refetchOnMount: 'always', // Always refetch on mount
    refetchOnWindowFocus: true, // Refetch when window regains focus
    refetchOnReconnect: true, // Refetch when network reconnects
    enabled: !jobsLoading && !jobsError, // Only run when jobs are loaded successfully
  });
}

// Get timeline entries for a specific job
export function useGetJobTimeline(jobId: string) {
  return useQuery({
    queryKey: ['job-timeline', jobId],
    queryFn: async (): Promise<JobTimeline[]> => {
      const response = await client.get(`/knowledge/jobs/${jobId}/timelines`);
      return response.data;
    },
    enabled: !!jobId,
    staleTime: 0, // NO CACHING - Always treat data as stale
    gcTime: 0, // NO CACHE TIME - Clear cache immediately
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
    refetchOnMount: 'always', // Always refetch on mount
    refetchOnWindowFocus: true, // Refetch when window regains focus
    refetchOnReconnect: true, // Refetch when network reconnects
  });
}
