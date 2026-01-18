<template>
  <div class="min-h-screen bg-zinc-100 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-xl shadow-lg p-8">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-zinc-900">TCGS</h1>
          <p class="text-zinc-500 mt-2">Topic & Capacity Governance System</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="Email" prop="email">
            <el-input
              v-model="form.email"
              type="email"
              placeholder="Enter your email"
              size="large"
            />
          </el-form-item>

          <el-form-item label="Password" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="Enter your password"
              size="large"
              show-password
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="w-full mt-4"
            :loading="loading"
            native-type="submit"
          >
            Sign In
          </el-button>
        </el-form>

        <div class="mt-6 p-4 bg-zinc-50 rounded-lg">
          <p class="text-xs text-zinc-500 mb-2">Demo Accounts:</p>
          <div class="space-y-1 text-xs text-zinc-600">
            <p><strong>Admin:</strong> admin@tcgs.local / admin123</p>
            <p><strong>Member:</strong> member@tcgs.local / member123</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';

const router = useRouter();
const authStore = useAuthStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  email: '',
  password: '',
});

const rules: FormRules = {
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter valid email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
};

async function handleLogin() {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      const success = await authStore.login(form.email, form.password);
      if (success) {
        ElMessage.success('Welcome back!');
        router.push('/dashboard');
      } else {
        ElMessage.error('Invalid credentials');
      }
    } catch (error) {
      ElMessage.error('Login failed. Please try again.');
    } finally {
      loading.value = false;
    }
  });
}
</script>
