import client from './client';
import type {
  AlgoDelivery,
  AlgoDeliveryCreateRequest,
  AlgoDeliveryUpdateRequest,
} from '@/types';

// Normalize response from snake_case to camelCase
function normalizeDelivery(d: any): AlgoDelivery {
  if (!d) return d;
  return {
    id: d.id,
    month: d.month,
    capabilityName: d.capability_name ?? d.capabilityName,
    archiveUrl: d.archive_url ?? d.archiveUrl,
    upgradeDescription: d.upgrade_description ?? d.upgradeDescription,
    videoUrl: d.video_url ?? d.videoUrl,
    ownerId: d.owner_id ?? d.ownerId,
    owner: d.owner,
    delivered: d.delivered ?? false,
    deliveredAt: d.delivered_at ?? d.deliveredAt,
    deliveredById: d.delivered_by_id ?? d.deliveredById,
    deliveredBy: d.delivered_by ?? d.deliveredBy,
    createdById: d.created_by_id ?? d.createdById,
    createdBy: d.created_by ?? d.createdBy,
    createdAt: d.created_at ?? d.createdAt,
    updatedAt: d.updated_at ?? d.updatedAt,
  };
}

export const algoDeliveriesApi = {
  // List deliveries, optionally filtered by month
  list: async (month?: string): Promise<AlgoDelivery[]> => {
    const response = await client.get<any[]>('/algo-deliveries', {
      params: month ? { month } : undefined,
    });
    return response.data.map(normalizeDelivery);
  },

  // Get a single delivery by ID
  get: async (id: number): Promise<AlgoDelivery> => {
    const response = await client.get<any>(`/algo-deliveries/${id}`);
    return normalizeDelivery(response.data);
  },

  // Create a new delivery
  create: async (data: AlgoDeliveryCreateRequest): Promise<AlgoDelivery> => {
    const payload = {
      month: data.month,
      capability_name: data.capabilityName,
      archive_url: data.archiveUrl,
      upgrade_description: data.upgradeDescription,
      video_url: data.videoUrl,
      owner_id: data.ownerId,
    };
    const response = await client.post<any>('/algo-deliveries', payload);
    return normalizeDelivery(response.data);
  },

  // Update a delivery
  update: async (id: number, data: AlgoDeliveryUpdateRequest): Promise<AlgoDelivery> => {
    const payload: any = {};
    if (data.capabilityName !== undefined) payload.capability_name = data.capabilityName;
    if (data.archiveUrl !== undefined) payload.archive_url = data.archiveUrl;
    if (data.upgradeDescription !== undefined) payload.upgrade_description = data.upgradeDescription;
    if (data.videoUrl !== undefined) payload.video_url = data.videoUrl;
    if (data.ownerId !== undefined) payload.owner_id = data.ownerId;
    if (data.delivered !== undefined) payload.delivered = data.delivered;

    const response = await client.put<any>(`/algo-deliveries/${id}`, payload);
    return normalizeDelivery(response.data);
  },

  // Delete a delivery
  delete: async (id: number): Promise<void> => {
    await client.delete(`/algo-deliveries/${id}`);
  },
};
