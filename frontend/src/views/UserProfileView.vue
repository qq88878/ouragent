<template>
  <div class="profile-page">
    <h3 style="margin-bottom:20px;">个人资料</h3>
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <el-form :model="form" label-width="100px">
            <el-form-item label="用户名">
              <el-input :model-value="user?.username" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" placeholder="给自己起个名字" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="邮箱" />
              <template v-if="!emailVerified"><el-tag type="warning" size="small" style="margin-left:8px;">未验证</el-tag></template>
              <template v-else><el-tag type="success" size="small" style="margin-left:8px;">已验证</el-tag></template>
            </el-form-item>
            <el-form-item label="手机">
              <el-input v-model="form.phone" placeholder="手机号" />
            </el-form-item>
            <el-form-item label="注册时间">
              <span style="color:#909399;">{{ formatTime(user?.createTime) }}</span>
            </el-form-item>
            <el-form-item label="上次登录">
              <span style="color:#909399;">{{ formatTime(user?.lastLoginTime) || '首次登录' }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="save">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card v-if="!emailVerified" class="extra-card">
          <template #header>邮箱验证</template>
          <div style="display:flex;gap:8px;">
            <el-input v-model="code" placeholder="6位验证码" maxlength="6" />
            <el-button @click="sendCode" :loading="sendingCode">发送</el-button>
          </div>
          <el-button type="primary" style="margin-top:12px;width:100%;" :loading="verifying" @click="verifyEmail">验证邮箱</el-button>
        </el-card>
      </el-col>
    </el-row>
    <!-- 学习画像问卷 -->
    <StudentQuestionnaire v-if="isStudent" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import StudentQuestionnaire from '@/components/StudentQuestionnaire.vue';
import { userApi, authApi } from '@/api';
import { ElMessage } from 'element-plus';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const emailVerified = computed(() => user.value?.emailVerified===1||authStore.emailVerified);
const isStudent = computed(() => user.value?.role==='STUDENT');
const saving = ref(false);
const form = ref({ nickname:'', email:'', phone:'' });
const code = ref('');
const sendingCode = ref(false);
const verifying = ref(false);

onMounted(async () => {
  await authStore.fetchUser();
  form.value = { nickname:user.value?.nickname||'', email:user.value?.email||'', phone:user.value?.phone||'' };
});

async function save() {
  saving.value = true;
  try {
    const r = await userApi.updateProfile({...form.value});
    if (r.code === 200) { ElMessage.success('保存成功'); authStore.fetchUser(); }
  } catch {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

async function sendCode() {
  sendingCode.value = true;
  try {
    await authApi.sendVerifyCode(user.value.email);
    ElMessage.success('验证码已发送');
  } catch {
    ElMessage.error('发送失败');
  } finally {
    sendingCode.value = false;
  }
}

async function verifyEmail() {
  if (!code.value) return;
  verifying.value = true;
  try {
    await authApi.verifyEmail(user.value.email, code.value);
    ElMessage.success('验证成功');
    user.value.emailVerified = 1;
  } catch {
    ElMessage.error('验证失败');
  } finally {
    verifying.value = false;
  }
}

function formatTime(t) {
  if (!t) return '';
  return new Date(t).toLocaleString('zh-CN');
}
</script>

<style scoped>
.profile-page { max-width: 800px; }
.extra-card { margin-bottom: 0; }
</style>