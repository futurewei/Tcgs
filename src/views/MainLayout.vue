<template>
  <div class="min-h-screen bg-zinc-50">
    <!-- TopBar -->
    <header class="fixed top-0 left-0 right-0 h-14 bg-white border-b border-zinc-200 z-50 flex items-center px-4">
      <div class="flex items-center gap-4">
        <button
          @click="sideNavCollapsed = !sideNavCollapsed"
          class="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
        >
          <el-icon :size="20"><Menu /></el-icon>
        </button>
        <h1 class="text-lg font-semibold text-zinc-900">TCGS</h1>
      </div>

      <div class="flex-1 flex items-center justify-center max-w-md mx-auto">
        <el-input
          v-model="searchQuery"
          placeholder="Search topics by title or ID..."
          class="w-full"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="flex items-center gap-3">
        <el-button
          v-if="authStore.isAdmin && !authStore.isCustomer"
          type="primary"
          @click="showCreateTopic = true"
        >
          New Topic
        </el-button>

        <el-dropdown trigger="click">
          <div class="flex items-center gap-2 cursor-pointer p-2 hover:bg-zinc-100 rounded-lg">
            <div class="w-8 h-8 bg-zinc-300 rounded-full flex items-center justify-center text-sm font-medium text-zinc-700">
              {{ userInitials }}
            </div>
            <span class="text-sm text-zinc-700">{{ authStore.user?.name }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <span class="text-xs text-zinc-500">{{ authStore.user?.role }}</span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon class="mr-2"><SwitchButton /></el-icon>
                Logout
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- SideNav -->
    <aside
      :class="[
        'fixed top-14 left-0 bottom-0 bg-white border-r border-zinc-200 transition-all duration-300 z-40',
        sideNavCollapsed ? 'w-16' : 'w-60'
      ]"
    >
      <nav class="p-2 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
            isActive(item.path)
              ? 'bg-zinc-900 text-white'
              : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
          ]"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <span v-if="!sideNavCollapsed" class="text-sm font-medium">{{ item.label }}</span>
        </router-link>

        <div v-if="authStore.isAdmin" class="pt-4 mt-4 border-t border-zinc-200">
          <p v-if="!sideNavCollapsed" class="px-3 py-2 text-xs font-medium text-zinc-400 uppercase">Admin</p>
          <router-link
            v-for="item in adminNavItems"
            :key="item.path"
            :to="item.path"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
              isActive(item.path)
                ? 'bg-zinc-900 text-white'
                : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
            ]"
          >
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
            <span v-if="!sideNavCollapsed" class="text-sm font-medium">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>
    </aside>

    <!-- Content Area -->
    <main
      :class="[
        'pt-14 transition-all duration-300',
        sideNavCollapsed ? 'pl-16' : 'pl-60'
      ]"
    >
      <div class="max-w-[1440px] mx-auto p-6">
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
  DataAnalysis,
  Document,
  User,
  Collection,
  Notebook,
  Setting,
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
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
});

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: DataAnalysis },
  { path: '/topics', label: 'Topics', icon: Document },
  { path: '/capacity', label: 'Capacity', icon: User },
  { path: '/wiki', label: 'Wiki', icon: Notebook },
  { path: '/templates', label: 'Stage Templates', icon: Collection },
  { path: '/insights', label: 'Insights / History', icon: Clock },
];

const adminNavItems = [
  { path: '/users', label: 'Users', icon: User },
  { path: '/audit-logs', label: 'Audit Log', icon: List },
];

function isActive(path: string) {
  if (path === '/dashboard') {
    return route.path === '/dashboard' || route.path === '/';
  }
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
