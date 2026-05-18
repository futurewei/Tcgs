import { defineStore } from 'pinia';
import { ref } from 'vue';
import type {
  Capability,
  CapabilityCreateRequest,
  CapabilityUpdateRequest,
  CapabilityStats,
} from '@/types';
import { capabilitiesApi } from '@/api/capabilities';

export const useCapabilitiesStore = defineStore('capabilities', () => {
  const capabilities = ref<Capability[]>([]);
  const stats = ref<CapabilityStats | null>(null);
  const loading = ref(false);
  const currentCapability = ref<Capability | null>(null);
  const detailLoading = ref(false);

  async function fetchCapabilities(params?: Record<string, any>) {
    loading.value = true;
    try {
      capabilities.value = await capabilitiesApi.list(params);
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchStats() {
    try {
      stats.value = await capabilitiesApi.getStats();
    } catch (error) {
      console.error('Failed to fetch capability stats:', error);
    }
  }

  async function fetchCapability(id: number) {
    detailLoading.value = true;
    try {
      currentCapability.value = await capabilitiesApi.get(id);
      return currentCapability.value;
    } catch (error) {
      console.error('Failed to fetch capability:', error);
      throw error;
    } finally {
      detailLoading.value = false;
    }
  }

  async function createCapability(data: CapabilityCreateRequest) {
    try {
      const cap = await capabilitiesApi.create(data);
      await fetchCapabilities();
      await fetchStats();
      return cap;
    } catch (error) {
      console.error('Failed to create capability:', error);
      throw error;
    }
  }

  async function updateCapability(id: number, data: CapabilityUpdateRequest) {
    try {
      const cap = await capabilitiesApi.update(id, data);
      // Update in local state
      const idx = capabilities.value.findIndex((c) => c.id === id);
      if (idx !== -1) {
        capabilities.value[idx] = cap;
      }
      if (currentCapability.value?.id === id) {
        currentCapability.value = cap;
      }
      return cap;
    } catch (error) {
      console.error('Failed to update capability:', error);
      throw error;
    }
  }

  async function deleteCapability(id: number) {
    try {
      await capabilitiesApi.delete(id);
      capabilities.value = capabilities.value.filter((c) => c.id !== id);
      if (currentCapability.value?.id === id) {
        currentCapability.value = null;
      }
      await fetchStats();
    } catch (error) {
      console.error('Failed to delete capability:', error);
      throw error;
    }
  }

  return {
    capabilities,
    stats,
    loading,
    currentCapability,
    detailLoading,
    fetchCapabilities,
    fetchStats,
    fetchCapability,
    createCapability,
    updateCapability,
    deleteCapability,
  };
});
