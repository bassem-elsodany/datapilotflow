import { User } from '@/api/entities';
import { createGetQueryHook } from '@/api/helpers';
import { apiEndpoints } from '@/config';

export const useGetAccountInfo = createGetQueryHook({
  endpoint: apiEndpoints.users.me,
  responseSchema: User,
  rQueryParams: { queryKey: ['account'] },
});
