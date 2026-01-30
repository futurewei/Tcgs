<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="dialogTitle"
    width="440px"
    destroy-on-close
  >
    <div v-if="binding" class="edit-binding">
      <div class="binding-summary">
        <div class="binding-name">
          <span class="name">{{ displayName }}</span>
          <el-tag v-if="isDri" size="small" type="success">DRI</el-tag>
          <el-tag v-if="isForced" size="small" type="warning">强制</el-tag>
        </div>
        <div class="binding-meta">
          <span class="meta-item">当前：{{ currentPct }}%</span>
          <span class="meta-item">调整后：{{ form.percentage }}%</span>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="时间投入 (%)" prop="percentage">
          <el-slider v-model="form.percentage" :min="0" :max="100" :step="5" show-input />
          <p class="help-text">建议 5% 为粒度。设为 0% 等价于“保留人但不投入”（仅调整投入，不会删除绑定）。</p>
        </el-form-item>

        <el-form-item v-if="authStore.isAdmin" label="管理员选项">
          <el-checkbox v-model="form.isForced">强制分配（忽略容量限制）</el-checkbox>
        </el-form-item>
      </el-form>
    </div>

    <div v-else class="empty-state">未选择成员</div>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>

      <el-button
        v-if="binding && !isDri"
        type="danger"
        plain
        :loading="loadingDelete"
        @click="handleDelete"
      >
        移除
      </el-button>

      <el-button
        type="primary"
        :loading="loadingSave"
        :disabled="!binding"
        @click="handleSave"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { useCapacityStore } from '@/stores/capacity';
import { useAuthStore } from '@/stores/auth';
import type { Binding } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  binding: Binding | any | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void;
  (e: 'updated'): void;
  (e: 'deleted'): void;
}>();

const capacityStore = useCapacityStore();
const authStore = useAuthStore();

const formRef = ref<FormInstance>();
const loadingSave = ref(false);
const loadingDelete = ref(false);

const form = reactive({
  percentage: 0,
  isForced: false,
});

const rules: FormRules = {
  percentage: [{ required: true, message: '请设置时间投入', trigger: 'change' }],
};

const isDri = computed(() => !!(props.binding?.isDri || props.binding?.is_dri));
const isForced = computed(() => !!(props.binding?.isForced || props.binding?.is_forced));
const currentPct = computed(() => Number(props.binding?.percentage ?? 0));

const displayName = computed(() => {
  const b: any = props.binding;
  return (
    b?.slot?.name ||
    b?.slot_name ||
    b?.user?.name ||
    b?.user_name ||
    `成员#${b?.slotId ?? b?.slot_id ?? b?.id ?? ''}`
  );
});

const dialogTitle = computed(() => (isDri.value ? '调整 DRI 时间投入' : '编辑成员时间投入'));

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return;
    form.percentage = currentPct.value;
    form.isForced = isForced.value;
  }
);

async function handleSave() {
  if (!props.binding) return;
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loadingSave.value = true;
    try {
      await capacityStore.updateBinding(Number(props.binding.id), {
        percentage: Number(form.percentage),
        isForced: form.isForced,
      });
      ElMessage.success('已更新');
      emit('update:modelValue', false);
      emit('updated');
    } catch (err: any) {
      ElMessage.error(err?.response?.data?.detail || '更新失败');
    } finally {
      loadingSave.value = false;
    }
  });
}

async function handleDelete() {
  if (!props.binding) return;

  if (isDri.value) {
    ElMessage.warning('DRI 责任人不能直接移除，请先更换 DRI 或将投入调整为 0%。');
    return;
  }

  try {
    await ElMessageBox.confirm(`确认移除“${displayName.value}”吗？`, '确认移除', {
      type: 'warning',
      confirmButtonText: '移除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }

  loadingDelete.value = true;
  try {
    await capacityStore.deleteBinding(Number(props.binding.id));
    ElMessage.success('已移除');
    emit('update:modelValue', false);
    emit('deleted');
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '移除失败');
  } finally {
    loadingDelete.value = false;
  }
}
</script>

<style scoped>
.edit-binding {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.binding-summary {
  padding: var(--space-3);
  border: 1px solid var(--color-border-subtle);
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
}

.binding-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.binding-name .name {
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.binding-meta {
  margin-top: var(--space-2);
  display: flex;
  gap: var(--space-3);
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

.help-text {
  margin: var(--space-2) 0 0;
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
  line-height: 1.4;
}

.empty-state {
  padding: var(--space-6) 0;
  text-align: center;
  color: var(--color-text-muted);
}
</style>
