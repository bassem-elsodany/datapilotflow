import { ReactNode } from 'react';
import { Center, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';
import { usePermissions } from '@/hooks/use-permissions';

interface PermissionGuardProps {
  /** The permission string that is required to render children, e.g. "knowledge:read" */
  permission: string;
  children: ReactNode;
  /** Custom fallback � defaults to an inline "Access Denied" message */
  fallback?: ReactNode;
}

function AccessDenied({ permission }: { permission: string }) {
  return (
    <Center h="60vh">
      <Stack align="center" gap="md">
        <ThemeIcon size={64} radius="xl" color="red" variant="light">
          <IconLock size={32} />
        </ThemeIcon>
        <Title order={3} c="dimmed">
          Access Denied
        </Title>
        <Text c="dimmed" size="sm" ta="center" maw={320}>
          You do not have the required permission{' '}
          <Text component="span" fw={600} c="red">
            {permission}
          </Text>{' '}
          to view this page. Contact your administrator to request access.
        </Text>
      </Stack>
    </Center>
  );
}

export function PermissionGuard({ permission, children, fallback }: PermissionGuardProps) {
  const { hasPermission, isAdmin } = usePermissions();

  if (!isAdmin() && !hasPermission(permission)) {
    return fallback ?? <AccessDenied permission={permission} />;
  }

  return <>{children}</>;
}
