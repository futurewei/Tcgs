import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/algo-platform',
    name: 'algo-platform',
    component: () => import('@/views/capability/AlgoPlatformView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/views/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
      },
      {
        path: 'topics',
        name: 'topics',
        component: () => import('@/views/topics/TopicsListView.vue'),
      },
      {
        path: 'topics/:id',
        name: 'topic-detail',
        component: () => import('@/views/topics/TopicDetailView.vue'),
      },
      {
        path: 'capacity',
        name: 'capacity',
        component: () => import('@/views/capacity/CapacityView.vue'),
      },
      {
        path: 'capability-shelf',
        name: 'capability-shelf',
        component: () => import('@/views/capability/CapabilityShelfView.vue'),
      },
      {
        path: 'responsibility-field',
        name: 'responsibility-field',
        component: () => import('@/views/responsibility/ResponsibilityFieldView.vue'),
      },
      {
        path: 'wiki',
        name: 'wiki',
        component: () => import('@/views/wiki/WikiView.vue'),
      },
      {
        path: 'wiki/directions/:id',
        name: 'wiki-direction',
        component: () => import('@/views/wiki/DirectionView.vue'),
      },
      {
        path: 'wiki/pages/:id',
        name: 'wiki-page',
        component: () => import('@/views/wiki/PageView.vue'),
      },
      {
        path: 'wiki/pages/:id/edit',
        name: 'wiki-page-edit',
        component: () => import('@/views/wiki/PageEditView.vue'),
      },
      {
        path: 'templates',
        name: 'templates',
        component: () => import('@/views/templates/TemplatesView.vue'),
      },
      {
        path: 'insights',
        name: 'insights',
        component: () => import('@/views/insights/InsightsView.vue'),
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'audit-logs',
        name: 'audit-logs',
        component: () => import('@/views/admin/AuditLogsView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'profile/user/:userId',
        name: 'user-profile',
        component: () => import('@/views/profile/ProfileView.vue'),
      },
      {
        path: 'profile/slot/:slotId',
        name: 'slot-profile',
        component: () => import('@/views/profile/ProfileView.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // If route requires auth and user is not authenticated
  if (to.meta.requiresAuth && !authStore.token) {
    return next('/login');
  }

  // If route is for guests only and user is authenticated
  if (to.meta.guest && authStore.token) {
    return next('/dashboard');
  }

  // If token exists but user not loaded, fetch user
  if (authStore.token && !authStore.user) {
    await authStore.fetchUser();
  }

  // If route requires admin and user is not admin
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/dashboard');
  }

  next();
});

export default router;
