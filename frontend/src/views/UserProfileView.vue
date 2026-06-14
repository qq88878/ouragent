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
        <!-- Student profile card -->
        <el-card v-if="isStudent" class="extra-card">
          <template #header>能力画像</template>
          <el-form :model="profile" label-width="80px" label-position="top">
            <el-form-item label="学习风格">
              <el-select v-model="profile.learningStyle" style="width:100%">
                <el-option label="视觉型" value="VISUAL" />
                <el-option label="听觉型" value="AUDITORY" />
                <el-option label="读写型" value="READING" />
                <el-option label="动手型" value="KINESTHETIC" />
              </el-select>
            </el-form-item>
            <el-form-item label="优势领域">
              <el-input v-model="profile.strengths" placeholder="如：逻辑推理、数学" />
            </el-form-item>
            <el-form-item label="薄弱环节">
              <el-input v-model="profile.weaknesses" placeholder="如：英语阅读、记忆" />
            </el-form-item>
            <el-form-item label="兴趣方向">
              <el-input v-model="profile.interests" placeholder="如：编程、AI" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存画像</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Email verify card -->
        <el-card v-if="!emailVerified" class="extra-card" style="margin-top:20px;">
          <template #header>邮箱验证</template>
          <div style="display:flex;gap:8px;">
            <el-input v-model="code" placeholder="6位验证码" maxlength="6" />
            <el-button @click="sendCode" :loading="sendingCode">发送</el-button>
          </div>
          <el-button type="primary" style="margin-top:12px;width:100%;" :loading="verifying" @click="verifyEmail">验证邮箱</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { userApi, learningApi, authApi } from '@/api';
import { ElMessage } from 'element-plus';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const emailVerified = computed(() => user.value?.emailVerified===1||authStore.emailVerified);
const isStudent = computed(() => user.value?.role==='STUDENT');
const saving = ref(false); const form = ref({ nickname:'', email:'', phone:'' });
const profile = ref({ learningStyle:'VISUAL', strengths:'', weaknesses:'', interests:'', gradeLevel:'BEGINNER' });
const savingProfile = ref(false);
const code = ref(''); const sendingCode = ref(false); const verifying = ref(false);

onMounted(async () => {
  await authStore.fetchUser();
  form.value = { nickname:user.value?.nickname||'', email:user.value?.email||'', phone:user.value?.phone||'' };
  if (isStudent.value) { try { const r=await learningApi.getProfile(); if(r.code===200){ const d=r.data; profile.value={learningStyle:d.learningStyle||'VISUAL',strengths:d.strengths||'',weaknesses:d.weaknesses||'',interests:d.interests||'',gradeLevel:d.gradeLevel||'BEGINNER'}; } } catch{} }
});

async function save() { saving.value=true; try { const r=await userApi.updateProfile({...form.value}); if(r.code===200){ ElMessage.success('保存成功'); authStore.fetchUser(); } } catch{ ElMessage.error('保存失败'); } finally {saving.value=false;} }
async function saveProfile() { savingProfile.value=true; try { await learningApi.updateProfile({...profile.value}); ElMessage.success('画像已保存'); } catch{ ElMessage.error('保存失败'); } finally {savingProfile.value=false;} }
async function sendCode() { sendingCode.value=true; try { await authApi.sendVerifyCode(user.value.email); ElMessage.success('验证码已发送'); } catch{ElMessage.error('发送失败');} finally {sendingCode.value=false;} }
async function verifyEmail() { if(!code.value) return; verifying.value=true; try { await authApi.verifyEmail(user.value.email,code.value); ElMessage.success('验证成功'); user.value.emailVerified=1; } catch{ElMessage.error('验证失败');} finally {verifying.value=false;} }
function formatTime(t) { if(!t) return ''; return new Date(t).toLocaleString('zh-CN'); }
</script>

<style scoped>
.profile-page { max-width: 800px; }
.extra-card { margin-bottom: 0; }
</style>
