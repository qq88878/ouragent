<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h2>欢迎回来{{ user ? '，' + user.username : '' }}</h2>
      <el-button type="danger" @click="handleLogout">退出登录</el-button>
    </div>
    <el-card v-if="user" style="max-width: 600px">
      <template #header>用户信息</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ user.role || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-skeleton v-else :rows="5" animated style="max-width: 600px" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';

const router = useRouter();
const authStore = useAuthStore();
const user = ref(null);

onMounted(async () => {
  const res = await authStore.fetchUser();
  if (res && res.code === 200) user.value = res.data;
});

async function handleLogout() {
  await authStore.logout();
  ElMessage.success('已退出登录');
  router.push('/login');
}
</script>
