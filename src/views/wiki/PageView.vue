<template>
  <div v-loading="loading" class="space-y-6">
    <div v-if="page">
      <div class="flex items-center gap-4 mb-6">
        <el-button text @click="router.push(`/wiki/directions/${page.directionId}`)">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          Back
        </el-button>
      </div>

      <div class="bg-white rounded-xl border border-zinc-200">
        <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
          <h1 class="text-xl font-bold text-zinc-900">{{ page.title }}</h1>
          <el-button @click="router.push(`/wiki/pages/${page.id}/edit`)">Edit</el-button>
        </div>
        <div class="p-6">
          <MdPreview
            :modelValue="page.currentRevision?.content || 'No content yet'"
            language="en-US"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useWikiStore } from '@/stores/wiki';
import { ArrowLeft } from '@element-plus/icons-vue';
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

const route = useRoute();
const router = useRouter();
const wikiStore = useWikiStore();

const pageId = computed(() => Number(route.params.id));
const page = computed(() => wikiStore.currentPage);
const loading = computed(() => wikiStore.loading);

onMounted(() => {
  wikiStore.fetchPage(pageId.value);
});
</script>
