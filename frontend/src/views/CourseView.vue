<template>
  <div class="course-page">
    <div class="page-header">
      <h3>课程中心</h3>
      <el-button v-if="isTeacher" type="primary" @click="showCreateDialog = true">创建课程</el-button>
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
      <el-card v-for="course in sortedCourses" :key="course.id" class="course-card" shadow="hover"
        :class="{ 'own-course': isTeacher && course.teacherId === userId }">
        <div class="course-info">
          <div class="course-title-row">
            <h4>{{ course.title }}</h4>
            <el-tag v-if="isTeacher && course.teacherId === userId" size="small" type="warning" effect="plain">我的</el-tag>
          </div>
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
          <el-button size="small" @click="$router.push(`/courses/${course.id}`)">详细</el-button>
          <template v-if="isTeacher && course.teacherId === userId">
            <el-button size="small" type="warning" @click="openMaterials(course)">管理辅材</el-button>
            <el-button size="small" @click="openEdit(course)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCourse(course.id)">删除</el-button>
          </template>
          <template v-if="isAdmin">
            <el-button size="small" type="warning" @click="openMaterials(course)">管理辅材</el-button>
            <el-button size="small" @click="openEdit(course)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCourse(course.id)">删除</el-button>
          </template>
          <template v-if="isStudent">
            <el-button type="primary" size="small" :loading="entering === course.id" @click="enterCourse(course.id)">进入课程</el-button>
          </template>
        </div>
      </el-card>
      <el-empty v-if="sortedCourses.length === 0 && !loading" description="暂无课程" />
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

    <el-dialog v-model="showEditDialog" title="编辑课程" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="editForm.title" placeholder="输入课程名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.category" placeholder="选择分类">
            <el-option label="编程" value="编程" />
            <el-option label="数学" value="数学" />
            <el-option label="外语" value="外语" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="editForm.difficulty" placeholder="选择难度">
            <el-option label="入门" value="BEGINNER" />
            <el-option label="中级" value="INTERMEDIATE" />
            <el-option label="高级" value="ADVANCED" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" placeholder="选择状态">
            <el-option label="草稿" :value="0" />
            <el-option label="已发布" :value="1" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-if="isTeacher || isAdmin" v-model="showMaterialsDialog" :title="'管理辅材 - ' + materialsCourse?.title" width="700px">
      <el-tabs v-model="materialsTab">
        <el-tab-pane label="当前辅材" name="current">
          <el-table :data="courseMaterials" v-loading="matLoading" empty-text="暂无辅材">
            <el-table-column prop="name" label="文件名" min-width="200" />
            <el-table-column prop="fileType" label="类型" width="80">
              <template #default="{ row }"><el-tag size="small">{{ row.fileType }}</el-tag></template>
            </el-table-column>
            <el-table-column label="大小" width="100">
              <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button text type="danger" size="small" @click="removeMaterial(row.id)">移出课程</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="添加辅材" name="add">
          <el-divider content-position="left">上传新文件</el-divider>
          <div style="display:flex;gap:12px;align-items:center;margin-bottom:16px;">
            <el-upload :auto-upload="false" :limit="1" :on-change="(f) => uploadFile = f.raw" :on-remove="() => uploadFile = null">
              <el-button type="primary" size="small">选择文件</el-button>
              <template #tip><span style="font-size:12px;color:#909399;margin-left:8px;">支持 PDF/DOCX/MD/TXT</span></template>
            </el-upload>
            <el-button type="success" size="small" :loading="uploading" :disabled="!uploadFile" @click="doUpload">上传</el-button>
          </div>
          <el-divider content-position="left">从知识库选择</el-divider>
          <el-table :data="allKnowledge" v-loading="allKbLoading" empty-text="知识库中没有其他文件" max-height="300" @selection-change="(rows) => selectedKnowledge = rows.map(r => r.id)">
            <el-table-column type="selection" width="50" :selectable="(row) => row.courseId !== materialsCourse?.id" />
            <el-table-column prop="name" label="文件名" min-width="160" />
            <el-table-column prop="courseName" label="所属课程" width="120" />
            <el-table-column prop="fileType" label="类型" width="80">
              <template #default="{ row }"><el-tag size="small">{{ row.fileType }}</el-tag></template>
            </el-table-column>
          </el-table>
          <el-button type="primary" size="small" style="margin-top:12px;" :loading="linking" :disabled="selectedKnowledge.length === 0" @click="linkKnowledge">关联选中文件</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { courseApi, chatApi, knowledgeApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const courses = ref([]);
const total = ref(0);
const loading = ref(false);
const creating = ref(false);
const saving = ref(false);
const showCreateDialog = ref(false);
const showEditDialog = ref(false);
const showMaterialsDialog = ref(false);
const entering = ref(null);
const query = ref({ page: 1, size: 12, keyword: '', category: '', difficulty: '' });
const createForm = ref({ title: '', description: '', category: '', difficulty: 'BEGINNER' });
const editForm = ref({ id: null, title: '', description: '', category: '', difficulty: 'BEGINNER', status: 0 });

const materialsCourse = ref(null);
const materialsTab = ref('current');
const courseMaterials = ref([]);
const matLoading = ref(false);
const allKnowledge = ref([]);
const allKbLoading = ref(false);
const selectedKnowledge = ref([]);
const uploadFile = ref(null);
const uploading = ref(false);
const linking = ref(false);

const userId = computed(() => authStore.user?.id);
const isTeacher = computed(() => authStore.user?.role === 'TEACHER');
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isStudent = computed(() => authStore.user?.role === 'STUDENT');

const sortedCourses = computed(() => {
  if (!isTeacher.value || !userId.value) return courses.value;
  const own = [], other = [];
  for (const c of courses.value) {
    if (c.teacherId === userId.value) own.push(c);
    else other.push(c);
  }
  return [...own, ...other];
});

onMounted(async () => {
  if (!authStore.user) await authStore.fetchUser();
  await loadCourses();
});

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
  if (!createForm.value.title.trim()) { ElMessage.warning('请输入课程名称'); return; }
  creating.value = true;
  try {
    const res = await courseApi.create(createForm.value);
    if (res.code === 200) {
      ElMessage.success('课程创建成功');
      showCreateDialog.value = false;
      createForm.value = { title: '', description: '', category: '', difficulty: 'BEGINNER' };
      await loadCourses();
    } else {
      ElMessage.error(res.message || '创建失败');
    }
  } catch { ElMessage.error('创建失败'); }
  finally { creating.value = false; }
}

function openEdit(course) {
  editForm.value = { id: course.id, title: course.title, description: course.description || '', category: course.category || '', difficulty: course.difficulty || 'BEGINNER', status: course.status };
  showEditDialog.value = true;
}
async function saveEdit() {
  if (!editForm.value.title.trim()) { ElMessage.warning('请输入课程名称'); return; }
  saving.value = true;
  try {
    await courseApi.update(editForm.value.id, editForm.value);
    ElMessage.success('保存成功');
    showEditDialog.value = false;
    await loadCourses();
  } catch { ElMessage.error('保存失败'); }
  finally { saving.value = false; }
}

async function deleteCourse(id) {
  try {
    await ElMessageBox.confirm('确定删除该课程？此操作不可恢复。', '警告', { type: 'error' });
    await courseApi.delete(id);
    ElMessage.success('已删除');
    await loadCourses();
  } catch { }
}

async function openMaterials(course) {
  materialsCourse.value = course;
  materialsTab.value = 'current';
  showMaterialsDialog.value = true;
  await loadCourseMaterials(course.id);
  await loadAllKnowledge();
}
async function loadCourseMaterials(courseId) {
  matLoading.value = true;
  try { const r = await knowledgeApi.list(courseId); if (r.code === 200) courseMaterials.value = r.data || []; } catch {}
  finally { matLoading.value = false; }
}
async function loadAllKnowledge() {
  allKbLoading.value = true;
  try { const r = await knowledgeApi.listAll(); if (r.code === 200) allKnowledge.value = r.data || []; } catch {}
  finally { allKbLoading.value = false; }
}
async function removeMaterial(id) {
  try { await ElMessageBox.confirm('确定将此辅材移出课程？文件保留在知识库中。', '提示', { type: 'warning' }); }
  catch { return; }
  try { await knowledgeApi.assignToCourse(id, null); await loadCourseMaterials(materialsCourse.value.id); ElMessage.success('已移出'); } catch(e) { ElMessage.error(e?.response?.data?.message || e?.message || '操作失败'); }
}
async function doUpload() {
  if (!uploadFile.value) return;
  uploading.value = true;
  try {
    const r = await knowledgeApi.upload(uploadFile.value, materialsCourse.value.id, uploadFile.value.name);
    if (r.code === 200) {
      ElMessage.success('上传成功');
      uploadFile.value = null;
      await loadCourseMaterials(materialsCourse.value.id);
    } else {
      ElMessage.error(r.message || '上传失败');
    }
  } catch { ElMessage.error('上传失败'); }
  finally { uploading.value = false; }
}
async function linkKnowledge() {
  if (selectedKnowledge.value.length === 0) return;
  linking.value = true;
  try {
    for (const kid of selectedKnowledge.value) { try { await knowledgeApi.assignToCourse(kid, materialsCourse.value.id); } catch {} }
    await loadCourseMaterials(materialsCourse.value.id);
    await loadAllKnowledge();
    selectedKnowledge.value = [];
    ElMessage.success('已关联');
  } finally { linking.value = false; }
}

async function enterCourse(courseId) {
  entering.value = courseId;
  try {
    try { await courseApi.enroll(courseId); } catch { }
    const res = await chatApi.createSession(courseId);
    if (res.code === 200) router.push('/chat/' + res.data.id);
    else ElMessage.error('进入课程失败');
  } catch { ElMessage.error('进入课程失败'); }
  finally { entering.value = null; }
}

function difficultyText(d) { return { BEGINNER: '入门', INTERMEDIATE: '中级', ADVANCED: '高级' }[d] || d; }
function difficultyType(d) { return { BEGINNER: 'success', INTERMEDIATE: 'warning', ADVANCED: 'danger' }[d] || 'info'; }
function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

</script>


<style scoped>
.course-page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.course-card { display: flex; flex-direction: column; }
.course-card.own-course { border-left: 3px solid #e6a23c; }
.course-info h4 { margin: 0 0 8px 0; font-size: 16px; }
.course-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.course-desc { color: #909399; font-size: 13px; margin: 0 0 8px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.course-meta { display: flex; gap: 6px; margin-bottom: 8px; }
.course-teacher { font-size: 12px; color: #606266; }
.course-actions { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
</style>