import { z } from 'zod';
import { dateSchema } from '@/utilities/date';

export const User = z.object({
  id: z.string().nullable().optional(),
  username: z.string().min(1),
  email: z.string().email(),
  name: z.string().min(1),
  roles: z.array(z.string()),
  permissions: z.array(z.string()).default([]),
  created_at: z.string().optional(),
  last_login: z.string().optional(),
  is_active: z.boolean().optional(),
});

export type User = z.infer<typeof User>;
