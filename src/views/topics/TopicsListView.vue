<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Topics</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showCreateDialog = true">
        New Topic
      </el-button>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-zinc-200 p-4">
      <div class="flex flex-wrap items-center gap-4">
        <el-input
          v-model="filters.search"
          placeholder="Search by title or ID..."
          class="w-64"
          clearable
          @input="debouncedFetch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="filters.type" placeholder="Type" clearable @change="fetchTopics">
          <el-option label="Uncertainty" value="UNCERTAINTY" />
          <el-option label="Evolution" value="EVOLUTION" />
        </el-select>

        <el-select v-model="filters.urgency" placeholder="Urgency" clearable @change="fetchTopics">
          <el-option label="P0" value="P0" />
          <el-option label="P1" value="P1" />
          <el-option label="P2" value="P2" />
          <el-option label="P3" value="P3" />
        </el-select>

        <el-select v-model="filters.result" placeholder="Result" clearable @change="fetchTopics">
          <el-option label="Open" value="OPEN" />
          <el-option label="Success" value="SUCCESS" />
          <el-option label="Unsolvable" value="UNSOLVABLE" />
        </el-select>

        <el-button @click="resetFilters">Reset</el-button>
      </div>
    </div>

    <!-- Topics Table -->
    <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
      <el-table
        :data="topicsStore.topics"
        v-loading="topicsStore.loading"
        row-class-name="cursor-pointer"
        @row-click="openTopic"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="Title" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ row.title }}</span>
              <el-tag :type="getUrgencyType(row.urgency)" size="small">{{ row.urgency }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Type" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="DRI" width="150">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs">
                {{ getInitials(row.dri?.name) }}
              </div>
              <span class="text-sm">{{ row.dri?.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Stage" min-width="200">
          <template #default="{ row }">
            <StageTimeline
              :stages="row.template?.stages || []"
              :stage-states="row.stageStates"
              :current-stage-id="row.currentStageId"
              compact
            />
          </template>
        </el-table-column>
        <el-table-column label="Result" width="120">
          <template #default="{ row }">
            <el-tag :type="getResultType(row.result)" size="small">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Updated" width="120">
          <template #default="{ row }">
            <span class="text-sm text-zinc-500">{{ formatDate(row.updatedAt) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="p-4 border-t border-zinc-100 flex justify-center">
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
    </div>

    <CreateTopicDialog v-model="showCreateDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useAuthStore } from '@/stores/auth';
import { Search } from '@element-plus/icons-vue';
import StageTimeline from '@/components/topic/StageTimeline.vue';
import CreateTopicDialog from '@/components/topic/CreateTopicDialog.vue';
import dayjs from 'dayjs';
import type { Topic } from '@/types';

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
  debounceTimer = setTimeout(() => {
    fetchTopics();
  }, 300);
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

function openTopic(row: Topic) {
  router.push(`/topics/${row.id}`);
}

function getUrgencyType(urgency: string) {
  switch (urgency) {
    case 'P0': return 'danger';
    case 'P1': return 'warning';
    default: return 'info';
  }
}

function getResultType(result: string) {
  switch (result) {
    case 'SUCCESS': return 'success';
    case 'UNSOLVABLE': return 'danger';
    default: return '';
  }
}

function getInitials(name?: string) {
  if (!name) return '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(date: string) {
  return dayjs(date).format('MMM D, YYYY');
}

onMounted(() => {
  fetchTopics();
});
</script>
