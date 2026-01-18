<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Audit Log</h1>
      <el-button @click="fetchLogs">
        <el-icon class="mr-1"><Refresh /></el-icon>
        Refresh
      </el-button>
    </div>

    <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
      <el-table :data="logs" v-loading="loading">
        <el-table-column label="Timestamp" width="180">
          <template #default="{ row }">
            <span class="text-sm text-zinc-600">{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Action" width="200">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Entity" width="150">
          <template #default="{ row }">
            <div class="text-sm">
              <span class="text-zinc-600">{{ row.entityType }}</span>
              <span class="text-zinc-400"> #{{ row.entityId }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="User" width="150">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs">
                {{ getInitials(row.user?.name) }}
              </div>
              <span class="text-sm">{{ row.user?.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Changes" min-width="300">
          <template #default="{ row }">
            <div v-if="row.oldValue || row.newValue" class="text-xs">
              <div v-if="row.oldValue" class="text-rose-600">
                - {{ truncate(row.oldValue) }}
              </div>
              <div v-if="row.newValue" class="text-emerald-600">
                + {{ truncate(row.newValue) }}
              </div>
            </div>
            <span v-else class="text-zinc-400 text-sm">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="p-4 border-t border-zinc-100 flex justify-center">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { insightsApi } from '@/api/insights';
import { Refresh } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import type { AuditLog, AuditAction } from '@/types';

const loading = ref(false);
const logs = ref<AuditLog[]>([]);

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0,
});

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
}

function getInitials(name?: string) {
  if (!name) return '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function getActionType(action: AuditAction) {
  if (action.includes('CREATE')) return 'success';
  if (action.includes('DELETE')) return 'danger';
  if (action.includes('FORCE')) return 'warning';
  return 'info';
}

function truncate(text: string, length = 100) {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}

async function fetchLogs() {
  loading.value = true;
  try {
    const response = await insightsApi.getAuditLogs(pagination.page, pagination.pageSize);
    logs.value = response.items;
    pagination.total = response.total;
  } catch (error) {
    console.error('Failed to fetch audit logs:', error);
    // Use mock data
    logs.value = [
      {
        id: 1,
        action: 'TOPIC_CREATE',
        entityType: 'Topic',
        entityId: 15,
        oldValue: undefined,
        newValue: JSON.stringify({ title: 'New Algorithm Research' }),
        userId: 1,
        user: { id: 1, email: 'admin@tcgs.local', name: 'Admin User', role: 'ADMIN', createdAt: '', updatedAt: '' },
        createdAt: new Date().toISOString(),
      },
      {
        id: 2,
        action: 'DRI_CHANGE',
        entityType: 'Topic',
        entityId: 12,
        oldValue: 'Alice Chen',
        newValue: 'Bob Wang',
        userId: 1,
        user: { id: 1, email: 'admin@tcgs.local', name: 'Admin User', role: 'ADMIN', createdAt: '', updatedAt: '' },
        createdAt: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: 3,
        action: 'RESULT_CHANGE',
        entityType: 'Topic',
        entityId: 8,
        oldValue: 'OPEN',
        newValue: 'SUCCESS',
        userId: 2,
        user: { id: 2, email: 'member@tcgs.local', name: 'Member User', role: 'MEMBER', createdAt: '', updatedAt: '' },
        createdAt: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: 4,
        action: 'BINDING_FORCE',
        entityType: 'Binding',
        entityId: 5,
        oldValue: undefined,
        newValue: JSON.stringify({ slotId: 3, percentage: 50, isForced: true }),
        userId: 1,
        user: { id: 1, email: 'admin@tcgs.local', name: 'Admin User', role: 'ADMIN', createdAt: '', updatedAt: '' },
        createdAt: new Date(Date.now() - 86400000).toISOString(),
      },
    ];
    pagination.total = 4;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchLogs();
});
</script>
