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
      // 使用新的 workforce API（基于 User）
      slots.value = await capacityApi.listWorkforce(type);
    } catch (error) {
      console.error('Failed to fetch workforce:', error);
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
    } finally {
      loading.value = false;
    }
  }

  async function createBinding(data: BindingCreateRequest) {
    loading.value = true;
    try {
      const binding = await capacityApi.createBinding(data);
      await fetchBindings(lastBindingsFilter.value.topicId, lastBindingsFilter.value.slotId);
      await fetchSlots(lastType.value);
      return binding;
    } catch (error) {
      console.error('Failed to create binding:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  // ✅ 新增：更新 binding（给 upsert 用）
  async function updateBinding(id: number, data: Partial<BindingCreateRequest>) {
    loading.value = true;
    try {
      const updated = await capacityApi.updateBinding(id, data);
      await fetchBindings(lastBindingsFilter.value.topicId, lastBindingsFilter.value.slotId);
      await fetchSlots(lastType.value);
      return updated;
    } catch (error) {
      console.error('Failed to update binding:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteBinding(id: number) {
    loading.value = true;
    try {
      await capacityApi.deleteBinding(id);
      await fetchBindings(lastBindingsFilter.value.topicId, lastBindingsFilter.value.slotId);
      await fetchSlots(lastType.value);
    } catch (error) {
      console.error('Failed to delete binding:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  // ✅ 下面 2 个是 Dashboard 乐观更新需要（不发请求，只改本地）
  function removeBindingLocal(bindingId: number) {
    // 从 slots[*].bindings 删除
    for (const s of slots.value) {
      if (!s.bindings?.length) continue;
      s.bindings = s.bindings.filter((b: any) => b.id !== bindingId);
    }
    // 从 bindings 列表删除
    bindings.value = bindings.value.filter((b: any) => b.id !== bindingId);
  }

  function addBindingLocal(slotId: number, binding: any) {
    const slot = slots.value.find(s => s.id === slotId);
    if (slot) {
      slot.bindings = slot.bindings || [];
      if (!slot.bindings.some((b: any) => b.id === binding.id)) {
        slot.bindings.push(binding);
      }
    }
    if (!bindings.value.some((b: any) => b.id === binding.id)) {
      bindings.value.push(binding);
    }
  }

  // ============ Slot CRUD ============
  async function createSlot(data: SlotCreateRequest) {
    loading.value = true;
    try {
      const slot = await capacityApi.createSlot(data);
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
      const slot = await capacityApi.updateSlot(id, data);
      await fetchSlots(lastType.value);
      return slot;
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
      await fetchSlots(lastType.value);
    } catch (error) {
      console.error('Failed to delete slot:', error);
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
    fetchBindings,
    createSlot,
    updateSlot,
    deleteSlot,
    createBinding,
    updateBinding,
    deleteBinding,
    removeBindingLocal,
    addBindingLocal,
  };
});
