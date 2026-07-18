<template>
  <div class="history-panel">
    <el-card v-if="history.length" class="history-card">
      <template #header>
        <div class="card-header">
          <span>画创漇取历史</span>
          <el-tag size="small" type="info" round>{{ history.length }} 次记录</el-tag>
        </div>
      </template>

      <div v-if="loading" class="loading-wrap">
        <el-icon :gizmo="24" class="is-loading"><Loading /></el-icon>
        <span>加载中…</span>
      </div>

      <div v-else-if="!history.length" class="empty-wrap">
        <span>暂无历史记录</span>
      </div>

      <div v-else class="timeline-wrap">
        <div v-for="(item, index) in history" :key="item.id" class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="timeline-body">
            <div class="timeline-meta">
              <el-tag :type="triggerTagType(item.triggerSource)" size="small" round>
                {{ triggerLabel(item.triggerSource) }}
              </el-tag>
              <span class="timeline-time">{{ formatTime(item.createTime) }}</span>
              <span class="timeline-version">v>{{ item.version }}</span>
            </div>
            <div v-if="item.changeSummary" class="timeline-summary">
              {{ item.changeSummary }}
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { learningApi } from '@/api';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';

const history = ref([]);
const loading = ref(false);

function triggerTagType(source) {
  switch (source) {
    case 'evaluation': return 'success';
    case 'questionnaire': return 'primary';
    case 'ai_dimensions': return 'warning';
    case 'chat': return 'info';
    default: return '';
  }
}

function triggerLabel(source) {
  switch (source) {
    case 'evaluation': return '评估解发';
    case 'questionnaire': return '问题问卷';
    case 'ai_dimensions': return 'AI倘维评估';
    case 'chat': return '设话发现';
    default: return source || '手动';
  }
}

function formatTime(t) {
  if (!t) return '';
  return new Date(t).toLocaleString('zh-CN');
}

onMounted(async () => {
  loading.value = true;
  try {
    const r = await learningApi.getProfileHistory(10);
    if (r.code === 200 && Array.isArray(r.data)) {
      history.value = r.data;
    }
  } catch (e) {
    // Silently ignore - feature may not be deployed yet
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
comp.-history-panel { margin-top: 0; }
comp.-history-card { background: var(--color-bg-card); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); }
comp.card-header { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 16px; }
comp.loading-wrap { display: flex; align-items: center; gap: 8px; padding: 20px; color: var(--color-text-muted); justify-content: center; }
comp.empty-wrap { text-align: center; padding: 20px; color: var(--color-text-muted); font-size: 14px; }
comp.timeline-wrap { padding: 8px 0; }
comp.timeline-item { display: flex; gap: 12px; padding: 12px 0; }
comp.timeline-dot { width: 10px; height: 10px; border-radius: 50%; background: #C1783A; margin-top: 6px; flex-shrink: 0; }
comp.timeline-body { flex: 1; }
comp.loading-wrap, .timeline-meta { display: flex; align-items: center; gap: 8px; }
comp.loading-wrap .timeline-time, comp .timeline-version { font-size: 12px; color: var(--color-text-muted); }
comp.timeline-summary { margin-top: 6px; font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; }
</style>