import { apiEndpoints } from '@/config';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook } from '../helpers';

// ============================================================================
// CONFLUENCE CREDENTIALS SCHEMAS
// ============================================================================

export const ConfluenceCredentialSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  name: z.string(),
  cloud_url: z.string(),
  username_or_email: z.string(),
  created_at: z.string(),
  last_verified: z.string().nullable().optional(),
  is_active: z.boolean(),
});

export const ConfluenceCredentialCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  cloud_url: z.string().url('Invalid Confluence URL'),
  username_or_email: z.string().email('Invalid email or username'),
  api_token: z.string().min(1, 'API token is required'),
});

export const ConfluenceCredentialUpdateSchema = z.object({
  name: z.string().optional(),
  cloud_url: z.string().url('Invalid Confluence URL').optional(),
  username_or_email: z.string().email('Invalid email or username').optional(),
  api_token: z.string().optional(),
});

export const ConfluenceCredentialVerifyResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
});

export type ConfluenceCredential = z.infer<typeof ConfluenceCredentialSchema>;
export type ConfluenceCredentialCreate = z.infer<typeof ConfluenceCredentialCreateSchema>;
export type ConfluenceCredentialUpdate = z.infer<typeof ConfluenceCredentialUpdateSchema>;
export type ConfluenceCredentialVerifyResponse = z.infer<typeof ConfluenceCredentialVerifyResponseSchema>;

// ============================================================================
// CONFLUENCE CREDENTIALS HOOKS
// ============================================================================

/**
 * Hook to create a new Confluence credential
 */
export const useCreateConfluenceCredential = createPostMutationHook({
  endpoint: apiEndpoints.confluence.credentials,
  bodySchema: ConfluenceCredentialCreateSchema,
  responseSchema: ConfluenceCredentialSchema,
});

/**
 * Hook to get a Confluence credential by ID
 */
export const useGetConfluenceCredential = (credentialId: string) => {
  const endpoint = apiEndpoints.confluence.credential(':id').replace(':id', credentialId);
  return createGetQueryHook({
    endpoint,
    responseSchema: ConfluenceCredentialSchema,
    rQueryParams: { queryKey: ['confluence-credentials', { id: credentialId }] },
  })();
};

/**
 * Hook to list all Confluence credentials
 */
export const useListConfluenceCredentials = createGetQueryHook({
  endpoint: apiEndpoints.confluence.credentials,
  responseSchema: z.array(ConfluenceCredentialSchema),
  rQueryParams: { queryKey: ['confluence-credentials'] },
});

/**
 * Hook to update a Confluence credential
 */
export const useUpdateConfluenceCredential = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ConfluenceCredentialUpdate }) => {
      const endpoint = apiEndpoints.confluence.credential(':id').replace(':id', id);
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update credential');
      }

      return ConfluenceCredentialSchema.parse(await response.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['confluence-credentials'] });
    },
  });
};

/**
 * Hook to delete a Confluence credential
 */
export const useDeleteConfluenceCredential = createDeleteMutationHook({
  endpoint: apiEndpoints.confluence.credential(':id'),
});

/**
 * Hook to verify a Confluence credential
 */
export const useVerifyConfluenceCredential = () => {
  return useMutation({
    mutationFn: async (credentialId: string) => {
      const endpoint = apiEndpoints.confluence.credentialVerify(':id').replace(':id', credentialId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to verify credential');
      }

      return ConfluenceCredentialVerifyResponseSchema.parse(await response.json());
    },
  });
};

/**
 * Hook to deactivate a Confluence credential
 */
export const useDeactivateConfluenceCredential = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentialId: string) => {
      const endpoint = apiEndpoints.confluence.credentialDeactivate(':id').replace(':id', credentialId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to deactivate credential');
      }

      return ConfluenceCredentialSchema.parse(await response.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['confluence-credentials'] });
    },
  });
};

/**
 * Hook to activate a Confluence credential
 */
export const useActivateConfluenceCredential = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentialId: string) => {
      const endpoint = apiEndpoints.confluence.credentialActivate(':id').replace(':id', credentialId);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to activate credential');
      }

      return ConfluenceCredentialSchema.parse(await response.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['confluence-credentials'] });
    },
  });
};
