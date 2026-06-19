<template>
  <div class="course-page">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h3>课程中心</h3>
        <p class="page-desc">共 {{ total }} 门课程，持续更新中</p>
      </div>
      <el-button v-if="isTeacher" type="primary" size="large" @click="showCreateDialog = true">
        <el-icon :size="16"><Plus /></el-icon>
        <span>创建课程</span>
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="query.keyword" placeholder="搜索课程名称或描述..." clearable class="filter-search" @keyup.enter="loadCourses" @clear="loadCourses">
        <template #prefix><el-icon :size="16"><Search /></el-icon></template>
      </el-input>
      <el-select v-model="query.category" placeholder="分类" clearable @change="loadCourses">
        <el-option label="编程" value="编程" />
        <el-option label="数学" value="数学" />
        <el-option label="外语" value="外语" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="query.difficulty" placeholder="难度" clearable @change="loadCourses">
        <el-option label="入门" value="BEGINNER" />
        <el-option label="中级" value="INTERMEDIATE" />
        <el-option label="高级" value="ADVANCED" />
      </el-select>
      <span class="filter-result" v-if="!loading">找到 {{ total }} 门课程</span>
    </div>

    <!-- 课程卡片 -->
    <div v-loading="loading" class="course-grid">
      <div v-for="course in sortedCourses" :key="course.id" class="course-card" :class="{ 'own-course': isTeacher && course.teacherId === userId }">
        <!-- 封面 -->
        <div class="course-cover" :style="{ background: coverGradient(course.id) }">
          <div class="cover-top">
            <el-tag v-if="isTeacher && course.teacherId === userId" size="small" type="warning" effect="dark">我的</el-tag>
            <el-tag size="small" effect="dark" class="cover-diff-tag">{{ difficultyText(course.difficulty) }}</el-tag>
          </div>
          <div class="cover-bottom">
            <span class="cover-category">{{ course.category || '未分类' }}</span>
          </div>
        </div>

        <!-- 内容 -->
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

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination layout="total, prev, pager, next" :total="total" :page-size="query.size" v-model:current-page="query.page" @current-change="loadCourses" />
    </div>

    <!-- 创建课程弹窗 -->
    <el-dialog v-model="showCreateDialog" title="创建课程" width="520px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="createForm.title" placeholder="输入课程名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="课程简介、教学目标等" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="createForm.category" placeholder="选择分类" style="width:100%;">
                <el-option label="编程" value="编程" /><el-option label="数学" value="数学" />
                <el-option label="外语" value="外语" /><el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度">
              <el-select v-model="createForm.difficulty" placeholder="选择难度" style="width:100%;">
                <el-option label="入门" value="BEGINNER" /><el-option label="中级" value="INTERMEDIATE" />
                <el-option label="高级" value="ADVANCED" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">创建课程</el-button>
      </template>
    </el-dialog>

    <!-- 编辑课程弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑课程" width="520px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="editForm.title" placeholder="输入课程名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="分类"><el-select v-model="editForm.category" style="width:100%;"><el-option label="编程" value="编程" /><el-option label="数学" value="数学" /><el-option label="外语" value="外语" /><el-option label="其他" value="其他" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="难度"><el-select v-model="editForm.difficulty" style="width:100%;"><el-option label="入门" value="BEGINNER" /><el-option label="中级" value="INTERMEDIATE" /><el-option label="高级" value="ADVANCED" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="状态"><el-select v-model="editForm.status" style="width:100%;"><el-option label="草稿" :value="0" /><el-option label="已发布" :value="1" /></el-select></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 辅材管理弹窗 -->
    <el-dialog v-model="showMaterialsDialog" :title="'管理辅材: ' + (materialsCourse?.title || '')" width="700px">
      <el-tabs v-model="materialsTab">
        <el-tab-pane label="当前辅材" name="current">
          <el-table :data="courseMaterials" v-loading="matLoading" empty-text="暂无辅材" max-height="300">
            <el-table-column prop="name" label="文件名" min-width="180" />
            <el-table-column prop="fileType" label="类型" width="80"><template #default="{ row }"><el-tag size="small" round>{{ row.fileType }}</el-tag></template></el-table-column>
            <el-table-column label="大小" width="100"><template #default="{ row }">{{ formatSize(row.fileSize) }}</template></el-table-column>
            <el-table-column label="操作" width="80"><template #default="{ row }"><el-button text type="danger" size="small" @click="removeMaterial(row.id)">移除</el-button></template></el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="上传文件" name="upload">
          <el-upload :auto-upload="false" :on-change="(f) => uploadFile = f.raw" :limit="1" drag>
            <el-icon :size="36" color="#C9CDD4"><UploadFilled /></el-icon>
            <div style="margin-top:8px;font-size:13px;">拖拽或点击上传</div>
          </el-upload>
          <el-button type="primary" :loading="uploading" @click="doUpload" style="margin-top:12px;" :disabled="!uploadFile">上传</el-button>
        </el-tab-pane>
        <el-tab-pane label="关联知识库" name="link">
          <el-table :data="allKnowledge" v-loading="allKbLoading" max-height="300" @selection-change="(v) => selectedKnowledge = v.map(i => i.id)">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="name" label="文件名" min-width="180" />
            <el-table-column prop="fileType" label="类型" width="80" />
          </el-table>
          <el-button type="primary" :loading="linking" @click="linkKnowledge" style="margin-top:12px;" :disabled="selectedKnowledge.length===0">关联选中</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { courseApi, chatApi, knowledgeApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, UserFilled, Avatar, UploadFilled } from '@element-plus/icons-vue';

const router = useRouter();
const authStore = useAuthStore();
const isTeacher = computed(() => authStore.user?.role === 'TEACHER');
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isStudent = computed(() => authStore.user?.role === 'STUDENT');
const userId = computed(() => authStore.user?.id);

const courses = ref([]); const loading = ref(false); const total = ref(0); const saving = ref(false); const entering = ref(null);
const query = reactive({ page: 1, size: 12, keyword: '', category: '', difficulty: '' });
const sortedCourses = computed(() => {
  const own = courses.value.filter(c => c.teacherId === userId.value);
  const other = courses.value.filter(c => c.teacherId !== userId.value);
  return [...own, ...other];
});

const coverGradients = [
  'linear-gradient(135deg, #5B6AF0, #A78BFA)',
  'linear-gradient(135deg, #34C759, #30D158)',
  'linear-gradient(135deg, #FF9500, #FFB340)',
  'linear-gradient(135deg, #FF3B30, #FF6B60)',
  'linear-gradient(135deg, #5AC8FA, #80D8FF)',
  'linear-gradient(135deg, #AF52DE, #C77DFF)',
];
const coverGradient = (id) => coverGradients[(id || 0) % coverGradients.length];

const showCreateDialog = ref(false); const createForm = reactive({ title: '', description: '', category: '', difficulty: 'BEGINNER' });
const showEditDialog = ref(false); const editForm = reactive({ id: null, title: '', description: '', category: '', difficulty: 'BEGINNER', status: 1 });
const showMaterialsDialog = ref(false); const materialsCourse = ref(null); const materialsTab = ref('current');
const courseMaterials = ref([]); const matLoading = ref(false); const uploadFile = ref(null); const uploading = ref(false);
const allKnowledge = ref([]); const allKbLoading = ref(false); const selectedKnowledge = ref([]); const linking = ref(false);

onMounted(() => loadCourses());
async function loadCourses() { loading.value = true; try { const res = await courseApi.list({ ...query }); if (res.code === 200) { courses.value = res.data?.records || []; total.value = res.data?.total || 0; } } catch {} finally { loading.value = false; } }
async function doCreate() { if (!createForm.title.trim()) { ElMessage.warning('请输入课程名称'); return; } saving.value = true; try { await courseApi.create({ ...createForm }); ElMessage.success('创建成功'); showCreateDialog.value = false; Object.assign(createForm, { title: '', description: '', category: '', difficulty: 'BEGINNER' }); await loadCourses(); } catch { ElMessage.error('创建失败'); } finally { saving.value = false; } }
function openEdit(course) { Object.assign(editForm, { id: course.id, title: course.title, description: course.description || '', category: course.category || '', difficulty: course.difficulty || 'BEGINNER', status: course.status }); showEditDialog.value = true; }
async function saveEdit() { if (!editForm.title.trim()) { ElMessage.warning('请输入课程名称'); return; } saving.value = true; try { await courseApi.update(editForm.id, editForm); ElMessage.success('保存成功'); showEditDialog.value = false; await loadCourses(); } catch { ElMessage.error('保存失败'); } finally { saving.value = false; } }
async function deleteCourse(id) { try { await ElMessageBox.confirm('确定删除该课程？所有数据不可恢复。', '警告', { type: 'error' }); await courseApi.delete(id); ElMessage.success('已删除'); await loadCourses(); } catch {} }
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
.course-page { max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h3 { font-size: 22px; font-weight: 700; color: var(--color-text); }
.page-desc { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }

.filter-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 22px; }
.filter-search { width: 280px; }
.filter-result { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; margin-left: 8px; }

.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 18px; }

.course-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  overflow: hidden; box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
}
.course-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }
.course-card.own-course { box-shadow: 0 0 0 2px #FFB340, var(--shadow-card); }

.course-cover {
  height: 90px; position: relative; padding: 12px 14px;
  display: flex; flex-direction: column; justify-content: space-between;
}
.cover-top { display: flex; justify-content: space-between; align-items: flex-start; }
.cover-bottom { display: flex; }
.cover-category {
  font-size: 10px; color: rgba(255,255,255,0.7);
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
  background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px;
}

.course-body { padding: 16px 18px 18px; }
.course-title {
  font-size: 16px; font-weight: 700; color: var(--color-text);
  margin-bottom: 6px; line-height: 1.3; cursor: pointer;
  transition: color var(--transition-fast);
}
.course-title:hover { color: var(--color-primary); }
.course-desc {
  font-size: 12px; color: var(--color-text-muted); line-height: 1.5;
  margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.course-meta-row { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--color-text-secondary); }
.course-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.pagination-wrap { margin-top: 28px; display: flex; justify-content: center; }
</style>
