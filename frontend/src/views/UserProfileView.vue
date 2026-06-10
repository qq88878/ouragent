<template>
  <div class="profile-page">
    <el-card style="max-width: 520px; margin: 0 auto;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>个人资料</span>
          <el-button text @click="$router.push('/dashboard')">← 返回</el-button>
        </div>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        v-loading="loading"
      >
        <el-form-item label="用户名">
          <el-input :model-value="form.username" disabled />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="手机" prop="phone">
          <el-input v-model="form.phone" maxlength="11" />
        </el-form-item>
        <el-form-item label="头像" prop="avatar">
          <el-input v-model="form.avatar" placeholder="头像URL" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { userApi } from '@/api';
import { ElMessage } from 'element-plus';

const formRef = ref(null);
const loading = ref(false);
const saving = ref(false);
const original = reactive({});

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  avatar: '',
});

const rules = {
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  phone: [
    { pattern: /^1\d{0,10}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
};

onMounted(async () => {
  loading.value = true;
  try {
    const res = await userApi.getProfile();
    if (res.code === 200) {
      Object.assign(form, {
        username: res.data.username,
        nickname: res.data.nickname || '',
        email: res.data.email || '',
        phone: res.data.phone || '',
        avatar: res.data.avatar || '',
      });
      Object.assign(original, { ...form });
    }
  } catch {
    ElMessage.error('加载用户信息失败');
  } finally {
    loading.value = false;
  }
});

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  saving.value = true;
  try {
    const payload = {};
    if (form.nickname !== original.nickname) payload.nickname = form.nickname;
    if (form.email !== original.email) payload.email = form.email;
    if (form.phone !== original.phone) payload.phone = form.phone;
    if (form.avatar !== original.avatar) payload.avatar = form.avatar;
    if (Object.keys(payload).length === 0) {
      ElMessage.info('没有变更');
      return;
    }
    const res = await userApi.updateProfile(payload);
    if (res.code === 200) {
      ElMessage.success('保存成功');
      Object.assign(original, { ...form });
    } else {
      ElMessage.error(res.message || '保存失败');
    }
  } catch {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

function handleReset() {
  Object.assign(form, { ...original });
}
</script>