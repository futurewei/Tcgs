<template>
  <div class="audit-page">
    <div class="page-header">
      <h1 class="page-title">审计日志</h1>
      <el-button @click="fetchLogs">
        <el-icon class="mr-1"><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <section class="tcgs-surface">
      <el-table :data="logs" v-loading="loading">
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <span :class="['action-badge', getActionType(row.action)]">{{ row.action }}</span>
          </template>
        </el-table-column>
        <el-table-column label="对象" width="150">
          <template #default="{ row }">
            <div class="entity-cell">
              <span class="entity-type">{{ row.entityType }}</span>
              <span class="entity-id">#{{ row.entityId }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用户" width="150">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar">{{ getInitials(row.user?.name) }}</div>
              <span class="user-name">{{ row.user?.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="变更" min-width="300">
          <template #default="{ row }">
            <div v-if="row.oldValue || row.newValue" class="changes-cell">
              <div v-if="row.oldValue" class="change-old">- {{ truncate(row.oldValue) }}</div>
              <div v-if="row.newValue" class="change-new">+ {{ truncate(row.newValue) }}</div>
            </div>
            <span v-else class="no-changes">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
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
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { insightsApi } from '@/api/insights';
import { Refresh } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import dayjs from 'dayjs';
import type { AuditLog, AuditAction } from '@/types';

const loading = ref(false);
const logs = ref<AuditLog[]>([]);
const pagination = reactive({ page: 1, pageSize: 20, total: 0 });

function formatDate(date: string) { return dayjs(date).format('YYYY-MM-DD HH:mm'); }
function getInitials(name?: string) { return name ? name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '??'; }
function getActionType(action: AuditAction) {
  if (action.includes('CREATE')) return 'success';
  if (action.includes('DELETE')) return 'danger';
  if (action.includes('FORCE')) return 'warning';
  return 'info';
}
function truncate(text: string, length = 100) { return text.length <= length ? text : text.slice(0, length) + '...'; }

async function fetchLogs() {
  loading.value = true;
  try {
    const response = await insightsApi.getAuditLogs(pagination.page, pagination.pageSize);
    logs.value = response.items;
    pagination.total = response.total;
  } catch (error : any) {
  	console.error('fetch audit logs failed:', error);
  	logs.value = [];
  	pagination.total = 0;
  	ElMessage.error(
    		error?.response?.data?.detail ||
    		error?.response?.statusText ||
    	'获取操作日志失败（请检查 /audit-logs 接口是否可用）'
  );  
  } finally {
    loading.value = false;
  }
}

onMounted(() => fetchLogs());
</script>

<style scoped>
.audit-page {
  padding: var(--space-6);
  max-width: 1400px;
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

.date-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.action-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.action-badge.success { background: var(--color-success-bg); color: var(--color-success); }
.action-badge.danger { background: var(--color-danger-bg); color: var(--color-danger); }
.action-badge.warning { background: var(--color-warning-bg); color: var(--color-warning); }
.action-badge.info { background: var(--color-info-bg); color: var(--color-info); }

.entity-cell { font-size: var(--text-sm); }
.entity-type { color: var(--color-text-secondary); }
.entity-id { color: var(--color-text-disabled); margin-left: var(--space-1); }

.user-cell { display: flex; align-items: center; gap: var(--space-2); }
.user-avatar {
  width: 24px; height: 24px; background: var(--color-neutral-200);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: var(--font-medium); color: var(--color-text-secondary);
}
.user-name { font-size: var(--text-sm); color: var(--color-text-primary); }

.changes-cell { font-size: var(--text-xs); font-family: var(--font-mono); }
.change-old { color: var(--color-danger); }
.change-new { color: var(--color-success); }
.no-changes { color: var(--color-text-disabled); font-size: var(--text-sm); }

.pagination-wrapper {
  display: flex; justify-content: center; padding: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}
</style>
