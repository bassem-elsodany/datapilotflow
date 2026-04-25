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

  const availablePermissions = [
    // User management
    { value: 'user:manage', label: '👥 Users — Manage (create, update, delete users & roles)', group: 'User Management' },
    { value: 'user:read',   label: '👥 Users — Read (view users & role assignments)', group: 'User Management' },
    // Knowledge pipeline
    { value: 'knowledge:manage', label: '🗂️ Knowledge — Manage (sources, jobs, collections)', group: 'Knowledge Pipeline' },
    { value: 'knowledge:read',   label: '🗂️ Knowledge — Read (view sources, jobs, collections)', group: 'Knowledge Pipeline' },
    // Conversations
    { value: 'conversation:manage', label: '💬 Conversations — Manage (create & manage AI conversations)', group: 'Conversations' },
    { value: 'conversation:read',   label: '💬 Conversations — Read (view conversations)', group: 'Conversations' },
    // Tools & MCP
    { value: 'tools:manage', label: '🔧 Tools — Manage (add, edit, delete tools & MCP servers)', group: 'Tools & MCP' },
    { value: 'tools:read',   label: '🔧 Tools — Read (view tools & MCP servers)', group: 'Tools & MCP' },
    // Model providers
    { value: 'models:manage', label: '🤖 Models — Manage (add, edit, delete model providers)', group: 'Model Providers' },
    { value: 'models:read',   label: '🤖 Models — Read (view model providers)', group: 'Model Providers' },
    // Analytics
    { value: 'analytics:manage', label: '📊 Analytics — Manage', group: 'Analytics' },
    { value: 'analytics:read',   label: '📊 Analytics — Read (view stats & reports)', group: 'Analytics' },
    // System
    { value: 'system:manage', label: '⚙️ System — Manage (system-level configuration)', group: 'System' },
    { value: 'system:read',   label: '⚙️ System — Read (view system config & health)', group: 'System' },
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
            description="Select the permissions this role grants. Grouped by platform area."
            placeholder="Select permissions"
            data={availablePermissions}
            value={formData.permissions}
            onChange={(value) => setFormData({ ...formData, permissions: value })}
            searchable
            clearable
            required
            maxDropdownHeight={320}
          />

          <Group gap="xs">
            <Text size="sm" fw={500}>Current Permissions:</Text>
            {formData.permissions.length > 0 ? (
              formData.permissions.map((permission) => {
                const colorMap: Record<string, string> = {
                  'user': 'grape', 'knowledge': 'blue', 'conversation': 'cyan',
                  'tools': 'orange', 'models': 'violet', 'analytics': 'teal', 'system': 'gray',
                };
                const category = permission.split(':')[0];
                return (
                  <Badge key={permission} variant="light" color={colorMap[category] ?? 'blue'}>
                    {permission}
                  </Badge>
                );
              })
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
