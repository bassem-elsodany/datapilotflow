import { z } from 'zod';
import { dateSchema } from '@/utilities/date';

export const NotificationType = z.enum([
  'job_upload_progress',
  'resume_upload_progress', 
  'analysis_progress',
  'session_created',
  'session_updated',
  'session_deleted',
  'interview_started',
  'resume_analysis_completed',
  'job_analysis_completed',
  'job_deleted',
  'resume_deleted',
  'error',
  'success',
  'info'
]);

export const NotificationStatus = z.enum([
  'pending',
  'in_progress',
  'completed',
  'failed',
  'cancelled'
]);

export const NotificationPriority = z.enum([
  'low',
  'medium',
  'high',
  'urgent'
]);

export const Notification = z.object({
  notification_id: z.string(),
  user_id: z.string(),
  session_id: z.string().nullable(),
  type: NotificationType,
  status: NotificationStatus,
  priority: NotificationPriority,
  title: z.string(),
  message: z.string(),
  progress: z.number().nullable(),
  metadata: z.record(z.any()),
  created_at: dateSchema,
  updated_at: dateSchema,
  expires_at: dateSchema.nullable(),
  read_at: dateSchema.nullable(),
  dismissed_at: dateSchema.nullable(),
});

export const NotificationListResponse = z.object({
  notifications: z.array(Notification),
  total_count: z.number(),
  unread_count: z.number(),
});

export const NotificationStats = z.object({
  total_count: z.number(),
  unread_count: z.number(),
  pending_count: z.number(),
  in_progress_count: z.number(),
  completed_count: z.number(),
  failed_count: z.number(),
  by_type: z.record(z.number()),
  by_priority: z.record(z.number()),
});

export type Notification = z.infer<typeof Notification>;
export type NotificationListResponse = z.infer<typeof NotificationListResponse>;
export type NotificationStats = z.infer<typeof NotificationStats>;
export type NotificationType = z.infer<typeof NotificationType>;
export type NotificationStatus = z.infer<typeof NotificationStatus>;
export type NotificationPriority = z.infer<typeof NotificationPriority>;
