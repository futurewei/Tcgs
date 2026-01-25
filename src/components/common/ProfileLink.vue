<template>
  <router-link
    v-if="userId || slotId"
    :to="linkTo"
    class="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
    :class="customClass"
  >
    <slot>{{ displayName }}</slot>
  </router-link>
  <span v-else :class="customClass">
    <slot>{{ displayName }}</slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  userId?: number | null;
  slotId?: number | null;
  name?: string;
  customClass?: string;
}>();

const displayName = computed(() => props.name || '未知');

const linkTo = computed(() => {
  if (props.userId) {
    return `/profile/user/${props.userId}`;
  }
  if (props.slotId) {
    return `/profile/slot/${props.slotId}`;
  }
  return '#';
});
</script>
