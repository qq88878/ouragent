<template>
  <div class="knowledge-page">
    <div class="page-header">
      <div>
        <h3>知识库管理</h3>
        <p class="page-desc">统一管理教学资料与知识文档</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-if="isAdmin" v-model="approvalFilter" size="small" @change="loadKnowledge">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="PENDING">待审核</el-radio-button>
          <el-radio-button value="APPROVED">已通过</el-radio-button>
          <el-radio-button value="REJECTED">已拒绝</el-radio-button>
        </el-radio-group>
        <el-button v-if="isAdmin && selectedIds.length > 0" type="success" size="small" @click="openBatchApproveDialog(true)">
          批量通过 ({{ selectedIds.length }})
        </el-button>
        <el-button v-if="isAdmin && selectedIds.length > 0" type="warning" size="small" @click="openBatchApproveDialog(false)">
          批量拒绝 ({{ selectedIds.length }})
        </el-button>
        <el-button v-if="isTeacherOrAdmin" type="primary" @click="openUploadDialog">
          <el-icon :size="14"><Plus /></el-icon>
          <span>上传文件</span>
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input v-model="searchKeyword" placeholder="按文件名搜索..." clearable class="search-input" @keyup.enter="doSearch" @clear="doSearch">
        <template #prefix><el-icon :size="16"><Search /></el-icon></template>
        <template #append>
          <el-button @click="doSearch" :loading="loading">搜索</el-button>
        </template>
      </el-input>
    </div>

    <el-table :data="knowledgeList" v-loading="loading" stripe class="kb-table" @selection-change="handleSelectionChange">
      <template #empty>
        <el-empty v-if="!loading" description="暂无知识库文件" :image-size="80" />
      </template>
      <el-table-column v-if="isAdmin" type="selection" width="50" />
      <el-table-column prop="name" label="文件名" min-width="200">
        <template #default="{ row }">
          <div class="file-name-cell">
            <span class="file-icon">{{ fileTypeIcon(row.fileType) }}</span>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="上传者" width="120">
        <template #default="{ row }">{{ row.uploadedByName || '-' }}</template>
      </el-table-column>
      <el-table-column label="所属课程" width="160">
        <template #default="{ row }">
          <el-tag v-if="row.courseName" size="small" effect="plain" round>{{ row.courseName }}</el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="fileType" label="类型" width="90">
        <template #default="{ row }">
          <el-tag size="small" effect="plain" round>{{ row.fileType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="审核状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getApprovalTagType(row.approvalStatus)" size="small" effect="plain" round>
            {{ getApprovalLabel(row.approvalStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="上传时间" width="170">
        <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="viewContent(row.id)">查看内容</el-button>
          <template v-if="isAdmin && row.approvalStatus === 'PENDING'">
            <el-button text type="success" size="small" @click="openApproveDialog(row.id, true)">通过</el-button>
            <el-button text type="warning" size="small" @click="openApproveDialog(row.id, false)">拒绝</el-button>
          </template>
          <el-button v-if="isTeacherOrAdmin" text type="danger" size="small" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传弹窗 -->
    <el-dialog v-if="isTeacherOrAdmin" v-model="showUploadDialog" title="上传知识库文件" width="500px">
      <el-form label-width="70px">
        <el-form-item label="课程">
          <el-select v-model="uploadForm.courseId" placeholder="可不选，上传到公共库" clearable style="width: 100%;">
            <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件名">
          <el-input v-model="uploadForm.name" placeholder="自定义文件名（选填）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" placeholder="文件描述（选填）" />
        </el-form-item>
        <el-form-item label="文件">
          <el-upload :auto-upload="false" :on-change="handleFileAdd" multiple drag style="width: 100%;">
            <el-icon :size="32" color="#C4BAB0"><UploadFilled /></el-icon>
            <div style="margin-top: 6px; font-size: 13px;">拖拽或点击选择文件（可多选）</div>
          </el-upload>
          <div v-if="uploadForm.files.length > 0" class="file-list">
            <div v-for="(f, idx) in uploadForm.files" :key="idx" class="file-item">
              <span class="file-item-name">{{ f.name }}</span>
              <span class="file-item-size">{{ formatSize(f.size) }}</span>
              <el-button text type="danger" size="small" @click="removeFile(idx)">
                <el-icon :size="14"><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="doUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 审核弹窗 -->
    <el-dialog v-model="showApproveDialog" title="文件审核" width="420px">
      <el-form>
        <el-form-item label="备注">
          <el-input v-model="approveForm.remark" type="textarea" :rows="3" placeholder="审核备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button :type="approveForm.approved ? 'success' : 'warning'" @click="doApprove">确认{{ approveForm.approved ? '通过' : '拒绝' }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量审核弹窗 -->
    <el-dialog v-model="showBatchApproveDialog" :title="(batchApproveForm.approved ? '批量通过' : '批量拒绝') + '文件'" width="420px">
      <el-form>
        <el-form-item label="备注">
          <el-input v-model="batchApproveForm.remark" type="textarea" :rows="3" placeholder="批量审核备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchApproveDialog = false">取消</el-button>
        <el-button :type="batchApproveForm.approved ? 'success' : 'warning'" @click="doBatchApprove">确认</el-button>
      </template>
    </el-dialog>

    <!-- 内容预览弹窗 -->
    <el-dialog v-model="showContentDialog" :title="'查看内容: ' + contentName" width="800px" top="3vh">
      <div v-loading="contentLoading" style="max-height: 70vh; overflow-y: auto;">
        <template v-if="!contentLoading && contentText">
          <div v-if="isPreviewPlaceholder" class="content-unavailable">
            <el-icon :size="48" color="#C4BAB0"><WarningFilled /></el-icon>
            <p>{{ contentText }}</p>
          </div>
          <pre v-else class="content-preview">{{ contentText }}</pre>
        </template>
        <el-empty v-if="!contentLoading && !contentText" description="无法加载内容" :image-size="60" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { knowledgeApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, UploadFilled, WarningFilled, Document } from '@element-plus/icons-vue';

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isTeacherOrAdmin = computed(() => authStore.user?.role === 'TEACHER' || authStore.user?.role === 'ADMIN');

const knowledgeList = ref([]);
const loading = ref(false);
const searchKeyword = ref('');
const approvalFilter = ref('');
const selectedIds = ref([]);
const courses = ref([]);

const showUploadDialog = ref(false);
const uploadForm = reactive({ courseId: null, files: [], name: '', description: '' });
const uploading = ref(false);

const showApproveDialog = ref(false);
const approveForm = reactive({ id: null, approved: true, remark: '' });

const showBatchApproveDialog = ref(false);
const batchApproveForm = reactive({ approved: true, remark: '' });

const showContentDialog = ref(false);
const contentText = ref('');
const contentName = ref('');
const contentLoading = ref(false);
const isPreviewPlaceholder = computed(() => contentText.value && contentText.value.startsWith('[此文件类型'));

const fileTypeIcons = {
  pdf: '📄', doc: '📝', docx: '📝', ppt: '📊', pptx: '📊',
  xls: '📈', xlsx: '📈', txt: '📃', md: '📋', png: '🖼️', jpg: '🖼️', jpeg: '🖼️',
};
const fileTypeIcon = (t) => fileTypeIcons[(t || '').toLowerCase()] || '📁';

onMounted(async () => {
  await loadKnowledge();
  if (isTeacherOrAdmin.value) { try { const r = await courseApi.list({ page: 1, size: 200 }); if (r.code === 200) courses.value = r.data?.records || []; } catch {} }
});

async function loadKnowledge() {
  loading.value = true;
  try {
    let res;
    if (approvalFilter.value === 'PENDING') {
      res = await knowledgeApi.listPending();
    } else {
      res = await knowledgeApi.listAll();
    }
    if (res.code === 200) {
      let data = res.data || [];
      if (approvalFilter.value && approvalFilter.value !== 'PENDING') {
        data = data.filter(k => k.approvalStatus === approvalFilter.value);
      }
      knowledgeList.value = data;
    }
  } catch {} finally { loading.value = false; }
}

async function doSearch() {
  loading.value = true; approvalFilter.value = '';
  try {
    if (searchKeyword.value.trim()) { const res = await knowledgeApi.search(searchKeyword.value.trim()); if (res.code === 200) knowledgeList.value = res.data || []; }
    else { await loadKnowledge(); }
  } catch {} finally { loading.value = false; }
}

async function viewContent(id) {
  contentLoading.value = true; contentText.value = ''; contentName.value = ''; showContentDialog.value = true;
  try { const res = await knowledgeApi.getContent(id); if (res.code === 200) { contentText.value = res.data.content || ''; contentName.value = res.data.name || ''; } }
  catch { ElMessage.error('加载内容失败'); } finally { contentLoading.value = false; }
}

function handleFileAdd(file) {
  const f = file.raw;
  if (!uploadForm.files.some(existing => existing.name === f.name && existing.size === f.size)) {
    uploadForm.files.push(f);
  }
}
function removeFile(idx) { uploadForm.files.splice(idx, 1); }

function openUploadDialog() { Object.assign(uploadForm, { courseId: null, files: [], name: '', description: '' }); showUploadDialog.value = true; }

async function doUpload() {
  if (uploadForm.files.length === 0) { ElMessage.warning('请选择文件'); return; }
  uploading.value = true;
  try {
    const res = await knowledgeApi.uploadBatch(uploadForm.files, uploadForm.courseId || null, uploadForm.name, uploadForm.description);
    if (res.code === 200) {
      const count = res.data ? res.data.length : uploadForm.files.length;
      ElMessage.success(`成功上传 ${count} 个文件`);
      showUploadDialog.value = false;
      await loadKnowledge();
    }
  } catch { ElMessage.error('上传失败'); } finally { uploading.value = false; }
}

async function remove(id) {
  try { await ElMessageBox.confirm('确定删除此知识库文件？', '提示', { type: 'warning' }); await knowledgeApi.delete(id); await loadKnowledge(); ElMessage.success('已删除'); }
  catch {}
}

function handleSelectionChange(selection) { selectedIds.value = selection.map(item => item.id); }

function openApproveDialog(id, approved) { Object.assign(approveForm, { id, approved, remark: '' }); showApproveDialog.value = true; }

function openBatchApproveDialog(approved) { Object.assign(batchApproveForm, { approved, remark: '' }); showBatchApproveDialog.value = true; }

async function doApprove() {
  try { const { id, approved, remark } = approveForm; await knowledgeApi.approve(id, approved, remark); showApproveDialog.value = false; await loadKnowledge(); ElMessage.success(`已${approved ? '通过' : '拒绝'}`); }
  catch { ElMessage.error('操作失败'); }
}

async function doBatchApprove() {
  try { const { approved, remark } = batchApproveForm; await knowledgeApi.batchApprove(selectedIds.value, approved, remark); showBatchApproveDialog.value = false; selectedIds.value = []; await loadKnowledge(); ElMessage.success(`已批量${approved ? '通过' : '拒绝'}`); }
  catch { ElMessage.error('操作失败'); }
}

function getApprovalTagType(s) { return { APPROVED: 'success', REJECTED: 'danger', PENDING: 'warning' }[s] || 'info'; }
function getApprovalLabel(s) { return { APPROVED: '已通过', REJECTED: '已拒绝', PENDING: '待审核' }[s] || s; }
function formatSize(bytes) { if (!bytes) return '-'; if (bytes < 1024) return bytes + ' B'; if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'; return (bytes / 1024 / 1024).toFixed(1) + ' MB'; }
</script>

<style scoped>
.knowledge-page { max-width: 1260px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 14px; }
.page-header h3 { font-size: 24px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.page-desc { font-size: 14px; color: var(--color-text-muted); margin-top: 4px; }
.header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

.search-bar { margin-bottom: 22px; }
.search-input { width: 400px; }

.kb-table { border-radius: var(--radius-lg); overflow: hidden; }
.kb-table :deep(.el-table__body tr:hover > td) { background: var(--color-bg-hover) !important; }
.file-name-cell { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.file-icon { font-size: 18px; flex-shrink: 0; }
.text-muted { color: var(--color-text-placeholder); }

.content-unavailable { text-align: center; padding: 48px 20px; color: var(--color-text-muted); }
.content-unavailable p { margin-top: 18px; font-size: 14px; }
.content-preview {
  background: var(--color-bg); padding: 24px; border-radius: var(--radius-md);
  font-size: 14px; line-height: 1.9; white-space: pre-wrap; word-break: break-all;
  max-height: 60vh; overflow-y: auto;
}

.file-list { margin-top: 10px; max-height: 160px; overflow-y: auto; }
.file-item { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--color-bg); border-radius: 6px; margin-bottom: 4px; font-size: 13px; }
.file-item-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--color-text); }
.file-item-size { color: var(--color-text-muted); font-size: 12px; flex-shrink: 0; }
</style>