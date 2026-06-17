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
              <div class="message-content">{{ msg.content }}<span v-if="msg.streaming" class="cursor">|</span></div>
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
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { chatApi, courseApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, ChatDotRound } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();

const sessions = ref([]);
const messages = ref([]);
const currentSessionId = ref(null);
const inputMessage = ref('');
const sending = ref(false);
const messagesArea = ref(null);
const courses = ref([]);
const selectedCourseId = ref(null);
let streamAbortController = null;

onMounted(async () => {
  await Promise.all([loadSessions(), loadCourses()]);
  const saved = localStorage.getItem('chatCourseId');
  if (saved) selectedCourseId.value = Number(saved);
  if (route.params.sessionId) {
    selectSession(Number(route.params.sessionId));
  }
});

onBeforeUnmount(() => {
  abortStream();
});

function abortStream() {
  if (streamAbortController) {
    streamAbortController.abort();
    streamAbortController = null;
  }
}

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
  abortStream();
  currentSessionId.value = id;
  router.replace(`/chat/${id}`);
  await loadMessages(id);
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

  const idx = messages.value.length;
  messages.value.push({
    id: Date.now() + 1,
    role: 'ASSISTANT',
    content: '',
    streaming: true,
  });
  await nextTick();
  scrollToBottom();

  const buffer = [];
  let streamDone = false;
  let hasError = '';

  // 创建 AbortController 用于中断流式请求
  streamAbortController = new AbortController();

  // 消费 SSE 流，写入 buffer
  const consume = (async () => {
    try {
      for await (const chunk of chatApi.sendMessageStream(currentSessionId.value, text, streamAbortController.signal)) {
        if (chunk.error) { hasError = chunk.error; break; }
        if (chunk.content) buffer.push(chunk.content);
        if (chunk.done) break;
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        streamDone = true;
        return;
      }
      if (!buffer.length && !hasError) hasError = '网络错误，请稍后重试。';
    } finally {
      streamDone = true;
    }
  })();

  // 渲染循环：每 30ms 从 buffer 读取内容更新 UI
  const render = new Promise(resolve => {
    const timer = setInterval(() => {
      if (hasError) {
        messages.value[idx].content = hasError;
        clearInterval(timer);
        resolve();
        return;
      }
      if (buffer.length) {
        messages.value[idx].content += buffer.splice(0).join('');
        scrollToBottom();
      }
      if (streamDone && buffer.length === 0) {
        clearInterval(timer);
        resolve();
      }
    }, 30);
  });

  await Promise.all([consume, render]);

  messages.value[idx].streaming = false;
  sending.value = false;
  streamAbortController = null;
  await loadSessions();
  await nextTick();
  scrollToBottom();
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
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.input-area { padding: 16px; border-top: 1px solid #ebeef5; display: flex; gap: 12px; align-items: flex-end; }
.input-area .el-input { flex: 1; }
</style>
