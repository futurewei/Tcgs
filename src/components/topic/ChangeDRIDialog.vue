<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
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
          {{ getInitials(getBindingDisplayName(currentDriBinding)) }}
        </div>
        <div>
          <p class="font-medium text-zinc-900">{{ getBindingDisplayName(currentDriBinding) }}</p>
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
              :key="getBindingSlotId(binding) ?? `${binding.id ?? 'b'}-${binding.slotId ?? binding.slot_id ?? 'x'}`"
              :value="getBindingSlotId(binding) ?? undefined"
              :label="getBindingDisplayName(binding)"
              :disabled="!!(binding.isDri || binding.is_dri) || !getBindingSlotId(binding)"
            >
              <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2">
                  <span>{{ getBindingDisplayName(binding) }}</span>
                  <el-tag size="small" :type="getBindingSlotType(binding) === 'EXTERNAL' ? 'info' : 'success'">
                    {{ slotTypeLabel(getBindingSlotType(binding)) }}
                  </el-tag>
                </div>
                <span v-if="binding.isDri || binding.is_dri" class="text-xs text-zinc-400">(当前DRI)</span>
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
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
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

/**
 * 核心修复点：归一化 binding 的“真实 slotId”
 * 你的报错 new_dri_slot_id=7，实际 7 是 user_id；真正的 slot.id 是 2
 * 所以这里必须优先取 binding.slot.id
 */
function getBindingSlotId(b: any): number | null {
  const raw =
    b?.slot?.id ??         // ✅ 最可信：嵌套 slot 的主键
    b?.slot_id ??          // 兼容 snake_case
    b?.slotId ??           // 兼容 camelCase
    null;

  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function getBindingSlotType(b: any): string | undefined {
  return b?.slot?.type ?? b?.slot_type ?? undefined;
}

function getBindingDisplayName(b: any): string {
  // 优先显示 slot.name（你的人力池/分配卡片都是用 slot.name）
  return b?.slot?.name ?? b?.slotName ?? b?.slot_name ?? '未知';
}

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

// Current DRI binding
const currentDriBinding = computed(() => {
  return props.bindings?.find((b: any) => b.isDri || b.is_dri) || null;
});

// Existing bindings as options（用原始列表，但 value 要走 getBindingSlotId）
const existingBindingOptions = computed(() => {
  return props.bindings || [];
});

// Available slots that are not yet bound to this topic（boundSlotIds 必须用真实 slotId）
const boundSlotIds = computed(() => {
  const s = new Set<number>();
  for (const b of props.bindings || []) {
    const sid = getBindingSlotId(b);
    if (sid) s.add(sid);
  }
  return s;
});

const availableSlots = computed(() => {
  return capacityStore.slots.filter(s => !boundSlotIds.value.has(s.id));
});

watch(() => props.modelValue, (open) => {
  if (open) {
    capacityStore.fetchSlots();
    form.newDriSlotId = undefined;
  }
});

async function handleSubmit() {
  if (!formRef.value || !props.topic) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    const slotId = Number(form.newDriSlotId);
    if (!Number.isFinite(slotId) || slotId <= 0) {
      ElMessage.error('请选择新负责人');
      return;
    }

    loading.value = true;
    try {
      // ✅ 这里传的一定是 capacity_slots.id
      await topicsStore.changeDri(props.topic!.id, { newDriSlotId: slotId });
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
