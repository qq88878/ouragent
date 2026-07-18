<template>
  <div v-if="isAuthPage" class="auth-wrapper">
    <router-view />
  </div>
  <el-container v-else class="app-layout">
    <el-aside width="240px" class="app-sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="36" height="36" rx="10" fill="url(#lg)"/>
            <path d="M18 8L26 14v10l-8 6-8-6V14l8-6z" fill="#FFF" opacity="0.92"/>
            <circle cx="18" cy="17" r="5" fill="url(#lg)"/>
            <defs><linearGradient id="lg" x1="0" y1="0" x2="36" y2="36"><stop stop-color="#C1783A"/><stop offset="1" stop-color="#B5651D"/></linearGradient></defs>
          </svg>
        </div>
        <span class="brand-text">EduAgent</span>
      </div>

      <div class="sidebar-nav">
        <div class="nav-section-label">主导航</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="rgba(255,255,255,0.65)"
          active-text-color="#fff"
        >
          <el-menu-item index="/dashboard">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><HomeFilled /></el-icon></div>
                <span>首页</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/chat">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><ChatDotRound /></el-icon></div>
                <span>智能对话</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/courses">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><Reading /></el-icon></div>
                <span>课程中心</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>

        <div v-if="isStudent" class="nav-section-label">学习工具</div>
        <el-menu
          v-if="isStudent"
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="rgba(255,255,255,0.65)"
          active-text-color="#fff"
        >
          <el-menu-item index="/schedule">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><Calendar /></el-icon></div>
                <span>课表</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/mistake-book">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><WarningFilled /></el-icon></div>
                <span>错题本</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/learning">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><TrendCharts /></el-icon></div>
                <span>学习路径</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>

        <div class="nav-section-label">知识管理</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="rgba(255,255,255,0.65)"
          active-text-color="#fff"
        >
          <el-menu-item index="/knowledge">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><Document /></el-icon></div>
                <span>知识库</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/profile">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><User /></el-icon></div>
                <span>个人资料</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>

        <div v-if="isAdmin" class="nav-section-label">系统管理</div>
        <el-menu
          v-if="isAdmin"
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="rgba(255,255,255,0.65)"
          active-text-color="#fff"
        >
          <el-menu-item index="/admin">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><Setting /></el-icon></div>
                <span>系统概览</span>
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <template #title>
              <div class="menu-item-inner">
                <div class="menu-icon-box"><el-icon :size="18"><Avatar /></el-icon></div>
                <span>用户管理</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="user-avatar">{{ (user?.nickname || user?.username || '?')[0] }}</div>
          <div class="user-detail">
            <div class="user-name">{{ user?.nickname || user?.username }}</div>
            <div class="user-role">{{ roleLabel }}</div>
          </div>
        </div>
      </div>
    </el-aside>

    <el-container class="main-area">
      <el-header class="app-header" height="60px">
        <div class="header-left">
          <div class="breadcrumb">
            <span class="breadcrumb-item">{{ pageTitle }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-button class="logout-btn" text @click="handleLogout">
            <el-icon :size="16"><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  HomeFilled, ChatDotRound, Reading, Calendar, WarningFilled,
  TrendCharts, Document, User, Setting, Avatar, SwitchButton
} from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const user = computed(() => authStore.user);

const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register';
});

const isStudent = computed(() => user.value?.role === 'STUDENT');
const isAdmin = computed(() => user.value?.role === 'ADMIN');

const roleLabel = computed(() => {
  switch (user.value?.role) { case 'ADMIN': return '管理员'; case 'TEACHER': return '教师'; case 'STUDENT': return '学生'; default: return ''; }
});

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/users')) return '/admin/users';
  if (route.path.startsWith('/admin')) return '/admin';
  if (route.path.startsWith('/chat')) return '/chat';
  if (route.path.startsWith('/courses')) return '/courses';
  if (route.path.startsWith('/schedule')) return '/schedule';
  if (route.path.startsWith('/mistake-book')) return '/mistake-book';
  if (route.path.startsWith('/learning')) return '/learning';
  if (route.path.startsWith('/knowledge')) return '/knowledge';
  if (route.path.startsWith('/profile')) return '/profile';
  return '/dashboard';
});

const pageTitles = {
  '/dashboard': '首页',
  '/chat': '智能对话',
  '/courses': '课程中心',
  '/schedule': '课表',
  '/mistake-book': '错题本',
  '/learning': '学习路径',
  '/knowledge': '知识库',
  '/profile': '个人资料',
  '/admin': '管理后台',
  '/admin/users': '用户管理',
};
const pageTitle = computed(() => {
  for (const [path, title] of Object.entries(pageTitles)) {
    if (route.path.startsWith(path)) return title;
  }
  if (route.path.startsWith('/courses/')) return '课程详情';
  if (route.path.startsWith('/chat/')) return '智能对话';
  return 'EduAgent';
});

onMounted(async () => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    await authStore.fetchUser();
  }
});

async function handleLogout() {
  await authStore.logout();
  router.push('/login');
}
</script>

<style>
.app-layout { height: 100vh; overflow: hidden; }

.app-sidebar {
  background: linear-gradient(180deg, #1E1610 0%, #241C15 50%, #2A2018 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: none;
  width: 240px !important;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.brand-icon svg { width: 36px; height: 36px; display: block; }
.brand-text {
  font-size: 20px;
  font-weight: 700;
  color: #F0E6D8;
  letter-spacing: -0.02em;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}
.nav-section-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,255,255,0.25);
  padding: 16px 24px 6px;
}

.app-sidebar .el-menu {
  border-right: none;
  padding: 0 12px;
}
.app-sidebar .el-menu-item {
  height: 44px;
  line-height: 44px;
  margin: 2px 0;
  border-radius: 10px;
  padding: 0 12px !important;
  font-size: 14px;
  transition: all 0.2s ease;
}
.app-sidebar .el-menu-item:hover {
  background: rgba(255,255,255,0.04) !important;
}
.app-sidebar .el-menu-item.is-active {
  background: rgba(181,101,29,0.30) !important;
  color: #F0E6D8 !important;
}
.app-sidebar .el-menu-item.is-active .menu-icon-box {
  background: var(--color-primary);
}
.menu-item-inner {
  display: flex;
  align-items: center;
  gap: 10px;
}
.menu-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.06);
  transition: background 0.2s ease;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #C1783A, #B5651D);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-detail {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  color: #F0E6D8;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-role {
  font-size: 11px;
  color: rgba(255,255,255,0.35);
  margin-top: 1px;
}

.main-area { background: var(--color-bg); }

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 28px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
}
.header-left { display: flex; align-items: center; }
.breadcrumb { display: flex; align-items: center; }
.breadcrumb-item {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logout-btn {
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 6px 10px;
  border-radius: var(--radius-md);
}
.logout-btn:hover {
  color: var(--color-danger);
  background: var(--color-danger-light);
}

.app-main {
  padding: 24px 28px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.auth-wrapper {
  min-height: 100vh;
  background: var(--color-bg);
}
</style>
