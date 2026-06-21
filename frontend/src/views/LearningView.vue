<template>
  <div class="learning-page">
    <div class="page-header">
      <div>
        <h3>我的学习路径</h3>
        <p class="page-desc">在课程AI对话中自动生成，点击步骤可切换状态</p>
      </div>
    </div>

    <el-empty v-if="paths.length === 0 && !loading" description="暂无学习路径，进入课程后在AI对话中说出你的学习目标即可自动生成" :image-size="100" />

    <div v-loading="loading" class="paths-list">
      <div v-for="path in paths" :key="path.id" class="path-card">
        <div class="path-header">
          <div class="path-info">
            <h4>{{ path.title }}</h4>
            <p>{{ path.description }}</p>
          </div>
          <div class="path-meta">
            <el-tag :type="['warning', 'success', 'info'][path.status]" size="small" effect="plain" round>
              {{ ['进行中', '已完成', '已放弃'][path.status] }}
            </el-tag>
            <el-button text type="danger" size="small" @click="removePath(path.id)">
              <el-icon :size="14"><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="path-progress">
          <div class="progress-info">
            <span class="progress-text">完成进度</span>
            <span class="progress-num">{{ path.completedSteps }}/{{ path.totalSteps }} 步</span>
          </div>
          <el-progress
            :percentage="path.totalSteps ? Math.round(path.completedSteps / path.totalSteps * 100) : 0"
            :stroke-width="8"
            :color="progressGradient"
            :show-text="false"
          />
        </div>

        <div v-if="path.steps && path.steps.length" class="steps-timeline">
          <div
            v-for="(step, si) in path.steps"
            :key="step.id"
            class="step-item"
            :class="{ 'step-done': step.status === 2, 'step-active': step.status === 1 }"
            @click="cycleStep(path.id, step)"
          >
            <div class="step-indicator">
              <div class="step-dot">
                <el-icon v-if="step.status === 2" :size="14"><Check /></el-icon>
                <div v-else-if="step.status === 1" class="dot-active"></div>
                <div v-else class="dot-empty"></div>
              </div>
              <div v-if="si < path.steps.length - 1" class="step-connector" :class="{ 'connector-done': step.status === 2 }"></div>
            </div>
            <div class="step-content">
              <div class="step-order">步骤 {{ step.stepOrder }}</div>
              <div class="step-title">{{ step.title }}</div>
              <div class="step-desc">{{ step.description }}</div>
            </div>
            <div class="step-status-badge">
              <el-tag size="small" :type="['info', '', 'success'][step.status]" effect="plain" round>
                {{ ['待开始', '进行中', '已完成'][step.status] }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { learningApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Check } from '@element-plus/icons-vue';

const paths = ref([]);
const loading = ref(false);
const progressGradient = [
  { color: '#C1803A', percentage: 30 },
  { color: '#B5651D', percentage: 60 },
  { color: '#5B8C5A', percentage: 100 },
];

onMounted(() => loadPaths());

async function loadPaths() { loading.value = true; try { const r = await learningApi.listPaths(); if (r.code === 200) paths.value = r.data || []; } catch {} finally { loading.value = false; } }

function cycleStep(pathId, step) {
  const next = step.status === 2 ? 0 : step.status + 1;
  learningApi.updateStepStatus(pathId, step.id, ['pending', 'in_progress', 'completed'][next]).then(() => loadPaths());
}

async function removePath(id) {
  try {
    await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' });
    await learningApi.deletePath(id);
    await loadPaths();
    ElMessage.success('已删除');
  } catch {}
}
</script>

<style scoped>
.learning-page { max-width: 880px; margin: 0 auto; }

.page-header { margin-bottom: 28px; }
.page-header h3 { font-size: 24px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.page-desc { font-size: 14px; color: var(--color-text-muted); margin-top: 4px; }

.paths-list { display: flex; flex-direction: column; gap: 24px; }

.path-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  padding: 28px 32px; box-shadow: var(--shadow-card);
  transition: all 0.25s ease; border: 1px solid transparent;
}
.path-card:hover { box-shadow: var(--shadow-md); border-color: var(--color-border); }

.path-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; }
.path-info h4 { font-size: 20px; font-weight: 700; color: var(--color-text); margin-bottom: 8px; letter-spacing: -0.01em; }
.path-info p { font-size: 14px; color: var(--color-text-muted); line-height: 1.6; }
.path-meta { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.path-progress {
  background: var(--color-bg); border-radius: 12px;
  padding: 18px 22px; margin-bottom: 26px;
}
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.progress-text { font-size: 13px; color: var(--color-text-muted); font-weight: 500; }
.progress-num { font-size: 14px; color: var(--color-text-secondary); font-weight: 700; }

.steps-timeline { display: flex; flex-direction: column; }

.step-item {
  display: flex; align-items: flex-start; gap: 16px;
  padding: 14px 16px; border-radius: 10px;
  cursor: pointer; transition: all 0.2s ease;
}
.step-item:hover { background: var(--color-bg-hover); }
.step-item.step-done { opacity: 0.6; }

.step-indicator {
  display: flex; flex-direction: column; align-items: center;
  padding-top: 4px; flex-shrink: 0;
}
.step-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.2s ease;
}
.dot-empty { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #D4CCC2; }
.dot-active { width: 12px; height: 12px; border-radius: 50%; background: var(--color-primary); box-shadow: 0 0 0 5px rgba(181,101,29,0.12); }
.step-done .step-dot { background: var(--color-success); color: #fff; }

.step-connector { width: 2px; flex: 1; min-height: 22px; background: #E9E3DA; margin-top: 4px; transition: background 0.3s ease; }
.connector-done { background: var(--color-success); }

.step-content { flex: 1; min-width: 0; }
.step-order { font-size: 11px; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.step-title { font-size: 15px; font-weight: 600; color: var(--color-text); margin-bottom: 4px; }
.step-done .step-title { text-decoration: line-through; color: var(--color-text-muted); }
.step-desc { font-size: 13px; color: var(--color-text-muted); line-height: 1.6; }

.step-status-badge { flex-shrink: 0; padding-top: 3px; }
</style>