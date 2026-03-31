import client from './client';
import type { StageTemplate, StageTemplateStage } from '@/types';

export interface StageTemplateCreateRequest {
  name: string;
  description: string;
  stages: Omit<StageTemplateStage, 'id' | 'templateId'>[];
}

// 转换 stages 为后端格式（snake_case）
function transformStages(stages: any[]) {
  return stages.map(s => ({
    name: s.name,
    description: s.description,
    order: s.order,
    is_terminal: s.isTerminal ?? s.is_terminal ?? false,
    allow_result: s.allowResult ?? s.allow_result ?? false,
    require_artifact: s.requireArtifact ?? s.require_artifact ?? false,
    require_review: s.requireReview ?? s.require_review ?? false,
  }));
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
    const payload = {
      name: data.name,
      description: data.description,
      stages: transformStages(data.stages),
    };
    const response = await client.post<StageTemplate>('/templates', payload);
    return response.data;
  },

  update: async (id: number, data: Partial<StageTemplateCreateRequest>): Promise<StageTemplate> => {
    const payload: any = {};
    if (data.name !== undefined) payload.name = data.name;
    if (data.description !== undefined) payload.description = data.description;
    if (data.stages !== undefined) payload.stages = transformStages(data.stages);

    const response = await client.put<StageTemplate>(`/templates/${id}`, payload);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/templates/${id}`);
  },

  updateStages: async (id: number, stages: Omit<StageTemplateStage, 'id' | 'templateId'>[]): Promise<StageTemplate> => {
    const response = await client.put<StageTemplate>(`/templates/${id}/stages`, {
      stages: transformStages(stages)
    });
    return response.data;
  },
};
