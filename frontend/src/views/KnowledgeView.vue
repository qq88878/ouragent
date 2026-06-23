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
      <el-table-column label="上传者" width="120">
        <template #default="{ row }">{{ row.uploadedByName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="fileType" label="类型" width="90">
        <template #default="{ row }">
          <el-tag size="small" effect="plain" round>{{ row.fileType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
      </el-table-column>
      <el-table-column label="备注" min-width="160">
        <template #default="{ row }">
          <template v-if="canEdit(row)">
            <span v-if="!row._editing" class="remark-text" @click="startEditRemark(row)">{{ row.remark || '点击添加备注' }}</span>
            <el-input v-else v-model="row._remarkValue" size="small" @blur="saveRemark(row)" @keyup.enter="saveRemark(row)" placeholder="输入备注" />
          </template>
          <span v-else class="text-muted">{{ row.remark || '-' }}</span>
        </template>
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
          <el-button v-if="canDelete(row)" text type="danger" size="small" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传弹窗 -->
    <el-dialog v-if="isTeacherOrAdmin" v-model="showUploadDialog" title="上传知识库文件" width="480px">
      <el-upload
        ref="uploadRef"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileAdd"
        :file-list="uploadForm.fileList"
        style="width: 100%;"
      >
        <el-icon :size="40" color="#C1803A"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF / DOCX / MD / TXT 格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="doUpload" :loading="uploading" :disabled="uploadForm.files.length === 0">上传</el-button>
      </template>
    </el-dialog>

    <!-- 查看内容 -->
    <el-dialog v-model="showContentDialog" :title="'文件内容：' + contentName" width="760px" top="5vh">
      <div v-if="contentLoading" v-loading="contentLoading" style="min-height: 200px;"></div>
      <div v-else-if="!contentText" class="content-unavailable">
        <el-icon :size="36" color="#C4BAB0"><WarningFilled /></el-icon>
        <p>暂不支持预览此文件类型</p>
      </div>
      <pre v-else class="content-preview">{{ contentText }}</pre>
    </el-dialog>

    <!-- 审核 -->
    <el-dialog v-model="showApproveDialog" title="审核文件" width="440px">
      <el-form label-width="60px">
        <el-form-item label="备注">
          <el-input v-model="approveForm.remark" type="textarea" :rows="3" placeholder="审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button type="primary" @click="doApprove">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量审核 -->
    <el-dialog v-model="showBatchApproveDialog" title="批量审核" width="440px">
      <el-form label-width="60px">
        <el-form-item label="备注">
          <el-input v-model="batchApproveForm.remark" type="textarea" :rows="3" placeholder="审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchApproveDialog = false">取消</el-button>
        <el-button type="primary" @click="doBatchApprove">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { knowledgeApi, courseApi } from '@/api';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, UploadFilled, WarningFilled } from '@element-plus/icons-vue';

const auth = useAuthStore();
const userId = computed(() => auth.user?.id);
const isTeacher = computed(() => auth.user?.role === 'TEACHER');
const isAdmin = computed(() => auth.user?.role === 'ADMIN');
const isTeacherOrAdmin = computed(() => isTeacher.value || isAdmin.value);

const knowledgeList = ref([]);
const loading = ref(false);
const searchKeyword = ref('');
const approvalFilter = ref('');

const showUploadDialog = ref(false);
const uploadForm = reactive({ files: [], fileList: [] });
const uploading = ref(false);

const showContentDialog = ref(false);
const contentLoading = ref(false);
const contentText = ref('');
const contentName = ref('');

const showApproveDialog = ref(false);
const approveForm = reactive({ id: null, approved: true, remark: '' });

const showBatchApproveDialog = ref(false);
const batchApproveForm = reactive({ approved: true, remark: '' });
const selectedIds = ref([]);

const courses = ref([]);

onMounted(async () => {
  await loadKnowledge();
  if (isTeacherOrAdmin.value) {
    try { const r = await courseApi.list({ page: 1, size: 100 }); courses.value = r.data?.records || []; } catch {}
  }
});

function canEdit(row) {
  return isTeacherOrAdmin.value && (row.uploadedBy === userId.value || isAdmin.value);
}

function canDelete(row) {
  return isTeacherOrAdmin.value && (row.uploadedBy === userId.value || isAdmin.value);
}

function startEditRemark(row) {
  row._editing = true;
  row._remarkValue = row.remark || '';
}

async function saveRemark(row) {
  row._editing = false;
  const val = (row._remarkValue || '').trim();
  if (val === (row.remark || '')) return;
  try {
    await knowledgeApi.updateRemark(row.id, val);
    row.remark = val;
    ElMessage.success('备注已更新');
  } catch {
    ElMessage.error('更新失败');
  }
}

function fileTypeIcon(type) {
  const map = { pdf: '📄', docx: '📝', md: '📋', txt: '📃' };
  return map[type] || '📁';
}

async function loadKnowledge() {
  loading.value = true;
  try {
    let res;
    if (approvalFilter.value) {
      res = await knowledgeApi.listPending();
    } else if (searchKeyword.value.trim()) {
      res = await knowledgeApi.search(searchKeyword.value.trim());
    } else {
      res = await knowledgeApi.listAll();
    }
    knowledgeList.value = (res.data || []).map(r => ({ ...r, _editing: false, _remarkValue: '' }));
  } catch {} finally { loading.value = false; }
}

async function doSearch() { approvalFilter.value = ''; await loadKnowledge(); }

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

function openUploadDialog() { uploadForm.files = []; uploadForm.fileList = []; showUploadDialog.value = true; }

async function doUpload() {
  if (uploadForm.files.length === 0) { ElMessage.warning('请选择文件'); return; }
  uploading.value = true;
  try {
    const res = await knowledgeApi.uploadBatch(uploadForm.files);
    if (res.code === 200) {
      ElMessage.success('上传成功');
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
  try { const { id, approved, remark } = approveForm; await knowledgeApi.approve(id, approved, remark); showApproveDialog.value = false; await loadKnowledge(); ElMessage.success('已' + (approved ? '通过' : '拒绝')); }
  catch { ElMessage.error('操作失败'); }
}

async function doBatchApprove() {
  try { const { approved, remark } = batchApproveForm; await knowledgeApi.batchApprove(selectedIds.value, approved, remark); showBatchApproveDialog.value = false; selectedIds.value = []; await loadKnowledge(); ElMessage.success('已批量' + (approved ? '通过' : '拒绝')); }
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
.file-name-cell { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.file-icon { font-size: 18px; flex-shrink: 0; }
.text-muted { color: var(--color-text-placeholder); }
.remark-text { cursor: pointer; color: var(--color-text-muted); font-size: 13px; }
.remark-text:hover { color: var(--color-primary); }

.content-unavailable { text-align: center; padding: 48px 20px; color: var(--color-text-muted); }
.content-unavailable p { margin-top: 18px; font-size: 14px; }
.content-preview {
  background: var(--color-bg); padding: 24px; border-radius: var(--radius-md);
  font-size: 14px; line-height: 1.9; white-space: pre-wrap; word-break: break-all;
  max-height: 60vh; overflow-y: auto;
}
</style>
