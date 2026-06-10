import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: () => import('@/views/UserProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('@/views/UserManagementView.vue'),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('accessToken');
  if (to.meta.requiresAuth && !token) {
    next('/login');
  } else if (to.meta.guest && token) {
    next('/dashboard');
  } else {
    next();
  }
});

export default router;