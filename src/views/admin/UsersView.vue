<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-zinc-900">User Management</h1>
      <el-button type="primary" @click="showCreateUser = true">
        New User
      </el-button>
    </div>

    <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="User" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-zinc-200 rounded-full flex items-center justify-center text-sm font-medium">
                {{ getInitials(row.name) }}
              </div>
              <div>
                <p class="font-medium text-zinc-900">{{ row.name }}</p>
                <p class="text-sm text-zinc-500">{{ row.email }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Role" width="150">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              size="small"
              @change="(val: string) => updateRole(row, val)"
            >
              <el-option value="ADMIN" label="Admin" />
              <el-option value="MEMBER" label="Member" />
              <el-option value="REVIEWER" label="Reviewer" />
              <el-option value="EXTERNAL" label="External" />
	      <el-option value="CUSTOMER" label="Customer" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'EXTERNAL' ? 'info' : 'success'" size="small">
              {{ row.role === 'EXTERNAL' ? 'External' : 'Active' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Created" width="150">
          <template #default="{ row }">
            <span class="text-sm text-zinc-500">{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="100" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click">
              <el-button size="small" text>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="editUser(row)">Edit</el-dropdown-item>
                  <el-dropdown-item @click="deleteUser(row)">Delete</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div class="p-4 border-t border-zinc-100 flex justify-center">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="usersStore.pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>
    </div>

    <!-- Create/Edit User Dialog -->
    <el-dialog
      v-model="showCreateUser"
      :title="editingUser ? 'Edit User' : 'Create User'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Full name" />
        </el-form-item>
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" type="email" placeholder="Email address" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="Password" prop="password">
          <el-input v-model="form.password" type="password" placeholder="Password" show-password />
        </el-form-item>
        <el-form-item label="Role" prop="role">
          <el-select v-model="form.role" class="w-full">
            <el-option value="ADMIN" label="Admin" />
            <el-option value="MEMBER" label="Member" />
            <el-option value="REVIEWER" label="Reviewer" />
            <el-option value="EXTERNAL" label="External" />
	    <el-option value="CUSTOMER" label="Customer" />
          </el-select>
          <p v-if="form.role === 'EXTERNAL'" class="text-xs text-amber-600 mt-1">
            External users cannot be assigned as DRI
          </p>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateUser = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">
          {{ editingUser ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useUsersStore } from '@/stores/users';
import { MoreFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import dayjs from 'dayjs';
import type { User, UserRole } from '@/types';

const usersStore = useUsersStore();

const showCreateUser = ref(false);
const editingUser = ref<User | null>(null);
const saving = ref(false);
const formRef = ref<FormInstance>();

const pagination = reactive({
  page: 1,
  pageSize: 20,
});

const form = reactive({
  name: '',
  email: '',
  password: '',
  role: 'MEMBER' as UserRole,
});

const rules: FormRules = {
  name: [{ required: true, message: 'Please enter name', trigger: 'blur' }],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter valid email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur', validator: (rule, value, callback) => {
      if (!editingUser.value && !value) {
        callback(new Error('Please enter password'));
      } else {
        callback();
      }
    }},
  ],
  role: [{ required: true, message: 'Please select role', trigger: 'change' }],
};

const users = computed(() => usersStore.users);
const loading = computed(() => usersStore.loading);

function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(date: string) {
  return dayjs(date).format('MMM D, YYYY');
}

function fetchUsers() {
  usersStore.fetchUsers(pagination.page, pagination.pageSize);
}

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
    ElMessage.success('Role updated');
  } catch (error) {
    ElMessage.error('Failed to update role');
  }
}

async function deleteUser(user: User) {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this user?',
      'Delete User',
      { type: 'warning' }
    );
    await usersStore.deleteUser(user.id);
    ElMessage.success('User deleted');
  } catch (error) {
    // Cancelled
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
          name: form.name,
          email: form.email,
          role: form.role,
          ...(form.password ? { password: form.password } : {}),
        });
        ElMessage.success('User updated');
      } else {
        await usersStore.createUser({
          name: form.name,
          email: form.email,
          password: form.password,
          role: form.role,
        });
        ElMessage.success('User created');
      }

      showCreateUser.value = false;
      editingUser.value = null;
      form.name = '';
      form.email = '';
      form.password = '';
      form.role = 'MEMBER';
    } catch (error) {
      ElMessage.error('Failed to save user');
    } finally {
      saving.value = false;
    }
  });
}

onMounted(() => {
  fetchUsers();
});
</script>
