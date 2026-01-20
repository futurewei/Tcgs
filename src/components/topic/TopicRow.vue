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
          ID: {{ props.topic.id }}
          <span v-if="requesterName" class="ml-2">• Requester: {{ requesterName }}</span>
        </p>
      </div>

      <!-- DRI -->
      <div class="flex items-center gap-2 flex-shrink-0">
        <div
          class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs font-medium text-zinc-600"
        >
          {{ driInitials }}
        </div>
        <span class="text-sm text-zinc-600 max-w-[110px] truncate">{{ driName }}</span>
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
        {{ props.topic.result }}
      </el-tag>

      <el-button size="small" @click.stop="emit('open', props.topic)">Open</el-button>
    </div>

    <!-- ✅ Bindings row (dedup by slotId, and use capacityStore slot so tooltip used/remaining is correct) -->
    <div v-if="uniqueBindings.length" class="mt-2 flex flex-wrap gap-2" @click.stop>
      <div
        v-for="b in uniqueBindings"
        :key="b.id"
        class="select-none"
        @pointerdown.stop.prevent="emit('binding-pointerdown', { e: $event, binding: b })"
      >
        <SlotChip
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
import type { Topic } from '@/types';
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

const requesterName = computed(() => {
  const t: any = props.topic;
  return t?.requesterName ?? t?.requester_name ?? '';
});

/** ✅ DRI 兼容 */
const driName = computed(() => {
  const t: any = props.topic;
  return t?.dri?.name ?? t?.driName ?? t?.dri_name ?? '';
});

const driInitials = computed(() => {
  const name = driName.value || '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
});

/** ✅ Stage 字段兼容：camel + snake */
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
 * ✅ bindings 兼容：bindings / capacity_bindings
 * ✅ 去重：同 slotId 只显示一次（兜底防重复）
 */
const uniqueBindings = computed(() => {
  const t: any = props.topic;
  const arr = (t?.bindings ?? t?.capacity_bindings ?? []) as any[];

  const seen = new Set<number>();
  const out: any[] = [];

  for (const b of arr) {
    const sid = Number(b.slotId ?? b.slot_id ?? b.slot?.id);
    if (!sid) continue;
    if (seen.has(sid)) continue;
    seen.add(sid);

    // 保证 slotId 字段存在，Dashboard release 逻辑需要
    out.push({
      ...b,
      slotId: b.slotId ?? b.slot_id ?? b.slot?.id,
      topicId: b.topicId ?? b.topic_id ?? t?.id,
    });
  }
  return out;
});

/**
 * ✅ SlotChip 用 capacityStore 的 slot（带 bindings，used/remaining 才准）
 * 找不到才退回 b.slot（不至于空）
 */
function resolveSlot(b: any) {
  const sid = Number(b.slotId ?? b.slot_id ?? b.slot?.id);
  return capacityStore.slots.find(s => s.id === sid) ?? b.slot;
}
</script>
