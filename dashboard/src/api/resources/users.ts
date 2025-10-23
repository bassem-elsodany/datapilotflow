import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '../helpers';
import { apiEndpoints } from '../../config';

// User Profile Schema
export const UserProfileSchema = z.object({
  id: z.string().nullable(),
  username: z.string(),
  email: z.string().email(),
  name: z.string(),
  roles: z.array(z.string()),
  created_at: z.string(),
  last_login: z.string().nullable(),
  is_active: z.boolean(),
});

export type UserProfile = z.infer<typeof UserProfileSchema>;

// User List Schema
export const UserListSchema = z.object({
  users: z.array(UserProfileSchema),
  total_count: z.number(),
});

export type UserList = z.infer<typeof UserListSchema>;

// Update Profile Request Schema
export const UpdateProfileRequestSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
});

export type UpdateProfileRequest = z.infer<typeof UpdateProfileRequestSchema>;

// Change Password Request Schema
export const ChangePasswordRequestSchema = z.object({
  current_password: z.string(),
  new_password: z.string(),
});

export type ChangePasswordRequest = z.infer<typeof ChangePasswordRequestSchema>;

// Create User Request Schema
export const CreateUserRequestSchema = z.object({
  username: z.string(),
  email: z.string().email(),
  password: z.string(),
  name: z.string(),
  roles: z.array(z.string()).optional(),
});

export type CreateUserRequest = z.infer<typeof CreateUserRequestSchema>;

// Update User Request Schema
export const UpdateUserRequestSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  roles: z.array(z.string()).optional(),
  is_active: z.boolean().optional(),
});

export type UpdateUserRequest = z.infer<typeof UpdateUserRequestSchema>;

// API Hooks

// Get current user profile
export const useGetCurrentUser = createGetQueryHook({
  endpoint: apiEndpoints.users.me,
  responseSchema: UserProfileSchema,
  rQueryParams: { queryKey: ['users', 'me'] },
});

// Update current user profile
export const useUpdateCurrentUser = createPutMutationHook({
  endpoint: apiEndpoints.users.profile,
  bodySchema: UpdateProfileRequestSchema,
  responseSchema: UserProfileSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
    },
  },
});

// Change password
export const useChangePassword = createPostMutationHook({
  endpoint: apiEndpoints.users.changePassword,
  bodySchema: ChangePasswordRequestSchema,
  responseSchema: z.object({ message: z.string() }),
});

// Delete current user account
export const useDeleteCurrentUser = createDeleteMutationHook({
  endpoint: apiEndpoints.users.deleteAccount,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
    },
  },
});

// List all users (admin only)
export const useGetUsers = createGetQueryHook({
  endpoint: apiEndpoints.users.list,
  responseSchema: UserListSchema,
  rQueryParams: { queryKey: ['users'] },
});

// Create new user (admin only)
export const useCreateUser = createPostMutationHook({
  endpoint: apiEndpoints.users.create,
  bodySchema: CreateUserRequestSchema,
  responseSchema: UserProfileSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  },
});

// Get user by ID (admin only)
export const useGetUser = (userId: string) => createGetQueryHook({
  endpoint: apiEndpoints.users.user(userId),
  responseSchema: UserProfileSchema,
  rQueryParams: { queryKey: ['users', userId] },
})();

// Update user by ID (admin only)
export const useUpdateUser = createPutMutationHook({
  endpoint: apiEndpoints.users.user(':userId'),
  bodySchema: UpdateUserRequestSchema,
  responseSchema: UserProfileSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  },
});

// Delete user by ID (admin only)
export const useDeleteUser = createDeleteMutationHook({
  endpoint: apiEndpoints.users.user(':userId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  },
});
