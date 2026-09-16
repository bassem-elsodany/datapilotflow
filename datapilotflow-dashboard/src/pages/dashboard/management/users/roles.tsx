import { Role, useDeleteRole, useGetPermissions, useGetRoles } from '@/api/resources/roles';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Group,
  LoadingOverlay,
  Modal,
  Pagination,
  Stack,
  Table,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconEdit, IconEye, IconPlus, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function RolesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState<Role | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: rolesData, isLoading, refetch } = useGetRoles();
  const { data: permissionsData } = useGetPermissions();
  const deleteRoleMutation = useDeleteRole();

  const handleDeleteRole = async () => {
    if (!roleToDelete?.id) return;

    try {
      await deleteRoleMutation.mutateAsync({ model: undefined, route: { roleId: roleToDelete.id } });
      notifications.show({
        title: 'Success',
        message: 'Role deleted successfully',
        color: 'green',
      });
      setDeleteModalOpen(false);
      setRoleToDelete(null);
      refetch();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to delete role',
        color: 'red',
      });
    }
  };

  const openDeleteModal = (role: Role) => {
    setRoleToDelete(role);
    setDeleteModalOpen(true);
  };

  const filteredRoles = rolesData?.roles.filter(role =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (role.description && role.description.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

  const itemsPerPage = 10;
  const totalPages = Math.ceil((filteredRoles.length || 0) / itemsPerPage);
  const paginatedRoles = filteredRoles.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  const rows = paginatedRoles.map((role) => (
    <Table.Tr key={role.id}>
      <Table.Td>
        <div>
          <Text fw={500}>{role.name}</Text>
          {role.description && (
            <Text size="sm" c="dimmed">{role.description}</Text>
          )}
        </div>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          {role.permissions.slice(0, 3).map((permission) => (
            <Badge key={permission} variant="light" size="sm">
              {permission}
            </Badge>
          ))}
          {role.permissions.length > 3 && (
            <Badge variant="light" size="sm">
              +{role.permissions.length - 3} more
            </Badge>
          )}
        </Group>
      </Table.Td>
      <Table.Td>
        <Badge color={role.is_system_role ? 'red' : 'blue'}>
          {role.is_system_role ? 'System' : 'Custom'}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Text size="sm">
          {role.created_at ? new Date(role.created_at).toLocaleDateString() : 'N/A'}
        </Text>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => navigate(paths.dashboard.management.users.roleEdit(role.id!))}
          >
            <IconEye size={16} />
          </ActionIcon>
          {!role.is_system_role && (
            <>
              <ActionIcon
                variant="subtle"
                color="blue"
                onClick={() => navigate(paths.dashboard.management.users.roleEdit(role.id!))}
              >
                <IconEdit size={16} />
              </ActionIcon>
              <ActionIcon
                variant="subtle"
                color="red"
                onClick={() => openDeleteModal(role)}
              >
                <IconTrash size={16} />
              </ActionIcon>
            </>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <>
      <Card>
        <Group justify="space-between" mb="md">
          <div>
            <Title order={3}>Role Management</Title>
            <Text c="dimmed">Manage user roles and permissions</Text>
          </div>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => navigate(paths.dashboard.management.users.roleCreate)}
          >
            Create Role
          </Button>
        </Group>

        <Group mb="md">
          <TextInput
            placeholder="Search roles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1 }}
          />
        </Group>

        <LoadingOverlay visible={isLoading} />

        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Role</Table.Th>
              <Table.Th>Permissions</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.length > 0 ? (
              rows
            ) : (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Text ta="center" c="dimmed" py="xl">
                    {searchTerm ? 'No roles found matching your search' : 'No roles found'}
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>

        {totalPages > 1 && (
          <Group justify="center" mt="md">
            <Pagination
              value={page}
              onChange={setPage}
              total={totalPages}
            />
          </Group>
        )}
      </Card>

      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Role"
        centered
      >
        <Stack>
          <Text>
            Are you sure you want to delete role <strong>{roleToDelete?.name}</strong>?
            This action cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="light" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              color="red"
              loading={deleteRoleMutation.isPending}
              onClick={handleDeleteRole}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
