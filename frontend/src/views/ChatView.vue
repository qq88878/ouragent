<template>
  <div class="chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-select
          v-model="selectedCourseId"
          placeholder="选择课程（可选）"
          clearable
          size="small"
          style="width: 100%; margin-bottom: 8px;"
          @change="onCourseChange"
        >
          <el-option
            v-for="c in courses"
            :key="c.id"
            :label="c.title"
            :value="c.id"
          />
        </el-select>
        <el-button type="primary" style="width: 100%;" @click="createSession">
          + 新对话
        </el-button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="selectSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div v-if="session.courseName" class="session-course">{{ session.courseName }}</div>
          <div class="session-time">{{ formatTime(session.lastMessageTime || session.createTime) }}</div>
          <el-button
            class="delete-btn"
            text
            size="small"
            type="danger"
            @click.stop="deleteSession(session.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <div class="chat-main">
      <div v-if="!currentSessionId" class="chat-empty">
        <el-icon :size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
        <p>选择或创建一个对话开始聊天</p>
      </div>

      <template v-else>
        <div class="messages-area" ref="messagesArea">
          <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.role.toLowerCase()">
            <div class="message-bubble">
              <div class="message-content" :class="{ thinking: msg.streaming && !msg.content }">
              <template v-if="msg.streaming && !msg.content">
                <span class="thinking-dots">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </span>
                <span class="thinking-text">思考中... {{ thinkingTime }}</span>
              </template>
              <template v-else>
                {{ msg.content }}<span v-if="msg.streaming" class="cursor">|</span>
              </template>
            </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            @keydown="handleKeydown"
            :disabled="sending"
          />
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!inputMessage.trim()"
            @click="sendMessage"
          >
            发送
          </el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { chatApi, courseApi } from '@/api';
import { useChatStore } from '@/stores/chat';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, ChatDotRound } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();

const sessions = ref([]);
const messages = ref([]);
const currentSessionId = ref(null);
const inputMessage = ref('');
const sending = ref(false);
const messagesArea = ref(null);
const courses = ref([]);
const selectedCourseId = ref(null);
const thinkingStart = ref(null);
const thinkingTime = ref('');
let thinkingTimer = null;

function startThinking() {
  thinkingStart.value = Date.now();
  thinkingTime.value = '0s';
  thinkingTimer = setInterval(() => {
    const elapsed = ((Date.now() - thinkingStart.value) / 1000).toFixed(1);
    thinkingTime.value = elapsed + 's';
  }, 100);
}

function stopThinking() {
  if (thinkingTimer) {
    clearInterval(thinkingTimer);
    thinkingTimer = null;
  }
  thinkingStart.value = null;
  thinkingTime.value = '';
}

onMounted(async () => {
  await Promise.all([loadSessions(), loadCourses()]);
  // 恢复用户上次选择的课程
  const saved = localStorage.getItem('chatCourseId');
  if (saved) selectedCourseId.value = Number(saved);
  if (route.params.sessionId) {
    selectSession(Number(route.params.sessionId));
  }
});

onUnmounted(() => {
  chatStore.setChatPageActive(false);
});

watch(() => route.params.sessionId, (id) => {
  if (id) selectSession(Number(id));
});

async function loadSessions() {
  try {
    const res = await chatApi.listSessions();
    if (res.code === 200) sessions.value = res.data || [];
  } catch { /* ignore */ }
}

async function loadCourses() {
  try {
    const res = await courseApi.list({ page: 1, size: 100 });
    if (res.code === 200) courses.value = res.data?.records || res.data || [];
  } catch { /* ignore */ }
}

function onCourseChange(courseId) {
  if (courseId) {
    localStorage.setItem('chatCourseId', courseId);
  } else {
    localStorage.removeItem('chatCourseId');
  }
}

async function createSession() {
  try {
    const res = await chatApi.createSession(selectedCourseId.value || undefined);
    if (res.code === 200) {
      await loadSessions();
      selectSession(res.data.id);
    }
  } catch {
    ElMessage.error('创建会话失败');
  }
}

async function selectSession(id) {
  currentSessionId.value = id;
  chatStore.setChatPageActive(true);
  router.replace(`/chat/${id}`);
  await loadMessages(id);

  // Reconnect to existing stream if any
  const existing = chatStore.getStream(id);
  if (existing && !existing.done) {
    // Inject the in-progress assistant message
    const assistantMsg = {
      id: Date.now(),
      role: 'ASSISTANT',
      content: existing.content,
      streaming: true,
    };
    messages.value.push(assistantMsg);
    sending.value = true;
    let displayLen = existing.content.length;
    let startTime = Date.now();
    const CHARS_PER_SEC = 80;

    const poll = new Promise((resolve) => {
      const timer = setInterval(() => {
        const s = chatStore.getStream(id);
        if (!s || s.done) {
          stopThinking();
          assistantMsg.content = s ? s.content : assistantMsg.content;
          if (assistantMsg.content) {
            assistantMsg.streaming = false;
          } else {
            messages.value.pop();
          }
          sending.value = false;
          clearInterval(timer);
          resolve();
          return;
        }
        const sourceLen = s.content.length;
        const elapsedSec = (Date.now() - startTime) / 1000;
        const targetLen = Math.min(Math.floor(elapsedSec * CHARS_PER_SEC), sourceLen);
        if (targetLen > displayLen) {
          displayLen = targetLen;
          assistantMsg.content = s.content.slice(0, displayLen);
          scrollToBottom();
        }
      }, 33);
    });
    await poll;
  }
}

async function loadMessages(sessionId) {
  try {
    const res = await chatApi.getMessages(sessionId, 1, 100);
    if (res.code === 200) {
      messages.value = res.data?.records || [];
      await nextTick();
      scrollToBottom();
    }
  } catch { /* ignore */ }
}

async function sendMessage() {
  const text = inputMessage.value.trim();
  if (!text || sending.value) return;

  inputMessage.value = '';
  sending.value = true;

  messages.value.push({
    id: Date.now(),
    role: 'USER',
    content: text,
  });

  const assistantMsg = {
    id: Date.now() + 1,
    role: 'ASSISTANT',
    content: '',
    streaming: true,
  };
  messages.value.push(assistantMsg);
  await nextTick();
  scrollToBottom();

  startThinking();

  const sid = currentSessionId.value;

  // Start stream via store ? runs in background even if component unmounts
  chatStore.startStream(sid, text);

  // Typewriter: reveal at steady 80 chars/sec using cumulative timing
  let displayLen = 0;
  let startTime = 0;
  const CHARS_PER_SEC = 80;

  const poll = new Promise((resolve) => {
    const timer = setInterval(() => {
      const s = chatStore.getStream(sid);
      if (!s) { clearInterval(timer); resolve(); return; }
      if (s.error) {
        stopThinking();
        assistantMsg.content = s.error;
        assistantMsg.streaming = false;
        clearInterval(timer);
        sending.value = false;
        resolve();
        return;
      }

      if (startTime === 0) startTime = Date.now();
      const sourceLen = s.content.length;

      // Calculate target display length based on elapsed time
      const elapsedSec = (Date.now() - startTime) / 1000;
      const targetLen = Math.min(Math.floor(elapsedSec * CHARS_PER_SEC), sourceLen);

      if (targetLen > displayLen) {
        if (displayLen === 0) stopThinking();
        displayLen = targetLen;
        assistantMsg.content = s.content.slice(0, displayLen);
        scrollToBottom();
      }

      // Stream done and all chars revealed
      if (s.done && displayLen >= sourceLen) {
        stopThinking();
        assistantMsg.content = s.content;
        assistantMsg.streaming = false;
        clearInterval(timer);
        sending.value = false;
        loadSessions();
        nextTick().then(scrollToBottom);
        resolve();
      }
    }, 33);  // ~30fps
  });

  await poll;
}

async function deleteSession(id) {
  try {
    await ElMessageBox.confirm('确定删除这个对话吗？', '提示', { type: 'warning' });
    await chatApi.deleteSession(id);
    if (currentSessionId.value === id) {
      currentSessionId.value = null;
      messages.value = [];
      router.replace('/chat');
    }
    await loadSessions();
    ElMessage.success('已删除');
  } catch { /* cancel */ }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function scrollToBottom() {
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight;
  }
}

function formatTime(time) {
  if (!time) return '';
  const d = new Date(time);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}
</script>

<style scoped>
.chat-page { display: flex; height: calc(100vh - 120px); background: #fff; border-radius: 8px; overflow: hidden; }
.chat-sidebar { width: 260px; border-right: 1px solid #ebeef5; display: flex; flex-direction: column; }
.sidebar-header { padding: 12px; border-bottom: 1px solid #ebeef5; }
.session-list { flex: 1; overflow-y: auto; }
.session-item {
  padding: 12px 16px; cursor: pointer; position: relative;
  border-bottom: 1px solid #f5f5f5; transition: background .2s;
}
.session-item:hover { background: #f5f7fa; }
.session-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }
.session-title { font-size: 14px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-course { font-size: 11px; color: #409eff; margin-top: 2px; }
.session-time { font-size: 12px; color: #909399; margin-top: 4px; }
.delete-btn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); opacity: 0; }
.session-item:hover .delete-btn { opacity: 1; }

.chat-main { flex: 1; display: flex; flex-direction: column; }
.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #c0c4cc; }
.chat-empty p { margin-top: 12px; font-size: 14px; }

.messages-area { flex: 1; overflow-y: auto; padding: 20px; }
.message-row { display: flex; margin-bottom: 16px; }
.message-row.user { justify-content: flex-end; }
.message-row.assistant { justify-content: flex-start; }
.message-bubble { max-width: 70%; }
.message-row.user .message-bubble { background: #409eff; color: #fff; border-radius: 12px 12px 0 12px; }
.message-row.assistant .message-bubble { background: #f4f4f5; color: #303133; border-radius: 12px 12px 12px 0; }
.message-content { padding: 10px 16px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.typing { color: #909399; }
.cursor { animation: blink 0.8s infinite; color: #409eff; }

.message-content.thinking {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
}
.thinking-dots {
  display: inline-flex;
  gap: 3px;
}
.thinking-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #909399;
  display: inline-block;
  animation: dotPulse 1.4s infinite ease-in-out both;
}
.thinking-dots .dot:nth-child(1) { animation-delay: 0s; }
.thinking-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots .dot:nth-child(3) { animation-delay: 0.4s; }
.thinking-text {
  font-size: 13px;
  color: #909399;
}
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.input-area { padding: 16px; border-top: 1px solid #ebeef5; display: flex; gap: 12px; align-items: flex-end; }
.input-area .el-input { flex: 1; }
</style>
