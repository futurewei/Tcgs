<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">工作台</h1>
    </div>

    <div v-if="dragHint" class="text-xs text-zinc-500">
      {{ dragHint }}
    </div>

    <div class="grid grid-cols-12 gap-4">
      <!-- Left -->
      <div class="col-span-8 space-y-4">
        <!-- Uncertainty Topics -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">不确定性课题</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ filteredUncertaintyTopics.length }}
              </span>
            </div>
            <el-radio-group v-model="uncertaintyFilter" size="small">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="P0">P0</el-radio-button>
              <el-radio-button label="P1">P1</el-radio-button>
              <el-radio-button label="me">DRI=我</el-radio-button>
            </el-radio-group>
          </div>

          <div class="max-h-[360px] overflow-y-auto p-4 space-y-2">
            <TopicRow
              v-for="topic in filteredUncertaintyTopics"
              :key="topic.id"
              :topic="topic"
              @open="openTopic"
              @binding-pointerdown="startReleaseDrag"
              :class="hoverTopicId === topic.id ? 'ring-2 ring-emerald-200 border-emerald-400' : ''"
            />
            <div v-if="filteredUncertaintyTopics.length === 0" class="text-center py-8 text-zinc-400">
              暂无不确定性课题
            </div>
          </div>
        </div>

        <!-- Evolution Projects -->
        <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">演进课题</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ filteredEvolutionTopics.length }}
              </span>
            </div>
            <el-radio-group v-model="evolutionFilter" size="small">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="P0">P0</el-radio-button>
              <el-radio-button label="P1">P1</el-radio-button>
              <el-radio-button label="me">DRI=我</el-radio-button>
            </el-radio-group>
          </div>

          <div class="max-h-[360px] overflow-y-auto p-4 space-y-2">
            <TopicRow
              v-for="topic in filteredEvolutionTopics"
              :key="topic.id"
              :topic="topic"
              @open="openTopic"
              @binding-pointerdown="startReleaseDrag"
              :class="hoverTopicId === topic.id ? 'ring-2 ring-emerald-200 border-emerald-400' : ''"
            />
            <div v-if="filteredEvolutionTopics.length === 0" class="text-center py-8 text-zinc-400">
              暂无演进课题
            </div>
          </div>
        </div>
      </div>

      <!-- Right -->
      <div class="col-span-4 space-y-4" id="dashboard-right-column">
        <!-- Algo Slots -->
        <div
          class="bg-white rounded-xl border overflow-hidden transition-all"
          :class="poolHover === 'ALGO' ? 'border-emerald-400 ring-2 ring-emerald-200' : 'border-zinc-200'"
          data-pool-drop="ALGO"
        >
          <div class="p-4 border-b border-zinc-100">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">自有人力</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ algoSlots.length }}
              </span>
            </div>
          </div>

          <div class="p-4">
            <div class="flex flex-wrap gap-2">
              <div
                v-for="slot in algoSlots"
                :key="slot.id"
                class="select-none"
                @pointerdown.prevent="startAssignDrag($event, slot.id)"
              >
                <SlotChip :slot="slot" show-percentage :draggable="true" />
              </div>
              <div v-if="algoSlots.length === 0" class="text-sm text-zinc-400">
                暂无自有人力
              </div>
            </div>
          </div>
        </div>

        <!-- External Slots -->
        <div
          class="bg-white rounded-xl border overflow-hidden transition-all"
          :class="poolHover === 'EXTERNAL' ? 'border-emerald-400 ring-2 ring-emerald-200' : 'border-zinc-200'"
          data-pool-drop="EXTERNAL"
        >
          <div class="p-4 border-b border-zinc-100">
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-zinc-900">协调人力</h2>
              <span class="px-2 py-0.5 bg-zinc-100 rounded-full text-xs font-medium text-zinc-600">
                {{ externalSlots.length }}
              </span>
            </div>
          </div>

          <div class="p-4">
            <div class="flex flex-wrap gap-2">
              <div
                v-for="slot in externalSlots"
                :key="slot.id"
                class="select-none"
                @pointerdown.prevent="startAssignDrag($event, slot.id)"
              >
                <SlotChip :slot="slot" show-percentage :draggable="true" />
              </div>
              <div v-if="externalSlots.length === 0" class="text-sm text-zinc-400">
                暂无协调人力
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="bg-white rounded-xl border border-zinc-200 p-4">
          <h3 class="font-semibold text-zinc-900 mb-4">快速统计</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">进行中课题</span>
              <span class="font-semibold text-zinc-900">{{ openTopicsCount }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">已完成</span>
              <span class="font-semibold text-emerald-600">{{ completedTopicsCount }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-zinc-600">无法解决</span>
              <span class="font-semibold text-rose-600">{{ unsolvableTopicsCount }}</span>
            </div>
          </div>
        </div>
      </div>
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

import type { Topic, Binding } from '@/types';

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

// Helper to check if user is DRI of a topic
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
  ghostEl.style.position = 'fixed';
  ghostEl.style.left = `${x + 12}px`;
  ghostEl.style.top = `${y + 12}px`;
  ghostEl.style.zIndex = '99999';
  ghostEl.style.pointerEvents = 'none';
  ghostEl.style.padding = '6px 10px';
  ghostEl.style.borderRadius = '9999px';
  ghostEl.style.background = 'rgba(255,255,255,0.92)';
  ghostEl.style.border = '1px solid rgba(0,0,0,0.08)';
  ghostEl.style.boxShadow = '0 6px 18px rgba(0,0,0,0.12)';
  ghostEl.style.fontSize = '12px';
  ghostEl.style.color = '#3f3f46';
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
  const inside =
    x >= rect.left && x <= rect.right &&
    y >= rect.top && y <= rect.bottom;
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

/** Release: Binding -> Pool */
function startReleaseDrag(payload: { e: PointerEvent; binding: any }) {
  const e = payload.e;
  if (e.button !== 0) return;

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
  for (const t of topicsStore.topics) {
    const b = t.bindings?.find((x: any) => x.id === bindingId);
    if (b) {
      return {
        ...b,
        topicId: b.topicId ?? t.id,
        slotId: b.slotId,
      };
    }
  }
  return null;
}

function findAllBindingIdsInSameTopicAndSlot(bindingId: number): number[] {
  for (const t of topicsStore.topics) {
    const target = t.bindings?.find((x: any) => x.id === bindingId);
    if (!target) continue;
    const slotId = target.slotId;
    return (t.bindings || []).filter((x: any) => x.slotId === slotId).map((x: any) => x.id);
  }
  return [];
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

  const binding = findBindingInLocalState(bindingId);
  if (!binding) {
    await capacityStore.deleteBinding(bindingId);
    await Promise.all([topicsStore.fetchTopics(), capacityStore.fetchSlots()]);
    return;
  }

  const ids = findAllBindingIdsInSameTopicAndSlot(bindingId);
  if (!ids.length) return;

  const snapshot: any[] = [];
  {
    const t = topicsStore.topics.find((x: any) => x.id === binding.topicId);
    if (t?.bindings?.length) {
      for (const id of ids) {
        const b = t.bindings.find((x: any) => x.id === id);
        if (b) snapshot.push({ ...b, topicId: b.topicId ?? t.id });
      }
    }
  }

  for (const id of ids) {
    topicsStore.removeBindingLocal(id);
    capacityStore.removeBindingLocal(id);
  }

  try {
    await Promise.all(ids.map((id) => capacityStore.deleteBinding(id)));
    ElMessage.success('已释放');
  } catch (e) {
    for (const b of snapshot) {
      topicsStore.addBindingLocal(b.topicId, b);
      capacityStore.addBindingLocal(b.slotId, b);
    }
    ElMessage.error('释放失败，已回滚');
  }
}

onMounted(() => {
  topicsStore.fetchTopics();
  capacityStore.fetchSlots();
});
</script>
