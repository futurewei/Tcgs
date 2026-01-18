<template>
  <div v-loading="loading" class="space-y-6">
    <!-- Back + Header -->
    <div class="flex items-center gap-4">
      <el-button text @click="router.back()">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>
        Back
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
                <el-tag type="info" size="small">{{ topic.type }}</el-tag>
              </div>
              <p class="text-zinc-500">ID: {{ topic.id }}</p>
            </div>
            <el-tag :type="resultType" size="large">{{ topic.result }}</el-tag>
          </div>

          <!-- Stage Timeline (Full Version) -->
          <div class="mt-6">
            <p class="text-sm font-medium text-zinc-500 mb-3">Stage Progress</p>
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
            <h2 class="font-semibold text-zinc-900">Basic Information</h2>
            <el-button v-if="canEdit" size="small" @click="showEditInfo = true">
              Edit
            </el-button>
          </div>
          <div class="prose prose-sm max-w-none">
            <p>{{ topic.description }}</p>
          </div>
          <!-- Requester Information -->
          <div class="mt-4 pt-4 border-t border-zinc-200">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-zinc-700">Requester:</span>
              <span class="text-sm text-zinc-900">{{ requesterName }}</span>
              <el-tag v-if="requesterUserId" type="info" size="small">Customer</el-tag>
              <el-tag v-else type="warning" size="small">External Requester</el-tag>
            </div>
          </div>
        </div>

        <!-- Stage Content Area -->
        <div v-if="selectedStage" class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div>
              <h2 class="font-semibold text-zinc-900">{{ selectedStage.name }}</h2>
              <p class="text-sm text-zinc-500">{{ selectedStage.description }}</p>
            </div>
            <div class="flex items-center gap-2">
              <el-tag v-if="selectedStage.isTerminal" type="warning" size="small">Terminal</el-tag>
              <el-tag v-if="selectedStage.requireArtifact" type="info" size="small">Requires Artifact</el-tag>
            </div>
          </div>

          <div class="p-6 space-y-6">
            <!-- Artifacts Section -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-medium text-zinc-800">Artifacts</h3>
                <el-button v-if="!authStore.isCustomer" size="small" @click="showAddArtifact = true">
                  Add Artifact
                </el-button>
              </div>

              <div class="space-y-3">
                <div
                  v-for="artifact in stageArtifacts"
                  :key="artifact.id"
                  class="p-4 bg-zinc-50 rounded-lg"
                >
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium">{{ artifact.title }}</h4>
                    <span class="text-xs text-zinc-400">
                      {{ artifact.createdBy?.name }} • {{ formatDate(artifact.createdAt) }}
                    </span>
                  </div>
                  <div class="prose prose-sm max-w-none" v-html="renderMarkdown(artifact.content)"></div>
                </div>

                <p v-if="stageArtifacts.length === 0" class="text-sm text-zinc-400 text-center py-4">
                  No artifacts yet
                </p>
              </div>
            </div>

            <!-- Reviews Section -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-medium text-zinc-800">Reviews</h3>
                <el-button v-if="!authStore.isCustomer" size="small" @click="showAddReview = true">
                  Add Review
                </el-button>
              </div>

              <div class="space-y-3">
                <div
                  v-for="review in stageReviews"
                  :key="review.id"
                  class="p-4 bg-zinc-50 rounded-lg"
                >
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs">
                      {{ getInitials(review.createdBy?.name) }}
                    </div>
                    <span class="font-medium text-sm">{{ review.createdBy?.name }}</span>
                    <span class="text-xs text-zinc-400">{{ formatDate(review.createdAt) }}</span>
                  </div>
                  <div class="prose prose-sm max-w-none" v-html="renderMarkdown(review.content)"></div>
                </div>

                <p v-if="stageReviews.length === 0" class="text-sm text-zinc-400 text-center py-4">
                  No reviews yet
                </p>
              </div>
            </div>

            <!-- Closure Section (only for terminal stages) -->
            <div v-if="selectedStage.isTerminal && selectedStage.allowResult">
              <h3 class="font-medium text-zinc-800 mb-4">Closure</h3>
              <div class="flex items-center gap-4">
                <el-button
                  v-if="topic.result === 'OPEN' && canEdit && !authStore.isCustomer"
                  type="success"
                  @click="closeTopic('SUCCESS')"
                >
                  Mark as Success
                </el-button>
                <el-button
                  v-if="topic.result === 'OPEN' && canEdit && !authStore.isCustomer"
                  type="danger"
                  @click="closeTopic('UNSOLVABLE')"
                >
                  Mark as Unsolvable
                </el-button>
                <el-tag v-if="topic.result !== 'OPEN'" :type="resultType" size="large">
                  {{ topic.result }}
                </el-tag>
              </div>
            </div>

            <!-- Advance Stage Button -->
            <div v-if="canAdvanceStage && canEdit && !authStore.isCustomer" class="pt-4 border-t border-zinc-200">
              <el-button type="primary" @click="advanceToNextStage">
                Advance to Next Stage
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Sticky Sidebar (4 columns) -->
      <div class="col-span-4">
        <div class="sticky top-20 space-y-4">
          <!-- DRI Card -->
          <div class="bg-white rounded-xl border border-zinc-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-zinc-900">DRI</h3>
              <el-button v-if="authStore.isAdmin" size="small" text @click="showChangeDRI = true">
                Change
              </el-button>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-zinc-200 rounded-full flex items-center justify-center font-medium text-zinc-600">
                {{ getInitials(topic.dri?.name) }}
              </div>
              <div>
                <p class="font-medium text-zinc-900">{{ topic.dri?.name }}</p>
                <p class="text-xs text-zinc-500">{{ topic.dri?.email }}</p>
              </div>
            </div>
          </div>

          <!-- Bindings Card -->
          <div class="bg-white rounded-xl border border-zinc-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-zinc-900">Bindings</h3>
              <el-button v-if="authStore.isAdmin" size="small" text @click="showAddBinding = true">
                Add
              </el-button>
            </div>
            <div class="space-y-2">
              
		<div
  		v-for="binding in ((topic as any).bindings || (topic as any).capacity_bindings || [])"
  		:key="binding.id"
  		class="flex items-center justify-between"
		>
  		<template v-if="binding.slot">
   		 <SlotChip :slot="binding.slot" :binding-percentage="binding.percentage" />
  		</template>
  		<template v-else>
    		<div class="text-sm text-zinc-500">Slot: (not loaded)</div>
  		</template>

 		 <div class="flex items-center gap-2">
   		 <span class="text-sm font-medium">{{ binding.percentage }}%</span>
   		 <el-tag v-if="binding.isForced" type="warning" size="small">Forced</el-tag>
  		</div>
		</div>

		<p v-if="!(((topic as any).bindings || (topic as any).capacity_bindings || []).length)" class="text-sm text-zinc-400">
                No capacity bindings
              </p>
            </div>
          </div>

          <!-- Recent Audit -->
          <div class="bg-white rounded-xl border border-zinc-200 p-4">
            <h3 class="font-semibold text-zinc-900 mb-3">Recent Activity</h3>
            <div class="space-y-2 max-h-[300px] overflow-y-auto">
              <div
                v-for="log in recentAuditLogs"
                :key="log.id"
                class="p-2 bg-zinc-50 rounded text-xs"
              >
                <p class="font-medium text-zinc-700">{{ log.action }}</p>
                <p class="text-zinc-500">{{ log.user?.name }} • {{ formatDate(log.createdAt) }}</p>
              </div>
              <p v-if="recentAuditLogs.length === 0" class="text-sm text-zinc-400">
                No recent activity
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <AddArtifactDialog
      v-model="showAddArtifact"
      :topic-id="topicId"
      :stage-id="selectedStageId"
      @created="refreshTopic"
    />
    <AddReviewDialog
      v-model="showAddReview"
      :topic-id="topicId"
      :stage-id="selectedStageId"
      @created="refreshTopic"
    />
    <ChangeDRIDialog
      v-model="showChangeDRI"
      :topic="topic"
      @changed="refreshTopic"
    />
    <AddBindingDialog
      v-model="showAddBinding"
      :topic-id="topicId"
      @created="refreshTopic"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useAuthStore } from '@/stores/auth';
import { ArrowLeft } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import StageTimeline from '@/components/topic/StageTimeline.vue';
import SlotChip from '@/components/common/SlotChip.vue';
import AddArtifactDialog from '@/components/topic/AddArtifactDialog.vue';
import AddReviewDialog from '@/components/topic/AddReviewDialog.vue';
import ChangeDRIDialog from '@/components/topic/ChangeDRIDialog.vue';
import AddBindingDialog from '@/components/topic/AddBindingDialog.vue';
import dayjs from 'dayjs';
import type { StageTemplateStage, AuditLog, TopicStageState, Artifact, ReviewComment } from '@/types';

const route = useRoute();
const router = useRouter();
const topicsStore = useTopicsStore();
const authStore = useAuthStore();

const topicId = computed(() => Number(route.params.id));
const topic = computed(() => topicsStore.currentTopic);
const loading = computed(() => topicsStore.loading);

const selectedStageId = ref<number | null>(null);
const showEditInfo = ref(false);
const showAddArtifact = ref(false);
const showAddReview = ref(false);
const showChangeDRI = ref(false);
const showAddBinding = ref(false);
const recentAuditLogs = ref<AuditLog[]>([]);

/**
 * ✅ 兼容 snake_case (后端) 与 camelCase (前端 types)
 * 后端返回: current_stage_id, stage_states
 */
const currentStageId = computed<number | undefined>(() => {
  const t: any = topic.value;
  return t?.currentStageId ?? t?.current_stage_id;
});

const stageStates = computed<TopicStageState[]>(() => {
  const t: any = topic.value;
  return (t?.stageStates ?? t?.stage_states ?? []) as TopicStageState[];
});

const selectedStage = computed(() => {
  if (!selectedStageId.value || !topic.value?.template?.stages) return null;
  return topic.value.template.stages.find(s => s.id === selectedStageId.value) || null;
});

/**
 * artifacts / reviews 字段也做兼容（有的后端是 stage_id）
 */
const stageArtifacts = computed<Artifact[]>(() => {
  if (!selectedStageId.value) return [];
  const t: any = topic.value;
  const artifacts: Artifact[] = (t?.artifacts ?? []) as Artifact[];
  return artifacts.filter((a: any) => (a.stageId ?? a.stage_id) === selectedStageId.value);
});

const stageReviews = computed<ReviewComment[]>(() => {
  if (!selectedStageId.value) return [];
  const t: any = topic.value;
  const reviews: ReviewComment[] = (t?.reviews ?? []) as ReviewComment[];
  return reviews.filter((r: any) => (r.stageId ?? r.stage_id) === selectedStageId.value);
});

const canEdit = computed(() => {
  // CUSTOMER cannot edit
  if (authStore.isCustomer) {
    return false;
  }
  const t: any = topic.value;
  const driId = t?.driId ?? t?.dri_id;
  return authStore.isAdmin || driId === authStore.user?.id;
});

const currentStageIndex = computed(() => {
  const cid = currentStageId.value;
  if (!cid || !topic.value?.template?.stages) return -1;
  return topic.value.template.stages.findIndex(s => s.id === cid);
});

const canAdvanceStage = computed(() => {
  if (!topic.value?.template?.stages) return false;
  const stages = topic.value.template.stages;
  return currentStageIndex.value < stages.length - 1 && topic.value.result === 'OPEN';
});

const urgencyType = computed(() => {
  switch (topic.value?.urgency) {
    case 'P0': return 'danger';
    case 'P1': return 'warning';
    default: return 'info';
  }
});

const resultType = computed(() => {
  switch (topic.value?.result) {
    case 'SUCCESS': return 'success';
    case 'UNSOLVABLE': return 'danger';
    default: return '';
  }
});

function selectStage(stage: StageTemplateStage) {
  selectedStageId.value = stage.id;
}

async function refreshTopic() {
  await topicsStore.fetchTopic(topicId.value);
}

async function advanceToNextStage() {
  if (!topic.value?.template?.stages) return;
  const nextStage = topic.value.template.stages[currentStageIndex.value + 1];
  if (!nextStage) return;

  try {
    await topicsStore.advanceStage(topicId.value, nextStage.id);
    // advanceStage 结束后 store 里应该已经更新 currentTopic，
    // 这里再强制拉一次，保证 stage_states 与 current_stage_id 更新到位
    await topicsStore.fetchTopic(topicId.value);

    selectedStageId.value = nextStage.id;
    ElMessage.success('Advanced to next stage');
  } catch (error) {
    ElMessage.error('Failed to advance stage');
  }
}

async function closeTopic(result: 'SUCCESS' | 'UNSOLVABLE') {
  const action = result === 'SUCCESS' ? 'mark as success' : 'mark as unsolvable';

  try {
    await ElMessageBox.confirm(
      `Are you sure you want to ${action}? This action is final.`,
      'Confirm Closure',
      { type: 'warning' }
    );

    await topicsStore.updateTopic(topicId.value, { result });
    await topicsStore.fetchTopic(topicId.value);
    ElMessage.success(`Topic ${result.toLowerCase()}`);
  } catch (error) {
    // cancelled
  }
}

function getInitials(name?: string) {
  if (!name) return '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(date: string) {
  return dayjs(date).format('MMM D, YYYY h:mm A');
}

function renderMarkdown(content: string) {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

const requesterName = computed(() => {
  const t: any = topic.value;
  return t?.requesterName ?? t?.requester_name ?? '';
});

const requesterUserId = computed(() => {
  const t: any = topic.value;
  return t?.requesterUserId ?? t?.requester_user_id;
});

watch(
  () => currentStageId.value,
  (stageId) => {
    if (stageId && !selectedStageId.value) selectedStageId.value = stageId;
  },
  { immediate: true }
);

onMounted(async () => {
  await topicsStore.fetchTopic(topicId.value);

  const cid = currentStageId.value;
  if (cid) {
    selectedStageId.value = cid;
  } else if (topic.value?.template?.stages?.length) {
    selectedStageId.value = topic.value.template.stages[0].id;
  }
});
</script>
