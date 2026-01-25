<template>
  <div v-loading="loading" class="space-y-6">
    <div v-if="page">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <el-button text @click="router.push(`/wiki/directions/${page.directionId}`)">
            <el-icon class="mr-1"><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>
        <el-button type="primary" @click="router.push(`/wiki/pages/${page.id}/edit`)">
          <el-icon class="mr-1"><Edit /></el-icon>
          编辑
        </el-button>
      </div>

      <!-- Main Content -->
      <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <!-- Title & Stats -->
        <div class="p-6 border-b border-zinc-100">
          <h1 class="text-2xl font-bold text-zinc-900 mb-3">{{ page.title }}</h1>
          <div class="flex items-center gap-6 text-sm text-zinc-500">
            <div class="flex items-center gap-1">
              <el-icon><View /></el-icon>
              <span>{{ formatCount(page.viewCount || 0) }} 次浏览</span>
            </div>
            <div class="flex items-center gap-1">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ (page.comments?.length || 0) }} 条评论</span>
            </div>
            <div v-if="page.currentRevision" class="flex items-center gap-1">
              <el-icon><Clock /></el-icon>
              <span>{{ page.currentRevision.createdBy?.name }} 更新于 {{ formatDate(page.currentRevision.createdAt) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Content -->
        <div class="p-6 wiki-content">
          <MdPreview
            v-if="page.currentRevision?.content"
            :modelValue="page.currentRevision.content"
            language="zh-CN"
          />
          <p v-else class="text-zinc-400 text-center py-8">暂无内容</p>
        </div>
        
        <!-- Like Button -->
        <div class="px-6 py-4 border-t border-zinc-100 flex items-center justify-between">
          <el-button 
            :type="page.userLiked ? 'primary' : 'default'" 
            :icon="Star"
            @click="handleLike"
            :loading="liking"
          >
            {{ page.userLiked ? '已点赞' : '点赞' }} ({{ formatCount(likeCount) }})
          </el-button>
          
          <div class="text-xs text-zinc-400">
            版本 {{ page.currentRevision?.version || 1 }}
          </div>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <div class="p-4 border-b border-zinc-100">
          <h2 class="font-semibold text-zinc-900">评论 ({{ comments.length }})</h2>
        </div>
        
        <!-- Add Comment -->
        <div class="p-4 border-b border-zinc-100">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的评论..."
            maxlength="1000"
            show-word-limit
          />
          <div class="mt-2 flex justify-end">
            <el-button type="primary" @click="submitComment" :loading="submitting" :disabled="!newComment.trim()">
              发表评论
            </el-button>
          </div>
        </div>
        
        <!-- Comment List -->
        <div class="divide-y divide-zinc-100">
          <div v-for="comment in comments" :key="comment.id" class="p-4">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-zinc-200 flex items-center justify-center text-xs font-medium">
                {{ getInitials(comment.createdBy?.name) }}
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium text-sm">{{ comment.createdBy?.name || '匿名' }}</span>
                  <span class="text-xs text-zinc-400">{{ formatDate(comment.createdAt) }}</span>
                </div>
                <p class="text-sm text-zinc-700 whitespace-pre-wrap">{{ comment.content }}</p>
                
                <!-- Reply button -->
                <div class="mt-2 flex items-center gap-3">
                  <el-button text size="small" @click="toggleReply(comment.id)">回复</el-button>
                  <el-button 
                    v-if="canDeleteComment(comment)" 
                    text size="small" type="danger"
                    @click="deleteComment(comment.id)"
                  >删除</el-button>
                </div>
                
                <!-- Reply input -->
                <div v-if="replyingTo === comment.id" class="mt-3">
                  <el-input
                    v-model="replyContent"
                    type="textarea"
                    :rows="2"
                    placeholder="回复..."
                    size="small"
                  />
                  <div class="mt-2 flex gap-2">
                    <el-button size="small" @click="replyingTo = null">取消</el-button>
                    <el-button size="small" type="primary" @click="submitReply(comment.id)" :loading="submitting">回复</el-button>
                  </div>
                </div>
                
                <!-- Replies -->
                <div v-if="comment.replies?.length" class="mt-3 pl-4 border-l-2 border-zinc-100 space-y-3">
                  <div v-for="reply in comment.replies" :key="reply.id" class="text-sm">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-medium">{{ reply.createdBy?.name || '匿名' }}</span>
                      <span class="text-xs text-zinc-400">{{ formatDate(reply.createdAt) }}</span>
                    </div>
                    <p class="text-zinc-700">{{ reply.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="comments.length === 0" class="p-8 text-center text-zinc-400">
            暂无评论，来发表第一条评论吧
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useWikiStore } from '@/stores/wiki';
import { useAuthStore } from '@/stores/auth';
import { ArrowLeft, Edit, View, ChatDotRound, Clock, Star } from '@element-plus/icons-vue';
import { MdPreview } from 'md-editor-v3';
import { ElMessage, ElMessageBox } from 'element-plus';
import { wikiApi } from '@/api/wiki';
import dayjs from 'dayjs';
import 'md-editor-v3/lib/style.css';
import type { WikiComment } from '@/types';

const route = useRoute();
const router = useRouter();
const wikiStore = useWikiStore();
const authStore = useAuthStore();

const pageId = computed(() => Number(route.params.id));
const page = computed(() => wikiStore.currentPage);
const loading = computed(() => wikiStore.loading);

// Like
const liking = ref(false);
const likeCount = ref(0);

// Comments
const comments = ref<WikiComment[]>([]);
const newComment = ref('');
const replyingTo = ref<number | null>(null);
const replyContent = ref('');
const submitting = ref(false);

// Format count (防止大数字溢出，使用 K/M 缩写)
function formatCount(count: number): string {
  if (count >= 1000000000) return (count / 1000000000).toFixed(1) + 'B';
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
  return count.toString();
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
}

function getInitials(name?: string) {
  return name ? name.slice(0, 2) : '?';
}

function canDeleteComment(comment: WikiComment) {
  return comment.createdBy?.id === authStore.user?.id || authStore.isAdmin;
}

// Like
async function handleLike() {
  liking.value = true;
  try {
    const result = await wikiApi.toggleLike(pageId.value);
    likeCount.value = result.like_count;
    if (page.value) {
      (page.value as any).userLiked = result.liked;
    }
  } catch {
    ElMessage.error('操作失败');
  } finally {
    liking.value = false;
  }
}

// Comments
async function loadComments() {
  try {
    comments.value = await wikiApi.listComments(pageId.value);
  } catch {
    console.error('Failed to load comments');
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return;
  submitting.value = true;
  try {
    await wikiApi.createComment(pageId.value, newComment.value.trim());
    newComment.value = '';
    await loadComments();
    ElMessage.success('评论已发表');
  } catch {
    ElMessage.error('发表失败');
  } finally {
    submitting.value = false;
  }
}

function toggleReply(commentId: number) {
  replyingTo.value = replyingTo.value === commentId ? null : commentId;
  replyContent.value = '';
}

async function submitReply(parentId: number) {
  if (!replyContent.value.trim()) return;
  submitting.value = true;
  try {
    await wikiApi.createComment(pageId.value, replyContent.value.trim(), parentId);
    replyContent.value = '';
    replyingTo.value = null;
    await loadComments();
    ElMessage.success('回复已发表');
  } catch {
    ElMessage.error('回复失败');
  } finally {
    submitting.value = false;
  }
}

async function deleteComment(commentId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', { type: 'warning' });
    await wikiApi.deleteComment(commentId);
    await loadComments();
    ElMessage.success('评论已删除');
  } catch {}
}

// Load data
watch(pageId, async (id) => {
  if (id) {
    await wikiStore.fetchPage(id);
    await loadComments();
    likeCount.value = page.value?.likeCount || 0;
  }
}, { immediate: true });

onMounted(async () => {
  await wikiStore.fetchPage(pageId.value);
  await loadComments();
  likeCount.value = page.value?.likeCount || 0;
});
</script>

<style scoped>
/* Wiki content styles - 确保图片正确显示 */
.wiki-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
}

.wiki-content :deep(pre) {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.wiki-content :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.wiki-content :deep(h1),
.wiki-content :deep(h2),
.wiki-content :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.wiki-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.wiki-content :deep(th),
.wiki-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.wiki-content :deep(th) {
  background: #f9fafb;
}
</style>
