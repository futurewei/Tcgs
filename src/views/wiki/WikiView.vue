<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Wiki</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showCreateDirection = true">
        New Direction
      </el-button>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div
        v-for="direction in directions"
        :key="direction.id"
        class="bg-white rounded-xl border border-zinc-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
        @click="openDirection(direction)"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-zinc-100 rounded-lg flex items-center justify-center">
            <el-icon :size="24" class="text-zinc-500"><Folder /></el-icon>
          </div>
          <el-dropdown v-if="authStore.isAdmin" trigger="click" @click.stop>
            <el-button size="small" text>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click.stop="editDirection(direction)">Edit</el-dropdown-item>
                <el-dropdown-item @click.stop="deleteDirection(direction)">Delete</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <h3 class="font-semibold text-zinc-900 mb-2">{{ direction.name }}</h3>
        <p class="text-sm text-zinc-500 mb-4 line-clamp-2">{{ direction.description }}</p>

        <div class="flex items-center justify-between text-xs text-zinc-400">
          <span>{{ direction.pages?.length || 0 }} pages</span>
          <span>Updated {{ formatDate(direction.updatedAt) }}</span>
        </div>
      </div>

      <div
        v-if="directions.length === 0"
        class="col-span-3 bg-white rounded-xl border border-zinc-200 p-12 text-center"
      >
        <p class="text-zinc-400">No wiki directions yet</p>
      </div>
    </div>

    <!-- Create/Edit Direction Dialog -->
    <el-dialog
      v-model="showCreateDirection"
      :title="editingDirection ? 'Edit Direction' : 'New Direction'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Direction name" />
        </el-form-item>
        <el-form-item label="Description" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="Describe this direction"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDirection = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="saveDirection">
          {{ editingDirection ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useWikiStore } from '@/stores/wiki';
import { useAuthStore } from '@/stores/auth';
import { Folder, MoreFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import dayjs from 'dayjs';
import type { WikiDirection } from '@/types';

const router = useRouter();
const wikiStore = useWikiStore();
const authStore = useAuthStore();

const showCreateDirection = ref(false);
const editingDirection = ref<WikiDirection | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  name: '',
  description: '',
});

const rules: FormRules = {
  name: [{ required: true, message: 'Please enter name', trigger: 'blur' }],
  description: [{ required: true, message: 'Please enter description', trigger: 'blur' }],
};

const directions = computed(() => wikiStore.directions);

function formatDate(date: string) {
  return dayjs(date).format('MMM D, YYYY');
}

function openDirection(direction: WikiDirection) {
  router.push(`/wiki/directions/${direction.id}`);
}

function editDirection(direction: WikiDirection) {
  editingDirection.value = direction;
  form.name = direction.name;
  form.description = direction.description;
  showCreateDirection.value = true;
}

async function deleteDirection(direction: WikiDirection) {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this direction? All pages will be deleted.',
      'Delete Direction',
      { type: 'warning' }
    );
    // await wikiApi.deleteDirection(direction.id);
    await wikiStore.fetchDirections();
    ElMessage.success('Direction deleted');
  } catch (error) {
    // Cancelled
  }
}

async function saveDirection() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    saving.value = true;
    try {
      if (editingDirection.value) {
        // await wikiApi.updateDirection(editingDirection.value.id, form);
        ElMessage.success('Direction updated');
      } else {
        await wikiStore.createDirection(form);
        ElMessage.success('Direction created');
      }
      showCreateDirection.value = false;
      editingDirection.value = null;
      form.name = '';
      form.description = '';
    } catch (error) {
      ElMessage.error('Failed to save direction');
    } finally {
      saving.value = false;
    }
  });
}

onMounted(() => {
  wikiStore.fetchDirections();
});
</script>
