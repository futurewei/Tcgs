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
  return { ...u, createdAt: u.created_at ?? u.createdAt, updatedAt: u.updated_at ?? u.updatedAt };
}

function normalizeSlot(s: any) {
  if (!s) return s;
  return { ...s, userId: s.user_id ?? s.userId, totalCapacity: s.total_capacity ?? s.totalCapacity, user: normalizeUser(s.user) };
}

function normalizeBinding(b: any) {
  if (!b) return b;
  return {
    ...b, topicId: b.topic_id ?? b.topicId, slotId: b.slot_id ?? b.slotId,
    isForced: b.is_forced ?? b.isForced ?? false, isDri: b.is_dri ?? b.isDri ?? false,
    createdAt: b.created_at ?? b.createdAt, updatedAt: b.updated_at ?? b.updatedAt, slot: normalizeSlot(b.slot),
  };
}

function normalizeStageTemplateStage(s: any) {
  if (!s) return s;
  return { ...s, templateId: s.template_id ?? s.templateId, isTerminal: s.is_terminal ?? s.isTerminal, allowResult: s.allow_result ?? s.allowResult, requireArtifact: s.require_artifact ?? s.requireArtifact, requireReview: s.require_review ?? s.requireReview };
}

function normalizeTemplate(t: any) {
  if (!t) return t;
  return { ...t, createdAt: t.created_at ?? t.createdAt, updatedAt: t.updated_at ?? t.updatedAt, stages: Array.isArray(t.stages) ? t.stages.map(normalizeStageTemplateStage) : t.stages };
}

function normalizeStageState(ss: any) {
  if (!ss) return ss;
  return { ...ss, topicId: ss.topic_id ?? ss.topicId, stageId: ss.stage_id ?? ss.stageId, completedAt: ss.completed_at ?? ss.completedAt, stage: normalizeStageTemplateStage(ss.stage) };
}

function normalizeReviewComment(r: any) {
  if (!r) return r;
  return {
    ...r,
    stageInstanceId: r.stage_instance_id ?? r.stageInstanceId,
    createdBy: normalizeUser(r.created_by ?? r.createdBy),
    createdAt: r.created_at ?? r.createdAt,
  };
}

function normalizeStageInstance(si: any) {
  if (!si) return si;
  return {
    ...si,
    topicId: si.topic_id ?? si.topicId,
    isTerminal: si.is_terminal ?? si.isTerminal,
    allowResult: si.allow_result ?? si.allowResult,
    requireArtifact: si.require_artifact ?? si.requireArtifact,
    requireReview: si.require_review ?? si.requireReview,
    startedAt: si.started_at ?? si.startedAt,
    completedAt: si.completed_at ?? si.completedAt,
    successCriteria: si.success_criteria ?? si.successCriteria,
    failureCriteria: si.failure_criteria ?? si.failureCriteria,
    clonedFromId: si.cloned_from_id ?? si.clonedFromId,
    createdAt: si.created_at ?? si.createdAt,
    createdBy: normalizeUser(si.created_by ?? si.createdBy),
    techPoints: Array.isArray(si.tech_points ?? si.techPoints)
      ? (si.tech_points ?? si.techPoints).map(normalizeTechPoint)
      : [],
    reviews: Array.isArray(si.reviews)
      ? si.reviews.map(normalizeReviewComment)
      : [],
  };
}

function normalizeTechPoint(tp: any) {
  if (!tp) return tp;
  return {
    ...tp,
    stageId: tp.stage_id ?? tp.stageId,
    firstAuthor: normalizeUser(tp.first_author ?? tp.firstAuthor),
    firstAuthorId: tp.first_author_id ?? tp.firstAuthorId,
    createdAt: tp.created_at ?? tp.createdAt,
    contributors: Array.isArray(tp.contributors) ? tp.contributors.map((c: any) => ({
      ...c, userId: c.user_id ?? c.userId, userName: c.user_name ?? c.userName,
      contributionPercentage: c.contribution_percentage ?? c.contributionPercentage,
    })) : [],
  };
}

function normalizeTopic(t: any): Topic {
  if (!t) return t;
  const bindings = Array.isArray(t.bindings) ? t.bindings.map(normalizeBinding) : [];
  return {
    ...t,
    templateId: t.template_id ?? t.templateId,
    currentStageId: t.current_stage_id ?? t.currentStageId,
    currentStageInstanceId: t.current_stage_instance_id ?? t.currentStageInstanceId,
    requesterName: t.requester_name ?? t.requesterName ?? '',
    requesterUserId: t.requester_user_id ?? t.requesterUserId,
    requesterUser: normalizeUser(t.requester_user ?? t.requesterUser),
    background: t.background,
    userGoal: t.user_goal ?? t.userGoal,
    stageStates: Array.isArray(t.stage_states) ? t.stage_states.map(normalizeStageState) : (Array.isArray(t.stageStates) ? t.stageStates.map(normalizeStageState) : []),
    stageInstances: Array.isArray(t.stage_instances) ? t.stage_instances.map(normalizeStageInstance) : (Array.isArray(t.stageInstances) ? t.stageInstances.map(normalizeStageInstance) : []),
    template: normalizeTemplate(t.template),
    bindings,
    driId: t.dri_id ?? t.driId,
    dri: normalizeUser(t.dri),
  } as any;
}

function normalizePaginatedTopics(p: any): PaginatedResponse<Topic> {
  return { ...p, pageSize: p.page_size ?? p.pageSize, totalPages: p.total_pages ?? p.totalPages, items: Array.isArray(p.items) ? p.items.map(normalizeTopic) : [] };
}

export const topicsApi = {
  list: async (filters: TopicFilters = {}): Promise<PaginatedResponse<Topic>> => {
    const params: any = { ...filters };
    if (filters.pageSize !== undefined) { params.page_size = filters.pageSize; delete params.pageSize; }
    if (filters.driId !== undefined) { params.dri_id = filters.driId; delete params.driId; }
    const response = await client.get<PaginatedResponse<any>>('/topics', { params });
    return normalizePaginatedTopics(response.data);
  },

  get: async (id: number): Promise<Topic> => {
    const response = await client.get<any>(`/topics/${id}`);
    return normalizeTopic(response.data);
  },

  create: async (data: TopicCreateRequest): Promise<Topic> => {
    const payload: any = {
      title: data.title, description: data.description, type: data.type, urgency: data.urgency,
      template_id: data.templateId, requester_name: data.requesterName, requester_user_id: data.requesterUserId,
      initial_dri_slot_id: data.initialDriSlotId, initial_dri_user_id: data.initialDriUserId, initial_dri_percentage: data.initialDriPercentage,
      background: data.background, user_goal: data.userGoal,
    };
    const response = await client.post<any>('/topics', payload);
    return normalizeTopic(response.data);
  },

  update: async (id: number, data: TopicUpdateRequest): Promise<Topic> => {
    const payload: any = {};
    if (data.title !== undefined) payload.title = data.title;
    if (data.description !== undefined) payload.description = data.description;
    if (data.urgency !== undefined) payload.urgency = data.urgency;
    if (data.result !== undefined) payload.result = data.result;
    if (data.background !== undefined) payload.background = data.background;
    if (data.userGoal !== undefined) payload.user_goal = data.userGoal;
    const response = await client.put<any>(`/topics/${id}`, payload);
    return normalizeTopic(response.data);
  },

  delete: async (id: number): Promise<void> => { await client.delete(`/topics/${id}`); },

  advanceStage: async (id: number, stageId: number): Promise<Topic> => {
    const response = await client.post<any>(`/topics/${id}/stages/${stageId}/advance`);
    return normalizeTopic(response.data);
  },

  backwardStage: async (id: number, stageId: number): Promise<Topic> => {
    const response = await client.post<any>(`/topics/${id}/stages/${stageId}/backward`);
    return normalizeTopic(response.data);
  },

  changeDri: async (id: number, data: ChangeDRIRequest): Promise<Topic> => {
    const payload = { new_dri_slot_id: data.newDriSlotId };
    const response = await client.post<any>(`/topics/${id}/change-dri`, payload);
    return normalizeTopic(response.data);
  },

  // ============ Stage Instances ============
  listStageInstances: async (topicId: number): Promise<any[]> => {
    const response = await client.get<any[]>(`/topics/${topicId}/stages`);
    return response.data.map(normalizeStageInstance);
  },

  createStageInstance: async (topicId: number, data: { name: string; description?: string; insertAfterId?: number | null; requireReview?: boolean }): Promise<any> => {
    const payload: any = { name: data.name, description: data.description };
    if (data.insertAfterId) payload.insert_after_id = data.insertAfterId;
    if (data.requireReview !== undefined) payload.require_review = data.requireReview;
    const response = await client.post<any>(`/topics/${topicId}/stages`, payload);
    return normalizeStageInstance(response.data);
  },

  updateStageInstance: async (topicId: number, stageId: number, data: any): Promise<any> => {
    const payload: any = {};
    if (data.name !== undefined) payload.name = data.name;
    if (data.description !== undefined) payload.description = data.description;
    if (data.objective !== undefined) payload.objective = data.objective;
    if (data.successCriteria !== undefined) payload.success_criteria = data.successCriteria;
    if (data.failureCriteria !== undefined) payload.failure_criteria = data.failureCriteria;
    if (data.success_criteria !== undefined) payload.success_criteria = data.success_criteria;
    if (data.failure_criteria !== undefined) payload.failure_criteria = data.failure_criteria;
    if (data.required_outputs !== undefined) payload.required_outputs = data.required_outputs;
    if (data.conclusion !== undefined) payload.conclusion = data.conclusion;
    if (data.status !== undefined) payload.status = data.status;
    const response = await client.put<any>(`/topics/${topicId}/stages/${stageId}`, payload);
    return normalizeStageInstance(response.data);
  },

  deleteStageInstance: async (topicId: number, stageId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/stages/${stageId}`);
  },

  copyStageInstance: async (topicId: number, sourceStageId: number, insertAfterId?: number): Promise<any> => {
    const payload: any = { source_stage_id: sourceStageId };
    if (insertAfterId) payload.insert_after_id = insertAfterId;
    const response = await client.post<any>(`/topics/${topicId}/stages/copy`, payload);
    return normalizeStageInstance(response.data);
  },

  activateStageInstance: async (topicId: number, stageId: number): Promise<any> => {
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/activate`);
    return normalizeStageInstance(response.data);
  },

  reorderStages: async (topicId: number, stageIds: number[]): Promise<any[]> => {
    const response = await client.post<any[]>(`/topics/${topicId}/stages/reorder`, { stage_ids: stageIds });
    return response.data.map(normalizeStageInstance);
  },

  // ============ 阶段跃迁 ============
  validateStageCompletion: async (topicId: number, stageId: number): Promise<{ valid: boolean; errors: string[]; warnings: string[] }> => {
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/validate`);
    return response.data;
  },

  completeStage: async (topicId: number, stageId: number, data?: { completionNote?: string; remainingIssues?: string; force?: boolean }): Promise<any> => {
    const payload = {
      completion_note: data?.completionNote,
      remaining_issues: data?.remainingIssues,
      force: data?.force || false,
    };
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/complete`, payload);
    return normalizeStageInstance(response.data);
  },

  reopenStage: async (topicId: number, stageId: number): Promise<any> => {
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/reopen`);
    return normalizeStageInstance(response.data);
  },

  moveStage: async (topicId: number, stageId: number, direction: 'forward' | 'back', data?: { completionNote?: string; remainingIssues?: string }): Promise<any> => {
    const payload = {
      direction,
      completion_note: data?.completionNote,
      remaining_issues: data?.remainingIssues,
    };
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/move`, payload);
    return response.data;
  },

  // ============ Tech Points ============
  createTechPoint: async (topicId: number, stageId: number, data: { name: string; description?: string; firstAuthorId: number; hypothesis?: string }): Promise<any> => {
    const payload = { name: data.name, description: data.description, first_author_id: data.firstAuthorId, hypothesis: data.hypothesis };
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/tech-points`, payload);
    return normalizeTechPoint(response.data);
  },

  updateTechPoint: async (topicId: number, stageId: number, pointId: number, data: any): Promise<any> => {
    const response = await client.put<any>(`/topics/${topicId}/stages/${stageId}/tech-points/${pointId}`, data);
    return normalizeTechPoint(response.data);
  },

  deleteTechPoint: async (topicId: number, stageId: number, pointId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/stages/${stageId}/tech-points/${pointId}`);
  },

  // ============ Deliverables ============
  listDeliverables: async (topicId: number, stageId?: number): Promise<StageDeliverable[]> => {
    const params: any = {};
    if (stageId) params.stage_id = stageId;
    const response = await client.get<any[]>(`/topics/${topicId}/deliverables`, { params });
    return response.data.map((d: any) => ({
      ...d, topicId: d.topic_id ?? d.topicId, stageId: d.stage_id ?? d.stageId,
      stageInstanceId: d.stage_instance_id ?? d.stageInstanceId,
      techPointId: d.tech_point_id ?? d.techPointId,
      fileName: d.file_name ?? d.fileName, fileSize: d.file_size ?? d.fileSize,
      mimeType: d.mime_type ?? d.mimeType, createdById: d.created_by_id ?? d.createdById,
      createdBy: d.created_by ?? d.createdBy, createdAt: d.created_at ?? d.createdAt,
      updatedAt: d.updated_at ?? d.updatedAt,
    }));
  },

  createDeliverable: async (topicId: number, data: StageDeliverableCreateRequest): Promise<StageDeliverable> => {
    const payload: any = {
      stage_id: data.stageId, stage_instance_id: data.stageInstanceId, tech_point_id: data.techPointId,
      name: data.name, type: data.type, category: data.category, url: data.url, description: data.description,
      file_name: data.fileName, file_size: data.fileSize, mime_type: data.mimeType,
    };
    const response = await client.post<any>(`/topics/${topicId}/deliverables`, payload);
    const d = response.data;
    return { ...d, topicId: d.topic_id ?? d.topicId, stageId: d.stage_id ?? d.stageId, fileName: d.file_name ?? d.fileName, fileSize: d.file_size ?? d.fileSize, mimeType: d.mime_type ?? d.mimeType, createdById: d.created_by_id ?? d.createdById, createdBy: d.created_by ?? d.createdBy, createdAt: d.created_at ?? d.createdAt, updatedAt: d.updated_at ?? d.updatedAt };
  },

  deleteDeliverable: async (topicId: number, deliverableId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/deliverables/${deliverableId}`);
  },

  // Artifacts
  createArtifact: async (data: ArtifactCreateRequest): Promise<Artifact> => {
    const response = await client.post<Artifact>(`/topics/${data.topicId}/artifacts`, data);
    return response.data;
  },

  // Reviews
  createReview: async (data: ReviewCreateRequest): Promise<ReviewComment> => {
    const response = await client.post<ReviewComment>(`/topics/${data.topicId}/reviews`, data);
    return response.data;
  },

  // ============ Topic-level Tech Points (算法思想) ============
  
  // 获取课题关联人员（用于选择提出人）
  getTopicMembers: async (topicId: number): Promise<any[]> => {
    const response = await client.get<any[]>(`/topics/${topicId}/members`);
    return response.data;
  },

  // 获取课题级别的技术点/算法思想
  getTopicTechPoints: async (topicId: number): Promise<any[]> => {
    const response = await client.get<any[]>(`/topics/${topicId}/tech-points`);
    return response.data;
  },

  // 创建课题级别的技术点/算法思想
  createTopicTechPoint: async (topicId: number, data: { name: string; description?: string; hypothesis?: string; firstAuthorId: number }): Promise<any> => {
    const payload = { name: data.name, description: data.description, hypothesis: data.hypothesis, first_author_id: data.firstAuthorId };
    const response = await client.post<any>(`/topics/${topicId}/tech-points`, payload);
    return response.data;
  },

  // 更新课题级别的技术点/算法思想
  updateTopicTechPoint: async (topicId: number, pointId: number, data: any): Promise<any> => {
    const response = await client.put<any>(`/topics/${topicId}/tech-points/${pointId}`, data);
    return response.data;
  },

  // 删除课题级别的技术点/算法思想
  deleteTopicTechPoint: async (topicId: number, pointId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/tech-points/${pointId}`);
  },

  // ============ Stage Reviews (评审意见) ============

  listStageReviews: async (topicId: number, stageId: number): Promise<any[]> => {
    const response = await client.get<any[]>(`/topics/${topicId}/stages/${stageId}/reviews`);
    return response.data.map(normalizeReviewComment);
  },

  addStageReview: async (topicId: number, stageId: number, content: string): Promise<any> => {
    const response = await client.post<any>(`/topics/${topicId}/stages/${stageId}/reviews`, { content });
    return normalizeReviewComment(response.data);
  },

  deleteStageReview: async (topicId: number, stageId: number, reviewId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/stages/${stageId}/reviews/${reviewId}`);
  },
};
