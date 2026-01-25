<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="添加人力分配"
    width="500px"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="人员" prop="slotId">
        <el-select v-model="form.slotId" class="w-full" filterable placeholder="选择人员">
          <el-option-group label="自有人力">
            <el-option
              v-for="slot in algoSlots"
              :key="slot.id"
              :value="slot.id"
              :label="slot.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ slot.name }}</span>
                <span class="text-xs text-zinc-400">剩{{ getSlotRemaining(slot) }}%</span>
              </div>
            </el-option>
          </el-option-group>

          <el-option-group label="协调人力">
            <el-option
              v-for="slot in externalSlots"
              :key="slot.id"
              :value="slot.id"
              :label="slot.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ slot.name }}</span>
                <span class="text-xs text-zinc-400">剩{{ getSlotRemaining(slot) }}%</span>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="分配比例 (%)" prop="percentage">
        <el-slider v-model="form.percentage" :min="5" :max="100" :step="5" show-input />
      </el-form-item>

      <el-form-item v-if="authStore.isAdmin">
        <el-checkbox v-model="form.isForced">强制分配（忽略容量限制）</el-checkbox>
        <p class="text-xs text-zinc-400 mt-1">强制分配会记录在操作日志中</p>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确认分配
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
  slotId: [{ required: true, message: '请选择人员', trigger: 'change' }],
  percentage: [{ required: true, message: '请设置分配比例', trigger: 'change' }],
};

const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

function getSlotUsage(slot: CapacitySlot) {
  return capacityStore.getSlotUsage(slot);
}

function getSlotRemaining(slot: CapacitySlot) {
  const usage = getSlotUsage(slot);
  const total = slot.totalCapacity || 100;
  return Math.max(0, total - usage);
}

/**
 * 在本地 state 里找"同 topic + 同 user"的已有 binding
 */
function findExistingBinding(topicId: number, userId: number): any | null {
  const ct: any = topicsStore.currentTopic;
  if (ct?.id === topicId && Array.isArray(ct.bindings)) {
    return ct.bindings.find((b: any) => (b.userId ?? b.user_id ?? b.slotId ?? b.slot_id) === userId) || null;
  }

  const t: any = topicsStore.topics.find((x: any) => x.id === topicId);
  if (t?.bindings?.length) {
    return t.bindings.find((b: any) => (b.userId ?? b.user_id ?? b.slotId ?? b.slot_id) === userId) || null;
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
    const userId = form.slotId!;  // 现在 slotId 实际上是 userId
    const pct = Number(form.percentage);

    loading.value = true;
    try {
      const existing = findExistingBinding(topicId, userId);

      if (existing) {
        // 已存在：更新（累加）
        const newPct = Math.min(100, Number(existing.percentage || 0) + pct);
        await capacityStore.updateBinding(existing.id, {
          percentage: newPct,
          isForced: form.isForced,
        });
        ElMessage.success('分配已更新');
      } else {
        // 不存在：创建 - 使用 userId
        await capacityStore.createBinding({
          topicId,
          userId,  // 使用新的 userId 字段
          percentage: pct,
          isForced: form.isForced,
        });
        ElMessage.success('分配成功');
      }

      emit('update:modelValue', false);
      emit('created');
    } catch (error: any) {
      console.error('Binding error:', error);
      ElMessage.error(error.response?.data?.detail || '分配失败');
    } finally {
      loading.value = false;
    }
  });
}
</script>
