<template>
  <div class="templates-page">
    <div class="page-header">
      <h1 class="page-title">课题模板管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="createNewTemplate">新建模板</el-button>
    </div>

    <div class="templates-layout">
      <!-- Left: Template List -->
      <div class="templates-sidebar">
        <section class="tcgs-surface">
          <div class="sidebar-header">
            <h2 class="sidebar-title">模板列表</h2>
          </div>
          <div class="templates-list">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="['template-item', { active: selectedTemplate?.id === template.id }]"
              @click="selectTemplate(template)"
            >
              <div class="template-info">
                <h3 class="template-name">{{ template.name }}</h3>
                <p class="template-meta">{{ template.stages?.length || 0 }} 个阶段</p>
              </div>
              <div class="template-actions">
                <el-button
                  v-if="authStore.isAdmin"
                  class="delete-btn"
                  size="small"
                  type="danger"
                  text
                  @click.stop="deleteTemplateById(template)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
                <el-icon v-if="selectedTemplate?.id === template.id" class="arrow-icon"><ArrowRight /></el-icon>
              </div>
            </div>
            <div v-if="templates.length === 0" class="empty-state">暂无模板</div>
          </div>
        </section>
      </div>

      <!-- Right: Edit Area -->
      <div class="templates-main">
        <section v-if="selectedTemplate || isCreating" class="tcgs-surface">
          <div class="edit-header">
            <h2 class="edit-title">{{ isCreating ? '新建模板' : '编辑模板' }}</h2>
            <el-button v-if="authStore.isAdmin" type="primary" :loading="saving" @click="saveTemplate">保存</el-button>
          </div>

          <div class="edit-content">
            <!-- Template Info -->
            <div class="form-grid">
              <el-form-item label="模板名称">
                <el-input v-model="form.name" placeholder="请输入模板名称" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="form.description" placeholder="请输入描述" />
              </el-form-item>
            </div>

            <!-- Stages List -->
            <div class="stages-section">
              <div class="stages-header">
                <h3 class="stages-title">阶段配置</h3>
                <el-button size="small" @click="addStage">添加阶段</el-button>
              </div>

              <div class="stages-list">
                <div v-for="(stage, index) in form.stages" :key="index" class="stage-card">
                  <div class="stage-order">
                    <el-button size="small" text :disabled="index === 0" @click="moveStage(index, -1)">
                      <el-icon><ArrowUp /></el-icon>
                    </el-button>
                    <span class="order-num">{{ index + 1 }}</span>
                    <el-button size="small" text :disabled="index === form.stages.length - 1" @click="moveStage(index, 1)">
                      <el-icon><ArrowDown /></el-icon>
                    </el-button>
                  </div>

                  <div class="stage-form">
                    <div class="stage-inputs">
                      <el-input v-model="stage.name" placeholder="阶段名称" />
                      <el-input v-model="stage.description" placeholder="描述" />
                    </div>
                    <div class="stage-options">
                      <el-checkbox v-model="stage.isTerminal">终止阶段</el-checkbox>
                      <el-checkbox v-model="stage.allowResult" :disabled="!stage.isTerminal">允许结项</el-checkbox>
                      <el-checkbox v-model="stage.requireArtifact">需要交付物</el-checkbox>
                    </div>
                  </div>

                  <el-button type="danger" text @click="removeStage(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- Timeline Preview -->
            <div class="preview-section">
              <h3 class="preview-title">时间轴预览</h3>
              <StageTimeline :stages="previewStages" />
            </div>
          </div>
        </section>

        <section v-else class="tcgs-surface empty-edit">
          <p class="empty-text">选择一个模板进行编辑，或创建新模板</p>
        </section>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useTemplatesStore } from '@/stores/templates';
import { useAuthStore } from '@/stores/auth';
import { ArrowRight, ArrowUp, ArrowDown, Delete } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import StageTimeline from '@/components/topic/StageTimeline.vue';
import type { StageTemplate, StageTemplateStage } from '@/types';

const templatesStore = useTemplatesStore();
const authStore = useAuthStore();

const selectedTemplate = ref<StageTemplate | null>(null);
const isCreating = ref(false);
const saving = ref(false);

interface StageForm {
  name: string;
  description: string;
  isTerminal: boolean;
  allowResult: boolean;
  requireArtifact: boolean;
}

const form = reactive({
  name: '',
  description: '',
  stages: [] as StageForm[],
});

const templates = computed(() => templatesStore.templates);

const previewStages = computed(() => form.stages.map((s, i) => ({
  id: i,
  name: s.name || `阶段 ${i + 1}`,
  status: i === 0 ? 'ACTIVE' : 'PENDING',
  order: i,
})));

function selectTemplate(template: StageTemplate) {
  selectedTemplate.value = template;
  isCreating.value = false;
  form.name = template.name;
  form.description = template.description;
  form.stages = template.stages?.map(s => ({
    name: s.name,
    description: s.description,
    isTerminal: s.isTerminal,
    allowResult: s.allowResult,
    requireArtifact: s.requireArtifact,
  })) || [];
}

function createNewTemplate() {
  selectedTemplate.value = null;
  isCreating.value = true;
  form.name = '';
  form.description = '';
  form.stages = [
    { name: '问题定义', description: '定义问题和目标', isTerminal: false, allowResult: false, requireArtifact: false },
    { name: '方案分析', description: '分析可行方案', isTerminal: false, allowResult: false, requireArtifact: true },
    { name: '结项评审', description: '最终评审', isTerminal: true, allowResult: true, requireArtifact: false },
  ];
}

function addStage() {
  form.stages.push({ name: '', description: '', isTerminal: false, allowResult: false, requireArtifact: false });
}

function removeStage(index: number) {
  form.stages.splice(index, 1);
}

function moveStage(index: number, direction: number) {
  const newIndex = index + direction;
  if (newIndex < 0 || newIndex >= form.stages.length) return;
  const temp = form.stages[index];
  form.stages[index] = form.stages[newIndex];
  form.stages[newIndex] = temp;
}

async function saveTemplate() {
  if (!form.name) { ElMessage.error('请输入模板名称'); return; }
  if (form.stages.length === 0) { ElMessage.error('请至少添加一个阶段'); return; }

  saving.value = true;
  try {
    const data = {
      name: form.name,
      description: form.description,
      stages: form.stages.map((s, i) => ({
        name: s.name, description: s.description, order: i,
        isTerminal: s.isTerminal, allowResult: s.allowResult, requireArtifact: s.requireArtifact,
      })),
    };

    if (isCreating.value) {
      const template = await templatesStore.createTemplate(data);
      selectedTemplate.value = template;
      isCreating.value = false;
      ElMessage.success('模板创建成功');
    } else if (selectedTemplate.value) {
      await templatesStore.updateTemplate(selectedTemplate.value.id, data);
      ElMessage.success('模板更新成功');
    }
  } catch (error) {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

async function deleteTemplateById(template: StageTemplate) {
  try {
    await ElMessageBox.confirm(`确定删除模板「${template.name}」吗？`, '删除模板', { type: 'warning' });
    await templatesStore.deleteTemplate(template.id);
    if (selectedTemplate.value?.id === template.id) {
      selectedTemplate.value = null;
      isCreating.value = false;
    }
    ElMessage.success('模板已删除');
  } catch (error) { /* Cancelled */ }
}

onMounted(() => templatesStore.fetchTemplates());
</script>


<style scoped>
.templates-page {
  padding: var(--space-6);
  max-width: 1280px;
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

.templates-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .templates-layout { grid-template-columns: 1fr; }
}

/* Sidebar */
.templates-sidebar .tcgs-surface {
  overflow: hidden;
}

.sidebar-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.sidebar-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.templates-list {
  display: flex;
  flex-direction: column;
}

.template-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  cursor: pointer;
  border-bottom: 1px solid var(--color-border-light);
  transition: var(--transition-fast);
}

.template-item:hover {
  background: var(--color-neutral-50);
}

.template-item.active {
  background: var(--color-neutral-100);
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
}

.template-meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.template-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.delete-btn {
  opacity: 0;
  transition: var(--transition-fast);
}

.template-item:hover .delete-btn {
  opacity: 1;
}

.arrow-icon {
  color: var(--color-text-tertiary);
}

/* Edit Area */
.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.edit-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.edit-content {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
}

/* Stages */
.stages-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.stages-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stages-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  margin: 0;
}

.stages-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.stage-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
}

.stage-order {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding-top: var(--space-2);
}

.order-num {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-disabled);
}

.stage-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.stage-inputs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

@media (max-width: 640px) {
  .stage-inputs { grid-template-columns: 1fr; }
}

.stage-options {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

/* Preview */
.preview-section {
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border-light);
}

.preview-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-4) 0;
}

/* Empty State */
.empty-state {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-disabled);
  font-size: var(--text-sm);
}

.empty-edit {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.empty-text {
  color: var(--color-text-disabled);
  font-size: var(--text-sm);
}
</style>
