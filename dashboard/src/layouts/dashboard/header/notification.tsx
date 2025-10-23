import { ReactNode, useState } from 'react';
import {
  ActionIcon,
  Badge,
  ElementProps,
  Grid,
  Group,
  Progress,
  Stack,
  Text,
  UnstyledButton,
  UnstyledButtonProps,
  Modal,
  Paper,
  Title,
  Code,
} from '@mantine/core';
import { IconCheck, IconX, IconDots } from '@tabler/icons-react';
import { CustomDate, formatRelativeDate } from '@/utilities/date';
import { capitalize } from '@/utilities/text';
import { Notification as NotificationType, NotificationStatus, NotificationType as NotificationTypeEnum } from '@/api/entities/notifications';
import classes from './notification.module.css';

interface NotificationBaseProps
  extends ElementProps<'button', keyof UnstyledButtonProps>,
    UnstyledButtonProps {
  notification: NotificationType;
  onMarkAsRead?: (notificationId: string) => void;
  onDismiss?: (notificationId: string) => void;
  onDelete?: (notificationId: string) => void;
}

const getNotificationIcon = (type: NotificationTypeEnum, status: NotificationStatus) => {
  switch (type) {
    case 'job_upload_progress':
    case 'resume_upload_progress':
      return '📄';
    case 'analysis_progress':
      return '🔍';
    case 'session_created':
    case 'session_updated':
      return '💼';
    case 'session_deleted':
      return '🗑️';
    case 'error':
      return '❌';
    case 'success':
      return '✅';
    case 'info':
      return 'ℹ️';
    default:
      return '🔔';
  }
};

const getStatusColor = (status: NotificationStatus) => {
  switch (status) {
    case 'completed':
      return 'green';
    case 'failed':
      return 'red';
    case 'in_progress':
      return 'blue';
    case 'pending':
      return 'yellow';
    case 'cancelled':
      return 'gray';
    default:
      return 'gray';
  }
};

const getTypeColor = (type: NotificationTypeEnum) => {
  switch (type) {
    case 'job_upload_progress':
    case 'resume_upload_progress':
      return 'blue';
    case 'analysis_progress':
      return 'purple';
    case 'session_created':
    case 'session_updated':
      return 'green';
    case 'session_deleted':
      return 'red';
    case 'error':
      return 'red';
    case 'success':
      return 'green';
    case 'info':
      return 'gray';
    default:
      return 'gray';
  }
};

export function Notification({
  notification,
  onMarkAsRead,
  onDismiss,
  onDelete,
  ...props
}: NotificationBaseProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isRead = !!notification.read_at;
  const isDismissed = !!notification.dismissed_at;
  const hasProgress = notification.progress !== null && notification.progress !== undefined;

  const handleNotificationClick = () => {
    setShowDetails(true);
    // Mark as read when clicked
    if (!isRead && onMarkAsRead) {
      onMarkAsRead(notification.notification_id);
    }
  };

  return (
    <>
      <UnstyledButton 
        className={`${classes.root} ${isRead ? classes.read : ''} ${isDismissed ? classes.dismissed : ''}`} 
        onClick={handleNotificationClick}
        {...props}
      >
        <Grid>
          <Grid.Col span={2}>
            <Text size="lg" ta="center">
              {getNotificationIcon(notification.type, notification.status)}
            </Text>
          </Grid.Col>

          <Grid.Col span={10}>
            <Stack gap="xs">
              <Group justify="space-between" align="flex-start">
                <Text fw={isRead ? 400 : 600} size="sm">
                  {notification.title}
                </Text>
                <Group gap="xs">
                  <Badge 
                    size="xs" 
                    color={getStatusColor(notification.status)}
                    variant="light"
                  >
                    {notification.status}
                  </Badge>
                  <Badge 
                    size="xs" 
                    color={getTypeColor(notification.type)}
                    variant="light"
                  >
                    {notification.type.replace('_', ' ')}
                  </Badge>
                </Group>
              </Group>

              <Text size="xs" c="dimmed" lineClamp={2}>
                {notification.message}
              </Text>

              {hasProgress && (
                <Progress 
                  value={notification.progress} 
                  size="xs" 
                  color={notification.progress === 100 ? 'green' : 'blue'}
                  label={`${Math.round(notification.progress)}%`}
                />
              )}

              <Group gap="xs" c="dimmed" fz="xs" justify="space-between">
                <Text c="inherit" fz="inherit">
                  {formatRelativeDate(notification.created_at)}
                </Text>
                
                <Group gap="xs">
                  {!isRead && onMarkAsRead && (
                    <ActionIcon 
                      size="xs" 
                      variant="subtle" 
                      color="green"
                      onClick={(e) => {
                        e.stopPropagation();
                        onMarkAsRead(notification.notification_id);
                      }}
                    >
                      <IconCheck size={12} />
                    </ActionIcon>
                  )}
                  
                  {onDismiss && (
                    <ActionIcon 
                      size="xs" 
                      variant="subtle" 
                      color="gray"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDismiss(notification.notification_id);
                      }}
                    >
                      <IconX size={12} />
                    </ActionIcon>
                  )}
                  
                  {onDelete && (
                    <ActionIcon 
                      size="xs" 
                      variant="subtle" 
                      color="red"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(notification.notification_id);
                      }}
                    >
                      <IconDots size={12} />
                    </ActionIcon>
                  )}
                </Group>
              </Group>
            </Stack>
          </Grid.Col>
        </Grid>
      </UnstyledButton>

      {/* Notification Details Modal */}
      <Modal
        opened={showDetails}
        onClose={() => setShowDetails(false)}
        title="Notification Details"
        size="lg"
      >
        <Stack gap="md">
          {/* Basic Information */}
          <Paper withBorder p="md">
            <Stack gap="xs">
              <Group>
                <Text fw={500}>Title:</Text>
                <Text>{notification.title}</Text>
              </Group>
              <Group>
                <Text fw={500}>Type:</Text>
                <Badge color={getTypeColor(notification.type)} variant="light">
                  {notification.type.replace('_', ' ')}
                </Badge>
              </Group>
              <Group>
                <Text fw={500}>Status:</Text>
                <Badge color={getStatusColor(notification.status)} variant="light">
                  {notification.status}
                </Badge>
              </Group>
              <Group>
                <Text fw={500}>Priority:</Text>
                <Badge color={notification.priority === 'high' ? 'red' : notification.priority === 'medium' ? 'yellow' : 'green'} variant="light">
                  {notification.priority}
                </Badge>
              </Group>
              <Group>
                <Text fw={500}>Created:</Text>
                <Text>{formatRelativeDate(notification.created_at)}</Text>
              </Group>
              {notification.session_id && (
                <Group>
                  <Text fw={500}>Session ID:</Text>
                  <Text style={{ fontFamily: 'monospace' }}>{notification.session_id}</Text>
                </Group>
              )}
            </Stack>
          </Paper>

          {/* Message */}
          <Paper withBorder p="md">
            <Title order={4} mb="md">Message</Title>
            <Text>{notification.message}</Text>
          </Paper>

          {/* Progress */}
          {hasProgress && (
            <Paper withBorder p="md">
              <Title order={4} mb="md">Progress</Title>
              <Progress 
                value={notification.progress} 
                size="md" 
                color={notification.progress === 100 ? 'green' : 'blue'}
                label={`${Math.round(notification.progress)}%`}
              />
            </Paper>
          )}

          {/* Metadata */}
          {notification.metadata && Object.keys(notification.metadata).length > 0 && (
            <Paper withBorder p="md">
              <Title order={4} mb="md">Additional Information</Title>
              <Code block>
                {JSON.stringify(notification.metadata, null, 2)}
              </Code>
            </Paper>
          )}

          {/* Timestamps */}
          <Paper withBorder p="md">
            <Title order={4} mb="md">Timestamps</Title>
            <Stack gap="xs">
              <Group>
                <Text fw={500}>Created:</Text>
                <Text>{(() => {
                  const date = new Date(notification.created_at);
                  return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                })()}</Text>
              </Group>
              <Group>
                <Text fw={500}>Updated:</Text>
                <Text>{(() => {
                  const date = new Date(notification.updated_at);
                  return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                })()}</Text>
              </Group>
              {notification.read_at && (
                <Group>
                  <Text fw={500}>Read:</Text>
                  <Text>{(() => {
                    const date = new Date(notification.read_at);
                    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                  })()}</Text>
                </Group>
              )}
              {notification.dismissed_at && (
                <Group>
                  <Text fw={500}>Dismissed:</Text>
                  <Text>{(() => {
                    const date = new Date(notification.dismissed_at);
                    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                  })()}</Text>
                </Group>
              )}
              {notification.expires_at && (
                <Group>
                  <Text fw={500}>Expires:</Text>
                  <Text>{(() => {
                    const date = new Date(notification.expires_at);
                    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                  })()}</Text>
                </Group>
              )}
            </Stack>
          </Paper>
        </Stack>
      </Modal>
    </>
  );
}
