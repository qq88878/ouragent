<template>
  <div class="admin-page">
    <div class="page-header">
      <div>
        <h3>系统概览</h3>
        <p class="page-desc">实时监控平台运行状态</p>
      </div>
    </div>

    <el-row :gutter="16" class="stats-grid">
      <el-col :span="6" v-for="c in statCards" :key="c.label">
        <div class="stat-card">
          <div class="stat-icon-box" :style="{ background: c.bg + '15', color: c.bg }">
            <span class="stat-emoji">{{ c.icon }}</span>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ c.value ?? '-' }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="health-section">
      <h3 class="section-title">系统健康</h3>
      <el-row :gutter="16">
        <el-col v-for="h in healthItems" :key="h.key" :span="6">
          <div class="health-card" :class="'status-' + h.status">
            <div class="health-icon">
              <div v-if="h.status === 'healthy'" class="pulse-dot green"></div>
              <div v-else-if="h.status === 'unhealthy'" class="pulse-dot red"></div>
              <div v-else class="pulse-dot yellow"></div>
            </div>
            <div class="health-info">
              <div class="health-name">{{ h.name }}</div>
              <div class="health-status">{{ h.statusText }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
      <div v-if="health.uptime" class="uptime-info">
        <el-icon :size="14"><Timer /></el-icon>
        <span>运行时长：{{ health.uptime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { adminApi } from '@/api';
import { Timer } from '@element-plus/icons-vue';

const dashboard = ref({});
const health = ref({});

const colors = ['#5B6AF0', '#34C759', '#FF9500', '#5AC8FA', '#AF52DE', '#FF3B30', '#FFB340', '#30D158'];

const statCards = computed(() => {
  const d = dashboard.value;
  const items = [
    { icon: '👥', label: '总用户', value: d.totalUsers },
    { icon: '👨‍🏫', label: '教师', value: d.totalTeachers },
    { icon: '🎓', label: '学生', value: d.totalStudents },
    { icon: '📚', label: '课程', value: d.totalCourses },
    { icon: '💬', label: '消息数', value: d.totalConversations },
    { icon: '📊', label: '今日活跃', value: d.activeStudentsToday },
    { icon: '📖', label: '知识库', value: d.totalKnowledgeItems },
    { icon: '🛤️', label: '学习路径', value: d.totalPaths },
  ];
  return items.map((item, i) => ({ ...item, bg: colors[i] }));
});

const healthItems = computed(() => [
  { key: 'agent', name: 'Agent 服务', status: health.value.agentStatus === 'healthy' ? 'healthy' : health.value.agentStatus === 'unhealthy' ? 'unhealthy' : 'unknown', statusText: health.value.agentStatus === 'healthy' ? '运行正常' : health.value.agentStatus === 'unhealthy' ? '异常' : health.value.agentStatus || '未知' },
  { key: 'db', name: '数据库', status: health.value.dbStatus === 'healthy' ? 'healthy' : health.value.dbStatus === 'unhealthy' ? 'unhealthy' : 'unknown', statusText: health.value.dbStatus === 'healthy' ? '运行正常' : health.value.dbStatus === 'unhealthy' ? '异常' : health.value.dbStatus || '未知' },
  { key: 'redis', name: 'Redis', status: health.value.redisStatus === 'healthy' ? 'healthy' : health.value.redisStatus === 'unhealthy' ? 'unhealthy' : 'unknown', statusText: health.value.redisStatus === 'healthy' ? '运行正常' : health.value.redisStatus === 'unhealthy' ? '异常' : health.value.redisStatus || '未知' },
]);

onMounted(async () => {
  try { const r = await adminApi.getDashboard(); if (r.code === 200) dashboard.value = r.data || {}; } catch {}
  try { const r = await adminApi.getSystemHealth(); if (r.code === 200) health.value = r.data || {}; } catch {}
});
</script>

<style scoped>
.admin-page { max-width: 1100px; }

.page-header { margin-bottom: 24px; }
.page-header h3 { font-size: 22px; font-weight: 700; color: var(--color-text); }
.page-desc { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }

.stats-grid { margin-bottom: 28px; }

.stat-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 14px;
  transition: all var(--transition-base);
  margin-bottom: 16px;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.stat-icon-box {
  width: 48px; height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-emoji { font-size: 20px; }
.stat-body { flex: 1; min-width: 0; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--color-text); line-height: 1; }
.stat-label { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; }

.health-section { margin-top: 4px; }
.section-title { font-size: 17px; font-weight: 700; color: var(--color-text); margin-bottom: 16px; }

.health-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
  transition: all var(--transition-base);
}
.health-card:hover { box-shadow: var(--shadow-md); }
.health-card.status-healthy { border-left: 3px solid #34C759; }
.health-card.status-unhealthy { border-left: 3px solid #FF3B30; }
.health-card.status-unknown { border-left: 3px solid #FF9500; }

.pulse-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  display: block;
}
.pulse-dot.green { background: #34C759; box-shadow: 0 0 0 4px rgba(52,199,89,0.2); }
.pulse-dot.red { background: #FF3B30; box-shadow: 0 0 0 4px rgba(255,59,48,0.2); }
.pulse-dot.yellow { background: #FF9500; box-shadow: 0 0 0 4px rgba(255,149,0,0.2); }

.health-name { font-size: 14px; font-weight: 600; color: var(--color-text); }
.health-status { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }

.uptime-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 8px;
}
</style>
