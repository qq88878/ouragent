<template>
  <div class="test-page">
    <div class="test-header">
      <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <h2>阶段自测</h2>
      <span class="test-subtitle">{{ path.title }}</span>
    </div>

    <div v-if="!testStarted && !testCompleted" class="test-intro">
      <el-empty description="准备开始阶段自测" :image-size="80">
        <template #default>
          <p class="intro-text">本次自测将覆盖已学内容的核心知识点，包含选择题和填空题。</p>
          <el-button type="primary" size="large" @click="startTest">开始自测</el-button>
        </template>
      </el-empty>
    </div>

    <div v-loading="loading" class="test-content" v-if="testStarted && !testCompleted">
      <div class="test-progress">
        <span>第 {{ currentQ + 1 }} / {{ questions.length }} 题</span>
        <el-progress :percentage="Math.round((currentQ + 1) / questions.length * 100)" :stroke-width="6" :show-text="false" />
      </div>

      <div v-if="questions[currentQ]" class="question-card">
        <div class="q-meta">
          <el-tag :type="questions[currentQ].difficulty === 'hard' ? 'danger' : questions[currentQ].difficulty === 'easy' ? 'success' : 'warning'" size="small">
            {{ { easy: '简单', medium: '中等', hard: '困难' }[questions[currentQ].difficulty] }}
          </el-tag>
          <span class="q-type">{{ questions[currentQ].type === 'choice' ? '选择题' : '填空题' }}</span>
        </div>
        <div class="q-text">{{ questions[currentQ].question }}</div>
        <div v-if="questions[currentQ].type === 'choice' && questions[currentQ].options" class="q-options">
          <el-radio-group v-model="testAnswers[currentQ]" class="option-group">
            <el-radio v-for="(opt, oi) in questions[currentQ].options" :key="oi" :value="opt" class="test-option">
              {{ opt }}
            </el-radio>
          </el-radio-group>
        </div>
        <div v-else class="q-textarea">
          <el-input v-model="testAnswers[currentQ]" type="textarea" :rows="3" placeholder="请输入你的答案..." />
        </div>
      </div>

      <div class="test-nav">
        <el-button v-if="currentQ > 0" @click="currentQ--">上一题</el-button>
        <el-button v-if="currentQ < questions.length - 1" type="primary" @click="currentQ++">下一题</el-button>
        <el-button v-if="currentQ === questions.length - 1" type="success" @click="submitTest">提交自测</el-button>
      </div>
    </div>

    <!-- 测试结果 -->
    <div v-if="testCompleted" class="test-results">
      <div class="result-card" :class="{ passed: testPassed }">
        <div class="result-icon">{{ testPassed ? '🎉' : '📚' }}</div>
        <h2>{{ testPassed ? '恭喜通过！' : '还需努力' }}</h2>
        <div class="result-score">
          <span class="score-num">{{ testCorrect }}/{{ questions.length }}</span>
          <span class="score-label">正确率 {{ Math.round(testCorrect / questions.length * 100) }}%</span>
        </div>
        <p class="result-msg">{{ testPassed ? '你已掌握本阶段核心知识，可以继续下一阶段学习。' : '建议复习相关知识点后再试一次。' }}</p>
        <div class="result-actions">
          <el-button v-if="!testPassed" type="warning" @click="retryTest">重新自测</el-button>
          <el-button type="primary" @click="$router.push(`/learning/${path.id}`)">返回学习</el-button>
        </div>
      </div>

      <div class="result-detail">
        <h3>答题详情</h3>
        <div v-for="(q, qi) in questions" :key="qi" class="result-q" :class="{ correct: q.isCorrect, wrong: !q.isCorrect }">
          <div class="rq-header">
            <span>第 {{ qi + 1 }} 题</span>
            <el-tag :type="q.isCorrect ? 'success' : 'danger'" size="small">{{ q.isCorrect ? '✓ 正确' : '✗ 错误' }}</el-tag>
          </div>
          <div class="rq-question">{{ q.question }}</div>
          <div class="rq-answer">
            <span class="rq-label">你的答案:</span> {{ q.userAnswer || '未作答' }}
          </div>
          <div v-if="!q.isCorrect" class="rq-correct">
            <span class="rq-label">正确答案:</span> {{ q.answer }}
          </div>
          <div v-if="q.explanation" class="rq-explain">{{ q.explanation }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { learningApi, stepApi } from '@/api';

const route = useRoute();
const router = useRouter();
const path = ref({});
const loading = ref(false);
const testStarted = ref(false);
const testCompleted = ref(false);
const testPassed = ref(false);
const testCorrect = ref(0);
const currentQ = ref(0);
const questions = ref([]);
const testAnswers = ref({});

onMounted(async () => {
  try {
    const res = await learningApi.getPathById(route.params.pathId);
    path.value = res.data || res;
  } catch { ElMessage.error('加载路径失败'); }
});

async function startTest() {
  loading.value = true;
  try {
    // 找第一个 checkpoint 步骤
    const checkpoint = path.value.steps?.find(s => s.isCheckpoint === 1 && s.status !== 2);
    if (!checkpoint) {
      ElMessage.warning('没有找到阶段自测步骤');
      return;
    }
    const res = await stepApi.generateCheckpoint(path.value.id, checkpoint.id, 10);
    const updated = (res.data || res);
    path.value = updated;
    const updatedStep = updated.steps?.find(s => s.id === checkpoint.id);
    if (updatedStep?.exercises) {
      const data = typeof updatedStep.exercises === 'string'
        ? JSON.parse(updatedStep.exercises)
        : updatedStep.exercises;
      questions.value = data.questions || [];
    }
    testStarted.value = true;
  } catch (e) {
    ElMessage.error('生成自测失败');
  } finally {
    loading.value = false;
  }
}

async function submitTest() {
  loading.value = true;
  try {
    const checkpoint = path.value.steps?.find(s => s.isCheckpoint === 1 && s.status !== 2);
    if (!checkpoint) return;

    const answers = {};
    testAnswers.value.forEach((ans, i) => { answers['q_' + i] = ans || ''; });
    // Use evaluateCheckpoint for checkpoint steps
    const res = await stepApi.evaluateCheckpoint(path.value.id, checkpoint.id, answers);
    const result = res.data || res;

    testPassed.value = result.passed;
    testCorrect.value = result.correct_count || 0;
    // 标记每道题的对错
    (result.results || []).forEach((r, i) => {
      if (questions.value[i]) {
        questions.value[i].isCorrect = r.is_correct;
        questions.value[i].userAnswer = r.user_answer;
      }
    });
    testCompleted.value = true;
  } catch (e) {
    ElMessage.error('提交失败');
  } finally {
    loading.value = false;
  }
}

function retryTest() {
  testStarted.value = false;
  testCompleted.value = false;
  testAnswers.value = {};
  currentQ.value = 0;
  questions.value = [];
}
</script>

<style scoped>
.test-page { max-width: 800px; margin: 0 auto; }

.test-header { display: flex; align-items: center; gap: 12px; margin-bottom: 32px; padding-bottom: 16px; border-bottom: 1px solid var(--color-border); }
.test-header h2 { font-size: 22px; font-weight: 700; margin: 0; }
.test-subtitle { font-size: 13px; color: var(--color-text-muted); }

.test-intro { padding: 60px 0; text-align: center; }
.intro-text { font-size: 14px; color: var(--color-text-muted); margin-bottom: 20px; }

.test-content { padding: 20px 0; }
.test-progress { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; font-size: 14px; color: var(--color-text-muted); }

.question-card {
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  padding: 28px 32px; box-shadow: var(--shadow-card); margin-bottom: 24px;
}
.q-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.q-type { font-size: 12px; color: var(--color-text-muted); }
.q-text { font-size: 17px; font-weight: 600; color: var(--color-text); line-height: 1.7; margin-bottom: 20px; }

.option-group { display: flex; flex-direction: column; gap: 10px; }
.test-option {
  padding: 12px 16px; border-radius: 8px; margin-right: 0;
  border: 1px solid var(--color-border); transition: all 0.15s;
}
.test-option:hover { background: var(--color-bg-hover); }
.q-textarea { margin-top: 12px; }

.test-nav { display: flex; justify-content: space-between; padding-top: 20px; }

/* Results */
.test-results { padding: 20px 0; }
.result-card {
  text-align: center; padding: 40px; background: var(--color-bg-card);
  border-radius: var(--radius-xl); box-shadow: var(--shadow-card); margin-bottom: 28px;
}
.result-card.passed { border: 2px solid var(--color-success); }
.result-icon { font-size: 48px; margin-bottom: 12px; }
.result-card h2 { font-size: 24px; margin: 0 0 12px; }
.result-score { display: flex; flex-direction: column; align-items: center; gap: 4px; margin-bottom: 12px; }
.score-num { font-size: 36px; font-weight: 700; color: var(--color-primary); }
.score-label { font-size: 14px; color: var(--color-text-muted); }
.result-msg { font-size: 14px; color: var(--color-text-muted); margin-bottom: 20px; }
.result-actions { display: flex; gap: 12px; justify-content: center; }

.result-detail { background: var(--color-bg-card); border-radius: var(--radius-lg); padding: 24px 28px; box-shadow: var(--shadow-card); }
.result-detail h3 { margin: 0 0 18px; font-size: 17px; font-weight: 700; }

.result-q { padding: 14px 18px; margin-bottom: 10px; border-radius: 8px; border: 1px solid var(--color-border); }
.result-q.correct { border-left: 3px solid var(--color-success); }
.result-q.wrong { border-left: 3px solid var(--color-danger); }
.rq-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; color: var(--color-text-muted); }
.rq-question { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.rq-answer { font-size: 13px; margin-bottom: 4px; }
.rq-correct { font-size: 13px; color: var(--color-success); margin-bottom: 4px; }
.rq-label { font-weight: 600; color: var(--color-text-muted); }
.rq-explain { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; font-style: italic; }
</style>
