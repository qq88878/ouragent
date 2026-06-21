import { createRouter, createWebHistory } from 'vue-router';
import MistakeBookView from '@/views/MistakeBookView.vue';

const ChatView = () => import('@/views/ChatView.vue');

const routes = [
  { path: '/', redirect: '/dashboard' },
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
    path: '/chat',
    name: 'Chat',
    component: ChatView,
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:sessionId',
    name: 'ChatSession',
    component: ChatView,
    meta: { requiresAuth: true },
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/views/CourseView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/courses/:id',
    name: 'CourseDetail',
    component: () => import('@/views/CourseDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/mistake-book',
    name: 'MistakeBook',
    component: MistakeBookView,
    meta: { requiresAuth: true },
  },
  {
    path: '/learning',
    name: 'Learning',
    component: () => import('@/views/LearningView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/KnowledgeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: () => import('@/views/UserProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/views/ScheduleView.vue'),
    meta: { requiresAuth: true, requiresStudent: true },
  },
  {
    path: '/admin', name: 'Admin', meta: { requiresAuth: true, requiresAdmin: true },
    component: () => import('@/views/AdminView.vue'),
  },
  {
    path: '/admin/users', name: 'UserManagement', meta: { requiresAuth: true, requiresAdmin: true },
    component: () => import('@/views/UserManagementView.vue'),
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
