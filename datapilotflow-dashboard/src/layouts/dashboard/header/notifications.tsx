import React from 'react';
import { ActionIcon, Drawer, Group, Stack, Text, Button, ScrollArea, Tooltip, Badge, Indicator } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconBell } from '@tabler/icons-react';
import { useNotifications } from '@/hooks';
import { Notification } from './notification';
import classes from './notification.module.css';

interface NotificationsProps {
  [key: string]: any;
}

export function Notifications(props: NotificationsProps) {
  const [opened, { open, close }] = useDisclosure(false);
  const { 
    notifications, 
    unreadCount, 
    isLoading, 
    markAsRead, 
    dismiss, 
    delete: deleteNotification, 
    markAllAsRead,
    hasNewNotifications: hasNewNotificationsState,
    isWebSocketConnected
  } = useNotifications();

  const hasNewNotifications = unreadCount > 0 || hasNewNotificationsState;

  return (
    <>
      <Tooltip label={`Notifications ${isWebSocketConnected ? '(Real-time)' : '(Polling)'}`}>
        <Group gap="xs">
          <Indicator
            inline
            withBorder
            offset={6}
            size={12}
            processing={hasNewNotifications}
            disabled={!hasNewNotifications}
            label={unreadCount > 0 ? unreadCount : undefined}
            className={`${classes.notificationBadge} ${hasNewNotifications ? classes.hasNew : ''}`}
          >
            <ActionIcon 
              variant="transparent" 
              c="inherit" 
              onClick={open} 
              className={`${classes.notificationIcon} ${hasNewNotifications ? classes.hasNew : ''}`}
              {...props}
            >
              <IconBell size="100%" />
            </ActionIcon>
          </Indicator>
        </Group>
      </Tooltip>

      <Drawer.Root position="right" opened={opened} onClose={close} size="420px">
        <Drawer.Overlay />
        <Drawer.Content pos="relative">
          <Drawer.Header>
            <Group justify="space-between" align="center" style={{ flex: 1 }}>
              <Group gap="xs">
                <Drawer.Title>Notifications</Drawer.Title>
              </Group>
              <Group gap="xs">
                {unreadCount > 0 && (
                  <Button 
                    size="compact-sm" 
                    variant="subtle"
                    onClick={markAllAsRead}
                  >
                    Mark all read
                  </Button>
                )}
                <Button size="compact-sm" variant="subtle">
                  View all
                </Button>
              </Group>
            </Group>
            <Drawer.CloseButton />
          </Drawer.Header>

          <Drawer.Body p="0">
            <ScrollArea h="calc(100vh - 120px)">
              {isLoading ? (
                <Stack p="md" align="center">
                  <Text size="sm" c="dimmed">Loading notifications...</Text>
                </Stack>
              ) : notifications.length === 0 ? (
                <Stack p="md" align="center">
                  <Text size="sm" c="dimmed">No notifications</Text>
                </Stack>
              ) : (
                <Stack gap={0}>
                  {notifications.map((notification) => (
                    <Notification
                      key={notification.notification_id}
                      notification={notification}
                      onMarkAsRead={markAsRead}
                      onDismiss={dismiss}
                      onDelete={deleteNotification}
                    />
                  ))}
                </Stack>
              )}
            </ScrollArea>
          </Drawer.Body>
        </Drawer.Content>
      </Drawer.Root>
    </>
  );
}
