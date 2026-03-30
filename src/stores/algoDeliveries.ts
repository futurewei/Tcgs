// src/stores/algoDeliveries.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { AlgoDelivery, AlgoDeliveryCreateRequest, AlgoDeliveryUpdateRequest } from '@/types';
import { algoDeliveriesApi } from '@/api/algoDeliveries';

// Helper to get current month in YYYY-MM format
function getCurrentMonth(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
}

export const useAlgoDeliveriesStore = defineStore('algoDeliveries', () => {
  const deliveries = ref<AlgoDelivery[]>([]);
  const currentMonth = ref<string>(getCurrentMonth());
  const loading = ref(false);

  async function fetchDeliveries(month?: string) {
    loading.value = true;
    try {
      deliveries.value = await algoDeliveriesApi.list(month);
    } catch (error) {
      console.error('Failed to fetch algo deliveries:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createDelivery(data: AlgoDeliveryCreateRequest) {
    loading.value = true;
    try {
      const delivery = await algoDeliveriesApi.create(data);
      // Refresh list to get full data with relationships
      await fetchDeliveries(currentMonth.value);
      return delivery;
    } catch (error) {
      console.error('Failed to create algo delivery:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateDelivery(id: number, data: AlgoDeliveryUpdateRequest) {
    loading.value = true;
    try {
      const delivery = await algoDeliveriesApi.update(id, data);
      // Update local state
      const index = deliveries.value.findIndex(d => d.id === id);
      if (index !== -1) {
        deliveries.value[index] = delivery;
      }
      return delivery;
    } catch (error) {
      console.error('Failed to update algo delivery:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteDelivery(id: number) {
    loading.value = true;
    try {
      await algoDeliveriesApi.delete(id);
      // Remove from local state
      deliveries.value = deliveries.value.filter(d => d.id !== id);
    } catch (error) {
      console.error('Failed to delete algo delivery:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  function setCurrentMonth(month: string) {
    currentMonth.value = month;
  }

  return {
    deliveries,
    currentMonth,
    loading,
    fetchDeliveries,
    createDelivery,
    updateDelivery,
    deleteDelivery,
    setCurrentMonth,
  };
});
