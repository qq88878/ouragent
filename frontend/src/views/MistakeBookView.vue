<template>
  <div class="mistake-book-page">
    <div class="page-header">
      <h2>错题本 & 智能复习</h2>
      <p class="subtitle">艾宾浩斯遗忘曲线驱动 · 错误分类诊断 · 薄弱点专项练习</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6"><el-card shadow="hover"><div class="stat-num">{{ stats.total_mistakes || 0 }}</div><div class="stat-label">总错题数</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat-num" style="color:#e6a23c">{{ stats.due_reviews || 0 }}</div><div class="stat-label">待复习</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat-num" style="color:#409eff">{{ stats.upcoming_reviews_7d || 0 }}</div><div class="stat-label">7日内复习</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="stat-label">主要错误类型</div><div class="stat-type">{{ errorTypeLabel(stats.primary_error_type) }}</div></el-card></el-col>
    </el-row>

    <!-- Tab切换 -->
    <div style="margin-bottom:16px;display:flex;justify-content:flex-end">
      <el-popconfirm title="确定清空所有错题？" @confirm="doClearAll">
        <template #reference>
          <el-button type="danger" plain size="small">清空全部</el-button>
        </template>
      </el-popconfirm>
    </div>
    <el-tabs v-model="activeTab" class="content-tabs">
      <!-- 错题列表 -->
      <el-tab-pane label="错题列表" name="list">
        <el-table :data="mistakes" stripe style="width:100%" v-loading="loading">
          <el-table-column prop="question" label="题目" min-width="200" show-overflow-tooltip />
          <el-table-column prop="student_answer" label="我的答案" width="120" />
          <el-table-column prop="reference_answer" label="正确答案" width="120" />
          <el-table-column label="错误分类" width="110">
            <template #default="{row}">{{ errorTypeLabel(row.error_category) }}</template>
          </el-table-column>
          <el-table-column label="掌握状态" width="100">
            <template #default="{row}"><el-tag :type="row.mastered ? 'success' : 'warning'">{{ row.mastered ? '已掌握' : '复习中' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="复习轮次" width="90">
            <template #default="{row}">第{{ row.review_stage + 1 }}轮</template>
          </el-table-column>
          <el-table-column label="操作" width="240">
            <template #default="{row}">
              <el-button size="small" type="danger" plain @click="doDelete(row)">删除</el-button>
              <el-button size="small" type="success" plain @click="doReview(row, true)" :disabled="row.mastered">记得</el-button>
              <el-button size="small" type="warning" plain @click="doReview(row, false)" :disabled="row.mastered">忘了</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 智能诊断 -->
      <el-tab-pane label="智能诊断" name="diagnose">
        <el-form :model="diagForm" label-width="100px" style="max-width:600px">
          <el-form-item label="题目"><el-input v-model="diagForm.question" type="textarea" rows="2" /></el-form-item>
          <el-form-item label="我的答案"><el-input v-model="diagForm.student_answer" /></el-form-item>
          <el-form-item label="正确答案"><el-input v-model="diagForm.correct_answer" /></el-form-item>
          <el-form-item><el-button type="primary" @click="doDiagnose" :loading="diagnosing">开始诊断</el-button></el-form-item>
        </el-form>
        <el-card v-if="diagnosisResult" class="diagnosis-card">
          <template #header>诊断结果</template>
          <p><strong>错误分类：</strong>{{ errorTypeLabel(diagnosisResult.error_category) }}</p>
          <p><strong>错误模式：</strong>{{ diagnosisResult.error_pattern }}</p>
          <p><strong>根因：</strong>{{ diagnosisResult.error_root_cause }}</p>
          <p><strong>建议：</strong>{{ diagnosisResult.suggestion }}</p>
        </el-card>
      </el-tab-pane>

      <!-- 专项练习 -->
      <el-tab-pane label="专项练习" name="practice">
        <el-form :model="practiceForm" label-width="100px" style="max-width:600px">
          <el-form-item label="错题题目"><el-input v-model="practiceForm.question" type="textarea" rows="2" /></el-form-item>
          <el-form-item label="我的答案"><el-input v-model="practiceForm.student_answer" /></el-form-item>
          <el-form-item label="正确答案"><el-input v-model="practiceForm.correct_answer" /></el-form-item>
          <el-form-item><el-button type="success" @click="doGeneratePractice" :loading="generating">生成专项练习</el-button></el-form-item>
        </el-form>
        <el-card v-if="practiceResult" class="practice-card">
          <template #header>{{ practiceResult.practice_title || '专项练习' }}</template>
          <p><strong>目标技能：</strong>{{ practiceResult.target_skill }}</p>
          <div v-for="(q, idx) in (practiceResult.questions || [])" :key="idx" class="practice-q" style="margin-top:12px;padding:12px;background:#f5f7fa;border-radius:8px">
            <p><strong>题目{{ idx + 1 }}：</strong>{{ q.question }}</p>
            <p><strong>答案：</strong>{{ q.answer }}</p>
            <p v-if="q.hint"><strong>提示：</strong>{{ q.hint }}</p>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 复习提醒 -->
      <el-tab-pane label="复习提醒" name="notifications">
        <el-button type="warning" @click="doDailyReview" :loading="generatingNotif" style="margin-bottom:16px">检查今日复习</el-button>
        <el-empty v-if="notifications.length === 0" description="暂无复习提醒" />
        <el-timeline v-else>
          <el-timeline-item v-for="n in notifications" :key="n.id" :timestamp="n.created_at" placement="top">
            <el-card>
              <p><strong>{{ n.title }}</strong></p>
              <p>{{ n.message }}</p>
              <p style="color:#909399;font-size:12px">知识点：{{ n.knowledge_name }} | {{ errorTypeLabel(n.error_category) }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { mistakeBookApi } from '@/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('list')
const loading = ref(false)
const mistakes = ref([])
const stats = ref({})
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const userId = computed(() => String(authStore.user?.id || '1'))

// 诊断
const diagnosing = ref(false)
const diagForm = reactive({ question: '', student_answer: '', correct_answer: '' })
const diagnosisResult = ref(null)

// 练习
const generating = ref(false)
const practiceForm = reactive({ question: '', student_answer: '', correct_answer: '' })
const practiceResult = ref(null)

// 通知
const generatingNotif = ref(false)
const notifications = ref([])

const errorTypeLabel = (type) => {
  const map = { concept_unclear: '概念不清', careless: '粗心大意', wrong_approach: '思路偏了', incomplete: '答案不完整', correct: '回答正确' }
  return map[type] || type || '未分类'
}

const loadData = async () => {
  loading.value = true
  console.log('[MistakeBook] loadData start, userId:', userId.value)
  try {
    const [mRes, sRes] = await Promise.all([
      mistakeBookApi.list(userId.value),
      mistakeBookApi.stats(userId.value)
    ])
    console.log('[MistakeBook] list response:', JSON.stringify(mRes))
    console.log('[MistakeBook] stats response:', JSON.stringify(sRes))
    mistakes.value = mRes.mistakes || []
    stats.value = sRes
    console.log('[MistakeBook] mistakes count:', mistakes.value.length)
  } catch (e) { ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message)) }
  finally { loading.value = false }
}

const doReview = async (row, recalled) => {
  try {
    await mistakeBookApi.review({ mistake_id: row.id, recalled })
    ElMessage.success(recalled ? '已标记为记得' : '已重置复习进度')
    await loadData()
  } catch (e) { ElMessage.error('操作失败') }
}

const doDiagnose = async () => {
  diagnosing.value = true
  try {
    const res = await mistakeBookApi.diagnose({ user_id: userId.value, ...diagForm })
    diagnosisResult.value = res.diagnosis
    ElMessage.success('诊断完成')
    await loadData()
  } catch (e) { ElMessage.error('诊断失败: ' + (e.response?.data?.detail || e.message)) }
  finally { diagnosing.value = false }
}

const doGeneratePractice = async () => {
  generating.value = true
  try {
    const res = await mistakeBookApi.practice({ user_id: userId.value, ...practiceForm })
    practiceResult.value = res.practice
    ElMessage.success('专项练习已生成')
  } catch (e) { ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message)) }
  finally { generating.value = false }
}

const doDailyReview = async () => {
  generatingNotif.value = true
  try {
    const res = await mistakeBookApi.dailyReview(userId.value)
    notifications.value = res.notifications || []
    ElMessage.success(`发现 ${notifications.value.length} 条待复习提醒`)
  } catch (e) { ElMessage.error('检查失败') }
  finally { generatingNotif.value = false }
}

const doDelete = async (row) => {
  try {
    await mistakeBookApi.delete(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e) { ElMessage.error('删除失败') }
}

const doClearAll = async () => {
  try {
    await mistakeBookApi.clearAll(userId.value)
    ElMessage.success('已清空')
    await loadData()
  } catch (e) { ElMessage.error('清空失败') }
}

onMounted(loadData)
</script>

<style scoped>
.mistake-book-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 24px; margin: 0 0 8px 0; }
.subtitle { color: #909399; font-size: 14px; margin: 0; }
.stats-row { margin-bottom: 20px; }
.stat-num { font-size: 32px; font-weight: bold; color: #303133; text-align: center; }
.stat-label { text-align: center; color: #909399; font-size: 13px; margin-top: 4px; }
.stat-type { text-align: center; font-size: 18px; font-weight: bold; color: #409eff; margin-top: 4px; }
.content-tabs { margin-top: 10px; }
.diagnosis-card, .practice-card { margin-top: 20px; max-width: 600px; }
</style>
