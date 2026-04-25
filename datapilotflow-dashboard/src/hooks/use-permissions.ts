import { useGetAccountInfo } from '@/hooks/api/account';

export function usePermissions() {
  const { data: me } = useGetAccountInfo();
  const permissions: string[] = me?.permissions ?? [];
  const roles: string[] = me?.roles ?? [];

  return {
    hasPermission: (perm: string) => permissions.includes(perm),
    hasRole: (role: string) => roles.includes(role),
    isAdmin: () =>
      roles.some((r) => r.toLowerCase() === 'platform admin' || r.toLowerCase() === 'admin'),
    permissions,
    roles,
  };
}
