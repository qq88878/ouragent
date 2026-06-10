<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h2>欢迎回来{{ user ? '，' + user.username : '' }}</h2>
      <el-button type="danger" @click="handleLogout">退出登录</el-button>
    </div>

    <el-alert
      v-if="user && !authStore.emailVerified"
      title="邮箱未验证"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px; max-width: 600px;"
    >
      <template #default>
        <p style="margin-bottom: 8px;">您的邮箱 {{ user.email }} 尚未验证，部分功能可能受限。</p>
        <el-button type="primary" size="small" @click="showVerifyDialog = true">立即验证</el-button>
      </template>
    </el-alert>

    <div class="dashboard-nav" style="margin-bottom: 20px; display: flex; gap: 12px;">
      <el-button type="primary" @click="$router.push('/profile')">编辑资料</el-button>
      <el-button v-if="isAdmin" type="warning" @click="$router.push('/admin/users')">用户管理</el-button>
    </div>

    <el-card v-if="user" style="max-width: 600px">
      <template #header>用户信息</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ user.role || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱状态">
          <el-tag :type="authStore.emailVerified ? 'success' : 'warning'" size="small">
            {{ authStore.emailVerified ? '已验证' : '未验证' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-skeleton v-else :rows="5" animated style="max-width: 600px" />

    <el-dialog v-model="showVerifyDialog" title="邮箱验证" width="400px" :close-on-click-modal="false">
      <p style="margin-bottom: 12px; color: #606266;">验证码已发送至 <b>{{ user?.email }}</b></p>
      <el-form @submit.prevent="handleVerify">
        <el-form-item>
          <el-input
            v-model="verifyCode"
            placeholder="请输入6位验证码"
            maxlength="6"
            style="letter-spacing: 4px; font-size: 18px; text-align: center;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="verifying" native-type="submit" style="width: 100%;">
            {{ verifying ? '验证中...' : '验 证' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center;">
        <el-button text type="primary" :disabled="resendCooldown > 0" @click="handleResend">
          {{ resendCooldown > 0 ? `${resendCooldown}秒后重发` : '重新发送验证码' }}
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { authApi } from '@/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const authStore = useAuthStore();
const user = ref(null);

const showVerifyDialog = ref(false);
const verifyCode = ref('');
const verifying = ref(false);
const resendCooldown = ref(0);

const isAdmin = computed(() => {
  return user.value && (user.value.role === 'ADMIN' || user.value.role === 'TEACHER');
});

onMounted(async () => {
  const res = await authStore.fetchUser();
  if (res && res.code === 200) user.value = res.data;
});

async function handleLogout() {
  await authStore.logout();
  ElMessage.success('已退出登录');
  router.push('/login');
}

async function handleVerify() {
  if (!verifyCode.value || verifyCode.value.length !== 6) {
    ElMessage.warning('请输入6位验证码');
    return;
  }
  verifying.value = true;
  try {
    const res = await authApi.verifyEmail(user.value.email, verifyCode.value);
    if (res.code === 200) {
      authStore.emailVerified = true;
      authStore.fetchUser();
      showVerifyDialog.value = false;
      ElMessage.success('邮箱验证成功！');
    } else {
      ElMessage.error(res.message || '验证失败');
    }
  } catch {
    ElMessage.error('验证失败');
  } finally {
    verifying.value = false;
  }
}

async function handleResend() {
  try {
    const res = await authApi.sendVerifyCode(user.value.email);
    if (res.code === 200) {
      ElMessage.success('验证码已重新发送');
      resendCooldown.value = 60;
      const timer = setInterval(() => {
        resendCooldown.value--;
        if (resendCooldown.value <= 0) clearInterval(timer);
      }, 1000);
    } else {
      ElMessage.error(res.message || '发送失败');
    }
  } catch {
    ElMessage.error('发送失败');
  }
}
</script>