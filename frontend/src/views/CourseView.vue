<template>
  <div class="course-page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h3>课程中心</h3>
        <p class="page-desc">共 {{ total }} 门课程，持续更新中</p>
      </div>
      <el-button v-if="isTeacher" type="primary" size="large" @click="showCreateDialog = true" class="create-btn">
        <el-icon :size="18"><Plus /></el-icon>
        <span>创建课程</span>
      </el-button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <el-input v-model="query.keyword" placeholder="搜索课程名称或描述..." clearable class="filter-search" @keyup.enter="loadCourses" @clear="loadCourses">
        <template #prefix><el-icon :size="16"><Search /></el-icon></template>
      </el-input>
      <el-select v-model="query.category" placeholder="分类" clearable @change="loadCourses" class="filter-select">
        <el-option label="编程" value="编程" />
        <el-option label="数学" value="数学" />
        <el-option label="外语" value="外语" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="query.difficulty" placeholder="难度" clearable @change="loadCourses" class="filter-select">
        <el-option label="入门" value="BEGINNER" />
        <el-option label="中级" value="INTERMEDIATE" />
        <el-option label="高级" value="ADVANCED" />
      </el-select>
      <span class="filter-result" v-if="!loading">找到 {{ total }} 门课程</span>
    </div>

    <!-- Course Grid -->
    <div v-loading="loading" class="course-grid">
      <div v-for="course in sortedCourses" :key="course.id" class="course-card" :class="{ 'own-course': isTeacher && course.teacherId === userId }">
        <div class="course-cover" :style="{ background: coverGradient(course.id) }">
          <div class="cover-pattern"></div>
          <div class="cover-top">
            <el-tag v-if="isTeacher && course.teacherId === userId" size="small" type="warning" effect="dark" class="cover-tag">我的</el-tag>
            <el-tag size="small" effect="dark" class="cover-tag diff-tag">{{ difficultyText(course.difficulty) }}</el-tag>
          </div>
          <div class="cover-center">
            <span class="cover-category">{{ course.category || '未分类' }}</span>
          </div>
          <div class="cover-bottom-decor"></div>
        </div>

        <div class="course-body">
          <h4 class="course-title" @click="$router.push(`/courses/${course.id}`)">{{ course.title }}</h4>
          <p class="course-desc">{{ course.description || '暂无描述' }}</p>

          <div class="course-meta-row">
            <div class="meta-item">
              <el-icon :size="14"><UserFilled /></el-icon>
              <span>{{ course.teacherName || '-' }}</span>
            </div>
            <div class="meta-item" v-if="course.enrollmentCount !== undefined">
              <el-icon :size="14"><Avatar /></el-icon>
              <span>{{ course.enrollmentCount || 0 }} 人已选</span>
            </div>
            <el-tag size="small" :type="course.status === 1 ? 'success' : 'info'" effect="plain" round>
              {{ course.status === 1 ? '已发布' : '草稿' }}
            </el-tag>
          </div>

          <div class="course-actions">
            <el-button size="small" round @click.stop="$router.push(`/courses/${course.id}`)">
              查看详情
            </el-button>
            <template v-if="isTeacher && course.teacherId === userId">
              <el-button size="small" round plain @click.stop="openMaterials(course)">管理辅材</el-button>
              <el-button size="small" round plain @click.stop="openEdit(course)">编辑</el-button>
              <el-button size="small" round plain type="danger" @click.stop="deleteCourse(course.id)">删除</el-button>
            </template>
            <template v-if="isAdmin">
              <el-button size="small" round plain @click.stop="openMaterials(course)">管理辅材</el-button>
              <el-button size="small" round plain @click.stop="openEdit(course)">编辑</el-button>
              <el-button size="small" round plain type="danger" @click.stop="deleteCourse(course.id)">删除</el-button>
            </template>
            <template v-if="isStudent">
              <el-button type="primary" size="small" round :loading="entering === course.id" @click.stop="enterCourse(course.id)">
                进入学习
              </el-button>
            </template>
          </div>
        </div>
      </div>
      <el-empty v-if="sortedCourses.length === 0 && !loading" description="暂无课程" :image-size="100" />
    </div>

    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination layout="total, prev, pager, next" :total="total" :page-size="query.size" v-model:current-page="query.page" @current-change="loadCourses" />
    </div>

    <!-- Dialogs (unchanged) -->
    <el-dialog v-model="showCreateDialog" title="创建课程" width="520px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="课程名称" required><el-input v-model="createForm.title" placeholder="课程名称" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="createForm.category" placeholder="选择分类" style="width:100%"><el-option label="编程" value="编程"/><el-option label="数学" value="数学"/><el-option label="外语" value="外语"/><el-option label="其他" value="其他"/></el-select></el-form-item>
        <el-form-item label="难度"><el-select v-model="createForm.difficulty" placeholder="选择难度" style="width:100%"><el-option label="入门" value="BEGINNER"/><el-option label="中级" value="INTERMEDIATE"/><el-option label="高级" value="ADVANCED"/></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="createForm.description" type="textarea" rows="3" placeholder="课程描述"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreateDialog=false">取消</el-button><el-button type="primary" @click="doCreate" :loading="creating">创建</el-button></template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑课程" width="520px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="课程名称" required><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="editForm.category" style="width:100%"><el-option label="编程" value="编程"/><el-option label="数学" value="数学"/><el-option label="外语" value="外语"/><el-option label="其他" value="其他"/></el-select></el-form-item>
        <el-form-item label="难度"><el-select v-model="editForm.difficulty" style="width:100%"><el-option label="入门" value="BEGINNER"/><el-option label="中级" value="INTERMEDIATE"/><el-option label="高级" value="ADVANCED"/></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" rows="3"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="showEditDialog=false">取消</el-button><el-button type="primary" @click="doEdit" :loading="editing">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="showMaterialsDialog" :title="'辅材管理: ' + (materialsCourse?.title || '')" width="640px">
      <el-tabs v-model="materialsTab">
        <el-tab-pane label="已关联" name="current">
          <el-table :data="courseMaterials" v-loading="matLoading" empty-text="暂无辅材">
            <el-table-column prop="name" label="文件名" min-width="160" />
            <el-table-column prop="fileType" label="类型" width="80" />
            <el-table-column label="大小" width="90"><template #default="{row}">{{ formatSize(row.fileSize) }}</template></el-table-column>
            <el-table-column label="操作" width="80"><template #default="{row}"><el-button text type="danger" size="small" @click="removeMaterial(row.id)">移出</el-button></template></el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="从知识库添加" name="add">
          <el-table :data="allKnowledge" v-loading="allKbLoading" @selection-change="(v) => selectedKnowledge = v.map(i=>i.id)" empty-text="暂无可用文件">
            <el-table-column type="selection" width="40" />
            <el-table-column prop="name" label="文件名" min-width="160" />
            <el-table-column prop="fileType" label="类型" width="80" />
            <el-table-column label="大小" width="90"><template #default="{row}">{{ formatSize(row.fileSize) }}</template></el-table-column>
          </el-table>
          <div style="margin-top:12px"><el-button type="primary" :disabled="selectedKnowledge.length===0" :loading="linking" @click="linkKnowledge">关联选中文件</el-button></div>
        </el-tab-pane>
        <el-tab-pane label="上传新文件" name="upload">
          <el-upload :auto-upload="false" :limit="1" :on-change="(f) => uploadFile = f.raw" accept="*">
            <el-button plain>选择文件</el-button>
          </el-upload>
          <div v-if="uploadFile" style="margin-top:10px;font-size:13px;color:var(--color-text-secondary)">已选: {{ uploadFile.name }} ({{ formatSize(uploadFile.size) }})</div>
          <div style="margin-top:12px"><el-button type="primary" :disabled="!uploadFile" :loading="uploading" @click="doUpload">上传</el-button></div>
        </el-tab-pane>
      </el-tabs>
      <template #footer><el-button @click="showMaterialsDialog=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { courseApi, knowledgeApi, chatApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, UserFilled, Avatar } from '@element-plus/icons-vue';

const router = useRouter();
const authStore = useAuthStore();
const user = computed(() => authStore.user);
const userId = computed(() => user.value?.id);
const isTeacher = computed(() => user.value?.role === 'TEACHER');
const isAdmin = computed(() => user.value?.role === 'ADMIN');
const isStudent = computed(() => user.value?.role === 'STUDENT');

const courses = ref([]);
const total = ref(0);
const loading = ref(false);
const query = reactive({ page: 1, size: 12, keyword: '', category: '', difficulty: '' });

const showCreateDialog = ref(false);
const creating = ref(false);
const createForm = reactive({ title: '', category: '', difficulty: 'BEGINNER', description: '' });

const showEditDialog = ref(false);
const editing = ref(false);
const editForm = reactive({ id: null, title: '', category: '', difficulty: '', description: '' });

const showMaterialsDialog = ref(false);
const materialsTab = ref('current');
const materialsCourse = ref(null);
const courseMaterials = ref([]);
const allKnowledge = ref([]);
const selectedKnowledge = ref([]);
const uploadFile = ref(null);
const matLoading = ref(false);
const allKbLoading = ref(false);
const linking = ref(false);
const uploading = ref(false);
const entering = ref(null);

const sortedCourses = computed(() => courses.value);

const gradients = [
  'linear-gradient(135deg, #8B5E3C, #B5651D)',
  'linear-gradient(135deg, #5B7B5A, #5B8C5A)',
  'linear-gradient(135deg, #7B5E3C, #C1803A)',
  'linear-gradient(135deg, #4A6B7A, #5B8BA8)',
  'linear-gradient(135deg, #7B4A5A, #A55B6E)',
  'linear-gradient(135deg, #5A5B7B, #7B5EA7)',
];
function coverGradient(id) { return gradients[(id || 0) % gradients.length]; }

onMounted(() => loadCourses());

async function loadCourses() {
  loading.value = true;
  try { const r = await courseApi.list({ ...query }); if (r.code === 200) { courses.value = r.data?.records || []; total.value = r.data?.total || 0; } } catch {} finally { loading.value = false; }
}

async function doCreate() {
  if (!createForm.title) { ElMessage.warning('请输入课程名称'); return; }
  creating.value = true;
  try { const r = await courseApi.create({ ...createForm }); if (r.code === 200) { ElMessage.success('创建成功'); showCreateDialog.value = false; Object.assign(createForm, { title: '', category: '', difficulty: 'BEGINNER', description: '' }); await loadCourses(); } } catch { ElMessage.error('创建失败'); } finally { creating.value = false; }
}

function openEdit(course) { Object.assign(editForm, { id: course.id, title: course.title, category: course.category, difficulty: course.difficulty, description: course.description }); showEditDialog.value = true; }

async function doEdit() {
  if (!editForm.title) return;
  editing.value = true;
  try { await courseApi.update(editForm.id, { title: editForm.title, category: editForm.category, difficulty: editForm.difficulty, description: editForm.description }); ElMessage.success('已更新'); showEditDialog.value = false; await loadCourses(); } catch { ElMessage.error('更新失败'); } finally { editing.value = false; }
}

async function deleteCourse(id) {
  try { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); } catch { return; }
  try { await courseApi.delete(id); ElMessage.success('已删除'); await loadCourses(); } catch { ElMessage.error('删除失败'); }
}

async function openMaterials(course) { materialsCourse.value = course; materialsTab.value = 'current'; showMaterialsDialog.value = true; await loadCourseMaterials(course.id); await loadAllKnowledge(); }
async function loadCourseMaterials(courseId) { matLoading.value = true; try { const r = await knowledgeApi.list(courseId); if (r.code === 200) courseMaterials.value = r.data || []; } catch {} finally { matLoading.value = false; } }
async function loadAllKnowledge() { allKbLoading.value = true; try { const r = await knowledgeApi.listAll(); if (r.code === 200) allKnowledge.value = r.data || []; } catch {} finally { allKbLoading.value = false; } }
async function removeMaterial(id) { try { await ElMessageBox.confirm('确定移出？文件保留在知识库。', '提示', { type: 'warning' }); } catch { return; } try { await knowledgeApi.assignToCourse(id, null); await loadCourseMaterials(materialsCourse.value.id); ElMessage.success('已移出'); } catch(e) { ElMessage.error(e?.response?.data?.message || e?.message || '操作失败'); } }
async function doUpload() { if (!uploadFile.value) return; uploading.value = true; try { const r = await knowledgeApi.upload(uploadFile.value, materialsCourse.value.id, uploadFile.value.name); if (r.code === 200) { ElMessage.success('上传成功'); uploadFile.value = null; await loadCourseMaterials(materialsCourse.value.id); } else { ElMessage.error(r.message || '上传失败'); } } catch { ElMessage.error('上传失败'); } finally { uploading.value = false; } }
async function linkKnowledge() { if (selectedKnowledge.value.length === 0) return; linking.value = true; try { for (const kid of selectedKnowledge.value) { try { await knowledgeApi.assignToCourse(kid, materialsCourse.value.id); } catch {} } await loadCourseMaterials(materialsCourse.value.id); await loadAllKnowledge(); selectedKnowledge.value = []; ElMessage.success('已关联'); } finally { linking.value = false; } }
async function enterCourse(courseId) { entering.value = courseId; try { try { await courseApi.enroll(courseId); } catch {} const res = await chatApi.createSession(courseId); if (res.code === 200) router.push('/chat/' + res.data.id); else ElMessage.error('进入课程失败'); } catch { ElMessage.error('进入课程失败'); } finally { entering.value = null; } }
function difficultyText(d) { return { BEGINNER: '入门', INTERMEDIATE: '中级', ADVANCED: '高级' }[d] || d; }
function formatSize(bytes) { if (!bytes) return '-'; if (bytes < 1024) return bytes + ' B'; if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'; return (bytes / 1024 / 1024).toFixed(1) + ' MB'; }
</script>

<style scoped>
.course-page { max-width: 1260px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h3 { font-size: 24px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.page-desc { font-size: 14px; color: var(--color-text-muted); margin-top: 4px; }
.create-btn { padding: 12px 24px !important; font-size: 15px; border-radius: 12px !important; }

.filter-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 28px;
  padding: 16px 20px; background: var(--color-bg-card);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
}
.filter-search { width: 300px; }
.filter-select { width: 130px; }
.filter-result { font-size: 13px; color: var(--color-text-muted); white-space: nowrap; margin-left: auto; font-weight: 500; }

.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 22px; }

.course-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  overflow: hidden; box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
}
.course-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-lg); }
.course-card.own-course { box-shadow: 0 0 0 2px #C1803A, var(--shadow-card); }
.course-card.own-course:hover { box-shadow: 0 0 0 2px #C1803A, var(--shadow-lg); }

.course-cover {
  height: 110px; position: relative; padding: 16px 18px;
  display: flex; flex-direction: column; justify-content: space-between;
  overflow: hidden;
}
.cover-pattern {
  position: absolute; inset: 0; opacity: 0.06;
  background-image: repeating-linear-gradient(45deg, #fff 0px, #fff 2px, transparent 2px, transparent 16px);
}
.cover-top { display: flex; justify-content: space-between; align-items: flex-start; position: relative; z-index: 1; }
.cover-tag { backdrop-filter: blur(4px); }
.diff-tag { background: rgba(255,255,255,0.2) !important; border: 1px solid rgba(255,255,255,0.25) !important; }
.cover-center { position: relative; z-index: 1; }
.cover-category {
  font-size: 11px; color: rgba(255,255,255,0.75);
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;
  background: rgba(255,255,255,0.12); padding: 3px 10px; border-radius: 6px;
}
.cover-bottom-decor {
  position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
  background: rgba(255,255,255,0.15);
}

.course-body { padding: 20px 22px 22px; }
.course-title {
  font-size: 17px; font-weight: 700; color: var(--color-text);
  margin-bottom: 8px; line-height: 1.35; cursor: pointer;
  transition: color 0.15s ease; letter-spacing: -0.01em;
}
.course-title:hover { color: var(--color-primary); }
.course-desc {
  font-size: 13px; color: var(--color-text-muted); line-height: 1.6;
  margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.course-meta-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--color-text-secondary); }
.course-actions { display: flex; gap: 8px; flex-wrap: wrap; padding-top: 4px; border-top: 1px solid var(--color-border-light); }
.pagination-wrap { margin-top: 32px; display: flex; justify-content: center; }
</style>
