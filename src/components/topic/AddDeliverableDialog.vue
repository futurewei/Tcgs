<template>
  <el-dialog
    :model-value="modelValue"
    title="Add Deliverable"
    width="560px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Name" prop="name">
        <el-input v-model="form.name" placeholder="e.g. Design Document, API Spec, Prototype..." />
      </el-form-item>

      <el-form-item label="Type" prop="type">
        <el-radio-group v-model="form.type" class="w-full">
          <div class="grid grid-cols-2 gap-3 w-full">
            <div 
              :class="[
                'flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all',
                form.type === 'link' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-zinc-200 hover:border-zinc-300'
              ]"
              @click="form.type = 'link'"
            >
              <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <el-icon class="text-blue-600" :size="20"><Link /></el-icon>
              </div>
              <div>
                <p class="font-medium text-zinc-800">Link</p>
                <p class="text-xs text-zinc-500">URL to external resource</p>
              </div>
            </div>
            <div 
              :class="[
                'flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all',
                form.type === 'file' 
                  ? 'border-emerald-500 bg-emerald-50' 
                  : 'border-zinc-200 hover:border-zinc-300'
              ]"
              @click="form.type = 'file'"
            >
              <div class="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                <el-icon class="text-emerald-600" :size="20"><Document /></el-icon>
              </div>
              <div>
                <p class="font-medium text-zinc-800">File</p>
                <p class="text-xs text-zinc-500">Uploaded file reference</p>
              </div>
            </div>
          </div>
        </el-radio-group>
      </el-form-item>

      <!-- Quick Link Templates -->
      <div v-if="form.type === 'link'" class="mb-4">
        <p class="text-xs text-zinc-500 mb-2">Quick templates:</p>
        <div class="flex flex-wrap gap-2">
          <el-button 
            v-for="tpl in linkTemplates" 
            :key="tpl.name"
            size="small" 
            :type="getTemplateButtonType(tpl.prefix)"
            plain
            @click="applyLinkTemplate(tpl)"
          >
            {{ tpl.name }}
          </el-button>
        </div>
      </div>

      <el-form-item label="URL" prop="url">
        <el-input
          v-model="form.url"
          :placeholder="form.type === 'link' ? 'https://...' : 'File storage URL (MinIO, OSS, etc.)'"
        >
          <template v-if="form.type === 'link'" #prefix>
            <el-icon><Link /></el-icon>
          </template>
        </el-input>
        <div class="text-xs text-zinc-400 mt-1">
          <template v-if="form.type === 'link'">
            Feishu / Confluence / Notion / GitHub / Figma links supported
          </template>
          <template v-else>
            Enter the URL where the file is hosted
          </template>
        </div>
      </el-form-item>

      <el-form-item label="Description" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="Brief description of this deliverable (optional)..."
        />
      </el-form-item>

      <!-- File metadata (only for file type) -->
      <div v-if="form.type === 'file'" class="grid grid-cols-2 gap-4">
        <el-form-item label="File Name" prop="fileName">
          <el-input v-model="form.fileName" placeholder="original_filename.pdf" />
        </el-form-item>
        <el-form-item label="File Size (bytes)" prop="fileSize">
          <el-input-number 
            v-model="form.fileSize" 
            :min="0" 
            :controls="false"
            placeholder="1024"
            class="w-full"
          />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <div class="flex items-center justify-between">
        <span class="text-xs text-zinc-400">
          Stage: {{ stageName }}
        </span>
        <div class="flex gap-2">
          <el-button @click="$emit('update:modelValue', false)">Cancel</el-button>
          <el-button type="primary" :loading="loading" @click="submit">
            Add Deliverable
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { Link, Document } from '@element-plus/icons-vue';
import { topicsApi } from '@/api/topics';
import { useTopicsStore } from '@/stores/topics';
import type { DeliverableType } from '@/types';

interface LinkTemplate {
  name: string;
  prefix: string;
}

const props = defineProps<{
  modelValue: boolean;
  topicId: number;
  stageId: number | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'created'): void;
}>();

const topicsStore = useTopicsStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  name: '',
  type: 'link' as DeliverableType,
  url: '',
  description: '',
  fileName: '',
  fileSize: undefined as number | undefined,
});

const linkTemplates: LinkTemplate[] = [
  { name: 'Feishu Doc', prefix: 'https://bytedance.feishu.cn/docx/' },
  { name: 'Confluence', prefix: 'https://confluence.atlassian.net/wiki/' },
  { name: 'Notion', prefix: 'https://notion.so/' },
  { name: 'GitHub', prefix: 'https://github.com/' },
  { name: 'Figma', prefix: 'https://figma.com/' },
];

const stageName = computed(() => {
  if (!props.stageId || !topicsStore.currentTopic?.template?.stages) return 'Unknown';
  const stage = topicsStore.currentTopic.template.stages.find(s => s.id === props.stageId);
  return stage?.name || 'Unknown';
});

const rules: FormRules = {
  name: [{ required: true, message: 'Please enter a name', trigger: 'blur' }],
  type: [{ required: true, message: 'Please select type', trigger: 'change' }],
  url: [
    { required: true, message: 'Please enter URL', trigger: 'blur' },
    { 
      pattern: /^https?:\/\/.+/,
      message: 'Please enter a valid URL starting with http:// or https://',
      trigger: 'blur'
    }
  ],
};

function getTemplateButtonType(prefix: string): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  if (form.url.startsWith(prefix)) return 'primary';
  return '';
}

function applyLinkTemplate(tpl: LinkTemplate) {
  form.url = tpl.prefix;
  if (!form.name) {
    form.name = tpl.name;
  }
}

function resetForm() {
  form.name = '';
  form.type = 'link';
  form.url = '';
  form.description = '';
  form.fileName = '';
  form.fileSize = undefined;
  formRef.value?.resetFields();
}

async function submit() {
  if (!props.stageId) {
    ElMessage.warning('No stage selected');
    return;
  }

  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await topicsApi.createDeliverable(props.topicId, {
      stageId: props.stageId,
      name: form.name,
      type: form.type,
      url: form.url,
      description: form.description || undefined,
      fileName: form.type === 'file' ? form.fileName || undefined : undefined,
      fileSize: form.type === 'file' ? form.fileSize : undefined,
    });

    ElMessage.success('Deliverable added');
    emit('update:modelValue', false);
    emit('created');
    resetForm();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to add deliverable');
  } finally {
    loading.value = false;
  }
}
</script>
