<template>
  <div
    class="p-3 bg-white rounded-lg border border-zinc-200 hover:border-zinc-300 hover:shadow-sm transition-all cursor-pointer"
    :data-topic-drop="props.topic.id"
    @click="emit('open', props.topic)"
  >
    <div class="flex items-center gap-4">
      <!-- Title + Urgency -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h4 class="font-medium text-zinc-900 truncate">{{ props.topic.title }}</h4>
          <el-tag :type="urgencyType" size="small" class="flex-shrink-0">
            {{ props.topic.urgency }}
          </el-tag>
        </div>
        <p class="text-xs text-zinc-500 mt-0.5 truncate">
          编号: {{ props.topic.id }}
          <span v-if="requesterName" class="ml-2">• 需求方: {{ requesterName }}</span>
        </p>
      </div>

      <!-- Stage Timeline (stop click open) -->
      <div class="flex-shrink-0" @click.stop>
        <StageTimeline
          :stages="stages"
          :stage-states="stageStates"
          :current-stage-id="currentStageId"
          compact
        />
      </div>

      <!-- Result -->
      <el-tag :type="resultType" size="small" class="flex-shrink-0">
        {{ resultLabel }}
      </el-tag>

      <el-button size="small" @click.stop="emit('open', props.topic)">打开</el-button>
    </div>

    <!-- Bindings row: DRI first with special mark, then others -->
    <div v-if="sortedBindings.length" class="mt-2 flex flex-wrap gap-2" @click.stop>
      <div
        v-for="b in sortedBindings"
        :key="b.id"
        class="select-none"
        @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
      >
        <!-- DRI binding with special styling -->
        <div v-if="b.isDri" class="relative">
          <SlotChip
            :slot="resolveSlot(b)"
            :binding-percentage="b.percentage"
            show-percentage
            class="ring-2 ring-blue-400 ring-offset-1"
          />
          <span class="absolute -top-1.5 -right-1.5 px-1 py-0.5 bg-blue-500 text-white text-[10px] font-bold rounded">
            DRI
          </span>
        </div>
        <!-- Normal binding -->
        <SlotChip
          v-else
          :slot="resolveSlot(b)"
          :binding-percentage="b.percentage"
          show-percentage
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Topic, Binding } from '@/types';
import StageTimeline from './StageTimeline.vue';
import SlotChip from '@/components/common/SlotChip.vue';
import { useCapacityStore } from '@/stores/capacity';

const props = defineProps<{ topic: Topic }>();

const emit = defineEmits<{
  (e: 'open', topic: Topic): void;
  (e: 'binding-pointerdown', payload: { e: PointerEvent; binding: any }): void;
}>();

const capacityStore = useCapacityStore();

const urgencyType = computed(() => {
  switch (props.topic.urgency) {
    case 'P0': return 'danger';
    case 'P1': return 'warning';
    case 'P2': return 'info';
    default: return 'info';
  }
});

const resultType = computed(() => {
  switch (props.topic.result) {
    case 'SUCCESS': return 'success';
    case 'UNSOLVABLE': return 'danger';
    default: return '';
  }
});

const resultLabel = computed(() => {
  switch (props.topic.result) {
    case 'SUCCESS': return '已完成';
    case 'UNSOLVABLE': return '无法解决';
    case 'OPEN': return '进行中';
    default: return props.topic.result;
  }
});

const requesterName = computed(() => {
  const t: any = props.topic;
  return t?.requesterName ?? t?.requester_name ?? '';
});

/** Stage 字段兼容：camel + snake */
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

/**
 * Bindings: normalize and sort (DRI first, then others by percentage desc)
 */
const sortedBindings = computed(() => {
  const t: any = props.topic;
  const arr = (t?.bindings ?? t?.capacity_bindings ?? []) as any[];

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

  // Sort: DRI first, then by percentage descending
  return out.sort((a, b) => {
    if (a.isDri && !b.isDri) return -1;
    if (!a.isDri && b.isDri) return 1;
    return (b.percentage || 0) - (a.percentage || 0);
  });
});

/**
 * SlotChip 用 capacityStore 的 slot（带 bindings，used/remaining 才准）
 * 找不到才退回 b.slot（不至于空）
 */
function resolveSlot(b: any) {
  const sid = Number(b.slotId ?? b.slot_id ?? b.slot?.id);
  return capacityStore.slots.find(s => s.id === sid) ?? b.slot;
}
</script>
