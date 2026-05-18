<template>
  <div class="capability-list-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">算法能力货架</h1>
        <p class="page-subtitle">沉淀底层可复用算法能力资产，连接交付问题、研究课题与责任田。</p>
      </div>
      <div class="header-actions">
        <el-button @click="router.push('/capability-shelf')">
          <el-icon class="mr-1"><Clock /></el-icon>
          交付货架
        </el-button>
        <el-button v-if="canCreate" type="primary" :icon="Plus" @click="openCreateDialog">
          新增能力
        </el-button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div v-if="stats" class="stats-grid">
      <div class="stat-card">
        <span class="stat-value">{{ stats.totalCapabilities }}</span>
        <span class="stat-label">能力总数</span>
      </div>
      <div class="stat-card" :class="{ 'stat-card--danger': stats.highRiskCount > 0 }">
        <span class="stat-value">{{ stats.highRiskCount }}</span>
        <span class="stat-label">高风险能力</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ stats.recent30dIssueCount }}</span>
        <span class="stat-label">30天交付问题</span>
      </div>
      <div class="stat-card" :class="{ 'stat-card--warning': stats.p0P1CapabilityCount > 0 }">
        <span class="stat-value">{{ stats.p0P1CapabilityCount }}</span>
        <span class="stat-label">P0/P1涉及能力</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ stats.topicBackedCount }}</span>
        <span class="stat-label">课题支撑</span>
      </div>
      <div class="stat-card" :class="{ 'stat-card--warning': stats.noOwnerCount > 0 }">
        <span class="stat-value">{{ stats.noOwnerCount }}</span>
        <span class="stat-label">无Owner</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <div class="filter-row">
        <el-input
          v-model="filters.search"
          placeholder="搜索能力名称..."
          :prefix-icon="Search"
          clearable
          class="filter-search"
          @change="handleFilterChange"
        />
        <el-tree-select
          v-model="filters.categoryId"
          :data="categoryTree"
          :props="{ label: 'name', value: 'id', children: 'children' }"
          placeholder="能力分类"
          clearable
          check-strictly
          filterable
          class="filter-category"
          @change="handleFilterChange"
        />
        <el-select v-model="filters.productLine" placeholder="产品线" clearable class="filter-select" @change="handleFilterChange">
          <el-option v-for="pl in PRODUCT_LINES" :key="pl.value" :label="pl.label" :value="pl.value" />
        </el-select>
        <el-select v-model="filters.maturityLevel" placeholder="成熟度" clearable class="filter-select" @change="handleFilterChange">
          <el-option v-for="ml in MATURITY_LEVELS" :key="ml.value" :label="ml.label" :value="ml.value" />
        </el-select>
        <el-select v-model="filters.riskStatus" placeholder="风险状态" clearable class="filter-select" @change="handleFilterChange">
          <el-option v-for="rs in RISK_STATUSES" :key="rs.value" :label="rs.label" :value="rs.value" />
        </el-select>
      </div>
      <div class="filter-row filter-row--secondary">
        <el-select v-model="filters.ownerId" placeholder="Owner" clearable filterable class="filter-select" @change="handleFilterChange">
          <el-option v-for="user in users" :key="user.id" :label="user.name" :value="user.id" />
        </el-select>
        <el-select v-model="filters.hasTopic" placeholder="研究课题" clearable class="filter-select--short" @change="handleFilterChange">
          <el-option label="有课题支撑" :value="true" />
          <el-option label="无课题支撑" :value="false" />
        </el-select>
        <el-select v-model="filters.hasIssue" placeholder="交付问题" clearable class="filter-select--short" @change="handleFilterChange">
          <el-option label="有关联问题" :value="true" />
          <el-option label="无关联问题" :value="false" />
        </el-select>
        <el-button text @click="resetFilters">重置筛选</el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="!filteredCapabilities.length" class="empty-state tcgs-surface">
      <el-icon class="empty-icon"><Goods /></el-icon>
      <h3>暂无能力资产</h3>
      <p>点击「新增能力」创建第一个算法能力资产</p>
    </div>

    <!-- Capability Card Grid -->
    <div v-else class="card-grid">
      <div
        v-for="cap in filteredCapabilities"
        :key="cap.id"
        class="cap-card tcgs-surface-interactive"
        @click="goToDetail(cap.id)"
      >
        <!-- Card Top: Category path + Risk badge -->
        <div class="card-top">
          <div class="card-top-left">
            <span v-if="cap.categoryPath" class="category-breadcrumb">{{ cap.categoryPath }}</span>
          </div>
          <span :class="['risk-badge', `risk-badge--${(cap.riskStatus || 'normal').toLowerCase()}`]">
            {{ RISK_LABELS[cap.riskStatus] || cap.riskStatus }}
          </span>
        </div>

        <!-- Card Name -->
        <h3 class="card-name">{{ cap.name }}</h3>

        <!-- Card Description -->
        <p v-if="cap.description" class="card-desc">{{ cap.description }}</p>

        <!-- Generation Tags -->
        <div class="card-meta">
          <span class="meta-tag">{{ PRODUCT_LINE_LABELS[cap.productLine] || cap.productLine }}</span>
          <span v-if="cap.currentProductionGeneration" class="meta-tag meta-tag--prod">
            量产: {{ cap.currentProductionGeneration.generationCode }} / {{ cap.currentProductionGeneration.maturityLevel }}
          </span>
          <span v-if="cap.currentResearchGeneration" class="meta-tag meta-tag--research">
            研发: {{ cap.currentResearchGeneration.generationCode }} / {{ cap.currentResearchGeneration.maturityLevel }}
          </span>
          <span v-if="!cap.currentProductionGeneration && !cap.currentResearchGeneration" class="meta-tag meta-tag--level">
            {{ MATURITY_LABELS[cap.maturityLevel] || cap.maturityLevel }}
          </span>
        </div>

        <!-- Card Stats Row -->
        <div class="card-stats">
          <div class="card-stat">
            <el-icon><User /></el-icon>
            <span>{{ cap.owner?.name || '未指定' }}</span>
          </div>
          <div class="card-stat">
            <el-icon><WarningFilled /></el-icon>
            <span class="card-stat__count">{{ cap.recent30dIssueCount || 0 }}</span>
            <span>30天问题</span>
          </div>
          <div v-if="cap.p0p1IssueCount > 0" class="card-stat card-stat--danger">
            <span class="card-stat__count">{{ cap.p0p1IssueCount }}</span>
            <span>P0/P1</span>
          </div>
          <div class="card-stat">
            <span class="card-stat__count">{{ cap.topicCount || 0 }}</span>
            <span>课题</span>
          </div>
          <div class="card-stat">
            <span class="card-stat__count">{{ cap.relatedIssues?.length || 0 }}</span>
            <span>问题</span>
          </div>
        </div>

        <!-- Card Bottom -->
        <div class="card-bottom">
          <span class="card-time">{{ formatTime(cap.updatedAt) }}</span>
          <el-button text size="small" type="primary" @click.stop="openEditDialog(cap)">编辑</el-button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑能力' : '新增能力'"
      width="680px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-position="top" label-width="auto">
        <!-- Naming guidance -->
        <el-alert
          v-if="!editingId"
          title="命名规范"
          type="info"
          :closable="false"
          show-icon
          class="mb-4"
        >
          <template #default>
            <p style="margin:0;font-size:12px;line-height:1.6;">
              请使用「底层可复用能力」命名，而非功能/Feature/车型名。<br/>
              <strong>正确</strong>：空间稳定性、实时渲染、畸变矫正<br/>
              <strong>禁止</strong>：照明光毯、M9 AR导航、转弯光毯
            </p>
          </template>
        </el-alert>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="能力分类" prop="categoryId">
              <el-tree-select
                v-model="form.categoryId"
                :data="categoryTree"
                :props="{ label: 'name', value: 'id', children: 'children' }"
                placeholder="选择分类归属"
                clearable
                check-strictly
                filterable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="能力名称" prop="name">
              <el-input v-model="form.name" placeholder="例如：空间稳定性" maxlength="200" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品线" prop="productLine">
              <el-select v-model="form.productLine" style="width: 100%">
                <el-option v-for="pl in PRODUCT_LINES" :key="pl.value" :label="pl.label" :value="pl.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成熟度" prop="maturityLevel">
              <el-select v-model="form.maturityLevel" style="width: 100%">
                <el-option v-for="ml in MATURITY_LEVELS" :key="ml.value" :label="ml.label" :value="ml.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="风险状态" prop="riskStatus">
              <el-select v-model="form.riskStatus" style="width: 100%">
                <el-option v-for="rs in RISK_STATUSES" :key="rs.value" :label="rs.label" :value="rs.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Owner">
              <el-select v-model="form.ownerId" placeholder="选择责任人" filterable clearable style="width: 100%">
                <el-option v-for="user in users" :key="user.id" :label="user.name" :value="user.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="备份Owner">
              <el-select v-model="form.backupOwnerId" placeholder="选择备份责任人" filterable clearable style="width: 100%">
                <el-option v-for="user in users" :key="user.id" :label="user.name" :value="user.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="责任田">
              <el-select
                v-model="selectedRespFieldId"
                placeholder="选择责任田"
                filterable
                clearable
                style="width: 100%"
                @change="onRespFieldChange"
              >
                <el-option
                  v-for="rf in respFields"
                  :key="rf.id"
                  :label="rf.name"
                  :value="rf.id"
                >
                  <span>{{ rf.name }}</span>
                  <span v-if="rf.ownerName" class="resp-owner-hint"> — {{ rf.ownerName }}</span>
                </el-option>
              </el-select>
              <div v-if="selectedRespOwnerName" class="resp-owner-info">
                关联负责人：<strong>{{ selectedRespOwnerName }}</strong>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="简介" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述该底层能力的核心定位、复用场景和当前短板..." />
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
import { useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { Plus, Search, User, Clock, Goods, Loading, WarningFilled } from '@element-plus/icons-vue';
import { useCapabilitiesStore } from '@/stores/capabilities';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import { capabilitiesApi } from '@/api/capabilities';
import { responsibilityApi, type ResponsibilityField } from '@/api/responsibility';
import type { Capability, CapabilityCategory } from '@/types';

const router = useRouter();
const capabilitiesStore = useCapabilitiesStore();
const usersStore = useUsersStore();
const authStore = useAuthStore();

const categoryTree = ref<CapabilityCategory[]>([]);

const PRODUCT_LINES = [
  { value: 'ALL', label: '全部' },
  { value: 'HUD', label: 'HUD' },
  { value: 'LIGHT', label: '车灯' },
  { value: 'PROJECTION', label: '投影' },
];

const PRODUCT_LINE_LABELS: Record<string, string> = {
  ALL: '全部', HUD: 'HUD', LIGHT: '车灯', PROJECTION: '投影',
};

const MATURITY_LEVELS = [
  { value: 'L1', label: 'L1 idea/prototype' },
  { value: 'L2', label: 'L2 testcase验证' },
  { value: 'L3', label: 'L3 cpp工程化' },
  { value: 'L4', label: 'L4 首车型陪跑' },
  { value: 'L5', label: 'L5 平台化复用' },
];

const MATURITY_LABELS: Record<string, string> = Object.fromEntries(
  MATURITY_LEVELS.map((ml) => [ml.value, ml.label])
);

const RISK_STATUSES = [
  { value: 'NORMAL', label: '正常' },
  { value: 'WATCH', label: '关注' },
  { value: 'HIGH_RISK', label: '高风险' },
];

const RISK_LABELS: Record<string, string> = {
  NORMAL: '正常', WATCH: '关注', HIGH_RISK: '高风险',
};

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();
const respFields = ref<ResponsibilityField[]>([]);
const selectedRespFieldId = ref<number | null>(null);

const selectedRespField = computed(() => {
  if (!selectedRespFieldId.value) return null;
  return respFields.value.find((rf) => rf.id === selectedRespFieldId.value) || null;
});

const selectedRespOwnerName = computed(() => selectedRespField.value?.ownerName || '');

const filters = reactive({
  search: '',
  categoryId: undefined as number | undefined,
  productLine: '',
  maturityLevel: '',
  riskStatus: '',
  ownerId: null as number | null | undefined,
  hasTopic: null as boolean | null | undefined,
  hasIssue: null as boolean | null | undefined,
});

const form = reactive({
  name: '',
  description: '',
  categoryId: undefined as number | undefined,
  productLine: 'ALL' as string,
  maturityLevel: 'L1' as string,
  riskStatus: 'NORMAL' as string,
  ownerId: undefined as number | undefined,
  backupOwnerId: undefined as number | undefined,
  responsibilityFieldName: '',
});

const formRules: FormRules = {
  name: [{ required: true, message: '请输入能力名称', trigger: 'blur' }],
  categoryId: [{ required: true, message: '请选择能力分类', trigger: 'change' }],
};

const canCreate = computed(() => authStore.canEditTopic);
const loading = computed(() => capabilitiesStore.loading);
const stats = computed(() => capabilitiesStore.stats);
const allCapabilities = computed(() => capabilitiesStore.capabilities);
const users = computed(() => usersStore.users);

const filteredCapabilities = computed(() => {
  return allCapabilities.value.filter((cap) => {
    if (filters.search && !cap.name.includes(filters.search)) return false;
    if (filters.categoryId && cap.categoryId !== filters.categoryId) return false;
    if (filters.productLine && cap.productLine !== filters.productLine) return false;
    if (filters.maturityLevel && cap.maturityLevel !== filters.maturityLevel) return false;
    if (filters.riskStatus && cap.riskStatus !== filters.riskStatus) return false;
    if (filters.ownerId && cap.ownerId !== filters.ownerId) return false;
    if (filters.hasTopic === true && (!cap.relatedTopics || cap.relatedTopics.length === 0)) return false;
    if (filters.hasTopic === false && cap.relatedTopics && cap.relatedTopics.length > 0) return false;
    if (filters.hasIssue === true && (!cap.relatedIssues || cap.relatedIssues.length === 0)) return false;
    if (filters.hasIssue === false && cap.relatedIssues && cap.relatedIssues.length > 0) return false;
    return true;
  });
});

function formatTime(dateStr: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 7) return `${days}天前`;
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}

function goToDetail(id: number) {
  router.push(`/capabilities/${id}`);
}

function openCreateDialog() {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(cap: Capability) {
  editingId.value = cap.id;
  form.name = cap.name;
  form.description = cap.description || '';
  form.categoryId = cap.categoryId;
  form.productLine = cap.productLine || 'ALL';
  form.maturityLevel = cap.maturityLevel || 'L1';
  form.riskStatus = cap.riskStatus || 'NORMAL';
  form.ownerId = cap.ownerId;
  form.backupOwnerId = cap.backupOwnerId;
  form.responsibilityFieldName = cap.responsibilityFieldName || '';
  selectedRespFieldId.value = cap.responsibilityFieldId || null;
  dialogVisible.value = true;
}

function resetForm() {
  form.name = '';
  form.description = '';
  form.categoryId = undefined;
  form.productLine = 'ALL';
  form.maturityLevel = 'L1';
  form.riskStatus = 'NORMAL';
  form.ownerId = undefined;
  form.backupOwnerId = undefined;
  form.responsibilityFieldName = '';
  selectedRespFieldId.value = null;
}

function resetFilters() {
  filters.search = '';
  filters.categoryId = undefined;
  filters.productLine = '';
  filters.maturityLevel = '';
  filters.riskStatus = '';
  filters.ownerId = null;
  filters.hasTopic = null;
  filters.hasIssue = null;
}

function handleFilterChange() {
  // Client-side filtering is reactive via computed
}

function onRespFieldChange(fieldId: number | null) {
  if (!fieldId) {
    form.responsibilityFieldName = '';
    return;
  }
  const rf = respFields.value.find((f) => f.id === fieldId);
  if (rf) {
    form.responsibilityFieldName = rf.name;
    // Attempt to match owner by name
    if (rf.ownerName && users.value.length) {
      const matchedUser = users.value.find(
        (u) => u.name === rf.ownerName || u.name.includes(rf.ownerName) || rf.ownerName.includes(u.name)
      );
      if (matchedUser) {
        form.ownerId = matchedUser.id;
      }
    }
  }
}

async function handleSave() {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  saving.value = true;
  try {
    if (editingId.value) {
      await capabilitiesStore.updateCapability(editingId.value, {
        name: form.name,
        description: form.description || undefined,
        categoryId: form.categoryId,
        productLine: form.productLine,
        maturityLevel: form.maturityLevel,
        riskStatus: form.riskStatus,
        ownerId: form.ownerId,
        backupOwnerId: form.backupOwnerId || undefined,
        responsibilityFieldId: selectedRespFieldId.value ?? undefined,
        responsibilityFieldName: form.responsibilityFieldName || undefined,
      });
      ElMessage.success('更新成功');
    } else {
      await capabilitiesStore.createCapability({
        name: form.name,
        description: form.description || undefined,
        categoryId: form.categoryId,
        productLine: form.productLine,
        maturityLevel: form.maturityLevel,
        riskStatus: form.riskStatus,
        ownerId: form.ownerId,
        backupOwnerId: form.backupOwnerId || undefined,
        responsibilityFieldId: selectedRespFieldId.value ?? undefined,
        responsibilityFieldName: form.responsibilityFieldName || undefined,
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

onMounted(async () => {
  capabilitiesStore.fetchCapabilities();
  capabilitiesStore.fetchStats();
  usersStore.fetchUsers(1, 100);
  try {
    categoryTree.value = await capabilitiesApi.getCategoryTree();
  } catch {
    // Category tree is optional
  }
  try {
    const resp = await responsibilityApi.getFields();
    respFields.value = resp.fields || [];
  } catch {
    // Responsibility fields are optional
  }
});
</script>

<style scoped>
.capability-list-page {
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
  margin: var(--space-1) 0 0 0;
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
}

.mr-1 {
  margin-right: var(--space-1);
}

.mb-4 {
  margin-bottom: var(--space-4);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.stat-card--danger {
  border-color: var(--color-danger-bg);
  background: var(--color-danger-light);
}

.stat-card--danger .stat-value {
  color: var(--color-danger);
}

.stat-card--warning {
  border-color: var(--color-warning-bg);
  background: var(--color-warning-light);
}

.stat-card--warning .stat-value {
  color: var(--color-warning);
}

/* Filters */
.filter-bar {
  margin-bottom: var(--space-6);
  padding: var(--space-4);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
}

.filter-row {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  flex-wrap: wrap;
}

.filter-row--secondary {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
}

.filter-search {
  width: 200px;
}

.filter-category {
  width: 200px;
}

.filter-select {
  width: 150px;
}

.filter-select--short {
  width: 140px;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-16);
  color: var(--color-text-tertiary);
}

/* Empty */
.empty-state {
  padding: var(--space-16) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.empty-state h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-1) 0;
}

.empty-state p {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Card Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--space-4);
}

.cap-card {
  padding: var(--space-5);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.card-top-left {
  flex: 1;
  min-width: 0;
}

.category-breadcrumb {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resp-owner-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.resp-owner-info {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-subtle);
  border-radius: var(--radius-sm);
}

.card-name {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.risk-badge {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  padding: 2px var(--space-2);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.risk-badge--normal {
  background: var(--color-success-bg);
  color: var(--color-success-600);
}

.risk-badge--watch {
  background: var(--color-warning-bg);
  color: var(--color-warning-600);
}

.risk-badge--high_risk {
  background: var(--color-danger-bg);
  color: var(--color-danger-600);
}

.card-desc {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--leading-normal);
}

.card-meta {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.meta-tag {
  font-size: var(--text-xs);
  padding: 1px var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-bg-subtle);
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
}

.meta-tag--level {
  background: var(--color-primary-light);
  color: var(--color-primary-700);
}

.meta-tag--prod {
  background: #dcfce7;
  color: #166534;
}

.meta-tag--research {
  background: #dbeafe;
  color: #1e40af;
}

.card-stats {
  display: flex;
  gap: var(--space-3);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-subtle);
  flex-wrap: wrap;
}

.card-stat {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.card-stat .el-icon {
  font-size: 14px;
}

.card-stat__count {
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.card-stat--danger .card-stat__count {
  color: var(--color-danger);
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-subtle);
}

.card-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
