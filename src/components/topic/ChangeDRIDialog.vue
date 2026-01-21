<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="更换负责人 (DRI)"
    width="550px"
  >
    <p class="text-sm text-zinc-600 mb-4">
      选择新的课题负责人。可以从已分配的团队成员中选择，或者添加新人员。
    </p>

    <!-- Current DRI -->
    <div v-if="currentDriBinding" class="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
      <p class="text-xs text-blue-600 font-medium mb-2">当前负责人</p>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-semibold text-blue-600">
          {{ getInitials(currentDriBinding.slot?.name) }}
        </div>
        <div>
          <p class="font-medium text-zinc-900">{{ currentDriBinding.slot?.name }}</p>
          <p class="text-xs text-zinc-500">{{ currentDriBinding.percentage }}% 已分配</p>
        </div>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="新负责人" prop="newDriSlotId">
        <el-select v-model="form.newDriSlotId" class="w-full" filterable placeholder="选择人员">
          <!-- Existing bindings first -->
          <el-option-group v-if="existingBindingOptions.length" label="已分配团队成员">
            <el-option
              v-for="binding in existingBindingOptions"
              :key="binding.slotId"
              :value="binding.slotId"
              :label="binding.slot?.name"
              :disabled="binding.isDri"
            >
              <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2">
                  <span>{{ binding.slot?.name }}</span>
                  <el-tag size="small" :type="binding.slot?.type === 'EXTERNAL' ? 'info' : 'success'">
                    {{ slotTypeLabel(binding.slot?.type) }}
                  </el-tag>
                </div>
                <span v-if="binding.isDri" class="text-xs text-zinc-400">(当前DRI)</span>
                <span v-else class="text-xs text-zinc-400">{{ binding.percentage }}%</span>
              </div>
            </el-option>
          </el-option-group>
          
          <!-- Available slots that are not bound yet -->
          <el-option-group v-if="availableSlots.length" label="添加新人员">
            <el-option
              v-for="slot in availableSlots"
              :key="slot.id"
              :value="slot.id"
              :label="slot.name"
            >
              <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2">
                  <span>{{ slot.name }}</span>
                  <el-tag size="small" :type="slot.type === 'EXTERNAL' ? 'info' : 'success'">
                    {{ slotTypeLabel(slot.type) }}
                  </el-tag>
                </div>
                <span class="text-xs text-zinc-400">{{ getSlotUsage(slot) }}% 已用</span>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确认更换
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { useCapacityStore } from '@/stores/capacity';
import { useTopicsStore } from '@/stores/topics';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import type { Topic, Binding, CapacitySlot } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  topic: Topic | null;
  bindings?: Binding[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'changed'): void;
}>();

const capacityStore = useCapacityStore();
const topicsStore = useTopicsStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  newDriSlotId: undefined as number | undefined,
});

const rules: FormRules = {
  newDriSlotId: [{ required: true, message: '请选择新负责人', trigger: 'change' }],
};

// Current DRI binding
const currentDriBinding = computed(() => {
  return props.bindings?.find(b => b.isDri) || null;
});

// Existing bindings as options
const existingBindingOptions = computed(() => {
  return props.bindings || [];
});

// Available slots that are not yet bound to this topic
const boundSlotIds = computed(() => {
  return new Set(props.bindings?.map(b => b.slotId) || []);
});

const availableSlots = computed(() => {
  return capacityStore.slots.filter(s => !boundSlotIds.value.has(s.id));
});

function getSlotUsage(slot: CapacitySlot): number {
  return slot.bindings?.reduce((sum, b) => sum + (b.percentage || 0), 0) || 0;
}

function slotTypeLabel(type?: string): string {
  return type === 'EXTERNAL' ? '协调人力' : '自有人力';
}

function getInitials(name?: string) {
  if (!name) return '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

watch(() => props.modelValue, (open) => {
  if (open) {
    capacityStore.fetchSlots();
    form.newDriSlotId = undefined;
  }
});

async function handleSubmit() {
  if (!formRef.value || !props.topic || !form.newDriSlotId) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await topicsStore.changeDri(props.topic!.id, { newDriSlotId: form.newDriSlotId! });
      ElMessage.success('负责人已更换');
      emit('update:modelValue', false);
      emit('changed');
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '更换失败');
    } finally {
      loading.value = false;
    }
  });
}
</script>
