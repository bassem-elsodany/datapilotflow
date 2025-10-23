import { useQuery } from '@tanstack/react-query';
import { client } from '@/api/axios';
import { getAccountInfo } from '@/api/resources/account';

export interface KnowledgeJob {
  file_id: string;
  job_id?: string;
  job_type?: string;
  status: string;
  filename?: string;
  message?: string;
  upload_timestamp?: string;
  status_history?: Array<{
    status: string;
    message: string;
    timestamp: string;
  }>;
  processing_results?: any;
  error_details?: any;
}

export function useGetKnowledgeJobs() {
  return useQuery({
    queryKey: ['knowledge', 'jobs'],
    queryFn: async (): Promise<KnowledgeJob[]> => {
      // First get user info to get email
      const user = await getAccountInfo();
      
      // Then fetch jobs for the user
      const response = await client.get(`/knowledge/jobs?user_id=${user.email}`);
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}

export function useGetKnowledgeJobStatus(fileId: string) {
  return useQuery({
    queryKey: ['knowledge', 'status', fileId],
    queryFn: async (): Promise<KnowledgeJob> => {
      const response = await client.get(`/knowledge/status/${fileId}`);
      return response.data;
    },
    enabled: !!fileId,
    staleTime: 5000, // 5 seconds
    refetchInterval: 2000, // Refetch every 2 seconds
  });
}
