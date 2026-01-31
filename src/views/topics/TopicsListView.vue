<template>
  <div class="topics-page">
    <!-- Page Header -->
    <div class="page-header">
      <h1 class="page-title">课题管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showCreateDialog = true">
        创建课题
      </el-button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-input
        v-model="filters.search"
        placeholder="搜索课题名称或编号..."
        class="filter-search"
        clearable
        @input="debouncedFetch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select v-model="filters.type" class="filter-item" placeholder="类型" clearable @change="fetchTopics">
        <el-option label="不确定性" value="UNCERTAINTY" />
        <el-option label="演进" value="EVOLUTION" />
      </el-select>

      <el-select v-model="filters.urgency" class="filter-item" placeholder="优先级" clearable @change="fetchTopics">
        <el-option label="P0 - 紧急" value="P0" />
        <el-option label="P1 - 高" value="P1" />
        <el-option label="P2 - 中" value="P2" />
        <el-option label="P3 - 低" value="P3" />
      </el-select>

      <el-select v-model="filters.result" class="filter-item" placeholder="结果" clearable @change="fetchTopics">
        <el-option label="进行中" value="OPEN" />
        <el-option label="已完成" value="SUCCESS" />
        <el-option label="无法解决" value="UNSOLVABLE" />
      </el-select>

      <el-button class="filter-reset" @click="resetFilters">重置</el-button>
    </div>

    <!-- Topics List -->
    <div class="topics-list">
      <div
        v-for="topic in topicsStore.topics"
        :key="topic.id"
        class="topic-card"
        @click="openTopic(topic)"
      >
        <div class="topic-card-main">
          <!-- Left: Main content -->
          <div class="topic-card-content">
            <div class="topic-card-header">
              <h3 class="topic-card-title">{{ topic.title }}</h3>

              <span
                :class="['priority-tag', `priority-tag--${(topic.urgency || '').toLowerCase()}`]"
              >
                {{ topic.urgency }}
              </span>

              <span class="type-tag">{{ getTypeLabel(topic.type) }}</span>

              <span
                :class="['result-tag', `result-tag--${(topic.result || '').toLowerCase()}`]"
              >
                {{ getResultLabel(topic.result) }}
              </span>
            </div>

            <p class="topic-card-meta">
              <span>ID: {{ topic.id }}</span>
              <span v-if="getRequesterName(topic)">需求方: {{ getRequesterName(topic) }}</span>
            </p>

            <!-- Stage Timeline -->
            <div v-if="topic.type === 'UNCERTAINTY'" class="topic-stages">
              <template v-if="getStageInstances(topic).length">
                <template v-for="(stage, idx) in getStageInstances(topic)" :key="stage.id">
                  <div :class="['stage-chip', `stage-chip--${stage.status}`]">
                    {{ stage.name }}
                    <span v-if="stage.status === 'done'" class="stage-icon">✓</span>
                    <span v-if="stage.status === 'active'" class="stage-dot"></span>
                  </div>
                  <span v-if="idx < getStageInstances(topic).length - 1" class="stage-arrow">→</span>
                </template>
              </template>
              <span v-else class="empty-hint">暂无阶段</span>
            </div>

            <StageTimeline
              v-else
              :stages="topic.template?.stages || []"
              :stage-states="topic.stageStates"
              :current-stage-id="topic.currentStageId"
              compact
            />
          </div>

          <!-- Right: DRI Card -->
          <div class="dri-card-wrapper" @click.stop>
            <router-link
              v-if="getDriBinding(topic)"
              :to="getSlotProfileLink(getDriBinding(topic)?.slot)"
              class="dri-card"
            >
              <p class="dri-card-label">算法责任人</p>
              <div class="dri-card-content">
                <div class="dri-avatar">{{ getInitials(getDriBinding(topic)?.slot?.name) }}</div>
                <div class="dri-info">
                  <p class="dri-name">{{ getDriBinding(topic)?.slot?.name }}</p>
                  <p class="dri-type">
                    {{ getDriBinding(topic)?.slot?.type === 'EXTERNAL' ? '协调人力' : '自有人力' }}
                  </p>
                </div>
              </div>
            </router-link>

            <div v-else class="dri-card dri-card--empty">
              <p class="dri-card-label">算法责任人</p>
              <p class="dri-empty-text">暂未分配</p>
            </div>
          </div>
        </div>

        <!-- Team Members -->
        <div v-if="getTeamBindings(topic).length" class="team-row">
          <span class="team-label">团队:</span>
          <div class="team-avatars">
            <router-link
              v-for="b in getTeamBindings(topic).slice(0, 6)"
              :key="b.id"
              :to="getSlotProfileLink(b.slot)"
              class="team-avatar"
              :title="(b.slot?.name || '') + ' - 点击查看档案'"
              @click.stop
            >
              {{ getInitials(b.slot?.name) }}
            </router-link>

            <div v-if="getTeamBindings(topic).length > 6" class="team-avatar team-avatar--more">
              +{{ getTeamBindings(topic).length - 6 }}
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!topicsStore.loading && topicsStore.topics.length === 0" class="empty-state">
        <p class="empty-title">暂无课题</p>
        <p class="empty-hint">点击“创建课题”开始</p>
      </div>

      <!-- Loading -->
      <div v-if="topicsStore.loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="topicsStore.pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchTopics"
        @current-change="fetchTopics"
      />
    </div>

    <CreateTopicDialog v-model="showCreateDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useAuthStore } from '@/stores/auth';
import { Search, Loading } from '@element-plus/icons-vue';
import StageTimeline from '@/components/topic/StageTimeline.vue';
import CreateTopicDialog from '@/components/topic/CreateTopicDialog.vue';
import type { Topic, Binding } from '@/types';

const router = useRouter();
const route = useRoute();
const topicsStore = useTopicsStore();
const authStore = useAuthStore();

const showCreateDialog = ref(false);

const filters = reactive({
  search: (route.query.search as string) || '',
  type: '',
  urgency: '',
  result: '',
});

const pagination = reactive({
  page: 1,
  pageSize: 20,
});

let debounceTimer: ReturnType<typeof setTimeout>;

function debouncedFetch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchTopics(), 300);
}

function fetchTopics() {
  topicsStore.fetchTopics({
    search: filters.search || undefined,
    type: filters.type || undefined,
    urgency: filters.urgency || undefined,
    result: filters.result || undefined,
    page: pagination.page,
    pageSize: pagination.pageSize,
  });
}

function resetFilters() {
  filters.search = '';
  filters.type = '';
  filters.urgency = '';
  filters.result = '';
  pagination.page = 1;
  fetchTopics();
}

function openTopic(topic: Topic) {
  router.push(`/topics/${topic.id}`);
}

function getTypeLabel(type: string) {
  return type === 'UNCERTAINTY' ? '不确定性' : '演进';
}

function getResultLabel(result: string) {
  switch (result) {
    case 'SUCCESS':
      return '已完成';
    case 'UNSOLVABLE':
      return '无法解决';
    default:
      return '进行中';
  }
}

function getRequesterName(topic: any) {
  return topic.requesterName ?? topic.requester_name ?? '';
}

function getInitials(name?: string) {
  if (!name) return '?';
  return name.slice(0, 2);
}

function getStageInstances(topic: any): any[] {
  const instances = topic.stageInstances ?? topic.stage_instances ?? [];
  return instances
    .map((s: any) => ({ id: s.id, name: s.name, status: s.status, order: s.order ?? 0 }))
    .sort((a: any, b: any) => a.order - b.order);
}

/**
 * ✅ 关键修复：只认真的 DRI，不要 fallback 到 bindings[0]
 * 否则会出现“我没选王五，最后 DRI 变王五”的假象
 */
function getDriBinding(topic: any): Binding | null {
  const bindings = topic.bindings || [];
  const dri = bindings.find((b: any) => b.isDri || b.is_dri);
  return dri ? normalizeBinding(dri) : null;
}

function getTeamBindings(topic: any): Binding[] {
  const bindings = topic.bindings || [];
  return bindings.filter((b: any) => !(b.isDri || b.is_dri)).map(normalizeBinding);
}

function normalizeBinding(b: any): Binding {
  return {
    ...b,
    slotId: b.slotId ?? b.slot_id,
    isDri: b.isDri ?? b.is_dri ?? false,
    slot: b.slot
      ? {
          ...b.slot,
          userId: b.slot.userId ?? b.slot.user_id,
          totalCapacity: b.slot.totalCapacity ?? b.slot.total_capacity,
        }
      : null,
  };
}

function getSlotProfileLink(slot: any): string {
  if (!slot) return '#';
  const userId = slot.userId ?? slot.user_id;
  if (userId) return `/profile/user/${userId}`;
  return `/profile/slot/${slot.id}`;
}

onMounted(() => {
  fetchTopics();
});
</script>

<style scoped>
.topics-page {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

/* ✅ 修复：搜索框被挤压 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  padding: var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
}

.filter-search {
  flex: 1 1 360px;
  min-width: 320px;
}

.filter-item {
  width: 160px;
}

.filter-reset {
  flex: 0 0 auto;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.topic-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  cursor: pointer;
  transition: var(--transition-fast);
}

.topic-card:hover {
  border-color: var(--color-border-emphasis);
  box-shadow: var(--shadow-sm);
}

.topic-card-main {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: var(--space-6);
  align-items: start;
}

.topic-card-content {
  min-width: 0;
}

.topic-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-bottom: var(--space-2);
}

.topic-card-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
  margin-right: var(--space-2);
}

.topic-card-meta {
  display: flex;
  gap: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-3) 0;
}

.priority-tag,
.type-tag,
.result-tag {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-secondary);
  background: var(--color-neutral-50);
}

.priority-tag--p0 { background: var(--color-danger-bg); color: var(--color-danger); border-color: transparent; }
.priority-tag--p1 { background: var(--color-warning-bg); color: var(--color-warning); border-color: transparent; }
.priority-tag--p2 { background: var(--color-info-bg); color: var(--color-info-text); border-color: transparent; }
.priority-tag--p3 { background: var(--color-neutral-100); color: var(--color-text-secondary); border-color: transparent; }

.result-tag--success { background: var(--color-success-bg); color: var(--color-success); border-color: transparent; }
.result-tag--unsolvable { background: var(--color-danger-bg); color: var(--color-danger); border-color: transparent; }
.result-tag--open { background: var(--color-neutral-100); color: var(--color-text-secondary); border-color: transparent; }

.topic-stages {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.stage-chip {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: var(--text-xs);
  background: var(--color-neutral-100);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-default);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.stage-chip--active {
  background: var(--color-info-bg);
  color: var(--color-info-text);
  border-color: transparent;
}

.stage-chip--done {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: transparent;
}

.stage-arrow {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

.stage-icon {
  font-weight: 700;
}

.stage-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  display: inline-block;
}

.dri-card-wrapper {
  display: flex;
  justify-content: flex-end;
}

.dri-card {
  width: 220px;
  background: var(--color-dri-bg);
  border: 1px solid var(--color-dri-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  text-decoration: none;
}

.dri-card--empty {
  background: var(--color-neutral-50);
  border-color: var(--color-border-default);
}

.dri-card-label {
  font-size: 10px;
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-2) 0;
}

.dri-card-content {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dri-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-primary);
}

.dri-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  margin: 0;
}

.dri-type {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.dri-empty-text {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.team-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.team-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.team-avatars {
  display: flex;
  align-items: center;
}

.team-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-neutral-100);
  border: 2px solid var(--color-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  margin-left: -8px;
  text-decoration: none;
}

.team-avatar:first-child {
  margin-left: 0;
}

.team-avatar--more {
  margin-left: 6px;
  border-radius: 999px;
  width: auto;
  padding: 0 10px;
}

.empty-state {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--color-text-tertiary);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: var(--space-6);
}
</style>

