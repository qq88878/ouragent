<template>
  <div class="auth-page">
    <div class="auth-bg"></div>
    <el-card class="auth-card">
      <h2 class="auth-title">EduAgent 登录</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" native-type="submit" size="large" style="width:100%">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="demo-accounts">
        <p class="demo-title">测试账号（点击快速填入）</p>
        <div class="demo-row">
          <el-button size="small" type="danger" plain @click="fill('admin')">管理员</el-button>
          <el-button size="small" type="warning" plain @click="fill('teacher')">教师</el-button>
          <el-button size="small" type="success" plain @click="fill('student')">学生</el-button>
        </div>
        <p class="demo-hint">密码统一：123456</p>
      </div>

      <div class="auth-footer">没有账户？<router-link to="/register">点击注册</router-link></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';

const router = useRouter();
const authStore = useAuthStore();
const formRef = ref(null);
const loading = ref(false);
const form = reactive({ username: '', password: '' });
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

function fill(role) { form.username = role; form.password = '123456'; }

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  try {
    const res = await authStore.login(form.username, form.password);
    if (res.code === 200) {
      ElMessage.success('登录成功');
      await authStore.fetchUser();
      router.push('/dashboard');
    } else {
      ElMessage.error(res.message || '用户名或密码错误');
    }
  } catch {
    ElMessage.error('无法连接服务器');
  } finally { loading.value = false; }
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); position: relative; }
.auth-bg { position: absolute; inset: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }
.auth-card { width: 400px; z-index: 1; border-radius: 12px; }
.auth-title { text-align: center; color: #303133; margin-bottom: 24px; }
.demo-accounts { margin-top: 16px; padding-top: 16px; border-top: 1px dashed #ebeef5; text-align: center; }
.demo-title { font-size: 12px; color: #909399; margin-bottom: 8px; }
.demo-row { display: flex; gap: 8px; justify-content: center; }
.demo-hint { font-size: 11px; color: #c0c4cc; margin-top: 6px; }
.auth-footer { text-align: center; margin-top: 16px; font-size: 13px; color: #909399; }
.auth-footer a { color: #409eff; }
</style>
