// src/stores/capacity.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CapacitySlot, Binding, SlotCreateRequest, BindingCreateRequest } from '@/types';
import { capacityApi } from '@/api/capacity';
import { mockSlots } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useCapacityStore = defineStore('capacity', () => {
  const slots = ref<CapacitySlot[]>([]);
  const bindings = ref<Binding[]>([]);
  const loading = ref(false);

  // remember last filters so "refresh after mutation" keeps current view
  const lastType = ref<string | undefined>(undefined);
  const lastBindingsFilter = ref<{ topicId?: number; slotId?: number }>({});

  const algoSlots = computed(() => slots.value.filter(s => s.type === 'ALGO'));
  const externalSlots = computed(() => slots.value.filter(s => s.type === 'EXTERNAL'));

  function getSlotStatus(slot: CapacitySlot) {
    const totalUsed = slot.bindings?.reduce((sum, b) => sum + b.percentage, 0) || 0;
    if (totalUsed === 0) return 'available';
    if (totalUsed >= 100) return 'occupied';
    return 'partial';
  }

  function getSlotUsage(slot: CapacitySlot) {
    return slot.bindings?.reduce((sum, b) => sum + b.percentage, 0) || 0;
  }

  async function fetchSlots(type?: string) {
    loading.value = true;
    lastType.value = type;
    try {
      if (DEMO_MODE) {
        let filtered = [...mockSlots];
        if (type) filtered = filtered.filter(s => s.type === type);
        slots.value = filtered;
        return;
      }

      // backend
      slots.value = await capacityApi.listSlots(type);
    } catch (error) {
      console.error('Failed to fetch slots:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createSlot(data: SlotCreateRequest) {
    loading.value = true;
    try {
      const slot = await capacityApi.createSlot(data);

      // refresh from backend to keep UI consistent
      await fetchSlots(lastType.value);

      return slot;
    } catch (error) {
      console.error('Failed to create slot:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateSlot(id: number, data: Partial<SlotCreateRequest>) {
    loading.value = true;
    try {
      const updated = await capacityApi.updateSlot(id, data);

      // refresh from backend to keep UI consistent
      await fetchSlots(lastType.value);

      return updated;
    } catch (error) {
      console.error('Failed to update slot:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteSlot(id: number) {
    loading.value = true;
    try {
      await capacityApi.deleteSlot(id);

      // refresh from backend to keep UI consistent
      await fetchSlots(lastType.value);
    } catch (error) {
      console.error('Failed to delete slot:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBindings(topicId?: number, slotId?: number) {
    loading.value = true;
    lastBindingsFilter.value = { topicId, slotId };
    try {
      bindings.value = await capacityApi.listBindings(topicId, slotId);
    } catch (error) {
      console.error('Failed to fetch bindings:', error);
      // 这里不 throw，避免某些页面绑定列表挂了导致整个页面不可用
    } finally {
      loading.value = false;
    }
  }

  async function createBinding(data: BindingCreateRequest) {
    loading.value = true;
    try {
      const binding = await capacityApi.createBinding(data);

      // refresh bindings list (keep current filter)
      await fetchBindings(lastBindingsFilter.value.topicId, lastBindingsFilter.value.slotId);

      // refresh slots because slot.bindings / usage changes
      await fetchSlots(lastType.value);

      return binding;
    } catch (error) {
      console.error('Failed to create binding:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteBinding(id: number) {
    loading.value = true;
    try {
      await capacityApi.deleteBinding(id);

      // refresh bindings list (keep current filter)
      await fetchBindings(lastBindingsFilter.value.topicId, lastBindingsFilter.value.slotId);

      // refresh slots because slot.bindings / usage changes
      await fetchSlots(lastType.value);
    } catch (error) {
      console.error('Failed to delete binding:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  return {
    slots,
    bindings,
    loading,
    algoSlots,
    externalSlots,
    getSlotStatus,
    getSlotUsage,
    fetchSlots,
    createSlot,
    updateSlot,
    deleteSlot,
    fetchBindings,
    createBinding,
    deleteBinding,
  };
});
