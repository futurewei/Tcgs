<template>
  <div class="rich-text-editor">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 p-2 border-b border-zinc-200 bg-zinc-50 rounded-t-lg">
      <el-button size="small" text @click="execCommand('bold')" title="加粗">
        <span class="font-bold">B</span>
      </el-button>
      <el-button size="small" text @click="execCommand('italic')" title="斜体">
        <span class="italic">I</span>
      </el-button>
      <el-button size="small" text @click="execCommand('underline')" title="下划线">
        <span class="underline">U</span>
      </el-button>
      <div class="w-px h-4 bg-zinc-300 mx-1"></div>
      <el-button size="small" text @click="execCommand('insertUnorderedList')" title="无序列表">
        <el-icon><List /></el-icon>
      </el-button>
      <el-button size="small" text @click="execCommand('insertOrderedList')" title="有序列表">
        <el-icon><Rank /></el-icon>
      </el-button>
      <div class="w-px h-4 bg-zinc-300 mx-1"></div>
      <el-button size="small" text @click="insertLink" title="插入链接">
        <el-icon><Link /></el-icon>
      </el-button>
      <el-button size="small" text @click="triggerImageUpload" title="插入图片" :loading="uploading">
        <el-icon><Picture /></el-icon>
      </el-button>
      <input
        ref="imageInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handleImageUpload"
      />
    </div>
    
    <!-- Editor -->
    <div
      ref="editorRef"
      class="min-h-[120px] p-3 bg-white border border-t-0 border-zinc-200 rounded-b-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset prose prose-sm max-w-none"
      contenteditable="true"
      :placeholder="placeholder"
      @input="handleInput"
      @blur="handleBlur"
      @paste="handlePaste"
      v-html="internalValue"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue';
import { List, Rank, Link, Picture } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { uploadApi } from '@/api/upload';

const props = defineProps<{
  modelValue: string;
  placeholder?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const editorRef = ref<HTMLDivElement>();
const imageInput = ref<HTMLInputElement>();
const internalValue = ref(props.modelValue || '');
const uploading = ref(false);

watch(() => props.modelValue, (newVal) => {
  if (newVal !== internalValue.value) {
    internalValue.value = newVal || '';
  }
});

function handleInput() {
  if (editorRef.value) {
    const html = editorRef.value.innerHTML;
    internalValue.value = html;
    emit('update:modelValue', html);
  }
}

function handleBlur() {
  handleInput();
}

function execCommand(command: string, value?: string) {
  document.execCommand(command, false, value);
  editorRef.value?.focus();
  handleInput();
}

async function insertLink() {
  try {
    const { value: url } = await ElMessageBox.prompt('请输入链接地址', '插入链接', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: 'https://',
      inputValue: 'https://'
    });
    if (url) {
      execCommand('createLink', url);
    }
  } catch {}
}

function triggerImageUpload() {
  imageInput.value?.click();
}

async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件');
    return;
  }

  // 检查文件大小（最大 10MB）
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB');
    return;
  }

  uploading.value = true;
  try {
    const result = await uploadApi.uploadImage(file);
    // 插入图片
    execCommand('insertImage', result.url);
    ElMessage.success('图片上传成功');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '图片上传失败');
  } finally {
    uploading.value = false;
    // 清空 input 以便再次选择同一文件
    input.value = '';
  }
}

// 处理粘贴（支持直接粘贴图片）
async function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const file = item.getAsFile();
      if (file) {
        // 检查文件大小
        if (file.size > 10 * 1024 * 1024) {
          ElMessage.error('图片大小不能超过 10MB');
          return;
        }

        uploading.value = true;
        try {
          const result = await uploadApi.uploadImage(file);
          execCommand('insertImage', result.url);
          ElMessage.success('图片上传成功');
        } catch {
          ElMessage.error('图片上传失败');
        } finally {
          uploading.value = false;
        }
      }
      return;
    }
  }
}

onMounted(() => {
  // 设置 placeholder 样式
  if (editorRef.value && props.placeholder) {
    editorRef.value.setAttribute('data-placeholder', props.placeholder);
  }
});
</script>

<style scoped>
.rich-text-editor [contenteditable]:empty:before {
  content: attr(data-placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.rich-text-editor [contenteditable] img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}

.rich-text-editor [contenteditable] a {
  color: #2563eb;
  text-decoration: underline;
}
</style>
