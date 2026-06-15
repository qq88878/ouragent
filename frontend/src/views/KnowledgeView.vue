<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h3>知识库管理</h3>
      <div>
        <el-radio-group v-if="isAdmin" v-model="approvalFilter" @change="loadKnowledge" style="margin-right: 16px;">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="PENDING">待审核</el-radio-button>
          <el-radio-button value="APPROVED">已通过</el-radio-button>
          <el-radio-button value="REJECTED">已拒绝</el-radio-button>
        </el-radio-group>
        <el-button v-if="isTeacherOrAdmin" type="primary" @click="openUploadDialog">上传文件</el-button>
      </div>
    </div>

    <el-table :data="knowledgeList" v-loading="loading" stripe>
      <template #empty>
        <el-empty v-if="!loading" description="暂无知识库文件" />
      </template>
      <el-table-column prop="name" label="文件名" min-width="200" />
      <el-table-column v-if="isAdmin" label="上传者" width="120">
        <template #default="{ row }">{{ row.uploadedByName || '-' }}</template>
      </el-table-column>
      <el-table-column label="所属课程" width="160">
        <template #default="{ row }">{{ row.courseName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="fileType" label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small">{{ row.fileType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="审核状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getApprovalTagType(row.approvalStatus)" size="small">
            {{ getApprovalLabel(row.approvalStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="上传时间" width="170">
        <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column v-if="isTeacherOrAdmin" label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="isAdmin && row.approvalStatus === 'PENDING'">
            <el-button text type="success" size="small" @click="approve(row.id, true)">通过</el-button>
            <el-button text type="warning" size="small" @click="approve(row.id, false)">拒绝</el-button>
          </template>
          <el-button text type="danger" size="small" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-if="isTeacherOrAdmin" v-model="showUploadDialog" title="上传知识库文件" width="500px">
      <el-form label-width="80px">
        <el-form-item label="课程">
          <el-select v-model="uploadForm.courseId" placeholder="可不选，上传到公共库" clearable style="width: 100%;">
            <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="() => uploadForm.file = null"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / DOCX / MD / TXT，最大 50MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="uploadForm.name" placeholder="留空则使用文件名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="doUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { knowledgeApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';

const knowledgeList = ref([]);
const courses = ref([]);
const loading = ref(false);
const uploading = ref(false);
const showUploadDialog = ref(false);
const approvalFilter = ref('');
const uploadForm = ref({ courseId: null, file: null, name: '' });
const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.role === 'ADMIN');
const isTeacherOrAdmin = computed(() => {
  const role = authStore.user?.role;
  return role === 'TEACHER' || role === 'ADMIN';
});

onMounted(async () => {
  await loadCourses();
  await loadKnowledge();
});

async function loadCourses() {
  try {
    const res = await courseApi.list({ page: 1, size: 100 });
    if (res.code === 200) {
      courses.value = res.data?.records || [];
    }
  } catch { /* ignore */ }
}

async function loadKnowledge() {
  loading.value = true;
  try {
    let res;
    if (isAdmin.value && approvalFilter.value) {
      res = await knowledgeApi.listPending();
      // Filter by approval status since listPending only returns PENDING
      if (res.code === 200) {
        knowledgeList.value = (res.data || []).filter(item => item.approvalStatus === approvalFilter.value);
      }
    } else {
      res = await knowledgeApi.listAll();
      if (res.code === 200) knowledgeList.value = res.data || [];
    }
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw;
}

function openUploadDialog() {
  uploadForm.value.courseId = null;
  uploadForm.value.file = null;
  uploadForm.value.name = '';
  showUploadDialog.value = true;
}

async function doUpload() {
  if (!uploadForm.value.file) { ElMessage.warning('请选择文件'); return; }
  uploading.value = true;
  try {
    const res = await knowledgeApi.upload(
      uploadForm.value.file,
      uploadForm.value.courseId || null,
      uploadForm.value.name,
    );
    if (res.code === 200) {
      ElMessage.success('上传成功');
      showUploadDialog.value = false;
      uploadForm.value = { courseId: null, file: null, name: '' };
      await loadKnowledge();
    }
  } catch {
    ElMessage.error('上传失败');
  } finally { uploading.value = false; }
}

async function remove(id) {
  try {
    await ElMessageBox.confirm('确定删除此知识库文件？', '提示', { type: 'warning' });
    await knowledgeApi.delete(id);
    await loadKnowledge();
    ElMessage.success('已删除');
  } catch { /* cancel */ }
}

async function approve(id, approved) {
  try {
    const action = approved ? '通过' : '拒绝';
    await ElMessageBox.confirm(`确定${action}此知识库文件？`, '提示', { type: 'warning' });
    await knowledgeApi.approve(id, approved);
    await loadKnowledge();
    ElMessage.success(`已${action}`);
  } catch { /* cancel */ }
}

function getApprovalTagType(status) {
  switch (status) {
    case 'APPROVED': return 'success';
    case 'REJECTED': return 'danger';
    case 'PENDING': return 'warning';
    default: return 'info';
  }
}

function getApprovalLabel(status) {
  switch (status) {
    case 'APPROVED': return '已通过';
    case 'REJECTED': return '已拒绝';
    case 'PENDING': return '待审核';
    default: return status;
  }
}

function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
</script>

<style scoped>
.knowledge-page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
