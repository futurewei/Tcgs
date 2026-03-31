import client from './client';
import type {
  DashboardKPI,
  ThroughputData,
  PersonLoadData,
  ExternalCollabData,
  AuditLog,
  PaginatedResponse
} from '@/types';

// 将审计日志从 snake_case 转换为 camelCase
function normalizeAuditLog(log: any): AuditLog {
  return {
    id: log.id,
    action: log.action,
    entityType: log.entity_type ?? log.entityType,
    entityId: log.entity_id ?? log.entityId,
    oldValue: log.old_value ?? log.oldValue,
    newValue: log.new_value ?? log.newValue,
    userId: log.user_id ?? log.userId,
    user: log.user,
    createdAt: log.created_at ?? log.createdAt,
  };
}

export const insightsApi = {
  getKPI: async (): Promise<DashboardKPI> => {
    const response = await client.get<DashboardKPI>('/insights/kpi');
    return response.data;
  },

  getThroughput: async (months = 12): Promise<ThroughputData[]> => {
    const response = await client.get<ThroughputData[]>('/insights/throughput', {
      params: { months }
    });
    return response.data;
  },

  getPersonLoad: async (): Promise<PersonLoadData[]> => {
    const response = await client.get<PersonLoadData[]>('/insights/person-load');
    return response.data;
  },

  getExternalCollab: async (): Promise<ExternalCollabData[]> => {
    const response = await client.get<ExternalCollabData[]>('/insights/external-collab');
    return response.data;
  },

  getAuditLogs: async (page = 1, pageSize = 50): Promise<PaginatedResponse<AuditLog>> => {
    const response = await client.get<any>('/insights/audit-logs', {
      params: { page, page_size: pageSize }
    });
    return {
      items: response.data.items.map(normalizeAuditLog),
      total: response.data.total,
      page: response.data.page,
      pageSize: response.data.page_size ?? response.data.pageSize,
      totalPages: response.data.total_pages ?? response.data.totalPages,
    };
  },
};
