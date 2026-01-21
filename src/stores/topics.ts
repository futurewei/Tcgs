import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Topic, TopicCreateRequest, TopicUpdateRequest, ChangeDRIRequest } from '@/types';
import { topicsApi, type TopicFilters } from '@/api/topics';
import { mockTopics } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useTopicsStore = defineStore('topics', () => {
  const topics = ref<Topic[]>([]);
  const currentTopic = ref<Topic | null>(null);
  const loading = ref(false);
  const pagination = ref({ page: 1, pageSize: 20, total: 0, totalPages: 0 });

  const uncertaintyTopics = computed(() =>
    topics.value.filter(t => t.type === 'UNCERTAINTY')
  );

  const evolutionTopics = computed(() =>
    topics.value.filter(t => t.type === 'EVOLUTION')
  );

  const openTopics = computed(() =>
    topics.value.filter(t => t.result === 'OPEN')
  );

  async function fetchTopics(filters: TopicFilters = {}) {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        let filtered = [...mockTopics];
        if (filters.type) filtered = filtered.filter(t => t.type === filters.type);
        if (filters.urgency) filtered = filtered.filter(t => t.urgency === filters.urgency);
        if (filters.result) filtered = filtered.filter(t => t.result === filters.result);
        if (filters.search) {
          const s = filters.search.toLowerCase();
          filtered = filtered.filter(t =>
            t.title.toLowerCase().includes(s) || t.id.toString() === s
          );
        }
        topics.value = filtered;
        pagination.value = { page: 1, pageSize: 20, total: filtered.length, totalPages: 1 };
        return;
      }
      const response = await topicsApi.list(filters);
      topics.value = response.items;
      pagination.value = {
        page: response.page,
        pageSize: response.pageSize,
        total: response.total,
        totalPages: response.totalPages,
      };
    } catch (error) {
      console.error('Failed to fetch topics:', error);
      topics.value = mockTopics;
      pagination.value = { page: 1, pageSize: 20, total: mockTopics.length, totalPages: 1 };
    } finally {
      loading.value = false;
    }
  }

  async function fetchTopic(id: number) {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        currentTopic.value = mockTopics.find(t => t.id === id) || null;
        return;
      }
      currentTopic.value = await topicsApi.get(id);
    } catch (error) {
      console.error('Failed to fetch topic:', error);
      currentTopic.value = mockTopics.find(t => t.id === id) || null;
    } finally {
      loading.value = false;
    }
  }

  async function createTopic(data: TopicCreateRequest) {
    loading.value = true;
    try {
      const topic = await topicsApi.create(data);
      topics.value.unshift(topic);
      return topic;
    } catch (error) {
      console.error('Failed to create topic:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateTopic(id: number, data: TopicUpdateRequest) {
    loading.value = true;
    try {
      const updated = await topicsApi.update(id, data);
      const index = topics.value.findIndex(t => t.id === id);
      if (index !== -1) {
        topics.value[index] = updated;
      }
      if (currentTopic.value?.id === id) {
        currentTopic.value = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to update topic:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteTopic(id: number) {
    loading.value = true;
    try {
      await topicsApi.delete(id);
      topics.value = topics.value.filter(t => t.id !== id);
    } catch (error) {
      console.error('Failed to delete topic:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function advanceStage(topicId: number, stageId: number) {
    loading.value = true;
    try {
      const updated = await topicsApi.advanceStage(topicId, stageId);
      if (currentTopic.value?.id === topicId) {
        currentTopic.value = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to advance stage:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function backwardStage(topicId: number, stageId: number) {
    loading.value = true;
    try {
      const updated = await topicsApi.backwardStage(topicId, stageId);
      if (currentTopic.value?.id === topicId) {
        currentTopic.value = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to go back to previous stage:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function changeDri(topicId: number, data: ChangeDRIRequest) {
    loading.value = true;
    try {
      const updated = await topicsApi.changeDri(topicId, data);
      if (currentTopic.value?.id === topicId) {
        currentTopic.value = updated;
      }
      const index = topics.value.findIndex(t => t.id === topicId);
      if (index !== -1) {
        topics.value[index] = updated;
      }
      return updated;
    } catch (error) {
      console.error('Failed to change DRI:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  function removeBindingLocal(bindingId: number) {
    for (const t of topics.value) {
      if (!t.bindings?.length) continue;
      const idx = t.bindings.findIndex((b) => b.id === bindingId);
      if (idx >= 0) {
        t.bindings.splice(idx, 1);
        return;
      }
    }
  }

  function addBindingLocal(topicId: number, binding: any) {
    const t = topics.value.find((x) => x.id === topicId);
    if (!t) return;
    if (!t.bindings) t.bindings = [];
    t.bindings.push(binding);
  }


  return {
    topics,
    currentTopic,
    loading,
    pagination,
    uncertaintyTopics,
    evolutionTopics,
    openTopics,
    fetchTopics,
    fetchTopic,
    createTopic,
    updateTopic,
    deleteTopic,
    advanceStage,
    backwardStage,
    changeDri,
    removeBindingLocal,   
    addBindingLocal,
  };
});
