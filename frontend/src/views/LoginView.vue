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
            <path d="M24 11l10 7.5v13L24 39l-10-7.5v-13L24 11z" fill="white" opacity="0.95"/>
            <circle cx="24" cy="23" r="7" fill="url(#lg2)"/>
            <defs><linearGradient id="lg2" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#5B6AF0"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs>
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
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
}

.auth-particles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.particle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  animation: floatUp 8s infinite ease-in-out;
}
@keyframes floatUp {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.3; }
  50% { transform: translateY(-40px) scale(1.5); opacity: 0.08; }
}

.auth-container {
  position: relative;
  z-index: 1;
  display: flex;
  width: 900px;
  max-width: 95vw;
  min-height: 560px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
}

.auth-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: linear-gradient(135deg, rgba(91,106,240,0.15), rgba(167,139,250,0.1));
}
.auth-brand {
  text-align: center;
}
.brand-logo { width: 64px; height: 64px; margin-bottom: 20px; }
.auth-brand h1 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}
.auth-brand p {
  font-size: 14px;
  color: rgba(255,255,255,0.55);
  line-height: 1.6;
}

.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}
.auth-card {
  width: 100%;
  max-width: 360px;
  background: rgba(255,255,255,0.95) !important;
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl) !important;
  padding: 8px;
}
.auth-card :deep(.el-card__body) { padding: 24px; }

.auth-header { text-align: center; margin-bottom: 28px; }
.auth-header h2 { font-size: 22px; font-weight: 700; color: var(--color-text); margin-bottom: 6px; }
.auth-header p { font-size: 13px; color: var(--color-text-muted); }

.submit-btn { width: 100%; border-radius: var(--radius-md) !important; height: 44px; font-size: 15px; font-weight: 600; }

.demo-section { margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--color-border); text-align: center; }
.demo-title { font-size: 12px; color: var(--color-text-muted); margin-bottom: 12px; }
.demo-buttons { display: flex; gap: 8px; justify-content: center; }
.demo-btn { border-radius: 20px !important; font-size: 12px; padding: 4px 16px !important; }
.demo-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  margin-right: 5px;
}
.admin-dot { background: #FF3B30; }
.teacher-dot { background: #FF9500; }
.student-dot { background: #34C759; }
.demo-hint { font-size: 11px; color: var(--color-text-placeholder); margin-top: 8px; }

.auth-footer { text-align: center; margin-top: 20px; font-size: 13px; color: var(--color-text-muted); }
.auth-footer a { color: var(--color-primary); font-weight: 600; text-decoration: none; margin-left: 4px; }
.auth-footer a:hover { text-decoration: underline; }
</style>
