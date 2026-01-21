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
  PaginatedResponse,
  StageDeliverable,
  StageDeliverableCreateRequest,
  ChangeDRIRequest
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

function normalizeSlot(s: any) {
  if (!s) return s;
  return {
    ...s,
    userId: s.user_id ?? s.userId,
    totalCapacity: s.total_capacity ?? s.totalCapacity,
    user: normalizeUser(s.user),
  };
}

function normalizeBinding(b: any) {
  if (!b) return b;
  return {
    ...b,
    topicId: b.topic_id ?? b.topicId,
    slotId: b.slot_id ?? b.slotId,
    isForced: b.is_forced ?? b.isForced ?? false,
    isDri: b.is_dri ?? b.isDri ?? false,
    createdAt: b.created_at ?? b.createdAt,
    updatedAt: b.updated_at ?? b.updatedAt,
    slot: normalizeSlot(b.slot),
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
  
  // Normalize bindings
  const bindings = Array.isArray(t.bindings) 
    ? t.bindings.map(normalizeBinding) 
    : [];
  
  return {
    ...t,
    templateId: t.template_id ?? t.templateId,
    currentStageId: t.current_stage_id ?? t.currentStageId,
    requesterName: t.requester_name ?? t.requesterName ?? '',
    requesterUserId: t.requester_user_id ?? t.requesterUserId,
    requesterUser: normalizeUser(t.requester_user ?? t.requesterUser),
    stageStates: Array.isArray(t.stage_states)
      ? t.stage_states.map(normalizeStageState)
      : (Array.isArray(t.stageStates) ? t.stageStates.map(normalizeStageState) : t.stageStates),
    template: normalizeTemplate(t.template),
    bindings,
    // Legacy dri fields
    driId: t.dri_id ?? t.driId,
    dri: normalizeUser(t.dri),
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
      title: data.title,
      description: data.description,
      type: data.type,
      urgency: data.urgency,
      template_id: data.templateId,
      requester_name: data.requesterName,
      requester_user_id: data.requesterUserId,
      initial_dri_slot_id: data.initialDriSlotId,
      initial_dri_percentage: data.initialDriPercentage,
    };

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

  backwardStage: async (id: number, stageId: number): Promise<Topic> => {
    const response = await client.post<any>(`/topics/${id}/stages/${stageId}/backward`);
    return normalizeTopic(response.data);
  },

  changeDri: async (id: number, data: ChangeDRIRequest): Promise<Topic> => {
    const payload = {
      new_dri_slot_id: data.newDriSlotId,
    };
    const response = await client.post<any>(`/topics/${id}/change-dri`, payload);
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

  // Stage Deliverables
  listDeliverables: async (topicId: number, stageId?: number): Promise<StageDeliverable[]> => {
    const params: any = {};
    if (stageId) params.stage_id = stageId;
    const response = await client.get<any[]>(`/topics/${topicId}/deliverables`, { params });
    return response.data.map((d: any) => ({
      ...d,
      topicId: d.topic_id ?? d.topicId,
      stageId: d.stage_id ?? d.stageId,
      fileName: d.file_name ?? d.fileName,
      fileSize: d.file_size ?? d.fileSize,
      mimeType: d.mime_type ?? d.mimeType,
      createdById: d.created_by_id ?? d.createdById,
      createdBy: d.created_by ?? d.createdBy,
      createdAt: d.created_at ?? d.createdAt,
      updatedAt: d.updated_at ?? d.updatedAt,
    }));
  },

  createDeliverable: async (topicId: number, data: StageDeliverableCreateRequest): Promise<StageDeliverable> => {
    const payload: any = {
      stage_id: data.stageId,
      name: data.name,
      type: data.type,
      url: data.url,
      description: data.description,
      file_name: data.fileName,
      file_size: data.fileSize,
      mime_type: data.mimeType,
    };
    const response = await client.post<any>(`/topics/${topicId}/deliverables`, payload);
    const d = response.data;
    return {
      ...d,
      topicId: d.topic_id ?? d.topicId,
      stageId: d.stage_id ?? d.stageId,
      fileName: d.file_name ?? d.fileName,
      fileSize: d.file_size ?? d.fileSize,
      mimeType: d.mime_type ?? d.mimeType,
      createdById: d.created_by_id ?? d.createdById,
      createdBy: d.created_by ?? d.createdBy,
      createdAt: d.created_at ?? d.createdAt,
      updatedAt: d.updated_at ?? d.updatedAt,
    };
  },

  deleteDeliverable: async (topicId: number, deliverableId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/deliverables/${deliverableId}`);
  },
};
