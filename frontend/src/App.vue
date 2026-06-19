<template>
  <div v-if="isAuthPage" class="auth-wrapper">
    <router-view />
  </div>
  <el-container v-else class="app-layout">
    <el-aside width="240px" class="app-sidebar">
      <div class="logo">EduAgent</div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能对话</span>
        </el-menu-item>
        <el-menu-item index="/courses">
          <el-icon><Reading /></el-icon>
          <span>课程中心</span>
        </el-menu-item>
        <el-menu-item v-if="isStudent" index="/schedule">
          <el-icon><Calendar /></el-icon>
          <span>课表</span>
        </el-menu-item>
        <el-menu-item v-if="isStudent" index="/mistake-book">
          <el-icon><WarningFilled /></el-icon>
          <span>错题本</span>
        </el-menu-item>
        <el-menu-item v-if="isStudent" index="/learning">
          <el-icon><TrendCharts /></el-icon>
          <span>学习路径</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>个人资料</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>管理后台</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin/users">
          <el-icon><Avatar /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-area">
      <el-header class="app-header">
        <div class="header-left">
          <div class="breadcrumb">
            <span class="breadcrumb-item">{{ pageTitle }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-tag :type="roleTagType" size="small" effect="plain" round>{{ roleLabel }}</el-tag>
          <el-divider direction="vertical" />
          <el-button text class="logout-btn" @click="handleLogout">
            <el-icon :size="16"><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  HomeFilled, ChatDotRound, Reading, TrendCharts,
  Document, User, Setting, Avatar, Calendar, WarningFilled, SwitchButton,
} from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const isAuthPage = computed(() => ['/login', '/register'].includes(route.path));
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isStudent = computed(() => authStore.user?.role === 'STUDENT');
const userDisplay = computed(() => authStore.user?.nickname || authStore.user?.username || '');
const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/users')) return '/admin/users';
  if (route.path.startsWith('/admin')) return '/admin';
  if (route.path.startsWith('/courses/')) return '/courses';
  if (route.path.startsWith('/chat/')) return '/chat';
  return route.path;
});

const roleLabel = computed(() => {
  switch (authStore.user?.role) {
    case 'ADMIN': return '管理员';
    case 'TEACHER': return '教师';
    case 'STUDENT': return '学生';
    default: return '';
  }
});
const roleTagType = computed(() => {
  switch (authStore.user?.role) {
    case 'ADMIN': return 'danger';
    case 'TEACHER': return 'warning';
    case 'STUDENT': return 'success';
    default: return 'info';
  }
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
/* === 布局 === */
.app-layout { height: 100vh; overflow: hidden; }

/* === 侧边栏 === */
.app-sidebar {
  background: linear-gradient(180deg, #1E2235 0%, #252A3E 100%);
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
  color: #fff;
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
  color: rgba(255,255,255,0.30);
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
  background: rgba(255,255,255,0.06) !important;
}
.app-sidebar .el-menu-item.is-active {
  background: rgba(91,106,240,0.25) !important;
  color: #fff !important;
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
  background: rgba(255,255,255,0.08);
  transition: background 0.2s ease;
}
.app-sidebar .el-menu-item.is-active .menu-icon-box {
  background: var(--color-primary);
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
  background: linear-gradient(135deg, #5B6AF0, #7C5CFC);
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
  color: #fff;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-role {
  font-size: 11px;
  color: rgba(255,255,255,0.45);
  margin-top: 1px;
}

/* === 主区域 === */
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
.header-right .el-divider--vertical {
  height: 16px;
  margin: 0 4px;
  border-color: var(--color-border);
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

/* === 内容区 === */
.app-main {
  padding: 24px 28px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

/* === 路由过渡动画 === */
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

/* === 认证页面容器 === */
.auth-wrapper {
  min-height: 100vh;
  background: var(--color-bg);
}
</style>
