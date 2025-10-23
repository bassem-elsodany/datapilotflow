import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '../helpers';
import { apiEndpoints } from '../../config';

// Role Schema
export const RoleSchema = z.object({
  id: z.string().nullable(),
  name: z.string(),
  description: z.string().nullable(),
  permissions: z.array(z.string()),
  is_system_role: z.boolean(),
  created_at: z.string().nullable(),
  updated_at: z.string().nullable(),
});

export type Role = z.infer<typeof RoleSchema>;

// Role List Schema
export const RoleListSchema = z.object({
  roles: z.array(RoleSchema),
  total_count: z.number(),
});

export type RoleList = z.infer<typeof RoleListSchema>;

// Permission Schema
export const PermissionSchema = z.object({
  name: z.string(),
  description: z.string(),
  category: z.string(),
});

export type Permission = z.infer<typeof PermissionSchema>;

// Permissions Response Schema
export const PermissionsResponseSchema = z.object({
  permissions: z.array(PermissionSchema),
  total_count: z.number(),
});

export type PermissionsResponse = z.infer<typeof PermissionsResponseSchema>;

// Create Role Request Schema
export const CreateRoleRequestSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  permissions: z.array(z.string()),
});

export type CreateRoleRequest = z.infer<typeof CreateRoleRequestSchema>;

// Update Role Request Schema
export const UpdateRoleRequestSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  permissions: z.array(z.string()).optional(),
});

export type UpdateRoleRequest = z.infer<typeof UpdateRoleRequestSchema>;

// Assign Role Request Schema
export const AssignRoleRequestSchema = z.object({
  user_id: z.string(),
  role_name: z.string(),
});

export type AssignRoleRequest = z.infer<typeof AssignRoleRequestSchema>;

// Remove Role Request Schema
export const RemoveRoleRequestSchema = z.object({
  user_id: z.string(),
  role_name: z.string(),
});

export type RemoveRoleRequest = z.infer<typeof RemoveRoleRequestSchema>;

// User Roles Response Schema
export const UserRolesResponseSchema = z.object({
  user_id: z.string(),
  username: z.string(),
  roles: z.array(z.string()),
  permissions: z.array(z.string()),
});

export type UserRolesResponse = z.infer<typeof UserRolesResponseSchema>;

// API Hooks

// List all roles (admin only)
export const useGetRoles = createGetQueryHook({
  endpoint: apiEndpoints.roles.list,
  responseSchema: RoleListSchema,
  rQueryParams: { queryKey: ['roles'] },
});

// Get role by ID (admin only)
export const useGetRole = (roleId: string) => createGetQueryHook({
  endpoint: apiEndpoints.roles.role(roleId),
  responseSchema: RoleSchema,
  rQueryParams: { queryKey: ['roles', roleId] },
})();

// Create new role (admin only)
export const useCreateRole = createPostMutationHook({
  endpoint: apiEndpoints.roles.create,
  bodySchema: CreateRoleRequestSchema,
  responseSchema: RoleSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  },
});

// Update role by ID (admin only)
export const useUpdateRole = createPutMutationHook({
  endpoint: apiEndpoints.roles.role(':roleId'),
  bodySchema: UpdateRoleRequestSchema,
  responseSchema: RoleSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  },
});

// Delete role by ID (admin only)
export const useDeleteRole = createDeleteMutationHook({
  endpoint: apiEndpoints.roles.role(':roleId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  },
});

// List all permissions (admin only)
export const useGetPermissions = createGetQueryHook({
  endpoint: apiEndpoints.roles.permissions,
  responseSchema: PermissionsResponseSchema,
  rQueryParams: { queryKey: ['permissions'] },
});

// Assign role to user (admin only)
export const useAssignRole = createPostMutationHook({
  endpoint: apiEndpoints.roles.assign,
  bodySchema: AssignRoleRequestSchema,
  responseSchema: UserRolesResponseSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  },
});

// Remove role from user (admin only)
export const useRemoveRole = createPostMutationHook({
  endpoint: apiEndpoints.roles.remove,
  bodySchema: RemoveRoleRequestSchema,
  responseSchema: UserRolesResponseSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  },
});

// Get user roles and permissions (admin only)
export const useGetUserRoles = (userId: string) => createGetQueryHook({
  endpoint: apiEndpoints.roles.userRoles(userId),
  responseSchema: UserRolesResponseSchema,
  rQueryParams: { queryKey: ['user-roles', userId] },
})();
