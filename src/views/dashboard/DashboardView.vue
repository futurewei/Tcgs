<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Dashboard</h1>
    </div>

    <!-- 12-column grid: left 8, right 4 -->
    <div class="grid grid-cols-12 gap-4">
      <!-- Left: Topic Pools (8 columns) -->
      <div class="col-span-8 space-y-4">
        <!-- Uncertainty Topics -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">Uncertainty Topics</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ filteredUncertaintyTopics.length }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <el-radio-group v-model="uncertaintyFilter" size="small">
                <el-radio-button label="">All</el-radio-button>
                <el-radio-button label="P0">P0</el-radio-button>
                <el-radio-button label="P1">P1</el-radio-button>
                <el-radio-button label="me">DRI=me</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="max-h-[360px] overflow-y-auto p-4 space-y-2">
            <TopicRow
              v-for="topic in filteredUncertaintyTopics"
              :key="topic.id"
              :topic="topic"
              @open="openTopic"
            />
            <div v-if="filteredUncertaintyTopics.length === 0" class="text-center py-8 text-zinc-400">
              No uncertainty topics found
            </div>
          </div>
        </div>

        <!-- Evolution Projects -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">Evolution Projects</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ filteredEvolutionTopics.length }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <el-radio-group v-model="evolutionFilter" size="small">
                <el-radio-button label="">All</el-radio-button>
                <el-radio-button label="P0">P0</el-radio-button>
                <el-radio-button label="P1">P1</el-radio-button>
                <el-radio-button label="me">DRI=me</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="max-h-[360px] overflow-y-auto p-4 space-y-2">
            <TopicRow
              v-for="topic in filteredEvolutionTopics"
              :key="topic.id"
              :topic="topic"
              @open="openTopic"
            />
            <div v-if="filteredEvolutionTopics.length === 0" class="text-center py-8 text-zinc-400">
              No evolution projects found
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Capacity (4 columns) -->
      <div class="col-span-4 space-y-4">
        <!-- Algo Slots -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">Algo Slots</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ algoSlots.length }}
              </span>
            </div>
          </div>
          <div class="p-4">
            <div class="flex flex-wrap gap-2">
              <SlotChip
                v-for="slot in algoSlots"
                :key="slot.id"
                :slot="slot"
                show-percentage
              />
              <div v-if="algoSlots.length === 0" class="text-sm text-zinc-400">
                No algo slots configured
              </div>
            </div>
          </div>
        </div>

        <!-- External Slots -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">External Slots</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ externalSlots.length }}
              </span>
            </div>
            <p class="text-xs text-zinc-400 mt-1">External cannot be DRI</p>
          </div>
          <div class="p-4">
            <div class="flex flex-wrap gap-2">
              <SlotChip
                v-for="slot in externalSlots"
                :key="slot.id"
                :slot="slot"
                show-percentage
              />
              <div v-if="externalSlots.length === 0" class="text-sm text-zinc-400">
                No external slots configured
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="bg-white rounded-xl border border-zinc-200 p-4">
          <h3 class="font-semibold text-zinc-900 mb-4">Quick Stats</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">Open Topics</span>
              <span class="font-semibold text-zinc-900">{{ openTopicsCount }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">Completed</span>
              <span class="font-semibold text-emerald-600">{{ completedTopicsCount }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">Unsolvable</span>
              <span class="font-semibold text-rose-600">{{ unsolvableTopicsCount }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useCapacityStore } from '@/stores/capacity';
import { useAuthStore } from '@/stores/auth';
import TopicRow from '@/components/topic/TopicRow.vue';
import SlotChip from '@/components/common/SlotChip.vue';
import type { Topic } from '@/types';

const router = useRouter();
const topicsStore = useTopicsStore();
const capacityStore = useCapacityStore();
const authStore = useAuthStore();

const uncertaintyFilter = ref('');
const evolutionFilter = ref('');

const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

const uncertaintyTopics = computed(() =>
  topicsStore.topics.filter(t => t.type === 'UNCERTAINTY' && t.result === 'OPEN')
);

const evolutionTopics = computed(() =>
  topicsStore.topics.filter(t => t.type === 'EVOLUTION' && t.result === 'OPEN')
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
);

const filteredUncertaintyTopics = computed(() => {
  let topics = uncertaintyTopics.value;
  if (uncertaintyFilter.value === 'P0') {
    topics = topics.filter(t => t.urgency === 'P0');
  } else if (uncertaintyFilter.value === 'P1') {
    topics = topics.filter(t => t.urgency === 'P1');
  } else if (uncertaintyFilter.value === 'me') {
    topics = topics.filter(t => t.driId === authStore.user?.id);
  }
  return topics;
});

const filteredEvolutionTopics = computed(() => {
  let topics = evolutionTopics.value;
  if (evolutionFilter.value === 'P0') {
    topics = topics.filter(t => t.urgency === 'P0');
  } else if (evolutionFilter.value === 'P1') {
    topics = topics.filter(t => t.urgency === 'P1');
  } else if (evolutionFilter.value === 'me') {
    topics = topics.filter(t => t.driId === authStore.user?.id);
  }
  return topics;
});

const openTopicsCount = computed(() =>
  topicsStore.topics.filter(t => t.result === 'OPEN').length
);

const completedTopicsCount = computed(() =>
  topicsStore.topics.filter(t => t.result === 'SUCCESS').length
);

const unsolvableTopicsCount = computed(() =>
  topicsStore.topics.filter(t => t.result === 'UNSOLVABLE').length
);

function openTopic(topic: Topic) {
  router.push(`/topics/${topic.id}`);
}

onMounted(() => {
  topicsStore.fetchTopics();
  capacityStore.fetchSlots();
});
</script>
