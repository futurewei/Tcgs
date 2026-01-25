// src/api/stageInstances.ts
// Stage Instance API - 阶段实例管理

import client from './client';

export interface StageInstanceCreate {
  name: string;
  description?: string;
  objective?: string;
  successCriteria?: string;
  failureCriteria?: string;
  insertAfterId?: number;
}

export interface StageInstanceUpdate {
  name?: string;
  description?: string;
  objective?: string;
  successCriteria?: string;
  failureCriteria?: string;
  conclusion?: string;
  status?: string;
}

export interface StageCopyRequest {
  sourceStageId: number;
  insertAfterId?: number;
}

export interface TechPointCreate {
  name: string;
  description?: string;
  hypothesis?: string;
  approach?: string;
  firstAuthorId: number;
}

export interface TechPointUpdate {
  name?: string;
  description?: string;
  hypothesis?: string;
  approach?: string;
  conclusion?: string;
  status?: string;
}

// Convert camelCase to snake_case
function toSnakeCase(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(toSnakeCase);
  if (typeof obj !== 'object') return obj;
  
  const result: any = {};
  for (const key in obj) {
    const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
    result[snakeKey] = toSnakeCase(obj[key]);
  }
  return result;
}

export const stageInstancesApi = {
  // List all stage instances for a topic
  list: async (topicId: number) => {
    const res = await api.get(`/topics/${topicId}/stages`);
    return res.data;
  },

  // Get a single stage instance with tech points
  get: async (topicId: number, stageId: number) => {
    const res = await api.get(`/topics/${topicId}/stages/${stageId}`);
    return res.data;
  },

  // Create a new stage instance
  create: async (topicId: number, data: StageInstanceCreate) => {
    const res = await api.post(`/topics/${topicId}/stages`, toSnakeCase(data));
    return res.data;
  },

  // Update a stage instance
  update: async (topicId: number, stageId: number, data: StageInstanceUpdate) => {
    const res = await api.put(`/topics/${topicId}/stages/${stageId}`, toSnakeCase(data));
    return res.data;
  },

  // Delete a stage instance
  delete: async (topicId: number, stageId: number) => {
    const res = await api.delete(`/topics/${topicId}/stages/${stageId}`);
    return res.data;
  },

  // Reorder stages
  reorder: async (topicId: number, stageIds: number[]) => {
    const res = await api.post(`/topics/${topicId}/stages/reorder`, { stage_ids: stageIds });
    return res.data;
  },

  // Copy a stage (for algorithm forking)
  copy: async (topicId: number, data: StageCopyRequest) => {
    const res = await api.post(`/topics/${topicId}/stages/copy`, toSnakeCase(data));
    return res.data;
  },

  // Activate a stage
  activate: async (topicId: number, stageId: number) => {
    const res = await api.post(`/topics/${topicId}/stages/${stageId}/activate`);
    return res.data;
  },

  // Tech Points
  listTechPoints: async (topicId: number, stageId: number) => {
    const res = await api.get(`/topics/${topicId}/stages/${stageId}/tech-points`);
    return res.data;
  },

  createTechPoint: async (topicId: number, stageId: number, data: TechPointCreate) => {
    const res = await api.post(`/topics/${topicId}/stages/${stageId}/tech-points`, toSnakeCase(data));
    return res.data;
  },

  updateTechPoint: async (topicId: number, stageId: number, pointId: number, data: TechPointUpdate) => {
    const res = await api.put(`/topics/${topicId}/stages/${stageId}/tech-points/${pointId}`, toSnakeCase(data));
    return res.data;
  },

  deleteTechPoint: async (topicId: number, stageId: number, pointId: number) => {
    const res = await api.delete(`/topics/${topicId}/stages/${stageId}/tech-points/${pointId}`);
    return res.data;
  },

  addContributor: async (topicId: number, stageId: number, pointId: number, data: { userId: number; contribution?: string }) => {
    const res = await api.post(`/topics/${topicId}/stages/${stageId}/tech-points/${pointId}/contributors`, toSnakeCase(data));
    return res.data;
  },
};

export default stageInstancesApi;
