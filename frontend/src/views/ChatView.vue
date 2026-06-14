<template>
  <div class="chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" style="width:100%" @click="createSession">+ 新建对话</el-button>
      </div>
      <div class="session-list">
        <div v-for="s in sessions" :key="s.id" class="session-item" :class="{active: s.id===currentSessionId}" @click="selectSession(s.id)">
          <div class="session-title">{{ s.title || '新对话' }}</div>
          <div class="session-time">{{ formatTime(s.lastMessageTime || s.createTime) }}</div>
          <div class="session-preview">{{ truncate(s.lastMessage, 30) }}</div>
          <el-button class="delete-btn" text size="small" @click.stop="deleteSession(s.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-empty v-if="sessions.length===0" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <div class="chat-main">
      <template v-if="currentSessionId">
        <div v-if="courseContext" class="course-bar">
          <el-icon><Reading /></el-icon>
          <span>{{ courseContext }}</span>
        </div>
        <div class="messages-area" ref="msgArea">
          <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.role.toLowerCase()">
            <div class="message-avatar">
              <el-avatar :size="32" :icon="msg.role==='USER' ? UserFilled : Service" />
            </div>
            <div class="message-bubble">
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="sending" class="message-row assistant">
            <div class="message-avatar"><el-avatar :size="32" :icon="Service" /></div>
            <div class="message-bubble"><div class="message-content typing">正在思考...</div></div>
          </div>
        </div>
        <div class="input-area">
          <el-input v-model="inputMessage" type="textarea" :rows="2" placeholder="输入消息，Enter 发送，Shift+Enter 换行" @keydown="handleKeydown" :disabled="sending" />
          <el-button type="primary" :disabled="!inputMessage.trim()||sending" @click="sendMessage">发送</el-button>
        </div>
      </template>
      <div v-else class="chat-empty">
        <el-icon :size="64"><ChatDotRound /></el-icon>
        <p>选择或创建一个对话开始</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { chatApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Service, UserFilled, ChatDotRound, Reading } from '@element-plus/icons-vue';

const route = useRoute(); const router = useRouter();
const sessions = ref([]); const messages = ref([]);
const currentSessionId = ref(null); const inputMessage = ref(''); const sending = ref(false);
const msgArea = ref(null);
const courseContext = ref('');

onMounted(async () => {
  await loadSessions();
  if (sessions.value.length > 0 && !route.params.sessionId) {
    selectSession(sessions.value[0].id);
  }
});
watch(() => route.params.sessionId, id => { if (id) selectSession(Number(id)); });

async function loadSessions() { try { const r=await chatApi.listSessions(); if(r.code===200) sessions.value=r.data||[]; } catch{} }
async function createSession() { try { const r=await chatApi.createSession(); if(r.code===200){ await loadSessions(); selectSession(r.data.id); } } catch{ ElMessage.error('创建失败'); } }
async function selectSession(id) {
  currentSessionId.value=id; router.replace(`/chat/${id}`);
  await loadMessages(id);
  // resolve course name
  const s = sessions.value.find(s => s.id === id);
  if (s?.courseId) {
    try {
      const r = await courseApi.getById(s.courseId);
      if (r.code === 200) courseContext.value = '当前课程：' + r.data.title;
      else courseContext.value = '';
    } catch { courseContext.value = ''; }
  } else {
    courseContext.value = '';
  }
}
async function loadMessages(sid) { try { const r=await chatApi.getMessages(sid,1,100); if(r.code===200){ messages.value=r.data?.records||[]; await nextTick(); scrollToBottom(); } } catch{} }
async function sendMessage() { const t=inputMessage.value.trim(); if(!t||sending.value) return; inputMessage.value=''; sending.value=true;
  messages.value.push({id:Date.now(),role:'USER',content:t}); await nextTick(); scrollToBottom();
  try { const r=await chatApi.sendMessage(currentSessionId.value,t); if(r.code===200){ messages.value.push({id:r.data.messageId,role:'ASSISTANT',content:r.data.response}); await loadSessions(); }
    else { messages.value.push({id:Date.now()+1,role:'ASSISTANT',content:'获取回复失败'}); }
  } catch { messages.value.push({id:Date.now()+1,role:'ASSISTANT',content:'网络错误'}); }
  finally { sending.value=false; await nextTick(); scrollToBottom(); } }
async function deleteSession(id) { try { await ElMessageBox.confirm('确定删除？','提示',{type:'warning'}); await chatApi.deleteSession(id);
  if(currentSessionId.value===id){currentSessionId.value=null;messages.value=[];router.replace('/chat');courseContext.value='';} await loadSessions(); ElMessage.success('已删除'); } catch{} }
function handleKeydown(e) { if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); sendMessage(); } }
function scrollToBottom() { if(msgArea.value) msgArea.value.scrollTop=msgArea.value.scrollHeight; }
function formatTime(t) { if(!t) return ''; const d=new Date(t); const n=new Date(); if(d.toDateString()===n.toDateString()) return d.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}); return d.toLocaleDateString('zh-CN',{month:'2-digit',day:'2-digit'}); }
function truncate(s,n) { if(!s) return ''; return s.length>n?s.substring(0,n)+'...':s; }
</script>

<style scoped>
.chat-page { display:flex; height:calc(100vh - 120px); background:#fff; border-radius:8px; overflow:hidden; }
.chat-sidebar { width:280px; border-right:1px solid #ebeef5; display:flex; flex-direction:column; }
.sidebar-header { padding:12px; border-bottom:1px solid #ebeef5; }
.session-list { flex:1; overflow-y:auto; }
.session-item { padding:14px 16px; cursor:pointer; position:relative; border-bottom:1px solid #f5f5f5; transition:background .2s; }
.session-item:hover { background:#f5f7fa; }
.session-item.active { background:#ecf5ff; border-left:3px solid #409eff; }
.session-title { font-size:14px; color:#303133; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:24px; }
.session-time { font-size:11px; color:#c0c4cc; margin-top:4px; }
.session-preview { font-size:12px; color:#909399; margin-top:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.delete-btn { position:absolute; right:8px; top:8px; opacity:0; }
.session-item:hover .delete-btn { opacity:1; }
.chat-main { flex:1; display:flex; flex-direction:column; }
.chat-empty { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#c0c4cc; }
.chat-empty p { margin-top:12px; font-size:14px; }
.course-bar { display:flex; align-items:center; gap:8px; padding:8px 20px; background:#ecf5ff; color:#409eff; font-size:13px; font-weight:500; border-bottom:1px solid #d9ecff; }
.messages-area { flex:1; overflow-y:auto; padding:20px; background:#fafafa; }
.message-row { display:flex; margin-bottom:20px; gap:10px; }
.message-row.user { flex-direction:row-reverse; }
.message-bubble { max-width:68%; }
.message-row.user .message-bubble { background:#409eff; color:#fff; border-radius:16px 16px 4px 16px; }
.message-row.assistant .message-bubble { background:#fff; color:#303133; border-radius:16px 16px 16px 4px; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.message-content { padding:12px 16px; font-size:14px; line-height:1.7; white-space:pre-wrap; word-break:break-word; }
.typing { color:#909399; }
.input-area { padding:16px; border-top:1px solid #ebeef5; display:flex; gap:12px; align-items:flex-end; background:#fff; }
.input-area :deep(.el-textarea__inner) { resize:none; }
</style>