import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/overview' },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/components/AppShell.vue'),
      children: [
        { path: 'overview', name: 'overview', component: () => import('@/views/OverviewView.vue') },
        { path: 'monitoring', name: 'monitoring', component: () => import('@/views/MonitoringView.vue') },
        { path: 'alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue') },
        { path: 'behaviors', name: 'behaviors', component: () => import('@/views/BehaviorsView.vue') },
        { path: 'analytics', name: 'analytics', component: () => import('@/views/AnalyticsView.vue') },
        { path: 'system', name: 'system', component: () => import('@/views/SystemView.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  if (!authStore.isBootstrapped) await authStore.bootstrap()

  if (to.meta.public) {
    if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) return { name: 'overview' }
    return true
  }

  if (!authStore.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
  return true
})

export default router

