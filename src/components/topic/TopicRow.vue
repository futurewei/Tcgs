<template>
  <div class="topic-row" :data-topic-drop="props.topic.id" @click="emit('open', props.topic)">
    <!-- Main Row -->
    <div class="topic-main">
      <!-- Title & Meta -->
      <div class="topic-content">
        <div class="topic-title-row">
          <h4 class="topic-title">{{ props.topic.title }}</h4>
          <span :class="['priority-tag', `priority-tag--${(props.topic.urgency || '').toLowerCase()}`]">
            {{ props.topic.urgency }}
          </span>
        </div>
        <div class="topic-meta">
          <span class="meta-item">ID: {{ props.topic.id }}</span>
          <span v-if="requesterName" class="meta-item">需求方: {{ requesterName }}</span>
        </div>
      </div>

      <!-- Stage Timeline (演进课题才显示) -->
      <div v-if="!hideStages && !isUncertainty" class="topic-stages" @click.stop>
        <StageTimeline :stages="stages" :stage-states="stageStates" :current-stage-id="currentStageId" compact />
      </div>

      <!-- Stage Flow (不确定性课题) -->
      <div v-if="!hideStages && isUncertainty && stageInstancesNormalized.length" class="topic-stages" @click.stop>
        <div class="stage-flow">
          <template v-for="(stage, idx) in stageInstancesNormalized" :key="stage.id">
            <div :class="['stage-chip', `stage-chip--${stage.status}`]">
              {{ stage.name }}
              <span v-if="stage.status === 'done'" class="stage-icon">✓</span>
              <span v-if="stage.status === 'active'" class="stage-dot"></span>
            </div>
            <span v-if="idx < stageInstancesNormalized.length - 1" class="stage-arrow">→</span>
          </template>
        </div>
      </div>

	<!-- Result Badge + Actions -->
<div class="topic-result" @click.stop>
  <span :class="['result-badge', `result-badge--${(props.topic.result || '').toLowerCase()}`]">
    {{ resultLabel }}
  </span>

  <!-- ✅ 右上角状态改写按钮（三点） -->
  <el-dropdown trigger="click" @command="changeTopicResult">
    <el-button text class="topic-more-btn" @click.stop>
      <el-icon><MoreFilled /></el-icon>
    </el-button>

    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="OPEN">标记为进行中</el-dropdown-item>
        <el-dropdown-item command="SUCCESS">标记为已完成</el-dropdown-item>
        <el-dropdown-item command="UNSOLVABLE">标记为无法解决</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</div>

      <!-- Action -->
      <el-button size="small" class="topic-action" @click.stop="emit('open', props.topic)">打开</el-button>
    </div>

    <!-- Bindings Row -->
    <div v-if="sortedBindings.length" class="topic-bindings" @click.stop>
      <div v-for="b in sortedBindings" :key="b.id" class="binding-item">
        <!-- DRI -->
        <div
          v-if="b.isDri"
          class="dri-chip"
          title="点击编辑时间投入，长按拖拽释放（DRI会被拦截）"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="dri-dot"></span>

          <!-- 短按打开编辑对话框，长按触发拖拽 -->
          <span
            class="dri-name"
            :class="{ 'dri-name--clickable': true }"
            @click.stop="onNameClick($event, b)"
            @pointerdown.stop.prevent="startLongPress($event, b)"
            title="点击编辑时间投入，长按拖拽释放"
          >
            {{ getBindingUserName(b) }}
          </span>

          <span class="dri-tag">DRI</span>
        </div>

        <!-- Internal Member -->
        <div
          v-else-if="b.slot?.type !== 'EXTERNAL'"
          class="member-chip member-chip--internal"
          title="点击编辑，拖动释放"
          @click.stop="emit('binding-click', b)"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="member-dot"></span>
          <span class="member-name">{{ b.slot?.name || '未知' }}</span>
          <span class="member-percent">{{ b.percentage ?? 0 }}%</span>
        </div>

        <!-- External Member -->
        <div
          v-else
          class="member-chip member-chip--external"
          title="点击编辑，拖动释放"
          @click.stop="emit('binding-click', b)"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="member-dot"></span>
          <span class="member-name">{{ b.slot?.name || '未知' }}</span>
          <span class="member-percent">{{ b.percentage ?? 0 }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { MoreFilled } from '@element-plus/icons-vue';
import { useTopicsStore } from '@/stores/topics';
import { computed, ref, onUnmounted } from 'vue';
import type { Topic } from '@/types';
import StageTimeline from './StageTimeline.vue';

const topicsStore = useTopicsStore();

const props = defineProps<{
  topic: Topic;
  hideStages?: boolean;
}>();

const emit = defineEmits<{
  (e: 'open', topic: Topic): void;
  (e: 'binding-pointerdown', payload: { e: PointerEvent; binding: any }): void;
  (e: 'binding-click', binding: any): void;
  (e: 'result-updated'): void; // ✅ 新增：通知父组件刷新列表
}>();

async function changeTopicResult(result: 'OPEN' | 'SUCCESS' | 'UNSOLVABLE') {
  try {
    await topicsStore.updateTopic(props.topic.id, { result });
    ElMessage.success('课题状态已更新');

    /**
     * ✅ 关键：Dashboard/全站默认只看 OPEN，
     * 如果设置为 SUCCESS/UNSOLVABLE，这条应该从列表消失。
     * 父组件收到事件后会 fetchTopics() => 默认 OPEN => 消失。
     */
    emit('result-updated');
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || '更新失败');
  }
}
// ========== 长按拖拽逻辑 ==========
const LONG_PRESS_DURATION = 300; // ms

let longPressTimer: ReturnType<typeof setTimeout> | null = null;
let pendingBinding: any = null;
let pendingEvent: PointerEvent | null = null;
const isLongPressing = ref(false);

function startLongPress(e: PointerEvent, binding: any) {
  // 只响应左键
  if (e.button !== 0) return;

  pendingBinding = binding;
  pendingEvent = e;
  isLongPressing.value = false;

  longPressTimer = setTimeout(() => {
    isLongPressing.value = true;
    // 长按触发拖拽
    if (pendingEvent && pendingBinding) {
      emit('binding-pointerdown', { e: pendingEvent, binding: pendingBinding });
    }
    clearLongPress();
  }, LONG_PRESS_DURATION);

  // 监听取消事件
  window.addEventListener('pointerup', cancelLongPress, { once: true });
  window.addEventListener('pointermove', onPointerMoveCheck);
}

function onPointerMoveCheck(e: PointerEvent) {
  // 如果移动超过阈值，取消长按（允许小幅度抖动）
  if (!pendingEvent) return;
  const dx = Math.abs(e.clientX - pendingEvent.clientX);
  const dy = Math.abs(e.clientY - pendingEvent.clientY);
  if (dx > 5 || dy > 5) {
    cancelLongPress();
  }
}

function cancelLongPress() {
  if (longPressTimer) {
    clearTimeout(longPressTimer);
    longPressTimer = null;
  }
  pendingBinding = null;
  pendingEvent = null;
  window.removeEventListener('pointermove', onPointerMoveCheck);
}

function clearLongPress() {
  longPressTimer = null;
  pendingBinding = null;
  pendingEvent = null;
  window.removeEventListener('pointerup', cancelLongPress);
  window.removeEventListener('pointermove', onPointerMoveCheck);
}

function onNameClick(e: MouseEvent, binding: any) {
  // 如果刚刚触发了长按拖拽，阻止点击
  if (isLongPressing.value) {
    e.preventDefault();
    e.stopPropagation();
    isLongPressing.value = false;
    return;
  }
  // 短按打开编辑对话框
  e.preventDefault();
  e.stopPropagation();
  emit('binding-click', binding);
}

onUnmounted(() => {
  cancelLongPress();
});

// ========== 其余显示逻辑 ==========
const isUncertainty = computed(() => props.topic.type === 'UNCERTAINTY');

const resultLabel = computed(() => {
  switch ((props.topic as any).result) {
    case 'SUCCESS':
      return '已完成';
    case 'UNSOLVABLE':
      return '无法解决';
    case 'OPEN':
      return '进行中';
    default:
      return (props.topic as any).result;
  }
});

const requesterName = computed(() => {
  const t: any = props.topic;
  return t?.requesterName ?? t?.requester_name ?? '';
});

const stages = computed(() => {
  const t: any = props.topic;
  return t?.template?.stages ?? [];
});

const stageStates = computed(() => {
  const t: any = props.topic;
  return t?.stageStates ?? t?.stage_states ?? [];
});

const currentStageId = computed(() => {
  const t: any = props.topic;
  return t?.currentStageId ?? t?.current_stage_id;
});

const stageInstancesNormalized = computed(() => {
  const t: any = props.topic;
  const instances = t?.stageInstances ?? t?.stage_instances ?? [];
  return instances
    .map((s: any) => ({
      id: s.id,
      name: s.name,
      status: s.status,
      order: s.order,
    }))
    .sort((a: any, b: any) => (a.order ?? 0) - (b.order ?? 0));
});

function getBindingUserName(b: any): string {
  return b?.user?.name ?? b?.slot?.user?.name ?? b?.slot?.name ?? '未知';
}

const sortedBindings = computed(() => {
  const t: any = props.topic;
  const arr = (t?.bindings ?? t?.capacity_bindings ?? []) as any[];

  // 同一个 slot 只显示一次
  const seen = new Set<number>();
  const out: any[] = [];

  for (const b of arr) {
    const sid = Number(b.slotId ?? b.slot_id ?? b.slot?.id);
    if (!sid) continue;
    if (seen.has(sid)) continue;
    seen.add(sid);

    out.push({
      ...b,
      slotId: b.slotId ?? b.slot_id ?? b.slot?.id,
      topicId: b.topicId ?? b.topic_id ?? t?.id,
      isDri: b.isDri ?? b.is_dri ?? false,
    });
  }

  return out.sort((a, b) => {
    if (a.isDri && !b.isDri) return -1;
    if (!a.isDri && b.isDri) return 1;
    return (b.percentage || 0) - (a.percentage || 0);
  });
});
</script>

<style scoped>
.topic-more-btn {
  margin-left: 6px;
}
.topic-row {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: border-color var(--transition-fast), background-color var(--transition-fast);
}

.topic-row:hover {
  border-color: var(--color-border-default);
  background: var(--color-surface-hover);
}

.topic-main {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.topic-content {
  flex: 1;
  min-width: 0;
}

.topic-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.topic-title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: var(--tracking-tight);
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.meta-item {
  white-space: nowrap;
}

.priority-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 18px;
  padding: 0 6px;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: var(--font-semibold);
  flex-shrink: 0;
}

.topic-stages {
  flex-shrink: 0;
}

.stage-flow {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-wrap: wrap;
  max-width: 400px;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: var(--font-medium);
  white-space: nowrap;
}

.stage-chip--pending {
  background: var(--color-neutral-100);
  color: var(--color-text-muted);
}

.stage-chip--active {
  background: var(--color-primary-100);
  color: var(--color-primary-600);
  box-shadow: inset 0 0 0 1px var(--color-primary-200);
}

.stage-chip--done {
  background: var(--color-success-light);
  color: var(--color-success);
}

.stage-icon {
  font-size: 9px;
}

.stage-dot {
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: var(--radius-full);
  animation: tcgs-pulse 2s infinite;
}

.stage-arrow {
  color: var(--color-text-disabled);
  font-size: 10px;
}

.topic-result {
  flex-shrink: 0;
}

.result-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.topic-action {
  flex-shrink: 0;
}

.topic-bindings {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
}

.binding-item {
  user-select: none;
}

/* DRI */
.dri-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: var(--space-1) var(--space-2-5);
  background: var(--color-dri-bg);
  border: 1px solid var(--color-dri-border);
  border-radius: var(--radius-md);
  cursor: grab;
}

.dri-chip:active {
  cursor: grabbing;
}

.dri-dot {
  width: 6px;
  height: 6px;
  background: var(--color-dri);
  border-radius: var(--radius-full);
}

.dri-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-dri);
  cursor: pointer;
  user-select: none;
}

.dri-name--clickable:hover {
  text-decoration: underline;
}

.dri-tag {
  padding: 1px 5px;
  background: var(--color-primary);
  border-radius: 3px;
  font-size: 9px;
  font-weight: var(--font-bold);
  color: var(--color-text-inverse);
  letter-spacing: 0.03em;
}

/* Members */
.member-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: var(--space-1) var(--space-2-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: grab;
}

.member-chip:active {
  cursor: grabbing;
}

.member-chip--internal {
  background: var(--color-member-internal-bg);
  color: var(--color-member-internal);
}

.member-chip--external {
  background: transparent;
  color: var(--color-member-external);
  border: 1px dashed var(--color-member-external-border);
}

.member-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  background: currentColor;
  opacity: 0.8;
}

.member-name {
  white-space: nowrap;
}

.member-percent {
  margin-left: 6px;
  font-size: 12px;
  opacity: 0.75;
}
</style>
