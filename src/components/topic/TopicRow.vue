<template>
  <div
    class="topic-row"
    :data-topic-drop="props.topic.id"
    @click="emit('open', props.topic)"
  >
    <!-- Main Row -->
    <div class="topic-main">
      <!-- Title & Meta -->
      <div class="topic-content">
        <div class="topic-title-row">
          <h4 class="topic-title">{{ props.topic.title }}</h4>
          <span :class="['priority-tag', `priority-tag--${props.topic.urgency?.toLowerCase()}`]">
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

      <!-- Result Badge -->
      <div class="topic-result">
        <span :class="['result-badge', `result-badge--${props.topic.result?.toLowerCase()}`]">
          {{ resultLabel }}
        </span>
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
          title="拖动释放"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="dri-dot"></span>

          <!-- 名字可点进 profile：必须 stop 掉 pointerdown，避免触发释放拖拽 -->
          <router-link
            v-if="getBindingUserId(b)"
            class="dri-name"
            :to="`/profile/user/${getBindingUserId(b)}`"
            @click.stop
            @mousedown.stop
            @pointerdown.stop
            @pointerup.stop
          >
            {{ getBindingUserName(b) }}
          </router-link>

          <!-- 没有 userId 就展示灰态文本 -->
          <span
            v-else
            class="dri-name dri-name--disabled"
            @click.stop
            @mousedown.stop
            @pointerdown.stop
            @pointerup.stop
            title="该绑定没有关联到用户"
          >
            {{ getBindingUserName(b) }}
          </span>

          <span class="dri-tag">DRI</span>
        </div>

        <!-- Internal Member -->
        <div
          v-else-if="b.slot?.type !== 'EXTERNAL'"
          class="member-chip member-chip--internal"
          title="拖动释放"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="member-dot"></span>
          <span class="member-name">{{ b.slot?.name || '未知' }}</span>
        </div>

        <!-- External Member -->
        <div
          v-else
          class="member-chip member-chip--external"
          title="拖动释放"
          @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
        >
          <span class="member-dot"></span>
          <span class="member-name">{{ b.slot?.name || '未知' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Topic } from '@/types';
import StageTimeline from './StageTimeline.vue';

const props = defineProps<{
  topic: Topic;
  hideStages?: boolean;
}>();

const emit = defineEmits<{
  (e: 'open', topic: Topic): void;
  (e: 'binding-pointerdown', payload: { e: PointerEvent; binding: any }): void;
}>();

const isUncertainty = computed(() => props.topic.type === 'UNCERTAINTY');

const resultLabel = computed(() => {
  switch (props.topic.result) {
    case 'SUCCESS':
      return '已完成';
    case 'UNSOLVABLE':
      return '无法解决';
    case 'OPEN':
      return '进行中';
    default:
      return props.topic.result as any;
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

/**
 * 统一取 userId / userName：兼容所有字段命名
 */
function getBindingUserId(b: any): number | null {
  const id =
    b?.user?.id ??
    b?.userId ??
    b?.user_id ??
    b?.slot?.user?.id ??
    b?.slot?.userId ??
    b?.slot?.user_id ??
    null;

  const n = Number(id);
  return Number.isFinite(n) && n > 0 ? n : null;
}

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
/* ══════════════════════════════════════════════════════════════
   TOPIC ROW - 克制的卡片设计
   ══════════════════════════════════════════════════════════════ */
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

/* ══════════════════════════════════════════════════════════════
   TITLE & META
   ══════════════════════════════════════════════════════════════ */
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

/* ══════════════════════════════════════════════════════════════
   PRIORITY TAG
   ══════════════════════════════════════════════════════════════ */
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

.priority-tag--p0 {
  background: var(--color-priority-p0-bg);
  color: var(--color-priority-p0);
}

.priority-tag--p1 {
  background: var(--color-priority-p1-bg);
  color: var(--color-priority-p1);
}

.priority-tag--p2 {
  background: var(--color-priority-p2-bg);
  color: var(--color-priority-p2);
}

/* ══════════════════════════════════════════════════════════════
   STAGE FLOW
   ══════════════════════════════════════════════════════════════ */
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

/* ══════════════════════════════════════════════════════════════
   RESULT BADGE
   ══════════════════════════════════════════════════════════════ */
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

.result-badge--open {
  background: var(--color-neutral-100);
  color: var(--color-text-secondary);
}

.result-badge--success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.result-badge--unsolvable {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

/* ══════════════════════════════════════════════════════════════
   ACTION BUTTON
   ══════════════════════════════════════════════════════════════ */
.topic-action {
  flex-shrink: 0;
}

/* ══════════════════════════════════════════════════════════════
   BINDINGS
   ══════════════════════════════════════════════════════════════ */
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

/* 让“可拖拽释放”的 chip 有 grab 手势 */
.dri-chip,
.member-chip {
  cursor: grab;
}
.dri-chip:active,
.member-chip:active {
  cursor: grabbing;
}

/* DRI Chip */
.dri-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: var(--space-1) var(--space-2-5);
  background: var(--color-dri-bg);
  border: 1px solid var(--color-dri-border);
  border-radius: var(--radius-md);
  transition: background-color var(--transition-fast);
}

.dri-chip:hover {
  background: var(--color-primary-200);
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
  text-decoration: none;
  cursor: pointer; /* 覆盖 grab，让用户知道能点 */
}

.dri-name:hover {
  text-decoration: underline;
}

.dri-name--disabled {
  cursor: not-allowed;
  opacity: 0.65;
  text-decoration: none;
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

/* Member Chip */
.member-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: var(--space-1) var(--space-2-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: background-color var(--transition-fast);
}

.member-chip--internal {
  background: var(--color-member-internal-bg);
  color: var(--color-member-internal);
}

.member-chip--internal:hover {
  background: var(--color-neutral-200);
}

.member-chip--internal .member-dot {
  background: var(--color-neutral-500);
}

.member-chip--external {
  background: transparent;
  color: var(--color-member-external);
  border: 1px dashed var(--color-member-external-border);
}

.member-chip--external:hover {
  background: var(--color-neutral-50);
}

.member-chip--external .member-dot {
  background: var(--color-neutral-400);
}

.member-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.member-name {
  white-space: nowrap;
}
</style>
