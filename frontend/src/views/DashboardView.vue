<template>
  <div class="dashboard-page">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-glow"></div>
      <div class="welcome-pattern"></div>
      <div class="welcome-content">
        <div class="welcome-text">
          <div class="greeting">{{ greetingText }}</div>
          <h2>{{ userDisplay }}</h2>
          <p>{{ roleDescription }}</p>
        </div>
        <div class="welcome-stats">
          <div class="ws-item" v-if="isStudent">
            <span class="ws-num">{{ studyStats.totalDurationHours || 0 }}<span class="ws-unit">h</span></span>
            <span class="ws-label">学习时长</span>
          </div>
          <div class="ws-item" v-if="isTeacher">
            <span class="ws-num">{{ myCourses }}</span>
            <span class="ws-label">我的课程</span>
          </div>
          <div class="ws-item" v-if="isAdmin">
            <span class="ws-num">{{ adminData.totalUsers ?? '-' }}</span>
            <span class="ws-label">总用户</span>
          </div>
          <div class="ws-divider"></div>
          <div class="ws-item">
            <span class="ws-num">{{ todayDate }}</span>
            <span class="ws-label">今天</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Email Verify -->
    <div v-if="!emailVerified" class="verify-banner">
      <div class="verify-left">
        <el-icon :size="18" color="#C1803A"><WarningFilled /></el-icon>
        <span>邮箱未验证 — 部分功能受限</span>
      </div>
      <el-button type="warning" size="small" round plain @click="showVerify = true">立即验证</el-button>
    </div>

    <!-- Quick Actions -->
    <div class="quick-section">
      <div class="section-header-row">
        <h3 class="section-title">快捷操作</h3>
        <span class="section-subtitle">常用功能入口</span>
      </div>
      <div class="quick-grid">
        <div class="quick-card" @click="$router.push('/chat')">
          <div class="qc-icon" style="background:#FFF8F0;color:#B5651D;">
            <el-icon :size="22"><ChatDotRound /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">智能对话</div>
            <div class="qc-desc">AI 辅助学习交流</div>
          </div>
          <div class="qc-arrow-wrap"><el-icon :size="18"><ArrowRight /></el-icon></div>
        </div>
        <div class="quick-card" @click="$router.push('/courses')">
          <div class="qc-icon" style="background:#EEF6EE;color:#5B8C5A;">
            <el-icon :size="22"><Reading /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">课程中心</div>
            <div class="qc-desc">浏览全部课程资源</div>
          </div>
          <div class="qc-arrow-wrap"><el-icon :size="18"><ArrowRight /></el-icon></div>
        </div>
        <div v-if="isStudent" class="quick-card" @click="$router.push('/learning')">
          <div class="qc-icon" style="background:#FEF6ED;color:#C1803A;">
            <el-icon :size="22"><TrendCharts /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">学习路径</div>
            <div class="qc-desc">追踪学习进度</div>
          </div>
          <div class="qc-arrow-wrap"><el-icon :size="18"><ArrowRight /></el-icon></div>
        </div>
        <div v-if="isStudent" class="quick-card" @click="$router.push('/schedule')">
          <div class="qc-icon" style="background:#F0F6FA;color:#5B8BA8;">
            <el-icon :size="22"><Calendar /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">我的课表</div>
            <div class="qc-desc">查看本周安排</div>
          </div>
          <div class="qc-arrow-wrap"><el-icon :size="18"><ArrowRight /></el-icon></div>
        </div>
        <div class="quick-card" @click="$router.push('/knowledge')">
          <div class="qc-icon" style="background:#F5EEF6;color:#7B5EA7;">
            <el-icon :size="22"><Document /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">知识库</div>
            <div class="qc-desc">查阅学习资料</div>
          </div>
          <div class="qc-arrow-wrap"><el-icon :size="18"><ArrowRight /></el-icon></div>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="section-header-row">
        <h3 class="section-title">数据概览</h3>
        <span class="section-subtitle">{{ isStudent ? '学习统计' : isTeacher ? '教学数据' : '平台数据' }}</span>
      </div>

      <template v-if="isStudent">
        <div class="stats-grid-3">
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#FEF5EC;color:#B5651D;"><el-icon :size="22"><Timer /></el-icon></div>
              <div class="sc-body">
                <div class="sc-value">{{ studyStats.totalDurationHours || 0 }}<span class="sc-unit"> h</span></div>
                <div class="sc-label">累计学习时长</div>
                <div class="sc-sub">日均 {{ ((studyStats.totalDurationHours || 0) / Math.max(studyStats.activeDays || 1, 1)).toFixed(1) }} 小时</div>
              </div>
            </div>
          </div>
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#EEF6EE;color:#5B8C5A;"><el-icon :size="22"><Check /></el-icon></div>
              <div class="sc-body">
                <div class="sc-value">{{ studyStats.weeklyCompletedSteps || 0 }}<span class="sc-unit"> 步</span></div>
                <div class="sc-label">本周完成步骤</div>
                <div class="sc-sub">继续保持</div>
              </div>
            </div>
          </div>
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#FEF6ED;color:#C1803A;"><el-icon :size="22"><TrendCharts /></el-icon></div>
              <div class="sc-body">
                <div class="sc-value">{{ activeCourses }}<span class="sc-unit"> 门</span></div>
                <div class="sc-label">进行中课程</div>
                <div class="sc-sub">持续精进</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-if="isTeacher">
        <div class="stats-grid-3">
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#FEF5EC;color:#B5651D;"><el-icon :size="22"><Reading /></el-icon></div>
              <div class="sc-body"><div class="sc-value">{{ myCourses }}</div><div class="sc-label">我的课程</div></div>
            </div>
          </div>
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#EEF6EE;color:#5B8C5A;"><el-icon :size="22"><Avatar /></el-icon></div>
              <div class="sc-body"><div class="sc-value">{{ totalEnrollment }}</div><div class="sc-label">总选课人数</div></div>
            </div>
          </div>
          <div class="stat-card elevated">
            <div class="stat-card-inner">
              <div class="sc-icon-ring" style="background:#EEF0F6;color:#5B8BA8;"><el-icon :size="22"><Document /></el-icon></div>
              <div class="sc-body"><div class="sc-value">{{ totalKnowledge }}</div><div class="sc-label">知识库文件</div></div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Verify Dialog -->
    <el-dialog v-model="showVerify" title="邮箱验证" width="440px" class="verify-dialog">
      <p>向 <strong>{{ user?.email }}</strong> 发送验证码</p>
      <el-input v-model="verifyCode" placeholder="6 位验证码" maxlength="6" size="large" style="margin-top:16px" />
      <template #footer>
        <el-button @click="sendCode" :loading="sendingCode" plain>发送验证码</el-button>
        <el-button type="primary" @click="doVerifyEmail" :loading="verifying">验证</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { courseApi, learningApi, adminApi, authApi } from '@/api';
import { ElMessage } from 'element-plus';
import { ChatDotRound, Reading, TrendCharts, Calendar, Document, Timer, Check, Avatar, ArrowRight, WarningFilled } from '@element-plus/icons-vue';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const emailVerified = computed(() => user.value?.emailVerified === 1 || authStore.emailVerified);
const isStudent = computed(() => user.value?.role === 'STUDENT');
const isTeacher = computed(() => user.value?.role === 'TEACHER');
const isAdmin = computed(() => user.value?.role === 'ADMIN');

const userDisplay = computed(() => user.value?.nickname || user.value?.username || '同学');
const roleDescription = computed(() => {
  switch (user.value?.role) { case 'ADMIN': return '系统管理员'; case 'TEACHER': return '教师'; case 'STUDENT': return '学生'; default: return ''; }
});

const greetingText = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '夜深了，注意休息 🌙';
  if (h < 12) return '早上好 ☀️';
  if (h < 18) return '下午好 🌤️';
  return '晚上好 🌆';
});

const todayDate = computed(() => {
  const d = new Date();
  return `${d.getMonth() + 1}/${d.getDate()}`;
});

const studyStats = ref({});
const myCourses = ref(0);
const totalEnrollment = ref(0);
const totalKnowledge = ref(0);
const activeCourses = ref(0);
const adminData = ref({});

const showVerify = ref(false);
const verifyCode = ref('');
const sendingCode = ref(false);
const verifying = ref(false);

onMounted(async () => {
  await authStore.fetchUser();
  if (isStudent.value) {
    try { const r = await learningApi.getStudyStats(); if (r.code === 200) studyStats.value = r.data || {}; } catch {}
    try { const r = await courseApi.getEnrolled(); if (r.code === 200) activeCourses.value = (r.data || []).length; } catch {}
  }
  if (isTeacher.value) {
    try { const r = await courseApi.list({ page: 1, size: 1 }); if (r.code === 200) myCourses.value = r.data?.total || 0; } catch {}
    try { const r = await courseApi.list({ page: 1, size: 100 }); if (r.code === 200) { const cs = r.data?.records || []; totalEnrollment.value = cs.reduce((s,c) => s + (c.enrollmentCount || 0), 0); totalKnowledge.value = cs.length; } } catch {}
  }
  if (isAdmin.value) {
    try { const r = await adminApi.getDashboard(); if (r.code === 200) adminData.value = r.data || {}; } catch {}
  }
});

async function sendCode() { sendingCode.value = true; try { await authApi.sendVerifyCode(user.value.email); ElMessage.success('验证码已发送'); } catch { ElMessage.error('发送失败'); } finally { sendingCode.value = false; } }
async function doVerifyEmail() { if (!verifyCode.value) return; verifying.value = true; try { await authApi.verifyEmail(user.value.email, verifyCode.value); ElMessage.success('验证成功'); showVerify.value = false; user.value.emailVerified = 1; } catch { ElMessage.error('验证失败'); } finally { verifying.value = false; } }
</script>

<style scoped>
.dashboard-page { max-width: 1100px; margin: 0 auto; }

/* ===== Welcome Banner ===== */
.welcome-banner {
  background: linear-gradient(135deg, #B5651D 0%, #C1783A 40%, #9C5216 100%);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}
.welcome-glow {
  position: absolute; right: -60px; top: -60px;
  width: 280px; height: 280px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.10) 0%, transparent 70%);
}
.welcome-pattern {
  position: absolute; inset: 0; opacity: 0.04;
  background-image: repeating-linear-gradient(45deg, #fff 0px, #fff 1px, transparent 1px, transparent 20px);
}
.welcome-content {
  display: flex; align-items: center; justify-content: space-between;
  padding: 32px 40px; position: relative; z-index: 1;
}
.greeting { font-size: 14px; color: rgba(255,255,255,0.70); font-weight: 500; letter-spacing: 0.02em; }
.welcome-text h2 { font-size: 30px; font-weight: 700; color: #fff; margin: 4px 0 6px; letter-spacing: -0.01em; }
.welcome-text p { font-size: 14px; color: rgba(255,255,255,0.55); font-weight: 400; }

.welcome-stats { display: flex; align-items: center; gap: 0; }
.ws-item { text-align: center; padding: 0 24px; }
.ws-num { font-size: 34px; font-weight: 700; color: #fff; display: block; line-height: 1.1; letter-spacing: -0.02em; }
.ws-unit { font-size: 16px; color: rgba(255,255,255,0.45); margin-left: 2px; font-weight: 500; }
.ws-label { font-size: 12px; color: rgba(255,255,255,0.40); margin-top: 6px; display: block; text-transform: uppercase; letter-spacing: 0.06em; }
.ws-divider { width: 1px; height: 44px; background: rgba(255,255,255,0.10); }

/* ===== Verify Banner ===== */
.verify-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: #FEF6ED; border: 1px solid #F0D4B0; border-left: 4px solid #C1803A;
  border-radius: var(--radius-lg); padding: 14px 20px; margin-bottom: 28px;
}
.verify-left { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #9C5A1A; font-weight: 500; }

/* ===== Section Header ===== */
.section-header-row {
  display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px;
}
.section-title { font-size: 18px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.section-subtitle { font-size: 13px; color: var(--color-text-muted); font-weight: 400; }

/* ===== Quick Actions ===== */
.quick-section { margin-bottom: 32px; }
.quick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; }

.quick-card {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 20px; border-radius: var(--radius-lg);
  background: var(--color-bg-card); box-shadow: var(--shadow-card);
  cursor: pointer; transition: all 0.2s ease;
  border: 1px solid transparent;
}
.quick-card:hover {
  transform: translateY(-3px); box-shadow: var(--shadow-md);
  border-color: var(--color-border);
}
.qc-icon { width: 46px; height: 46px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.qc-info { flex: 1; min-width: 0; }
.qc-title { font-size: 14px; font-weight: 600; color: var(--color-text); letter-spacing: -0.01em; }
.qc-desc { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }
.qc-arrow-wrap {
  width: 32px; height: 32px; border-radius: 8px;
  background: var(--color-bg); display: flex; align-items: center; justify-content: center;
  color: var(--color-text-placeholder); flex-shrink: 0; transition: all 0.2s ease;
}
.quick-card:hover .qc-arrow-wrap { background: var(--color-primary-light); color: var(--color-primary); }

/* ===== Stats ===== */
.stats-section { margin-bottom: 8px; }
.stats-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.stat-card.elevated {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card); transition: all 0.25s ease;
  overflow: hidden;
}
.stat-card.elevated:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.stat-card-inner { display: flex; align-items: center; gap: 18px; padding: 24px; }
.sc-icon-ring {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sc-body { flex: 1; min-width: 0; }
.sc-value { font-size: 30px; font-weight: 700; color: var(--color-text); line-height: 1.1; letter-spacing: -0.02em; }
.sc-unit { font-size: 15px; color: var(--color-text-muted); font-weight: 500; }
.sc-label { font-size: 14px; color: var(--color-text-secondary); margin-top: 4px; font-weight: 500; }
.sc-sub { font-size: 12px; color: var(--color-text-muted); margin-top: 3px; }

/* ===== Verify Dialog ===== */
.verify-dialog { text-align: center; padding: 8px 0; }
.verify-dialog p { font-size: 14px; color: var(--color-text-secondary); margin-top: 12px; }
.verify-dialog strong { color: var(--color-text); }

@media (max-width: 768px) {
  .welcome-content { flex-direction: column; gap: 20px; padding: 24px; }
  .welcome-stats { flex-wrap: wrap; }
  .ws-divider { display: none; }
  .stats-grid-3 { grid-template-columns: 1fr; }
}
</style>
