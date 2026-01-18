<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="Change DRI"
    width="500px"
  >
    <p class="text-sm text-zinc-600 mb-4">
      Select a new DRI for this topic. EXTERNAL and CUSTOMER users cannot be DRI.
    </p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="New DRI" prop="driId">
        <el-select v-model="form.driId" class="w-full" filterable>
          <el-option
            v-for="user in eligibleDRIs"
            :key="user.id"
            :value="user.id"
            :label="user.name"
            :disabled="user.id === topic?.driId"
          >
            <div class="flex items-center gap-2">
              <span>{{ user.name }}</span>
              <el-tag size="small" type="info">{{ user.role }}</el-tag>
              <span v-if="user.id === topic?.driId" class="text-xs text-zinc-400">(Current)</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        Change DRI
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { useUsersStore } from '@/stores/users';
import { useTopicsStore } from '@/stores/topics';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import type { Topic } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  topic: Topic | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'changed'): void;
}>();

const usersStore = useUsersStore();
const topicsStore = useTopicsStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  driId: undefined as number | undefined,
});

const rules: FormRules = {
  driId: [{ required: true, message: 'Please select DRI', trigger: 'change' }],
};

const eligibleDRIs = computed(() =>
  usersStore.users.filter(u => u.role !== 'EXTERNAL' && u.role !== 'CUSTOMER')
);

watch(() => props.modelValue, (open) => {
  if (open) {
    usersStore.fetchUsers();
    form.driId = props.topic?.driId;
  }
});

async function handleSubmit() {
  if (!formRef.value || !props.topic) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await topicsStore.updateTopic(props.topic.id, { driId: form.driId });
      ElMessage.success('DRI changed');
      emit('update:modelValue', false);
      emit('changed');
    } catch (error) {
      ElMessage.error('Failed to change DRI');
    } finally {
      loading.value = false;
    }
  });
}
</script>
