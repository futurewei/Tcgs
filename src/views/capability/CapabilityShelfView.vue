<template>
  <div class="capability-shelf-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">算法能力货架</h1>
        <p class="page-subtitle">管理和展示算法团队的核心能力资产</p>
      </div>
      <div class="header-actions">
        <router-link to="/algo-platform">
          <el-button type="primary" :icon="Monitor">算法中台演示</el-button>
        </router-link>
      </div>
    </div>

    <!-- Toolbar: Month Selector + Add Button -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          placeholder="选择月份"
          format="YYYY-MM"
          value-format="YYYY-MM"
          :clearable="false"
          @change="handleMonthChange"
        />
        <el-checkbox v-model="showAll" @change="handleShowAllChange">
          查看全部
        </el-checkbox>
      </div>
      <div class="toolbar-right">
        <el-button v-if="canCreate" type="primary" :icon="Plus" @click="openCreateDialog">
          新增能力
        </el-button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- Delivery Table -->
    <div v-else class="table-container tcgs-surface">
      <el-table :data="paginatedDeliveries" style="width: 100%" empty-text="暂无数据">
        <el-table-column prop="capabilityName" label="能力名称" min-width="180">
          <template #default="{ row }">
            <span class="capability-name">{{ row.capabilityName }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="archiveUrl" label="归档链接" width="100">
          <template #default="{ row }">
            <a v-if="row.archiveUrl" :href="row.archiveUrl" target="_blank" class="link">
              查看
            </a>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="upgradeDescription" label="升级描述" min-width="200">
          <template #default="{ row }">
            <span v-if="row.upgradeDescription" class="description">{{ row.upgradeDescription }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="videoUrl" label="串讲视频" width="100">
          <template #default="{ row }">
            <a v-if="row.videoUrl" :href="row.videoUrl" target="_blank" class="link">
              观看
            </a>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="owner" label="责任人" width="120">
          <template #default="{ row }">
            <span v-if="row.owner">{{ row.owner.name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="已交付" width="200">
          <template #default="{ row }">
            <div class="deliver-cell">
              <el-checkbox
                :model-value="row.delivered"
                :disabled="!canEdit(row)"
                @change="handleDeliverChange(row, $event as boolean)"
              />
              <span v-if="row.delivered" class="deliver-info">
                {{ row.deliveredBy?.name }} @ {{ formatDate(row.deliveredAt) }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="canEdit(row)"
                size="small"
                text
                type="primary"
                @click="openEditDialog(row)"
              >
                编辑
              </el-button>
              <el-popconfirm
                v-if="canEdit(row)"
                title="确定删除这条记录吗？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button size="small" text type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div v-if="!showAll && totalDeliveries > pageSize" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalDeliveries"
          layout="total, prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑能力' : '新增能力'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-position="top"
      >
        <el-form-item label="能力名称" prop="capabilityName">
          <el-input v-model="form.capabilityName" placeholder="请输入能力名称" maxlength="200" />
        </el-form-item>

        <el-form-item label="归档链接" prop="archiveUrl">
          <el-input v-model="form.archiveUrl" placeholder="https://..." maxlength="500" />
        </el-form-item>

        <el-form-item label="升级描述" prop="upgradeDescription">
          <el-input
            v-model="form.upgradeDescription"
            type="textarea"
            :rows="3"
            placeholder="请输入升级描述"
          />
        </el-form-item>

        <el-form-item label="串讲视频链接" prop="videoUrl">
          <el-input v-model="form.videoUrl" placeholder="https://..." maxlength="500" />
        </el-form-item>

        <el-form-item label="责任人" prop="ownerId">
          <el-select v-model="form.ownerId" placeholder="请选择责任人" filterable style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :value="user.id"
              :label="user.name"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { Monitor, Plus, Loading } from '@element-plus/icons-vue';
import { useAlgoDeliveriesStore } from '@/stores/algoDeliveries';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import type { AlgoDelivery } from '@/types';

const algoDeliveriesStore = useAlgoDeliveriesStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

// State
const selectedMonth = ref<string>(algoDeliveriesStore.currentMonth);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();

// Pagination state
const currentPage = ref(1);
const pageSize = 15;
const showAll = ref(false);

const form = reactive({
  capabilityName: '',
  archiveUrl: '',
  upgradeDescription: '',
  videoUrl: '',
  ownerId: undefined as number | undefined,
});

const formRules: FormRules = {
  capabilityName: [
    { required: true, message: '请输入能力名称', trigger: 'blur' },
  ],
  ownerId: [
    { required: true, message: '请选择责任人', trigger: 'change' },
  ],
};

// Computed
const allDeliveries = computed(() => algoDeliveriesStore.deliveries);
const totalDeliveries = computed(() => allDeliveries.value.length);
const loading = computed(() => algoDeliveriesStore.loading);
const users = computed(() => usersStore.users);

// Paginated deliveries
const paginatedDeliveries = computed(() => {
  if (showAll.value) {
    return allDeliveries.value;
  }
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return allDeliveries.value.slice(start, end);
});

// canCreate: non-CUSTOMER users can create
const canCreate = computed(() => authStore.canEditTopic);

// canEdit: creator or admin can edit
function canEdit(row: AlgoDelivery): boolean {
  return authStore.isAdmin || authStore.user?.id === row.createdById;
}

// Format date
function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Handle month change
function handleMonthChange(month: string) {
  currentPage.value = 1; // Reset to first page
  algoDeliveriesStore.setCurrentMonth(month);
  algoDeliveriesStore.fetchDeliveries(month);
}

// Handle page change
function handlePageChange(page: number) {
  currentPage.value = page;
}

// Handle show all change
function handleShowAllChange() {
  currentPage.value = 1;
}

// Open create dialog
function openCreateDialog() {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

// Open edit dialog
function openEditDialog(row: AlgoDelivery) {
  editingId.value = row.id;
  form.capabilityName = row.capabilityName;
  form.archiveUrl = row.archiveUrl || '';
  form.upgradeDescription = row.upgradeDescription || '';
  form.videoUrl = row.videoUrl || '';
  form.ownerId = row.ownerId;
  dialogVisible.value = true;
}

// Reset form
function resetForm() {
  form.capabilityName = '';
  form.archiveUrl = '';
  form.upgradeDescription = '';
  form.videoUrl = '';
  form.ownerId = undefined;
}

// Save (create or update)
async function handleSave() {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
  } catch {
    return; // 验证失败
  }

  saving.value = true;
  try {
    if (editingId.value) {
      // Update
      await algoDeliveriesStore.updateDelivery(editingId.value, {
        capabilityName: form.capabilityName,
        archiveUrl: form.archiveUrl || undefined,
        upgradeDescription: form.upgradeDescription || undefined,
        videoUrl: form.videoUrl || undefined,
        ownerId: form.ownerId,
      });
      ElMessage.success('更新成功');
    } else {
      // Create
      await algoDeliveriesStore.createDelivery({
        month: selectedMonth.value,
        capabilityName: form.capabilityName,
        archiveUrl: form.archiveUrl || undefined,
        upgradeDescription: form.upgradeDescription || undefined,
        videoUrl: form.videoUrl || undefined,
        ownerId: form.ownerId!,
      });
      ElMessage.success('创建成功');
    }
    dialogVisible.value = false;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  } finally {
    saving.value = false;
  }
}

// Handle deliver checkbox change
async function handleDeliverChange(row: AlgoDelivery, delivered: boolean) {
  try {
    await algoDeliveriesStore.updateDelivery(row.id, { delivered });
    ElMessage.success(delivered ? '已标记为交付' : '已取消交付标记');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  }
}

// Handle delete
async function handleDelete(row: AlgoDelivery) {
  try {
    await algoDeliveriesStore.deleteDelivery(row.id);
    ElMessage.success('删除成功');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败');
  }
}

// Lifecycle
onMounted(() => {
  algoDeliveriesStore.fetchDeliveries(selectedMonth.value);
  usersStore.fetchUsers(1, 100); // Fetch users for owner selector
});
</script>

<style scoped>
.capability-shelf-page {
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.header-info {
  flex: 1;
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-2) 0 0 0;
}

.header-actions {
  flex-shrink: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-16);
  color: var(--color-text-tertiary);
}

.table-container {
  padding: 0;
  overflow: hidden;
}

.capability-name {
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

.description {
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.link {
  color: var(--color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.text-muted {
  color: var(--color-text-muted);
}

.deliver-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.deliver-info {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}

/* Table styling */
:deep(.el-table) {
  --el-table-border-color: var(--color-border-light);
  --el-table-header-bg-color: var(--color-bg-subtle);
}

:deep(.el-table th) {
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

/* Dialog styling */
:deep(.el-dialog__header) {
  border-bottom: 1px solid var(--color-border-light);
  padding-bottom: var(--space-4);
}

:deep(.el-dialog__footer) {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-4);
}
</style>
