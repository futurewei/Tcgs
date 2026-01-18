<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">Capacity Management</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showCreateSlot = true">
        New Slot
      </el-button>
    </div>

    <div class="grid grid-cols-2 gap-6">
      <!-- Algo Slots -->
      <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <div class="p-4 border-b border-zinc-100">
          <h2 class="font-semibold text-zinc-900">Algo Slots</h2>
          <p class="text-sm text-zinc-500">Internal algorithm team members</p>
        </div>
        <div class="p-4 space-y-3">
          <div
            v-for="slot in algoSlots"
            :key="slot.id"
            class="p-4 bg-zinc-50 rounded-lg"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <SlotChip :slot="slot" />
                <span v-if="slot.user" class="text-sm text-zinc-600">{{ slot.user.name }}</span>
              </div>
              <el-dropdown v-if="authStore.isAdmin" trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editSlot(slot)">Edit</el-dropdown-item>
                    <el-dropdown-item @click="deleteSlot(slot)">Delete</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="mb-2">
              <div class="flex items-center justify-between text-xs text-zinc-500 mb-1">
                <span>Capacity Usage</span>
                <span>{{ getSlotUsage(slot) }}%</span>
              </div>
              <el-progress
                :percentage="getSlotUsage(slot)"
                :status="getSlotUsage(slot) >= 100 ? 'exception' : ''"
                :show-text="false"
              />
            </div>

            <div v-if="slot.bindings?.length" class="mt-3 space-y-1">
              <p class="text-xs font-medium text-zinc-500">Bindings:</p>
              <div
                v-for="binding in slot.bindings"
                :key="binding.id"
                class="flex items-center justify-between text-xs"
              >
                <span class="text-zinc-600">{{ binding.topic?.title || `Topic #${binding.topicId}` }}</span>
                <span class="text-zinc-500">{{ binding.percentage }}%</span>
              </div>
            </div>
          </div>
          <div v-if="algoSlots.length === 0" class="text-center py-8 text-zinc-400">
            No algo slots configured
          </div>
        </div>
      </div>

      <!-- External Slots -->
      <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <div class="p-4 border-b border-zinc-100">
          <h2 class="font-semibold text-zinc-900">External Slots</h2>
          <p class="text-sm text-zinc-500">External collaborators (cannot be DRI)</p>
        </div>
        <div class="p-4 space-y-3">
          <div
            v-for="slot in externalSlots"
            :key="slot.id"
            class="p-4 bg-zinc-50 rounded-lg border border-dashed border-zinc-200"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <SlotChip :slot="slot" />
                <span v-if="slot.user" class="text-sm text-zinc-500">{{ slot.user.name }}</span>
              </div>
              <el-dropdown v-if="authStore.isAdmin" trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editSlot(slot)">Edit</el-dropdown-item>
                    <el-dropdown-item @click="deleteSlot(slot)">Delete</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="mb-2">
              <div class="flex items-center justify-between text-xs text-zinc-500 mb-1">
                <span>Capacity Usage</span>
                <span>{{ getSlotUsage(slot) }}%</span>
              </div>
              <el-progress
                :percentage="getSlotUsage(slot)"
                :status="getSlotUsage(slot) >= 100 ? 'exception' : ''"
                :show-text="false"
              />
            </div>

            <div v-if="slot.bindings?.length" class="mt-3 space-y-1">
              <p class="text-xs font-medium text-zinc-500">Bindings:</p>
              <div
                v-for="binding in slot.bindings"
                :key="binding.id"
                class="flex items-center justify-between text-xs"
              >
                <span class="text-zinc-500">{{ binding.topic?.title || `Topic #${binding.topicId}` }}</span>
                <span class="text-zinc-400">{{ binding.percentage }}%</span>
              </div>
            </div>
          </div>
          <div v-if="externalSlots.length === 0" class="text-center py-8 text-zinc-400">
            No external slots configured
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Slot Dialog -->
    <el-dialog v-model="showCreateSlot" :title="editingSlot ? 'Edit Slot' : 'Create Slot'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Slot name" />
        </el-form-item>

        <el-form-item label="Type" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="ALGO">Algo</el-radio>
            <el-radio value="EXTERNAL">External</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="Linked User (Optional)">
          <el-select v-model="form.userId" class="w-full" clearable filterable>
            <el-option
              v-for="user in usersStore.users"
              :key="user.id"
              :value="user.id"
              :label="user.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Total Capacity (%)" prop="totalCapacity">
          <el-input-number v-model="form.totalCapacity" :min="10" :max="200" :step="10" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateSlot = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="saveSlot">
          {{ editingSlot ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useCapacityStore } from '@/stores/capacity';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import { MoreFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import SlotChip from '@/components/common/SlotChip.vue';
import type { CapacitySlot } from '@/types';

const capacityStore = useCapacityStore();
const usersStore = useUsersStore();
const authStore = useAuthStore();

const showCreateSlot = ref(false);
const editingSlot = ref<CapacitySlot | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  name: '',
  type: 'ALGO' as 'ALGO' | 'EXTERNAL',
  userId: undefined as number | undefined,
  totalCapacity: 100,
});

const rules: FormRules = {
  name: [{ required: true, message: 'Please enter name', trigger: 'blur' }],
  type: [{ required: true, message: 'Please select type', trigger: 'change' }],
  totalCapacity: [{ required: true, message: 'Please set capacity', trigger: 'change' }],
};

const algoSlots = computed(() => capacityStore.algoSlots);
const externalSlots = computed(() => capacityStore.externalSlots);

function getSlotUsage(slot: CapacitySlot) {
  return capacityStore.getSlotUsage(slot);
}

function editSlot(slot: CapacitySlot) {
  editingSlot.value = slot;
  form.name = slot.name;
  form.type = slot.type;
  form.userId = slot.userId;
  form.totalCapacity = slot.totalCapacity;
  showCreateSlot.value = true;
}

async function deleteSlot(slot: CapacitySlot) {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this slot?',
      'Delete Slot',
      { type: 'warning' }
    );
    await capacityStore.deleteSlot(slot.id);
    ElMessage.success('Slot deleted');
  } catch (error) {
    // Cancelled
  }
}

async function saveSlot() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    saving.value = true;
    try {
      if (editingSlot.value) {
        await capacityStore.updateSlot(editingSlot.value.id, form);
        ElMessage.success('Slot updated');
      } else {
        await capacityStore.createSlot(form);
        ElMessage.success('Slot created');
      }
      showCreateSlot.value = false;
      editingSlot.value = null;
      form.name = '';
      form.type = 'ALGO';
      form.userId = undefined;
      form.totalCapacity = 100;
    } catch (error) {
      ElMessage.error('Failed to save slot');
    } finally {
      saving.value = false;
    }
  });
}

onMounted(() => {
  capacityStore.fetchSlots();
  usersStore.fetchUsers();
});
</script>
