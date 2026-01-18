import client from './client';
import type {
  DashboardKPI,
  ThroughputData,
  PersonLoadData,
  ExternalCollabData,
  AuditLog,
  PaginatedResponse
} from '@/types';

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
    const response = await client.get<PaginatedResponse<AuditLog>>('/audit-logs', {
      params: { page, pageSize }
    });
    return response.data;
  },
};
