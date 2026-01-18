<template>
  <el-tooltip :content="tooltipContent" placement="top">
    <div
      :class="[
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors cursor-default',
        isExternal
          ? 'bg-zinc-100 text-zinc-500 border border-dashed border-zinc-300'
          : 'bg-zinc-100 text-zinc-700'
      ]"
    >
      <span
        :class="[
          'w-2 h-2 rounded-full',
          statusColor,
          isExternal ? 'border border-dashed border-current' : ''
        ]"
      />
      <span :class="isExternal ? 'opacity-70' : ''">{{ slot.name }}</span>
      <span v-if="showPercentage" class="text-xs text-zinc-400">{{ usagePercentage }}%</span>
    </div>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CapacitySlot } from '@/types';

const props = defineProps<{
  slot: CapacitySlot;
  showPercentage?: boolean;
  bindingPercentage?: number;
}>();

const isExternal = computed(() => props.slot.type === 'EXTERNAL');

const usagePercentage = computed(() => {
  if (props.bindingPercentage !== undefined) {
    return props.bindingPercentage;
  }
  return props.slot.bindings?.reduce((sum, b) => sum + b.percentage, 0) || 0;
});

const status = computed(() => {
  const usage = usagePercentage.value;
  if (usage === 0) return 'available';
  if (usage >= 100) return 'occupied';
  return 'partial';
});

const statusColor = computed(() => {
  switch (status.value) {
    case 'available': return 'bg-emerald-500';
    case 'partial': return 'bg-amber-500';
    case 'occupied': return 'bg-rose-500';
    default: return 'bg-zinc-400';
  }
});

const tooltipContent = computed(() => {
  const lines = [
    `Type: ${props.slot.type}`,
    `Usage: ${usagePercentage.value}%`,
  ];

  if (props.slot.bindings?.length) {
    lines.push(`Bound Topics: ${props.slot.bindings.length}`);
  }

  if (isExternal.value) {
    lines.push('External cannot be DRI');
  }

  return lines.join(' | ');
});
</script>
