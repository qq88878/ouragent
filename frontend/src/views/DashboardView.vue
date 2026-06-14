<template>
  <div class="dashboard-page">
    <div class="welcome-section">
      <h2>欢迎回来，{{ userDisplay }}</h2>
      <p class="subtitle">基于大模型的个性化资源生成与学习系统</p>
    </div>

    <el-alert v-if="!emailVerified" title="邮箱未验证" type="warning" :closable="false" show-icon style="margin-bottom:20px">
      <template #default>
        <span>您的邮箱尚未验证。</span>
        <el-button type="primary" size="small" style="margin-left:12px" @click="showVerify=true">立即验证</el-button>
      </template>
    </el-alert>

    <!-- Student -->
    <template v-if="isStudent">
      <el-row :gutter="20">
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ studyStats.totalDurationHours || 0 }}h</div><div class="dash-label">学习时长</div></el-card></el-col>
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ studyStats.totalRecords || 0 }}</div><div class="dash-label">学习记录</div></el-card></el-col>
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ studyStats.courseCount || 0 }}</div><div class="dash-label">已选课程</div></el-card></el-col>
      </el-row>
    </template>

    <!-- Teacher -->
    <template v-if="isTeacher">
      <el-row :gutter="20">
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ myCourses }}</div><div class="dash-label">我的课程</div></el-card></el-col>
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ knowledgeCount }}</div><div class="dash-label">知识库文件</div></el-card></el-col>
        <el-col :span="8"><el-card shadow="hover" class="dash-card"><div class="dash-num">{{ studentCount }}</div><div class="dash-label">平台学生</div></el-card></el-col>
      </el-row>
    </template>

    <!-- Admin -->
    <template v-if="isAdmin">
      <el-row :gutter="20">
        <el-col :span="6" v-for="c in adminCards" :key="c.label">
          <el-card shadow="hover" class="dash-card">
            <div class="dash-icon">{{ c.icon }}</div>
            <div class="dash-num">{{ c.value ?? '-' }}</div>
            <div class="dash-label">{{ c.label }}</div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-dialog v-model="showVerify" title="邮箱验证" width="400px">
      <el-form label-width="80px">
        <el-form-item label="邮箱">{{ user?.email }}</el-form-item>
        <el-form-item label="验证码">
          <el-input v-model="verifyCode" placeholder="6位验证码" maxlength="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendCode" :loading="sending">发送验证码</el-button>
        <el-button type="primary" @click="doVerify" :loading="verifying">验证</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { learningApi, courseApi, adminApi, authApi, knowledgeApi } from '@/api';
import { ElMessage } from 'element-plus';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const userDisplay = computed(() => user.value?.nickname || user.value?.username || '');
const emailVerified = computed(() => user.value?.emailVerified === 1 || authStore.emailVerified);
const isStudent = computed(() => user.value?.role === 'STUDENT');
const isTeacher = computed(() => user.value?.role === 'TEACHER');
const isAdmin = computed(() => user.value?.role === 'ADMIN');

const studyStats = ref({});
const myCourses = ref(0); const knowledgeCount = ref(0); const studentCount = ref(0);
const adminCards = ref([]);
const showVerify = ref(false); const verifyCode = ref(''); const sending = ref(false); const verifying = ref(false);

onMounted(async () => {
  if (!user.value) await authStore.fetchUser();
  const role = user.value?.role;
  if (role === 'STUDENT') { try { const r=await learningApi.getStudyStats(); if(r.code===200) studyStats.value=r.data; } catch{} }
  if (role === 'TEACHER') {
    try { const r=await courseApi.list({page:1,size:100,teacherId:user.value?.id}); if(r.code===200) myCourses.value=r.data?.total||0; } catch{}
    try { const r=await knowledgeApi.listAll(); if(r.code===200) { knowledgeCount.value=(r.data||[]).filter(k=>k.courseTeacherId===user.value?.id).length; } } catch{}
    try { const r=await adminApi.getDashboard(); if(r.code===200) studentCount.value=r.data?.totalStudents||0; } catch{}
  }
  if (role === 'ADMIN') {
    try { const r=await adminApi.getDashboard(); if(r.code===200) {
      const d=r.data;
      adminCards.value=[
        {icon:'👥',label:'总用户',value:d.totalUsers},{icon:'👨‍🏫',label:'教师',value:d.totalTeachers},{icon:'🎓',label:'学生',value:d.totalStudents},{icon:'📚',label:'课程',value:d.totalCourses},
        {icon:'💬',label:'消息数',value:d.totalConversations},{icon:'📅',label:'今日活跃',value:d.activeStudentsToday},{icon:'📁',label:'知识库',value:d.totalKnowledgeItems},{icon:'🛤️',label:'学习路径',value:d.totalPaths},
      ];
    }} catch{}
  }
});

async function sendCode() { sending.value=true; try { await authApi.sendVerifyCode(user.value.email); ElMessage.success('验证码已发送'); } catch{ElMessage.error('发送失败');} finally{sending.value=false;} }
async function doVerify() { if(!verifyCode.value) return; verifying.value=true; try { await authApi.verifyEmail(user.value.email,verifyCode.value); ElMessage.success('验证成功'); showVerify.value=false; user.value.emailVerified=1; } catch{ElMessage.error('验证失败');} finally{verifying.value=false;} }
</script>

<style scoped>
.dashboard-page { max-width: 1000px; }
.welcome-section { margin-bottom: 24px; }
.welcome-section h2 { font-size: 24px; color: #303133; }
.subtitle { color: #909399; margin-top: 4px; }
.dash-card { text-align: center; }
.dash-icon { font-size: 24px; margin-bottom: 4px; }
.dash-num { font-size: 28px; font-weight: 700; color: #409eff; }
.dash-label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>
