<template>
  <div class="auth-page register-bg">
    <div class="auth-particles">
      <div v-for="i in 16" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>
    <div class="auth-container">
      <div class="auth-left">
        <div class="auth-brand">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-logo">
            <rect width="48" height="48" rx="14" fill="url(#rg)"/>
            <path d="M24 11l10 7.5v13L24 39l-10-7.5v-13L24 11z" fill="#FFF" opacity="0.95"/>
            <circle cx="24" cy="23" r="7" fill="url(#rg)"/>
            <defs><linearGradient id="rg" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#6B8C5A"/><stop offset="1" stop-color="#5B8C5A"/></linearGradient></defs>
          </svg>
          <h1>加入 EduAgent</h1>
          <p>开启你的智能学习之旅</p>
        </div>
      </div>
      <div class="auth-right">
        <el-card class="auth-card" shadow="never">
          <div class="auth-header">
            <h2>创建账户</h2>
            <p>填写信息开始使用</p>
          </div>
          <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleRegister">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名（3-20个字符）" maxlength="20" size="large" :prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="nickname">
              <el-input v-model="form.nickname" placeholder="昵称（选填）" maxlength="20" size="large" :prefix-icon="EditPen" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="邮箱" size="large" :prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码（至少6个字符）" show-password size="large" :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password size="large" :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item prop="role">
              <el-select v-model="form.role" placeholder="选择角色" size="large" style="width: 100%" :prefix-icon="Avatar">
                <el-option label="🎓 学生" value="STUDENT" />
                <el-option label="📚 教师" value="TEACHER" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" native-type="submit" size="large" class="submit-btn">
                {{ loading ? '注册中...' : '创建账户' }}
              </el-button>
            </el-form-item>
          </el-form>
          <div class="auth-footer">
            <span>已有账户？</span>
            <router-link to="/login">去登录</router-link>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';
import { User, Lock, Message, EditPen, Avatar } from '@element-plus/icons-vue';

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

const particleStyle = (i) => ({
  left: `${(i * 19 + 5) % 100}%`,
  top: `${(i * 27 + 3) % 100}%`,
  animationDelay: `${(i * 0.6) % 6}s`,
  animationDuration: `${7 + (i % 4) * 2}s`,
  width: `${3 + (i % 4)}px`,
  height: `${3 + (i % 4)}px`,
});

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
.register-bg {
  background: linear-gradient(160deg, #141910 0%, #1A1F18 45%, #1A2218 100%);
  display: flex; align-items: center; justify-content: center;
}

.auth-particles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.particle {
  position: absolute; border-radius: 50%;
  background: rgba(107,140,90,0.10);
  animation: floatUp 8s infinite ease-in-out;
}
@keyframes floatUp {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.25; }
  50% { transform: translateY(-50px) scale(1.6); opacity: 0.04; }
}

.auth-container {
  position: relative; z-index: 1; display: flex;
  width: 980px; max-width: 96vw; min-height: 640px;
  border-radius: 24px; overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.40);
  background: rgba(255,250,245,0.015);
  backdrop-filter: blur(28px);
  border: 1px solid rgba(255,255,255,0.05);
}

.auth-left {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 56px 48px;
  background: linear-gradient(160deg, rgba(91,140,90,0.12), rgba(107,140,90,0.04));
}
.auth-brand { text-align: center; }
.brand-logo { width: 72px; height: 72px; margin-bottom: 24px; filter: drop-shadow(0 8px 24px rgba(91,140,90,0.25)); }
.auth-brand h1 {
  font-size: 32px; font-weight: 700; color: #EBF2E8;
  margin-bottom: 10px; letter-spacing: -0.02em;
}
.auth-brand p {
  font-size: 15px; color: rgba(235,242,232,0.40); line-height: 1.7;
  max-width: 260px; margin: 0 auto;
}

.auth-right {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 32px; overflow-y: auto;
}
.auth-card {
  width: 100%; max-width: 400px;
  background: rgba(255,255,255,0.96) !important;
  backdrop-filter: blur(20px); border-radius: 20px !important; padding: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08) !important;
}
.auth-card :deep(.el-card__body) { padding: 28px 32px; }

.auth-header { text-align: center; margin-bottom: 28px; }
.auth-header h2 { font-size: 24px; font-weight: 700; color: var(--color-text); margin-bottom: 8px; letter-spacing: -0.01em; }
.auth-header p { font-size: 14px; color: var(--color-text-muted); }

.submit-btn { width: 100%; border-radius: 12px !important; height: 48px; font-size: 16px; font-weight: 600; margin-top: 4px; }

.auth-footer { text-align: center; margin-top: 24px; font-size: 14px; color: var(--color-text-muted); }
.auth-footer a { color: var(--color-success); font-weight: 600; text-decoration: none; margin-left: 6px; }
.auth-footer a:hover { text-decoration: underline; }
</style>