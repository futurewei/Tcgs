<template>
  <div class="rich-editor">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 p-2 border-b border-zinc-200 bg-zinc-50 rounded-t-lg">
      <el-button-group>
        <el-button size="small" text @click="execCommand('bold')" title="加粗">
          <strong>B</strong>
        </el-button>
        <el-button size="small" text @click="execCommand('italic')" title="斜体">
          <em>I</em>
        </el-button>
        <el-button size="small" text @click="execCommand('underline')" title="下划线">
          <u>U</u>
        </el-button>
      </el-button-group>
      
      <div class="w-px h-4 bg-zinc-300 mx-1"></div>
      
      <el-button-group>
        <el-button size="small" text @click="execCommand('insertUnorderedList')" title="无序列表">
          <el-icon><List /></el-icon>
        </el-button>
        <el-button size="small" text @click="execCommand('insertOrderedList')" title="有序列表">
          <el-icon><Document /></el-icon>
        </el-button>
      </el-button-group>
      
      <div class="w-px h-4 bg-zinc-300 mx-1"></div>
      
      <!-- 图片上传 -->
      <el-upload
        ref="uploadRef"
        :show-file-list="false"
        :before-upload="beforeImageUpload"
        :http-request="handleImageUpload"
        accept="image/*"
      >
        <el-button size="small" text :loading="uploading" title="插入图片">
          <el-icon><Picture /></el-icon>
        </el-button>
      </el-upload>
      
      <el-button size="small" text @click="showLinkDialog = true" title="插入链接">
        <el-icon><Link /></el-icon>
      </el-button>
    </div>
    
    <!-- Editor Content -->
    <div
      ref="editorRef"
      class="min-h-[250px] max-h-[500px] overflow-y-auto p-4 border border-t-0 border-zinc-200 rounded-b-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      contenteditable="true"
      :placeholder="placeholder"
      @input="handleInput"
      @paste="handlePaste"
      @blur="handleBlur"
    ></div>
    
    <!-- Link Dialog -->
    <el-dialog v-model="showLinkDialog" title="插入链接" width="400px">
      <el-form label-position="top">
        <el-form-item label="链接文字">
          <el-input v-model="linkForm.text" placeholder="显示的文字" />
        </el-form-item>
        <el-form-item label="链接地址">
          <el-input v-model="linkForm.url" placeholder="https://" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLinkDialog = false">取消</el-button>
        <el-button type="primary" @click="insertLink">插入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue';
import { Picture, Link, List, Document } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { uploadApi } from '@/api/upload';

const props = defineProps<{
  modelValue: string;
  placeholder?: string;
  folder?: string; // 图片上传的文件夹
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const editorRef = ref<HTMLElement | null>(null);
const uploading = ref(false);
const showLinkDialog = ref(false);
const linkForm = ref({ text: '', url: '' });

// 初始化内容
onMounted(() => {
  if (editorRef.value && props.modelValue) {
    editorRef.value.innerHTML = props.modelValue;
  }
});

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (editorRef.value && editorRef.value.innerHTML !== newVal) {
    editorRef.value.innerHTML = newVal || '';
  }
});

function handleInput() {
  if (editorRef.value) {
    emit('update:modelValue', editorRef.value.innerHTML);
  }
}

function handleBlur() {
  handleInput();
}

function execCommand(command: string, value?: string) {
  document.execCommand(command, false, value);
  editorRef.value?.focus();
}

// 图片上传前检查
function beforeImageUpload(file: File) {
  const isImage = file.type.startsWith('image/');
  const isLt5M = file.size / 1024 / 1024 < 5;
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件');
    return false;
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB');
    return false;
  }
  return true;
}

// 处理图片上传
async function handleImageUpload(options: any) {
  const file = options.file as File;
  uploading.value = true;
  
  try {
    const result = await uploadApi.uploadImage(file, props.folder || 'rich-text');
    insertImage(result.url, file.name);
    ElMessage.success('图片上传成功');
  } catch (error) {
    ElMessage.error('图片上传失败');
  } finally {
    uploading.value = false;
  }
}

// 插入图片
function insertImage(url: string, alt: string = '') {
  const img = `<img src="${url}" alt="${alt}" style="max-width: 100%; height: auto; margin: 8px 0;" />`;
  execCommand('insertHTML', img);
}

// 插入链接
function insertLink() {
  if (!linkForm.value.url) {
    ElMessage.warning('请输入链接地址');
    return;
  }
  
  const text = linkForm.value.text || linkForm.value.url;
  const link = `<a href="${linkForm.value.url}" target="_blank" class="text-blue-600 hover:underline">${text}</a>`;
  execCommand('insertHTML', link);
  
  showLinkDialog.value = false;
  linkForm.value = { text: '', url: '' };
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
        uploading.value = true;
        try {
          const result = await uploadApi.uploadImage(file, props.folder || 'rich-text');
          insertImage(result.url, 'pasted-image');
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
</script>

<style scoped>
.rich-editor [contenteditable]:empty:before {
  content: attr(placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.rich-editor [contenteditable] {
  min-height: 200px;
}

.rich-editor :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 8px 0;
  display: block;
}

.rich-editor :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.rich-editor :deep(ul),
.rich-editor :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.rich-editor :deep(p) {
  margin: 0.5em 0;
}
</style>
