<template>
  <div class="capability-shelf-page">
    <div class="page-header">
      <h1 class="page-title">算法能力货架</h1>
      <p class="page-subtitle">管理和展示算法团队的核心能力资产</p>
    </div>

    <section class="tcgs-surface empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon"><Goods /></el-icon>
        <h3 class="empty-title">功能建设中</h3>
        <p class="empty-desc">算法能力货架功能正在开发中，敬请期待</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Goods } from '@element-plus/icons-vue';
</script>

<style scoped>
.capability-shelf-page {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-2) 0 0 0;
}

.empty-state {
  padding: var(--space-16) var(--space-6);
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-2) 0;
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}
</style>
