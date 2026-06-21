<template>
  <div class="auth-page login-bg">
    <div class="auth-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>
    <div class="auth-container">
      <div class="auth-left">
        <div class="auth-brand">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-logo">
            <rect width="48" height="48" rx="14" fill="url(#lg2)"/>
            <path d="M24 11l10 7.5v13L24 39l-10-7.5v-13L24 11z" fill="#FFF" opacity="0.95"/>
            <circle cx="24" cy="23" r="7" fill="url(#lg2)"/>
            <defs><linearGradient id="lg2" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#C1783A"/><stop offset="1" stop-color="#B5651D"/></linearGradient></defs>
          </svg>
          <h1>EduAgent</h1>
          <p>基于大模型的个性化学习系统</p>
        </div>
      </div>
      <div class="auth-right">
        <el-card class="auth-card" shadow="never">
          <div class="auth-header">
            <h2>欢迎回来</h2>
            <p>登录您的账户以继续学习</p>
          </div>
          <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                show-password
                size="large"
                :prefix-icon="Lock"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                native-type="submit"
                size="large"
                class="submit-btn"
              >
                {{ loading ? '登录中...' : '登录' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="demo-section">
            <p class="demo-title">测试账号（点击快速填充）</p>
            <div class="demo-buttons">
              <el-button size="small" class="demo-btn admin" plain @click="fill('admin')">
                <span class="demo-dot admin-dot"></span>管理员
              </el-button>
              <el-button size="small" class="demo-btn teacher" plain @click="fill('teacher')">
                <span class="demo-dot teacher-dot"></span>教师
              </el-button>
              <el-button size="small" class="demo-btn student" plain @click="fill('student')">
                <span class="demo-dot student-dot"></span>学生
              </el-button>
            </div>
            <p class="demo-hint">密码统一：123456</p>
          </div>

          <div class="auth-footer">
            <span>还没有账户？</span>
            <router-link to="/register">创建账户</router-link>
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
import { User, Lock } from '@element-plus/icons-vue';

const router = useRouter();
const authStore = useAuthStore();
const formRef = ref(null);
const loading = ref(false);
const form = reactive({ username: '', password: '' });
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

const particleStyle = (i) => ({
  left: `${(i * 17 + 3) % 100}%`,
  top: `${(i * 23 + 7) % 100}%`,
  animationDelay: `${(i * 0.7) % 8}s`,
  animationDuration: `${6 + (i % 5) * 2}s`,
  width: `${3 + (i % 4)}px`,
  height: `${3 + (i % 4)}px`,
});

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
.login-bg {
  background: linear-gradient(160deg, #1A1510 0%, #241C15 45%, #2B1F14 100%);
  display: flex; align-items: center; justify-content: center;
}

.auth-particles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.particle {
  position: absolute; border-radius: 50%;
  background: rgba(197,140,70,0.10);
  animation: floatUp 8s infinite ease-in-out;
}
@keyframes floatUp {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.25; }
  50% { transform: translateY(-50px) scale(1.6); opacity: 0.04; }
}

.auth-container {
  position: relative; z-index: 1; display: flex;
  width: 960px; max-width: 96vw; min-height: 580px;
  border-radius: 24px; overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.40);
  background: rgba(255,250,245,0.015);
  backdrop-filter: blur(28px);
  border: 1px solid rgba(255,255,255,0.05);
}

.auth-left {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 56px 48px;
  background: linear-gradient(160deg, rgba(181,101,29,0.14), rgba(197,140,70,0.05));
}
.auth-brand { text-align: center; }
.brand-logo { width: 72px; height: 72px; margin-bottom: 24px; filter: drop-shadow(0 8px 24px rgba(181,101,29,0.25)); }
.auth-brand h1 {
  font-size: 32px; font-weight: 700; color: #F0E6D8;
  margin-bottom: 10px; letter-spacing: -0.02em;
}
.auth-brand p {
  font-size: 15px; color: rgba(240,230,216,0.40); line-height: 1.7;
  max-width: 260px; margin: 0 auto;
}

.auth-right {
  flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px;
}
.auth-card {
  width: 100%; max-width: 380px;
  background: rgba(255,255,255,0.96) !important;
  backdrop-filter: blur(20px); border-radius: 20px !important; padding: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08) !important;
}
.auth-card :deep(.el-card__body) { padding: 32px 28px; }

.auth-header { text-align: center; margin-bottom: 32px; }
.auth-header h2 { font-size: 24px; font-weight: 700; color: var(--color-text); margin-bottom: 8px; letter-spacing: -0.01em; }
.auth-header p { font-size: 14px; color: var(--color-text-muted); }

.submit-btn { width: 100%; border-radius: 12px !important; height: 48px; font-size: 16px; font-weight: 600; margin-top: 4px; }

.demo-section { margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--color-border); text-align: center; }
.demo-title { font-size: 12px; color: var(--color-text-muted); margin-bottom: 14px; font-weight: 500; }
.demo-buttons { display: flex; gap: 10px; justify-content: center; }
.demo-btn { border-radius: 24px !important; font-size: 13px; padding: 6px 20px !important; }
.demo-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.admin-dot { background: #C44B4B; }
.teacher-dot { background: #C1803A; }
.student-dot { background: #5B8C5A; }
.demo-hint { font-size: 11px; color: var(--color-text-placeholder); margin-top: 10px; }

.auth-footer { text-align: center; margin-top: 24px; font-size: 14px; color: var(--color-text-muted); }
.auth-footer a { color: var(--color-primary); font-weight: 600; text-decoration: none; margin-left: 6px; }
.auth-footer a:hover { text-decoration: underline; }
</style>