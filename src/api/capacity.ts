import client from './client';
import type {
  CapacitySlot,
  SlotCreateRequest,
  Binding,
  BindingCreateRequest,
  PaginatedResponse
} from '@/types';

// Normalize slot response
function normalizeSlot(s: any): CapacitySlot {
  if (!s) return s;
  return {
    ...s,
    id: s.id ?? s.slot_id,         // ✅ 兜底：workforce 返回 slot_id 时也能工作
    slotId: s.slot_id ?? s.slotId, // ✅ 保留原字段（可选）
    userId: s.user_id ?? s.userId,
    totalCapacity: s.total_capacity ?? s.totalCapacity,
    createdAt: s.created_at ?? s.createdAt,
    updatedAt: s.updated_at ?? s.updatedAt,
    bindings: Array.isArray(s.bindings) ? s.bindings.map(normalizeBinding) : [],
    user: s.user,
  };
}

function normalizeBinding(b: any): Binding {
  if (!b) return b;
  return {
    ...b,
    topicId: b.topic_id ?? b.topicId,
    slotId: b.slot_id ?? b.slotId,
    userId: b.user_id ?? b.userId,
    isForced: b.is_forced ?? b.isForced ?? false,
    isDri: b.is_dri ?? b.isDri ?? false,
    createdAt: b.created_at ?? b.createdAt,
    updatedAt: b.updated_at ?? b.updatedAt,
  };
}

export const capacityApi = {
  // Slots
  listSlots: async (type?: string): Promise<CapacitySlot[]> => {
    const response = await client.get<any[]>('/capacity/slots', {
      params: type ? { type } : undefined
    });
    return response.data.map(normalizeSlot);
  },

  getSlot: async (id: number): Promise<CapacitySlot> => {
    const response = await client.get<any>(`/capacity/slots/${id}`);
    return normalizeSlot(response.data);
  },

  createSlot: async (data: SlotCreateRequest): Promise<CapacitySlot> => {
    // Convert to snake_case
    const payload: any = {
      name: data.name,
      type: data.type,
      total_capacity: data.totalCapacity,
    };
    if (data.userId !== undefined) payload.user_id = data.userId;
    
    const response = await client.post<any>('/capacity/slots', payload);
    return normalizeSlot(response.data);
  },

  updateSlot: async (id: number, data: Partial<SlotCreateRequest>): Promise<CapacitySlot> => {
    // Convert to snake_case
    const payload: any = {};
    if (data.name !== undefined) payload.name = data.name;
    if (data.type !== undefined) payload.type = data.type;
    if (data.totalCapacity !== undefined) payload.total_capacity = data.totalCapacity;
    if (data.userId !== undefined) payload.user_id = data.userId;
    
    const response = await client.put<any>(`/capacity/slots/${id}`, payload);
    return normalizeSlot(response.data);
  },

  deleteSlot: async (id: number): Promise<void> => {
    await client.delete(`/capacity/slots/${id}`);
  },

  // Bindings
  listBindings: async (topicId?: number, slotId?: number): Promise<Binding[]> => {
    const params: any = {};
    if (topicId !== undefined) params.topic_id = topicId;
    if (slotId !== undefined) params.slot_id = slotId;
    
    const response = await client.get<any[]>('/capacity/bindings', { params });
    return response.data.map(normalizeBinding);
  },

  createBinding: async (data: BindingCreateRequest): Promise<Binding> => {
    // Convert to snake_case for backend
    const payload: any = {
      topic_id: data.topicId,
      percentage: data.percentage,
    };
    // 支持新的 user_id 方式
    if (data.userId !== undefined) payload.user_id = data.userId;
    if (data.slotId !== undefined) payload.slot_id = data.slotId;
    if (data.isForced !== undefined) payload.is_forced = data.isForced;
    if (data.isDri !== undefined) payload.is_dri = data.isDri;
    
    const response = await client.post<any>('/capacity/bindings', payload);
    return normalizeBinding(response.data);
  },

  updateBinding: async (id: number, data: Partial<BindingCreateRequest>): Promise<Binding> => {
    // Convert to snake_case
    const payload: any = {};
    if (data.percentage !== undefined) payload.percentage = data.percentage;
    if (data.isForced !== undefined) payload.is_forced = data.isForced;
    if (data.isDri !== undefined) payload.is_dri = data.isDri;
    
    const response = await client.put<any>(`/capacity/bindings/${id}`, payload);
    return normalizeBinding(response.data);
  },

  deleteBinding: async (id: number): Promise<void> => {
    await client.delete(`/capacity/bindings/${id}`);
  },

  forceBinding: async (id: number, data: BindingCreateRequest): Promise<Binding> => {
    const payload: any = {
      topic_id: data.topicId,
      slot_id: data.slotId,
      percentage: data.percentage,
    };
    if (data.isForced !== undefined) payload.is_forced = data.isForced;
    
    const response = await client.post<any>(`/capacity/bindings/${id}/force`, payload);
    return normalizeBinding(response.data);
  },

  // 新的 workforce API（基于 User）
  listWorkforce: async (type?: string): Promise<CapacitySlot[]> => {
    const response = await client.get<any[]>('/capacity/workforce', {
      params: type ? { type } : undefined
    });
    return response.data.map(normalizeSlot);
  },
};
