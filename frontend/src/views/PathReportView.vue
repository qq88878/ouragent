<template>
  <div class="report-page">
    <div class="report-header">
      <el-button text @click="$router.push('/learning')"><el-icon><ArrowLeft /></el-icon> 返回列表</el-button>
    </div>

    <div v-loading="loading">
      <!-- 报告头部 -->
      <div class="report-hero">
        <div class="hero-icon">🏆</div>
        <h1>{{ path.title }}</h1>
        <p class="hero-desc">{{ path.description }}</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hs-val">{{ path.completedSteps }}/{{ path.totalSteps }}</span>
            <span class="hs-label">完成步骤</span>
          </div>
          <div class="hero-stat">
            <span class="hs-val">{{ statusLabel }}</span>
            <span class="hs-label">状态</span>
          </div>
          <div class="hero-stat">
            <span class="hs-val">{{ studyHours }}h {{ studyMins }}m</span>
            <span class="hs-label">学习时长</span>
          </div>
          <div class="hero-stat">
            <span class="hs-val">{{ path.correctRate || '-' }}{{ path.correctRate ? '%' : '' }}</span>
            <span class="hs-label">正确率</span>
          </div>
        </div>
      </div>

      <!-- 步骤完成情况 -->
      <div class="report-section">
        <h3>📋 步骤完成情况</h3>
        <div class="steps-review">
          <div v-for="step in path.steps" :key="step.id" class="review-step" :class="{ done: step.status === 2 }">
            <div class="rs-indicator">
              <el-icon v-if="step.status === 2" color="#67c23a"><Check /></el-icon>
              <el-icon v-else color="#c0c4cc"><Clock /></el-icon>
            </div>
            <div class="rs-info">
              <div class="rs-title">
                步骤 {{ step.stepOrder }}: {{ step.title }}
                <el-tag v-if="step.isCheckpoint === 1" type="warning" size="small" effect="plain">自测</el-tag>
              </div>
              <div class="rs-type">{{ stepTypeLabel[step.stepType] || step.stepType }} · {{ step.estimatedHours || '-' }}h</div>
              <div v-if="step.status === 2 && step.exerciseResults" class="rs-result">
                <span v-if="getStepScore(step) !== null" class="rs-score">得分: {{ getStepScore(step) }}</span>
              </div>
            </div>
            <el-tag :type="step.status === 2 ? 'success' : 'info'" size="small" effect="plain">
              {{ step.status === 2 ? '已完成' : step.status === 1 ? '学习中' : '待开始' }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 建议 -->
      <div class="report-section">
        <h3>💡 学习建议</h3>
        <div class="suggestion-card">
          <p v-if="path.status === 1">🎉 恭喜你完成了全部学习内容！建议回顾薄弱环节，或开始新的学习路径。</p>
          <p v-else-if="progressPercent >= 80">👍 进度不错，马上就能完成了！重点关注剩余的步骤。</p>
          <p v-else-if="progressPercent >= 50">📖 已过半程，保持节奏继续前进。</p>
          <p v-else>🚀 学习之旅刚刚开始，坚持下去！建议每天安排固定时间学习。</p>
        </div>
        <div class="actions">
          <el-button type="primary" @click="$router.push(`/learning/${path.id}`)">继续学习</el-button>
          <el-button @click="$router.push('/learning')">返回列表</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { learningApi } from '@/api';

const route = useRoute();
const path = ref({ steps: [] });
const loading = ref(false);

const stepTypeLabel = { CONCEPT: '概念学习', PRACTICE: '实践练习', REVIEW: '复习巩固', PROJECT: '项目实战' };
const statusLabel = computed(() => ['进行中', '已完成', '已放弃'][path.value.status]);
const progressPercent = computed(() => {
  if (!path.value.totalSteps) return 0;
  return Math.round((path.value.completedSteps || 0) / path.value.totalSteps * 100);
});
const studyHours = computed(() => Math.floor((path.value.totalStudyMinutes || 0) / 60));
const studyMins = computed(() => (path.value.totalStudyMinutes || 0) % 60);

function getStepScore(step) {
  if (!step.exerciseResults) return null;
  try {
    const data = typeof step.exerciseResults === 'string' ? JSON.parse(step.exerciseResults) : step.exerciseResults;
    return data.total_score != null ? data.total_score + '/' + (data.total_count * 100 || '?') : null;
  } catch { return null; }
}

onMounted(async () => {
  loading.value = true;
  try {
    const res = await learningApi.getPathById(route.params.pathId);
    path.value = res.data || res;
  } catch (e) {
    ElMessage.error('加载报告失败');
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.report-page { max-width: 800px; margin: 0 auto; }

.report-header { margin-bottom: 20px; }

.report-hero {
  text-align: center; padding: 40px 20px;
  background: linear-gradient(135deg, rgba(181, 101, 29, 0.06), rgba(181, 101, 29, 0.02));
  border-radius: var(--radius-xl); margin-bottom: 32px;
}
.hero-icon { font-size: 56px; margin-bottom: 12px; }
.report-hero h1 { font-size: 26px; font-weight: 700; margin: 0 0 8px; }
.hero-desc { font-size: 14px; color: var(--color-text-muted); max-width: 500px; margin: 0 auto 20px; }

.hero-stats { display: flex; justify-content: center; gap: 40px; }
.hero-stat { text-align: center; }
.hs-val { font-size: 24px; font-weight: 700; color: var(--color-primary); display: block; }
.hs-label { font-size: 12px; color: var(--color-text-muted); }

.report-section {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 24px 28px; margin-bottom: 20px; box-shadow: var(--shadow-card);
}
.report-section h3 { margin: 0 0 16px; font-size: 17px; font-weight: 700; }

.steps-review { display: flex; flex-direction: column; gap: 8px; }
.review-step {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; border-radius: 8px; background: var(--color-bg);
}
.review-step.done { opacity: 0.65; }

.rs-indicator { flex-shrink: 0; }
.rs-info { flex: 1; min-width: 0; }
.rs-title { font-size: 14px; font-weight: 600; color: var(--color-text); display: flex; align-items: center; gap: 6px; }
.rs-type { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }
.rs-result { font-size: 12px; color: var(--color-primary); margin-top: 2px; }

.suggestion-card {
  padding: 20px; background: var(--color-bg); border-radius: 10px; margin-bottom: 16px;
}
.suggestion-card p { margin: 0; font-size: 15px; color: var(--color-text-secondary); line-height: 1.6; }
.actions { display: flex; gap: 10px; }
</style>
