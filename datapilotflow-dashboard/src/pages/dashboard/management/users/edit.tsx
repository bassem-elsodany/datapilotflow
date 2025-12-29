import { useGetRoles } from '@/api/resources/roles';
import { useGetUser, useUpdateUser } from '@/api/resources/users';
import { paths } from '@/routes/paths';
import {
  Alert,
  Button,
  Card,
  Group,
  LoadingOverlay,
  Select,
  Stack,
  Switch,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconArrowLeft, IconDeviceFloppy } from '@tabler/icons-react';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function UserEditPage() {
  const navigate = useNavigate();
  const { userId } = useParams<{ userId: string }>();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    is_active: true,
    role_ids: [] as string[],
  });

  const { data: user, isLoading: userLoading, error: userError } = useGetUser(userId!);
  const { data: rolesData, isLoading: rolesLoading } = useGetRoles();
  const updateUserMutation = useUpdateUser();

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name,
        email: user.email,
        is_active: user.is_active,
        role_ids: user.roles.map(role => {
          // Find role ID by name
          const roleObj = rolesData?.roles.find(r => r.name === role);
          return roleObj?.id || '';
        }).filter(id => id !== ''),
      });
    }
  }, [user, rolesData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!userId) return;

    try {
      await updateUserMutation.mutateAsync({
        variables: {
          name: formData.name,
          email: formData.email,
          is_active: formData.is_active,
          roles: formData.role_ids,
        },
        route: { userId },
      });

      notifications.show({
        title: 'Success',
        message: 'User updated successfully',
        color: 'green',
      });

      navigate(paths.dashboard.management.users.list);
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update user',
        color: 'red',
      });
    }
  };

  const handleBack = () => {
    navigate(paths.dashboard.management.users.list);
  };

  if (userLoading || rolesLoading) {
    return (
      <Card>
        <LoadingOverlay visible />
      </Card>
    );
  }

  if (userError || !user) {
    return (
      <Card>
        <Alert title="Error" color="red">
          User not found or error loading user data.
        </Alert>
        <Button onClick={handleBack} mt="md" leftSection={<IconArrowLeft size={16} />}>
          Back to Users
        </Button>
      </Card>
    );
  }

  const roleOptions = rolesData?.roles
    .filter(role => role.id !== null)
    .map(role => ({
      value: role.id!,
      label: role.name,
    })) || [];

  return (
    <Card>
      <Group justify="space-between" mb="lg">
        <Title order={3}>Edit User</Title>
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          onClick={handleBack}
        >
          Back to Users
        </Button>
      </Group>

      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />

          <TextInput
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />

          <Select
            label="Roles"
            placeholder="Select roles"
            data={roleOptions}
            value={formData.role_ids[0] || null}
            onChange={(value) => setFormData({ ...formData, role_ids: value ? [value] : [] })}
            searchable
            clearable
          />

          <Switch
            label="Active"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.currentTarget.checked })}
          />

          <Group justify="flex-end" mt="lg">
            <Button
              variant="subtle"
              onClick={handleBack}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              leftSection={<IconDeviceFloppy size={16} />}
              loading={updateUserMutation.isPending}
            >
              Save Changes
            </Button>
          </Group>
        </Stack>
      </form>
    </Card>
  );
}
