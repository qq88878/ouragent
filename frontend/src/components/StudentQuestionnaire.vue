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
            请如实填写，帮助AI为你提供更精准的学习建议
          </span>
        </div>
      </template>

      <el-form :model="form" label-position="top" class="q-form">
        <el-divider content-position="left">一、基础身份与背景</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="学历/年级">
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
          <el-col :span="8">
            <el-form-item label="专业/学科方向">
              <el-input v-model="form.majorDirection" placeholder="如：计算机科学、金融、医学..." />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年龄段">
              <el-select v-model="form.ageRange" style="width:100%" clearable>
                <el-option label="18岁以下" value="UNDER_18" />
                <el-option label="18-22岁" value="18_22" />
                <el-option label="23-30岁" value="23_30" />
                <el-option label="31-40岁" value="31_40" />
                <el-option label="40岁以上" value="ABOVE_40" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">二、目标与动机</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="学习目标（可多选）">
              <el-select v-model="form.learningGoals" multiple style="width:100%" clearable>
                <el-option label="应对考试" value="EXAM" />
                <el-option label="兴趣爱好" value="INTEREST" />
                <el-option label="就业求职" value="EMPLOYMENT" />
                <el-option label="职业晋升" value="PROMOTION" />
                <el-option label="自我提升" value="SELF_IMPROVEMENT" />
                <el-option label="其他" value="OTHER" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="目标明确度">
              <el-radio-group v-model="form.goalClarity">
                <el-radio value="CLEAR">目标明确</el-radio>
                <el-radio value="VAGUE">比较模糊</el-radio>
                <el-radio value="UNDECIDED">尚未确定</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学习动机强度">
              <el-radio-group v-model="form.motivationLevel">
                <el-radio value="STRONG">强烈</el-radio>
                <el-radio value="MODERATE">一般</el-radio>
                <el-radio value="WEAK">较弱</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">三、知识储备与能力现状</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="当前学科水平">
              <el-select v-model="form.subjectLevel" style="width:100%" clearable>
                <el-option label="零基础" value="ZERO_BASIC" />
                <el-option label="入门" value="BEGINNER" />
                <el-option label="中级" value="INTERMEDIATE" />
                <el-option label="高级" value="ADVANCED" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="自评优势能力（可多选）">
              <el-select v-model="form.selfStrengths" multiple style="width:100%" clearable>
                <el-option label="逻辑推理" value="LOGICAL" />
                <el-option label="记忆力" value="MEMORY" />
                <el-option label="创造力" value="CREATIVITY" />
                <el-option label="动手实践" value="PRACTICAL" />
                <el-option label="沟通表达" value="COMMUNICATION" />
                <el-option label="数学" value="MATH" />
                <el-option label="语言" value="LANGUAGE" />
                <el-option label="编程" value="PROGRAMMING" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="自评薄弱环节（可多选）">
              <el-select v-model="form.selfWeaknesses" multiple style="width:100%" clearable>
                <el-option label="逻辑推理" value="LOGICAL" />
                <el-option label="记忆力" value="MEMORY" />
                <el-option label="创造力" value="CREATIVITY" />
                <el-option label="动手实践" value="PRACTICAL" />
                <el-option label="沟通表达" value="COMMUNICATION" />
                <el-option label="数学" value="MATH" />
                <el-option label="语言" value="LANGUAGE" />
                <el-option label="编程" value="PROGRAMMING" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">四、学习风格与偏好</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="偏好学习方式（可多选）">
              <el-select v-model="form.learningMethods" multiple style="width:100%" clearable>
                <el-option label="看视频" value="VIDEO" />
                <el-option label="阅读文档" value="READING" />
                <el-option label="动手操作" value="HANDS_ON" />
                <el-option label="讨论交流" value="DISCUSSION" />
                <el-option label="听讲座" value="LECTURE" />
                <el-option label="做题测试" value="QUIZ" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="偏好学习时段（可多选）">
              <el-select v-model="form.studyTimeSlots" multiple style="width:100%" clearable>
                <el-option label="早晨 (6-9点)" value="MORNING" />
                <el-option label="上午 (9-12点)" value="FORENOON" />
                <el-option label="下午 (12-18点)" value="AFTERNOON" />
                <el-option label="晚上 (18-22点)" value="EVENING" />
                <el-option label="深夜 (22点后)" value="NIGHT" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单次专注学习时长">
              <el-radio-group v-model="form.sessionDuration">
                <el-radio value="LESS_30MIN">不到30分钟</el-radio>
                <el-radio value="30_60MIN">30-60分钟</el-radio>
                <el-radio value="1_2HOURS">1-2小时</el-radio>
                <el-radio value="2_4HOURS">2-4小时</el-radio>
                <el-radio value="MORE_4HOURS">4小时以上</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">五、元认知与自律性</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="制定学习计划的习惯">
              <el-radio-group v-model="form.planningHabit">
                <el-radio value="ALWAYS">总是计划</el-radio>
                <el-radio value="OFTEN">经常计划</el-radio>
                <el-radio value="SOMETIMES">偶尔计划</el-radio>
                <el-radio value="RARELY">很少计划</el-radio>
                <el-radio value="NEVER">从不计划</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学习时的专注程度">
              <el-radio-group v-model="form.focusLevel">
                <el-radio value="VERY_HIGH">非常专注</el-radio>
                <el-radio value="HIGH">比较专注</el-radio>
                <el-radio value="MODERATE">一般</el-radio>
                <el-radio value="LOW">容易分心</el-radio>
                <el-radio value="VERY_LOW">难以集中</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学后复习习惯">
              <el-radio-group v-model="form.reviewHabit">
                <el-radio value="EVERY_TIME">每次必复习</el-radio>
                <el-radio value="OFTEN">经常复习</el-radio>
                <el-radio value="SOMETIMES">偶尔复习</el-radio>
                <el-radio value="RARELY">很少复习</el-radio>
                <el-radio value="NEVER">从不复习</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">六、环境与资源支持</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="每天可用学习时间">
              <el-radio-group v-model="form.dailyStudyHours">
                <el-radio value="LESS_1H">不到1小时</el-radio>
                <el-radio value="1_2H">1-2小时</el-radio>
                <el-radio value="2_4H">2-4小时</el-radio>
                <el-radio value="4_6H">4-6小时</el-radio>
                <el-radio value="MORE_6H">6小时以上</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="可用学习设备（可多选）">
              <el-select v-model="form.devices" multiple style="width:100%" clearable>
                <el-option label="手机" value="PHONE" />
                <el-option label="平板" value="TABLET" />
                <el-option label="笔记本电脑" value="LAPTOP" />
                <el-option label="台式电脑" value="DESKTOP" />
                <el-option label="纸质书籍" value="BOOKS" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否有导师或学习同伴">
              <el-radio-group v-model="form.hasMentor">
                <el-radio value="YES">有</el-radio>
                <el-radio value="NO">没有</el-radio>
                <el-radio value="WANT">希望有</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">七、心理障碍与过往失败史</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="过往学习挫败经历">
              <el-radio-group v-model="form.hasPastFailures">
                <el-radio value="YES">有过</el-radio>
                <el-radio value="NO">没有</el-radio>
                <el-radio value="NOT_SURE">不确定</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="主要学习障碍（可多选）">
              <el-select v-model="form.mainBarriers" multiple style="width:100%" clearable>
                <el-option label="懒惰拖延" value="LAZINESS" />
                <el-option label="容易分心" value="DISTRACTION" />
                <el-option label="缺乏方法" value="NO_METHOD" />
                <el-option label="缺乏自信" value="NO_CONFIDENCE" />
                <el-option label="时间不足" value="NO_TIME" />
                <el-option label="缺乏支持" value="NO_SUPPORT" />
                <el-option label="内容枯燥" value="BORING" />
                <el-option label="焦虑压力" value="ANXIETY" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="当前学习自信心水平">
              <el-radio-group v-model="form.confidenceLevel">
                <el-radio value="VERY_HIGH">非常有信心</el-radio>
                <el-radio value="HIGH">比较有信心</el-radio>
                <el-radio value="MODERATE">一般</el-radio>
                <el-radio value="LOW">信心不足</el-radio>
                <el-radio value="VERY_LOW">非常缺乏信心</el-radio>
              </el-radio-group>
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
import { ref, onMounted } from 'vue';
import { learningApi } from '@/api';
import { ElMessage } from 'element-plus';

const showForm = ref(false);
const isCompleted = ref(false);
const saving = ref(false);

const defaultForm = () => ({
  educationLevel: '',
  majorDirection: '',
  ageRange: '',
  learningGoals: [],
  goalClarity: '',
  motivationLevel: '',
  subjectLevel: '',
  selfStrengths: [],
  selfWeaknesses: [],
  learningMethods: [],
  studyTimeSlots: [],
  sessionDuration: '',
  planningHabit: '',
  focusLevel: '',
  reviewHabit: '',
  dailyStudyHours: '',
  devices: [],
  hasMentor: '',
  hasPastFailures: '',
  mainBarriers: [],
  confidenceLevel: '',
});

const form = ref(defaultForm());

onMounted(async () => {
  try {
    const r = await learningApi.getQuestionnaireStatus();
    if (r.code === 200) {
      isCompleted.value = r.data.completed;
    }
  } catch {}
});

async function openForm() {
  showForm.value = true;
  try {
    const r = await learningApi.getQuestionnaire();
    if (r.code === 200 && r.data) {
      const d = r.data;
      form.value = {
        educationLevel: d.educationLevel || '',
        majorDirection: d.majorDirection || '',
        ageRange: d.ageRange || '',
        learningGoals: d.learningGoals || [],
        goalClarity: d.goalClarity || '',
        motivationLevel: d.motivationLevel || '',
        subjectLevel: d.subjectLevel || '',
        selfStrengths: d.selfStrengths || [],
        selfWeaknesses: d.selfWeaknesses || [],
        learningMethods: d.learningMethods || [],
        studyTimeSlots: d.studyTimeSlots || [],
        sessionDuration: d.sessionDuration || '',
        planningHabit: d.planningHabit || '',
        focusLevel: d.focusLevel || '',
        reviewHabit: d.reviewHabit || '',
        dailyStudyHours: d.dailyStudyHours || '',
        devices: d.devices || [],
        hasMentor: d.hasMentor || '',
        hasPastFailures: d.hasPastFailures || '',
        mainBarriers: d.mainBarriers || [],
        confidenceLevel: d.confidenceLevel || '',
      };
    }
  } catch {
    form.value = defaultForm();
  }
}

async function saveQuestionnaire() {
  saving.value = true;
  try {
    await learningApi.saveQuestionnaire({ ...form.value });
    isCompleted.value = true;
    showForm.value = false;
    ElMessage.success('画像已保存');
  } catch {
    ElMessage.error('保存失败，请重试');
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.questionnaire-wrapper {
  margin-top: 24px;
}
.questionnaire-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
}
.status-label {
  font-weight: 600;
  font-size: 15px;
}
.questionnaire-card {
  max-width: 100%;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  font-weight: 600;
}
.q-form {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 8px;
}
.q-form .el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
}
</style>