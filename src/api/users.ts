import client from './client';
import type { User, UserRole, PaginatedResponse } from '@/types';

export interface UserCreateRequest {
  email: string;
  password: string;
  name: string;
  role: UserRole;
}

export const usersApi = {
  list: async (page = 1, pageSize = 200): Promise<PaginatedResponse<User>> => {
    const response = await client.get<PaginatedResponse<User>>('/users', {
      params: {
        page,
        page_size: pageSize, // ⚠️ 关键：后端用 snake_case
      },
    })
    return response.data
  },

  get: async (id: number): Promise<User> => {
    const response = await client.get<User>(`/users/${id}`);
    return response.data;
  },

  create: async (data: UserCreateRequest): Promise<User> => {
    const response = await client.post<User>('/users', data);
    return response.data;
  },

  update: async (id: number, data: Partial<UserCreateRequest>): Promise<User> => {
    const response = await client.put<User>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/users/${id}`);
  },

  updateRole: async (id: number, role: UserRole): Promise<User> => {
    const response = await client.put<User>(`/users/${id}/role`, { role });
    return response.data;
  },
};
