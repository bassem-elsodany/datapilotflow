import { User } from '@/api/entities';
import { createGetQueryHook } from '@/api/helpers';
import { apiEndpoints } from '@/config';

export const useGetAccountInfo = createGetQueryHook({
  endpoint: apiEndpoints.auth.me,
  responseSchema: User,
  rQueryParams: { queryKey: ['account'] },
});
