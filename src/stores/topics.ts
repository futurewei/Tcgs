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

function normalizeTopic(t: any) {
  return {
    ...t,
    currentStageId: t.currentStageId ?? t.current_stage_id ?? t.current_stage?.id ?? null,
    stageStates: t.stageStates ?? t.stage_states ?? [],
    stageInstances: t.stageInstances ?? t.stage_instances ?? [],
    bindings: (t.bindings ?? []).map((b: any) => ({
      ...b,
      slotId: b.slotId ?? b.slot_id,
      isDri: b.isDri ?? b.is_dri ?? false,
      topicId: b.topicId ?? b.topic_id ?? t.id,
      slot: b.slot
        ? {
            ...b.slot,
            userId: b.slot.userId ?? b.slot.user_id,
            totalCapacity: b.slot.totalCapacity ?? b.slot.total_capacity,
          }
        : null,
    })),
  };
}

// src/stores/topics.ts
async function fetchTopics(filters: any = {}) {
  loading.value = true;
  try {
    const effective = { ...filters };

    /**
     * ✅ 全站默认隐藏 已完成/无法解决：只拉 OPEN
     * - Dashboard / 其它页面调用 fetchTopics() 不传 result => 只会看到 OPEN
     * - /topics 页面想看 SUCCESS/UNSOLVABLE => 必须显式传 result
     */
    if (effective.result === undefined || effective.result === null || effective.result === '') {
      effective.result = 'OPEN';
    }

    const res = await topicsApi.list(effective);
   topics.value = (res.items ?? []).map(normalizeTopic);

    pagination.value = {
      page: res.page,
      pageSize: res.pageSize,
      total: res.total,
      totalPages: res.totalPages,
    };
  } catch (e) {
    console.error('fetchTopics failed:', e);
    throw e;
  } finally {
    loading.value = false;
  }
}
  async function fetchTopic(id: number) {
    loading.value = true;
    try {
      if (DEMO_MODE) {
          // ✅ demo 也最好 normalize（否则 demo 和真实接口字段可能不一致）
         currentTopic.value = normalizeTopic(mockTopics.find((t) => t.id === id) || null);
	 return;
      }
    currentTopic.value = normalizeTopic(await topicsApi.get(id));
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
