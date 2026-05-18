import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

function toSnakeKey(key: string) {
  return key.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
}

function toSnakeCaseDeep(input: any): any {
  if (Array.isArray(input)) return input.map(toSnakeCaseDeep);
  if (input && typeof input === 'object' && input.constructor === Object) {
    const out: Record<string, any> = {};
    for (const [k, v] of Object.entries(input)) {
      out[toSnakeKey(k)] = toSnakeCaseDeep(v);
    }
    return out;
  }
  return input;
}

function toCamelKey(key: string) {
  return key.replace(/_([a-z])/g, (_, m) => m.toUpperCase());
}

function toCamelCaseDeep(input: any): any {
  if (Array.isArray(input)) return input.map(toCamelCaseDeep);
  if (input && typeof input === 'object' && input.constructor === Object) {
    const out: Record<string, any> = {};
    for (const [k, v] of Object.entries(input)) {
      out[toCamelKey(k)] = toCamelCaseDeep(v);
    }
    return out;
  }
  return input;
}


const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token + normalize payload keys
client.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }

    // --- add: convert JSON body keys ---
    const ct =
      (config.headers as any)?.['Content-Type'] ??
      (config.headers as any)?.['content-type'];

    const isJson =
      typeof ct === 'string' ? ct.includes('application/json') : true;

    // don't touch FormData / Blob / ArrayBuffer etc.
    const isFormData =
      typeof FormData !== 'undefined' && config.data instanceof FormData;

    if (isJson && !isFormData && config.data && typeof config.data === 'object') {
      config.data = toSnakeCaseDeep(config.data);
    }

    return config;
  },
  (error) => Promise.reject(error)
);



// Response interceptor - normalize response keys (snake_case -> camelCase)
client.interceptors.response.use(
  (response) => {
    const ct = response.headers['content-type'] || '';
    if (ct.includes('application/json') && response.data) {
      response.data = toCamelCaseDeep(response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore();
      authStore.logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
