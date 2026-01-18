<template>
  <div class="flex items-center gap-1">
    <template v-for="(stage, index) in stages" :key="stage.id">
      <el-tooltip :content="getStageTooltip(stage)" placement="top">
        <div
          :class="[
            'flex items-center justify-center rounded transition-all cursor-pointer',
            compact ? 'h-6 px-2 text-xs' : 'h-8 px-3 text-sm',
            getStageClass(stage)
          ]"
          @click="$emit('stage-click', stage)"
        >
          <span v-if="!compact" class="font-medium truncate max-w-[80px]">{{ stage.name }}</span>
          <span v-else class="font-medium">{{ getStageAbbr(stage.name) }}</span>

          <el-icon v-if="isStageCompleted(stage)" class="ml-1" :size="compact ? 12 : 14">
            <Check />
          </el-icon>
        </div>
      </el-tooltip>

      <div
        v-if="index < stages.length - 1"
        :class="[
          'flex-shrink-0',
          compact ? 'w-2' : 'w-4',
          'h-0.5',
          index < currentStageIndex ? 'bg-zinc-900' : 'bg-zinc-200'
        ]"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Check } from '@element-plus/icons-vue';
import type { StageTemplateStage, TopicStageState } from '@/types';

const props = defineProps<{
  stages: StageTemplateStage[];
  stageStates?: TopicStageState[];
  currentStageId?: number;
  compact?: boolean;
}>();

defineEmits<{
  (e: 'stage-click', stage: StageTemplateStage): void;
}>();

/** 兼容后端 snake_case / 前端 camelCase */
function getStageIdFromState(ss: any): number | undefined {
  return ss?.stageId ?? ss?.stage_id;
}
function getStatusFromState(ss: any): string | undefined {
  return ss?.status;
}

const currentStageIndex = computed(() => {
  if (!props.currentStageId) return -1;
  return props.stages.findIndex(s => s.id === props.currentStageId);
});

function getStageState(stage: StageTemplateStage): TopicStageState | undefined {
  return props.stageStates?.find((ss: any) => getStageIdFromState(ss) === stage.id);
}

function isStageCompleted(stage: StageTemplateStage): boolean {
  const ss: any = getStageState(stage);
  const status = (getStatusFromState(ss) || '').toLowerCase();

  // 兼容多种后端命名：done / completed / finished / closed
  if (['done', 'completed', 'finished', 'closed'].includes(status)) return true;

  // 有 completed_at 也当作完成（你后端返回里有 completed_at）
  if (ss && (ss.completedAt || (ss as any).completed_at)) return true;

  // 如果后端没给 stageStates，就用 currentStageId + order 推断
  if (!props.stageStates?.length && props.currentStageId) {
    const idx = props.stages.findIndex(s => s.id === stage.id);
    return idx !== -1 && idx < currentStageIndex.value;
  }

  return false;
}

function isStageActive(stage: StageTemplateStage): boolean {
  const ss: any = getStageState(stage);
  const status = (getStatusFromState(ss) || '').toLowerCase();

  if (status === 'active' || status === 'current') return true;
  return stage.id === props.currentStageId;
}

function getStageClass(stage: StageTemplateStage): string {
  if (isStageCompleted(stage)) {
    return 'bg-emerald-600 text-white';
  }
  if (isStageActive(stage)) {
    return 'bg-blue-600 text-white ring-2 ring-blue-300 ring-offset-1';
  }
  return 'bg-zinc-100 text-zinc-500';
}

function getStageTooltip(stage: StageTemplateStage): string {
  const ss: any = getStageState(stage);
  const statusRaw = (getStatusFromState(ss) || '').toLowerCase();

  let statusLabel = 'Pending';
  if (isStageCompleted(stage)) statusLabel = 'Completed';
  else if (isStageActive(stage)) statusLabel = 'Active';
  else if (statusRaw) statusLabel = statusRaw;

  return `${stage.name}: ${statusLabel}${stage.isTerminal ? ' (Terminal)' : ''}`;
}

function getStageAbbr(name: string): string {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 3);
}
</script>
