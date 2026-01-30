<template>
  <div class="dashboard">
    <!-- Page Header -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">工作台</h1>
      <p class="dashboard-subtitle" v-if="dragHint">{{ dragHint }}</p>
    </div>

    <div class="dashboard-grid">
      <!-- Left Column: Topics -->
      <div class="dashboard-main">
        <!-- Uncertainty Topics -->
        <section class="topic-section">
          <div class="section-header">
            <div class="section-title-group">
              <h2 class="section-title">不确定性课题</h2>
              <span class="section-count">{{ filteredUncertaintyTopics.length }}</span>
            </div>
            <el-radio-group v-model="uncertaintyFilter" size="small">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="P0">P0</el-radio-button>
              <el-radio-button label="P1">P1</el-radio-button>
              <el-radio-button label="me">DRI=我</el-radio-button>
            </el-radio-group>
          </div>

          <div class="topic-list">
            <TopicRow
              v-for="topic in filteredUncertaintyTopics"
              :key="topic.id"
              :topic="topic"
              :hide-stages="true"
              @open="openTopic"
              @binding-pointerdown="startReleaseDrag"
              :class="{ 'topic-row--hover': hoverTopicId === topic.id }"
            />
            <div v-if="filteredUncertaintyTopics.length === 0" class="empty-state">
              暂无不确定性课题
            </div>
          </div>
        </section>

        <!-- Evolution Topics -->
        <section class="topic-section">
          <div class="section-header">
            <div class="section-title-group">
              <h2 class="section-title">演进课题</h2>
              <span class="section-count">{{ filteredEvolutionTopics.length }}</span>
            </div>
            <el-radio-group v-model="evolutionFilter" size="small">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="P0">P0</el-radio-button>
              <el-radio-button label="P1">P1</el-radio-button>
              <el-radio-button label="me">DRI=我</el-radio-button>
            </el-radio-group>
          </div>

          <div class="topic-list">
            <TopicRow
              v-for="topic in filteredEvolutionTopics"
              :key="topic.id"
              :topic="topic"
              @open="openTopic"
              @binding-pointerdown="startReleaseDrag"
              :class="{ 'topic-row--hover': hoverTopicId === topic.id }"
            />
            <div v-if="filteredEvolutionTopics.length === 0" class="empty-state">
              暂无演进课题
            </div>
          </div>
        </section>
      </div>

      <!-- Right Column: Capacity Pool -->
      <aside class="dashboard-aside" id="dashboard-right-column">
        <!-- Algo Slots -->
        <div
          class="capacity-panel"
          :class="{ 'capacity-panel--active': poolHover === 'ALGO' }"
          data-pool-drop="ALGO"
        >
          <div class="panel-header">
            <span class="panel-title">自有人力</span>
            <span class="panel-count">{{ algoSlots.length }}</span>
          </div>
          <div class="panel-body">
            <div class="slot-grid">
              <div
                v-for="slot in algoSlots"
                :key="slot.id"
                class="slot-item"
                @pointerdown.prevent="startAssignDrag($event, slot.id)"
              >
                <SlotChip :slot="slot" show-percentage :draggable="true" />
              </div>
              <div v-if="algoSlots.length === 0" class="empty-hint">暂无自有人力</div>
            </div>
          </div>
        </div>

        <!-- External Slots -->
        <div
          class="capacity-panel"
          :class="{ 'capacity-panel--active': poolHover === 'EXTERNAL' }"
          data-pool-drop="EXTERNAL"
        >
          <div class="panel-header">
            <span class="panel-title">协调人力</span>
            <span class="panel-count">{{ externalSlots.length }}</span>
          </div>
          <div class="panel-body">
            <div class="slot-grid">
              <div
                v-for="slot in externalSlots"
                :key="slot.id"
                class="slot-item"
                @pointerdown.prevent="startAssignDrag($event, slot.id)"
              >
                <SlotChip :slot="slot" show-percentage :draggable="true" />
              </div>
              <div v-if="externalSlots.length === 0" class="empty-hint">暂无协调人力</div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="stats-panel">
          <div class="panel-header">
            <span class="panel-title">快速统计</span>
          </div>
          <div class="stats-body">
            <div class="stat-row">
              <span class="stat-label">进行中</span>
              <span class="stat-value">{{ openTopicsCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">已完成</span>
              <span class="stat-value stat-value--success">{{ completedTopicsCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">无法解决</span>
              <span class="stat-value stat-value--danger">{{ unsolvableTopicsCount }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Add binding dialog -->
    <AddBindingDialog
      v-model="addBindingOpen"
      :topic-id="bindingTopicId"
      :initial-slot-id="bindingSlotId"
      @created="afterBindingCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import { useTopicsStore } from '@/stores/topics';
import { useCapacityStore } from '@/stores/capacity';
import { useAuthStore } from '@/stores/auth';

import TopicRow from '@/components/topic/TopicRow.vue';
import SlotChip from '@/components/common/SlotChip.vue';
import AddBindingDialog from '@/components/topic/AddBindingDialog.vue';

import type { Topic } from '@/types';

type DragMode = 'none' | 'assign' | 'release';
type PoolType = 'ALGO' | 'EXTERNAL';

const router = useRouter();
const topicsStore = useTopicsStore();
const capacityStore = useCapacityStore();
const authStore = useAuthStore();

const uncertaintyFilter = ref('');
const evolutionFilter = ref('');

/** topics data */
const uncertaintyTopics = computed(() =>
  topicsStore.topics.filter((t) => t.type === 'UNCERTAINTY' && t.result === 'OPEN')
);
const evolutionTopics = computed(() =>
  topicsStore.topics.filter((t) => t.type === 'EVOLUTION' && t.result === 'OPEN')
);

function isDriOfTopic(topic: Topic): boolean {
  const bindings = (topic as any).bindings || [];
  const driBinding = bindings.find((b: any) => b.isDri || b.is_dri);
  if (!driBinding) return false;
  const slotUserId = driBinding.slot?.userId ?? driBinding.slot?.user_id;
  return slotUserId === authStore.user?.id;
}

const filteredUncertaintyTopics = computed(() => {
  let topics = uncertaintyTopics.value;
  if (uncertaintyFilter.value === 'P0') topics = topics.filter((t) => t.urgency === 'P0');
  else if (uncertaintyFilter.value === 'P1') topics = topics.filter((t) => t.urgency === 'P1');
  else if (uncertaintyFilter.value === 'me') topics = topics.filter((t) => isDriOfTopic(t));
  return topics;
});

const filteredEvolutionTopics = computed(() => {
  let topics = evolutionTopics.value;
  if (evolutionFilter.value === 'P0') topics = topics.filter((t) => t.urgency === 'P0');
  else if (evolutionFilter.value === 'P1') topics = topics.filter((t) => t.urgency === 'P1');
  else if (evolutionFilter.value === 'me') topics = topics.filter((t) => isDriOfTopic(t));
  return topics;
});

/** slots data */
const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

/** stats */
const openTopicsCount = computed(() => topicsStore.topics.filter((t) => t.result === 'OPEN').length);
const completedTopicsCount = computed(() => topicsStore.topics.filter((t) => t.result === 'SUCCESS').length);
const unsolvableTopicsCount = computed(() => topicsStore.topics.filter((t) => t.result === 'UNSOLVABLE').length);

function openTopic(topic: Topic) {
  router.push(`/topics/${topic.id}`);
}

/** AddBindingDialog state */
const addBindingOpen = ref(false);
const bindingTopicId = ref(0);
const bindingSlotId = ref<number | undefined>(undefined);

async function afterBindingCreated() {
  await Promise.all([topicsStore.fetchTopics(), capacityStore.fetchSlots()]);
}

/** pointer-drag core */
const dragMode = ref<DragMode>('none');
const draggingSlotId = ref<number | null>(null);
const draggingBindingId = ref<number | null>(null);

const hoverTopicId = ref<number | null>(null);
const poolHover = ref<PoolType | null>(null);

const dragHint = computed(() => {
  if (dragMode.value === 'assign') return '拖动人员到课题上进行分配';
  if (dragMode.value === 'release') return '拖动分配块到右侧释放人力';
  return '';
});

let ghostEl: HTMLDivElement | null = null;

function createGhost(text: string, x: number, y: number) {
  ghostEl = document.createElement('div');
  ghostEl.style.cssText = `
    position: fixed;
    left: ${x + 12}px;
    top: ${y + 12}px;
    z-index: 99999;
    pointer-events: none;
    padding: 6px 12px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--color-border-default);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-primary);
  `;
  ghostEl.innerText = text;
  document.body.appendChild(ghostEl);
}

function moveGhost(x: number, y: number) {
  if (!ghostEl) return;
  ghostEl.style.left = `${x + 12}px`;
  ghostEl.style.top = `${y + 12}px`;
}

function removeGhost() {
  if (ghostEl) ghostEl.remove();
  ghostEl = null;
}

function findTopicIdUnderPointer(x: number, y: number): number | null {
  const el = document.elementFromPoint(x, y) as HTMLElement | null;
  if (!el) return null;
  const holder = el.closest('[data-topic-drop]') as HTMLElement | null;
  if (!holder) return null;
  const id = Number(holder.getAttribute('data-topic-drop'));
  return Number.isFinite(id) ? id : null;
}

function findPoolUnderPointer(x: number, y: number): PoolType | null {
  const el = document.elementFromPoint(x, y) as HTMLElement | null;
  if (el) {
    const holder = el.closest('[data-pool-drop]') as HTMLElement | null;
    if (holder) {
      const raw = holder.getAttribute('data-pool-drop') as PoolType | null;
      if (raw === 'ALGO' || raw === 'EXTERNAL') return raw;
    }
  }
  const right = document.getElementById('dashboard-right-column');
  if (!right) return null;

  const rect = right.getBoundingClientRect();
  const inside = x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
  if (!inside) return null;

  const algoEl = right.querySelector('[data-pool-drop="ALGO"]') as HTMLElement | null;
  const extEl = right.querySelector('[data-pool-drop="EXTERNAL"]') as HTMLElement | null;

  if (algoEl && extEl) {
    const a = algoEl.getBoundingClientRect();
    const e = extEl.getBoundingClientRect();
    const inAlgo = x >= a.left && x <= a.right && y >= a.top && y <= a.bottom;
    const inExt = x >= e.left && x <= e.right && y >= e.top && y <= e.bottom;
    if (inAlgo) return 'ALGO';
    if (inExt) return 'EXTERNAL';
    return y < (a.bottom + e.top) / 2 ? 'ALGO' : 'EXTERNAL';
  }
  if (algoEl) return 'ALGO';
  if (extEl) return 'EXTERNAL';
  return null;
}

/** Assign: Slot -> Topic */
function startAssignDrag(e: PointerEvent, slotId: number) {
  if (e.button !== 0) return;

  dragMode.value = 'assign';
  draggingSlotId.value = slotId;
  hoverTopicId.value = null;

  const slot = capacityStore.slots.find((s) => s.id === slotId);
  createGhost(slot?.name ?? `Slot#${slotId}`, e.clientX, e.clientY);

  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  window.addEventListener('pointermove', onAssignMove, { passive: true });
  window.addEventListener('pointerup', onAssignUp, { passive: true });
}

function onAssignMove(e: PointerEvent) {
  if (dragMode.value !== 'assign') return;
  moveGhost(e.clientX, e.clientY);
  hoverTopicId.value = findTopicIdUnderPointer(e.clientX, e.clientY);
}

function onAssignUp() {
  if (dragMode.value !== 'assign') return;

  window.removeEventListener('pointermove', onAssignMove);
  window.removeEventListener('pointerup', onAssignUp);
  removeGhost();

  const slotId = draggingSlotId.value;
  const topicId = hoverTopicId.value;

  dragMode.value = 'none';
  draggingSlotId.value = null;
  hoverTopicId.value = null;

  if (!slotId || !topicId) return;

  bindingTopicId.value = topicId;
  bindingSlotId.value = slotId;
  addBindingOpen.value = true;
}

/** ---- Release helpers ---- */

function getTopicAndBinding(bindingId: number): { topic: any; binding: any } | null {
  for (const t of topicsStore.topics as any[]) {
    const b = t.bindings?.find((x: any) => x.id === bindingId);
    if (b) return { topic: t, binding: b };
  }
  return null;
}

/** 前端预判：是否允许释放（避免“最后一个DRI”触发后端约束失败） */
function canReleaseBinding(bindingId: number): { ok: boolean; reason?: string } {
  const pair = getTopicAndBinding(bindingId);
  if (!pair) return { ok: true }; // 本地没找到，交给后端处理

  const { topic, binding } = pair;
  const bindings = (topic.bindings || []) as any[];

  const isDri = !!(binding.isDri || binding.is_dri);
  const bindingCount = bindings.length;

  // 如果这个课题只有一个绑定，并且它是 DRI，则不允许释放
  if (isDri && bindingCount <= 1) {
    return { ok: false, reason: '该课题只剩最后一个 DRI，不能释放。请先为课题分配其他成员/DRI。' };
  }

  return { ok: true };
}

/** Release: Binding -> Pool */
function startReleaseDrag(payload: { e: PointerEvent; binding: any }) {
  const e = payload.e;
  if (e.button !== 0) return;

  // ✅ 点击跳转/点击文本时不要被拖拽吃掉（后续你把 TopicRow 的名字改成 router-link 后就生效）
  const target = e.target as HTMLElement | null;
  if (
    target?.closest('a') ||              // router-link 渲染成 <a>
    target?.closest('.dri-name') ||      // 你现在 DOM 里就是 .dri-name
    target?.closest('[data-no-drag]')    // 预留：以后想强制禁拖的区域加这个属性
  ) {
    return;
  }

  // ✅ 前置规则：最后一个 DRI 不允许释放（避免后端 not null/约束失败导致回滚）
  const check = canReleaseBinding(payload.binding.id);
  if (!check.ok) {
    ElMessage.warning(check.reason || '当前绑定不允许释放');
    return;
  }

  dragMode.value = 'release';
  draggingBindingId.value = payload.binding.id;
  poolHover.value = null;

  const label = `${payload.binding.slot?.name ?? `Slot#${payload.binding.slotId}`} (${payload.binding.percentage}%)`;
  createGhost(label, e.clientX, e.clientY);

  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  window.addEventListener('pointermove', onReleaseMove, { passive: true });
  window.addEventListener('pointerup', onReleaseUp, { passive: true });
}

function onReleaseMove(e: PointerEvent) {
  if (dragMode.value !== 'release') return;
  moveGhost(e.clientX, e.clientY);
  poolHover.value = findPoolUnderPointer(e.clientX, e.clientY);
}

function findBindingInLocalState(bindingId: number): any | null {
  const pair = getTopicAndBinding(bindingId);
  if (!pair) return null;

  const { topic, binding } = pair;

  // 兼容不同字段命名
  const slotId = binding.slotId ?? binding.slot_id ?? binding.slot?.id;
  const topicId = binding.topicId ?? binding.topic_id ?? topic.id;

  return { ...binding, topicId, slotId };
}

/** 一个 slot 可能被拆成多个 binding（同 topic 同 slot），释放时一起删 */
function findAllBindingIdsInSameTopicAndSlot(bindingId: number): number[] {
  const pair = getTopicAndBinding(bindingId);
  if (!pair) return [];

  const { topic, binding } = pair;
  const slotId = binding.slotId ?? binding.slot_id ?? binding.slot?.id;
  if (!slotId) return [];

  return (topic.bindings || [])
    .filter((x: any) => (x.slotId ?? x.slot_id ?? x.slot?.id) === slotId)
    .map((x: any) => x.id);
}

async function onReleaseUp() {
  if (dragMode.value !== 'release') return;

  window.removeEventListener('pointermove', onReleaseMove);
  window.removeEventListener('pointerup', onReleaseUp);
  removeGhost();

  const bindingId = draggingBindingId.value;
  const pool = poolHover.value;

  dragMode.value = 'none';
  draggingBindingId.value = null;
  poolHover.value = null;

  if (!bindingId || !pool) return;

  // 再做一次兜底校验（防止拖拽过程中状态变化）
  const check = canReleaseBinding(bindingId);
  if (!check.ok) {
    ElMessage.warning(check.reason || '当前绑定不允许释放');
    return;
  }

  const binding = findBindingInLocalState(bindingId);

  // 本地没找到，直接删 + 刷新
  if (!binding) {
    try {
      await capacityStore.deleteBinding(bindingId);
      await Promise.all([topicsStore.fetchTopics(), capacityStore.fetchSlots()]);
      ElMessage.success('已释放');
    } catch {
      ElMessage.error('释放失败');
    }
    return;
  }

  const ids = findAllBindingIdsInSameTopicAndSlot(bindingId);
  if (!ids.length) return;

  // snapshot rollback
  const snapshot: any[] = [];
  {
    const t = (topicsStore.topics as any[]).find((x) => x.id === binding.topicId);
    if (t?.bindings?.length) {
      for (const id of ids) {
        const b = t.bindings.find((x: any) => x.id === id);
        if (b) snapshot.push({ ...b, topicId: b.topicId ?? b.topic_id ?? t.id });
      }
    }
  }

  // optimistic remove
  for (const id of ids) {
    topicsStore.removeBindingLocal(id);
    capacityStore.removeBindingLocal(id);
  }

  try {
    await Promise.all(ids.map((id) => capacityStore.deleteBinding(id)));
    ElMessage.success('已释放');
  } catch (err: any) {
    // rollback
    for (const b of snapshot) {
      const slotId = b.slotId ?? b.slot_id ?? b.slot?.id;
      topicsStore.addBindingLocal(b.topicId, b);
      capacityStore.addBindingLocal(slotId, b);
    }

    // ✅ 这里把“最后一个DRI/约束失败”提示得更明确一些
    const msg = String(err?.response?.data?.detail || err?.message || '');
    if (msg.includes('dri') || msg.includes('DRI') || msg.includes('not null')) {
      ElMessage.error('释放失败：该课题必须保留 DRI 责任人（请先分配其他成员/DRI）');
    } else {
      ElMessage.error('释放失败，已回滚');
    }
  }
}

onMounted(() => {
  topicsStore.fetchTopics();
  capacityStore.fetchSlots();
});
</script>

<style scoped>
.dashboard {
  max-width: var(--content-max-width);
}

.dashboard-header {
  margin-bottom: var(--space-6);
}

.dashboard-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  letter-spacing: var(--tracking-tight);
  margin: 0;
}

.dashboard-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-5);
}

.dashboard-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.topic-section {
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-secondary);
}

.section-title-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.section-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: var(--tracking-tight);
}

.section-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--color-neutral-200);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
}

.topic-list {
  max-height: 380px;
  overflow-y: auto;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.topic-row--hover {
  box-shadow: inset 0 0 0 2px var(--color-primary-300);
}

.empty-state {
  text-align: center;
  padding: var(--space-10) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.dashboard-aside {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.capacity-panel,
.stats-panel {
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.capacity-panel--active {
  border-color: var(--color-primary-400);
  box-shadow: 0 0 0 2px var(--color-primary-100);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-secondary);
}

.panel-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.panel-count {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  background: var(--color-neutral-200);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.panel-body {
  padding: var(--space-4);
}

.slot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.slot-item {
  cursor: grab;
  user-select: none;
}

.slot-item:active {
  cursor: grabbing;
}

.empty-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.stats-body {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.stat-value {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

.stat-value--success {
  color: var(--color-success);
}

.stat-value--danger {
  color: var(--color-danger);
}
</style>
