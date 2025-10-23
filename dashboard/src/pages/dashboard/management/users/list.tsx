import { useDeleteUser, useGetUsers, UserProfile } from '@/api/resources/users';
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

export default function UserListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserProfile | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: usersData, isLoading, refetch } = useGetUsers();
  const deleteUserMutation = useDeleteUser();

  const handleDeleteUser = async () => {
    if (!userToDelete?.id) return;

    try {
      await deleteUserMutation.mutateAsync({ userId: userToDelete.id });
      notifications.show({
        title: 'Success',
        message: 'User deleted successfully',
        color: 'green',
      });
      setDeleteModalOpen(false);
      setUserToDelete(null);
      refetch();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to delete user',
        color: 'red',
      });
    }
  };

  const openDeleteModal = (user: UserProfile) => {
    setUserToDelete(user);
    setDeleteModalOpen(true);
  };

  const filteredUsers = usersData?.users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const itemsPerPage = 10;
  const totalPages = Math.ceil((filteredUsers.length || 0) / itemsPerPage);
  const paginatedUsers = filteredUsers.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  const rows = paginatedUsers.map((user) => (
    <Table.Tr key={user.id}>
      <Table.Td>
        <div>
          <Text fw={500}>{user.name}</Text>
          <Text size="sm" c="dimmed">@{user.username}</Text>
        </div>
      </Table.Td>
      <Table.Td>{user.email}</Table.Td>
      <Table.Td>
        <Group gap="xs">
          {user.roles.map((role) => (
            <Badge key={role} variant="light" color={role === 'admin' ? 'red' : 'blue'}>
              {role}
            </Badge>
          ))}
        </Group>
      </Table.Td>
      <Table.Td>
        <Badge color={user.is_active ? 'green' : 'red'}>
          {user.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{(() => {
          const date = new Date(user.created_at);
          return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
        })()}</Text>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => navigate(paths.dashboard.management.users.edit(user.id!))}
          >
            <IconEye size={16} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => navigate(paths.dashboard.management.users.edit(user.id!))}
          >
            <IconEdit size={16} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color="red"
            onClick={() => openDeleteModal(user)}
          >
            <IconTrash size={16} />
          </ActionIcon>
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <>
      <Card>
        <Group justify="space-between" mb="md">
          <div>
            <Title order={3}>User Management</Title>
            <Text c="dimmed">Manage system users and their roles</Text>
          </div>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => navigate(paths.dashboard.management.users.create)}
          >
            Add User
          </Button>
        </Group>

        <Group mb="md">
          <TextInput
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1 }}
          />
        </Group>

        <LoadingOverlay visible={isLoading} />

        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>User</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Roles</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.length > 0 ? (
              rows
            ) : (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center" c="dimmed" py="xl">
                    {searchTerm ? 'No users found matching your search' : 'No users found'}
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
        title="Delete User"
        centered
      >
        <Stack>
          <Text>
            Are you sure you want to delete user <strong>{userToDelete?.name}</strong>?
            This action cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="light" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              color="red"
              loading={deleteUserMutation.isPending}
              onClick={handleDeleteUser}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
