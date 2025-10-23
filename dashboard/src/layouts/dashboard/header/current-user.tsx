import {
  PiGearSixDuotone,
  PiSignOut,
  PiUserSwitchDuotone,
} from 'react-icons/pi';
import { Avatar, AvatarProps, ElementProps, Menu, Modal, Text, Group, Stack, Badge, Divider } from '@mantine/core';
import { useAuth, useGetAccountInfo, useLogout } from '@/hooks';
import { useState } from 'react';

type CurrentUserProps = Omit<AvatarProps, 'src' | 'alt'> & ElementProps<'div', keyof AvatarProps>;

export function CurrentUser(props: CurrentUserProps) {
  const { mutate: logout } = useLogout();
  const { setIsAuthenticated, isAuthenticated, isLoading } = useAuth(); // Add auth state checks
  const { data: user } = useGetAccountInfo({
    enabled: isAuthenticated && !isLoading // Only fetch when authenticated AND not loading
  });
  const [settingsModalOpened, setSettingsModalOpened] = useState(false);

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
  };

  const handleAccountSettings = () => {
    setSettingsModalOpened(true);
  };

  const getUserInitials = () => {
    if (!user?.name) return 'CU';
    return user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <>
      <Menu>
        <Menu.Target>
          <Avatar
            alt={user?.name ?? user?.username ?? 'Current user'}
            {...props}
            style={{ cursor: 'pointer', ...props.style }}
          >
            {getUserInitials()}
          </Avatar>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Label>Settings</Menu.Label>
          <Menu.Item leftSection={<PiGearSixDuotone size="1rem" />} onClick={handleAccountSettings}>
            Account settings
          </Menu.Item>
          <Menu.Item leftSection={<PiUserSwitchDuotone size="1rem" />}>Change account</Menu.Item>

          <Menu.Divider />

          <Menu.Item leftSection={<PiSignOut size="1rem" />} onClick={handleLogout}>
            Logout
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>

      <Modal
        opened={settingsModalOpened}
        onClose={() => setSettingsModalOpened(false)}
        title="Account Settings"
        size="md"
        centered
      >
        <Stack gap="md">
          <Group>
            <Avatar size="lg" radius="xl">
              {getUserInitials()}
            </Avatar>
            <div>
              <Text size="lg" fw={600}>
                {user?.name || 'User'}
              </Text>
              <Text size="sm" c="dimmed">
                {user?.username || user?.email || 'No username'}
              </Text>
            </div>
          </Group>

          <Divider />

          <Stack gap="xs">
            <Text size="sm" fw={500} c="dimmed">Account Information</Text>
            
            <Group justify="space-between">
              <Text size="sm">Full Name:</Text>
              <Text size="sm" fw={500}>{user?.name || 'Not provided'}</Text>
            </Group>

            <Group justify="space-between">
              <Text size="sm">Username:</Text>
              <Text size="sm" fw={500}>{user?.username || 'Not provided'}</Text>
            </Group>

            <Group justify="space-between">
              <Text size="sm">Email:</Text>
              <Text size="sm" fw={500}>{user?.email || 'Not provided'}</Text>
            </Group>

            {user?.role && (
              <Group justify="space-between">
                <Text size="sm">Role:</Text>
                <Badge variant="light" color="blue">
                  {user.role}
                </Badge>
              </Group>
            )}

            {user?.created_at && (
              <Group justify="space-between">
                <Text size="sm">Member since:</Text>
                <Text size="sm" fw={500}>
                  {(() => {
                    const date = new Date(user.created_at);
                    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
                  })()}
                </Text>
              </Group>
            )}
          </Stack>

          <Divider />

          <Text size="xs" c="dimmed" ta="center">
            For additional account changes, please contact your administrator.
          </Text>
        </Stack>
      </Modal>
    </>
  );
}
