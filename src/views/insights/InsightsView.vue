<template>
  <div class="insights-page">
    <div class="page-header">
      <h1 class="page-title">洞察 / 历史</h1>
      <el-date-picker
        v-model="dateRange"
        type="monthrange"
        range-separator="至"
        start-placeholder="开始月份"
        end-placeholder="结束月份"
        format="YYYY-MM"
        value-format="YYYY-MM"
      />
    </div>

    <!-- KPI Overview -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <p class="kpi-label">总课题</p>
        <p class="kpi-value">{{ kpi.totalTopics }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">进行中</p>
        <p class="kpi-value warning">{{ kpi.openTopics }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">已完成</p>
        <p class="kpi-value success">{{ kpi.successTopics }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">无法解决</p>
        <p class="kpi-value danger">{{ kpi.unsolvableTopics }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">平均周期（天）</p>
        <p class="kpi-value">{{ kpi.avgCycleDays.toFixed(1) }}</p>
      </div>
    </div>

    <!-- Throughput Trends -->
    <section class="tcgs-surface chart-section">
      <h2 class="section-title">吞吐量趋势</h2>
      <div class="throughput-chart">
        <div class="chart-bars">
          <div
            v-for="(data, index) in throughputData"
            :key="index"
            class="bar-group"
          >
            <div class="bars-stack">
              <div
                class="bar bar-closed"
                :style="{ height: `${(data.closedTopics / maxThroughput) * 180}px` }"
                :title="`已关闭: ${data.closedTopics}`"
              />
              <div
                class="bar bar-new"
                :style="{ height: `${(data.newTopics / maxThroughput) * 180}px` }"
                :title="`新建: ${data.newTopics}`"
              />
            </div>
            <span class="bar-label">{{ formatMonth(data.month) }}</span>
          </div>
        </div>
      </div>
      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-dot new"></span>
          <span class="legend-text">新建课题</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot closed"></span>
          <span class="legend-text">关闭课题</span>
        </div>
      </div>
    </section>

    <!-- Type Distribution & Completion Rate -->
    <div class="stats-grid">
      <section class="tcgs-surface">
        <h2 class="section-title">课题类型分布</h2>
        <div class="distribution-content">
          <div class="donut-chart">
            <svg class="donut-svg" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="var(--color-neutral-200)" stroke-width="20" />
              <circle
                cx="50" cy="50" r="40" fill="none"
                stroke="var(--color-warning)"
                stroke-width="20"
                :stroke-dasharray="`${uncertaintyPercent * 2.51} 251`"
                class="donut-segment"
              />
            </svg>
            <div class="donut-center">
              <span class="donut-value">{{ kpi.totalTopics }}</span>
            </div>
          </div>
          <div class="distribution-legend">
            <div class="legend-row">
              <span class="legend-dot uncertainty"></span>
              <span class="legend-text">不确定性: {{ kpi.uncertaintyCount }} ({{ uncertaintyPercent.toFixed(0) }}%)</span>
            </div>
            <div class="legend-row">
              <span class="legend-dot evolution"></span>
              <span class="legend-text">演进: {{ kpi.evolutionCount }} ({{ evolutionPercent.toFixed(0) }}%)</span>
            </div>
          </div>
        </div>
      </section>

      <section class="tcgs-surface">
        <h2 class="section-title">完成率</h2>
        <div class="completion-rates">
          <div class="rate-item">
            <div class="rate-header">
              <span class="rate-label">成功率</span>
              <span class="rate-value">{{ successRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="successRate" :show-text="false" status="success" />
          </div>
          <div class="rate-item">
            <div class="rate-header">
              <span class="rate-label">无法解决率</span>
              <span class="rate-value">{{ unsolvableRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="unsolvableRate" :show-text="false" status="exception" />
          </div>
          <div class="rate-item">
            <div class="rate-header">
              <span class="rate-label">仍在进行</span>
              <span class="rate-value">{{ openRate.toFixed(1) }}%</span>
            </div>
            <el-progress :percentage="openRate" :show-text="false" status="warning" />
          </div>
        </div>
      </section>
    </div>

    <!-- Person Load -->
    <section class="tcgs-surface">
      <h2 class="section-title">团队负载</h2>
      <el-table :data="personLoadData" v-loading="loading" class="insights-table">
        <el-table-column prop="userName" label="成员" min-width="150" />
        <el-table-column label="DRI 课题" width="120">
          <template #default="{ row }">
            <span class="table-value primary">{{ row.driTopics }}</span>
          </template>
        </el-table-column>
        <el-table-column label="协作课题" width="120">
          <template #default="{ row }">
            <span class="table-value">{{ row.collaborationTopics }}</span>
          </template>
        </el-table-column>
        <el-table-column label="负载" width="200">
          <template #default="{ row }">
            <div class="load-cell">
              <el-progress
                :percentage="Math.min(row.totalPercentage, 100)"
                :status="row.totalPercentage > 100 ? 'exception' : row.totalPercentage > 80 ? 'warning' : 'success'"
                :show-text="false"
                class="load-progress"
              />
              <span class="load-value">{{ row.totalPercentage }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="DRI/协作比" width="150">
          <template #default="{ row }">
            <div class="ratio-bar">
              <div class="ratio-dri" :style="{ width: `${(row.driTopics / (row.driTopics + row.collaborationTopics)) * 100}%` }" />
              <div class="ratio-collab" :style="{ width: `${(row.collaborationTopics / (row.driTopics + row.collaborationTopics)) * 100}%` }" />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- External Collaboration -->
    <section class="tcgs-surface">
      <h2 class="section-title">外部协作</h2>
      <el-table :data="externalCollabData" v-loading="loading" class="insights-table">
        <el-table-column prop="userName" label="外部协作方" min-width="150" />
        <el-table-column label="参与课题" width="150">
          <template #default="{ row }">
            <span class="table-value primary">{{ row.topicCount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阶段分布" min-width="300">
          <template #default="{ row }">
            <div class="stage-distribution">
              <el-tooltip v-for="(count, stage) in row.stageDistribution" :key="stage" :content="`${stage}: ${count}`">
                <div class="stage-chip" :style="{ width: `${Math.max(count * 24, 36)}px` }">{{ count }}</div>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="externalCollabData.length === 0" class="empty-state">暂无外部协作数据</p>
    </section>
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
  const max = Math.max(...throughputData.value.map(d => Math.max(d.newTopics, d.closedTopics)));
  return max || 1;
});

const uncertaintyPercent = computed(() => kpi.totalTopics ? (kpi.uncertaintyCount / kpi.totalTopics) * 100 : 0);
const evolutionPercent = computed(() => kpi.totalTopics ? (kpi.evolutionCount / kpi.totalTopics) * 100 : 0);
const successRate = computed(() => kpi.totalTopics ? (kpi.successTopics / kpi.totalTopics) * 100 : 0);
const unsolvableRate = computed(() => kpi.totalTopics ? (kpi.unsolvableTopics / kpi.totalTopics) * 100 : 0);
const openRate = computed(() => kpi.totalTopics ? (kpi.openTopics / kpi.totalTopics) * 100 : 0);

function formatMonth(month: string) {
  return dayjs(month).format('M月');
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
    // Mock data for demo
    Object.assign(kpi, {
      totalTopics: 47, openTopics: 18, successTopics: 24, unsolvableTopics: 5,
      avgCycleDays: 23.5, uncertaintyCount: 28, evolutionCount: 19,
    });
    throughputData.value = Array.from({ length: 12 }, (_, i) => ({
      month: dayjs().subtract(11 - i, 'month').format('YYYY-MM'),
      newTopics: Math.floor(Math.random() * 10) + 2,
      closedTopics: Math.floor(Math.random() * 8) + 1,
      uncertainty: Math.floor(Math.random() * 6) + 1,
      evolution: Math.floor(Math.random() * 5) + 1,
    }));
    personLoadData.value = [
      { userId: 1, userName: '陈工', driTopics: 5, collaborationTopics: 3, totalPercentage: 85 },
      { userId: 2, userName: '王工', driTopics: 4, collaborationTopics: 4, totalPercentage: 95 },
      { userId: 3, userName: '刘工', driTopics: 3, collaborationTopics: 2, totalPercentage: 60 },
      { userId: 4, userName: '张工', driTopics: 6, collaborationTopics: 1, totalPercentage: 110 },
    ];
    externalCollabData.value = [
      { userId: 10, userName: '外部供应商A', topicCount: 4, stageDistribution: { '分析': 2, '评审': 1, '测试': 1 } },
      { userId: 11, userName: '合作团队B', topicCount: 2, stageDistribution: { '定义': 1, '分析': 1 } },
    ];
  } finally {
    loading.value = false;
  }
}

onMounted(() => fetchData());
</script>


<style scoped>
.insights-page {
  padding: var(--space-6);
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-4);
}

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

.kpi-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
}

.kpi-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-1) 0;
}

.kpi-value {
  font-size: 28px;
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0;
}
.kpi-value.warning { color: var(--color-warning); }
.kpi-value.success { color: var(--color-success); }
.kpi-value.danger { color: var(--color-danger); }

/* Section */
.section-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-4) 0;
}

/* Throughput Chart */
.chart-section {
  padding: var(--space-5);
}

.throughput-chart {
  height: 220px;
  margin-bottom: var(--space-4);
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 100%;
  gap: var(--space-2);
}

.bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
}

.bars-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
}

.bar {
  width: 100%;
  min-height: 2px;
  border-radius: var(--radius-xs);
  transition: var(--transition-fast);
}

.bar-closed { background: var(--color-success); }
.bar-new { background: var(--color-neutral-300); }

.bar-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.chart-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-6);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-xs);
}
.legend-dot.new { background: var(--color-neutral-300); }
.legend-dot.closed { background: var(--color-success); }
.legend-dot.uncertainty { background: var(--color-warning); }
.legend-dot.evolution { background: var(--color-neutral-300); }

.legend-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-6);
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
}

/* Donut Chart */
.distribution-content {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.donut-chart {
  width: 120px;
  height: 120px;
  position: relative;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.donut-segment {
  transition: stroke-dasharray 0.3s ease;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-value {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
}

.distribution-legend {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.legend-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Completion Rates */
.completion-rates {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.rate-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.rate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rate-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.rate-value {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

/* Table Styles */
.insights-table {
  margin-top: var(--space-4);
}

.table-value {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
.table-value.primary {
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.load-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.load-progress {
  flex: 1;
}

.load-value {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  width: 48px;
  text-align: right;
}

.ratio-bar {
  display: flex;
  height: 16px;
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.ratio-dri { background: var(--color-primary); }
.ratio-collab { background: var(--color-neutral-300); }

.stage-distribution {
  display: flex;
  gap: 4px;
}

.stage-chip {
  height: 24px;
  background: var(--color-neutral-100);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.empty-state {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-disabled);
  font-size: var(--text-sm);
}
</style>
