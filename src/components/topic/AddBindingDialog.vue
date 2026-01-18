<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="Add Capacity Binding"
    width="500px"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Slot" prop="slotId">
        <el-select v-model="form.slotId" class="w-full" filterable>
          <el-option-group label="Algo Slots">
            <el-option
              v-for="slot in algoSlots"
              :key="slot.id"
              :value="slot.id"
              :label="slot.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ slot.name }}</span>
                <span class="text-xs text-zinc-400">{{ getSlotUsage(slot) }}% used</span>
              </div>
            </el-option>
          </el-option-group>
          <el-option-group label="External Slots">
            <el-option
              v-for="slot in externalSlots"
              :key="slot.id"
              :value="slot.id"
              :label="slot.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ slot.name }}</span>
                <span class="text-xs text-zinc-400">{{ getSlotUsage(slot) }}% used</span>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="Percentage" prop="percentage">
        <el-slider v-model="form.percentage" :min="5" :max="100" :step="5" show-input />
      </el-form-item>

      <el-form-item v-if="authStore.isAdmin">
        <el-checkbox v-model="form.isForced">Force binding (override capacity limits)</el-checkbox>
        <p class="text-xs text-zinc-400 mt-1">
          Force binding will be logged in audit trail
        </p>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        Add Binding
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { useCapacityStore } from '@/stores/capacity';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import type { CapacitySlot } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  topicId: number;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'created'): void;
}>();

const capacityStore = useCapacityStore();
const authStore = useAuthStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  slotId: undefined as number | undefined,
  percentage: 25,
  isForced: false,
});

const rules: FormRules = {
  slotId: [{ required: true, message: 'Please select slot', trigger: 'change' }],
  percentage: [{ required: true, message: 'Please set percentage', trigger: 'change' }],
};

const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

function getSlotUsage(slot: CapacitySlot) {
  return capacityStore.getSlotUsage(slot);
}

watch(() => props.modelValue, (open) => {
  if (open) {
    capacityStore.fetchSlots();
    form.slotId = undefined;
    form.percentage = 25;
    form.isForced = false;
  }
});

async function handleSubmit() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await capacityStore.createBinding({
        topicId: props.topicId,
        slotId: form.slotId!,
        percentage: form.percentage,
        isForced: form.isForced,
      });

      ElMessage.success('Binding created');
      emit('update:modelValue', false);
      emit('created');
    } catch (error) {
      ElMessage.error('Failed to create binding');
    } finally {
      loading.value = false;
    }
  });
}
</script>
