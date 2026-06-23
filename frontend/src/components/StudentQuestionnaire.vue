<template>
  <div class="questionnaire-wrapper">
    <div class="questionnaire-status" v-if="!showForm">
      <span class="status-label">学习画像问卷</span>
      <el-tag :type="isCompleted ? 'success' : 'info'" size="default">
        {{ isCompleted ? '已完成' : '未完成' }}
      </el-tag>
      <el-link type="primary" :underline="false" @click="openForm" style="margin-left:12px;">
        {{ isCompleted ? '去修改' : '去完成' }}
      </el-link>
    </div>

    <el-card v-if="showForm" class="questionnaire-card">
      <template #header>
        <div class="card-header">
          <span>学习画像问卷</span>
          <span style="font-size:13px;color:#909399;font-weight:normal;">
            填写基础信息，AI 会在每门课程对话中进一步了解你
          </span>
        </div>
      </template>

      <el-form :model="form" label-position="top" class="q-form">

        <!-- 一、基础身份 -->
        <el-divider content-position="left">一、基础身份</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学历阶段">
              <el-select v-model="form.educationLevel" style="width:100%" clearable>
                <el-option label="高中" value="HIGH_SCHOOL" />
                <el-option label="大专" value="ASSOCIATE" />
                <el-option label="本科" value="BACHELOR" />
                <el-option label="硕士" value="MASTER" />
                <el-option label="博士" value="PHD" />
                <el-option label="其他" value="OTHER" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业 / 兴趣方向">
              <el-input v-model="form.majorDirection" placeholder="如：计算机科学、金融、医学…" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 二、学习目标 -->
        <el-divider content-position="left">二、学习目标</el-divider>
        <el-form-item label="我来这里主要是为了（可多选）">
          <el-checkbox-group v-model="form.learningGoals">
            <el-checkbox value="EXAM">应对考试</el-checkbox>
            <el-checkbox value="POSTGRADUATE">考研升学</el-checkbox>
            <el-checkbox value="EMPLOYMENT">求职就业</el-checkbox>
            <el-checkbox value="SELF_IMPROVEMENT">自我提升</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 三、学习风格 -->
        <el-divider content-position="left">三、学习风格</el-divider>
        <el-form-item label="我更喜欢的学习方式（可多选）">
          <el-checkbox-group v-model="form.learningMethods">
            <el-checkbox value="VIDEO">看视频</el-checkbox>
            <el-checkbox value="READING">读文档 / 教材</el-checkbox>
            <el-checkbox value="DISCUSSION">讨论交流</el-checkbox>
            <el-checkbox value="QUIZ">刷题练习</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 四、自我认知 -->
        <el-divider content-position="left">四、自我认知</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="我的优势（可多选）">
              <el-checkbox-group v-model="form.selfStrengths">
                <el-checkbox value="COMPREHENSION">理解力</el-checkbox>
                <el-checkbox value="MEMORY">记忆力</el-checkbox>
                <el-checkbox value="FOCUS">专注力</el-checkbox>
                <el-checkbox value="DISCIPLINE">自律性</el-checkbox>
                <el-checkbox value="EXPRESSION">表达力</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="我的不足（可多选）">
              <el-checkbox-group v-model="form.selfWeaknesses">
                <el-checkbox value="COMPREHENSION">理解力</el-checkbox>
                <el-checkbox value="MEMORY">记忆力</el-checkbox>
                <el-checkbox value="FOCUS">专注力</el-checkbox>
                <el-checkbox value="DISCIPLINE">自律性</el-checkbox>
                <el-checkbox value="EXPRESSION">表达力</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>

        <div style="margin-top:24px;display:flex;gap:12px;">
          <el-button type="primary" :loading="saving" @click="saveQuestionnaire">保存画像</el-button>
          <el-button @click="showForm = false">取消</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { learningApi } from '@/api'
import { ElMessage } from 'element-plus'

const showForm = ref(false)
const isCompleted = ref(false)
const saving = ref(false)

const defaultForm = () => ({
  educationLevel: '',
  majorDirection: '',
  learningGoals: [],
  learningMethods: [],
  selfStrengths: [],
  selfWeaknesses: [],
})

const form = ref(defaultForm())

onMounted(async () => {
  try {
    const r = await learningApi.getQuestionnaireStatus()
    if (r.code === 200) isCompleted.value = r.data.completed
  } catch {}
})

async function openForm() {
  showForm.value = true
  try {
    const r = await learningApi.getQuestionnaire()
    if (r.code === 200 && r.data) {
      const d = r.data
      form.value = {
        educationLevel: d.educationLevel || '',
        majorDirection: d.majorDirection || '',
        learningGoals: d.learningGoals || [],
        learningMethods: d.learningMethods || [],
        selfStrengths: d.selfStrengths || [],
        selfWeaknesses: d.selfWeaknesses || [],
      }
    }
  } catch {
    form.value = defaultForm()
  }
}

async function saveQuestionnaire() {
  saving.value = true
  try {
    await learningApi.saveQuestionnaire({ ...form.value })
    isCompleted.value = true
    showForm.value = false
    ElMessage.success('基础画像已保存')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.questionnaire-wrapper { margin-top: 24px; }
.questionnaire-status { display: flex; align-items: center; gap: 8px; padding: 12px 0; }
.status-label { font-weight: 600; font-size: 15px; }
.questionnaire-card { max-width: 100%; }
.card-header { display: flex; align-items: center; gap: 16px; font-weight: 600; }
.q-form { max-height: 70vh; overflow-y: auto; padding-right: 8px; }
.q-form .el-checkbox-group { display: flex; flex-wrap: wrap; gap: 4px 20px; }
</style>
