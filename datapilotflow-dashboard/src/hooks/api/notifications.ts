import { NotificationListResponse, NotificationStats } from '@/api/entities/notifications';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '@/api/helpers';
import { z } from 'zod';

export const useGetNotifications = createGetQueryHook({
  endpoint: '/notifications',
  responseSchema: NotificationListResponse,
  rQueryParams: { queryKey: ['notifications'] },
});

export const useGetNotification = createGetQueryHook({
  endpoint: '/notifications/:notification_id',
  responseSchema: NotificationListResponse,
  rQueryParams: { queryKey: ['notification'] },
});

export const useGetNotificationStats = createGetQueryHook({
  endpoint: '/notifications/stats/summary',
  responseSchema: NotificationStats,
  rQueryParams: { queryKey: ['notification-stats'] },
});

export const useMarkNotificationAsRead = createPostMutationHook({
  endpoint: '/notifications/:notification_id/read',
  bodySchema: z.object({}),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
  },
});

export const useDismissNotification = createPostMutationHook({
  endpoint: '/notifications/:notification_id/dismiss',
  bodySchema: z.object({}),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
  },
});

export const useMarkAllNotificationsAsRead = createPostMutationHook({
  endpoint: '/notifications/read-all',
  bodySchema: z.object({}),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
  },
});

export const useDeleteNotification = createDeleteMutationHook({
  endpoint: '/notifications/:notification_id',
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
  },
});
