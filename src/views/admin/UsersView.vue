<template>
  <div class="users-page">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <el-button type="primary" @click="showCreateUser = true">新建用户</el-button>
    </div>

    <section class="tcgs-surface users-table-section">
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar">{{ getInitials(row.name) }}</div>
              <div class="user-info">
                <p class="user-name">{{ row.name }}</p>
                <p class="user-email">{{ row.email }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-select :model-value="row.role" size="small" @change="(val: string) => updateRole(row, val)">
              <el-option value="ADMIN" label="管理员" />
              <el-option value="MEMBER" label="成员" />
              <el-option value="REVIEWER" label="评审人" />
              <el-option value="EXTERNAL" label="外部人员" />
              <el-option value="CUSTOMER_INTERNAL" label="需求方(PDU内)" />
              <el-option value="CUSTOMER_EXTERNAL" label="需求方(PDU外)" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <span :class="['status-badge', row.role === 'EXTERNAL' ? 'external' : 'active']">
              {{ row.role === 'EXTERNAL' ? '外部' : '活跃' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text @click="editUser(row)">编辑</el-button>
            <el-button size="small" type="danger" text @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="usersStore.total"
          layout="total, prev, pager, next"
          @current-change="fetchUsers"
        />
      </div>
    </section>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showCreateUser" :title="editingUser ? '编辑用户' : '新建用户'" width="480px" @closed="editingUser = null">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="editingUser ? '留空则不修改' : '请输入密码'" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" class="w-full">
            <el-option value="ADMIN" label="管理员" />
            <el-option value="MEMBER" label="成员" />
            <el-option value="REVIEWER" label="评审人" />
            <el-option value="EXTERNAL" label="外部人员" />
            <el-option value="CUSTOMER_INTERNAL" label="需求方(PDU内)" />
            <el-option value="CUSTOMER_EXTERNAL" label="需求方(PDU外)" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateUser = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useUsersStore } from '@/stores/users';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import dayjs from 'dayjs';
import type { User, UserRole } from '@/types';

const usersStore = useUsersStore();
const showCreateUser = ref(false);
const editingUser = ref<User | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();

const pagination = reactive({ page: 1, pageSize: 20 });
const form = reactive({ name: '', email: '', password: '', role: 'MEMBER' as UserRole });

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [{ validator: (rule, value, callback) => {
    if (!editingUser.value && !value) callback(new Error('请输入密码'));
    else callback();
  }}],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
};

const users = computed(() => usersStore.users);
const loading = computed(() => usersStore.loading);

function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD');
}

function fetchUsers() { usersStore.fetchUsers(pagination.page, pagination.pageSize); }

function editUser(user: User) {
  editingUser.value = user;
  form.name = user.name;
  form.email = user.email;
  form.password = '';
  form.role = user.role;
  showCreateUser.value = true;
}

async function updateRole(user: User, role: string) {
  try {
    await usersStore.updateRole(user.id, role as UserRole);
    ElMessage.success('角色已更新');
  } catch { ElMessage.error('更新失败'); }
}

async function deleteUser(user: User) {
  try {
    await ElMessageBox.confirm('确定删除该用户吗？', '删除用户', { type: 'warning' });
  } catch {
    return; // 用户取消
  }

  try {
    await usersStore.deleteUser(user.id);
    ElMessage.success('用户已删除');
  } catch (error: any) {
    console.error('删除用户失败:', error);
    ElMessage.error(error?.response?.data?.detail || '删除失败');
  }
}

async function saveUser() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editingUser.value) {
        await usersStore.updateUser(editingUser.value.id, {
          name: form.name, email: form.email, role: form.role,
          ...(form.password ? { password: form.password } : {}),
        });
        ElMessage.success('用户已更新');
      } else {
        await usersStore.createUser({ name: form.name, email: form.email, password: form.password, role: form.role });
        ElMessage.success('用户已创建');
      }
      showCreateUser.value = false;
      editingUser.value = null;
      form.name = ''; form.email = ''; form.password = ''; form.role = 'MEMBER';
    } catch { ElMessage.error('保存失败'); }
    finally { saving.value = false; }
  });
}

onMounted(() => fetchUsers());
</script>

<style scoped>
.users-page {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.users-table-section {
  overflow: hidden;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: var(--color-neutral-200);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  margin: 0;
}

.user-email {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.status-badge.active {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.external {
  background: var(--color-neutral-100);
  color: var(--color-text-secondary);
}

.date-text {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}

.w-full { width: 100%; }
</style>
