import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { User, UserRole } from '@/types';
import { usersApi, type UserCreateRequest } from '@/api/users';
import { mockUsers } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([]);
  const loading = ref(false);
  const pagination = ref({ page: 1, pageSize: 20, total: 0, totalPages: 0 });

  async function fetchUsers(page = 1, pageSize = 20) {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        users.value = mockUsers;
        pagination.value = {
  		page: (response as any).page ?? page,
  		pageSize: (response as any).pageSize ?? (response as any).page_size ?? pageSize,
  		total: (response as any).total ?? 0,
  		totalPages: (response as any).totalPages ?? (response as any).total_pages ?? 1,
		};
	return;
      }
      const response = await usersApi.list(page, pageSize);
      users.value = response.items;
      pagination.value = {
        page: response.page,
        pageSize: response.pageSize,
        total: response.total,
        totalPages: response.totalPages,
      };
    } catch (error) {
      console.error('Failed to fetch users:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createUser(data: UserCreateRequest) {
    loading.value = true;
    try {
      const user = await usersApi.create(data);
      await fetchUsers(pagination.value.page, pagination.value.pageSize);
      return user;
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateUser(id: number, data: Partial<UserCreateRequest>) {
    loading.value = true;
    try {
      const updated = await usersApi.update(id, data);
      const index = users.value.findIndex(u => u.id === id);
      if (index !== -1) {
        users.value[index] = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to update user:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteUser(id: number) {
    loading.value = true;
    try {
      await usersApi.delete(id);
      users.value = users.value.filter(u => u.id !== id);
    } catch (error) {
      console.error('Failed to delete user:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateRole(id: number, role: UserRole) {
    loading.value = true;
    try {
      const updated = await usersApi.updateRole(id, role);
      const index = users.value.findIndex(u => u.id === id);
      if (index !== -1) {
        users.value[index] = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to update role:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  return {
    users,
    loading,
    pagination,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateRole,
  };
});
