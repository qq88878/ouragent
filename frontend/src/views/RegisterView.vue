<template>
  <div class="auth-page">
    <div class="auth-bg"></div>
    <el-card class="auth-card">
      <h2 class="auth-title">创建账户</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleRegister">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3-20个字符" maxlength="20" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="选填" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少6个字符" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="学生" value="STUDENT" />
            <el-option label="教师" value="TEACHER" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="success" :loading="loading" native-type="submit" style="width:100%">
            {{ loading ? '注册中...' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">已有账户？<router-link to="/login">点击登录</router-link></div>
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
const form = reactive({ username: '', nickname: '', email: '', password: '', confirmPassword: '', role: 'STUDENT' });

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'));
  else callback();
};

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名3-20个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
};

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  try {
    const res = await authStore.register({
      username: form.username,
      nickname: form.nickname || form.username,
      email: form.email,
      password: form.password,
      role: form.role,
    });
    if (res.code === 200) {
      ElMessage.success('注册成功！请登录');
      router.push('/login');
    } else {
      ElMessage.error(res.message || '注册失败');
    }
  } catch {
    ElMessage.error('无法连接服务器');
  } finally { loading.value = false; }
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); position: relative; }
.auth-bg { position: absolute; inset: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }
.auth-card { width: 420px; z-index: 1; border-radius: 12px; }
.auth-title { text-align: center; color: #303133; margin-bottom: 24px; }
.auth-footer { text-align: center; margin-top: 16px; font-size: 13px; color: #909399; }
.auth-footer a { color: #67c23a; }
</style>
