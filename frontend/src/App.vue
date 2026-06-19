<template>
  <div v-if="isAuthPage">
    <router-view />
  </div>
  <el-container v-else class="app-layout">
    <el-aside width="200px" class="app-sidebar">
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
    <el-container>
      <el-header class="app-header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <el-tag :type="roleTagType" size="small" style="margin-right: 8px;">{{ roleLabel }}</el-tag>
          <span class="user-info">{{ userDisplay }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  HomeFilled, ChatDotRound, Reading, TrendCharts,
  Document, User, Setting, Avatar, Calendar, WarningFilled,
} from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();


const isAuthPage = computed(() => ['/login', '/register'].includes(route.path));
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isTeacherOrAdmin = computed(() => authStore.user?.role === 'TEACHER' || authStore.user?.role === 'ADMIN');
const isStudent = computed(() => authStore.user?.role === 'STUDENT');
const userDisplay = computed(() => authStore.user?.nickname || authStore.user?.username || '');

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
  return 'EduAgent';
});

onMounted(async () => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    const res = await authStore.fetchUser();
    if (res?.code === 200) { /* user stored in authStore */ }
  }
});

async function handleLogout() {
  await authStore.logout();
  router.push('/login');
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.app-layout { height: 100vh; }
.app-sidebar {
  background-color: #304156;
  overflow-y: auto;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #3a4a5a;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.page-title { font-size: 18px; font-weight: 600; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user-info { color: #606266; font-size: 14px; }
.app-main { background: #f5f7fa; padding: 20px; }
</style>