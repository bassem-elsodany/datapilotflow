import { Alert, Group, Button, Badge } from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';
import { useApiHealth } from '@/hooks/use-api-health';

interface ApiHealthBannerProps {
  className?: string;
}

export function ApiHealthBanner({ className }: ApiHealthBannerProps) {
  const { isHealthy, isChecking, checkHealth, version, features } = useApiHealth();

  // Only show banner when API is down
  if (isHealthy !== false) {
    return null;
  }

  return (
    <Alert
      icon={<IconAlertTriangle size={16} />}
      title="API Connection Issue"
      color="red"
      variant="light"
      className={className}
    >
      <Group justify="space-between" align="center">
        <span>
          The API server is not reachable. Some features may not work properly.
        </span>
        <Button
          variant="light"
          size="xs"
          leftSection={<IconRefresh size={14} />}
          onClick={checkHealth}
          loading={isChecking}
        >
          Retry Connection
        </Button>
      </Group>
      {version && (
        <Group gap="xs" mt="xs">
          <Badge variant="light" color="gray">v{version}</Badge>
        </Group>
      )}
      {Array.isArray(features) && features.length > 0 && (
        <Group gap="xs" mt="xs">
          {features.slice(0,6).map((f) => (
            <Badge key={f.name} variant="light" color={f.status === 'up' || f.status === 'enabled' || f.status === 'configured' ? 'green' : 'red'}>
              {f.name}: {f.status}
            </Badge>
          ))}
        </Group>
      )}
    </Alert>
  );
}
