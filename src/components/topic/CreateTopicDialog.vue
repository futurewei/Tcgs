<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="Create New Topic"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <el-form-item label="Title" prop="title">
        <el-input v-model="form.title" placeholder="Enter topic title" />
      </el-form-item>

      <el-form-item label="Description" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="Describe the topic"
        />
      </el-form-item>

      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="Type" prop="type">
          <el-select v-model="form.type" class="w-full">
            <el-option value="UNCERTAINTY" label="Uncertainty" />
            <el-option value="EVOLUTION" label="Evolution" />
          </el-select>
        </el-form-item>

        <el-form-item label="Urgency" prop="urgency">
          <el-select v-model="form.urgency" class="w-full">
            <el-option value="P0" label="P0 - Critical" />
            <el-option value="P1" label="P1 - High" />
            <el-option value="P2" label="P2 - Medium" />
            <el-option value="P3" label="P3 - Low" />
          </el-select>
        </el-form-item>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="DRI (Directly Responsible Individual)" prop="driId">
          <el-select v-model="form.driId" class="w-full" filterable>
            <el-option
              v-for="user in eligibleDRIs"
              :key="user.id"
              :value="user.id"
              :label="user.name"
            >
              <div class="flex items-center gap-2">
                <span>{{ user.name }}</span>
                <el-tag size="small" type="info">{{ user.role }}</el-tag>
              </div>
            </el-option>
          </el-select>
          <p class="text-xs text-zinc-400 mt-1">EXTERNAL and CUSTOMER users cannot be DRI</p>
        </el-form-item>

        <el-form-item label="Stage Template" prop="templateId">
          <el-select v-model="form.templateId" class="w-full">
            <el-option
              v-for="template in templates"
              :key="template.id"
              :value="template.id"
              :label="template.name"
            >
              <div class="flex items-center justify-between w-full">
                <span>{{ template.name }}</span>
                <span class="text-xs text-zinc-400">{{ template.stages?.length || 0 }} stages</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </div>

      <!-- Requester Section -->
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="Requester (Customer)" prop="requesterUserId">
          <el-select 
            v-model="form.requesterUserId" 
            class="w-full" 
            filterable
            clearable
            placeholder="Select customer user (optional)"
          >
            <el-option
              v-for="user in eligibleRequesters"
              :key="user.id"
              :value="user.id"
              :label="user.name"
            >
              <div class="flex items-center gap-2">
                <span>{{ user.name }}</span>
                <el-tag size="small" type="info">CUSTOMER</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="Requester Name (External)" prop="requesterName">
          <el-input 
            v-model="form.requesterName" 
            placeholder="Enter requester name (required if no customer selected)"
            :disabled="!!form.requesterUserId"
          />
          <p class="text-xs text-zinc-400 mt-1">
            {{ form.requesterUserId ? 'Using selected customer name' : 'Enter external requester name' }}
          </p>
        </el-form-item>
      </div>

      <!-- Template Preview -->
      <div v-if="selectedTemplate" class="mt-4 p-4 bg-zinc-50 rounded-lg">
        <p class="text-sm font-medium text-zinc-700 mb-2">Stage Preview:</p>
        <StageTimeline
          :stages="selectedTemplate.stages"
          :compact="false"
        />
      </div>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleCreate">
        Create Topic
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
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import StageTimeline from './StageTimeline.vue';

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

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  title: '',
  description: '',
  type: 'UNCERTAINTY' as const,
  urgency: 'P2' as const,
  driId: undefined as number | undefined,
  templateId: undefined as number | undefined,
  requesterName: '' as string,
  requesterUserId: undefined as number | undefined,
});

const rules: FormRules = {
  title: [{ required: true, message: 'Please enter title', trigger: 'blur' }],
  description: [{ required: true, message: 'Please enter description', trigger: 'blur' }],
  type: [{ required: true, message: 'Please select type', trigger: 'change' }],
  urgency: [{ required: true, message: 'Please select urgency', trigger: 'change' }],
  driId: [{ required: true, message: 'Please select DRI', trigger: 'change' }],
  templateId: [{ required: true, message: 'Please select template', trigger: 'change' }],
  requesterName: [
    {
      validator: (rule, value, callback) => {
        if (!form.requesterUserId && (!value || !value.trim())) {
          callback(new Error('Please enter requester name or select a customer'));
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

// EXTERNAL and CUSTOMER users cannot be DRI
const eligibleDRIs = computed(() =>
  usersStore.users.filter(u => u.role !== 'CUSTOMER')
);

// CUSTOMER users for requester selection
const eligibleRequesters = computed(() =>
  usersStore.users.filter(u => u.role === 'CUSTOMER')
);

watch(() => props.modelValue, (open) => {
  if (open) {
    templatesStore.fetchTemplates();
    usersStore.fetchUsers();
    // Reset form
    form.title = '';
    form.description = '';
    form.type = 'UNCERTAINTY';
    form.urgency = 'P2';
    form.driId = undefined;
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
      ElMessage.error('Please enter requester name or select a customer');
      return;
    }

    loading.value = true;
    try {
      const topic = await topicsStore.createTopic({
        title: form.title,
        description: form.description,
        type: form.type,
        urgency: form.urgency,
        driId: form.driId!,
        templateId: form.templateId!,
        requesterName: form.requesterName,
        requesterUserId: form.requesterUserId,
      });

      ElMessage.success('Topic created successfully');
      emit('update:modelValue', false);
      router.push(`/topics/${topic.id}`);
    } catch (error) {
      ElMessage.error('Failed to create topic');
    } finally {
      loading.value = false;
    }
  });
}
</script>
