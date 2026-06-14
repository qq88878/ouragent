<template>
  <div class="admin-page">
    <h3 style="margin-bottom:20px;">系统概览</h3>

    <el-row :gutter="20" style="margin-bottom:24px;">
      <el-col :span="6" v-for="c in statCards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">{{ c.icon }}</div>
          <div class="stat-value">{{ c.value ?? '-' }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="max-width:600px;">
      <template #header>系统健康</template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="Agent 服务">
          <el-tag :type="healthTag(health.agentStatus)" size="small">{{ health.agentStatus || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据库">
          <el-tag :type="healthTag(health.dbStatus)" size="small">{{ health.dbStatus || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Redis">
          <el-tag :type="healthTag(health.redisStatus)" size="small">{{ health.redisStatus || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="运行时长">{{ health.uptime || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { adminApi } from '@/api';

const dashboard = ref({});
const health = ref({});

const statCards = computed(() => {
  const d = dashboard.value;
  return [
    { icon:'👥', label:'总用户', value:d.totalUsers },
    { icon:'👨‍🏫', label:'教师', value:d.totalTeachers },
    { icon:'🎓', label:'学生', value:d.totalStudents },
    { icon:'📚', label:'课程', value:d.totalCourses },
    { icon:'💬', label:'消息数', value:d.totalConversations },
    { icon:'📅', label:'今日活跃', value:d.activeStudentsToday },
    { icon:'📁', label:'知识库', value:d.totalKnowledgeItems },
    { icon:'🛤️', label:'学习路径', value:d.totalPaths },
  ];
});

onMounted(async () => {
  try { const r=await adminApi.getDashboard(); if(r.code===200) dashboard.value=r.data||{}; } catch{}
  try { const r=await adminApi.getSystemHealth(); if(r.code===200) health.value=r.data||{}; } catch{}
});

function healthTag(s) {
  if (s==='healthy') return 'success';
  if (s==='unhealthy') return 'danger';
  return 'warning';
}
</script>

<style scoped>
.admin-page { max-width: 1000px; }
.stat-card { text-align:center; }
.stat-icon { font-size:24px; margin-bottom:4px; }
.stat-value { font-size:28px; font-weight:700; color:#303133; }
.stat-label { font-size:12px; color:#909399; margin-top:4px; }
</style>
