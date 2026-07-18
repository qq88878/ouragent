<template>
  <div class="path-detail-page">
    <!-- 顶栏 -->
    <div class="top-bar">
      <div class="top-left">
        <el-button text @click="$router.push('/learning')">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <div class="path-title-area">
          <h2>{{ path.title }}</h2>
          <el-tag :type="statusTagType" size="small" effect="plain" round>{{ statusLabel }}</el-tag>
        </div>
      </div>
      <div class="top-right">
        <span class="progress-label">进度 {{ progressPercent }}%</span>
        <el-progress :percentage="progressPercent" :stroke-width="6" :show-text="false" style="width:120px" />
        <el-button v-if="hasCheckpoint" type="warning" size="small" plain @click="goToTest">
          阶段自测
        </el-button>
      </div>
    </div>

    <div class="main-area" v-loading="loading">
      <!-- 左侧：学习内容区 -->
      <div class="content-panel">
        <!-- 加载提示 -->
        <div v-if="!currentStep" class="empty-state">
          <el-empty description="请从右侧选择一个步骤开始学习" />
        </div>

        <template v-else>
          <!-- 步骤标题区 -->
          <div class="step-header">
            <div class="step-meta">
              <span class="step-num">步骤 {{ currentStep.stepOrder }}</span>
              <el-tag :type="stepTypeColor[currentStep.stepType]" size="small" effect="light">
                {{ stepTypeLabel[currentStep.stepType] || currentStep.stepType }}
              </el-tag>
              <span v-if="currentStep.estimatedHours" class="step-hours">
                <el-icon><Clock /></el-icon> 约{{ currentStep.estimatedHours }}h
              </span>
            </div>
            <h3>{{ currentStep.title }}</h3>
            <p class="step-desc">{{ currentStep.description }}</p>
          </div>

          <!-- 学习内容区（Markdown 渲染） -->
          <div class="learning-content" v-if="currentStep.content">
            <div class="content-header">
              <h4>📖 学习内容</h4>
              <el-button v-if="!currentStep.content || currentStep.content.length < 20" type="primary" size="small" :loading="generatingContent" @click="generateContent">
                AI 生成内容
              </el-button>
            </div>
            <div class="markdown-body" v-html="renderedContent"></div>
          </div>
          <div v-else class="content-placeholder">
            <el-empty description="暂未生成学习内容" :image-size="60">
              <el-button type="primary" :loading="generatingContent" @click="generateContent">
                AI 生成学习内容
              </el-button>
            </el-empty>
          </div>

          <!-- 课内练习区 -->
          <div class="exercises-section" v-if="exercises.length > 0">
            <div class="section-header">
              <h4>✏️ 课内练习</h4>
              <span v-if="exerciseResults" class="exercise-score">
                得分: {{ exerciseResults.total_score }} / {{ exerciseResults.total_count * 100 }}
              </span>
            </div>
            <div v-for="(q, qi) in exercises" :key="qi" class="exercise-card" :class="{ correct: q.userCorrect, wrong: q.userCorrect === false }">
              <div class="q-header">
                <span class="q-num">第 {{ qi + 1 }} 题</span>
                <el-tag :type="q.difficulty === 'hard' ? 'danger' : q.difficulty === 'easy' ? 'success' : 'warning'" size="small" effect="plain">
                  {{ { easy: '简单', medium: '中等', hard: '困难' }[q.difficulty] || q.difficulty }}
                </el-tag>
              </div>
              <div class="q-question">{{ q.question }}</div>
              <div v-if="q.type === 'choice' && q.options" class="q-options">
                <el-radio-group v-model="userAnswers[qi]" :disabled="!!exerciseResults">
                  <el-radio v-for="(opt, oi) in q.options" :key="oi" :value="opt" class="q-option">
                    {{ opt }}
                  </el-radio>
                </el-radio-group>
              </div>
              <div v-else class="q-input">
                <el-input v-model="userAnswers[qi]" type="textarea" :rows="2" placeholder="请输入你的答案..." :disabled="!!exerciseResults" />
              </div>
              <!-- 评估结果 -->
              <div v-if="q.evaluation" class="q-evaluation">
                <div class="eval-header">
                  <el-tag :type="q.evaluation.is_correct ? 'success' : 'danger'" size="small">
                    {{ q.evaluation.is_correct ? '✓ 正确' : '✗ 错误' }}
                  </el-tag>
                  <span class="eval-score">评分: {{ q.evaluation.score }}</span>
                </div>
                <div v-if="!q.evaluation.is_correct" class="eval-correct">
                  <strong>正确答案:</strong> {{ q.answer }}
                </div>
                <div v-if="q.evaluation.suggestions?.length" class="eval-suggestions">
                  <strong>建议:</strong>
                  <ul><li v-for="s in q.evaluation.suggestions" :key="s">{{ s }}</li></ul>
                </div>
                <div v-if="q.evaluation.encouragement" class="eval-encouragement">
                  💬 {{ q.evaluation.encouragement }}
                </div>
              </div>
            </div>
            <div class="exercise-actions">
              <el-button v-if="!exerciseResults" type="primary" :loading="evaluating" @click="submitExercises">
                提交练习
              </el-button>
              <el-button v-else type="success" @click="markStepComplete">
                标记完成 →
              </el-button>
            </div>
          </div>

          <!-- 无练习题时的生成按钮 -->
          <div v-else-if="currentStep.stepType !== 'PROJECT'" class="exercise-generate">
            <el-button type="primary" plain :loading="generatingExercises" @click="generateExercises">
              AI 生成课内练习
            </el-button>
          </div>

          <!-- 底部导航 -->
          <div class="step-nav-bottom">
            <el-button v-if="prevStep" @click="selectStep(prevStep)" :icon="'ArrowLeft'">上一步</el-button>
            <el-button v-if="nextStep" type="primary" @click="selectStep(nextStep)">
              下一步 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>
      </div>

      <!-- 右侧：步骤导航 + 统计 -->
      <div class="side-panel">
        <div class="side-card">
          <h4>📋 学习步骤</h4>
          <div class="step-list">
            <div
              v-for="(step, si) in path.steps"
              :key="step.id"
              class="side-step"
              :class="{ active: currentStep?.id === step.id, done: step.status === 2, checkpoint: step.isCheckpoint === 1 }"
              @click="selectStep(step)"
            >
              <div class="side-step-dot">
                <el-icon v-if="step.status === 2"><Check /></el-icon>
                <el-icon v-else-if="step.isCheckpoint === 1"><Aim /></el-icon>
                <span v-else>{{ si + 1 }}</span>
              </div>
              <div class="side-step-info">
                <div class="side-step-title">{{ step.title }}</div>
                <div class="side-step-type">
                  {{ stepTypeLabel[step.stepType] || step.stepType }}
                  <span v-if="step.estimatedHours">· {{ step.estimatedHours }}h</span>
                </div>
              </div>
              <el-tag v-if="step.status === 2" type="success" size="small" effect="plain">✓</el-tag>
              <el-tag v-else-if="step.status === 1" type="warning" size="small" effect="plain">学习中</el-tag>
            </div>
          </div>
        </div>

        <div class="side-card">
          <h4>📊 学习统计</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-val">{{ path.completedSteps }}/{{ path.totalSteps }}</div>
              <div class="stat-label">完成步骤</div>
            </div>
            <div class="stat-item">
              <div class="stat-val">{{ Math.floor((path.totalStudyMinutes || 0) / 60) }}h{{ (path.totalStudyMinutes || 0) % 60 }}m</div>
              <div class="stat-label">学习时长</div>
            </div>
            <div class="stat-item">
              <div class="stat-val">{{ path.totalExercisesDone || 0 }}</div>
              <div class="stat-label">已完成练习</div>
            </div>
            <div class="stat-item">
              <div class="stat-val">{{ path.correctRate ? path.correctRate + '%' : '-' }}</div>
              <div class="stat-label">正确率</div>
            </div>
          </div>
        </div>

        <div class="side-card">
          <div class="path-actions">
            <el-button text :type="path.starred ? 'warning' : 'default'" @click="toggleStar">
              <el-icon><Star /></el-icon> {{ path.starred ? '已收藏' : '收藏' }}
            </el-button>
            <el-button text type="danger" @click="deletePath">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { learningApi, stepApi } from '@/api';
import { marked } from 'marked';

const route = useRoute();
const router = useRouter();
const path = ref({ steps: [] });
const currentStep = ref(null);
const loading = ref(false);
const generatingContent = ref(false);
const generatingExercises = ref(false);
const evaluating = ref(false);
const userAnswers = ref({});
const exerciseResults = ref(null);
const studyTimer = ref(null);
const studyMinutes = ref(0);

const stepTypeLabel = { CONCEPT: '概念', PRACTICE: '练习', REVIEW: '复习', PROJECT: '项目' };
const stepTypeColor = { CONCEPT: '', PRACTICE: 'success', REVIEW: 'warning', PROJECT: 'danger' };
const statusTagType = computed(() => ['warning', 'success', 'info'][path.value.status]);
const statusLabel = computed(() => ['进行中', '已完成', '已放弃'][path.value.status]);

const progressPercent = computed(() => {
  if (!path.value.totalSteps) return 0;
  return Math.round((path.value.completedSteps || 0) / path.value.totalSteps * 100);
});

const hasCheckpoint = computed(() => {
  return path.value.steps?.some(s => s.isCheckpoint === 1 && s.status !== 2);
});

const currentIndex = computed(() => {
  if (!currentStep.value) return -1;
  return path.value.steps?.findIndex(s => s.id === currentStep.value.id) ?? -1;
});

// AI background auto-generation hint
const generatingHint = computed(() => {
  const steps = path.value.steps || [];
  const emptyContent = steps.filter(s => !s.content || s.content.length < 20).length;
  const emptyExercises = steps.filter(s => !s.exercises || s.exercises === "{}").length;
  if (emptyContent === 0 && emptyExercises === 0) return "";
  if (emptyContent > 0 && emptyExercises > 0) return `AI正在后台生成…… (剩${emptyContent}步内容, ${emptyExercises}步练习)`;
  if (emptyContent > 0) return `生成教学内容中… (剩${emptyContent}步)`;
  return `生成练习题中… (剩${emptyExercises}步)`;
});

const prevStep = computed(() => {
  const idx = currentIndex.value;
  return idx > 0 ? path.value.steps[idx - 1] : null;
});

const nextStep = computed(() => {
  const idx = currentIndex.value;
  return idx < (path.value.steps?.length || 0) - 1 ? path.value.steps[idx + 1] : null;
});

const exercises = computed(() => {
  if (!currentStep.value?.exercises) return [];
  try {
    const data = typeof currentStep.value.exercises === 'string'
      ? JSON.parse(currentStep.value.exercises)
      : currentStep.value.exercises;
    const qs = data.questions || [];
    return qs.map(q => {
      const existing = exerciseResults.value?.questions?.find(
        r => r.question === q.question
      );
      return { ...q, evaluation: existing, userCorrect: existing?.is_correct };
    });
  } catch { return []; }
});

const renderedContent = computed(() => {
  if (!currentStep.value?.content) return '';
  return marked(currentStep.value.content);
});

function selectStep(step) {
  currentStep.value = step;
  userAnswers.value = {};
  exerciseResults.value = null;
  // parse existing exercise results
  if (step.exerciseResults) {
    try {
      const data = typeof step.exerciseResults === 'string'
        ? JSON.parse(step.exerciseResults)
        : step.exerciseResults;
      exerciseResults.value = data;
    } catch {}
  }
  autoGenerateIfNeeded(step);
}

let autoGenBusy = false;
async function autoGenerateIfNeeded(step) {
  if (!step || !path.value || autoGenBusy) return;
  autoGenBusy = true;
  const pid = path.value.id, sid = step.id;
  try {
    const s = (path.value.steps || []).find(x => x.id === sid) || step;
    if (!s.content || s.content.length < 20) {
      generatingContent.value = true;
      const r = await stepApi.generateContent(pid, sid);
      path.value = r.data || r;
      const u = (path.value.steps || []).find(x => x.id === sid);
      if (u) currentStep.value = u;
    }
    const cur = (path.value.steps || []).find(x => x.id === sid) || step;
    if (!cur.exercises || cur.exercises === "{}" || (typeof cur.exercises === "string" && cur.exercises.length < 20)) {
      generatingExercises.value = true;
      const r = await stepApi.generateExercises(pid, sid, 3);
      path.value = r.data || r;
      const u = (path.value.steps || []).find(x => x.id === sid);
      if (u) currentStep.value = u;
    }
  } catch(e) {}
  generatingContent.value = false;
  generatingExercises.value = false;
  autoGenBusy = false;
}

async function loadPath() {
  loading.value = true;
  try {
    const res = await learningApi.getPathById(route.params.pathId);
    path.value = res.data || res;
    // 选择当前步骤
    const currentIdx = res.currentStepIndex ?? res.data?.currentStepIndex ?? 0;
    const steps = path.value.steps || [];
    if (steps.length > 0) {
      selectStep(steps[currentIdx >= 0 ? Math.min(currentIdx, steps.length - 1) : 0]);
    }
  } catch (e) {
    ElMessage.error('加载路径失败');
    router.push('/learning');
  } finally {
    loading.value = false;
  }
}

async function generateContent() {
  generatingContent.value = true;
  try {
    const res = await stepApi.generateContent(path.value.id, currentStep.value.id);
    path.value = res.data || res;
    const updated = (path.value.steps || []).find(s => s.id === currentStep.value.id);
    if (updated) selectStep(updated);
    ElMessage.success('学习内容已生成');
  } catch (e) {
    ElMessage.error('内容生成失败');
  } finally {
    generatingContent.value = false;
  }
}

async function generateExercises() {
  generatingExercises.value = true;
  try {
    const res = await stepApi.generateExercises(path.value.id, currentStep.value.id, 3);
    path.value = res.data || res;
    const updated = (path.value.steps || []).find(s => s.id === currentStep.value.id);
    if (updated) selectStep(updated);
    ElMessage.success('练习题已生成');
  } catch (e) {
    ElMessage.error('练习生成失败');
  } finally {
    generatingExercises.value = false;
  }
}

async function submitExercises() {
  const answered = Object.keys(userAnswers.value).length;
  if (answered === 0) {
    ElMessage.warning('请至少回答一道题');
    return;
  }
  evaluating.value = true;
  try {
    const answers = {};
    exercises.value.forEach((q, i) => {
      if (userAnswers.value[i]) {
        answers['q_' + i] = userAnswers.value[i];
      }
    });
    const res = await stepApi.evaluateExercises(path.value.id, currentStep.value.id, answers);
    exerciseResults.value = res.data || res;
    // 更新当前步骤
    const updated = path.value.steps?.find(s => s.id === currentStep.value.id);
    if (updated) {
      try {
        updated.exerciseResults = typeof updated.exerciseResults === 'string'
          ? updated.exerciseResults
          : JSON.stringify(res.data || res);
      } catch {}
      selectStep(updated);
    }
    const score = res.data?.total_score || res.total_score || 0;
    const total = (res.data?.total_count || res.total_count || 1) * 100;
    ElMessage.success(`评估完成！得分: ${score}/${total}`);
  } catch (e) {
    ElMessage.error('评估失败');
  } finally {
    evaluating.value = false;
  }
}

async function markStepComplete() {
  try {
    await learningApi.updateStepStatus(path.value.id, currentStep.value.id, 'completed');
    currentStep.value.status = 2;
    path.value.completedSteps = (path.value.completedSteps || 0) + 1;
    ElMessage.success('步骤已完成！');
    // 自动跳到下一步
    if (nextStep.value) {
      selectStep(nextStep.value);
    } else {
      // 全部完成
      ElMessageBox.alert('恭喜！你已完成所有学习步骤！', '学习完成', {
        confirmButtonText: '查看报告',
        callback: () => router.push(`/learning/${path.value.id}/report`),
      });
    }
  } catch (e) {
    ElMessage.error('操作失败');
  }
}

function goToTest() {
  router.push(`/learning/${path.value.id}/test`);
}

async function toggleStar() {
  await learningApi.toggleStar(path.value.id);
  path.value.starred = path.value.starred ? 0 : 1;
}

async function deletePath() {
  try {
    await ElMessageBox.confirm('确定删除此学习路径？', '提示', { type: 'warning' });
    await learningApi.deletePath(path.value.id);
    ElMessage.success('已删除');
    router.push('/learning');
  } catch {}
}

// 学习计时器
onMounted(() => {
  loadPath();
  studyTimer.value = setInterval(() => {
    studyMinutes.value++;
    if (studyMinutes.value % 5 === 0) {
      stepApi.recordStudyTime(path.value.id, 5).catch(() => {});
    }
  }, 60000);
});

onBeforeUnmount(() => {
  if (studyTimer.value) clearInterval(studyTimer.value);
  if (studyMinutes.value > 0) {
    stepApi.recordStudyTime(path.value.id, studyMinutes.value).catch(() => {});
  }
});
</script>

<style scoped>
.path-detail-page { max-width: 1200px; margin: 0 auto; min-height: calc(100vh - 120px); }

/* Top Bar */
.top-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 0; border-bottom: 1px solid var(--color-border); margin-bottom: 24px;
  flex-wrap: wrap; gap: 12px;
}
.top-left { display: flex; align-items: center; gap: 16px; }
.path-title-area { display: flex; align-items: center; gap: 10px; }
.path-title-area h2 { font-size: 22px; font-weight: 700; margin: 0; }
.top-right { display: flex; align-items: center; gap: 12px; }
.progress-label { font-size: 13px; color: var(--color-text-muted); font-weight: 600; }

/* Main Layout */
.main-area { display: flex; gap: 28px; }
.content-panel { flex: 1; min-width: 0; }
.side-panel { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

/* Side Panel */
.side-card {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 20px; box-shadow: var(--shadow-card);
}
.side-card h4 { font-size: 15px; font-weight: 700; margin: 0 0 14px; color: var(--color-text); }

.step-list { display: flex; flex-direction: column; gap: 2px; }
.side-step {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  transition: all 0.15s ease;
}
.side-step:hover { background: var(--color-bg-hover); }
.side-step.active { background: rgba(181, 101, 29, 0.06); border: 1px solid rgba(181, 101, 29, 0.2); }
.side-step.done { opacity: 0.55; }
.side-step.checkpoint { border-left: 3px solid var(--el-color-warning); }

.side-step-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
  background: var(--color-bg); color: var(--color-text-muted);
}
.side-step.active .side-step-dot { background: var(--color-primary); color: #fff; }
.side-step.done .side-step-dot { background: var(--color-success); color: #fff; }

.side-step-info { flex: 1; min-width: 0; }
.side-step-title { font-size: 13px; font-weight: 600; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.side-step-type { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.stat-item { text-align: center; padding: 10px 8px; background: var(--color-bg); border-radius: 8px; }
.stat-val { font-size: 18px; font-weight: 700; color: var(--color-text); }
.stat-label { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; }

.path-actions { display: flex; gap: 8px; justify-content: center; }

/* Content Panel */
.empty-state { padding: 80px 0; }
.step-header { margin-bottom: 24px; }
.step-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.step-num { font-size: 12px; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; }
.step-hours { font-size: 12px; color: var(--color-text-muted); display: flex; align-items: center; gap: 2px; }
.step-header h3 { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
.step-desc { font-size: 14px; color: var(--color-text-muted); line-height: 1.6; }

/* Learning Content */
.learning-content {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 24px 28px; margin-bottom: 24px; box-shadow: var(--shadow-card);
}
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.content-header h4 { font-size: 16px; font-weight: 700; margin: 0; }
.content-placeholder {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 40px; margin-bottom: 24px; text-align: center;
}

.markdown-body { font-size: 15px; line-height: 1.8; color: var(--color-text-secondary); }
.markdown-body :deep(h2) { font-size: 20px; margin: 20px 0 10px; }
.markdown-body :deep(h3) { font-size: 17px; margin: 16px 0 8px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(code) { background: var(--color-bg); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.markdown-body :deep(pre) { background: #1e1e2e; color: #cdd6f4; padding: 16px; border-radius: 8px; overflow-x: auto; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; }

/* Exercises */
.exercises-section {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 24px 28px; box-shadow: var(--shadow-card);
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.section-header h4 { font-size: 16px; font-weight: 700; margin: 0; }
.exercise-score { font-size: 14px; color: var(--color-primary); font-weight: 700; }

.exercise-card {
  padding: 18px; margin-bottom: 14px;
  background: var(--color-bg); border-radius: 10px;
  border: 1px solid transparent; transition: border-color 0.2s;
}
.exercise-card.correct { border-color: var(--color-success); background: rgba(103, 194, 58, 0.04); }
.exercise-card.wrong { border-color: var(--color-danger); background: rgba(245, 108, 108, 0.04); }

.q-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.q-num { font-size: 12px; font-weight: 600; color: var(--color-text-muted); }
.q-question { font-size: 15px; font-weight: 600; color: var(--color-text); margin-bottom: 12px; line-height: 1.6; }

.q-options { display: flex; flex-direction: column; gap: 6px; }
.q-option { margin-right: 0; padding: 8px 12px; border-radius: 6px; transition: background 0.15s; }
.q-option:hover { background: var(--color-bg-hover); }

.q-input { margin-bottom: 8px; }

.q-evaluation {
  margin-top: 14px; padding: 14px;
  background: #fff; border-radius: 8px; border: 1px solid var(--color-border);
}
.eval-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.eval-score { font-size: 13px; color: var(--color-text-muted); }
.eval-correct { font-size: 13px; color: var(--color-success); margin-bottom: 4px; }
.eval-suggestions { font-size: 13px; color: var(--color-text-secondary); }
.eval-suggestions ul { margin: 4px 0; padding-left: 18px; }
.eval-encouragement { font-size: 13px; color: var(--color-primary); margin-top: 6px; font-style: italic; }

.exercise-actions { margin-top: 18px; display: flex; gap: 10px; }
.exercise-generate { text-align: center; padding: 20px; }

/* Bottom Nav */
.step-nav-bottom { display: flex; justify-content: space-between; margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--color-border); }
</style>
