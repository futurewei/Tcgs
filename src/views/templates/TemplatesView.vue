<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Stage Templates</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="createNewTemplate">
        New Template
      </el-button>
    </div>

    <div class="grid grid-cols-12 gap-6">
      <!-- Left: Template List -->
      <div class="col-span-4">
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100">
            <h2 class="font-semibold text-zinc-900">Templates</h2>
          </div>
          <div class="divide-y divide-zinc-100">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="[
                'p-4 cursor-pointer transition-colors',
                selectedTemplate?.id === template.id ? 'bg-zinc-100' : 'hover:bg-zinc-50'
              ]"
              @click="selectTemplate(template)"
            >
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="font-medium text-zinc-900">{{ template.name }}</h3>
                  <p class="text-sm text-zinc-500">{{ template.stages?.length || 0 }} stages</p>
                </div>
                <el-icon v-if="selectedTemplate?.id === template.id"><ArrowRight /></el-icon>
              </div>
            </div>
            <div v-if="templates.length === 0" class="p-8 text-center text-zinc-400">
              No templates yet
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Edit Area -->
      <div class="col-span-8">
        <div v-if="selectedTemplate || isCreating" class="bg-white rounded-xl border border-zinc-200">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <h2 class="font-semibold text-zinc-900">
              {{ isCreating ? 'New Template' : 'Edit Template' }}
            </h2>
            <div class="flex items-center gap-2">
              <el-button v-if="!isCreating && authStore.isAdmin" type="danger" text @click="deleteTemplate">
                Delete
              </el-button>
              <el-button v-if="authStore.isAdmin" type="primary" :loading="saving" @click="saveTemplate">
                Save
              </el-button>
            </div>
          </div>

          <div class="p-6 space-y-6">
            <!-- Template Info -->
            <div class="grid grid-cols-2 gap-4">
              <el-form-item label="Name">
                <el-input v-model="form.name" placeholder="Template name" />
              </el-form-item>
              <el-form-item label="Description">
                <el-input v-model="form.description" placeholder="Template description" />
              </el-form-item>
            </div>

            <!-- Stages List -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-medium text-zinc-800">Stages</h3>
                <el-button size="small" @click="addStage">Add Stage</el-button>
              </div>

              <div class="space-y-3">
                <div
                  v-for="(stage, index) in form.stages"
                  :key="index"
                  class="p-4 bg-zinc-50 rounded-lg border border-zinc-200"
                >
                  <div class="flex items-start gap-4">
                    <div class="flex flex-col items-center gap-1 pt-2">
                      <el-button
                        size="small"
                        text
                        :disabled="index === 0"
                        @click="moveStage(index, -1)"
                      >
                        <el-icon><ArrowUp /></el-icon>
                      </el-button>
                      <span class="text-sm font-medium text-zinc-400">{{ index + 1 }}</span>
                      <el-button
                        size="small"
                        text
                        :disabled="index === form.stages.length - 1"
                        @click="moveStage(index, 1)"
                      >
                        <el-icon><ArrowDown /></el-icon>
                      </el-button>
                    </div>

                    <div class="flex-1 space-y-3">
                      <div class="grid grid-cols-2 gap-3">
                        <el-input v-model="stage.name" placeholder="Stage name" />
                        <el-input v-model="stage.description" placeholder="Description" />
                      </div>
                      <div class="flex items-center gap-4">
                        <el-checkbox v-model="stage.isTerminal">Terminal Stage</el-checkbox>
                        <el-checkbox v-model="stage.allowResult" :disabled="!stage.isTerminal">
                          Allow Result
                        </el-checkbox>
                        <el-checkbox v-model="stage.requireArtifact">Require Artifact</el-checkbox>
                      </div>
                    </div>

                    <el-button type="danger" text @click="removeStage(index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Timeline Preview -->
            <div class="pt-6 border-t border-zinc-200">
              <h3 class="font-medium text-zinc-800 mb-4">Timeline Preview</h3>
              <StageTimeline :stages="previewStages" />
            </div>
          </div>
        </div>

        <div v-else class="bg-white rounded-xl border border-zinc-200 p-12 text-center">
          <p class="text-zinc-400">Select a template to edit or create a new one</p>
        </div>
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

const previewStages = computed(() =>
  form.stages.map((s, i) => ({
    id: i + 1,
    templateId: 0,
    name: s.name || `Stage ${i + 1}`,
    description: s.description,
    order: i,
    isTerminal: s.isTerminal,
    allowResult: s.allowResult,
    requireArtifact: s.requireArtifact,
  }))
);

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
    { name: 'Definition', description: 'Define the problem', isTerminal: false, allowResult: false, requireArtifact: false },
    { name: 'Analysis', description: 'Analyze solutions', isTerminal: false, allowResult: false, requireArtifact: true },
    { name: 'Closure', description: 'Final review', isTerminal: true, allowResult: true, requireArtifact: false },
  ];
}

function addStage() {
  form.stages.push({
    name: '',
    description: '',
    isTerminal: false,
    allowResult: false,
    requireArtifact: false,
  });
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
  if (!form.name) {
    ElMessage.error('Please enter template name');
    return;
  }
  if (form.stages.length === 0) {
    ElMessage.error('Please add at least one stage');
    return;
  }

  saving.value = true;
  try {
    const data = {
      name: form.name,
      description: form.description,
      stages: form.stages.map((s, i) => ({
        name: s.name,
        description: s.description,
        order: i,
        isTerminal: s.isTerminal,
        allowResult: s.allowResult,
        requireArtifact: s.requireArtifact,
      })),
    };

    if (isCreating.value) {
      const template = await templatesStore.createTemplate(data);
      selectedTemplate.value = template;
      isCreating.value = false;
      ElMessage.success('Template created');
    } else if (selectedTemplate.value) {
      await templatesStore.updateTemplate(selectedTemplate.value.id, data);
      ElMessage.success('Template updated');
    }
  } catch (error) {
    ElMessage.error('Failed to save template');
  } finally {
    saving.value = false;
  }
}

async function deleteTemplate() {
  if (!selectedTemplate.value) return;

  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this template?',
      'Delete Template',
      { type: 'warning' }
    );
    await templatesStore.deleteTemplate(selectedTemplate.value.id);
    selectedTemplate.value = null;
    ElMessage.success('Template deleted');
  } catch (error) {
    // Cancelled
  }
}

onMounted(() => {
  templatesStore.fetchTemplates();
});
</script>
