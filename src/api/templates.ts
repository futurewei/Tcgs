import client from './client';
import type { StageTemplate, StageTemplateStage } from '@/types';

export interface StageTemplateCreateRequest {
  name: string;
  description: string;
  stages: Omit<StageTemplateStage, 'id' | 'templateId'>[];
}

export const templatesApi = {
  list: async (): Promise<StageTemplate[]> => {
    const response = await client.get<StageTemplate[]>('/templates');
    return response.data;
  },

  get: async (id: number): Promise<StageTemplate> => {
    const response = await client.get<StageTemplate>(`/templates/${id}`);
    return response.data;
  },

  create: async (data: StageTemplateCreateRequest): Promise<StageTemplate> => {
    const response = await client.post<StageTemplate>('/templates', data);
    return response.data;
  },

  update: async (id: number, data: Partial<StageTemplateCreateRequest>): Promise<StageTemplate> => {
    const response = await client.put<StageTemplate>(`/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/templates/${id}`);
  },

  updateStages: async (id: number, stages: Omit<StageTemplateStage, 'id' | 'templateId'>[]): Promise<StageTemplate> => {
    const response = await client.put<StageTemplate>(`/templates/${id}/stages`, { stages });
    return response.data;
  },
};
