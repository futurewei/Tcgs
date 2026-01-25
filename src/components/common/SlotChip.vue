<template>
  <el-tooltip :content="tooltipContent" placement="top">
    <component
      :is="clickable ? 'router-link' : 'div'"
      :to="clickable ? profileLink : undefined"
      :class="[
        'slot-chip',
        isExternal ? 'slot-chip--external' : 'slot-chip--internal',
        clickable && 'slot-chip--clickable',
        draggable && 'slot-chip--draggable'
      ]"
      @click.stop
    >
      <span :class="['slot-dot', `slot-dot--${status}`]" />
      <span class="slot-name">{{ slot.name }}</span>
      <span v-if="showPercentage && !hideRemaining" class="slot-remaining">
        剩{{ remainingPercentage }}%
      </span>
    </component>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CapacitySlot } from '@/types';

const props = defineProps<{
  slot: CapacitySlot;
  showPercentage?: boolean;
  bindingPercentage?: number;
  hideRemaining?: boolean;
  clickable?: boolean;
  draggable?: boolean;
}>();

const isExternal = computed(() => props.slot.type === 'EXTERNAL');

const profileLink = computed(() => {
  if (props.slot.userId) {
    return `/profile/user/${props.slot.userId}`;
  }
  return `/profile/slot/${props.slot.id}`;
});

const usagePercentage = computed(() => {
  if (props.bindingPercentage !== undefined) return props.bindingPercentage;
  return props.slot.bindings?.reduce((sum, b) => sum + b.percentage, 0) || 0;
});

const totalCapacity = computed(() => props.slot.totalCapacity || 100);

const remainingPercentage = computed(() => {
  return Math.max(0, totalCapacity.value - usagePercentage.value);
});

const status = computed(() => {
  const remaining = remainingPercentage.value;
  if (remaining >= totalCapacity.value) return 'available';
  if (remaining <= 0) return 'occupied';
  return 'partial';
});

const tooltipContent = computed(() => {
  const typeLabel = props.slot.type === 'EXTERNAL' ? '协调人力' : '自有人力';
  const lines = [
    `类型: ${typeLabel}`,
    `剩余: ${remainingPercentage.value}%`,
  ];
  if (props.slot.bindings?.length) lines.push(`已绑定课题: ${props.slot.bindings.length}`);
  if (props.clickable) lines.push('点击查看档案');
  return lines.join(' | ');
});
</script>

<style scoped>
.slot-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1-5) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
  user-select: none;
}

/* Internal - 更强调 */
.slot-chip--internal {
  background: var(--color-neutral-100);
  color: var(--color-text-primary);
}

.slot-chip--internal:hover {
  background: var(--color-neutral-150);
}

/* External - 低权重（虚线边框） */
.slot-chip--external {
  background: transparent;
  color: var(--color-text-tertiary);
  border: 1px dashed var(--color-border-strong);
}

.slot-chip--external:hover {
  background: var(--color-neutral-50);
  color: var(--color-text-secondary);
}

.slot-chip--clickable {
  cursor: pointer;
}

.slot-chip--clickable:hover {
  box-shadow: 0 0 0 2px var(--color-primary-200);
}

.slot-chip--draggable {
  cursor: grab;
}

.slot-chip--draggable:active {
  cursor: grabbing;
}

/* Status Dot */
.slot-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.slot-dot--available {
  background: var(--color-success);
}

.slot-dot--partial {
  background: var(--color-warning);
}

.slot-dot--occupied {
  background: var(--color-danger);
}

.slot-name {
  white-space: nowrap;
}

.slot-remaining {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-normal);
}
</style>
