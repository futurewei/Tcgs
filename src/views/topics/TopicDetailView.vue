<template>
  <div v-loading="loading" class="space-y-6">
    <!-- Back + Header -->
    <div class="flex items-center gap-4">
      <el-button text @click="router.back()">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div v-if="topic" class="grid grid-cols-12 gap-6">
      <!-- Left: Content (8 columns) -->
      <div class="col-span-8 space-y-6">
        <!-- Header -->
        <div class="bg-white rounded-xl border border-zinc-200 p-6">
          <div class="flex items-start justify-between mb-4">
            <div>
              <div class="flex items-center gap-3 mb-2">
                <h1 class="text-2xl font-bold text-zinc-900">{{ topic.title }}</h1>
                <el-tag :type="urgencyType" size="small">{{ topic.urgency }}</el-tag>
                <el-tag type="info" size="small">{{ typeLabel }}</el-tag>
              </div>
              <p class="text-zinc-500">编号: {{ topic.id }}</p>
            </div>
            <el-tag :type="resultType" size="large">{{ resultLabel }}</el-tag>
          </div>

          <!-- Stage Timeline with Progress -->
          <div class="mt-6">
            <div class="flex items-center justify-between mb-3">
              <p class="text-sm font-medium text-zinc-500">阶段进度</p>
              <span class="text-xs text-zinc-400">
                {{ completedStagesCount }} / {{ totalStagesCount }} 个阶段已完成
              </span>
            </div>
            <StageTimeline
              :stages="topic.template?.stages || []"
              :stage-states="stageStates"
              :current-stage-id="currentStageId"
              @stage-click="selectStage"
            />
          </div>
        </div>

        <!-- Basic Info Card -->
        <div class="bg-white rounded-xl border border-zinc-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-semibold text-zinc-900">基本信息</h2>
            <el-button v-if="canEdit" size="small" @click="showEditInfo = true">编辑</el-button>
          </div>
          <div class="prose prose-sm max-w-none">
            <p>{{ topic.description }}</p>
          </div>

          <!-- Requester Information -->
          <div class="mt-4 pt-4 border-t border-zinc-200">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-zinc-700">需求方:</span>
              <span class="text-sm text-zinc-900">{{ requesterName }}</span>
              <el-tag v-if="requesterUserId" type="info" size="small">已注册用户</el-tag>
              <el-tag v-else type="warning" size="small">外部需求方</el-tag>
            </div>
          </div>
        </div>

        <!-- Stage Content Area -->
        <div v-if="selectedStage" class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div>
              <div class="flex items-center gap-2">
                <h2 class="font-semibold text-zinc-900">{{ selectedStage.name }}</h2>
                <el-tag :type="getStageStatusType(selectedStage)" size="small">
                  {{ getStageStatusLabel(selectedStage) }}
                </el-tag>
              </div>
              <p class="text-sm text-zinc-500">{{ selectedStage.description }}</p>
            </div>
            <div class="flex items-center gap-2">
              <el-tag v-if="selectedStage.isTerminal" type="warning" size="small">终止阶段</el-tag>
              <el-tag v-if="selectedStage.requireArtifact" type="info" size="small">需要交付物</el-tag>
            </div>
          </div>

          <div class="p-6 space-y-6">
            <!-- Deliverables Section -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                  <el-icon class="text-zinc-600"><Folder /></el-icon>
                  <h3 class="font-medium text-zinc-800">交付物</h3>
                  <span class="text-xs text-zinc-400">({{ stageDeliverables.length }})</span>
                </div>
                <el-button v-if="canEdit && !authStore.isCustomer" size="small" type="primary" plain @click="showAddDeliverable = true">
                  <el-icon class="mr-1"><Plus /></el-icon>添加
                </el-button>
              </div>

              <div class="space-y-2">
                <div
                  v-for="deliverable in stageDeliverables"
                  :key="deliverable.id"
                  class="flex items-center justify-between p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors group"
                >
                  <div class="flex items-center gap-3 flex-1 min-w-0">
                    <div :class="['w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', getDeliverableIconStyle(deliverable)]">
                      <el-icon :size="20"><component :is="getDeliverableIcon(deliverable)" /></el-icon>
                    </div>
                    <div class="min-w-0 flex-1">
                      <a :href="deliverable.url" target="_blank" class="font-medium text-zinc-900 hover:text-blue-600 truncate block">{{ deliverable.name }}</a>
                      <p v-if="deliverable.description" class="text-xs text-zinc-500 truncate">{{ deliverable.description }}</p>
                      <div class="flex items-center gap-2 text-xs text-zinc-400">
                        <span>{{ deliverable.createdBy?.name }}</span>
                        <span>•</span>
                        <span>{{ formatDate(deliverable.createdAt) }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <el-button size="small" text type="primary" @click="openDeliverable(deliverable)"><el-icon><View /></el-icon></el-button>
                    <el-button v-if="canDeleteDeliverable(deliverable)" size="small" text type="danger" @click="deleteDeliverable(deliverable)"><el-icon><Delete /></el-icon></el-button>
                  </div>
                </div>
                <div v-if="stageDeliverables.length === 0" class="text-center py-8 text-zinc-400">
                  <el-icon class="text-3xl mb-2"><FolderOpened /></el-icon>
                  <p class="text-sm font-medium">暂无交付物</p>
                </div>
              </div>
            </div>

            <!-- Artifacts Section -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-medium text-zinc-800">笔记与备注</h3>
                <el-button v-if="!authStore.isCustomer" size="small" @click="showAddArtifact = true">添加笔记</el-button>
              </div>
              <div class="space-y-3">
                <div v-for="artifact in stageArtifacts" :key="artifact.id" class="p-4 bg-zinc-50 rounded-lg">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium">{{ artifact.title }}</h4>
                    <span class="text-xs text-zinc-400">{{ artifact.createdBy?.name }} • {{ formatDate(artifact.createdAt) }}</span>
                  </div>
                  <div class="prose prose-sm max-w-none" v-html="renderMarkdown(artifact.content)"></div>
                </div>
                <p v-if="stageArtifacts.length === 0" class="text-sm text-zinc-400 text-center py-4">暂无笔记</p>
              </div>
            </div>

            <!-- Reviews Section -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-medium text-zinc-800">评审记录</h3>
                <el-button v-if="!authStore.isCustomer" size="small" @click="showAddReview = true">添加评审</el-button>
              </div>
              <div class="space-y-3">
                <div v-for="review in stageReviews" :key="review.id" class="p-4 bg-zinc-50 rounded-lg">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs">{{ getInitials(review.createdBy?.name) }}</div>
                    <span class="font-medium text-sm">{{ review.createdBy?.name }}</span>
                    <span class="text-xs text-zinc-400">{{ formatDate(review.createdAt) }}</span>
                  </div>
                  <div class="prose prose-sm max-w-none" v-html="renderMarkdown(review.content)"></div>
                </div>
                <p v-if="stageReviews.length === 0" class="text-sm text-zinc-400 text-center py-4">暂无评审</p>
              </div>
            </div>

            <!-- Closure Section -->
            <div v-if="selectedStage.isTerminal && selectedStage.allowResult">
              <h3 class="font-medium text-zinc-800 mb-4">结果</h3>
              <div class="flex items-center gap-4">
                <el-button v-if="topic.result === 'OPEN' && canEdit && !authStore.isCustomer" type="success" @click="closeTopic('SUCCESS')">标记为成功</el-button>
                <el-button v-if="topic.result === 'OPEN' && canEdit && !authStore.isCustomer" type="danger" @click="closeTopic('UNSOLVABLE')">标记为无法解决</el-button>
                <el-tag v-if="topic.result !== 'OPEN'" :type="resultType" size="large">{{ resultLabel }}</el-tag>
              </div>
            </div>

            <!-- Stage Navigation Buttons -->
            <div v-if="canEdit && !authStore.isCustomer && topic.result === 'OPEN'" class="pt-4 border-t border-zinc-200 flex items-center gap-3">
              <el-button v-if="canBackwardStage" type="warning" plain @click="showBackwardDialog = true">
                <el-icon class="mr-1"><Back /></el-icon>回退阶段
              </el-button>
              <el-button v-if="canAdvanceStage" type="primary" @click="advanceToNextStage">
                推进到下一阶段<el-icon class="ml-1"><Right /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Sticky Sidebar (4 columns) -->
      <div class="col-span-4">
        <div class="sticky top-20 space-y-4">
          <!-- DRI Card -->
          <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
            <div class="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-blue-100 uppercase tracking-wide">DRI (负责人)</span>
                <el-button v-if="authStore.isAdmin" size="small" text class="!text-white hover:!bg-white/20" @click="showChangeDRI = true">更换</el-button>
              </div>
            </div>
            <div class="p-4">
              <div v-if="driBinding" class="flex items-start gap-4">
                <div class="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center font-bold text-blue-600 text-xl flex-shrink-0">{{ getInitials(driSlotName) }}</div>
                <div class="flex-1 min-w-0">
                  <p class="font-semibold text-zinc-900 text-lg truncate">{{ driSlotName }}</p>
                  <p v-if="driUserEmail" class="text-sm text-zinc-500 truncate mb-2">{{ driUserEmail }}</p>
                  <div class="flex flex-wrap items-center gap-2">
                    <el-tag size="small" :type="driSlotType === 'EXTERNAL' ? 'info' : 'success'">{{ slotTypeLabel(driSlotType) }}</el-tag>
                    <span class="text-xs text-zinc-400">{{ driBinding.percentage }}% 已分配</span>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-4 text-zinc-400">
                <p class="text-sm">暂无负责人</p>
                <p class="text-xs mt-1">请先分配人力以指定负责人</p>
              </div>

              <!-- DRI Usage Info -->
              <div v-if="driBinding && driTotalUsage !== null" class="mt-4 pt-4 border-t border-zinc-100">
                <div class="flex items-center justify-between text-sm mb-2">
                  <span class="text-zinc-500">总分配量</span>
                  <span :class="['font-semibold', driTotalUsage >= 100 ? 'text-rose-600' : driTotalUsage >= 80 ? 'text-amber-600' : 'text-emerald-600']">{{ driTotalUsage }}%</span>
                </div>
                <el-progress :percentage="Math.min(driTotalUsage, 100)" :stroke-width="6" :color="driTotalUsage >= 100 ? '#e11d48' : driTotalUsage >= 80 ? '#f59e0b' : '#10b981'" :show-text="false" />
              </div>
            </div>
          </div>

          <!-- Team Bindings Card -->
          <div class="bg-white rounded-xl border border-zinc-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-zinc-900">团队成员</h3>
              <el-button v-if="authStore.isAdmin" size="small" text @click="showAddBinding = true">添加</el-button>
            </div>
            <div class="space-y-2">
              <div v-for="binding in teamBindings" :key="binding.id" class="flex items-center justify-between">
                <SlotChip :slot="binding.slot" :binding-percentage="binding.percentage" show-percentage />
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium">{{ binding.percentage }}%</span>
                  <el-tag v-if="binding.isForced" type="warning" size="small">强制</el-tag>
                </div>
              </div>
              <p v-if="!teamBindings.length" class="text-sm text-zinc-400">暂无其他团队成员</p>
            </div>
          </div>

          <!-- Stage History -->
          <div class="bg-white rounded-xl border border-zinc-200 p-4">
            <h3 class="font-semibold text-zinc-900 mb-3">阶段历史</h3>
            <div class="space-y-2 max-h-[300px] overflow-y-auto">
              <div v-for="log in stageHistoryLogs" :key="log.id" class="p-2 bg-zinc-50 rounded text-xs">
                <div class="flex items-center gap-2">
                  <el-icon v-if="log.action === 'backward'" class="text-amber-500"><Back /></el-icon>
                  <el-icon v-else class="text-emerald-500"><Right /></el-icon>
                  <span class="font-medium text-zinc-700">{{ log.stageName }}</span>
                </div>
                <p class="text-zinc-500 mt-1">{{ log.userName }} • {{ formatDate(log.createdAt) }}</p>
              </div>
              <p v-if="stageHistoryLogs.length === 0" class="text-sm text-zinc-400">暂无阶段变更记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <AddArtifactDialog v-model="showAddArtifact" :topic-id="topicId" :stage-id="selectedStageId" @created="refreshTopic" />
    <AddReviewDialog v-model="showAddReview" :topic-id="topicId" :stage-id="selectedStageId" @created="refreshTopic" />
    <ChangeDRIDialog v-model="showChangeDRI" :topic="topic" :bindings="normalizedBindings" @changed="refreshTopic" />
    <AddBindingDialog v-model="showAddBinding" :topic-id="topicId" @created="afterBindingChanged" />
    <AddDeliverableDialog v-model="showAddDeliverable" :topic-id="topicId" :stage-id="selectedStageId" @created="refreshTopic" />
    
    <!-- Backward Stage Dialog -->
    <el-dialog v-model="showBackwardDialog" title="回退阶段" width="450px">
      <p class="text-zinc-600 mb-4">选择要回退到的阶段:</p>
      <el-select v-model="selectedBackwardStageId" placeholder="选择阶段" class="w-full">
        <el-option v-for="stage in previousStages" :key="stage.id" :label="stage.name" :value="stage.id" />
      </el-select>
      <template #footer>
        <el-button @click="showBackwardDialog = false">取消</el-button>
        <el-button type="warning" :disabled="!selectedBackwardStageId" @click="goBackToStage">确认回退</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, markRaw } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useAuthStore } from '@/stores/auth';
import { useCapacityStore } from '@/stores/capacity';
import { ArrowLeft, Link, Document, Folder, FolderOpened, Plus, View, Delete, Picture, VideoCamera, DocumentCopy, Memo, Connection, Back, Right } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import StageTimeline from '@/components/topic/StageTimeline.vue';
import SlotChip from '@/components/common/SlotChip.vue';
import AddArtifactDialog from '@/components/topic/AddArtifactDialog.vue';
import AddReviewDialog from '@/components/topic/AddReviewDialog.vue';
import ChangeDRIDialog from '@/components/topic/ChangeDRIDialog.vue';
import AddBindingDialog from '@/components/topic/AddBindingDialog.vue';
import AddDeliverableDialog from '@/components/topic/AddDeliverableDialog.vue';
import { topicsApi } from '@/api/topics';
import dayjs from 'dayjs';
import type { StageTemplateStage, TopicStageState, Artifact, ReviewComment, StageDeliverable, Binding } from '@/types';

const route = useRoute();
const router = useRouter();
const topicsStore = useTopicsStore();
const authStore = useAuthStore();
const capacityStore = useCapacityStore();

const topicId = computed(() => Number(route.params.id));
const topic = computed(() => topicsStore.currentTopic);
const loading = computed(() => topicsStore.loading);

const selectedStageId = ref<number | null>(null);
const showEditInfo = ref(false);
const showAddArtifact = ref(false);
const showAddReview = ref(false);
const showChangeDRI = ref(false);
const showAddBinding = ref(false);
const showAddDeliverable = ref(false);
const showBackwardDialog = ref(false);
const selectedBackwardStageId = ref<number | null>(null);
const stageHistoryLogs = ref<any[]>([]);

// Labels
const typeLabel = computed(() => topic.value?.type === 'UNCERTAINTY' ? '不确定性' : topic.value?.type === 'EVOLUTION' ? '演进' : topic.value?.type);
const resultLabel = computed(() => topic.value?.result === 'SUCCESS' ? '已完成' : topic.value?.result === 'UNSOLVABLE' ? '无法解决' : '进行中');
function slotTypeLabel(type: string): string { return type === 'EXTERNAL' ? '协调人力' : '自有人力'; }

// Normalize bindings
const normalizedBindings = computed<Binding[]>(() => {
  const t: any = topic.value;
  if (!t?.bindings) return [];
  return t.bindings.map((b: any) => ({
    ...b, slotId: b.slotId ?? b.slot_id, topicId: b.topicId ?? b.topic_id,
    isForced: b.isForced ?? b.is_forced ?? false, isDri: b.isDri ?? b.is_dri ?? false,
    slot: b.slot ? { ...b.slot, userId: b.slot.userId ?? b.slot.user_id, totalCapacity: b.slot.totalCapacity ?? b.slot.total_capacity } : null,
  }));
});

const driBinding = computed<Binding | null>(() => normalizedBindings.value.find(b => b.isDri) || normalizedBindings.value[0] || null);
const driSlotName = computed(() => driBinding.value?.slot?.name ?? '未知');
const driSlotType = computed(() => driBinding.value?.slot?.type ?? 'ALGO');
const driUserEmail = computed(() => driBinding.value?.slot?.user?.email ?? '');
const driTotalUsage = computed(() => {
  if (!driBinding.value?.slot) return null;
  const slot = capacityStore.slots.find(s => s.id === driBinding.value!.slotId);
  if (!slot?.bindings?.length) return driBinding.value.percentage;
  return slot.bindings.reduce((sum, b) => sum + (b.percentage || 0), 0);
});
const teamBindings = computed<Binding[]>(() => normalizedBindings.value.filter(b => !b.isDri));

const currentStageId = computed<number | undefined>(() => { const t: any = topic.value; return t?.currentStageId ?? t?.current_stage_id; });
const stageStates = computed<TopicStageState[]>(() => { const t: any = topic.value; return (t?.stageStates ?? t?.stage_states ?? []) as TopicStageState[]; });
const selectedStage = computed(() => selectedStageId.value && topic.value?.template?.stages ? topic.value.template.stages.find(s => s.id === selectedStageId.value) : null);
const stageArtifacts = computed<Artifact[]>(() => { if (!selectedStageId.value) return []; const t: any = topic.value; return ((t?.artifacts ?? []) as Artifact[]).filter((a: any) => (a.stageId ?? a.stage_id) === selectedStageId.value); });
const stageReviews = computed<ReviewComment[]>(() => { if (!selectedStageId.value) return []; const t: any = topic.value; return ((t?.reviews ?? []) as ReviewComment[]).filter((r: any) => (r.stageId ?? r.stage_id) === selectedStageId.value); });
const stageDeliverables = computed<StageDeliverable[]>(() => { if (!selectedStageId.value) return []; const t: any = topic.value; return ((t?.deliverables ?? []) as StageDeliverable[]).filter((d: any) => (d.stageId ?? d.stage_id) === selectedStageId.value); });

const totalStagesCount = computed(() => topic.value?.template?.stages?.length || 0);
const completedStagesCount = computed(() => stageStates.value.filter((ss: any) => ['done', 'completed', 'finished', 'closed'].includes(((ss as any)?.status || '').toLowerCase())).length);
const isDriUser = computed(() => driBinding.value?.slot?.userId && driBinding.value.slot.userId === authStore.user?.id);
const canEdit = computed(() => !authStore.isCustomer && (authStore.isAdmin || isDriUser.value));
const currentStageIndex = computed(() => { const cid = currentStageId.value; if (!cid || !topic.value?.template?.stages) return -1; return topic.value.template.stages.findIndex(s => s.id === cid); });
const canAdvanceStage = computed(() => topic.value?.template?.stages && currentStageIndex.value < topic.value.template.stages.length - 1 && topic.value.result === 'OPEN');
const canBackwardStage = computed(() => currentStageIndex.value > 0 && topic.value?.result === 'OPEN');
const previousStages = computed(() => !topic.value?.template?.stages || currentStageIndex.value <= 0 ? [] : topic.value.template.stages.slice(0, currentStageIndex.value));
const urgencyType = computed(() => topic.value?.urgency === 'P0' ? 'danger' : topic.value?.urgency === 'P1' ? 'warning' : 'info');
const resultType = computed(() => topic.value?.result === 'SUCCESS' ? 'success' : topic.value?.result === 'UNSOLVABLE' ? 'danger' : '');
const requesterName = computed(() => { const t: any = topic.value; return t?.requesterName ?? t?.requester_name ?? ''; });
const requesterUserId = computed(() => { const t: any = topic.value; return t?.requesterUserId ?? t?.requester_user_id; });

function selectStage(stage: StageTemplateStage) { selectedStageId.value = stage.id; }
async function refreshTopic() { await topicsStore.fetchTopic(topicId.value); }
async function afterBindingChanged() { await Promise.all([topicsStore.fetchTopic(topicId.value), capacityStore.fetchSlots()]); }

function getStageState(stage: StageTemplateStage): TopicStageState | undefined { return stageStates.value.find((ss: any) => (ss.stageId ?? ss.stage_id) === stage.id); }
function getStageStatusLabel(stage: StageTemplateStage): string { const ss = getStageState(stage); const status = ((ss as any)?.status || '').toLowerCase(); if (status === 'done' || status === 'completed') return '已完成'; if (status === 'active' || stage.id === currentStageId.value) return '进行中'; return '待开始'; }
function getStageStatusType(stage: StageTemplateStage): '' | 'success' | 'warning' | 'info' { const label = getStageStatusLabel(stage); if (label === '已完成') return 'success'; if (label === '进行中') return 'warning'; return 'info'; }

function getDeliverableIcon(deliverable: StageDeliverable) {
  const url = deliverable.url?.toLowerCase() || '';
  if (deliverable.type === 'link') {
    if (url.includes('feishu') || url.includes('larksuite')) return markRaw(Memo);
    if (url.includes('confluence') || url.includes('atlassian')) return markRaw(DocumentCopy);
    if (url.includes('notion')) return markRaw(Memo);
    if (url.includes('github') || url.includes('gitlab') || url.includes('git')) return markRaw(Connection);
    if (url.includes('figma') || url.includes('sketch')) return markRaw(Picture);
    return markRaw(Link);
  }
  const mime = deliverable.mimeType?.toLowerCase() || '';
  if (mime.includes('image')) return markRaw(Picture);
  if (mime.includes('video')) return markRaw(VideoCamera);
  return markRaw(Document);
}

function getDeliverableIconStyle(deliverable: StageDeliverable): string {
  const url = deliverable.url?.toLowerCase() || '';
  if (deliverable.type === 'link') {
    if (url.includes('github') || url.includes('gitlab')) return 'bg-zinc-800 text-white';
    if (url.includes('figma')) return 'bg-purple-100 text-purple-600';
    return 'bg-blue-100 text-blue-600';
  }
  return 'bg-emerald-100 text-emerald-600';
}

function openDeliverable(deliverable: StageDeliverable) { window.open(deliverable.url, '_blank'); }
function canDeleteDeliverable(deliverable: StageDeliverable): boolean { return authStore.isAdmin || isDriUser.value || deliverable.createdById === authStore.user?.id; }
async function deleteDeliverable(deliverable: StageDeliverable) {
  try { await ElMessageBox.confirm(`确定删除 "${deliverable.name}"？此操作不可撤销。`, '删除交付物', { type: 'warning' }); await topicsApi.deleteDeliverable(topicId.value, deliverable.id); ElMessage.success('交付物已删除'); await refreshTopic(); }
  catch (error: any) { if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败'); }
}
async function advanceToNextStage() { if (!topic.value?.template?.stages) return; const nextStage = topic.value.template.stages[currentStageIndex.value + 1]; if (!nextStage) return; try { await topicsStore.advanceStage(topicId.value, nextStage.id); selectedStageId.value = nextStage.id; ElMessage.success('已推进到下一阶段'); } catch { ElMessage.error('推进阶段失败'); } }
async function goBackToStage() { if (!selectedBackwardStageId.value) return; try { await topicsStore.backwardStage(topicId.value, selectedBackwardStageId.value); selectedStageId.value = selectedBackwardStageId.value; showBackwardDialog.value = false; selectedBackwardStageId.value = null; ElMessage.success('已回退到上一阶段'); } catch (error: any) { ElMessage.error(error.response?.data?.detail || '回退失败'); } }
async function closeTopic(result: 'SUCCESS' | 'UNSOLVABLE') { const action = result === 'SUCCESS' ? '标记为成功' : '标记为无法解决'; try { await ElMessageBox.confirm(`确定要${action}？此操作是最终的。`, '确认结果', { type: 'warning' }); await topicsStore.updateTopic(topicId.value, { result }); ElMessage.success(`课题已${result === 'SUCCESS' ? '完成' : '标记为无法解决'}`); } catch {} }
function getInitials(name?: string) { if (!name) return ''; return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2); }
function formatDate(date: string) { return dayjs(date).format('YYYY-MM-DD HH:mm'); }
function renderMarkdown(content: string) { return content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>').replace(/\n/g, '<br>'); }

watch(() => currentStageId.value, (stageId) => { if (stageId && !selectedStageId.value) selectedStageId.value = stageId; }, { immediate: true });

onMounted(async () => {
  await Promise.all([capacityStore.fetchSlots(), topicsStore.fetchTopic(topicId.value)]);
  const cid = currentStageId.value;
  if (cid) selectedStageId.value = cid;
  else if (topic.value?.template?.stages?.length) selectedStageId.value = topic.value.template.stages[0].id;
});
</script>
