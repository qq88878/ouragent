<template>
  <div class="learning-page">
    <div class="page-header">
      <h3>我的学习路径</h3>
      <el-button type="primary" @click="showGenerateDialog = true">生成新路径</el-button>
    </div>

    <el-empty v-if="paths.length === 0 && !loading" description="暂无学习路径，点击上方按钮生成" />

    <div v-loading="loading" class="path-list">
      <el-card v-for="path in paths" :key="path.id" class="path-card" shadow="hover">
        <div class="path-header">
          <div>
            <h4>{{ path.title }}</h4>
            <p class="path-desc">{{ path.description }}</p>
          </div>
          <div class="path-meta">
            <el-tag :type="statusType(path.status)" size="small">{{ statusText(path.status) }}</el-tag>
            <el-button text type="danger" size="small" @click="deletePath(path.id)">删除</el-button>
          </div>
        </div>

        <el-progress
          :percentage="path.totalSteps > 0 ? Math.round(path.completedSteps / path.totalSteps * 100) : 0"
          :stroke-width="8"
          style="margin: 12px 0;"
        />
        <span class="progress-text">{{ path.completedSteps }} / {{ path.totalSteps }} 步骤已完成</span>

        <div v-if="path.steps && path.steps.length > 0" class="steps-list">
          <div
            v-for="step in path.steps"
            :key="step.id"
            class="step-item"
            :class="'status-' + step.status"
          >
            <div class="step-order">{{ step.stepOrder }}</div>
            <div class="step-info">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-desc">{{ step.description }}</div>
            </div>
            <el-select
              :model-value="stepStatusText(step.status)"
              size="small"
              style="width: 110px;"
              @change="(val) => updateStep(path.id, step.id, val)"
            >
              <el-option label="待开始" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </div>
        </div>

        <el-button text type="primary" @click="toggleExpand(path.id)" style="margin-top: 8px;">
          {{ expandedPaths.has(path.id) ? '收起步骤' : '展开步骤' }}
        </el-button>
      </el-card>
    </div>

    <el-dialog v-model="showGenerateDialog" title="生成学习路径" width="500px">
      <el-form :model="generateForm" label-width="80px">
        <el-form-item label="课程" required>
          <el-select v-model="generateForm.courseId" placeholder="选择课程" style="width: 100%;">
            <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学习目标">
          <el-input v-model="generateForm.goal" placeholder="例如：掌握Python基础语法" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="generatePath">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { learningApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';

const paths = ref([]);
const courses = ref([]);
const loading = ref(false);
const generating = ref(false);
const showGenerateDialog = ref(false);
const expandedPaths = ref(new Set());
const generateForm = ref({ courseId: null, goal: '' });

onMounted(async () => {
  await loadPaths();
  await loadCourses();
});

async function loadPaths() {
  loading.value = true;
  try {
    const res = await learningApi.listPaths();
    if (res.code === 200) paths.value = res.data || [];
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

async function loadCourses() {
  try {
    const res = await courseApi.list({ page: 1, size: 100 });
    if (res.code === 200) courses.value = res.data?.records || [];
  } catch { /* ignore */ }
}

async function generatePath() {
  if (!generateForm.value.courseId) {
    ElMessage.warning('请选择课程');
    return;
  }
  generating.value = true;
  try {
    const res = await learningApi.generatePath(generateForm.value);
    if (res.code === 200) {
      ElMessage.success('学习路径生成成功');
      showGenerateDialog.value = false;
      await loadPaths();
    }
  } catch {
    ElMessage.error('生成失败');
  } finally { generating.value = false; }
}

async function updateStep(pathId, stepId, status) {
  try {
    await learningApi.updateStepStatus(pathId, stepId, status);
    await loadPaths();
  } catch {
    ElMessage.error('更新失败');
  }
}

async function deletePath(id) {
  try {
    await ElMessageBox.confirm('确定删除此学习路径？', '提示', { type: 'warning' });
    await learningApi.deletePath(id);
    await loadPaths();
    ElMessage.success('已删除');
  } catch { /* cancel */ }
}

function toggleExpand(pathId) {
  const set = new Set(expandedPaths.value);
  if (set.has(pathId)) set.delete(pathId);
  else set.add(pathId);
  expandedPaths.value = set;
}

function statusText(s) { return ['进行中', '已完成', '已放弃'][s] || '未知'; }
function statusType(s) { return ['warning', 'success', 'info'][s] || 'info'; }
function stepStatusText(s) { return ['pending', 'in_progress', 'completed'][s] || 'pending'; }
</script>

<style scoped>
.learning-page { max-width: 900px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.path-card { margin-bottom: 16px; }
.path-header { display: flex; justify-content: space-between; align-items: flex-start; }
.path-header h4 { margin: 0 0 4px 0; font-size: 16px; }
.path-desc { color: #909399; font-size: 13px; margin: 0; }
.path-meta { display: flex; align-items: center; gap: 8px; }
.progress-text { font-size: 12px; color: #909399; }
.steps-list { margin-top: 12px; }
.step-item {
  display: flex; align-items: center; gap: 12px; padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}
.step-item:last-child { border-bottom: none; }
.step-item.status-2 { opacity: 0.6; }
.step-order {
  width: 28px; height: 28px; border-radius: 50%; background: #409eff; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0;
}
.step-item.status-2 .step-order { background: #67c23a; }
.step-info { flex: 1; }
.step-title { font-size: 14px; color: #303133; }
.step-desc { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
