<template>
  <div class="admin-page">
    <h3 style="margin-bottom: 20px;">管理后台</h3>

    <el-row :gutter="20" style="margin-bottom: 24px;">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ card.value ?? '-' }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>系统健康状态</template>
          <el-descriptions :column="1" border v-loading="healthLoading">
            <el-descriptions-item label="Agent 服务">
              <el-tag :type="healthStatusType(health.agentStatus)" size="small">
                {{ health.agentStatus || '检测中' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据库">
              <el-tag :type="healthStatusType(health.dbStatus)" size="small">
                {{ health.dbStatus || '检测中' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Redis">
              <el-tag :type="healthStatusType(health.redisStatus)" size="small">
                {{ health.redisStatus || '检测中' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行状态">
              {{ health.uptime || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>快捷操作</template>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <el-button type="primary" @click="$router.push('/admin/users')">用户管理</el-button>
            <el-button @click="$router.push('/courses')">课程管理</el-button>
            <el-button @click="$router.push('/knowledge')">知识库管理</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { adminApi } from '@/api';

const dashboard = ref({});
const health = ref({});
const healthLoading = ref(false);

const statCards = computed(() => [
  { label: '总用户数', value: dashboard.value.totalUsers },
  { label: '教师数', value: dashboard.value.totalTeachers },
  { label: '学生数', value: dashboard.value.totalStudents },
  { label: '课程数', value: dashboard.value.totalCourses },
  { label: '对话消息数', value: dashboard.value.totalConversations },
  { label: '今日活跃学生', value: dashboard.value.activeStudentsToday },
  { label: '知识库文件', value: dashboard.value.totalKnowledgeItems },
]);

onMounted(async () => {
  await Promise.all([loadDashboard(), loadHealth()]);
});

async function loadDashboard() {
  try {
    const res = await adminApi.getDashboard();
    if (res.code === 200) dashboard.value = res.data || {};
  } catch { /* ignore */ }
}

async function loadHealth() {
  healthLoading.value = true;
  try {
    const res = await adminApi.getSystemHealth();
    if (res.code === 200) health.value = res.data || {};
  } catch { /* ignore */ }
  finally { healthLoading.value = false; }
}

function healthStatusType(status) {
  if (status === 'healthy') return 'success';
  if (status === 'unhealthy') return 'danger';
  return 'warning';
}
</script>

<style scoped>
.admin-page { max-width: 1100px; }
.stat-card { text-align: center; }
.stat-value { font-size: 32px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>
