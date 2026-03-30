import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@/types';
import { authApi } from '@/api/auth';
import { mockUsers } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('token'));
  const loading = ref(false);

  const isAuthenticated = computed(() => !!token.value && !!user.value);
  const isAdmin = computed(() => user.value?.role === 'ADMIN');
  const isMember = computed(() => user.value?.role === 'MEMBER');
  const isReviewer = computed(() => user.value?.role === 'REVIEWER');
  const isExternal = computed(() => user.value?.role === 'EXTERNAL');
  const isCustomer = computed(() => user.value?.role === 'CUSTOMER');
  // 是否可以编辑课题内容（非 CUSTOMER 的已登录用户）
  const canEditTopic = computed(() => !!user.value && user.value.role !== 'CUSTOMER');

  async function login(email: string, password: string) {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        // Demo mode - accept any valid demo email
        const demoUser = mockUsers.find(u => u.email === email);
        user.value = demoUser ?? mockUsers[0];
        token.value = 'demo-token';
        localStorage.setItem('token', 'demo-token');
        return true;
      }

      const p = await authApi.login({ email, password });
      token.value = p.access_token;
      user.value = p.user;
      localStorage.setItem('token', p.access_token);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      // 非 demo 模式：登录失败就保持为空
      user.value = null;
      token.value = null;
      localStorage.removeItem('token');
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;

    loading.value = true;
    try {
      if (DEMO_MODE || token.value === 'demo-token') {
        user.value = mockUsers[0];
        return;
      }
      user.value = await authApi.me();
    } catch (error) {
      console.error('Failed to fetch user:', error);
      // 非 demo 模式：不要 fallback 到 mock，否则会把系统变成假数据状态
      user.value = null;
      token.value = null;
      localStorage.removeItem('token');
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem('token');
  }

  function hasRole(...roles: string[]) {
    return user.value ? roles.includes(user.value.role) : false;
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isAdmin,
    isMember,
    isReviewer,
    isExternal,
    isCustomer,
    canEditTopic,
    login,
    fetchUser,
    logout,
    hasRole,
  };
});
