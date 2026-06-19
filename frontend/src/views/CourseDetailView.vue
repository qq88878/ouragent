<template>
  <div class="course-detail-page">
    <div class="back-nav">
      <el-button text @click="$router.push('/courses')" class="back-btn">
        <el-icon :size="16"><ArrowLeft /></el-icon>
        <span>返回课程中心</span>
      </el-button>
    </div>

    <div v-if="course" v-loading="loading">
      <!-- 课程信息 -->
      <div class="info-card">
        <div class="info-cover" :style="{ background: 'linear-gradient(135deg, #5B6AF0, #A78BFA)' }">
          <div class="info-tags">
            <el-tag :type="difficultyType" effect="dark">{{ difficultyText }}</el-tag>
            <el-tag :type="course.status === 1 ? 'success' : 'info'" effect="dark">{{ course.status === 1 ? '已发布' : '草稿' }}</el-tag>
          </div>
        </div>
        <div class="info-body">
          <div class="info-category">{{ course.category || '未分类' }}</div>
          <h2>{{ course.title }}</h2>
          <p class="info-desc">{{ course.description || '暂无描述' }}</p>
          <div class="info-meta">
            <div class="meta-item">
              <el-icon :size="16"><UserFilled /></el-icon>
              <span>授课教师：{{ course.teacherName || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 辅助资料 -->
      <div class="files-section">
        <div class="section-header">
          <h3>辅助资料</h3>
          <el-tag size="small" round effect="plain">{{ knowledgeList.length }} 个文件</el-tag>
        </div>
        <el-table :data="knowledgeList" v-loading="kbLoading" stripe empty-text="暂无辅助资料" class="files-table">
          <el-table-column prop="name" label="文件名" min-width="200">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon :size="16" color="#5B6AF0"><Document /></el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="fileType" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" effect="plain" round>{{ row.fileType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.fileSize || row.size) }}</template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="{ row }">{{ new Date(row.createTime).toLocaleString('zh-CN') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="viewContent(row.id)">查看内容</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="课程不存在" :image-size="100" />

    <!-- 内容预览弹窗 -->
    <el-dialog v-model="showContentDialog" :title="'查看内容: ' + contentName" width="800px" top="3vh">
      <div v-loading="contentLoading" style="max-height: 70vh; overflow-y: auto;">
        <template v-if="!contentLoading && contentText">
          <div v-if="isPreviewPlaceholder" class="content-unavailable">
            <el-icon :size="48" color="#C9CDD4"><WarningFilled /></el-icon>
            <p>{{ contentText }}</p>
          </div>
          <pre v-else class="content-preview">{{ contentText }}</pre>
        </template>
        <el-empty v-if="!contentLoading && !contentText" description="无法加载内容" :image-size="60" />
      </div>
      <template #footer>
        <el-button @click="showContentDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { courseApi, knowledgeApi } from '@/api';
import { ArrowLeft, UserFilled, Document, WarningFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const route = useRoute();
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
  try { const res = await courseApi.getById(id); if (res.code === 200) course.value = res.data; } catch {} finally { loading.value = false; }
  kbLoading.value = true;
  try { const res = await knowledgeApi.list(id); if (res.code === 200) knowledgeList.value = res.data || []; } catch {} finally { kbLoading.value = false; }
});

async function viewContent(id) {
  contentLoading.value = true; contentText.value = ''; contentName.value = ''; showContentDialog.value = true;
  try { const res = await knowledgeApi.getContent(id); if (res.code === 200) { contentText.value = res.data.content || ''; contentName.value = res.data.name || ''; } }
  catch { ElMessage.error('加载内容失败'); } finally { contentLoading.value = false; }
}

function formatSize(bytes) { if (!bytes) return '-'; if (bytes < 1024) return bytes + ' B'; if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'; return (bytes / 1024 / 1024).toFixed(1) + ' MB'; }
</script>

<style scoped>
.course-detail-page { max-width: 900px; }

.back-nav { margin-bottom: 20px; }
.back-btn { color: var(--color-text-muted); font-size: 13px; }
.back-btn:hover { color: var(--color-primary); }

.info-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  margin-bottom: 24px;
}
.info-cover { height: 100px; display: flex; align-items: flex-start; justify-content: flex-end; padding: 16px; }
.info-tags { display: flex; gap: 8px; }
.info-body { padding: 20px 28px 28px; }
.info-category { font-size: 11px; color: var(--color-primary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.info-body h2 { font-size: 24px; font-weight: 700; color: var(--color-text); margin-bottom: 12px; }
.info-desc { font-size: 14px; color: var(--color-text-secondary); line-height: 1.8; margin-bottom: 16px; }
.info-meta { display: flex; gap: 24px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--color-text-muted); }

.files-section { margin-top: 8px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-header h3 { font-size: 17px; font-weight: 700; color: var(--color-text); }
.files-table { border-radius: var(--radius-lg); overflow: hidden; }
.file-name-cell { display: flex; align-items: center; gap: 8px; font-size: 13px; }

.content-unavailable { text-align: center; padding: 40px 20px; color: var(--color-text-muted); }
.content-unavailable p { margin-top: 16px; font-size: 14px; }
.content-preview { background: var(--color-bg); padding: 20px; border-radius: var(--radius-md); font-size: 13px; line-height: 1.8; white-space: pre-wrap; word-break: break-all; max-height: 60vh; overflow-y: auto; }
</style>
