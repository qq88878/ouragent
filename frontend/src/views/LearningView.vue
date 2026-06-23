<template>
  <div class="learning-page">
    <div class="page-header">
      <div>
        <h3>我的学习路径</h3>
        <p class="page-desc">在课程AI对话中自动生成，点击步骤可切换状态</p>
      </div>
      <div class="header-actions">
        <el-switch v-model="showArchived" active-text="显示已归档" @change="loadPaths" />
      </div>
    </div>

    <el-empty v-if="paths.length === 0 && !loading" description="暂无学习路径，进入课程后在AI对话中说出你的学习目标即可自动生成" :image-size="100" />

    <div v-loading="loading" class="paths-list">
      <div v-for="path in paths" :key="path.id" class="path-card" :class="{ 'path-archived': path.archived === 1 }">
        <div class="path-header">
          <div class="path-info">
            <h4>
              <el-icon v-if="path.starred === 1" class="star-icon" color="#E6A23C"><Star /></el-icon>
              {{ path.title }}
              <span v-if="path.version > 1" class="version-badge">v{{ path.version }}</span>
            </h4>
            <p>{{ path.description }}</p>
          </div>
          <div class="path-meta">
            <el-tag :type="['warning', 'success', 'info'][path.status]" size="small" effect="plain" round>
              {{ ['进行中', '已完成', '已放弃'][path.status] }}
            </el-tag>
            <el-button text size="small" :type="path.starred === 1 ? 'warning' : 'default'" @click="toggleStar(path.id)">
              <el-icon :size="14"><Star /></el-icon>
            </el-button>
            <el-button text size="small" @click="toggleArchive(path.id)">
              <el-icon :size="14"><FolderOpened /></el-icon>
            </el-button>
            <el-button text type="danger" size="small" @click="removePath(path.id)">
              <el-icon :size="14"><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="path-progress">
          <div class="progress-info">
            <span class="progress-text">完成进度</span>
            <div>
              <span class="progress-num">{{ path.completedSteps }}/{{ path.totalSteps }} 步</span>
              <span v-if="path.estimatedRemainingHours > 0" class="progress-remain">预计还需约 {{ path.estimatedRemainingHours }} 小时</span>
            </div>
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
            :ref="el => { if (el) stepRefs[step.id] = el }"
            class="step-item"
            :class="{ 'step-done': step.status === 2, 'step-active': step.status === 1, 'step-current': step.isCurrent }"
            @click="cycleStep(path.id, step)"
          >
            <div class="step-indicator">
              <div class="step-dot">
                <el-icon v-if="step.status === 2" :size="14"><Check /></el-icon>
                <el-icon v-else-if="step.stepType === 'PRACTICE'" :size="14" color="var(--color-primary)"><EditPen /></el-icon>
                <el-icon v-else-if="step.stepType === 'REVIEW'" :size="14" color="var(--color-primary)"><RefreshRight /></el-icon>
                <el-icon v-else-if="step.stepType === 'PROJECT'" :size="14" color="var(--color-primary)"><Aim /></el-icon>
                <el-icon v-else :size="14" color="var(--color-primary)"><Reading /></el-icon>
                <div v-if="step.status === 1" class="dot-active"></div>
              </div>
              <div v-if="si < path.steps.length - 1" class="step-connector" :class="{ 'connector-done': step.status === 2 }"></div>
            </div>
            <div class="step-content">
              <div class="step-order">
                步骤 {{ step.stepOrder }}
                <span v-if="step.stepType" class="step-type-tag">{{ stepTypeLabel[step.stepType] }}</span>
                <span v-if="step.estimatedHours" class="step-hours">约{{ step.estimatedHours }}h</span>
              </div>
              <div class="step-title">{{ step.title }}</div>
              <div class="step-desc">{{ step.description }}</div>
              <el-button
                v-if="step.isCurrent && step.status !== 2"
                type="primary" size="small" plain
                class="start-btn"
                @click.stop="startLearning(step)"
              >
                开始学习
              </el-button>
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
import { ref, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { learningApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Check, Star, FolderOpened, Reading, EditPen, RefreshRight, Aim } from '@element-plus/icons-vue';

const router = useRouter();
const paths = ref([]);
const loading = ref(false);
const showArchived = ref(false);
const stepRefs = ref({});

const stepTypeLabel = { CONCEPT: '概念', PRACTICE: '练习', REVIEW: '复习', PROJECT: '项目' };

const progressGradient = [
  { color: '#C1803A', percentage: 30 },
  { color: '#B5651D', percentage: 60 },
  { color: '#5B8C5A', percentage: 100 },
];

onMounted(() => loadPaths());

async function loadPaths() {
  loading.value = true;
  try {
    const r = await learningApi.listPaths(showArchived.value);
    if (r.code === 200) paths.value = r.data || [];
  } catch {} finally {
    loading.value = false;
  }
  await nextTick();
  scrollToCurrent();
}

function scrollToCurrent() {
  for (const path of paths.value) {
    if (!path.steps) continue;
    const current = path.steps.find(s => s.isCurrent);
    if (current && stepRefs.value[current.id]) {
      stepRefs.value[current.id].scrollIntoView({ behavior: 'smooth', block: 'center' });
      break;
    }
  }
}

function cycleStep(pathId, step) {
  const next = step.status === 2 ? 0 : step.status + 1;
  learningApi.updateStepStatus(pathId, step.id, ['pending', 'in_progress', 'completed'][next]).then(() => loadPaths());
}

function startLearning(step) {
  if (step.knowledgeBaseId) {
    router.push({ path: '/knowledge', query: { id: step.knowledgeBaseId } });
  } else {
    ElMessage.info('该步骤暂未关联知识库内容');
  }
}

async function toggleStar(id) {
  await learningApi.toggleStar(id);
  await loadPaths();
}

async function toggleArchive(id) {
  await learningApi.toggleArchive(id);
  await loadPaths();
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

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.page-header h3 { font-size: 24px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.page-desc { font-size: 14px; color: var(--color-text-muted); margin-top: 4px; }
.header-actions { display: flex; align-items: center; gap: 12px; }

.paths-list { display: flex; flex-direction: column; gap: 24px; }

.path-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  padding: 28px 32px; box-shadow: var(--shadow-card);
  transition: all 0.25s ease; border: 1px solid transparent;
}
.path-card:hover { box-shadow: var(--shadow-md); border-color: var(--color-border); }
.path-archived { opacity: 0.55; }

.path-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; }
.path-info h4 { font-size: 20px; font-weight: 700; color: var(--color-text); margin-bottom: 8px; letter-spacing: -0.01em; display: flex; align-items: center; gap: 6px; }
.path-info p { font-size: 14px; color: var(--color-text-muted); line-height: 1.6; }
.path-meta { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.star-icon { vertical-align: middle; }
.version-badge { font-size: 11px; color: var(--color-text-muted); background: var(--color-bg); padding: 1px 6px; border-radius: 8px; font-weight: 500; }

.path-progress {
  background: var(--color-bg); border-radius: 12px;
  padding: 18px 22px; margin-bottom: 26px;
}
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.progress-text { font-size: 13px; color: var(--color-text-muted); font-weight: 500; }
.progress-num { font-size: 14px; color: var(--color-text-secondary); font-weight: 700; }
.progress-remain { font-size: 12px; color: var(--color-text-muted); margin-left: 10px; }

.steps-timeline { display: flex; flex-direction: column; }

.step-item {
  display: flex; align-items: flex-start; gap: 16px;
  padding: 14px 16px; border-radius: 10px;
  cursor: pointer; transition: all 0.2s ease;
}
.step-item:hover { background: var(--color-bg-hover); }
.step-item.step-done { opacity: 0.6; }
.step-item.step-current {
  background: rgba(181, 101, 29, 0.04);
  border-left: 3px solid var(--color-primary);
  padding-left: 13px;
}

.step-indicator {
  display: flex; flex-direction: column; align-items: center;
  padding-top: 4px; flex-shrink: 0;
}
.step-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.2s ease;
  position: relative;
}
.dot-active {
  position: absolute; inset: -4px; border-radius: 50%;
  border: 2px solid var(--color-primary); opacity: 0.3;
  animation: pulse-ring 1.5s ease-out infinite;
}
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.4; }
  100% { transform: scale(1.2); opacity: 0; }
}
.step-done .step-dot { background: var(--color-success); color: #fff; }

.step-connector { width: 2px; flex: 1; min-height: 22px; background: #E9E3DA; margin-top: 4px; transition: background 0.3s ease; }
.connector-done { background: var(--color-success); }

.step-content { flex: 1; min-width: 0; }
.step-order { font-size: 11px; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.step-type-tag { font-size: 10px; color: var(--color-primary); background: rgba(181, 101, 29, 0.08); padding: 1px 5px; border-radius: 4px; text-transform: none; letter-spacing: 0; }
.step-hours { font-size: 10px; color: var(--color-text-muted); }
.step-title { font-size: 15px; font-weight: 600; color: var(--color-text); margin-bottom: 4px; }
.step-done .step-title { text-decoration: line-through; color: var(--color-text-muted); }
.step-desc { font-size: 13px; color: var(--color-text-muted); line-height: 1.6; }
.start-btn { margin-top: 8px; }

.step-status-badge { flex-shrink: 0; padding-top: 3px; }
</style>
