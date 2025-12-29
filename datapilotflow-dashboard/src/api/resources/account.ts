import { client } from '../axios';
import { User } from '../entities';
import { apiEndpoints } from '@/config';

export async function getAccountInfo() {
  const response = await client.get(apiEndpoints.users.me);
  return User.parse(response.data);
}
