<template>
  <div class="user-mgmt-page">
    <div class="page-header">
      <div>
        <h3>用户管理</h3>
        <p class="page-desc">管理平台所有用户账户</p>
      </div>
      <el-button text @click="$router.push('/dashboard')" class="back-link">
        <el-icon :size="14"><ArrowLeft /></el-icon>
        <span>返回首页</span>
      </el-button>
    </div>

    <div class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe class="mgmt-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="nickname" label="昵称" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="phone" label="手机" width="140">
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="90">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small" effect="plain" round>
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <div class="status-cell">
              <el-switch :model-value="row.status !== 0" :disabled="row.id === currentUserId" @change="(val) => handleToggleStatus(row, val)" size="small" />
              <span class="status-text" :class="{ disabled: row.status === 0 }">{{ row.status !== 0 ? '正常' : '已禁用' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170">
          <template #default="{ row }">{{ row.lastLoginTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.id !== currentUserId"
              title="确定要删除该用户吗？此操作不可撤销"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" text>删除</el-button>
              </template>
            </el-popconfirm>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchData"
          @size-change="fetchData"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { userApi, authApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowLeft } from '@element-plus/icons-vue';

const loading = ref(false);
const tableData = ref([]);
const page = ref(1);
const size = ref(10);
const total = ref(0);
const currentUserId = ref(null);

function roleType(r) { return { ADMIN: 'danger', TEACHER: 'warning', STUDENT: '' }[r] || 'info'; }
function roleLabel(r) { return { ADMIN: '管理员', TEACHER: '教师', STUDENT: '学生' }[r] || r; }

onMounted(async () => {
  const me = await authApi.me();
  if (me && me.code === 200) currentUserId.value = me.data.id;
  fetchData();
});

async function fetchData() {
  loading.value = true;
  try {
    const res = await userApi.listUsers(page.value, size.value);
    if (res.code === 200) { tableData.value = res.data.records || []; total.value = res.data.total || 0; }
  } catch { ElMessage.error('加载用户列表失败'); } finally { loading.value = false; }
}

async function handleToggleStatus(row, enabled) {
  if (row.id === currentUserId.value) { ElMessage.warning('不能禁用自己的账户'); return; }
  const action = enabled ? '启用' : '禁用';
  try { await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '确认操作', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }); }
  catch { return; }
  try {
    const newStatus = enabled ? 1 : 0;
    const res = await userApi.updateStatus(row.id, newStatus);
    if (res.code === 200) { row.status = newStatus; ElMessage.success(`已${action}`); }
    else { ElMessage.error(res.message || '操作失败'); }
  } catch { ElMessage.error('操作失败'); }
}

async function handleDelete(row) {
  try {
    const res = await userApi.deleteUser(row.id);
    if (res.code === 200) { ElMessage.success(`已删除用户"${row.username}"`); fetchData(); }
    else { ElMessage.error(res.message || '删除失败'); }
  } catch { ElMessage.error('删除失败'); }
}
</script>

<style scoped>
.user-mgmt-page { max-width: 1200px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h3 { font-size: 22px; font-weight: 700; color: var(--color-text); }
.page-desc { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }
.back-link { color: var(--color-text-muted); font-size: 13px; }

.table-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.mgmt-table { border-radius: var(--radius-xl); overflow: hidden; }

.status-cell { display: flex; align-items: center; gap: 8px; }
.status-text { font-size: 12px; color: var(--color-text-secondary); }
.status-text.disabled { color: var(--color-text-placeholder); }
.text-muted { color: var(--color-text-placeholder); font-size: 12px; }

.pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
</style>
