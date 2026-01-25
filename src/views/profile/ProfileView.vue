<template>
  <div v-loading="loading" class="space-y-6">
    <!-- 返回按钮 -->
    <div class="flex items-center gap-4">
      <el-button text @click="router.back()">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>返回
      </el-button>
    </div>

    <div v-if="profile" class="space-y-6">
      <!-- 个人信息卡片 -->
      <div class="bg-white rounded-xl border border-zinc-200 p-6">
        <div class="flex items-start gap-6">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
            {{ getInitials(profile.userName) }}
          </div>
          <div class="flex-1">
            <h1 class="text-2xl font-bold text-zinc-900 mb-1">{{ profile.userName }}</h1>
            <div class="flex items-center gap-4 text-sm text-zinc-500">
              <span v-if="profile.userEmail">{{ profile.userEmail }}</span>
              <el-tag v-if="profile.slotType" :type="profile.slotType === 'ALGO' ? 'primary' : 'warning'" size="small">
                {{ profile.slotType === 'ALGO' ? '自有人力' : '协调人力' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 统计卡片 - 可点击 -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          class="bg-white rounded-xl border border-zinc-200 p-4 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all"
          :class="activeDetail === 'dri' ? 'ring-2 ring-blue-500' : ''"
          @click="showDetail('dri')"
        >
          <p class="text-sm text-zinc-500 mb-1">作为 DRI</p>
          <p class="text-3xl font-bold text-blue-600">{{ profile.driTopicCount }}</p>
          <p class="text-xs text-zinc-400">个课题 <span class="text-blue-500">›</span></p>
        </div>
        <div 
          class="bg-white rounded-xl border border-zinc-200 p-4 cursor-pointer hover:border-purple-300 hover:shadow-md transition-all"
          :class="activeDetail === 'participant' ? 'ring-2 ring-purple-500' : ''"
          @click="showDetail('participant')"
        >
          <p class="text-sm text-zinc-500 mb-1">作为参与者</p>
          <p class="text-3xl font-bold text-purple-600">{{ profile.participantTopicCount }}</p>
          <p class="text-xs text-zinc-400">个课题 <span class="text-purple-500">›</span></p>
        </div>
        <div 
          class="bg-white rounded-xl border border-zinc-200 p-4 cursor-pointer hover:border-amber-300 hover:shadow-md transition-all"
          :class="activeDetail === 'techpoints' ? 'ring-2 ring-amber-500' : ''"
          @click="showDetail('techpoints')"
        >
          <p class="text-sm text-zinc-500 mb-1">技术点（第一作者）</p>
          <p class="text-3xl font-bold text-amber-600">{{ profile.firstAuthorTechPoints }}</p>
          <p class="text-xs text-zinc-400">个 <span class="text-amber-500">›</span></p>
        </div>
        <div 
          class="bg-white rounded-xl border border-zinc-200 p-4 cursor-pointer hover:border-emerald-300 hover:shadow-md transition-all"
          :class="activeDetail === 'deliverables' ? 'ring-2 ring-emerald-500' : ''"
          @click="showDetail('deliverables')"
        >
          <p class="text-sm text-zinc-500 mb-1">交付物</p>
          <p class="text-3xl font-bold text-emerald-600">{{ profile.deliverableCount }}</p>
          <p class="text-xs text-zinc-400">个 <span class="text-emerald-500">›</span></p>
        </div>
      </div>

      <!-- 详情展开区域 -->
      <transition name="slide">
        <div v-if="activeDetail" class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <!-- DRI 课题列表 -->
          <div v-if="activeDetail === 'dri'" class="p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-zinc-800">作为 DRI 的课题</h3>
              <el-button text @click="activeDetail = null">收起</el-button>
            </div>
            <div v-if="driTopics.length" class="space-y-2">
              <router-link
                v-for="t in driTopics"
                :key="t.id"
                :to="`/topics/${t.id}`"
                class="block p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-zinc-800">{{ t.title }}</span>
                    <el-tag :type="t.urgency === 'P0' ? 'danger' : t.urgency === 'P1' ? 'warning' : 'info'" size="small">{{ t.urgency }}</el-tag>
                  </div>
                  <el-tag :type="t.result === 'SUCCESS' ? 'success' : t.result === 'UNSOLVABLE' ? 'danger' : ''" size="small">
                    {{ t.result === 'SUCCESS' ? '已完成' : t.result === 'UNSOLVABLE' ? '无法解决' : '进行中' }}
                  </el-tag>
                </div>
              </router-link>
            </div>
            <div v-else class="text-center py-8 text-zinc-400">暂无课题</div>
          </div>

          <!-- 参与者课题列表 -->
          <div v-if="activeDetail === 'participant'" class="p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-zinc-800">作为参与者的课题</h3>
              <el-button text @click="activeDetail = null">收起</el-button>
            </div>
            <div v-if="participantTopics.length" class="space-y-2">
              <router-link
                v-for="t in participantTopics"
                :key="t.id"
                :to="`/topics/${t.id}`"
                class="block p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-zinc-800">{{ t.title }}</span>
                    <el-tag :type="t.urgency === 'P0' ? 'danger' : t.urgency === 'P1' ? 'warning' : 'info'" size="small">{{ t.urgency }}</el-tag>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-zinc-500">DRI: {{ t.driName || '未分配' }}</span>
                    <el-tag :type="t.result === 'SUCCESS' ? 'success' : t.result === 'UNSOLVABLE' ? 'danger' : ''" size="small">
                      {{ t.result === 'SUCCESS' ? '已完成' : t.result === 'UNSOLVABLE' ? '无法解决' : '进行中' }}
                    </el-tag>
                  </div>
                </div>
              </router-link>
            </div>
            <div v-else class="text-center py-8 text-zinc-400">暂无课题</div>
          </div>

          <!-- 技术点列表 -->
          <div v-if="activeDetail === 'techpoints'" class="p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-zinc-800">技术点（第一作者）</h3>
              <el-button text @click="activeDetail = null">收起</el-button>
            </div>
            <div v-if="techPoints.length" class="space-y-2">
              <div
                v-for="tp in techPoints"
                :key="tp.id"
                class="p-3 bg-zinc-50 rounded-lg"
              >
                <div class="flex items-center justify-between mb-1">
                  <span class="font-medium text-zinc-800">{{ tp.name }}</span>
                  <el-tag :type="tp.status === 'completed' ? 'success' : tp.status === 'in_progress' ? 'warning' : 'info'" size="small">
                    {{ tp.status === 'completed' ? '已完成' : tp.status === 'in_progress' ? '进行中' : '草稿' }}
                  </el-tag>
                </div>
                <div class="text-sm text-zinc-500">
                  <router-link v-if="tp.topicId" :to="`/topics/${tp.topicId}`" class="hover:text-blue-600">{{ tp.topicTitle }}</router-link>
                  <span v-if="tp.stageName" class="mx-1">›</span>
                  <span v-if="tp.stageName">{{ tp.stageName }}</span>
                </div>
                <p v-if="tp.hypothesis" class="text-xs text-amber-600 mt-1">假设: {{ tp.hypothesis }}</p>
              </div>
            </div>
            <div v-else class="text-center py-8 text-zinc-400">暂无技术点</div>
          </div>

          <!-- 交付物列表 -->
          <div v-if="activeDetail === 'deliverables'" class="p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-zinc-800">交付物</h3>
              <el-button text @click="activeDetail = null">收起</el-button>
            </div>
            <div v-if="deliverables.length" class="space-y-2">
              <div
                v-for="d in deliverables"
                :key="d.id"
                class="flex items-start gap-3 p-3 bg-zinc-50 rounded-lg"
              >
                <div :class="['w-8 h-8 rounded flex items-center justify-center flex-shrink-0', getCategoryStyle(d.category)]">
                  <el-icon :size="16"><component :is="getCategoryIcon(d.category)" /></el-icon>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <a :href="d.url || '#'" target="_blank" class="font-medium text-zinc-800 hover:text-blue-600">{{ d.name }}</a>
                    <el-tag v-if="d.isFirstAuthor" size="small" type="warning">第一作者</el-tag>
                  </div>
                  <div class="text-sm text-zinc-500">
                    <router-link :to="`/topics/${d.topicId}`" class="hover:text-blue-600">{{ d.topicTitle }}</router-link>
                    <span v-if="d.stageName" class="mx-1">›</span>
                    <span v-if="d.stageName">{{ d.stageName }}</span>
                  </div>
                  <p class="text-xs text-zinc-400">{{ formatDateTime(d.createdAt) }}</p>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-zinc-400">暂无交付物</div>
          </div>
        </div>
      </transition>

      <!-- 课题状态分布 + 效率 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-white rounded-xl border border-zinc-200 p-4">
          <h3 class="font-semibold text-zinc-800 mb-4">课题状态分布</h3>
          <div class="space-y-3">
            <div class="flex items-center gap-4 cursor-pointer hover:bg-zinc-50 p-2 -mx-2 rounded" @click="showTopicsByStatus('open')">
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm text-zinc-600">进行中</span>
                  <span class="font-medium text-blue-600">{{ profile.inProgressTopicCount }}</span>
                </div>
                <el-progress :percentage="getPercentage(profile.inProgressTopicCount)" :show-text="false" />
              </div>
            </div>
            <div class="flex items-center gap-4 cursor-pointer hover:bg-zinc-50 p-2 -mx-2 rounded" @click="showTopicsByStatus('success')">
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm text-zinc-600">已完成</span>
                  <span class="font-medium text-emerald-600">{{ profile.completedTopicCount }}</span>
                </div>
                <el-progress :percentage="getPercentage(profile.completedTopicCount)" :show-text="false" status="success" />
              </div>
            </div>
            <div class="flex items-center gap-4 cursor-pointer hover:bg-zinc-50 p-2 -mx-2 rounded" @click="showTopicsByStatus('unsolvable')">
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm text-zinc-600">无法解决</span>
                  <span class="font-medium text-rose-600">{{ profile.unsolvableTopicCount }}</span>
                </div>
                <el-progress :percentage="getPercentage(profile.unsolvableTopicCount)" :show-text="false" status="exception" />
              </div>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-xl border border-zinc-200 p-4">
          <h3 class="font-semibold text-zinc-800 mb-4">效率指标</h3>
          <div class="flex items-center gap-8">
            <div>
              <p class="text-sm text-zinc-500">平均闭环周期</p>
              <p class="text-2xl font-bold text-zinc-800">
                {{ profile.avgClosureDays !== null ? `${profile.avgClosureDays} 天` : '—' }}
              </p>
            </div>
            <div>
              <p class="text-sm text-zinc-500">完成率</p>
              <p class="text-2xl font-bold text-emerald-600">
                {{ completionRate }}%
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史时间线 -->
      <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <div class="p-4 border-b border-zinc-100">
          <h3 class="font-semibold text-zinc-800">📅 历史时间线</h3>
        </div>
        <div class="p-4">
          <div v-if="timeline.length" class="relative">
            <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-zinc-200"></div>
            <div class="space-y-4">
              <div v-for="event in timeline" :key="event.id" class="relative pl-10">
                <div :class="['absolute left-2 w-5 h-5 rounded-full border-2 border-white', getEventColor(event.action)]"></div>
                <div class="p-3 bg-zinc-50 rounded-lg">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-medium text-zinc-800">{{ event.actionLabel }}</span>
                    <span v-if="event.entityName" class="text-zinc-600">「{{ event.entityName }}」</span>
                  </div>
                  <div v-if="event.topicTitle" class="text-sm text-zinc-500">
                    课题: <router-link :to="`/topics/${event.topicId}`" class="hover:text-blue-600">{{ event.topicTitle }}</router-link>
                  </div>
                  <p class="text-xs text-zinc-400 mt-1">{{ formatDateTime(event.createdAt) }}</p>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-zinc-400">
            <el-icon :size="48" class="mb-4"><Clock /></el-icon>
            <p>暂无活动记录</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 按状态筛选的课题弹窗 -->
    <el-dialog v-model="showStatusTopics" :title="statusTopicsTitle" width="600px">
      <div v-if="statusTopics.length" class="space-y-2 max-h-96 overflow-y-auto">
        <router-link
          v-for="t in statusTopics"
          :key="t.id"
          :to="`/topics/${t.id}`"
          class="block p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors"
          @click="showStatusTopics = false"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="font-medium text-zinc-800">{{ t.title }}</span>
              <el-tag v-if="t.isDri" size="small" type="primary">DRI</el-tag>
            </div>
            <el-tag :type="t.urgency === 'P0' ? 'danger' : t.urgency === 'P1' ? 'warning' : 'info'" size="small">{{ t.urgency }}</el-tag>
          </div>
        </router-link>
      </div>
      <div v-else class="text-center py-8 text-zinc-400">暂无课题</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Folder, Document, VideoPlay, Link, DataLine, Clock } from '@element-plus/icons-vue';
import { profileApi, type ProfileStats, type TopicItem, type TechPointItem, type DeliverableItem, type TimelineEvent } from '@/api/profile';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const profile = ref<ProfileStats | null>(null);
const activeDetail = ref<string | null>(null);

// 详情数据
const driTopics = ref<TopicItem[]>([]);
const participantTopics = ref<TopicItem[]>([]);
const techPoints = ref<TechPointItem[]>([]);
const deliverables = ref<DeliverableItem[]>([]);
const timeline = ref<TimelineEvent[]>([]);

// 状态筛选弹窗
const showStatusTopics = ref(false);
const statusTopicsTitle = ref('');
const statusTopics = ref<TopicItem[]>([]);

const userId = computed(() => {
  const id = route.params.userId || route.query.userId;
  return id ? Number(id) : null;
});

const slotId = computed(() => {
  const id = route.params.slotId || route.query.slotId;
  return id ? Number(id) : null;
});

const completionRate = computed(() => {
  if (!profile.value) return 0;
  const total = profile.value.driTopicCount + profile.value.participantTopicCount;
  if (total === 0) return 0;
  return Math.round((profile.value.completedTopicCount / total) * 100);
});

function getInitials(name?: string) {
  return name ? name.slice(0, 2).toUpperCase() : '??';
}

function formatDateTime(date?: string) {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '';
}

function getPercentage(count: number) {
  if (!profile.value) return 0;
  const total = profile.value.driTopicCount + profile.value.participantTopicCount;
  if (total === 0) return 0;
  return Math.round((count / total) * 100);
}

function getCategoryStyle(category?: string) {
  const styles: Record<string, string> = {
    document: 'bg-blue-100 text-blue-600',
    video: 'bg-purple-100 text-purple-600',
    data: 'bg-green-100 text-green-600',
    code: 'bg-amber-100 text-amber-600',
    link: 'bg-zinc-100 text-zinc-600',
  };
  return styles[category || 'link'] || styles.link;
}

function getCategoryIcon(category?: string) {
  const icons: Record<string, any> = { document: Document, video: VideoPlay, data: DataLine, code: Folder, link: Link };
  return icons[category || 'link'] || Link;
}

function getEventColor(action: string) {
  if (action.includes('create')) return 'bg-emerald-500';
  if (action.includes('complete') || action.includes('close')) return 'bg-blue-500';
  if (action.includes('delete')) return 'bg-rose-500';
  return 'bg-zinc-400';
}

async function loadProfile() {
  loading.value = true;
  try {
    if (userId.value) {
      profile.value = await profileApi.getUserProfile(userId.value);
    } else if (slotId.value) {
      profile.value = await profileApi.getSlotProfile(slotId.value);
    }
  } catch (error) {
    console.error('Failed to load profile:', error);
  } finally {
    loading.value = false;
  }
}

async function showDetail(type: string) {
  if (activeDetail.value === type) {
    activeDetail.value = null;
    return;
  }
  activeDetail.value = type;
  if (!userId.value) return;

  try {
    if (type === 'dri') {
      const result = await profileApi.getUserTopics(userId.value, { role: 'dri' });
      driTopics.value = result.items;
    } else if (type === 'participant') {
      const result = await profileApi.getUserTopics(userId.value, { role: 'participant' });
      participantTopics.value = result.items;
    } else if (type === 'techpoints') {
      const result = await profileApi.getUserTechPoints(userId.value);
      techPoints.value = result.items;
    } else if (type === 'deliverables') {
      const result = await profileApi.getUserDeliverables(userId.value);
      deliverables.value = result.items;
    }
  } catch (error) {
    console.error('Failed to load detail:', error);
  }
}

async function showTopicsByStatus(status: string) {
  if (!userId.value) return;
  const titles: Record<string, string> = {
    open: '进行中的课题',
    success: '已完成的课题',
    unsolvable: '无法解决的课题',
  };
  statusTopicsTitle.value = titles[status] || '课题';
  showStatusTopics.value = true;
  
  try {
    const result = await profileApi.getUserTopics(userId.value, { status });
    statusTopics.value = result.items;
  } catch (error) {
    console.error('Failed to load topics:', error);
  }
}

async function loadTimeline() {
  if (!userId.value) return;
  try {
    const result = await profileApi.getUserTimeline(userId.value);
    timeline.value = result.items;
  } catch (error) {
    console.error('Failed to load timeline:', error);
  }
}

onMounted(async () => {
  await loadProfile();
  if (userId.value) {
    await loadTimeline();
  }
});

watch([userId, slotId], async () => {
  activeDetail.value = null;
  await loadProfile();
  if (userId.value) {
    await loadTimeline();
  }
});
</script>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
