<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="Add Artifact"
    width="700px"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Title" prop="title">
        <el-input v-model="form.title" placeholder="Artifact title" />
      </el-form-item>

      <el-form-item label="Content" prop="content">
        <MdEditor
          v-model="form.content"
          language="en-US"
          :preview="false"
          style="height: 300px"
          @on-upload-img="handleUploadImg"
        />
        <p class="text-xs text-zinc-400 mt-1">支持直接粘贴图片 (Ctrl+V / Cmd+V)</p>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        Add Artifact
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { topicsApi } from '@/api/topics';
import { uploadApi } from '@/api/upload';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

const props = defineProps<{
  modelValue: boolean;
  topicId: number;
  stageId: number | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'created'): void;
}>();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  title: '',
  content: '',
});

const rules: FormRules = {
  title: [{ required: true, message: 'Please enter title', trigger: 'blur' }],
  content: [{ required: true, message: 'Please enter content', trigger: 'blur' }],
};

// 处理图片上传（支持粘贴和拖拽）
async function handleUploadImg(files: File[], callback: (urls: string[]) => void) {
  const urls: string[] = [];
  for (const file of files) {
    try {
      const result = await uploadApi.uploadImage(file, 'artifacts');
      urls.push(result.url);
    } catch (error) {
      ElMessage.error(`Upload failed: ${file.name}`);
    }
  }
  callback(urls);
}

async function handleSubmit() {
  if (!formRef.value || !props.stageId) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await topicsApi.createArtifact({
        topicId: props.topicId,
        stageId: props.stageId,
        title: form.title,
        content: form.content,
      });

      ElMessage.success('Artifact added');
      form.title = '';
      form.content = '';
      emit('update:modelValue', false);
      emit('created');
    } catch (error) {
      ElMessage.error('Failed to add artifact');
    } finally {
      loading.value = false;
    }
  });
}
</script>
