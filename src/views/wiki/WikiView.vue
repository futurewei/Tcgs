<template>
  <div class="h-[calc(100vh-120px)] flex gap-4">
    <!-- 左侧：类别列表 -->
    <div class="w-64 flex-shrink-0 bg-white rounded-xl border border-zinc-200 overflow-hidden flex flex-col">
      <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
        <h2 class="font-semibold text-zinc-900">技术类别</h2>
        <el-button size="small" type="primary" text @click="showAddCategory = true">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="group px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-zinc-50 transition-colors"
          :class="selectedCategoryId === cat.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''"
          @click="selectCategory(cat)"
        >
          <div class="flex items-center gap-2 min-w-0">
            <el-icon class="text-zinc-400"><Folder /></el-icon>
            <span class="truncate" :class="selectedCategoryId === cat.id ? 'text-blue-600 font-medium' : 'text-zinc-700'">
              {{ cat.name }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span class="text-xs text-zinc-400">{{ cat.pages?.length || 0 }}</span>
            <el-button
              v-if="authStore.isAdmin"
              class="opacity-0 group-hover:opacity-100 transition-opacity"
              size="small"
              type="danger"
              text
              @click.stop="deleteCategory(cat)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div v-if="categories.length === 0" class="p-4 text-center text-zinc-400 text-sm">
          暂无类别
        </div>
      </div>
    </div>

    <!-- 中间：文章列表 -->
    <div class="w-80 flex-shrink-0 bg-white rounded-xl border border-zinc-200 overflow-hidden flex flex-col">
      <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
        <h2 class="font-semibold text-zinc-900">
          {{ selectedCategory?.name || '文章列表' }}
        </h2>
        <el-button v-if="selectedCategory" size="small" type="primary" @click="startWriteArticle">
          <el-icon class="mr-1"><Edit /></el-icon>写文章
        </el-button>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="article in currentArticles"
          :key="article.id"
          class="px-4 py-3 border-b border-zinc-50 cursor-pointer hover:bg-zinc-50 transition-colors"
          :class="selectedArticleId === article.id ? 'bg-blue-50' : ''"
          @click="selectArticle(article)"
        >
          <h4 class="font-medium text-zinc-800 mb-1 truncate">{{ article.title }}</h4>
          <div class="flex items-center gap-3 text-xs text-zinc-400">
            <span class="flex items-center gap-1">
              <el-icon><View /></el-icon>{{ formatCount(article.viewCount || 0) }}
            </span>
            <span class="flex items-center gap-1">
              <el-icon><Star /></el-icon>{{ formatCount(article.likeCount || 0) }}
            </span>
            <span>{{ formatDate(article.updatedAt) }}</span>
          </div>
        </div>
        <div v-if="selectedCategory && currentArticles.length === 0" class="p-8 text-center text-zinc-400 text-sm">
          该类别下暂无文章
        </div>
        <div v-if="!selectedCategory" class="p-8 text-center text-zinc-400 text-sm">
          请先选择一个类别
        </div>
      </div>
    </div>

    <!-- 右侧：文章详情 -->
    <div class="flex-1 bg-white rounded-xl border border-zinc-200 overflow-hidden flex flex-col">
      <!-- 写文章模式 -->
      <template v-if="isWriting">
        <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
          <el-input
            v-model="articleForm.title"
            placeholder="请输入文章标题"
            class="!w-auto flex-1 mr-4"
            size="large"
          />
          <div class="flex items-center gap-2">
            <el-button @click="cancelWrite">取消</el-button>
            <el-button type="primary" @click="saveArticle" :loading="saving">
              {{ editingArticle ? '更新' : '发布' }}
            </el-button>
          </div>
        </div>
        <div class="flex-1 overflow-hidden">
          <MdEditor
            v-model="articleForm.content"
            language="zh-CN"
            :toolbars="toolbars"
            @on-upload-img="handleUploadImg"
            style="height: 100%"
          />
        </div>
      </template>

      <!-- 阅读模式 -->
      <template v-else-if="selectedArticle">
        <div class="p-4 border-b border-zinc-100">
          <div class="flex items-center justify-between mb-3">
            <h1 class="text-xl font-bold text-zinc-900">{{ selectedArticle.title }}</h1>
            <div v-if="canEditArticle" class="flex items-center gap-2">
              <el-button size="small" @click="editArticle">
                <el-icon class="mr-1"><Edit /></el-icon>编辑
              </el-button>
              <el-button size="small" type="danger" text @click="deleteArticle">删除</el-button>
            </div>
          </div>
          <div class="flex items-center gap-4 text-sm text-zinc-500">
            <span class="flex items-center gap-1">
              <el-icon><View /></el-icon>
              {{ formatCount(selectedArticle.viewCount || 0) }} 次浏览
            </span>
            <span v-if="selectedArticle.currentRevision">
              {{ selectedArticle.currentRevision.createdBy?.name }} 更新于 {{ formatDate(selectedArticle.currentRevision.createdAt) }}
            </span>
          </div>
        </div>

        <!-- 文章内容 -->
        <div class="flex-1 overflow-y-auto">
          <div class="p-6 article-content">
            <MdPreview
              v-if="selectedArticle.currentRevision?.content"
              :modelValue="selectedArticle.currentRevision.content"
              language="zh-CN"
            />
            <p v-else class="text-zinc-400 text-center py-8">暂无内容</p>
          </div>

          <!-- 点赞栏 -->
          <div class="px-6 py-4 border-t border-zinc-100 flex items-center gap-4">
            <el-button
              :type="selectedArticle.userLiked ? 'primary' : 'default'"
              @click="toggleLike"
              :loading="liking"
              round
            >
              <el-icon class="mr-1"><Star /></el-icon>
              {{ selectedArticle.userLiked ? '已点赞' : '点赞' }}
              <span class="ml-1">({{ formatCount(likeCount) }})</span>
            </el-button>
          </div>

          <!-- 评论区 -->
          <div class="border-t border-zinc-100">
            <div class="px-6 py-4 border-b border-zinc-50">
              <h3 class="font-semibold text-zinc-800">评论 ({{ comments.length }})</h3>
            </div>

            <!-- 发表评论 -->
            <div class="px-6 py-4 border-b border-zinc-100 bg-zinc-50">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="2"
                placeholder="发表你的评论..."
                maxlength="500"
              />
              <div class="mt-2 flex justify-end">
                <el-button type="primary" size="small" @click="submitComment" :loading="submittingComment" :disabled="!newComment.trim()">
                  发表
                </el-button>
              </div>
            </div>

            <!-- 评论列表 -->
            <div class="divide-y divide-zinc-50">
              <div v-for="comment in comments" :key="comment.id" class="px-6 py-4">
                <div class="flex items-start gap-3">
                  <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium flex-shrink-0">
                    {{ getInitials(comment.createdBy?.name) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-medium text-sm text-zinc-800">{{ comment.createdBy?.name || '匿名' }}</span>
                      <span class="text-xs text-zinc-400">{{ formatDateTime(comment.createdAt) }}</span>
                    </div>
                    <p class="text-sm text-zinc-600 whitespace-pre-wrap break-words">{{ comment.content }}</p>

                    <div class="mt-2 flex items-center gap-3">
                      <el-button text size="small" @click="startReply(comment.id)">回复</el-button>
                      <el-button v-if="canDelete(comment)" text size="small" type="danger" @click="deleteComment(comment.id)">删除</el-button>
                    </div>

                    <!-- 回复输入框 -->
                    <div v-if="replyingTo === comment.id" class="mt-3 pl-4 border-l-2 border-blue-200">
                      <el-input v-model="replyContent" type="textarea" :rows="2" placeholder="回复..." size="small" />
                      <div class="mt-2 flex gap-2">
                        <el-button size="small" @click="replyingTo = null">取消</el-button>
                        <el-button size="small" type="primary" @click="submitReply(comment.id)" :loading="submittingComment">回复</el-button>
                      </div>
                    </div>

                    <!-- 回复列表 -->
                    <div v-if="comment.replies?.length" class="mt-3 space-y-3 pl-4 border-l-2 border-zinc-100">
                      <div v-for="reply in comment.replies" :key="reply.id" class="text-sm">
                        <div class="flex items-center gap-2 mb-1">
                          <span class="font-medium text-zinc-700">{{ reply.createdBy?.name || '匿名' }}</span>
                          <span class="text-xs text-zinc-400">{{ formatDateTime(reply.createdAt) }}</span>
                        </div>
                        <p class="text-zinc-600">{{ reply.content }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="comments.length === 0" class="px-6 py-8 text-center text-zinc-400 text-sm">
                暂无评论，来发表第一条评论吧
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <template v-else>
        <div class="flex-1 flex items-center justify-center text-zinc-400">
          <div class="text-center">
            <el-icon :size="48" class="mb-4"><Document /></el-icon>
            <p>选择一篇文章开始阅读</p>
          </div>
        </div>
      </template>
    </div>

    <!-- 添加类别对话框 -->
    <el-dialog v-model="showAddCategory" title="添加技术类别" width="400px">
      <el-form :model="categoryForm" label-position="top">
        <el-form-item label="类别名称" required>
          <el-input v-model="categoryForm.name" placeholder="如：算法优化、系统架构" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="简单描述这个类别" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCategory = false">取消</el-button>
        <el-button type="primary" @click="createCategory" :loading="savingCategory">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useWikiStore } from '@/stores/wiki';
import { useAuthStore } from '@/stores/auth';
import { wikiApi } from '@/api/wiki';
import { uploadApi } from '@/api/upload';
import { Folder, Plus, Edit, View, Star, Document, Delete } from '@element-plus/icons-vue';
import { MdEditor, MdPreview } from 'md-editor-v3';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs';
import type { WikiDirection, WikiPage, WikiComment } from '@/types';
import 'md-editor-v3/lib/style.css';

const wikiStore = useWikiStore();
const authStore = useAuthStore();

// 类别
const categories = computed(() => wikiStore.directions);
const selectedCategoryId = ref<number | null>(null);
const selectedCategory = computed(() => categories.value.find(c => c.id === selectedCategoryId.value) || null);
const showAddCategory = ref(false);
const savingCategory = ref(false);
const categoryForm = ref({ name: '', description: '' });

// 文章
const selectedArticleId = ref<number | null>(null);
const selectedArticle = ref<WikiPage | null>(null);
const currentArticles = computed(() => selectedCategory.value?.pages || []);

// 写文章
const isWriting = ref(false);
const editingArticle = ref<WikiPage | null>(null);
const saving = ref(false);
const articleForm = ref({ title: '', content: '' });

// 点赞
const liking = ref(false);
const likeCount = ref(0);

// 评论
const comments = ref<WikiComment[]>([]);
const newComment = ref('');
const replyingTo = ref<number | null>(null);
const replyContent = ref('');
const submittingComment = ref(false);

// Markdown 工具栏
const toolbars = [
  'bold', 'underline', 'italic', '-',
  'title', 'strikeThrough', 'sub', 'sup', 'quote', '-',
  'unorderedList', 'orderedList', 'task', '-',
  'codeRow', 'code', 'link', 'image', 'table', '-',
  'revoke', 'next', '=',
  'preview', 'fullscreen'
];

// 格式化
function formatCount(n: number): string {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return String(n);
}

function formatDate(d?: string) {
  return d ? dayjs(d).format('MM-DD HH:mm') : '';
}

function formatDateTime(d?: string) {
  return d ? dayjs(d).format('YYYY-MM-DD HH:mm') : '';
}

function getInitials(name?: string) {
  return name ? name.slice(0, 2) : '?';
}

function canDelete(comment: WikiComment) {
  return comment.createdBy?.id === authStore.user?.id || authStore.isAdmin;
}

// 文章编辑/删除权限：Admin 或创建者本人
const canEditArticle = computed(() => {
  if (!selectedArticle.value) return false;
  if (authStore.isAdmin) return true;
  // 检查创建者（第一个 revision 的作者）
  const article = selectedArticle.value as any;
  const creatorId = article.createdById ?? article.created_by_id ?? article.currentRevision?.createdBy?.id;
  return creatorId && creatorId === authStore.user?.id;
});

// 类别操作
function selectCategory(cat: WikiDirection) {
  selectedCategoryId.value = cat.id;
  selectedArticleId.value = null;
  selectedArticle.value = null;
  isWriting.value = false;
  wikiStore.fetchDirection(cat.id);
}

async function createCategory() {
  if (!categoryForm.value.name.trim()) {
    ElMessage.warning('请输入类别名称');
    return;
  }
  savingCategory.value = true;
  try {
    await wikiStore.createDirection({
      name: categoryForm.value.name,
      description: categoryForm.value.description
    });
    showAddCategory.value = false;
    categoryForm.value = { name: '', description: '' };
    ElMessage.success('类别创建成功');
  } catch {
    ElMessage.error('创建失败');
  } finally {
    savingCategory.value = false;
  }
}

async function deleteCategory(cat: WikiDirection) {
  const articleCount = cat.pages?.length || 0;
  const msg = articleCount > 0 
    ? `确定删除类别「${cat.name}」吗？该类别下有 ${articleCount} 篇文章，将一并删除。`
    : `确定删除类别「${cat.name}」吗？`;
  
  try {
    await ElMessageBox.confirm(msg, '删除类别', { type: 'warning' });
    await wikiApi.deleteDirection(cat.id);
    
    // 如果删除的是当前选中的类别，清空选择
    if (selectedCategoryId.value === cat.id) {
      selectedCategoryId.value = null;
      selectedArticle.value = null;
      selectedArticleId.value = null;
    }
    
    await wikiStore.fetchDirections();
    ElMessage.success('类别已删除');
  } catch {}
}

// 文章操作
async function selectArticle(article: WikiPage) {
  selectedArticleId.value = article.id;
  isWriting.value = false;
  try {
    selectedArticle.value = await wikiApi.getPage(article.id);
    likeCount.value = selectedArticle.value.likeCount || 0;
    await loadComments();
  } catch {
    ElMessage.error('加载文章失败');
  }
}

function startWriteArticle() {
  isWriting.value = true;
  editingArticle.value = null;
  articleForm.value = { title: '', content: '' };
}

function editArticle() {
  if (!selectedArticle.value) return;
  isWriting.value = true;
  editingArticle.value = selectedArticle.value;
  articleForm.value = {
    title: selectedArticle.value.title,
    content: selectedArticle.value.currentRevision?.content || ''
  };
}

function cancelWrite() {
  isWriting.value = false;
  editingArticle.value = null;
  articleForm.value = { title: '', content: '' };
}

async function saveArticle() {
  if (!articleForm.value.title.trim()) {
    ElMessage.warning('请输入文章标题');
    return;
  }
  if (!selectedCategoryId.value) {
    ElMessage.warning('请先选择类别');
    return;
  }

  saving.value = true;
  try {
    if (editingArticle.value) {
      // 更新文章
      await wikiApi.updatePage(editingArticle.value.id, { title: articleForm.value.title });
      await wikiApi.createRevision({ pageId: editingArticle.value.id, content: articleForm.value.content });
      ElMessage.success('文章已更新');
      await selectArticle(editingArticle.value);
    } else {
      // 新建文章
      const page = await wikiApi.createPage({
        directionId: selectedCategoryId.value,
        title: articleForm.value.title,
        content: articleForm.value.content
      });
      ElMessage.success('文章已发布');
      await wikiStore.fetchDirection(selectedCategoryId.value);
      await selectArticle(page);
    }
    isWriting.value = false;
    editingArticle.value = null;
  } catch {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

async function deleteArticle() {
  if (!selectedArticle.value) return;
  try {
    await ElMessageBox.confirm('确定删除这篇文章吗？', '删除文章', { type: 'warning' });
    await wikiApi.deletePage(selectedArticle.value.id);
    selectedArticle.value = null;
    selectedArticleId.value = null;
    if (selectedCategoryId.value) {
      await wikiStore.fetchDirection(selectedCategoryId.value);
    }
    ElMessage.success('文章已删除');
  } catch {}
}

// 图片上传
async function handleUploadImg(files: File[], callback: (urls: string[]) => void) {
  const urls: string[] = [];
  for (const file of files) {
    try {
      const result = await uploadApi.uploadImage(file, 'wiki');
      urls.push(result.url);
    } catch {
      ElMessage.error(`上传失败: ${file.name}`);
    }
  }
  callback(urls);
}

// 点赞
async function toggleLike() {
  if (!selectedArticle.value) return;
  liking.value = true;
  try {
    const result = await wikiApi.toggleLike(selectedArticle.value.id);
    likeCount.value = result.like_count;
    (selectedArticle.value as any).userLiked = result.liked;
  } catch {
    ElMessage.error('操作失败');
  } finally {
    liking.value = false;
  }
}

// 评论
async function loadComments() {
  if (!selectedArticle.value) return;
  try {
    comments.value = await wikiApi.listComments(selectedArticle.value.id);
  } catch {}
}

async function submitComment() {
  if (!selectedArticle.value || !newComment.value.trim()) return;
  submittingComment.value = true;
  try {
    await wikiApi.createComment(selectedArticle.value.id, newComment.value.trim());
    newComment.value = '';
    await loadComments();
    ElMessage.success('评论已发表');
  } catch {
    ElMessage.error('发表失败');
  } finally {
    submittingComment.value = false;
  }
}

function startReply(commentId: number) {
  replyingTo.value = replyingTo.value === commentId ? null : commentId;
  replyContent.value = '';
}

async function submitReply(parentId: number) {
  if (!selectedArticle.value || !replyContent.value.trim()) return;
  submittingComment.value = true;
  try {
    await wikiApi.createComment(selectedArticle.value.id, replyContent.value.trim(), parentId);
    replyContent.value = '';
    replyingTo.value = null;
    await loadComments();
    ElMessage.success('回复已发表');
  } catch {
    ElMessage.error('回复失败');
  } finally {
    submittingComment.value = false;
  }
}

async function deleteComment(commentId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除', { type: 'warning' });
    await wikiApi.deleteComment(commentId);
    await loadComments();
    ElMessage.success('已删除');
  } catch {}
}

// 初始化
onMounted(async () => {
  await wikiStore.fetchDirections();
  if (categories.value.length > 0) {
    selectCategory(categories.value[0]);
  }
});
</script>

<style scoped>
.article-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
}

.article-content :deep(pre) {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.article-content :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.article-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.article-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.article-content :deep(th),
.article-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
}

.article-content :deep(th) {
  background: #f9fafb;
}

.article-content :deep(blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 16px;
  margin: 16px 0;
  color: #6b7280;
}
</style>
