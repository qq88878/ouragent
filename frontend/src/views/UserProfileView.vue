<template>
  <div class="profile-page">
    <div class="page-header">
      <div>
        <h3>个人资料</h3>
        <p class="page-desc">管理您的账户信息和邮箱验证</p>
      </div>
    </div>

    <el-row :gutter="24">
      <el-col :span="16">
        <div class="profile-card">
          <div class="profile-cover">
            <div class="profile-avatar">{{ (user?.nickname || user?.username || '?')[0] }}</div>
            <div class="profile-name">{{ user?.nickname || user?.username }}</div>
            <el-tag :type="roleTagType" size="small" effect="dark" round>{{ roleLabel }}</el-tag>
          </div>
          <div class="profile-form">
            <el-form :model="form" label-width="80px" label-position="left">
              <el-form-item label="用户名">
                <el-input :model-value="user?.username" disabled />
              </el-form-item>
              <el-form-item label="昵称">
                <el-input v-model="form.nickname" placeholder="给自己起个名字" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="邮箱">
                  <template #append>
                    <el-tag v-if="!emailVerified" type="warning" size="small">未验证</el-tag>
                    <el-tag v-else type="success" size="small">已验证</el-tag>
                  </template>
                </el-input>
              </el-form-item>
              <el-form-item label="手机">
                <el-input v-model="form.phone" placeholder="手机号" />
              </el-form-item>
              <el-form-item label="注册时间">
                <span class="info-text">{{ formatTime(user?.createTime) }}</span>
              </el-form-item>
              <el-form-item label="上次登录">
                <span class="info-text">{{ formatTime(user?.lastLoginTime) || '首次登录' }}</span>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saving" @click="save" size="large">保存修改</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>

      <el-col :span="8">
        <div v-if="!emailVerified" class="verify-card">
          <div class="verify-icon">
            <el-icon :size="28" color="#FF9500"><Message /></el-icon>
          </div>
          <h4>邮箱验证</h4>
          <p>验证邮箱以解锁全部功能</p>
          <div class="verify-input">
            <el-input v-model="code" placeholder="6位验证码" maxlength="6" size="large" />
          </div>
          <div class="verify-actions">
            <el-button :loading="sendingCode" @click="sendCode" size="default" plain>发送验证码</el-button>
            <el-button type="primary" :loading="verifying" @click="verifyEmail" size="default">验证邮箱</el-button>
          </div>
        </div>
        <div v-else class="verify-card verified">
          <div class="verify-icon">
            <el-icon :size="28" color="#34C759"><CircleCheckFilled /></el-icon>
          </div>
          <h4>邮箱已验证</h4>
          <p>您的账户已完全激活</p>
        </div>
      </el-col>
    </el-row>

    <StudentQuestionnaire v-if="isStudent" class="questionnaire-section" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import StudentQuestionnaire from '@/components/StudentQuestionnaire.vue';
import { userApi, authApi } from '@/api';
import { ElMessage } from 'element-plus';
import { Message, CircleCheckFilled } from '@element-plus/icons-vue';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const emailVerified = computed(() => user.value?.emailVerified === 1 || authStore.emailVerified);
const isStudent = computed(() => user.value?.role === 'STUDENT');

const roleLabel = computed(() => {
  switch (user.value?.role) { case 'ADMIN': return '管理员'; case 'TEACHER': return '教师'; case 'STUDENT': return '学生'; default: return ''; }
});
const roleTagType = computed(() => {
  switch (user.value?.role) { case 'ADMIN': return 'danger'; case 'TEACHER': return 'warning'; case 'STUDENT': return 'success'; default: return 'info'; }
});

const saving = ref(false);
const form = ref({ nickname: '', email: '', phone: '' });
const code = ref('');
const sendingCode = ref(false);
const verifying = ref(false);

onMounted(async () => {
  await authStore.fetchUser();
  form.value = { nickname: user.value?.nickname || '', email: user.value?.email || '', phone: user.value?.phone || '' };
});

async function save() {
  saving.value = true;
  try { const r = await userApi.updateProfile({ ...form.value }); if (r.code === 200) { ElMessage.success('保存成功'); authStore.fetchUser(); } }
  catch { ElMessage.error('保存失败'); } finally { saving.value = false; }
}

async function sendCode() { sendingCode.value = true; try { await authApi.sendVerifyCode(user.value.email); ElMessage.success('验证码已发送'); } catch { ElMessage.error('发送失败'); } finally { sendingCode.value = false; } }

async function verifyEmail() { if (!code.value) return; verifying.value = true; try { await authApi.verifyEmail(user.value.email, code.value); ElMessage.success('验证成功'); user.value.emailVerified = 1; } catch { ElMessage.error('验证失败'); } finally { verifying.value = false; } }

function formatTime(t) { if (!t) return ''; return new Date(t).toLocaleString('zh-CN'); }
</script>

<style scoped>
.profile-page { max-width: 900px; }

.page-header { margin-bottom: 24px; }
.page-header h3 { font-size: 22px; font-weight: 700; color: var(--color-text); }
.page-desc { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }

.profile-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  margin-bottom: 24px;
}
.profile-cover {
  background: linear-gradient(135deg, #5B6AF0 0%, #7C5CFC 100%);
  padding: 28px 32px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.profile-avatar {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.2);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}
.profile-name { font-size: 18px; font-weight: 700; color: #fff; flex: 1; }
.profile-form { padding: 28px 32px; }

.info-text { color: var(--color-text-muted); font-size: 13px; }

.verify-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  padding: 28px 24px;
  text-align: center;
  box-shadow: var(--shadow-card);
  border: 1px solid #FFE8C0;
}
.verify-card.verified { border-color: #D4F5E0; }
.verify-icon { margin-bottom: 12px; }
.verify-card h4 { font-size: 16px; font-weight: 700; color: var(--color-text); margin-bottom: 4px; }
.verify-card p { font-size: 12px; color: var(--color-text-muted); margin-bottom: 16px; }
.verify-input { margin-bottom: 12px; }
.verify-actions { display: flex; gap: 8px; justify-content: center; }

.questionnaire-section { margin-top: 32px; }
</style>
