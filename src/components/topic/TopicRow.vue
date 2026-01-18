<template>
  <div
    class="flex items-center gap-4 p-3 bg-white rounded-lg border border-zinc-200 hover:border-zinc-300 hover:shadow-sm transition-all cursor-pointer"
    @click="emit('open', props.topic)"
  >
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
        <span v-if="requesterName" class="ml-2">
          • Requester: {{ requesterName }}
        </span>
      </p>
    </div>

    <!-- DRI -->
    <div class="flex items-center gap-2 flex-shrink-0">
      <div class="w-6 h-6 bg-zinc-200 rounded-full flex items-center justify-center text-xs font-medium text-zinc-600">
        {{ driInitials }}
      </div>
      <span class="text-sm text-zinc-600 max-w-[80px] truncate">{{ props.topic.dri?.name }}</span>
    </div>

    <!-- Stage Timeline (不要触发 open，避免误点跳转) -->
    <div class="flex-shrink-0" @click.stop>
      <StageTimeline
        :stages="props.topic.template?.stages || []"
        :stage-states="props.topic.stageStates"
        :current-stage-id="props.topic.currentStageId"
        compact
      />
    </div>

    <!-- Result Badge -->
    <el-tag :type="resultType" size="small" class="flex-shrink-0">
      {{ props.topic.result }}
    </el-tag>

    <!-- Open Button -->
    <el-button size="small" @click.stop="emit('open', props.topic)">
      Open
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Topic } from '@/types';
import StageTimeline from './StageTimeline.vue';

const props = defineProps<{ topic: Topic }>();

const emit = defineEmits<{
  (e: 'open', topic: Topic): void;
}>();

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

const driInitials = computed(() => {
  const name = props.topic.dri?.name || '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
});

const requesterName = computed(() => {
  const t: any = props.topic;
  return t?.requesterName ?? t?.requester_name ?? '';
});
</script>
