<template>
  <div class="issues-page">
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">交付重点问题</h1>
        <p class="page-subtitle">跟踪各产品线交付过程中的关键问题，关联能力短板</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">登记问题</el-button>
    </div>

    <!-- Product Line Swiper -->
    <div class="pl-swiper">
      <div
        v-for="pl in PRODUCT_LINES"
        :key="pl.value"
        :class="['pl-card', { 'pl-card--active': activePL === pl.value }]"
        @click="switchPL(pl.value)"
      >
        <span class="pl-card-label">{{ pl.label }}</span>
        <span class="pl-card-count">{{ plCount(pl.value) }}</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-input v-model="filters.search" placeholder="搜索问题..." :prefix-icon="Search" clearable class="filter-search" />
      <el-select v-model="filters.priority" placeholder="优先级" clearable class="filter-select" @change="fetchIssues">
        <el-option v-for="p in PRIORITY_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable class="filter-select" @change="fetchIssues">
        <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>
      <el-select v-model="filters.ownerId" placeholder="责任人" clearable filterable class="filter-select" @change="fetchIssues">
        <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
      </el-select>
      <el-button v-if="filters.includeClosed" text type="warning" @click="filters.includeClosed = false; fetchIssues()">隐藏已关闭</el-button>
      <el-button v-else text @click="filters.includeClosed = true; fetchIssues()">显示已关闭</el-button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon> 加载中...</div>

    <!-- Empty -->
    <div v-else-if="!filteredIssues.length" class="empty-state">
      <p>暂无问题</p>
    </div>

    <!-- Issue Cards -->
    <div v-else class="issue-list">
      <div
        v-for="issue in filteredIssues"
        :key="issue.id"
        :class="['issue-card', getStageClass(issue.status)]"
      >
        <div class="issue-card-body">
          <div class="issue-card-left">
            <h3 class="issue-title">{{ issue.title }}</h3>
            <p v-if="issue.description" class="issue-desc">{{ issue.description }}</p>
            <div class="issue-meta">
              <span v-if="issue.projectName" class="meta-tag">{{ issue.projectName }}</span>
              <span v-if="issue.owner" class="meta-tag meta-tag--owner">{{ issue.owner.name }}</span>
              <span class="meta-tag meta-tag--time">{{ formatTime(issue.updatedAt) }}</span>
            </div>
            <p v-if="issue.impact" class="issue-impact">影响：{{ issue.impact }}</p>
            <p v-if="issue.latestProgress" class="issue-progress">最新进展：{{ issue.latestProgress }}</p>
            <div v-if="issue.relatedCapabilities?.length || issue.generation" class="issue-capabilities">
              <span class="cap-link-label">关联能力：</span>
              <span v-for="c in issue.relatedCapabilities" :key="c.id" class="cap-link">{{ c.name }}</span>
              <span v-if="issue.generation" class="cap-link cap-link--gen">{{ issue.generation.generationCode }} {{ issue.generation.name }}</span>
            </div>
          </div>
          <div class="issue-card-right">
            <!-- Stage Progress -->
            <div class="stage-track">
              <div
                v-for="(stage, idx) in STAGES"
                :key="stage.value"
                :class="['stage-dot', getStageDotClass(issue.status, stage.value)]"
                @click="quickStage(issue, stage.value)"
              >
                <span class="stage-dot-inner" />
                <span class="stage-label">{{ stage.label }}</span>
              </div>
            </div>

            <!-- Priority Badge -->
            <span :class="['priority-badge', `priority-badge--${(issue.priority||'P2').toLowerCase()}`]">
              {{ issue.priority }}
            </span>

            <!-- Actions -->
            <el-dropdown trigger="click" :teleported="true">
              <el-button text size="small" type="primary">操作 ▾</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="quickStage(issue, 'ANALYZING')">定位中</el-dropdown-item>
                  <el-dropdown-item @click="quickStage(issue, 'FIXING')">修改中</el-dropdown-item>
                  <el-dropdown-item @click="quickStage(issue, 'VERIFYING')">验证中</el-dropdown-item>
                  <el-dropdown-item @click="quickStage(issue, 'CLOSED')">关闭</el-dropdown-item>
                  <el-dropdown-item @click="quickStage(issue, 'NEW')">重新打开</el-dropdown-item>
                  <el-dropdown-item divided @click="openEditDialog(issue)">编辑</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" @click="handleDelete(issue.id)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑问题' : '登记问题'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form :model="form" label-position="top">
        <el-form-item label="问题标题" required>
          <el-input v-model="form.title" placeholder="例如：HUD高速转弯抖动" maxlength="300" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="产品线">
              <el-select v-model="form.productLine" style="width:100%">
                <el-option v-for="pl in PRODUCT_LINES" :key="pl.value" :label="pl.label" :value="pl.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width:100%">
                <el-option v-for="p in PRIORITY_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="责任人">
              <el-select v-model="form.ownerId" filterable clearable placeholder="选择" style="width:100%">
                <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目名称">
              <el-input v-model="form.projectName" placeholder="如：M9首发" maxlength="200" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="详细描述问题现象..." />
        </el-form-item>
        <el-form-item label="影响范围">
          <el-input v-model="form.impact" type="textarea" :rows="2" placeholder="对交付的影响..." />
        </el-form-item>
        <el-form-item label="最新进展">
          <el-input v-model="form.latestProgress" type="textarea" :rows="2" placeholder="当前处理进展..." />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="关联能力 (Capability)">
              <el-select v-model="form.capabilityId" filterable clearable placeholder="选择能力 (可选)" style="width:100%" @change="onCapabilityChange">
                <el-option v-for="c in allCapabilities" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联代际 (Generation)">
              <el-select v-model="form.generationId" filterable clearable placeholder="选择代际 (可选)" style="width:100%" :disabled="!form.capabilityId">
                <el-option v-for="g in availableGenerations" :key="g.id" :label="`${g.generationCode} ${g.name}`" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
import { ElMessage } from 'element-plus';
import { Plus, Search, Loading } from '@element-plus/icons-vue';
import { capabilitiesApi } from '@/api/capabilities';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';

const usersStore = useUsersStore();
const authStore = useAuthStore();

const PRODUCT_LINES = [
  { value: 'HUD', label: 'HUD' },
  { value: 'LIGHT', label: '车灯' },
  { value: 'PROJECTION', label: '投影' },
];

const STAGES = [
  { value: 'NEW', label: '开启' },
  { value: 'ANALYZING', label: '定位中' },
  { value: 'FIXING', label: '修改中' },
  { value: 'VERIFYING', label: '验证中' },
  { value: 'CLOSED', label: '关闭' },
];

const STAGE_ORDER = ['NEW', 'ANALYZING', 'FIXING', 'VERIFYING', 'CLOSED'];
const PRIORITY_OPTIONS = [{ value:'P0',label:'P0'},{ value:'P1',label:'P1'},{ value:'P2',label:'P2'}];
const STATUS_OPTIONS = STAGES;

const issues = ref<any[]>([]);
const loading = ref(false);
const activePL = ref('HUD');
const dialogVisible = ref(false);
const editingId = ref<number|null>(null);
const saving = ref(false);
const allCapabilities = ref<any[]>([]);
const availableGenerations = ref<any[]>([]);

const filters = reactive({
  search: '',
  priority: '',
  status: '',
  ownerId: null as number|null,
  includeClosed: false,
});

const users = computed(() => usersStore.users);

const filteredIssues = computed(() => {
  return issues.value.filter(i => {
    if (!filters.includeClosed && i.status === 'CLOSED') return false;
    if (filters.search && !i.title?.includes(filters.search)) return false;
    if (filters.priority && i.priority !== filters.priority) return false;
    if (filters.status && i.status !== filters.status) return false;
    if (filters.ownerId && i.ownerId !== filters.ownerId) return false;
    return true;
  });
});

const form = reactive({
  title: '',
  description: '',
  productLine: 'HUD',
  priority: 'P2',
  status: 'NEW',
  projectName: '',
  ownerId: undefined as number|undefined,
  impact: '',
  latestProgress: '',
  capabilityId: undefined as number|undefined,
  generationId: undefined as number|undefined,
});

function plCount(pl: string) {
  return issues.value.filter(i => i.productLine === pl && i.status !== 'CLOSED').length;
}

function switchPL(pl: string) {
  activePL.value = pl;
  fetchIssues();
}

async function fetchIssues() {
  loading.value = true;
  try {
    issues.value = await capabilitiesApi.listIssues({
      product_line: activePL.value === 'ALL' ? undefined : activePL.value,
      priority: filters.priority || undefined,
      status: filters.includeClosed ? (filters.status || undefined) : (filters.status || undefined),
      owner_id: filters.ownerId ?? undefined,
      search: filters.search || undefined,
    });
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function quickStage(issue: any, status: string) {
  try {
    await capabilitiesApi.updateIssue(issue.id, { status });
    issue.status = status;
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败');
  }
}

function openCreateDialog() {
  editingId.value = null;
  resetForm();
  form.productLine = activePL.value;
  availableGenerations.value = [];
  dialogVisible.value = true;
}

function openEditDialog(issue: any) {
  editingId.value = issue.id;
  form.title = issue.title;
  form.description = issue.description || '';
  form.productLine = issue.productLine;
  form.priority = issue.priority;
  form.status = issue.status;
  form.projectName = issue.projectName || '';
  form.ownerId = issue.ownerId;
  form.impact = issue.impact || '';
  form.latestProgress = issue.latestProgress || '';
  form.generationId = issue.generationId;
  form.capabilityId = issue.relatedCapabilities?.[0]?.id;
  if (issue.relatedCapabilities?.[0]?.generations) {
    availableGenerations.value = issue.relatedCapabilities[0].generations || [];
  }
  dialogVisible.value = true;
}

function resetForm() {
  form.title = ''; form.description = ''; form.productLine = 'HUD'; form.priority = 'P2';
  form.status = 'NEW'; form.projectName = ''; form.ownerId = undefined; form.impact = ''; form.latestProgress = '';
  form.capabilityId = undefined; form.generationId = undefined;
}

async function handleSave() {
  if (!form.title) { ElMessage.warning('请输入标题'); return; }
  saving.value = true;
  try {
    if (editingId.value) {
      await capabilitiesApi.updateIssue(editingId.value, {
        title: form.title, description: form.description || undefined,
        productLine: form.productLine, priority: form.priority, status: form.status,
        projectName: form.projectName || undefined, ownerId: form.ownerId,
        impact: form.impact || undefined, latestProgress: form.latestProgress || undefined,
        generationId: form.generationId,
        relatedCapabilityIds: form.capabilityId ? [form.capabilityId] : undefined,
      });
    } else {
      await capabilitiesApi.createIssue({
        title: form.title, description: form.description || undefined,
        productLine: form.productLine, priority: form.priority, status: form.status,
        projectName: form.projectName || undefined, ownerId: form.ownerId,
        impact: form.impact || undefined, latestProgress: form.latestProgress || undefined,
        generationId: form.generationId,
        relatedCapabilityIds: form.capabilityId ? [form.capabilityId] : undefined,
      });
    }
    dialogVisible.value = false;
    fetchIssues();
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败');
  } finally {
    saving.value = false;
  }
}

async function handleDelete(id: number) {
  try {
    await capabilitiesApi.deleteIssue(id);
    issues.value = issues.value.filter(i => i.id !== id);
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败');
  }
}

function getStageClass(status: string) {
  return `issue-card--${(status||'new').toLowerCase()}`;
}

function getStageDotClass(issueStatus: string, stage: string) {
  const currentIdx = STAGE_ORDER.indexOf(issueStatus);
  const stageIdx = STAGE_ORDER.indexOf(stage);
  if (stageIdx <= currentIdx) return 'stage-dot--done';
  if (stageIdx === currentIdx + 1) return 'stage-dot--current';
  return '';
}

function formatTime(d: string) {
  if (!d) return '';
  const date = new Date(d);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString('zh-CN', { month:'2-digit', day:'2-digit' });
}

async function onCapabilityChange(capId: number | undefined) {
  form.generationId = undefined;
  availableGenerations.value = [];
  if (!capId) return;
  try {
    const cap = await capabilitiesApi.get(capId);
    availableGenerations.value = cap.generations || [];
  } catch { /* ignore */ }
}

onMounted(async () => {
  fetchIssues();
  usersStore.fetchUsers(1, 200);
  try {
    allCapabilities.value = await capabilitiesApi.list();
  } catch { /* ignore */ }
});
</script>

<style scoped>
.issues-page { padding: var(--space-6); max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: var(--space-6); }
.header-info { flex: 1; }
.page-title { font-size: var(--text-2xl); font-weight: var(--font-bold); margin: 0; }
.page-subtitle { font-size: var(--text-sm); color: var(--color-text-tertiary); margin: var(--space-1) 0 0 0; }

/* Product Line Swiper */
.pl-swiper { display: flex; gap: var(--space-3); margin-bottom: var(--space-5); }
.pl-card { flex: 1; padding: var(--space-4); border: 2px solid var(--color-border-subtle); border-radius: var(--radius-lg); cursor: pointer; text-align: center; transition: all .2s; }
.pl-card:hover { border-color: var(--color-primary); }
.pl-card--active { border-color: var(--color-primary); background: var(--color-primary-light); }
.pl-card-label { display: block; font-size: var(--text-base); font-weight: var(--font-semibold); margin-bottom: var(--space-1); }
.pl-card-count { display: block; font-size: var(--text-2xl); font-weight: var(--font-bold); color: var(--color-primary); }

/* Filters */
.filter-bar { display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap; margin-bottom: var(--space-5); padding: var(--space-3); background: var(--color-surface-primary); border-radius: var(--radius-lg); border: 1px solid var(--color-border-subtle); }
.filter-search { width: 200px; }
.filter-select { width: 140px; }

.loading-state { display: flex; align-items: center; justify-content: center; gap: var(--space-2); padding: var(--space-16); color: var(--color-text-tertiary); }
.empty-state { text-align: center; padding: var(--space-16); color: var(--color-text-tertiary); }

/* Issue Cards */
.issue-list { display: flex; flex-direction: column; gap: var(--space-3); }
.issue-card { background: var(--color-surface-primary); border: 1px solid var(--color-border-subtle); border-left: 4px solid var(--color-border-subtle); border-radius: var(--radius-lg); overflow: hidden; }
.issue-card--new { border-left-color: #6b7280; }
.issue-card--analyzing { border-left-color: #3b82f6; }
.issue-card--fixing { border-left-color: #f59e0b; }
.issue-card--verifying { border-left-color: #8b5cf6; }
.issue-card--closed { border-left-color: #9ca3af; opacity: .7; }
.issue-card-body { display: flex; padding: var(--space-4); gap: var(--space-4); }
.issue-card-left { flex: 1; min-width: 0; }
.issue-title { font-size: var(--text-base); font-weight: var(--font-semibold); margin: 0 0 var(--space-1); }
.issue-desc { font-size: var(--text-sm); color: var(--color-text-secondary); margin: 0 0 var(--space-2); }
.issue-meta { display: flex; gap: var(--space-2); flex-wrap: wrap; margin-bottom: var(--space-1); }
.meta-tag { font-size: var(--text-xs); padding: 1px var(--space-2); border-radius: var(--radius-md); background: var(--color-bg-subtle); color: var(--color-text-secondary); }
.meta-tag--owner { background: var(--color-primary-light); color: var(--color-primary); }
.meta-tag--time { background: transparent; color: var(--color-text-muted); }
.issue-impact { font-size: var(--text-xs); color: var(--color-danger); margin: var(--space-1) 0; }
.issue-progress { font-size: var(--text-xs); color: var(--color-text-secondary); margin: var(--space-1) 0; }
.issue-capabilities { margin-top: var(--space-2); }
.cap-link-label { font-size: var(--text-xs); color: var(--color-text-muted); }
.cap-link { display: inline-block; font-size: var(--text-xs); padding: 1px var(--space-2); margin: 0 var(--space-1) var(--space-1) 0; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); }
.cap-link--gen { background: #ede9fe; color: #7c3aed; }

.issue-card-right { display: flex; flex-direction: column; align-items: flex-end; gap: var(--space-2); flex-shrink: 0; }

/* Stage Track */
.stage-track { display: flex; align-items: center; gap: var(--space-1); }
.stage-dot { display: flex; flex-direction: column; align-items: center; cursor: pointer; }
.stage-dot-inner { width: 10px; height: 10px; border-radius: 50%; background: var(--color-border); transition: all .15s; }
.stage-dot--done .stage-dot-inner { background: #22c55e; }
.stage-dot--current .stage-dot-inner { background: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-light); }
.stage-dot:hover .stage-dot-inner { transform: scale(1.3); }
.stage-label { font-size: 9px; color: var(--color-text-muted); margin-top: 2px; }
.stage-dot--done .stage-label { color: #22c55e; }
.stage-dot--current .stage-label { color: var(--color-primary); font-weight: var(--font-semibold); }

.priority-badge { font-size: var(--text-xs); font-weight: var(--font-bold); padding: 2px var(--space-2); border-radius: var(--radius-md); }
.priority-badge--p0 { background: #fee2e2; color: #dc2626; }
.priority-badge--p1 { background: #fed7aa; color: #ea580c; }
.priority-badge--p2 { background: var(--color-bg-subtle); color: var(--color-text-secondary); }
</style>
