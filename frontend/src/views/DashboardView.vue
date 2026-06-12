<template>
  <div class="dashboard-page">
    <div class="welcome-section">
      <h2>欢迎回来{{ user ? '，' + (user.nickname || user.username) : '' }}</h2>
      <p class="subtitle">基于大模型的个性化资源生成与学习系统</p>
    </div>

    <el-alert
      v-if="user && !user.emailVerified"
      title="邮箱未验证"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #default>
        <span>您的邮箱 {{ user.email }} 尚未验证。</span>
        <el-button type="primary" size="small" style="margin-left: 12px;" @click="showVerifyDialog = true">立即验证</el-button>
      </template>
    </el-alert>

    <el-row :gutter="20" class="quick-nav">
      <el-col :span="6" v-for="nav in quickNavs" :key="nav.path">
        <el-card shadow="hover" class="nav-card" @click="$router.push(nav.path)">
          <el-icon :size="32" :color="nav.color"><component :is="nav.icon" /></el-icon>
          <h4>{{ nav.title }}</h4>
          <p>{{ nav.desc }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>学习统计</template>
          <el-skeleton v-if="statsLoading" :rows="4" animated />
          <el-descriptions v-else :column="2" border>
            <el-descriptions-item label="学习时长">{{ stats.totalDurationHours || 0 }} 小时</el-descriptions-item>
            <el-descriptions-item label="交互次数">{{ stats.totalInteractions || 0 }}</el-descriptions-item>
            <el-descriptions-item label="学习记录">{{ stats.totalRecords || 0 }} 条</el-descriptions-item>
            <el-descriptions-item label="涉及课程">{{ stats.courseCount || 0 }} 门</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>最近课程</template>
          <div v-if="recentCourses.length > 0">
            <div v-for="c in recentCourses" :key="c.id" class="recent-course" @click="$router.push('/courses')">
              <span class="course-title">{{ c.title }}</span>
              <el-tag size="small">{{ c.category || '未分类' }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无课程" :image-size="48" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showVerifyDialog" title="邮箱验证" width="400px" :close-on-click-modal="false">
      <p style="margin-bottom: 12px; color: #606266;">验证码已发送至 <b>{{ user?.email }}</b></p>
      <el-form @submit.prevent="handleVerify">
        <el-form-item>
          <el-input v-model="verifyCode" placeholder="请输入6位验证码" maxlength="6"
            style="letter-spacing: 4px; font-size: 18px; text-align: center;" />
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
import { ref, computed, onMounted, shallowRef } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { authApi, learningApi, courseApi } from '@/api';
import { ElMessage } from 'element-plus';
import { ChatDotRound, Reading, TrendCharts, Setting } from '@element-plus/icons-vue';

const authStore = useAuthStore();
const user = ref(null);
const stats = ref({});
const statsLoading = ref(false);
const recentCourses = ref([]);
const showVerifyDialog = ref(false);
const verifyCode = ref('');
const verifying = ref(false);
const resendCooldown = ref(0);

const quickNavs = [
  { path: '/chat', title: '智能对话', desc: 'AI 助手随时解答', icon: shallowRef(ChatDotRound), color: '#409eff' },
  { path: '/courses', title: '课程中心', desc: '浏览和选择课程', icon: shallowRef(Reading), color: '#67c23a' },
  { path: '/learning', title: '学习路径', desc: '个性化学习规划', icon: shallowRef(TrendCharts), color: '#e6a23c' },
  { path: '/admin', title: '管理后台', desc: '系统管理与监控', icon: shallowRef(Setting), color: '#909399' },
];

onMounted(async () => {
  const res = await authStore.fetchUser();
  if (res?.code === 200) user.value = res.data;
  await Promise.all([loadStats(), loadCourses()]);
});

async function loadStats() {
  statsLoading.value = true;
  try {
    const res = await learningApi.getStudyStats();
    if (res.code === 200) stats.value = res.data || {};
  } catch { /* ignore */ }
  finally { statsLoading.value = false; }
}

async function loadCourses() {
  try {
    const res = await courseApi.list({ page: 1, size: 5 });
    if (res.code === 200) recentCourses.value = res.data?.records || [];
  } catch { /* ignore */ }
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
      showVerifyDialog.value = false;
      ElMessage.success('邮箱验证成功！');
    } else {
      ElMessage.error(res.message || '验证失败');
    }
  } catch { ElMessage.error('验证失败'); }
  finally { verifying.value = false; }
}

async function handleResend() {
  try {
    const res = await authApi.sendVerifyCode(user.value.email);
    if (res.code === 200) {
      ElMessage.success('验证码已重新发送');
      resendCooldown.value = 60;
      const timer = setInterval(() => { resendCooldown.value--; if (resendCooldown.value <= 0) clearInterval(timer); }, 1000);
    }
  } catch { ElMessage.error('发送失败'); }
}
</script>

<style scoped>
.dashboard-page { max-width: 1100px; }
.welcome-section { margin-bottom: 24px; }
.welcome-section h2 { margin: 0 0 4px 0; font-size: 24px; }
.subtitle { color: #909399; margin: 0; }
.nav-card { text-align: center; cursor: pointer; transition: transform .2s; }
.nav-card:hover { transform: translateY(-4px); }
.nav-card h4 { margin: 12px 0 4px; font-size: 15px; }
.nav-card p { color: #909399; font-size: 12px; margin: 0; }
.recent-course { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f5f5f5; cursor: pointer; }
.recent-course:last-child { border-bottom: none; }
.course-title { font-size: 14px; }
</style>
