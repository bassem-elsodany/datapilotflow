import { Badge, Group, ActionIcon, Tooltip } from '@mantine/core';
import { IconRefresh, IconWifi, IconWifiOff, IconLoader } from '@tabler/icons-react';
import { useApiHealth } from '@/hooks/use-api-health';

interface ApiStatusProps {
  className?: string;
}

export function ApiStatus({ className }: ApiStatusProps) {
  const { isHealthy, isChecking, checkHealth, version } = useApiHealth();

  const getStatusIcon = () => {
    if (isChecking) {
      return <IconLoader size={14} className="animate-spin" />;
    }
    if (isHealthy === true) {
      return <IconWifi size={14} />;
    }
    return <IconWifiOff size={14} />;
  };

  const getStatusColor = () => {
    if (isChecking) return 'yellow';
    if (isHealthy === true) return 'green';
    return 'red';
  };

  const getStatusText = () => {
    if (isChecking) return 'Checking...';
    if (isHealthy === true) return 'Connected';
    return 'Disconnected';
  };

  return (
    <Group gap="xs" className={className}>
      <Tooltip label={isHealthy === false ? 'Click to retry connection' : `API ${version ? `v${version} ` : ''}Connection Status`}>
        <Badge
          color={getStatusColor()}
          variant="light"
          size="sm"
          leftSection={getStatusIcon()}
          style={{ cursor: isHealthy === false ? 'pointer' : 'default' }}
          onClick={isHealthy === false ? checkHealth : undefined}
        >
          {getStatusText()}
        </Badge>
      </Tooltip>
      
      {isHealthy === false && (
        <Tooltip label="Retry connection">
          <ActionIcon
            variant="light"
            size="xs"
            color="red"
            onClick={checkHealth}
            loading={isChecking}
          >
            <IconRefresh size={12} />
          </ActionIcon>
        </Tooltip>
      )}
    </Group>
  );
}
