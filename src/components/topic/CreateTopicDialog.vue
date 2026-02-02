<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="创建课题"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <el-form-item label="课题名称" prop="title">
        <el-input v-model="form.title" placeholder="输入课题名称" />
      </el-form-item>

      <el-form-item label="课题描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="描述课题内容"
        />
      </el-form-item>

      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" class="w-full">
            <el-option value="UNCERTAINTY" label="不确定性" />
            <el-option value="EVOLUTION" label="演进" />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级" prop="urgency">
          <el-select v-model="form.urgency" class="w-full">
            <el-option value="P0" label="P0 - 紧急" />
            <el-option value="P1" label="P1 - 高" />
            <el-option value="P2" label="P2 - 中" />
            <el-option value="P3" label="P3 - 低" />
          </el-select>
        </el-form-item>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="DRI (负责人)" prop="initialDriSlotId">
          <el-select v-model="form.initialDriSlotId" class="w-full" filterable placeholder="选择负责人">
            <el-option-group label="自有人力">
              <el-option
                v-for="slot in algoSlots"
                :key="slot.id"
                :value="slot.id"
                :label="slot.name"
              >
                <div class="flex items-center justify-between w-full">
                  <span>{{ slot.name }}</span>
                  <span class="text-xs text-zinc-400">{{ getSlotUsage(slot) }}% 已用</span>
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
                  <span class="text-xs text-zinc-400">{{ getSlotUsage(slot) }}% 已用</span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
          <p class="text-xs text-zinc-400 mt-1">DRI 会自动成为首个人力绑定</p>
        </el-form-item>

        <el-form-item label="流程模板" prop="templateId">
          <el-select v-model="form.templateId" class="w-full" placeholder="选择流程模板">
            <el-option
              v-for="template in templates"
              :key="template.id"
              :value="template.id"
              :label="template.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ template.name }}</span>
                <span class="text-xs text-zinc-400">{{ template.stages?.length || 0 }} 个阶段</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </div>

      <!-- DRI Percentage -->
      <el-form-item v-if="form.initialDriSlotId" label="DRI 分配比例 (%)">
        <el-slider v-model="form.initialDriPercentage" :min="5" :max="100" :step="5" show-input />
      </el-form-item>

      <!-- Requester Section -->
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="需求方 (已注册用户)" prop="requesterUserId">
          <el-select 
            v-model="form.requesterUserId" 
            class="w-full" 
            filterable
            clearable
            placeholder="选择需求方用户 (可选)"
          >
            <el-option
              v-for="user in eligibleRequesters"
              :key="user.id"
              :value="user.id"
              :label="user.name"
            >
              <div class="flex items-center gap-2">
                <span>{{ user.name }}</span>
                <el-tag size="small" type="info">需求方</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="需求方名称 (外部)" prop="requesterName">
          <el-input 
            v-model="form.requesterName" 
            placeholder="输入需求方名称 (如未选择用户则必填)"
            :disabled="!!form.requesterUserId"
          />
          <p class="text-xs text-zinc-400 mt-1">
            {{ form.requesterUserId ? '使用已选用户名称' : '输入外部需求方名称' }}
          </p>
        </el-form-item>
      </div>

      <!-- Template Preview -->
      <div v-if="selectedTemplate" class="mt-4 p-4 bg-zinc-50 rounded-lg">
        <p class="text-sm font-medium text-zinc-700 mb-2">阶段预览:</p>
        <StageTimeline
          :stages="selectedTemplate.stages"
          :compact="false"
        />
      </div>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleCreate">
        创建课题
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useTopicsStore } from '@/stores/topics';
import { useTemplatesStore } from '@/stores/templates';
import { useUsersStore } from '@/stores/users';
import { useCapacityStore } from '@/stores/capacity';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import StageTimeline from './StageTimeline.vue';
import type { CapacitySlot } from '@/types';

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const router = useRouter();
const topicsStore = useTopicsStore();
const templatesStore = useTemplatesStore();
const usersStore = useUsersStore();
const capacityStore = useCapacityStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  title: '',
  description: '',
  type: 'UNCERTAINTY' as const,
  urgency: 'P2' as const,
  initialDriSlotId: undefined as number | undefined,
  initialDriPercentage: 25,
  templateId: undefined as number | undefined,
  requesterName: '' as string,
  requesterUserId: undefined as number | undefined,
});

const rules: FormRules = {
  title: [{ required: true, message: '请输入课题名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入课题描述', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  urgency: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  initialDriSlotId: [{ required: true, message: '请选择负责人', trigger: 'change' }],
  templateId: [{ required: true, message: '请选择流程模板', trigger: 'change' }],
  requesterName: [
    {
      validator: (rule, value, callback) => {
        if (!form.requesterUserId && (!value || !value.trim())) {
          callback(new Error('请输入需求方名称或选择需求方用户'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
};

const templates = computed(() => templatesStore.templates);
const selectedTemplate = computed(() =>
  templates.value.find(t => t.id === form.templateId)
);

// Slots for DRI selection
const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

function getSlotUsage(slot: CapacitySlot): number {
  return capacityStore.getSlotUsage(slot);
}

// CUSTOMER users for requester selection
const eligibleRequesters = computed(() =>
  usersStore.users.filter(u => u.role === 'CUSTOMER')
);

watch(() => props.modelValue, (open) => {
  if (open) {
    templatesStore.fetchTemplates();
    usersStore.fetchUsers();
    capacityStore.fetchSlots();
    // Reset form
    form.title = '';
    form.description = '';
    form.type = 'UNCERTAINTY';
    form.urgency = 'P2';
    form.initialDriSlotId = undefined;
    form.initialDriPercentage = 25;
    form.templateId = undefined;
    form.requesterName = '';
    form.requesterUserId = undefined;
  }
});

// Sync requester name when customer is selected
watch(() => form.requesterUserId, (userId) => {
  if (userId) {
    const user = eligibleRequesters.value.find(u => u.id === userId);
    if (user) {
      form.requesterName = user.name;
    }
  }
});

async function handleCreate() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    // Validate requester: either requesterUserId or requesterName must be provided
    if (!form.requesterUserId && !form.requesterName?.trim()) {
      ElMessage.error('请输入需求方名称或选择需求方用户');
      return;
    }

    loading.value = true;
    try {
      // --- 关键新增：从 initialDriSlotId 推导 initialDriUserId ---
      const pickedDriId = form.initialDriSlotId;

      // capacityStore.slots 里的一条记录一般长这样：
      // { id: slotId(或userId), userId, user: {id, name...}, ... }
      const pickedSlot = pickedDriId != null
        ? capacityStore.slots?.find((s: any) => Number(s.id) === Number(pickedDriId))
        : undefined;

      // 兼容各种字段：userId / user.id；以及“id 本身就是 userId”的迁移期情况
      const initialDriUserId =
        pickedSlot?.userId != null
          ? Number(pickedSlot.userId)
          : pickedSlot?.user?.id != null
            ? Number(pickedSlot.user.id)
            : pickedDriId != null
              ? Number(pickedDriId)
              : undefined;

      const topic = await topicsStore.createTopic({
        title: form.title,
        description: form.description,
        type: form.type,
        urgency: form.urgency,
        templateId: form.templateId!,
        requesterName: form.requesterName,
        requesterUserId: form.requesterUserId,

        // --- DRI：同时传 slotId + userId，后端认哪个用哪个 ---
        initialDriSlotId: form.initialDriSlotId,
        initialDriUserId,
        initialDriPercentage: form.initialDriPercentage,
      });

      ElMessage.success('创建成功');
      
      // ✅ 创建课题会在后端自动创建 DRI binding，但 capacity 看板数据需要刷新
      // 否则用户需要手动刷新页面才会看到 usage 扣减
      try {
  	   await capacityStore.fetchSlots();
      } catch (e) {
  	   console.warn('refresh slots after create topic failed', e);
      }

      emit('created', topic);
      emit('update:modelValue', false);
    } catch (error: any) {
      console.error('Create topic error:', error);
      ElMessage.error(error.response?.data?.detail || '创建失败');
    } finally {
      loading.value = false;
    }
  });
}

</script>
