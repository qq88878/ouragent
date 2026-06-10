<template>
  <div class="user-mgmt-page">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>用户管理</span>
          <el-button text @click="$router.push('/dashboard')">← 返回</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag :type="row.role === 'ADMIN' ? 'danger' : row.role === 'TEACHER' ? 'warning' : 'primary'" size="small">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status !== 0"
              :disabled="row.id === currentUserId"
              @change="(val) => handleToggleStatus(row, val)"
            />
            <span style="margin-left: 6px; font-size: 12px; color: #909399;">
              {{ row.status !== 0 ? '正常' : '已禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170">
          <template #default="{ row }">
            {{ row.lastLoginTime || '-' }}
          </template>
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
            <span v-else style="color: #c0c4cc; font-size: 12px;">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; text-align: right;">
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
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { userApi, authApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';

const loading = ref(false);
const tableData = ref([]);
const page = ref(1);
const size = ref(10);
const total = ref(0);
const currentUserId = ref(null);

onMounted(async () => {
  const me = await authApi.me();
  if (me && me.code === 200) {
    currentUserId.value = me.data.id;
  }
  fetchData();
});

async function fetchData() {
  loading.value = true;
  try {
    const res = await userApi.listUsers(page.value, size.value);
    if (res.code === 200) {
      tableData.value = res.data.records || [];
      total.value = res.data.total || 0;
    }
  } catch {
    ElMessage.error('加载用户列表失败');
  } finally {
    loading.value = false;
  }
}

async function handleToggleStatus(row, enabled) {
  if (row.id === currentUserId.value) {
    ElMessage.warning('不能禁用自己的账号');
    return;
  }
  const action = enabled ? '启用' : '禁用';
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch {
    return;
  }
  try {
    const newStatus = enabled ? 1 : 0;
    const res = await userApi.updateStatus(row.id, newStatus);
    if (res.code === 200) {
      row.status = newStatus;
      ElMessage.success(`已${action}`);
    } else {
      ElMessage.error(res.message || '操作失败');
    }
  } catch {
    ElMessage.error('操作失败');
  }
}

async function handleDelete(row) {
  try {
    const res = await userApi.deleteUser(row.id);
    if (res.code === 200) {
      ElMessage.success(`已删除用户 "${row.username}"`);
      fetchData();
    } else {
      ElMessage.error(res.message || '删除失败');
    }
  } catch {
    ElMessage.error('删除失败');
  }
}
</script>