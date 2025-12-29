import { z } from 'zod';
import { notifications } from '@mantine/notifications';
import { removeClientAccessToken, setClientAccessToken } from '@/api/axios';
import { LoginRequestSchema, LoginResponseSchema } from '@/api/dtos';
import { createPostMutationHook, createGetQueryHook } from '@/api/helpers';
import { apiEndpoints } from '@/config';

export const useLogin = createPostMutationHook({
  endpoint: apiEndpoints.auth.login,
  bodySchema: LoginRequestSchema,
  responseSchema: LoginResponseSchema,
  rMutationParams: {
    onSuccess: (data) => {
      setClientAccessToken(data.access_token);
      notifications.show({ title: 'Welcome to dataPilotFlow!', message: 'You have successfully logged in' });
    },
    onError: (error: any) => {
      console.error('❌ Login failed:', error);
      const message = error.message || error.detail || 'Login failed. Please try again.';
      notifications.show({ message, color: 'red' });
    },
  },
});

// Register new user
export const useRegister = createPostMutationHook({
  endpoint: apiEndpoints.auth.register,
  bodySchema: z.object({
    username: z.string(),
    email: z.string().email(),
    password: z.string(),
    name: z.string(),
  }),
  responseSchema: LoginResponseSchema,
  rMutationParams: {
    onSuccess: (data) => {
      setClientAccessToken(data.access_token);
      notifications.show({ title: 'Welcome to dataPilotFlow!', message: 'Your account has been created successfully' });
    },
    onError: (error: any) => {
      console.error('❌ Registration failed:', error);
      const message = error.message || error.detail || 'Registration failed. Please try again.';
      notifications.show({ message, color: 'red' });
    },
  },
});

// Logout with backend call
export const useLogout = createPostMutationHook({
  endpoint: apiEndpoints.auth.logout,
  bodySchema: z.object({
    token: z.string(),
  }),
  responseSchema: z.object({ message: z.string() }),
  rMutationParams: {
    onSuccess: () => {
      removeClientAccessToken();
      notifications.show({ title: 'Goodbye!', message: 'You have successfully logged out' });
      // Navigate to login page
      window.location.href = '/auth/login';
    },
    onError: (error) => {
      console.error('❌ Logout failed:', error);
      // Still remove token and redirect even if backend call fails
      removeClientAccessToken();
      window.location.href = '/auth/login';
    },
  },
});

// Refresh token
export const useRefreshToken = createPostMutationHook({
  endpoint: apiEndpoints.auth.refresh,
  bodySchema: z.object({}), // No body needed for refresh
  responseSchema: LoginResponseSchema,
  rMutationParams: {
    onSuccess: (data) => {
      setClientAccessToken(data.access_token);
    },
    onError: (error) => {
      console.error('❌ Token refresh failed:', error);
      // Redirect to login if refresh fails
      removeClientAccessToken();
      window.location.href = '/auth/login';
    },
  },
});

// Request password reset
export const useRequestPasswordReset = createPostMutationHook({
  endpoint: apiEndpoints.auth.passwordReset,
  bodySchema: z.object({
    email: z.string().email(),
  }),
  responseSchema: z.object({ message: z.string() }),
  rMutationParams: {
    onSuccess: () => {
      notifications.show({ title: 'Password Reset', message: 'If the email exists, a password reset link has been sent' });
    },
    onError: (error: any) => {
      console.error('❌ Password reset request failed:', error);
      const message = error.message || error.detail || 'Password reset request failed. Please try again.';
      notifications.show({ message, color: 'red' });
    },
  },
});

// Confirm password reset
export const useConfirmPasswordReset = createPostMutationHook({
  endpoint: apiEndpoints.auth.passwordResetConfirm,
  bodySchema: z.object({
    token: z.string(),
    new_password: z.string(),
  }),
  responseSchema: z.object({ message: z.string() }),
  rMutationParams: {
    onSuccess: () => {
      notifications.show({ title: 'Success', message: 'Password has been reset successfully' });
    },
    onError: (error: any) => {
      console.error('❌ Password reset confirmation failed:', error);
      const message = error.message || error.detail || 'Password reset confirmation failed. Please try again.';
      notifications.show({ message, color: 'red' });
    },
  },
});
