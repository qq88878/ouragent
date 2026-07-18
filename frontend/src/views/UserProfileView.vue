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
            <el-icon :size="28" color="#C1803A"><Message /></el-icon>
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
            <el-icon :size="28" color="#5B8C5A"><CircleCheckFilled /></el-icon>
          </div>
          <h4>邮箱已验证</h4>
          <p>您的账户已完全激活</p>
        </div>
      </el-col>
    </el-row>

    <!-- Profile History -->
    <ProfileHistoryPanel v-if="isStudent" class="questionnaire-section" />
    <StudentQuestionnaire v-if="isStudent" class="questionnaire-section" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import StudentQuestionnaire from '@/components/StudentQuestionnaire.vue';
import ProfileHistoryPanel from '@/components/ProfileHistoryPanel.vue';
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
.profile-page { max-width: 920px; margin: 0 auto; }

.page-header { margin-bottom: 28px; }
.page-header h3 { font-size: 24px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.page-desc { font-size: 14px; color: var(--color-text-muted); margin-top: 4px; }

.profile-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  overflow: hidden; box-shadow: var(--shadow-card); margin-bottom: 24px;
}
.profile-cover {
  background: linear-gradient(135deg, #8B5E3C 0%, #C1783A 100%);
  padding: 32px 36px; display: flex; align-items: center; gap: 16px;
}
.profile-avatar {
  width: 60px; height: 60px; border-radius: 16px;
  background: rgba(255,255,255,0.18); color: #fff;
  font-size: 26px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(10px);
}
.profile-name { font-size: 20px; font-weight: 700; color: #fff; flex: 1; letter-spacing: -0.01em; }
.profile-form { padding: 28px 36px; }
.profile-form :deep(.el-form-item__label) { font-weight: 600; color: var(--color-text-secondary); }

.info-text { color: var(--color-text-muted); font-size: 14px; }

.verify-card {
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  padding: 32px 28px; text-align: center;
  box-shadow: var(--shadow-card); border: 1px solid #F0D4B0;
}
.verify-card.verified { border-color: #D4ECD4; }
.verify-icon { margin-bottom: 14px; }
.verify-card h4 { font-size: 18px; font-weight: 700; color: var(--color-text); margin-bottom: 6px; }
.verify-card p { font-size: 13px; color: var(--color-text-muted); margin-bottom: 20px; }
.verify-input { margin-bottom: 14px; }
.verify-actions { display: flex; gap: 10px; justify-content: center; }

.questionnaire-section { margin-top: 36px; }
</style>