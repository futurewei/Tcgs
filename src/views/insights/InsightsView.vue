<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Insights / History</h1>
      <el-date-picker
        v-model="dateRange"
        type="monthrange"
        range-separator="to"
        start-placeholder="Start month"
        end-placeholder="End month"
        format="YYYY-MM"
        value-format="YYYY-MM"
      />
    </div>

    <!-- KPI Overview -->
    <div class="grid grid-cols-5 gap-4">
      <div class="bg-white rounded-xl border border-zinc-200 p-5">
        <p class="text-sm text-zinc-500 mb-1">Total Topics</p>
        <p class="text-3xl font-bold text-zinc-900">{{ kpi.totalTopics }}</p>
      </div>
      <div class="bg-white rounded-xl border border-zinc-200 p-5">
        <p class="text-sm text-zinc-500 mb-1">Open</p>
        <p class="text-3xl font-bold text-amber-600">{{ kpi.openTopics }}</p>
      </div>
      <div class="bg-white rounded-xl border border-zinc-200 p-5">
        <p class="text-sm text-zinc-500 mb-1">Success</p>
        <p class="text-3xl font-bold text-emerald-600">{{ kpi.successTopics }}</p>
      </div>
      <div class="bg-white rounded-xl border border-zinc-200 p-5">
        <p class="text-sm text-zinc-500 mb-1">Unsolvable</p>
        <p class="text-3xl font-bold text-rose-600">{{ kpi.unsolvableTopics }}</p>
      </div>
      <div class="bg-white rounded-xl border border-zinc-200 p-5">
        <p class="text-sm text-zinc-500 mb-1">Avg. Cycle (days)</p>
        <p class="text-3xl font-bold text-zinc-900">{{ kpi.avgCycleDays.toFixed(1) }}</p>
      </div>
    </div>

    <!-- Throughput Trends -->
    <div class="bg-white rounded-xl border border-zinc-200 p-6">
      <h2 class="font-semibold text-zinc-900 mb-4">Throughput Trends</h2>
      <div class="h-[300px]">
        <div class="flex items-end justify-between h-full gap-2">
          <div
            v-for="(data, index) in throughputData"
            :key="index"
            class="flex-1 flex flex-col items-center gap-1"
          >
            <div class="w-full flex flex-col gap-1">
              <div
                class="w-full bg-emerald-500 rounded-t"
                :style="{ height: `${(data.closedTopics / maxThroughput) * 200}px` }"
                :title="`Closed: ${data.closedTopics}`"
              />
              <div
                class="w-full bg-zinc-300 rounded-b"
                :style="{ height: `${(data.newTopics / maxThroughput) * 200}px` }"
                :title="`New: ${data.newTopics}`"
              />
            </div>
            <span class="text-xs text-zinc-500 mt-2">{{ formatMonth(data.month) }}</span>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-center gap-6 mt-4">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 bg-zinc-300 rounded" />
          <span class="text-sm text-zinc-600">New Topics</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 bg-emerald-500 rounded" />
          <span class="text-sm text-zinc-600">Closed Topics</span>
        </div>
      </div>
    </div>

    <!-- Type Distribution -->
    <div class="grid grid-cols-2 gap-6">
      <div class="bg-white rounded-xl border border-zinc-200 p-6">
        <h2 class="font-semibold text-zinc-900 mb-4">Topic Type Distribution</h2>
        <div class="flex items-center gap-8">
          <div class="w-32 h-32 relative">
            <svg class="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#e4e4e7"
                stroke-width="20"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#f59e0b"
                stroke-width="20"
                :stroke-dasharray="`${uncertaintyPercent * 2.51} 251`"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-lg font-bold">{{ kpi.totalTopics }}</span>
            </div>
          </div>
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 bg-amber-500 rounded" />
              <span class="text-sm">Uncertainty: {{ kpi.uncertaintyCount }} ({{ uncertaintyPercent.toFixed(0) }}%)</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 bg-zinc-300 rounded" />
              <span class="text-sm">Evolution: {{ kpi.evolutionCount }} ({{ evolutionPercent.toFixed(0) }}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-zinc-200 p-6">
        <h2 class="font-semibold text-zinc-900 mb-4">Completion Rate</h2>
        <div class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-zinc-600">Success Rate</span>
              <span class="font-medium">{{ successRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="successRate" :show-text="false" status="success" />
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-zinc-600">Unsolvable Rate</span>
              <span class="font-medium">{{ unsolvableRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="unsolvableRate" :show-text="false" status="exception" />
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-zinc-600">Still Open</span>
              <span class="font-medium">{{ openRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="openRate" :show-text="false" status="warning" />
          </div>
        </div>
      </div>
    </div>

    <!-- Person Load (Algo Team) -->
    <div class="bg-white rounded-xl border border-zinc-200 p-6">
      <h2 class="font-semibold text-zinc-900 mb-4">Algo Team Load</h2>
      <el-table :data="personLoadData" v-loading="loading">
        <el-table-column prop="userName" label="Person" min-width="150" />
        <el-table-column label="DRI Topics" width="120">
          <template #default="{ row }">
            <span class="font-medium">{{ row.driTopics }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Collaboration" width="120">
          <template #default="{ row }">
            <span>{{ row.collaborationTopics }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Load %" width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-progress
                :percentage="Math.min(row.totalPercentage, 100)"
                :status="row.totalPercentage > 100 ? 'exception' : row.totalPercentage > 80 ? 'warning' : 'success'"
                :show-text="false"
                class="flex-1"
              />
              <span class="text-sm font-medium w-12 text-right">{{ row.totalPercentage }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="DRI vs Collab" width="150">
          <template #default="{ row }">
            <div class="flex h-4 rounded overflow-hidden">
              <div
                class="bg-zinc-700"
                :style="{ width: `${(row.driTopics / (row.driTopics + row.collaborationTopics)) * 100}%` }"
              />
              <div
                class="bg-zinc-300"
                :style="{ width: `${(row.collaborationTopics / (row.driTopics + row.collaborationTopics)) * 100}%` }"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- External Collaboration -->
    <div class="bg-white rounded-xl border border-zinc-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-zinc-900">External Collaboration</h2>
        <el-tag type="info" size="small">External cannot be DRI</el-tag>
      </div>
      <el-table :data="externalCollabData" v-loading="loading">
        <el-table-column prop="userName" label="External Collaborator" min-width="150" />
        <el-table-column label="Topics Involved" width="150">
          <template #default="{ row }">
            <span class="font-medium">{{ row.topicCount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Stage Distribution" min-width="300">
          <template #default="{ row }">
            <div class="flex gap-1">
              <el-tooltip
                v-for="(count, stage) in row.stageDistribution"
                :key="stage"
                :content="`${stage}: ${count}`"
              >
                <div
                  class="h-6 bg-zinc-200 rounded flex items-center justify-center text-xs"
                  :style="{ width: `${Math.max(count * 20, 30)}px` }"
                >
                  {{ count }}
                </div>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="externalCollabData.length === 0" class="text-center py-8 text-zinc-400">
        No external collaboration data
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { insightsApi } from '@/api/insights';
import type { DashboardKPI, ThroughputData, PersonLoadData, ExternalCollabData } from '@/types';
import dayjs from 'dayjs';

const loading = ref(false);
const dateRange = ref<[string, string] | null>(null);

const kpi = reactive<DashboardKPI>({
  totalTopics: 0,
  openTopics: 0,
  successTopics: 0,
  unsolvableTopics: 0,
  avgCycleDays: 0,
  uncertaintyCount: 0,
  evolutionCount: 0,
});

const throughputData = ref<ThroughputData[]>([]);
const personLoadData = ref<PersonLoadData[]>([]);
const externalCollabData = ref<ExternalCollabData[]>([]);

const maxThroughput = computed(() => {
  const max = Math.max(
    ...throughputData.value.map(d => Math.max(d.newTopics, d.closedTopics))
  );
  return max || 1;
});

const uncertaintyPercent = computed(() =>
  kpi.totalTopics ? (kpi.uncertaintyCount / kpi.totalTopics) * 100 : 0
);

const evolutionPercent = computed(() =>
  kpi.totalTopics ? (kpi.evolutionCount / kpi.totalTopics) * 100 : 0
);

const successRate = computed(() =>
  kpi.totalTopics ? (kpi.successTopics / kpi.totalTopics) * 100 : 0
);

const unsolvableRate = computed(() =>
  kpi.totalTopics ? (kpi.unsolvableTopics / kpi.totalTopics) * 100 : 0
);

const openRate = computed(() =>
  kpi.totalTopics ? (kpi.openTopics / kpi.totalTopics) * 100 : 0
);

function formatMonth(month: string) {
  return dayjs(month).format('MMM');
}

async function fetchData() {
  loading.value = true;
  try {
    const [kpiData, throughput, personLoad, externalCollab] = await Promise.all([
      insightsApi.getKPI(),
      insightsApi.getThroughput(12),
      insightsApi.getPersonLoad(),
      insightsApi.getExternalCollab(),
    ]);

    Object.assign(kpi, kpiData);
    throughputData.value = throughput;
    personLoadData.value = personLoad;
    externalCollabData.value = externalCollab;
  } catch (error) {
    console.error('Failed to fetch insights:', error);
    // Use mock data for demo
    Object.assign(kpi, {
      totalTopics: 47,
      openTopics: 18,
      successTopics: 24,
      unsolvableTopics: 5,
      avgCycleDays: 23.5,
      uncertaintyCount: 28,
      evolutionCount: 19,
    });

    throughputData.value = Array.from({ length: 12 }, (_, i) => ({
      month: dayjs().subtract(11 - i, 'month').format('YYYY-MM'),
      newTopics: Math.floor(Math.random() * 10) + 2,
      closedTopics: Math.floor(Math.random() * 8) + 1,
      uncertainty: Math.floor(Math.random() * 6) + 1,
      evolution: Math.floor(Math.random() * 5) + 1,
    }));

    personLoadData.value = [
      { userId: 1, userName: 'Alice Chen', driTopics: 5, collaborationTopics: 3, totalPercentage: 85 },
      { userId: 2, userName: 'Bob Wang', driTopics: 4, collaborationTopics: 4, totalPercentage: 95 },
      { userId: 3, userName: 'Charlie Liu', driTopics: 3, collaborationTopics: 2, totalPercentage: 60 },
      { userId: 4, userName: 'Diana Zhang', driTopics: 6, collaborationTopics: 1, totalPercentage: 110 },
    ];

    externalCollabData.value = [
      { userId: 10, userName: 'External Vendor A', topicCount: 4, stageDistribution: { 'Analysis': 2, 'Review': 1, 'Testing': 1 } },
      { userId: 11, userName: 'Partner Team B', topicCount: 2, stageDistribution: { 'Definition': 1, 'Analysis': 1 } },
    ];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchData();
});
</script>
