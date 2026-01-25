<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1 class="login-title">TCGS 课题治理系统</h1>
          <p class="login-subtitle">Topic & Capacity Governance System</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" type="email" placeholder="请输入邮箱" size="large" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password />
          </el-form-item>

          <el-button type="primary" size="large" class="login-btn" :loading="loading" native-type="submit">
            登录
          </el-button>
        </el-form>

        <div class="demo-accounts">
          <p class="demo-title">演示账号:</p>
          <div class="demo-list">
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

const form = reactive({ email: '', password: '' });

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

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg-base);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  box-shadow: var(--shadow-md);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.login-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.login-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-2) 0 0 0;
}

.login-btn {
  width: 100%;
  margin-top: var(--space-4);
}

.demo-accounts {
  margin-top: var(--space-6);
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}

.demo-title {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-2) 0;
}

.demo-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.demo-list strong {
  color: var(--color-text-primary);
}
</style>
