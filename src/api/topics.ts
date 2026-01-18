// src/api/topics.ts
import client from './client';
import type {
  Topic,
  TopicCreateRequest,
  TopicUpdateRequest,
  Artifact,
  ArtifactCreateRequest,
  ReviewComment,
  ReviewCreateRequest,
  PaginatedResponse
} from '@/types';

export interface TopicFilters {
  type?: string;
  urgency?: string;
  result?: string;
  driId?: number;
  search?: string;
  page?: number;
  pageSize?: number;
}

// --- normalize helpers (snake_case -> camelCase) ---
function normalizeUser(u: any) {
  if (!u) return u;
  return {
    ...u,
    createdAt: u.created_at ?? u.createdAt,
    updatedAt: u.updated_at ?? u.updatedAt,
  };
}

function normalizeStageTemplateStage(s: any) {
  if (!s) return s;
  return {
    ...s,
    templateId: s.template_id ?? s.templateId,
    isTerminal: s.is_terminal ?? s.isTerminal,
    allowResult: s.allow_result ?? s.allowResult,
    requireArtifact: s.require_artifact ?? s.requireArtifact,
  };
}

function normalizeTemplate(t: any) {
  if (!t) return t;
  return {
    ...t,
    createdAt: t.created_at ?? t.createdAt,
    updatedAt: t.updated_at ?? t.updatedAt,
    stages: Array.isArray(t.stages) ? t.stages.map(normalizeStageTemplateStage) : t.stages,
  };
}

function normalizeStageState(ss: any) {
  if (!ss) return ss;
  return {
    ...ss,
    topicId: ss.topic_id ?? ss.topicId,
    stageId: ss.stage_id ?? ss.stageId,
    completedAt: ss.completed_at ?? ss.completedAt,
    stage: normalizeStageTemplateStage(ss.stage),
  };
}

function normalizeTopic(t: any): Topic {
  if (!t) return t;
  return {
    ...t,
    driId: t.dri_id ?? t.driId,
    templateId: t.template_id ?? t.templateId,
    currentStageId: t.current_stage_id ?? t.currentStageId,
    requesterName: t.requester_name ?? t.requesterName ?? '',
    requesterUserId: t.requester_user_id ?? t.requesterUserId,
    requesterUser: normalizeUser(t.requester_user ?? t.requesterUser),
    stageStates: Array.isArray(t.stage_states)
      ? t.stage_states.map(normalizeStageState)
      : (Array.isArray(t.stageStates) ? t.stageStates.map(normalizeStageState) : t.stageStates),
    dri: normalizeUser(t.dri),
    template: normalizeTemplate(t.template),
    // 你后端如果也返回 bindings/artifacts/reviews，且字段是 snake_case，
    // 建议后面也统一在这里 normalize（先不动也不影响"点灯/跳转"）
  } as any;
}

function normalizePaginatedTopics(p: any): PaginatedResponse<Topic> {
  return {
    ...p,
    pageSize: p.page_size ?? p.pageSize,
    totalPages: p.total_pages ?? p.totalPages,
    items: Array.isArray(p.items) ? p.items.map(normalizeTopic) : [],
  };
}

export const topicsApi = {
  list: async (filters: TopicFilters = {}): Promise<PaginatedResponse<Topic>> => {
    const params: any = { ...filters };

    // camelCase -> snake_case (query)
    if (filters.pageSize !== undefined) {
      params.page_size = filters.pageSize;
      delete params.pageSize;
    }
    if (filters.driId !== undefined) {
      params.dri_id = filters.driId;
      delete params.driId;
    }

    const response = await client.get<PaginatedResponse<any>>('/topics', { params });
    return normalizePaginatedTopics(response.data);
  },

  get: async (id: number): Promise<Topic> => {
    const response = await client.get<any>(`/topics/${id}`);
    return normalizeTopic(response.data);
  },

  create: async (data: TopicCreateRequest): Promise<Topic> => {
    const payload: any = {
      ...data,
      dri_id: (data as any).driId ?? (data as any).dri_id,
      template_id: (data as any).templateId ?? (data as any).template_id,
      requester_name: (data as any).requesterName ?? (data as any).requester_name,
      requester_user_id: (data as any).requesterUserId ?? (data as any).requester_user_id,
    };
    delete payload.driId;
    delete payload.templateId;
    delete payload.requesterName;
    delete payload.requesterUserId;

    const response = await client.post<any>('/topics', payload);
    return normalizeTopic(response.data);
  },

  update: async (id: number, data: TopicUpdateRequest): Promise<Topic> => {
    const response = await client.put<any>(`/topics/${id}`, data);
    return normalizeTopic(response.data);
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/topics/${id}`);
  },

  advanceStage: async (id: number, stageId: number): Promise<Topic> => {
    const response = await client.post<any>(`/topics/${id}/stages/${stageId}/advance`);
    return normalizeTopic(response.data);
  },

  setResult: async (id: number, result: string): Promise<Topic> => {
    const response = await client.post<any>(`/topics/${id}/result`, { result });
    return normalizeTopic(response.data);
  },

  // Artifacts
  listArtifacts: async (topicId: number, stageId?: number): Promise<Artifact[]> => {
    const response = await client.get<Artifact[]>(`/topics/${topicId}/artifacts`, {
      params: stageId ? { stageId } : undefined
    });
    return response.data;
  },

  createArtifact: async (data: ArtifactCreateRequest): Promise<Artifact> => {
    const response = await client.post<Artifact>(`/topics/${data.topicId}/artifacts`, data);
    return response.data;
  },

  // Reviews
  listReviews: async (topicId: number, stageId?: number): Promise<ReviewComment[]> => {
    const response = await client.get<ReviewComment[]>(`/topics/${topicId}/reviews`, {
      params: stageId ? { stageId } : undefined
    });
    return response.data;
  },

  createReview: async (data: ReviewCreateRequest): Promise<ReviewComment> => {
    const response = await client.post<ReviewComment>(`/topics/${data.topicId}/reviews`, data);
    return response.data;
  },
};
