<template>
  <div class="algo-platform-page">
    <div class="page-header">
      <router-link to="/capability-shelf" class="back-link">
        <el-button :icon="Back">返回能力货架</el-button>
      </router-link>
      <h1 class="page-title">算法中台演示</h1>
    </div>

    <div class="iframe-container">
      <iframe
        :src="algPlatformUrl"
        frameborder="0"
        allow="clipboard-read; clipboard-write"
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Back } from '@element-plus/icons-vue';

// alg项目的Flask服务地址
const algPlatformUrl = 'http://localhost:5001';
</script>

<style scoped>
.algo-platform-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-base);
}

.page-header {
  padding: var(--space-4) var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-elevated);
  flex-shrink: 0;
}

.back-link {
  text-decoration: none;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.iframe-container {
  flex: 1;
  overflow: hidden;
}

.iframe-container iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
