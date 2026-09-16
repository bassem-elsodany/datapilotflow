import {
  PiGearSixDuotone,
  PiSignOut,
  PiUserSwitchDuotone,
} from 'react-icons/pi';
import { Avatar, AvatarProps, ElementProps, Menu, Modal, Text, Group, Stack, Divider, Skeleton } from '@mantine/core';
import { useAuth, useGetAccountInfo, useLogout } from '@/hooks';
import { useState } from 'react';

type CurrentUserProps = Omit<AvatarProps, 'src' | 'alt'> & ElementProps<'div', keyof AvatarProps>;

export function CurrentUser(props: CurrentUserProps) {
  const { mutate: logout } = useLogout();
  const { setIsAuthenticated } = useAuth();
  // AuthProvider already blocks rendering until auth is initialized,
  // so we can always fetch without extra guards.
  const { data: user, isLoading: userLoading } = useGetAccountInfo();
  const [settingsModalOpened, setSettingsModalOpened] = useState(false);

  const handleLogout = () => {
    const token = localStorage.getItem('jwt_token') ?? '';
    logout({ variables: { token } });
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
              {userLoading ? (
                <>
                  <Skeleton height={20} width={160} mb={6} />
                  <Skeleton height={14} width={100} />
                </>
              ) : (
                <>
                  <Text size="lg" fw={600}>
                    {user?.name || 'User'}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {user?.username || user?.email || 'No username'}
                  </Text>
                </>
              )}
            </div>
          </Group>

          <Divider />

          <Stack gap="xs">
            <Text size="sm" fw={500} c="dimmed">Account Information</Text>

            {userLoading ? (
              <>
                <Skeleton height={16} />
                <Skeleton height={16} />
                <Skeleton height={16} />
                <Skeleton height={16} />
              </>
            ) : (
              <>
                <Group justify="space-between">
                  <Text size="sm">Full Name:</Text>
                  <Text size="sm" fw={500}>{user?.name || '—'}</Text>
                </Group>

                <Group justify="space-between">
                  <Text size="sm">Username:</Text>
                  <Text size="sm" fw={500}>{user?.username || '—'}</Text>
                </Group>

                <Group justify="space-between">
                  <Text size="sm">Email:</Text>
                  <Text size="sm" fw={500}>{user?.email || '—'}</Text>
                </Group>

                {user?.roles && user.roles.length > 0 && (
                  <Group justify="space-between" align="flex-start">
                    <Text size="sm">Roles:</Text>
                    <Group gap={4} justify="flex-end" style={{ flex: 1 }}>
                      {user.roles.map((role) => (
                        <Text key={role} size="sm" fw={500} c="blue">
                          {role}
                        </Text>
                      ))}
                    </Group>
                  </Group>
                )}

                {user?.created_at && (
                  <Group justify="space-between">
                    <Text size="sm">Member since:</Text>
                    <Text size="sm" fw={500}>
                      {(() => {
                        const date = new Date(user.created_at!);
                        return isNaN(date.getTime()) ? '—' : date.toLocaleDateString();
                      })()}
                    </Text>
                  </Group>
                )}

                {user?.permissions && user.permissions.length > 0 && (
                  <Group justify="space-between">
                    <Text size="sm">Permissions:</Text>
                    <Text size="sm" fw={500} c="green">{user.permissions.length} granted</Text>
                  </Group>
                )}
              </>
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
