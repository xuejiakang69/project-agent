import { createRouter, createWebHistory } from 'vue-router'
import { readSession } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true, title: '登录' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true, title: '注册' },
    },
    {
      path: '/home',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '工作台', requiresAuth: true },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/UsersView.vue'),
          meta: { title: '用户管理', requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'orders',
          name: 'orders',
          component: () => import('@/views/ModuleView.vue'),
          props: { title: '订单中心', description: '订单查询、履约跟踪和售后处理将在这里完成。' },
          meta: { title: '订单中心', requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('@/views/ModuleView.vue'),
          props: { title: '数据分析', description: '核心指标、趋势分析和经营报表将在这里呈现。' },
          meta: { title: '数据分析', requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/ModuleView.vue'),
          props: { title: '系统设置', description: '组织配置、安全策略和通知设置将在这里维护。' },
          meta: { title: '系统设置', requiresAuth: true, requiresAdmin: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/home',
    },
  ],
})

router.beforeEach((to) => {
  const user = readSession()

  if (to.meta.requiresAuth && !user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && user?.role !== 'admin') {
    return { name: 'dashboard' }
  }

  if (to.meta.guestOnly && user) {
    return { name: 'dashboard' }
  }

  document.title = to.meta.title ? `${to.meta.title} · 智能实验室预约系统` : '智能实验室预约系统'
})

export default router
