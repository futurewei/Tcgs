<template>
  <div class="capacity-page">
    <div class="page-header">
      <h1 class="page-title">人力管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showCreateSlot = true">
        添加人员
      </el-button>
    </div>

    <div class="slots-grid">
      <!-- Algo Slots -->
      <section class="tcgs-surface slots-section">
        <div class="section-header">
          <div>
            <h2 class="section-title">自有人力</h2>
            <p class="section-desc">内部算法团队成员</p>
          </div>
        </div>
        <div class="slots-list">
          <div v-for="slot in algoSlots" :key="slot.id" class="slot-card internal">
            <div class="slot-header">
              <div class="slot-info">
                <SlotChip :slot="slot" :clickable="true" />
              </div>
              <el-dropdown v-if="authStore.isAdmin" trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editSlot(slot)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="deleteSlot(slot)">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="slot-progress">
              <div class="progress-header">
                <span class="progress-label">容量使用</span>
                <span class="progress-value">{{ getSlotUsage(slot) }}%</span>
              </div>
              <el-progress
                :percentage="getSlotUsage(slot)"
                :status="getSlotUsage(slot) >= 100 ? 'exception' : ''"
                :show-text="false"
              />
            </div>

            <div v-if="slot.bindings?.length" class="slot-bindings">
              <p class="bindings-title">分配详情:</p>
              <div v-for="binding in slot.bindings" :key="binding.id" class="binding-row">
                <span class="binding-topic">{{ binding.topic?.title || `课题 #${binding.topicId}` }}</span>
                <span class="binding-percent">{{ binding.percentage }}%</span>
              </div>
            </div>
          </div>
          <div v-if="algoSlots.length === 0" class="empty-state">
            暂无自有人力
          </div>
        </div>
      </section>

      <!-- External Slots -->
      <section class="tcgs-surface slots-section">
        <div class="section-header">
          <div>
            <h2 class="section-title">协调人力</h2>
            <p class="section-desc">外部协作人员</p>
          </div>
        </div>
        <div class="slots-list">
          <div v-for="slot in externalSlots" :key="slot.id" class="slot-card external">
            <div class="slot-header">
              <div class="slot-info">
                <SlotChip :slot="slot" :clickable="true" />
              </div>
              <el-dropdown v-if="authStore.isAdmin" trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editSlot(slot)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="deleteSlot(slot)">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="slot-progress">
              <div class="progress-header">
                <span class="progress-label">容量使用</span>
                <span class="progress-value">{{ getSlotUsage(slot) }}%</span>
              </div>
              <el-progress
                :percentage="getSlotUsage(slot)"
                :status="getSlotUsage(slot) >= 100 ? 'exception' : ''"
                :show-text="false"
              />
            </div>

            <div v-if="slot.bindings?.length" class="slot-bindings">
              <p class="bindings-title">分配详情:</p>
              <div v-for="binding in slot.bindings" :key="binding.id" class="binding-row">
                <span class="binding-topic">{{ binding.topic?.title || `课题 #${binding.topicId}` }}</span>
                <span class="binding-percent">{{ binding.percentage }}%</span>
              </div>
            </div>
          </div>
          <div v-if="externalSlots.length === 0" class="empty-state">
            暂无协调人力
          </div>
        </div>
      </section>
    </div>

    <!-- Create/Edit Slot Dialog -->
    <el-dialog v-model="showCreateSlot" :title="editingSlot ? '编辑人员' : '添加人员'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="人员名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="ALGO">自有人力</el-radio>
            <el-radio value="EXTERNAL">协调人力</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关联用户 (可选)">
          <el-select v-model="form.userId" class="w-full" clearable filterable placeholder="选择用户">
            <el-option v-for="user in usersStore.users" :key="user.id" :value="user.id" :label="user.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="总容量 (%)" prop="totalCapacity">
          <el-input-number v-model="form.totalCapacity" :min="10" :max="200" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSlot = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSlot">{{ editingSlot ? '更新' : '创建' }}</el-button>
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
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  totalCapacity: [{ required: true, message: '请设置容量', trigger: 'change' }],
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
    await ElMessageBox.confirm('确定要删除此人员？', '删除人员', { type: 'warning' });
    await capacityStore.deleteSlot(slot.id);
    ElMessage.success('删除成功');
  } catch (error) {}
}

async function saveSlot() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editingSlot.value) {
        await capacityStore.updateSlot(editingSlot.value.id, form);
        ElMessage.success('更新成功');
      } else {
        await capacityStore.createSlot(form);
        ElMessage.success('创建成功');
      }
      showCreateSlot.value = false;
      editingSlot.value = null;
      form.name = '';
      form.type = 'ALGO';
      form.userId = undefined;
      form.totalCapacity = 100;
    } catch (error) {
      ElMessage.error('保存失败');
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

<style scoped>
.capacity-page {
  padding: var(--space-5);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}
.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-5);
}
@media (max-width: 1024px) {
  .slots-grid {
    grid-template-columns: 1fr;
  }
}

.slots-section {
  overflow: hidden;
}
.section-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}
.section-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}
.section-desc {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0 0;
}

.slots-list {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.slot-card {
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}
.slot-card.internal {
  border: 1px solid var(--color-border-light);
}
.slot-card.external {
  border: 1px dashed var(--color-member-external-border);
  background: var(--color-member-external-bg);
}

.slot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}
.slot-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.slot-user {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
}
.slot-user:hover {
  color: var(--color-primary);
}
.slot-user.external {
  color: var(--color-text-tertiary);
}

.slot-progress {
  margin-bottom: var(--space-2);
}
.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-1);
}
.progress-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
.progress-value {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.slot-bindings {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}
.bindings-title {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-2) 0;
}
.binding-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--text-xs);
  padding: var(--space-1) 0;
}
.binding-topic {
  color: var(--color-text-secondary);
}
.binding-percent {
  color: var(--color-text-tertiary);
}

.empty-state {
  text-align: center;
  padding: var(--space-6);
  color: var(--color-text-disabled);
  font-size: var(--text-sm);
}

.w-full {
  width: 100%;
}
</style>
