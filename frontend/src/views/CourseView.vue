<template>
  <div class="course-page">
    <div class="page-header">
      <h3>课程中心</h3>
      <el-button type="primary" @click="showCreateDialog = true">创建课程</el-button>
    </div>

    <div class="filters" style="margin-bottom: 16px; display: flex; gap: 12px;">
      <el-input v-model="query.keyword" placeholder="搜索课程" clearable style="width: 240px;" @keyup.enter="loadCourses" />
      <el-select v-model="query.category" placeholder="分类" clearable style="width: 140px;" @change="loadCourses">
        <el-option label="编程" value="编程" />
        <el-option label="数学" value="数学" />
        <el-option label="外语" value="外语" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="query.difficulty" placeholder="难度" clearable style="width: 140px;" @change="loadCourses">
        <el-option label="入门" value="BEGINNER" />
        <el-option label="中级" value="INTERMEDIATE" />
        <el-option label="高级" value="ADVANCED" />
      </el-select>
    </div>

    <div v-loading="loading" class="course-grid">
      <el-card v-for="course in courses" :key="course.id" class="course-card" shadow="hover">
        <div class="course-info">
          <h4>{{ course.title }}</h4>
          <p class="course-desc">{{ course.description || '暂无描述' }}</p>
          <div class="course-meta">
            <el-tag size="small">{{ course.category || '未分类' }}</el-tag>
            <el-tag size="small" :type="difficultyType(course.difficulty)">{{ difficultyText(course.difficulty) }}</el-tag>
            <el-tag size="small" :type="course.status === 1 ? 'success' : 'info'">
              {{ course.status === 1 ? '已发布' : '草稿' }}
            </el-tag>
          </div>
          <div class="course-teacher">教师：{{ course.teacherName || '-' }}</div>
        </div>
        <div class="course-actions">
          <el-button type="primary" size="small" @click="enrollCourse(course.id)">选课</el-button>
          <el-button size="small" @click="startChat(course.id)">开始对话</el-button>
        </div>
      </el-card>
      <el-empty v-if="courses.length === 0 && !loading" description="暂无课程" />
    </div>

    <el-pagination
      v-if="total > 0"
      style="margin-top: 20px; justify-content: center;"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="(p) => { query.page = p; loadCourses(); }"
    />

    <el-dialog v-model="showCreateDialog" title="创建课程" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="createForm.title" placeholder="输入课程名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category" placeholder="选择分类">
            <el-option label="编程" value="编程" />
            <el-option label="数学" value="数学" />
            <el-option label="外语" value="外语" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="createForm.difficulty" placeholder="选择难度">
            <el-option label="入门" value="BEGINNER" />
            <el-option label="中级" value="INTERMEDIATE" />
            <el-option label="高级" value="ADVANCED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createCourse">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { courseApi, chatApi } from '@/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const courses = ref([]);
const total = ref(0);
const loading = ref(false);
const creating = ref(false);
const showCreateDialog = ref(false);
const query = ref({ page: 1, size: 12, keyword: '', category: '', difficulty: '' });
const createForm = ref({ title: '', description: '', category: '', difficulty: 'BEGINNER' });

onMounted(() => loadCourses());

async function loadCourses() {
  loading.value = true;
  try {
    const res = await courseApi.list(query.value);
    if (res.code === 200) {
      courses.value = res.data?.records || [];
      total.value = res.data?.total || 0;
    }
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

async function createCourse() {
  if (!createForm.value.title.trim()) {
    ElMessage.warning('请输入课程名称');
    return;
  }
  creating.value = true;
  try {
    const res = await courseApi.create(createForm.value);
    if (res.code === 200) {
      ElMessage.success('课程创建成功');
      showCreateDialog.value = false;
      createForm.value = { title: '', description: '', category: '', difficulty: 'BEGINNER' };
      await loadCourses();
    }
  } catch {
    ElMessage.error('创建失败，确认您有教师权限');
  } finally { creating.value = false; }
}

async function enrollCourse(courseId) {
  try {
    await courseApi.enroll(courseId);
    ElMessage.success('选课成功');
  } catch {
    ElMessage.error('选课失败');
  }
}

async function startChat(courseId) {
  try {
    const res = await chatApi.createSession(courseId);
    if (res.code === 200) {
      router.push(`/chat/${res.data.id}`);
    }
  } catch {
    ElMessage.error('创建对话失败');
  }
}

function difficultyText(d) { return { BEGINNER: '入门', INTERMEDIATE: '中级', ADVANCED: '高级' }[d] || d; }
function difficultyType(d) { return { BEGINNER: 'success', INTERMEDIATE: 'warning', ADVANCED: 'danger' }[d] || 'info'; }
</script>

<style scoped>
.course-page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.course-card { display: flex; flex-direction: column; }
.course-info h4 { margin: 0 0 8px 0; font-size: 16px; }
.course-desc { color: #909399; font-size: 13px; margin: 0 0 8px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.course-meta { display: flex; gap: 6px; margin-bottom: 8px; }
.course-teacher { font-size: 12px; color: #606266; }
.course-actions { margin-top: 12px; display: flex; gap: 8px; }
</style>
