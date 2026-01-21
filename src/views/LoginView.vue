<template>
  <div class="min-h-screen bg-zinc-100 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-xl shadow-lg p-8">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-zinc-900">TCGS 课题治理系统</h1>
          <p class="text-zinc-500 mt-2">Topic & Capacity Governance System</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              type="email"
              placeholder="请输入邮箱"
              size="large"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
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
            登录
          </el-button>
        </el-form>

        <div class="mt-6 p-4 bg-zinc-50 rounded-lg">
          <p class="text-xs text-zinc-500 mb-2">演示账号:</p>
          <div class="space-y-1 text-xs text-zinc-600">
            <p><strong>管理员:</strong> admin@tcgs.com / admin123</p>
            <p><strong>算法成员:</strong> member@tcgs.com / member123</p>
            <p><strong>需求方:</strong> pdt@tcgs.com / pdt123</p>
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
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
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
        ElMessage.success('欢迎回来！');
        router.push('/dashboard');
      } else {
        ElMessage.error('登录失败，请检查账号密码');
      }
    } catch (error) {
      ElMessage.error('登录失败，请重试');
    } finally {
      loading.value = false;
    }
  });
}
</script>
