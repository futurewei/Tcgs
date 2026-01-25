<template>
  <div class="tcgs-layout">
    <!-- TopBar -->
    <header class="tcgs-topbar">
      <div class="tcgs-topbar-left">
        <button @click="sideNavCollapsed = !sideNavCollapsed" class="tcgs-topbar-toggle">
          <el-icon :size="18"><Menu /></el-icon>
        </button>
        <div class="tcgs-brand">
          <span class="tcgs-brand-text">TCGS</span>
          <span class="tcgs-brand-divider"></span>
          <span class="tcgs-brand-subtitle">课题治理系统</span>
        </div>
      </div>

      <div class="tcgs-topbar-center">
        <div class="tcgs-search">
          <el-icon class="tcgs-search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索课题、人员..."
            class="tcgs-search-input"
            @keyup.enter="handleSearch"
          />
          <kbd class="tcgs-search-shortcut">⌘K</kbd>
        </div>
      </div>

      <div class="tcgs-topbar-right">
        <el-button
          v-if="authStore.isAdmin && !authStore.isCustomer"
          class="tcgs-btn-create"
          @click="showCreateTopic = true"
        >
          <el-icon class="mr-1"><Plus /></el-icon>
          创建课题
        </el-button>

        <el-dropdown trigger="click" :teleported="true">
          <div class="tcgs-user-menu">
            <div class="tcgs-user-avatar">{{ userInitials }}</div>
            <div class="tcgs-user-info">
              <span class="tcgs-user-name">{{ authStore.user?.name }}</span>
              <span class="tcgs-user-role">{{ roleLabel }}</span>
            </div>
            <el-icon class="tcgs-user-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">
                <el-icon class="mr-2"><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- SideNav -->
    <aside :class="['tcgs-sidebar', { 'tcgs-sidebar--collapsed': sideNavCollapsed }]">
      <nav class="tcgs-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="['tcgs-nav-item', { 'tcgs-nav-item--active': isActive(item.path) }]"
        >
          <el-icon class="tcgs-nav-icon" :size="18"><component :is="item.icon" /></el-icon>
          <span v-if="!sideNavCollapsed" class="tcgs-nav-label">{{ item.label }}</span>
        </router-link>

        <div v-if="authStore.isAdmin" class="tcgs-nav-section">
          <span v-if="!sideNavCollapsed" class="tcgs-nav-section-title">系统管理</span>
          <router-link
            v-for="item in adminNavItems"
            :key="item.path"
            :to="item.path"
            :class="['tcgs-nav-item', { 'tcgs-nav-item--active': isActive(item.path) }]"
          >
            <el-icon class="tcgs-nav-icon" :size="18"><component :is="item.icon" /></el-icon>
            <span v-if="!sideNavCollapsed" class="tcgs-nav-label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <!-- Sidebar Footer -->
      <div v-if="!sideNavCollapsed" class="tcgs-sidebar-footer">
        <div class="tcgs-sidebar-version">v2.0</div>
      </div>
    </aside>

    <!-- Content Area -->
    <main :class="['tcgs-main', { 'tcgs-main--expanded': sideNavCollapsed }]">
      <div class="tcgs-content">
        <router-view />
      </div>
    </main>

    <!-- Create Topic Dialog -->
    <CreateTopicDialog v-model="showCreateTopic" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  Menu,
  Search,
  ArrowDown,
  SwitchButton,
  Plus,
  DataAnalysis,
  Document,
  User,
  Collection,
  Notebook,
  List,
  Clock
} from '@element-plus/icons-vue';
import CreateTopicDialog from '@/components/topic/CreateTopicDialog.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const sideNavCollapsed = ref(false);
const searchQuery = ref('');
const showCreateTopic = ref(false);

const userInitials = computed(() => {
  const name = authStore.user?.name || '';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?';
});

const roleLabels: Record<string, string> = {
  ADMIN: '管理员',
  MEMBER: '算法成员',
  REVIEWER: '评审员',
  EXTERNAL: '协调人力',
  CUSTOMER: '需求方',
};

const roleLabel = computed(() => roleLabels[authStore.user?.role || ''] || authStore.user?.role);

const navItems = [
  { path: '/dashboard', label: '工作台', icon: DataAnalysis },
  { path: '/topics', label: '课题管理', icon: Document },
  { path: '/capacity', label: '人力管理', icon: User },
  { path: '/wiki', label: '知识库', icon: Notebook },
  { path: '/templates', label: '流程模板', icon: Collection },
  { path: '/insights', label: '数据洞察', icon: Clock },
];

const adminNavItems = [
  { path: '/users', label: '用户管理', icon: User },
  { path: '/audit-logs', label: '操作日志', icon: List },
];

function isActive(path: string) {
  if (path === '/dashboard') return route.path === '/dashboard' || route.path === '/';
  return route.path.startsWith(path);
}

function handleSearch() {
  if (searchQuery.value) {
    router.push({ path: '/topics', query: { search: searchQuery.value } });
  }
}

function handleLogout() {
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════════
   LAYOUT STRUCTURE
   ══════════════════════════════════════════════════════════════ */
.tcgs-layout {
  min-height: 100vh;
  background: var(--color-bg-base);
}

/* ══════════════════════════════════════════════════════════════
   TOPBAR - 顶部导航
   ══════════════════════════════════════════════════════════════ */
.tcgs-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--topbar-height);
  background: var(--color-surface-primary);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  z-index: var(--z-fixed);
}

.tcgs-topbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.tcgs-topbar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tcgs-topbar-toggle:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

/* Brand */
.tcgs-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.tcgs-brand-text {
  font-size: var(--text-md);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  letter-spacing: var(--tracking-tight);
}

.tcgs-brand-divider {
  width: 1px;
  height: 14px;
  background: var(--color-border-default);
}

.tcgs-brand-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-weight: var(--font-medium);
}

/* Search */
.tcgs-topbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 420px;
  margin: 0 var(--space-6);
}

.tcgs-search {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
}

.tcgs-search-icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-muted);
  pointer-events: none;
  font-size: 14px;
}

.tcgs-search-input {
  width: 100%;
  height: 32px;
  padding: 0 60px 0 32px;
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-md);
  background: var(--color-surface-secondary);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  outline: none;
  transition: all var(--transition-fast);
}

.tcgs-search-input::placeholder {
  color: var(--color-text-muted);
}

.tcgs-search-input:focus {
  border-color: var(--color-primary-400);
  background: var(--color-surface-primary);
}

.tcgs-search-shortcut {
  position: absolute;
  right: 8px;
  padding: 2px 5px;
  font-size: 10px;
  font-family: var(--font-sans);
  color: var(--color-text-muted);
  background: var(--color-surface-primary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-sm);
}

/* Right Actions */
.tcgs-topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.tcgs-btn-create {
  height: 32px;
  padding: 0 var(--space-3);
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  border-radius: var(--radius-md) !important;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.tcgs-btn-create:hover {
  background: var(--color-primary-hover) !important;
  border-color: var(--color-primary-hover) !important;
}

/* User Menu */
.tcgs-user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.tcgs-user-menu:hover {
  background: var(--color-surface-hover);
}

.tcgs-user-avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-100);
  color: var(--color-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.tcgs-user-info {
  display: flex;
  flex-direction: column;
}

.tcgs-user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  line-height: 1.2;
}

.tcgs-user-role {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.tcgs-user-arrow {
  color: var(--color-text-muted);
  font-size: 12px;
}


/* ══════════════════════════════════════════════════════════════
   SIDEBAR - 侧边导航
   ══════════════════════════════════════════════════════════════ */
.tcgs-sidebar {
  position: fixed;
  top: var(--topbar-height);
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-surface-primary);
  border-right: 1px solid var(--color-border-subtle);
  transition: width var(--transition-slow);
  z-index: var(--z-sticky);
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

.tcgs-sidebar--collapsed {
  width: var(--sidebar-width-collapsed);
}

.tcgs-nav {
  flex: 1;
  padding: var(--space-3);
  overflow-y: auto;
}

.tcgs-nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  margin-bottom: 2px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.tcgs-nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.tcgs-nav-item--active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.tcgs-nav-item--active:hover {
  background: var(--color-primary-hover);
  color: var(--color-text-inverse);
}

.tcgs-nav-icon {
  flex-shrink: 0;
}

.tcgs-nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.tcgs-nav-section {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
}

.tcgs-nav-section-title {
  display: block;
  padding: var(--space-1) var(--space-3);
  margin-bottom: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.tcgs-sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
}

.tcgs-sidebar-version {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
}

/* ══════════════════════════════════════════════════════════════
   MAIN CONTENT
   ══════════════════════════════════════════════════════════════ */
.tcgs-main {
  padding-top: var(--topbar-height);
  padding-left: var(--sidebar-width);
  min-height: 100vh;
  transition: padding-left var(--transition-slow);
}

.tcgs-main--expanded {
  padding-left: var(--sidebar-width-collapsed);
}

.tcgs-content {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-6);
}
</style>
