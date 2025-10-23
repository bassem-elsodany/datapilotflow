import { useGetRole, useGetRoles, useUpdateRole } from '@/api/resources/roles';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  LoadingOverlay,
  MultiSelect,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconArrowLeft, IconDeviceFloppy } from '@tabler/icons-react';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function RoleEditPage() {
  const navigate = useNavigate();
  const { roleId } = useParams<{ roleId: string }>();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as string[],
  });

  const { data: role, isLoading: roleLoading, error: roleError } = useGetRole(roleId!);
  const { data: rolesData, isLoading: rolesLoading } = useGetRoles();
  const updateRoleMutation = useUpdateRole();

  useEffect(() => {
    if (role) {
      setFormData({
        name: role.name,
        description: role.description || '',
        permissions: role.permissions,
      });
    }
  }, [role]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!roleId) return;

    try {
      await updateRoleMutation.mutateAsync({
        variables: {
          name: formData.name,
          description: formData.description,
          permissions: formData.permissions,
        },
        route: { roleId: roleId },
      });

      notifications.show({
        title: 'Success',
        message: 'Role updated successfully',
        color: 'green',
      });

      navigate(paths.dashboard.management.users.roles);
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update role',
        color: 'red',
      });
    }
  };

  const handleBack = () => {
    navigate(paths.dashboard.management.users.roles);
  };

  if (roleLoading || rolesLoading) {
    return (
      <Card>
        <LoadingOverlay visible />
      </Card>
    );
  }

  if (roleError || !role) {
    return (
      <Card>
        <Alert title="Error" color="red">
          Role not found or error loading role data.
        </Alert>
        <Button onClick={handleBack} mt="md" leftSection={<IconArrowLeft size={16} />}>
          Back to Roles
        </Button>
      </Card>
    );
  }

  // Define available permissions
  const availablePermissions = [
    { value: 'user:manage', label: 'Manage Users' },
    { value: 'user:read', label: 'Read Users' },
    { value: 'interview:manage', label: 'Manage Interviews' },
    { value: 'interview:read', label: 'Read Interviews' },
    { value: 'knowledge:manage', label: 'Manage Knowledge' },
    { value: 'knowledge:read', label: 'Read Knowledge' },
    { value: 'analytics:manage', label: 'Manage Analytics' },
    { value: 'analytics:read', label: 'Read Analytics' },
    { value: 'system:manage', label: 'Manage System' },
    { value: 'system:read', label: 'Read System' },
  ];

  return (
    <Card>
      <Group justify="space-between" mb="lg">
        <Title order={3}>Edit Role: {role.name}</Title>
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          onClick={handleBack}
        >
          Back to Roles
        </Button>
      </Group>

      {role.is_system_role && (
        <Alert title="System Role" color="blue" mb="md">
          This is a system role and some properties may be restricted from modification.
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="Role Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            disabled={role.is_system_role}
          />

          <Textarea
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter role description"
            rows={3}
          />

          <MultiSelect
            label="Permissions"
            placeholder="Select permissions"
            data={availablePermissions}
            value={formData.permissions}
            onChange={(value) => setFormData({ ...formData, permissions: value })}
            searchable
            clearable
            required
          />

          <Group gap="xs">
            <Text size="sm" fw={500}>Current Permissions:</Text>
            {formData.permissions.length > 0 ? (
              formData.permissions.map((permission) => (
                <Badge key={permission} variant="light" color="blue">
                  {permission}
                </Badge>
              ))
            ) : (
              <Text size="sm" c="dimmed">No permissions selected</Text>
            )}
          </Group>

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
              loading={updateRoleMutation.isPending}
            >
              Save Changes
            </Button>
          </Group>
        </Stack>
      </form>
    </Card>
  );
}
