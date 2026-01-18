import client from './client';
import type {
  CapacitySlot,
  SlotCreateRequest,
  Binding,
  BindingCreateRequest,
  PaginatedResponse
} from '@/types';

export const capacityApi = {
  // Slots
  listSlots: async (type?: string): Promise<CapacitySlot[]> => {
    const response = await client.get<CapacitySlot[]>('/capacity/slots', {
      params: type ? { type } : undefined
    });
    return response.data;
  },

  getSlot: async (id: number): Promise<CapacitySlot> => {
    const response = await client.get<CapacitySlot>(`/capacity/slots/${id}`);
    return response.data;
  },

  createSlot: async (data: SlotCreateRequest): Promise<CapacitySlot> => {
    const response = await client.post<CapacitySlot>('/capacity/slots', data);
    return response.data;
  },

  updateSlot: async (id: number, data: Partial<SlotCreateRequest>): Promise<CapacitySlot> => {
    const response = await client.put<CapacitySlot>(`/capacity/slots/${id}`, data);
    return response.data;
  },

  deleteSlot: async (id: number): Promise<void> => {
    await client.delete(`/capacity/slots/${id}`);
  },

  // Bindings
  listBindings: async (topicId?: number, slotId?: number): Promise<Binding[]> => {
    const response = await client.get<Binding[]>('/capacity/bindings', {
      params: { topicId, slotId }
    });
    return response.data;
  },

  createBinding: async (data: BindingCreateRequest): Promise<Binding> => {
    const response = await client.post<Binding>('/capacity/bindings', data);
    return response.data;
  },

  updateBinding: async (id: number, data: Partial<BindingCreateRequest>): Promise<Binding> => {
    const response = await client.put<Binding>(`/capacity/bindings/${id}`, data);
    return response.data;
  },

  deleteBinding: async (id: number): Promise<void> => {
    await client.delete(`/capacity/bindings/${id}`);
  },

  forceBinding: async (id: number, data: BindingCreateRequest): Promise<Binding> => {
    const response = await client.post<Binding>(`/capacity/bindings/${id}/force`, data);
    return response.data;
  },
};
