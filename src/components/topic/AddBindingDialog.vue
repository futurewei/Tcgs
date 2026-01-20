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
        <p class="text-xs text-zinc-400 mt-1">Force binding will be logged in audit trail</p>
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
import { useTopicsStore } from '@/stores/topics';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import type { CapacitySlot } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  topicId: number;
  initialSlotId?: number;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'created'): void;
}>();

const capacityStore = useCapacityStore();
const topicsStore = useTopicsStore();
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

/**
 * ✅ 在本地 state 里找“同 topic + 同 slot”的已有 binding
 * 优先 currentTopic（详情页最准），没有就退化到 topics 列表
 */
function findExistingBinding(topicId: number, slotId: number): any | null {
  const ct: any = topicsStore.currentTopic;
  if (ct?.id === topicId && Array.isArray(ct.bindings)) {
    return ct.bindings.find((b: any) => b.slotId === slotId) || null;
  }

  const t: any = topicsStore.topics.find((x: any) => x.id === topicId);
  if (t?.bindings?.length) {
    return t.bindings.find((b: any) => b.slotId === slotId) || null;
  }

  return null;
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return;

    capacityStore.fetchSlots();

    form.percentage = 25;
    form.isForced = false;

    if (props.initialSlotId) form.slotId = props.initialSlotId;
    else form.slotId = undefined;
  }
);

async function handleSubmit() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    const topicId = props.topicId;
    const slotId = form.slotId!;
    const pct = Number(form.percentage);

    loading.value = true;
    try {
      const existing = findExistingBinding(topicId, slotId);

      if (existing) {
        // ✅ 已存在：改成 update，默认“累加”并 clamp 到 100
        // 如果你要“覆盖”，把 newPct 改成 pct 就行
        const newPct = Math.min(100, Number(existing.percentage || 0) + pct);

        // 需要 capacityStore.updateBinding
        await capacityStore.updateBinding(existing.id, {
          percentage: newPct,
          isForced: form.isForced,
        });

        ElMessage.success('Binding updated');
      } else {
        // ✅ 不存在：正常创建
        await capacityStore.createBinding({
          topicId,
          slotId,
          percentage: pct,
          isForced: form.isForced,
        });
        ElMessage.success('Binding created');
      }

      emit('update:modelValue', false);
      emit('created');
    } catch (error) {
      ElMessage.error('Failed to save binding');
    } finally {
      loading.value = false;
    }
  });
}
</script>
