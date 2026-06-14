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
          <span>辅导资料（{{ knowledgeList.length }}）</span>
        </template>
        <el-table :data="knowledgeList" v-loading="kbLoading" stripe empty-text="暂无辅导资料">
          <el-table-column prop="name" label="文件名" min-width="200" />
          <el-table-column prop="fileType" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ row.fileType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="上传时间" width="170">
            <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-empty v-else-if="!loading" description="课程不存在" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { courseApi, knowledgeApi } from '@/api';
import { ArrowLeft } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const course = ref(null);
const knowledgeList = ref([]);
const loading = ref(true);
const kbLoading = ref(false);

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
</style>