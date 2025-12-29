import { useChangePassword, useGetCurrentUser, useUpdateCurrentUser } from '@/api/resources/users';
import {
  Badge,
  Button,
  Card,
  Divider,
  Group,
  LoadingOverlay,
  Modal,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import React, { useState } from 'react';

export default function UserProfilePage() {
  const [changePasswordModalOpen, setChangePasswordModalOpen] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const { data: user, isLoading, refetch } = useGetCurrentUser();
  const updateProfileMutation = useUpdateCurrentUser();
  const changePasswordMutation = useChangePassword();

  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  React.useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name,
        email: user.email,
      });
    }
  }, [user]);

  const handleUpdateProfile = async () => {
    try {
      const updates: any = {};
      if (profileData.name !== user?.name) updates.name = profileData.name;
      if (profileData.email !== user?.email) updates.email = profileData.email;

      if (Object.keys(updates).length === 0) {
        notifications.show({
          title: 'No Changes',
          message: 'No changes to save',
          color: 'blue',
        });
        return;
      }

      await updateProfileMutation.mutateAsync(updates);
      notifications.show({
        title: 'Success',
        message: 'Profile updated successfully',
        color: 'green',
      });
      refetch();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update profile',
        color: 'red',
      });
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      notifications.show({
        title: 'Error',
        message: 'New passwords do not match',
        color: 'red',
      });
      return;
    }

    if (passwordData.new_password.length < 8) {
      notifications.show({
        title: 'Error',
        message: 'Password must be at least 8 characters long',
        color: 'red',
      });
      return;
    }

    try {
      await changePasswordMutation.mutateAsync({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      notifications.show({
        title: 'Success',
        message: 'Password changed successfully',
        color: 'green',
      });
      setChangePasswordModalOpen(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to change password',
        color: 'red',
      });
    }
  };

  if (isLoading) {
    return (
      <Card>
        <LoadingOverlay visible={true} />
      </Card>
    );
  }

  if (!user) {
    return (
      <Card>
        <Text c="red">Failed to load user profile</Text>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <Title order={3} mb="md">My Profile</Title>

        <Stack gap="lg">
          {/* Profile Information */}
          <div>
            <Title order={4} mb="sm">Profile Information</Title>
            <Stack gap="md">
              <TextInput
                label="Username"
                value={user.username}
                disabled
                description="Username cannot be changed"
              />
              <TextInput
                label="Full Name"
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                placeholder="Enter your full name"
              />
              <TextInput
                label="Email"
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                placeholder="Enter your email"
              />
            </Stack>
            <Group mt="md">
              <Button
                onClick={handleUpdateProfile}
                loading={updateProfileMutation.isPending}
              >
                Update Profile
              </Button>
            </Group>
          </div>

          <Divider />

          {/* Account Information */}
          <div>
            <Title order={4} mb="sm">Account Information</Title>
            <Stack gap="sm">
              <Group>
                <Text size="sm" fw={500}>Account Status:</Text>
                <Badge color={user.is_active ? 'green' : 'red'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </Group>
              <Group>
                <Text size="sm" fw={500}>Member Since:</Text>
                <Text size="sm">{new Date(user.created_at).toLocaleDateString()}</Text>
              </Group>
              <Group>
                <Text size="sm" fw={500}>Last Login:</Text>
                <Text size="sm">
                  {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                </Text>
              </Group>
              <Group>
                <Text size="sm" fw={500}>Roles:</Text>
                <Group gap="xs">
                  {user.roles.map((role) => (
                    <Badge key={role} variant="light" color={role === 'admin' ? 'red' : 'blue'}>
                      {role}
                    </Badge>
                  ))}
                </Group>
              </Group>
            </Stack>
          </div>

          <Divider />

          {/* Security */}
          <div>
            <Title order={4} mb="sm">Security</Title>
            <Button
              variant="outline"
              onClick={() => setChangePasswordModalOpen(true)}
            >
              Change Password
            </Button>
          </div>
        </Stack>
      </Card>

      <Modal
        opened={changePasswordModalOpen}
        onClose={() => setChangePasswordModalOpen(false)}
        title="Change Password"
        centered
      >
        <Stack>
          <PasswordInput
            label="Current Password"
            value={passwordData.current_password}
            onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
            placeholder="Enter your current password"
            required
          />
          <PasswordInput
            label="New Password"
            value={passwordData.new_password}
            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
            placeholder="Enter your new password"
            required
          />
          <PasswordInput
            label="Confirm New Password"
            value={passwordData.confirm_password}
            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
            placeholder="Confirm your new password"
            required
          />
          <Group justify="flex-end">
            <Button variant="light" onClick={() => setChangePasswordModalOpen(false)}>
              Cancel
            </Button>
            <Button
              loading={changePasswordMutation.isPending}
              onClick={handleChangePassword}
            >
              Change Password
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
