<template>
  <div class="course-detail-page">
    <div class="page-header">
      <el-button text @click="$router.push('/courses')">
        <el-icon><ArrowLeft /></el-icon> 返回课程中心
      </el-button>
    </div>

    <div v-if="course" v-loading="loading">
      <!-- Course Info -->
      <el-card class="info-card" shadow="hover">
        <h2>{{ course.title }}</h2>
        <p class="desc">{{ course.description || '暂无描述' }}</p>
        <div class="meta">
          <el-tag>{{ course.category || '未分类' }}</el-tag>
          <el-tag :type="difficultyType">{{ difficultyText }}</el-tag>
          <el-tag :type="course.status === 1 ? 'success' : 'info'">{{ course.status === 1 ? '已发布' : '草稿' }}</el-tag>
        </div>
        <div class="teacher">授课教师：{{ course.teacherName || '-' }}</div>
      </el-card>

      <!-- Knowledge Base Files -->
      <el-card class="files-card" shadow="hover" style="margin-top: 20px;">
        <template #header>
          <span>辅助资料（{{ knowledgeList.length }}）</span>
        </template>
        <el-table :data="knowledgeList" v-loading="kbLoading" stripe empty-text="暂无辅助资料">
          <el-table-column prop="name" label="文件名" min-width="200" />
          <el-table-column prop="fileType" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ row.fileType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.fileSize || row.size) }}</template>
          </el-table-column>
          <el-table-column label="上传时间" width="170">
            <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="viewContent(row.id)">查看内容</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-empty v-else-if="!loading" description="课程不存在" />

    <!-- Content Preview Dialog -->
    <el-dialog v-model="showContentDialog" :title="'查看内容: ' + contentName" width="800px" top="3vh">
      <div v-loading="contentLoading" style="max-height: 70vh; overflow-y: auto;">
        <template v-if="!contentLoading && contentText">
          <div v-if="isPreviewPlaceholder" class="content-unavailable">
            <el-icon :size="48" color="#909399"><WarningFilled /></el-icon>
            <p>{{ contentText }}</p>
          </div>
          <pre v-else class="content-preview">{{ contentText }}</pre>
        </template>
        <el-empty v-if="!contentLoading && !contentText" description="无法加载内容" />
      </div>
      <template #footer>
        <el-button @click="showContentDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { courseApi, knowledgeApi } from '@/api';
import { ArrowLeft } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const course = ref(null);
const knowledgeList = ref([]);
const loading = ref(true);
const kbLoading = ref(false);
const showContentDialog = ref(false);
const contentText = ref('');
const contentName = ref('');
const contentLoading = ref(false);
const isPreviewPlaceholder = computed(() => contentText.value && contentText.value.startsWith('[此文件类型'));

const difficultyText = computed(() => {
  const d = course.value?.difficulty;
  return { BEGINNER: '入门', INTERMEDIATE: '中级', ADVANCED: '高级' }[d] || d || '-';
});
const difficultyType = computed(() => {
  const d = course.value?.difficulty;
  return { BEGINNER: 'success', INTERMEDIATE: 'warning', ADVANCED: 'danger' }[d] || 'info';
});

onMounted(async () => {
  const id = route.params.id;
  if (!id) return;
  try {
    const res = await courseApi.getById(id);
    if (res.code === 200) course.value = res.data;
  } catch { /* ignore */ }
  finally { loading.value = false; }

  kbLoading.value = true;
  try {
    const res = await knowledgeApi.list(id);
    if (res.code === 200) knowledgeList.value = res.data || [];
  } catch { /* ignore */ }
  finally { kbLoading.value = false; }
});

async function viewContent(id) {
  contentLoading.value = true;
  contentText.value = '';
  contentName.value = '';
  showContentDialog.value = true;
  try {
    const res = await knowledgeApi.getContent(id);
    if (res.code === 200) {
      contentText.value = res.data.content || '';
      contentName.value = res.data.name || '';
    }
  } catch {
    ElMessage.error('加载内容失败');
  } finally {
    contentLoading.value = false;
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
.course-detail-page { max-width: 900px; }
.page-header { margin-bottom: 16px; }
.info-card h2 { margin: 0 0 12px 0; font-size: 22px; color: #303133; }
.info-card .desc { color: #606266; font-size: 14px; line-height: 1.8; margin-bottom: 12px; }
.info-card .meta { display: flex; gap: 8px; margin-bottom: 8px; }
.info-card .teacher { font-size: 13px; color: #909399; }
.files-card :deep(.el-card__header) { font-weight: 600; }
.content-unavailable { text-align: center; padding: 40px 20px; color: #909399; }
.content-unavailable p { margin-top: 16px; font-size: 14px; }
.content-preview {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 60vh;
  overflow-y: auto;
}
</style>
