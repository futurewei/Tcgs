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

function bindingSlotId(b: any): number | undefined {
  return b.slotId ?? b.slot_id ?? b.slot?.id;
}

function findExistingBinding(
  topicId: number,
  key: { slotId?: number; userId?: number; pickedId: number }
) {
  // 这里按你项目里真实获取 topic/bindings 的方式调整：
  const topic = topicsStore.topics?.find((t: any) => Number(t.id) === Number(topicId));
  const bindings = topic?.bindings || [];

  return (
    bindings.find((b: any) => {
      // 兼容各种字段名
      const bSlotId = b.slotId ?? b.slot_id ?? b.slot?.id;
      const bUserId =
        b.userId ??
        b.user_id ??
        b.user?.id ??
        b.slot?.userId ??
        b.slot?.user?.id;

      // 命中任意一种就算同一个人/同一个slot
      return (
        (key.slotId != null && Number(bSlotId) === Number(key.slotId)) ||
        (key.userId != null && Number(bUserId) === Number(key.userId)) ||
        Number(bSlotId) === Number(key.pickedId) ||
        Number(bUserId) === Number(key.pickedId)
      );
    }) || null
  );
}


function bindingUserId(b: any): number | undefined {
  return b.userId ?? b.user_id ?? b.user?.id;
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
    const slotId = Number(form.slotId);          // ✅ 现在 slotId 就是 CapacitySlot.id
    const pct = Number(form.percentage);

    loading.value = true;
    try {
      const existing = findExistingBinding(topicId, slotId);

      if (existing) {
        const newPct = Math.min(100, Number(existing.percentage || 0) + pct);
        await capacityStore.updateBinding(existing.id, {
          percentage: newPct,
          isForced: form.isForced,
        });
        ElMessage.success('分配已更新');
      } else {
        await capacityStore.createBinding({
          topicId,
          slotId,                    // ✅ 真 slotId
          percentage: pct,
          isForced: form.isForced,
        });
        ElMessage.success('分配成功');
      }

      emit('update:modelValue', false);
      emit('created');               // TopicDetailView 会 refreshTopic()
    } catch (error: any) {
      console.error('Binding error:', error);
      ElMessage.error(error.response?.data?.detail || '分配失败');
    } finally {
      loading.value = false;
    }
  });
}

</script>
