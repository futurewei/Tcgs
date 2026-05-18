import client from './client';
import type {
  Capability,
  CapabilityCreateRequest,
  CapabilityUpdateRequest,
  CapabilityStats,
  CapabilityCategory,
  CapabilityGeneration,
  GenerationCreateRequest,
  GenerationUpdateRequest,
  DeliveryIssue,
  DeliveryIssueCreateRequest,
  DeliveryIssueUpdateRequest,
} from '@/types';

export const capabilitiesApi = {
  // ============ Category ============

  getCategoryTree: async (): Promise<CapabilityCategory[]> => {
    const response = await client.get<CapabilityCategory[]>('/capabilities/categories/tree');
    return response.data;
  },

  getCategoriesFlat: async (): Promise<CapabilityCategory[]> => {
    const response = await client.get<CapabilityCategory[]>('/capabilities/categories/flat');
    return response.data;
  },

  // ============ Generation CRUD ============

  createGeneration: async (capabilityId: number, data: GenerationCreateRequest): Promise<CapabilityGeneration> => {
    const response = await client.post<CapabilityGeneration>(`/capabilities/${capabilityId}/generations`, data);
    return response.data;
  },

  updateGeneration: async (generationId: number, data: GenerationUpdateRequest): Promise<CapabilityGeneration> => {
    const response = await client.put<CapabilityGeneration>(`/capabilities/generations/${generationId}`, data);
    return response.data;
  },

  deleteGeneration: async (generationId: number): Promise<void> => {
    await client.delete(`/capabilities/generations/${generationId}`);
  },

  // ============ Capability CRUD ============

  list: async (params?: Record<string, any>): Promise<Capability[]> => {
    const response = await client.get<Capability[]>('/capabilities', { params });
    return response.data;
  },

  get: async (id: number): Promise<Capability> => {
    const response = await client.get<Capability>(`/capabilities/${id}`);
    return response.data;
  },

  create: async (data: CapabilityCreateRequest): Promise<Capability> => {
    const response = await client.post<Capability>('/capabilities', data);
    return response.data;
  },

  update: async (id: number, data: CapabilityUpdateRequest): Promise<Capability> => {
    const response = await client.put<Capability>(`/capabilities/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/capabilities/${id}`);
  },

  getStats: async (): Promise<CapabilityStats> => {
    const response = await client.get<CapabilityStats>('/capabilities/stats');
    return response.data;
  },

  // ============ DeliveryIssue CRUD ============

  listIssues: async (params?: Record<string, any>): Promise<DeliveryIssue[]> => {
    const response = await client.get<DeliveryIssue[]>('/capabilities/issues', { params });
    return response.data;
  },

  getIssue: async (id: number): Promise<DeliveryIssue> => {
    const response = await client.get<DeliveryIssue>(`/capabilities/issues/${id}`);
    return response.data;
  },

  createIssue: async (data: DeliveryIssueCreateRequest): Promise<DeliveryIssue> => {
    const response = await client.post<DeliveryIssue>('/capabilities/issues', data);
    return response.data;
  },

  updateIssue: async (id: number, data: DeliveryIssueUpdateRequest): Promise<DeliveryIssue> => {
    const response = await client.put<DeliveryIssue>(`/capabilities/issues/${id}`, data);
    return response.data;
  },

  deleteIssue: async (id: number): Promise<void> => {
    await client.delete(`/capabilities/issues/${id}`);
  },
};
