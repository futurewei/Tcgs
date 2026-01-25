import client from './client';

export interface Risk {
  id: number;
  topicId: number;
  stageInstanceId?: number;
  level: 'red' | 'yellow' | 'green';
  blockerType: string;
  blockerName?: string;
  description: string;
  expectedResolveDate?: string;
  ownerId?: number;
  owner?: { id: number; name: string; email: string };
  isResolved: boolean;
  resolvedAt?: string;
  resolutionNote?: string;
  createdById?: number;
  createdBy?: { id: number; name: string; email: string };
  createdAt: string;
  updatedAt: string;
}

export interface RiskCreate {
  topicId: number;
  stageInstanceId?: number;
  level?: string;
  blockerType: string;
  blockerName?: string;
  description: string;
  expectedResolveDate?: string;
  ownerId?: number;
}

export interface RiskUpdate {
  level?: string;
  blockerType?: string;
  blockerName?: string;
  description?: string;
  expectedResolveDate?: string;
  ownerId?: number;
  isResolved?: boolean;
  resolutionNote?: string;
}

function normalizeRisk(r: any): Risk {
  return {
    id: r.id,
    topicId: r.topic_id ?? r.topicId,
    stageInstanceId: r.stage_instance_id ?? r.stageInstanceId,
    level: r.level,
    blockerType: r.blocker_type ?? r.blockerType,
    blockerName: r.blocker_name ?? r.blockerName,
    description: r.description,
    expectedResolveDate: r.expected_resolve_date ?? r.expectedResolveDate,
    ownerId: r.owner_id ?? r.ownerId,
    owner: r.owner,
    isResolved: r.is_resolved ?? r.isResolved ?? false,
    resolvedAt: r.resolved_at ?? r.resolvedAt,
    resolutionNote: r.resolution_note ?? r.resolutionNote,
    createdById: r.created_by_id ?? r.createdById,
    createdBy: r.created_by ?? r.createdBy,
    createdAt: r.created_at ?? r.createdAt,
    updatedAt: r.updated_at ?? r.updatedAt,
  };
}

export const riskApi = {
  list: async (topicId: number, includeResolved = false): Promise<Risk[]> => {
    const response = await client.get<any[]>(`/topics/${topicId}/risks`, {
      params: { include_resolved: includeResolved }
    });
    return response.data.map(normalizeRisk);
  },

  create: async (data: RiskCreate): Promise<Risk> => {
    const response = await client.post<any>('/risks', {
      topic_id: data.topicId,
      stage_instance_id: data.stageInstanceId,
      level: data.level || 'yellow',
      blocker_type: data.blockerType,
      blocker_name: data.blockerName,
      description: data.description,
      expected_resolve_date: data.expectedResolveDate,
      owner_id: data.ownerId,
    });
    return normalizeRisk(response.data);
  },

  update: async (id: number, data: RiskUpdate): Promise<Risk> => {
    const payload: any = {};
    if (data.level !== undefined) payload.level = data.level;
    if (data.blockerType !== undefined) payload.blocker_type = data.blockerType;
    if (data.blockerName !== undefined) payload.blocker_name = data.blockerName;
    if (data.description !== undefined) payload.description = data.description;
    if (data.expectedResolveDate !== undefined) payload.expected_resolve_date = data.expectedResolveDate;
    if (data.ownerId !== undefined) payload.owner_id = data.ownerId;
    if (data.isResolved !== undefined) payload.is_resolved = data.isResolved;
    if (data.resolutionNote !== undefined) payload.resolution_note = data.resolutionNote;

    const response = await client.put<any>(`/risks/${id}`, payload);
    return normalizeRisk(response.data);
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/risks/${id}`);
  },

  resolve: async (id: number, note?: string): Promise<Risk> => {
    return riskApi.update(id, { isResolved: true, resolutionNote: note });
  },
};
