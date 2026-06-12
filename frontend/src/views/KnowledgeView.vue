<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="showUploadDialog = true">上传文件</el-button>
    </div>

    <div style="margin-bottom: 16px;">
      <el-select v-model="selectedCourseId" placeholder="选择课程筛选" clearable @change="loadKnowledge">
        <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
      </el-select>
    </div>

    <el-table :data="knowledgeList" v-loading="loading" stripe>
      <el-table-column prop="name" label="文件名" min-width="200" />
      <el-table-column prop="fileType" label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small">{{ row.fileType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="上传时间" width="170">
        <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="reprocess(row.id)">重新处理</el-button>
          <el-button text type="danger" size="small" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showUploadDialog" title="上传知识库文件" width="500px">
      <el-form label-width="80px">
        <el-form-item label="课程" required>
          <el-select v-model="uploadForm.courseId" placeholder="选择课程" style="width: 100%;">
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
import { ref, onMounted } from 'vue';
import { knowledgeApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';

const knowledgeList = ref([]);
const courses = ref([]);
const loading = ref(false);
const uploading = ref(false);
const showUploadDialog = ref(false);
const selectedCourseId = ref(null);
const uploadForm = ref({ courseId: null, file: null, name: '' });

onMounted(async () => {
  await loadCourses();
  await loadKnowledge();
});

async function loadCourses() {
  try {
    const res = await courseApi.list({ page: 1, size: 100 });
    if (res.code === 200) courses.value = res.data?.records || [];
  } catch { /* ignore */ }
}

async function loadKnowledge() {
  if (!selectedCourseId.value) {
    knowledgeList.value = [];
    return;
  }
  loading.value = true;
  try {
    const res = await knowledgeApi.list(selectedCourseId.value);
    if (res.code === 200) knowledgeList.value = res.data || [];
  } catch { /* ignore */ }
  finally { loading.value = false; }
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw;
}

async function doUpload() {
  if (!uploadForm.value.courseId) { ElMessage.warning('请选择课程'); return; }
  if (!uploadForm.value.file) { ElMessage.warning('请选择文件'); return; }
  uploading.value = true;
  try {
    const res = await knowledgeApi.upload(
      uploadForm.value.file,
      uploadForm.value.courseId,
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

async function reprocess(id) {
  try {
    await knowledgeApi.reprocess(id);
    ElMessage.success('已触发重新处理');
    await loadKnowledge();
  } catch {
    ElMessage.error('操作失败');
  }
}

async function remove(id) {
  try {
    await ElMessageBox.confirm('确定删除此知识库文件？', '提示', { type: 'warning' });
    await knowledgeApi.delete(id);
    await loadKnowledge();
    ElMessage.success('已删除');
  } catch { /* cancel */ }
}

function formatSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
function statusText(s) { return ['待处理', '已索引', '处理失败'][s] || '未知'; }
function statusType(s) { return ['warning', 'success', 'danger'][s] || 'info'; }
</script>

<style scoped>
.knowledge-page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
