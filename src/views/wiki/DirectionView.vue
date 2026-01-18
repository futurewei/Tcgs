<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <el-button text @click="router.push('/wiki')">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>
        Back to Wiki
      </el-button>
    </div>

    <div v-if="direction" class="grid grid-cols-12 gap-6">
      <!-- Left: Page Tree -->
      <div class="col-span-3">
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden sticky top-20">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <h2 class="font-semibold text-zinc-900">{{ direction.name }}</h2>
            <el-button size="small" @click="showCreatePage = true">
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <div class="p-2 max-h-[600px] overflow-y-auto">
            <el-tree
              :data="pageTree"
              :props="{ label: 'title', children: 'children' }"
              node-key="id"
              :expand-on-click-node="false"
              @node-click="selectPage"
            >
              <template #default="{ node, data }">
                <div class="flex items-center justify-between w-full pr-2">
                  <span :class="selectedPageId === data.id ? 'font-medium text-zinc-900' : 'text-zinc-600'">
                    {{ node.label }}
                  </span>
                </div>
              </template>
            </el-tree>
            <div v-if="!direction.pages?.length" class="p-4 text-center text-zinc-400 text-sm">
              No pages yet
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Page Content -->
      <div class="col-span-9">
        <div v-if="selectedPage" class="bg-white rounded-xl border border-zinc-200">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <h1 class="text-xl font-bold text-zinc-900">{{ selectedPage.title }}</h1>
            <div class="flex items-center gap-2">
              <el-button size="small" @click="router.push(`/wiki/pages/${selectedPage.id}/edit`)">
                Edit
              </el-button>
              <el-dropdown trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="showRevisions = true">View History</el-dropdown-item>
                    <el-dropdown-item @click="deletePage">Delete</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <div class="p-6">
            <MdPreview
              :modelValue="selectedPage.currentRevision?.content || 'No content yet'"
              language="en-US"
            />
          </div>
          <div class="p-4 border-t border-zinc-100 text-xs text-zinc-400">
            Last updated {{ formatDate(selectedPage.currentRevision?.createdAt) }}
            by {{ selectedPage.currentRevision?.createdBy?.name }}
          </div>
        </div>

        <div v-else class="bg-white rounded-xl border border-zinc-200 p-12 text-center">
          <p class="text-zinc-400">Select a page from the sidebar</p>
        </div>
      </div>
    </div>

    <!-- Create Page Dialog -->
    <el-dialog v-model="showCreatePage" title="Create Page" width="500px">
      <el-form ref="formRef" :model="pageForm" :rules="pageRules" label-position="top">
        <el-form-item label="Title" prop="title">
          <el-input v-model="pageForm.title" placeholder="Page title" />
        </el-form-item>
        <el-form-item label="Parent Page">
          <el-select v-model="pageForm.parentId" class="w-full" clearable>
            <el-option
              v-for="page in flatPages"
              :key="page.id"
              :value="page.id"
              :label="page.title"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Initial Content">
          <el-input
            v-model="pageForm.content"
            type="textarea"
            :rows="4"
            placeholder="Initial content (Markdown supported)"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreatePage = false">Cancel</el-button>
        <el-button type="primary" :loading="creating" @click="createPage">Create</el-button>
      </template>
    </el-dialog>

    <!-- Revisions Dialog -->
    <el-dialog v-model="showRevisions" title="Page History" width="600px">
      <div class="space-y-3 max-h-[400px] overflow-y-auto">
        <div
          v-for="revision in revisions"
          :key="revision.id"
          class="p-4 bg-zinc-50 rounded-lg"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-medium">Version {{ revision.version }}</span>
            <span class="text-sm text-zinc-500">{{ formatDate(revision.createdAt) }}</span>
          </div>
          <p class="text-sm text-zinc-600">by {{ revision.createdBy?.name }}</p>
        </div>
        <div v-if="revisions.length === 0" class="text-center py-8 text-zinc-400">
          No revision history
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useWikiStore } from '@/stores/wiki';
import { ArrowLeft, Plus, MoreFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import dayjs from 'dayjs';
import type { WikiPage, WikiRevision } from '@/types';

const route = useRoute();
const router = useRouter();
const wikiStore = useWikiStore();

const directionId = computed(() => Number(route.params.id));
const direction = computed(() => wikiStore.currentDirection);
const selectedPageId = ref<number | null>(null);
const selectedPage = ref<WikiPage | null>(null);
const revisions = computed(() => wikiStore.revisions);

const showCreatePage = ref(false);
const showRevisions = ref(false);
const creating = ref(false);
const formRef = ref<FormInstance>();

const pageForm = reactive({
  title: '',
  parentId: undefined as number | undefined,
  content: '',
});

const pageRules: FormRules = {
  title: [{ required: true, message: 'Please enter title', trigger: 'blur' }],
};

const pageTree = computed(() => {
  const pages = direction.value?.pages || [];
  return buildTree(pages);
});

const flatPages = computed(() => {
  return direction.value?.pages || [];
});

function buildTree(pages: WikiPage[], parentId?: number): WikiPage[] {
  return pages
    .filter(p => p.parentId === parentId)
    .map(p => ({
      ...p,
      children: buildTree(pages, p.id),
    }));
}

function selectPage(page: WikiPage) {
  selectedPageId.value = page.id;
  wikiStore.fetchPage(page.id).then(() => {
    selectedPage.value = wikiStore.currentPage;
  });
}

async function createPage() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    creating.value = true;
    try {
      const page = await wikiStore.createPage({
        directionId: directionId.value,
        title: pageForm.title,
        parentId: pageForm.parentId,
        content: pageForm.content,
      });

      showCreatePage.value = false;
      pageForm.title = '';
      pageForm.parentId = undefined;
      pageForm.content = '';

      selectPage(page);
      ElMessage.success('Page created');
    } catch (error) {
      ElMessage.error('Failed to create page');
    } finally {
      creating.value = false;
    }
  });
}

async function deletePage() {
  if (!selectedPage.value) return;

  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this page?',
      'Delete Page',
      { type: 'warning' }
    );
    // await wikiApi.deletePage(selectedPage.value.id);
    selectedPage.value = null;
    selectedPageId.value = null;
    await wikiStore.fetchDirection(directionId.value);
    ElMessage.success('Page deleted');
  } catch (error) {
    // Cancelled
  }
}

function formatDate(date?: string) {
  if (!date) return 'N/A';
  return dayjs(date).format('MMM D, YYYY h:mm A');
}

watch(() => showRevisions.value, (show) => {
  if (show && selectedPage.value) {
    wikiStore.fetchRevisions(selectedPage.value.id);
  }
});

onMounted(() => {
  wikiStore.fetchDirection(directionId.value);
});
</script>
