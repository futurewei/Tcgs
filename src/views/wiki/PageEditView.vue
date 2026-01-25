<template>
  <div v-loading="loading" class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <el-button text @click="goBack">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="text-xl font-bold text-zinc-900">编辑: {{ page?.title }}</h1>
      </div>
      <div class="flex items-center gap-2">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRevision">
          保存版本
        </el-button>
      </div>
    </div>

    <div v-if="page" class="grid grid-cols-12 gap-6">
      <!-- Editor -->
      <div class="col-span-8">
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <MdEditor
            v-model="content"
            language="zh-CN"
            style="height: 600px"
            :on-upload-img="handleUploadImg"
            :toolbars="toolbars"
          />
        </div>
      </div>

      <!-- Sidebar: Revision History -->
      <div class="col-span-4">
        <div class="bg-white rounded-xl border border-zinc-200 sticky top-20">
          <div class="p-4 border-b border-zinc-100">
            <h2 class="font-semibold text-zinc-900">版本历史</h2>
          </div>
          <div class="p-4 space-y-3 max-h-[500px] overflow-y-auto">
            <div
              v-for="revision in revisions"
              :key="revision.id"
              :class="[
                'p-3 rounded-lg cursor-pointer transition-colors',
                selectedRevisionId === revision.id ? 'bg-zinc-200' : 'bg-zinc-50 hover:bg-zinc-100'
              ]"
              @click="loadRevision(revision)"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-sm">版本 {{ revision.version }}</span>
                <el-tag v-if="revision.id === page.currentRevisionId" size="small" type="success">
                  当前
                </el-tag>
              </div>
              <p class="text-xs text-zinc-500">
                {{ revision.createdBy?.name }} • {{ formatDate(revision.createdAt) }}
              </p>
            </div>
            <div v-if="revisions.length === 0" class="text-center py-4 text-zinc-400 text-sm">
              暂无版本
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="text-xs text-zinc-400 text-center">
      版本只能追加，不能删除。每次保存会创建一个新版本。
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useWikiStore } from '@/stores/wiki';
import { ArrowLeft } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import dayjs from 'dayjs';
import type { WikiRevision } from '@/types';
import { uploadApi } from '@/api/upload';

const route = useRoute();
const router = useRouter();
const wikiStore = useWikiStore();

const pageId = computed(() => Number(route.params.id));
const page = computed(() => wikiStore.currentPage);
const revisions = computed(() => wikiStore.revisions);
const loading = computed(() => wikiStore.loading);

const content = ref('');
const saving = ref(false);
const selectedRevisionId = ref<number | null>(null);

// Markdown 编辑器工具栏配置
const toolbars = [
  'bold', 'underline', 'italic', '-',
  'title', 'strikeThrough', 'sub', 'sup', 'quote', 'unorderedList', 'orderedList', 'task', '-',
  'codeRow', 'code', 'link', 'image', 'table', 'mermaid', 'katex', '-',
  'revoke', 'next', 'save', '=',
  'pageFullscreen', 'fullscreen', 'preview', 'htmlPreview', 'catalog'
];

// 处理图片上传
async function handleUploadImg(files: File[], callback: (urls: string[]) => void) {
  const urls: string[] = [];
  
  for (const file of files) {
    try {
      const result = await uploadApi.uploadImage(file, 'wiki');
      urls.push(result.url);
    } catch (error) {
      ElMessage.error(`上传 ${file.name} 失败`);
    }
  }
  
  callback(urls);
}

function goBack() {
  if (page.value?.directionId) {
    router.push(`/wiki/directions/${page.value.directionId}`);
  } else {
    router.push('/wiki');
  }
}

function loadRevision(revision: WikiRevision) {
  selectedRevisionId.value = revision.id;
  content.value = revision.content;
}

async function saveRevision() {
  if (!page.value) return;

  saving.value = true;
  try {
    await wikiStore.createRevision(page.value.id, content.value);
    ElMessage.success('版本已保存');
    await wikiStore.fetchRevisions(page.value.id);
  } catch (error) {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
}

onMounted(async () => {
  await wikiStore.fetchPage(pageId.value);
  await wikiStore.fetchRevisions(pageId.value);

  if (page.value?.currentRevision) {
    content.value = page.value.currentRevision.content;
    selectedRevisionId.value = page.value.currentRevisionId || null;
  }
});
</script>
