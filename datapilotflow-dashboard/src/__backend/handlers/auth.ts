import { http, HttpResponse } from 'msw';
import { z } from 'zod';
import { apiUrl, validateRequestUsing } from '@/__backend/helpers';
import { date } from '@/utilities/date';
import { generateId } from '@/utilities/uid';
import { apiEndpoints } from '@/config';

const TOKEN_EXPIRATION_IN_HOURS = 24;

export default [
  // POST /auth/login
  http.post(apiUrl(apiEndpoints.auth.login), async ({ request }) => {
    const schema = z.object({
      username: z.string(),
      password: z.string(),
      remember: z.boolean().optional(),
    });

    try {
      const data = await validateRequestUsing(request, schema);

      if (data.password !== '123456789' || data.username !== 'john.doe') {
        return HttpResponse.json({ detail: 'Invalid username or password' }, { status: 401 });
      }

      return HttpResponse.json({
        access_token: generateId(),
        token_type: 'bearer',
        expires_in: TOKEN_EXPIRATION_IN_HOURS * 60 * 60, // Convert to seconds
      });
    } catch (error) {
      return HttpResponse.json({ detail: 'Invalid request format' }, { status: 400 });
    }
  }),

  // GET /auth/me
  http.get(apiUrl(apiEndpoints.auth.me), async () => {
    return HttpResponse.json({
      id: generateId(),
      username: 'john.doe',
      email: 'john.doe@example.com',
      name: 'John Doe',
      roles: ['interviewer'],
      created_at: date().subtract(30, 'days').toISOString(),
      last_login: date().subtract(1, 'hour').toISOString(),
    });
  }),

  // POST /auth/logout
  http.post(apiUrl(apiEndpoints.auth.logout), async () => {
    return new HttpResponse(null, { status: 200 });
  }),
];
