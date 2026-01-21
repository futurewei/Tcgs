<template>
  <div class="flex items-center gap-1">
    <template v-for="(stage, index) in stages" :key="stage.id">
      <el-tooltip :content="getStageTooltip(stage)" placement="top">
        <div
          :class="[
            'flex items-center justify-center rounded-lg transition-all cursor-pointer',
            compact ? 'h-7 px-2.5 text-xs' : 'h-9 px-4 text-sm',
            getStageClass(stage)
          ]"
          @click="$emit('stage-click', stage)"
        >
          <!-- Status indicator -->
          <span
            v-if="!compact && !isStageCompleted(stage)"
            :class="[
              'w-2 h-2 rounded-full mr-2 flex-shrink-0',
              isStageActive(stage) ? 'bg-white animate-pulse' : 'bg-current opacity-40'
            ]"
          />
          
          <span v-if="!compact" class="font-medium truncate max-w-[100px]">{{ stage.name }}</span>
          <span v-else class="font-medium">{{ getStageAbbr(stage.name) }}</span>

          <el-icon v-if="isStageCompleted(stage)" class="ml-1.5 flex-shrink-0" :size="compact ? 12 : 14">
            <Check />
          </el-icon>
          
          <!-- Terminal stage indicator -->
          <el-icon v-if="!compact && stage.isTerminal && !isStageCompleted(stage)" class="ml-1 flex-shrink-0 opacity-60" :size="12">
            <Flag />
          </el-icon>
        </div>
      </el-tooltip>

      <!-- Connector line -->
      <div
        v-if="index < stages.length - 1"
        :class="[
          'flex-shrink-0 transition-all duration-300',
          compact ? 'w-3' : 'w-6',
          'h-0.5',
          getConnectorClass(index)
        ]"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Check, Flag } from '@element-plus/icons-vue';
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

/** Compatible with backend snake_case / frontend camelCase */
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

  // Compatible with various backend naming: done / completed / finished / closed
  if (['done', 'completed', 'finished', 'closed'].includes(status)) return true;

  // Has completed_at also counts as completed
  if (ss && (ss.completedAt || (ss as any).completed_at)) return true;

  // If backend doesn't provide stageStates, infer from currentStageId + order
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

function isStagePending(stage: StageTemplateStage): boolean {
  return !isStageCompleted(stage) && !isStageActive(stage);
}

function getStageClass(stage: StageTemplateStage): string {
  if (isStageCompleted(stage)) {
    return 'bg-emerald-600 text-white shadow-sm hover:bg-emerald-700';
  }
  if (isStageActive(stage)) {
    return 'bg-blue-600 text-white ring-2 ring-blue-300 ring-offset-1 shadow-md hover:bg-blue-700';
  }
  return 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200';
}

function getConnectorClass(index: number): string {
  // If the stage after this connector is completed or active, the connector is "done"
  const nextStage = props.stages[index + 1];
  if (!nextStage) return 'bg-zinc-200';
  
  if (isStageCompleted(nextStage) || isStageActive(nextStage)) {
    return 'bg-emerald-600';
  }
  
  // If current stage is completed, connector shows progress
  const currentStage = props.stages[index];
  if (isStageCompleted(currentStage)) {
    return 'bg-gradient-to-r from-emerald-600 to-zinc-300';
  }
  
  return 'bg-zinc-200';
}

function getStageTooltip(stage: StageTemplateStage): string {
  const ss: any = getStageState(stage);
  const statusRaw = (getStatusFromState(ss) || '').toLowerCase();

  let statusLabel = 'Pending';
  if (isStageCompleted(stage)) statusLabel = '✅ Completed';
  else if (isStageActive(stage)) statusLabel = '🔄 In Progress';
  else if (statusRaw) statusLabel = statusRaw;

  const lines = [
    `${stage.name}`,
    `Status: ${statusLabel}`,
  ];
  
  if (stage.description) {
    lines.push(`${stage.description}`);
  }
  
  if (stage.isTerminal) {
    lines.push('🏁 Terminal Stage');
  }
  
  if (stage.requireArtifact) {
    lines.push('📎 Requires Deliverable');
  }

  return lines.join('\n');
}

function getStageAbbr(name: string): string {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 3);
}
</script>
