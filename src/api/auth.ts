import client from './client';
import type { LoginRequest, AuthResponse, User } from '@/types';

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await client.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await client.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const response = await client.get<User>('/auth/me');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await client.put<User>('/auth/me', data);
    return response.data;
  },
};
