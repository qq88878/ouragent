<template>
  <div class="dashboard-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-glow"></div>
      <div class="welcome-content">
        <div class="welcome-text">
          <div class="greeting">{{ greetingText }}</div>
          <h2>{{ userDisplay }}</h2>
          <p>{{ roleDescription }}</p>
        </div>
        <div class="welcome-stats">
          <div class="ws-item" v-if="isStudent">
            <span class="ws-num">{{ studyStats.totalDurationHours || 0 }}</span>
            <span class="ws-unit">h</span>
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

    <!-- 邮箱验证提示 -->
    <div v-if="!emailVerified" class="verify-banner">
      <div class="verify-left">
        <el-icon :size="18" color="#FF9500"><WarningFilled /></el-icon>
        <span>邮箱未验证 — 部分功能受限</span>
      </div>
      <el-button type="warning" size="small" round plain @click="showVerify = true">立即验证</el-button>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-section">
      <h3 class="section-title">快捷操作</h3>
      <div class="quick-grid">
        <div class="quick-card" @click="$router.push('/chat')">
          <div class="qc-icon" style="background:#EEF0FF;color:#5B6AF0;">
            <el-icon :size="20"><ChatDotRound /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">智能对话</div>
            <div class="qc-desc">AI辅助学习交流</div>
          </div>
          <el-icon :size="16" class="qc-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="quick-card" @click="$router.push('/courses')">
          <div class="qc-icon" style="background:#EDFFF3;color:#34C759;">
            <el-icon :size="20"><Reading /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">课程中心</div>
            <div class="qc-desc">浏览全部课程资源</div>
          </div>
          <el-icon :size="16" class="qc-arrow"><ArrowRight /></el-icon>
        </div>
        <div v-if="isStudent" class="quick-card" @click="$router.push('/learning')">
          <div class="qc-icon" style="background:#FFF8ED;color:#FF9500;">
            <el-icon :size="20"><TrendCharts /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">学习路径</div>
            <div class="qc-desc">追踪学习进度</div>
          </div>
          <el-icon :size="16" class="qc-arrow"><ArrowRight /></el-icon>
        </div>
        <div v-if="isStudent" class="quick-card" @click="$router.push('/schedule')">
          <div class="qc-icon" style="background:#F0F9FF;color:#5AC8FA;">
            <el-icon :size="20"><Calendar /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">我的课表</div>
            <div class="qc-desc">查看本周安排</div>
          </div>
          <el-icon :size="16" class="qc-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="quick-card" @click="$router.push('/knowledge')">
          <div class="qc-icon" style="background:#F5F0FF;color:#AF52DE;">
            <el-icon :size="20"><Document /></el-icon>
          </div>
          <div class="qc-info">
            <div class="qc-title">知识库</div>
            <div class="qc-desc">查阅学习资料</div>
          </div>
          <el-icon :size="16" class="qc-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 数据概览 -->
    <div class="stats-section">
      <h3 class="section-title">数据概览</h3>

      <!-- 学生统计 -->
      <template v-if="isStudent">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="stat-card primary">
              <div class="sc-top">
                <div class="sc-icon"><el-icon :size="20"><Timer /></el-icon></div>
                <el-tag size="small" effect="plain" round>累计</el-tag>
              </div>
              <div class="sc-value">{{ studyStats.totalDurationHours || 0 }}<span class="sc-unit">h</span></div>
              <div class="sc-label">学习总时长</div>
              <div class="sc-sub">日均 {{ ((studyStats.totalDurationHours || 0) / Math.max(studyStats.totalDays || 1, 1)).toFixed(1) }}h</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card success">
              <div class="sc-top">
                <div class="sc-icon"><el-icon :size="20"><Notebook /></el-icon></div>
                <el-tag size="small" effect="plain" round>累计</el-tag>
              </div>
              <div class="sc-value">{{ studyStats.totalRecords || 0 }}<span class="sc-unit">条</span></div>
              <div class="sc-label">学习记录</div>
              <div class="sc-sub">持续 {{ studyStats.totalDays || 0 }} 天</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card warning">
              <div class="sc-top">
                <div class="sc-icon"><el-icon :size="20"><Collection /></el-icon></div>
                <el-tag size="small" effect="plain" round>当前</el-tag>
              </div>
              <div class="sc-value">{{ studyStats.courseCount || 0 }}<span class="sc-unit">门</span></div>
              <div class="sc-label">已选课程</div>
              <div class="sc-sub">含 {{ studyStats.activeCourses || 0 }} 门进行中</div>
            </div>
          </el-col>
        </el-row>
      </template>

      <!-- 教师统计 -->
      <template v-if="isTeacher">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="stat-card primary">
              <div class="sc-top"><div class="sc-icon"><el-icon :size="20"><Reading /></el-icon></div><el-tag size="small" effect="plain" round>已发布</el-tag></div>
              <div class="sc-value">{{ myCourses }}<span class="sc-unit">门</span></div>
              <div class="sc-label">我的课程</div>
              <div class="sc-sub">其中 {{ publishedCourses }} 门已发布</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card success">
              <div class="sc-top"><div class="sc-icon"><el-icon :size="20"><Files /></el-icon></div></div>
              <div class="sc-value">{{ knowledgeCount }}<span class="sc-unit">个</span></div>
              <div class="sc-label">知识库文件</div>
              <div class="sc-sub">关联至课程辅材</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card warning">
              <div class="sc-top"><div class="sc-icon"><el-icon :size="20"><UserFilled /></el-icon></div></div>
              <div class="sc-value">{{ studentCount }}<span class="sc-unit">人</span></div>
              <div class="sc-label">平台学生数</div>
              <div class="sc-sub">选课总人次 {{ totalEnrollments }}</div>
            </div>
          </el-col>
        </el-row>
      </template>

      <!-- 管理员统计 -->
      <template v-if="isAdmin">
        <el-row :gutter="16">
          <el-col v-for="s in adminStats" :key="s.label" :span="6">
            <div class="stat-card-mini">
              <div class="sm-icon" :style="{ background: s.bg + '15', color: s.bg }">
                <el-icon :size="18"><component :is="s.icon" /></el-icon>
              </div>
              <div class="sm-info">
                <div class="sm-value">{{ s.value ?? '-' }}</div>
                <div class="sm-label">{{ s.label }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </template>
    </div>

    <!-- 验证弹窗 -->
    <el-dialog v-model="showVerify" title="邮箱验证" width="420px" :close-on-click-modal="false">
      <div class="verify-dialog">
        <div class="vd-icon"><el-icon :size="36" color="#FF9500"><Message /></el-icon></div>
        <p>验证码已发送至 <strong>{{ user?.email }}</strong></p>
        <div style="display:flex;gap:8px;margin-top:16px;">
          <el-input v-model="verifyCode" placeholder="6位验证码" maxlength="6" size="large" />
          <el-button :loading="sending" @click="sendCode" size="large" plain>重新发送</el-button>
        </div>
        <el-button type="primary" :loading="verifying" @click="doVerify" size="large" style="width:100%;margin-top:12px;">验证</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { learningApi, courseApi, adminApi, authApi, knowledgeApi } from '@/api';
import { ElMessage } from 'element-plus';
import {
  ChatDotRound, Reading, TrendCharts, Calendar, Document, ArrowRight,
  WarningFilled, Timer, Notebook, Collection, Files, UserFilled, Message,
  DataAnalysis,
} from '@element-plus/icons-vue';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const userDisplay = computed(() => user.value?.nickname || user.value?.username || '');
const emailVerified = computed(() => user.value?.emailVerified === 1 || authStore.emailVerified);
const isStudent = computed(() => user.value?.role === 'STUDENT');
const isTeacher = computed(() => user.value?.role === 'TEACHER');
const isAdmin = computed(() => user.value?.role === 'ADMIN');

const studyStats = ref({});
const myCourses = ref(0);
const publishedCourses = ref(0);
const knowledgeCount = ref(0);
const studentCount = ref(0);
const totalEnrollments = ref(0);
const adminData = ref({});
const showVerify = ref(false); const verifyCode = ref(''); const sending = ref(false); const verifying = ref(false);

const todayDate = computed(() => {
  const d = new Date();
  return (d.getMonth() + 1) + '/' + d.getDate();
});

const greetings = ['新的一天，', '下午好，', '晚上好，', '继续加油，'];
const greetingText = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '早上好，';
  if (h < 14) return '中午好，';
  if (h < 18) return '下午好，';
  return '晚上好，';
});

const roleDescription = computed(() => {
  switch (user.value?.role) {
    case 'STUDENT': return '今天也是充实学习的一天';
    case 'TEACHER': return '用心教学，成就未来';
    case 'ADMIN': return '平台运行一切正常';
    default: return '';
  }
});

const adminStats = computed(() => {
  const d = adminData.value;
  return [
    { label: '总用户', value: d.totalUsers, icon: UserFilled, bg: '#5B6AF0' },
    { label: '教师', value: d.totalTeachers, icon: Reading, bg: '#34C759' },
    { label: '学生', value: d.totalStudents, icon: Notebook, bg: '#FF9500' },
    { label: '课程', value: d.totalCourses, icon: Collection, bg: '#5AC8FA' },
    { label: '会话数', value: d.totalConversations, icon: ChatDotRound, bg: '#FF3B30' },
    { label: '今日活跃', value: d.activeStudentsToday, icon: DataAnalysis, bg: '#AF52DE' },
    { label: '知识库', value: d.totalKnowledgeItems, icon: Files, bg: '#FFB340' },
    { label: '学习路径', value: d.totalPaths, icon: TrendCharts, bg: '#34C759' },
  ];
});

onMounted(async () => {
  if (!user.value) await authStore.fetchUser();
  const role = user.value?.role;
  if (role === 'STUDENT') {
    try { const r = await learningApi.getStudyStats(); if (r.code === 200) studyStats.value = r.data; } catch {}
  }
  if (role === 'TEACHER') {
    try {
      const r = await courseApi.list({ page: 1, size: 200, teacherId: user.value?.id });
      if (r.code === 200) {
        const records = r.data?.records || [];
        myCourses.value = r.data?.total || 0;
        publishedCourses.value = records.filter(c => c.status === 1).length;
        totalEnrollments.value = records.reduce((sum, c) => sum + (c.enrollmentCount || 0), 0);
      }
    } catch {}
    try { const r = await knowledgeApi.listAll(); if (r.code === 200) knowledgeCount.value = (r.data || []).filter(k => k.courseTeacherId === user.value?.id).length; } catch {}
    try { const r = await adminApi.getDashboard(); if (r.code === 200) studentCount.value = r.data?.totalStudents || 0; } catch {}
  }
  if (role === 'ADMIN') {
    try { const r = await adminApi.getDashboard(); if (r.code === 200) adminData.value = r.data || {}; } catch {}
  }
});

async function sendCode() { sending.value = true; try { await authApi.sendVerifyCode(user.value.email); ElMessage.success('验证码已发送'); } catch { ElMessage.error('发送失败'); } finally { sending.value = false; } }
async function doVerify() { if (!verifyCode.value) return; verifying.value = true; try { await authApi.verifyEmail(user.value.email, verifyCode.value); ElMessage.success('验证成功'); showVerify.value = false; user.value.emailVerified = 1; } catch { ElMessage.error('验证失败'); } finally { verifying.value = false; } }
</script>

<style scoped>
.dashboard-page { max-width: 1100px; }

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #5B6AF0 0%, #7C5CFC 100%);
  border-radius: var(--radius-xl);
  padding: 0;
  margin-bottom: 18px;
  position: relative;
  overflow: hidden;
}
.welcome-glow {
  position: absolute; right: -40px; top: -40px;
  width: 200px; height: 200px; border-radius: 50%;
  background: rgba(255,255,255,0.08);
}
.welcome-content {
  display: flex; align-items: center; justify-content: space-between;
  padding: 28px 36px; position: relative; z-index: 1;
}
.greeting { font-size: 13px; color: rgba(255,255,255,0.7); font-weight: 500; }
.welcome-text h2 { font-size: 26px; font-weight: 700; color: #fff; margin: 2px 0 4px; }
.welcome-text p { font-size: 13px; color: rgba(255,255,255,0.65); }

.welcome-stats { display: flex; align-items: center; gap: 0; }
.ws-item { text-align: center; padding: 0 20px; }
.ws-num { font-size: 28px; font-weight: 700; color: #fff; display: block; line-height: 1; }
.ws-unit { font-size: 14px; color: rgba(255,255,255,0.6); margin-left: 2px; }
.ws-label { font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 4px; display: block; }
.ws-divider { width: 1px; height: 40px; background: rgba(255,255,255,0.15); }

/* 验证横幅 */
.verify-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: #FFF8ED; border: 1px solid #FFE8C0;
  border-radius: var(--radius-lg); padding: 10px 18px; margin-bottom: 22px;
}
.verify-left { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #B86E00; }

/* 快捷操作 */
.quick-section { margin-bottom: 26px; }
.section-title { font-size: 16px; font-weight: 700; color: var(--color-text); margin-bottom: 12px; }
.quick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }

.quick-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: var(--radius-lg);
  background: var(--color-bg-card); box-shadow: var(--shadow-card);
  cursor: pointer; transition: all var(--transition-base);
}
.quick-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.qc-icon { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.qc-info { flex: 1; min-width: 0; }
.qc-title { font-size: 13px; font-weight: 600; color: var(--color-text); }
.qc-desc { font-size: 11px; color: var(--color-text-muted); margin-top: 1px; }
.qc-arrow { color: var(--color-text-placeholder); flex-shrink: 0; }

/* 统计卡片 */
.stats-section { margin-bottom: 24px; }

.stat-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  padding: 22px 24px; box-shadow: var(--shadow-card);
  transition: all var(--transition-base); margin-bottom: 16px;
  border-top: 3px solid transparent;
}
.stat-card.primary { border-top-color: #5B6AF0; }
.stat-card.success { border-top-color: #34C759; }
.stat-card.warning { border-top-color: #FF9500; }
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

.sc-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.sc-icon { width: 36px; height: 36px; border-radius: var(--radius-sm); background: var(--color-bg); display: flex; align-items: center; justify-content: center; color: var(--color-text-secondary); }
.sc-value { font-size: 32px; font-weight: 700; color: var(--color-text); line-height: 1; }
.sc-unit { font-size: 16px; color: var(--color-text-muted); font-weight: 500; margin-left: 2px; }
.sc-label { font-size: 13px; color: var(--color-text-secondary); margin-top: 6px; font-weight: 500; }
.sc-sub { font-size: 11px; color: var(--color-text-muted); margin-top: 3px; }

.stat-card-mini {
  display: flex; align-items: center; gap: 12px;
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 16px 18px; box-shadow: var(--shadow-card);
  transition: all var(--transition-base); margin-bottom: 16px;
}
.stat-card-mini:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.sm-icon { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.sm-value { font-size: 22px; font-weight: 700; color: var(--color-text); line-height: 1; }
.sm-label { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; }

.verify-dialog { text-align: center; padding: 8px 0; }
.verify-dialog p { font-size: 14px; color: var(--color-text-secondary); margin-top: 12px; }
.verify-dialog strong { color: var(--color-text); }
</style>
