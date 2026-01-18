<template>
  <div v-loading="loading" class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <el-button text @click="goBack">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          Back
        </el-button>
        <h1 class="text-xl font-bold text-zinc-900">Edit: {{ page?.title }}</h1>
      </div>
      <div class="flex items-center gap-2">
        <el-button @click="goBack">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="saveRevision">
          Save Revision
        </el-button>
      </div>
    </div>

    <div v-if="page" class="grid grid-cols-12 gap-6">
      <!-- Editor -->
      <div class="col-span-8">
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <MdEditor
            v-model="content"
            language="en-US"
            style="height: 600px"
          />
        </div>
      </div>

      <!-- Sidebar: Revision History -->
      <div class="col-span-4">
        <div class="bg-white rounded-xl border border-zinc-200 sticky top-20">
          <div class="p-4 border-b border-zinc-100">
            <h2 class="font-semibold text-zinc-900">Revision History</h2>
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
                <span class="font-medium text-sm">Version {{ revision.version }}</span>
                <el-tag v-if="revision.id === page.currentRevisionId" size="small" type="success">
                  Current
                </el-tag>
              </div>
              <p class="text-xs text-zinc-500">
                {{ revision.createdBy?.name }} • {{ formatDate(revision.createdAt) }}
              </p>
            </div>
            <div v-if="revisions.length === 0" class="text-center py-4 text-zinc-400 text-sm">
              No revisions yet
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="text-xs text-zinc-400 text-center">
      Revisions are append-only. Each save creates a new revision and cannot be deleted.
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
    ElMessage.success('Revision saved');
    await wikiStore.fetchRevisions(page.value.id);
  } catch (error) {
    ElMessage.error('Failed to save revision');
  } finally {
    saving.value = false;
  }
}

function formatDate(date: string) {
  return dayjs(date).format('MMM D, YYYY h:mm A');
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
