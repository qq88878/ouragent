<template>
  <div class="chat-page">
    <!-- 侧边栏 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-select v-model="selectedCourseId" placeholder="按课程筛选" clearable size="default" style="width: 100%; margin-bottom: 10px;" @change="onCourseChange">
          <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
        </el-select>
        <el-button type="primary" style="width: 100%;" @click="createSession">
          <el-icon :size="16"><Plus /></el-icon>
          <span>新建对话</span>
        </el-button>
      </div>

      <div class="session-list">
        <div v-for="session in sessions" :key="session.id" class="session-item" :class="{ active: currentSessionId === session.id }" @click="selectSession(session.id)">
          <div class="session-indicator" :class="{ active: currentSessionId === session.id }"></div>
          <div class="session-main">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-meta">
              <span v-if="session.courseName" class="session-course-tag">{{ session.courseName }}</span>
              <span class="session-count" v-if="session.messageCount">{{ session.messageCount }} 条消息</span>
            </div>
            <div class="session-time">{{ formatTime(session.lastMessageTime || session.createTime) }}</div>
          </div>
          <el-button class="delete-btn" text size="small" type="danger" @click.stop="deleteSession(session.id)">
            <el-icon :size="14"><Delete /></el-icon>
          </el-button>
        </div>
        <div v-if="sessions.length === 0" class="empty-sessions">
          <el-icon :size="40" color="#C9CDD4"><ChatDotRound /></el-icon>
          <p>暂无对话</p>
          <span>点击上方按钮创建新对话</span>
        </div>
      </div>
    </div>

    <!-- 主区域 -->
    <div class="chat-main">
      <div v-if="!currentSessionId" class="chat-empty">
        <div class="empty-illustration">
          <svg viewBox="0 0 140 110" fill="none"><rect x="25" y="25" width="90" height="55" rx="12" fill="#EEF0FF"/><circle cx="50" cy="52" r="10" fill="#5B6AF0" opacity="0.25"/><circle cx="70" cy="52" r="10" fill="#5B6AF0" opacity="0.45"/><circle cx="90" cy="52" r="10" fill="#5B6AF0" opacity="0.65"/><rect x="38" y="88" width="64" height="7" rx="3.5" fill="#E8ECF3"/></svg>
        </div>
        <h3>开始对话</h3>
        <p>选择已有对话或创建新的对话，与AI进行智能交流</p>
      </div>

      <template v-else>
        <div class="chat-session-header">
          <h4>{{ currentSessionTitle }}</h4>
        </div>

        <div class="messages-area" ref="messagesArea">
          <div v-for="(msg, idx) in messages" :key="msg.id" class="message-row" :class="msg.role.toLowerCase()">
            <div v-if="msg.role.toLowerCase() === 'assistant'" class="msg-avatar ai-avatar">
              <svg viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#EEF0FF"/><path d="M16 7l7 5v9l-7 5-7-5v-9l7-5z" fill="#5B6AF0" opacity="0.3"/><circle cx="16" cy="15" r="4" fill="#5B6AF0"/></svg>
            </div>

            <div class="message-body">
              <div class="msg-meta" v-if="idx === 0 || messages[idx-1]?.role !== msg.role">
                <span>{{ msg.role.toLowerCase() === 'assistant' ? 'AI 助手' : '我' }}</span>
                <span class="msg-time" v-if="msg.createTime">{{ formatMsgTime(msg.createTime) }}</span>
              </div>

              <div class="message-bubble">
                <div class="message-content" :class="{ thinking: msg.streaming && !msg.content }">
                  <template v-if="msg.streaming && !msg.content">
                    <span class="thinking-dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
                    <span class="thinking-text">思考中...</span>
                  </template>
                  <template v-else>
                    <span class="msg-text">{{ msg.content }}</span>
                    <span v-if="msg.streaming" class="cursor">|</span>
                  </template>
                </div>
                <div v-if="msg.quality" class="quality-badge">
                  <el-tag :type="msg.quality.score >= 70 ? 'success' : msg.quality.score >= 50 ? 'warning' : 'danger'" size="small" effect="plain">
                    质量评分: {{ msg.quality.score }}分
                  </el-tag>
                  <el-tag v-if="msg.workflow?.retries > 0" type="info" size="small" effect="plain">
                    优化 {{ msg.workflow.retries }} 次
                  </el-tag>
                </div>
              </div>
            </div>

            <div v-if="msg.role.toLowerCase() === 'user'" class="msg-avatar user-avatar">
              {{ userInitial }}
            </div>
          </div>

          <div v-if="messages.length === 0 && currentSessionId" class="chat-empty-inline">
            <p>发送第一条消息，开始对话</p>
          </div>
        </div>

        <div class="input-area">
          <div class="input-options">
            <el-switch v-model="deepMode" active-text="深度答疑" inactive-text="快速对话" size="small" />
            <span v-if="deepMode" class="deep-mode-hint">AI 将自动检查回答质量</span>
          </div>
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="1"
              :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              @keydown="handleKeydown"
              :disabled="sending"
              class="chat-input"
            />
            <el-button type="primary" :loading="sending" :disabled="!inputMessage.trim()" @click="sendMessage" class="send-btn">
              <el-icon :size="18"><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { chatApi, courseApi, agentApi } from '@/api';
import { useChatStore } from '@/stores/chat';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, ChatDotRound, Plus, Promotion } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();

const userInitial = computed(() => (authStore.user?.nickname || authStore.user?.username || '?')[0]);
const currentSessionTitle = computed(() => {
  const s = sessions.value.find(s => s.id === currentSessionId.value);
  return s?.title || '对话';
});

const sessions = ref([]);
const messages = ref([]);
const currentSessionId = ref(null);
const inputMessage = ref('');
const sending = ref(false);
const messagesArea = ref(null);
const courses = ref([]);
const selectedCourseId = ref(null);
const deepMode = ref(false);

let abortController = null;

onMounted(async () => {
  await Promise.all([loadSessions(), loadCourses()]);
  const saved = localStorage.getItem('chatCourseId');
  if (saved) selectedCourseId.value = Number(saved);
  if (route.params.sessionId) selectSession(Number(route.params.sessionId));
});

onUnmounted(() => {
  chatStore.setChatOpen(false);
  if (abortController) abortController.abort();
});

watch(() => route.params.sessionId, (newId) => {
  if (newId) {
    selectSession(Number(newId));
  } else {
    currentSessionId.value = null;
    messages.value = [];
  }
});

async function loadSessions() { try { const r = await chatApi.listSessions(); if (r.code === 200) sessions.value = r.data || []; } catch {} }
async function loadCourses() { try { const r = await courseApi.list({ page: 1, size: 200 }); if (r.code === 200) courses.value = r.data?.records || []; } catch {} }
function onCourseChange() { if (selectedCourseId.value) { localStorage.setItem('chatCourseId', String(selectedCourseId.value)); } else { localStorage.removeItem('chatCourseId'); } }

async function createSession() {
  try {
    const res = await chatApi.createSession(selectedCourseId.value || null);
    if (res.code === 200) { await loadSessions(); selectSession(res.data.id); router.replace('/chat/' + res.data.id); }
  } catch { ElMessage.error('创建失败'); }
}

async function selectSession(id) {
  if (abortController) abortController.abort();
  currentSessionId.value = id;
  router.replace('/chat/' + id);
  try {
    const res = await chatApi.getMessages(id);
    messages.value = (res.data?.records || []).map(m => ({ ...m, streaming: false }));
    await nextTick();
    scrollToBottom();
  } catch { messages.value = []; }
}

async function sendMessage() {
  const text = inputMessage.value.trim();
  if (!text || sending.value) return;
  inputMessage.value = '';

  const msgId = Date.now();
  messages.value.push({ id: msgId, role: 'user', content: text, streaming: false, createTime: new Date().toISOString() });
  const assistantMsg = { id: msgId + 1, role: 'assistant', content: '', streaming: true, quality: null };
  messages.value.push(assistantMsg);
  await nextTick();
  scrollToBottom();
  sending.value = true;

  // 深度答疑模式：流式调用 quality-check 端点
  if (deepMode.value) {
    abortController = new AbortController();
    try {
      for await (const event of agentApi.streamChatWithQualityCheck(text, {}, currentSessionId.value, abortController.signal)) {
        if (event.type === 'text') {
          assistantMsg.content += event.content;
          scrollToBottom();
        } else if (event.type === 'quality_check') {
          assistantMsg.quality = event.quality;
        } else if (event.type === 'error') {
          assistantMsg.content += '\n\n[错误] ' + event.error;
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        assistantMsg.content = assistantMsg.content || '请求失败：' + (e.message || '网络错误');
      }
    }
    assistantMsg.streaming = false;
    assistantMsg.createTime = new Date().toISOString();
    sending.value = false;
    abortController = null;
    loadSessions();
    nextTick().then(scrollToBottom);
    return;
  }

  // 准备 AbortController 用于取消
  abortController = new AbortController();

  try {
    // 直接使用 fetch + ReadableStream（更可靠）
    const token = localStorage.getItem('accessToken');
    const response = await fetch('/api/chat/sessions/' + currentSessionId.value + '/messages/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
      body: JSON.stringify({ message: text }),
      signal: abortController.signal,
    });

    if (!response.ok) throw new Error('HTTP ' + response.status);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';
    let streamEnded = false;

    // 流读取循环：读所有数据到 buffer
    const readAll = async () => {
      while (!streamEnded) {
        try {
          const { done, value } = await reader.read();
          if (value) buffer += decoder.decode(value, { stream: true });
          if (done) {
            buffer += decoder.decode(); // flush
            streamEnded = true;
          }
        } catch (e) {
          if (e.name === 'AbortError') { streamEnded = true; }
          else throw e;
        }
        // 解析 buffer 中的 SSE 数据
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(line.charAt(5) === ' ' ? 6 : 5));
              if (data.type === 'end' || data.done) { streamEnded = true; break; }
              if (data.type === 'text' || data.type === 'message') { fullContent += data.content || ''; }
              else if (data.content !== undefined) { fullContent += data.content || ''; }
              if (data.type === 'error' || data.error) { fullContent += '[错误] ' + (data.error || ''); streamEnded = true; break; }
            } catch {}
          }
        }
      }
    };

    // 显示动画循环：按速率显示内容
    const CHARS_PER_SEC = 80;
    const startTime = Date.now();

    const displayLoop = () => {
      return new Promise((resolve) => {
        const timer = setInterval(() => {
          const elapsed = (Date.now() - startTime) / 1000;
          const targetLen = Math.floor(elapsed * CHARS_PER_SEC);

          if (targetLen > assistantMsg.content.length) {
            const newLen = Math.min(targetLen, fullContent.length);
            assistantMsg.content = fullContent.slice(0, newLen);
            scrollToBottom();
          }

          if (streamEnded && assistantMsg.content.length >= fullContent.length) {
            assistantMsg.content = fullContent;
            assistantMsg.streaming = false;
            assistantMsg.createTime = new Date().toISOString();
            clearInterval(timer);
            sending.value = false;
            abortController = null;
            loadSessions();
            nextTick().then(scrollToBottom);
            resolve();
          }
        }, 33);
      });
    };

    await Promise.all([readAll(), displayLoop()]);
  } catch (e) {
    if (e.name !== 'AbortError') {
      assistantMsg.content = assistantMsg.content || '抱歉，请求失败了，请检查后端服务。';
    }
    assistantMsg.streaming = false;
    sending.value = false;
    abortController = null;
  }
}

async function deleteSession(id) {
  try { await ElMessageBox.confirm('确定删除这个对话吗？', '提示', { type: 'warning' }); await chatApi.deleteSession(id); if (currentSessionId.value === id) { currentSessionId.value = null; messages.value = []; router.replace('/chat'); } await loadSessions(); ElMessage.success('已删除'); } catch {}
}

function handleKeydown(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }
function scrollToBottom() { if (messagesArea.value) { messagesArea.value.scrollTop = messagesArea.value.scrollHeight; } }

function formatTime(time) {
  if (!time) return '';
  const d = new Date(time); const now = new Date();
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24));
  if (diffDays < 7) return diffDays + '天前';
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}
function formatMsgTime(time) {
  if (!time) return '';
  return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}
</script>

<style scoped>
.chat-page { display: flex; height: calc(100vh - 120px); background: var(--color-bg-card); border-radius: var(--radius-xl); overflow: hidden; box-shadow: var(--shadow-card); }

.chat-sidebar { width: 280px; border-right: 1px solid var(--color-border); display: flex; flex-direction: column; background: var(--color-bg); }
.sidebar-header { padding: 16px; border-bottom: 1px solid var(--color-border); }
.session-list { flex: 1; overflow-y: auto; padding: 6px 8px; }

.session-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: var(--radius-md); cursor: pointer; transition: all var(--transition-fast); margin-bottom: 2px; position: relative; }
.session-item:hover { background: var(--color-bg-hover); }
.session-item.active { background: var(--color-primary-light); }
.session-indicator { width: 3px; height: 36px; border-radius: 2px; background: transparent; transition: background var(--transition-fast); flex-shrink: 0; margin-top: 2px; }
.session-indicator.active { background: var(--color-primary); }
.session-main { flex: 1; min-width: 0; }
.session-title { font-size: 13px; font-weight: 600; color: var(--color-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-meta { display: flex; align-items: center; gap: 6px; margin-top: 3px; }
.session-course-tag { font-size: 10px; color: var(--color-primary); background: var(--color-primary-light); padding: 1px 6px; border-radius: 4px; font-weight: 500; }
.session-count { font-size: 10px; color: var(--color-text-muted); }
.session-time { font-size: 11px; color: var(--color-text-placeholder); margin-top: 3px; }
.delete-btn { opacity: 0; flex-shrink: 0; margin-top: 2px; transition: opacity var(--transition-fast); }
.session-item:hover .delete-btn { opacity: 1; }

.empty-sessions { display: flex; flex-direction: column; align-items: center; padding: 48px 20px; color: var(--color-text-placeholder); text-align: center; }
.empty-sessions p { margin-top: 12px; font-size: 13px; font-weight: 500; }
.empty-sessions span { font-size: 11px; margin-top: 4px; }

.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.empty-illustration { margin-bottom: 20px; }
.empty-illustration svg { width: 140px; height: 110px; }
.chat-empty h3 { font-size: 18px; font-weight: 600; color: var(--color-text); margin-bottom: 6px; }
.chat-empty p { font-size: 13px; color: var(--color-text-muted); }

.chat-session-header { padding: 14px 24px; border-bottom: 1px solid var(--color-border); background: var(--color-bg-card); }
.chat-session-header h4 { font-size: 15px; font-weight: 600; color: var(--color-text); }

.messages-area { flex: 1; overflow-y: auto; padding: 20px 24px; }
.message-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 20px; }
.message-row.user { justify-content: flex-end; }
.message-row.assistant { justify-content: flex-start; }

.msg-avatar { width: 34px; height: 34px; border-radius: var(--radius-sm); flex-shrink: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.ai-avatar { background: #EEF0FF; }
.ai-avatar svg { width: 34px; height: 34px; }
.user-avatar { background: linear-gradient(135deg, #5B6AF0, #7C5CFC); color: #fff; font-size: 14px; font-weight: 600; }

.msg-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; padding: 0 2px; }
.msg-meta span:first-child { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }
.msg-time { font-size: 11px; color: var(--color-text-placeholder) !important; font-weight: 400 !important; }

.message-body { max-width: 70%; }
.message-row.user .message-body { max-width: 62%; }
.message-bubble { border-radius: var(--radius-lg); overflow: hidden; }
.message-row.user .message-bubble { background: linear-gradient(135deg, #5B6AF0, #6B7AF5); color: #fff; }
.message-row.assistant .message-bubble { background: var(--color-bg); color: var(--color-text); border: 1px solid var(--color-border); }
.message-content { padding: 12px 16px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.message-content.thinking { display: flex; align-items: center; gap: 8px; min-height: 32px; }

.thinking-dots { display: inline-flex; gap: 3px; }
.thinking-dots .dot { width: 5px; height: 5px; border-radius: 50%; background: #909399; display: inline-block; animation: dotPulse 1.4s infinite ease-in-out both; }
.thinking-dots .dot:nth-child(1) { animation-delay: 0s; }
.thinking-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots .dot:nth-child(3) { animation-delay: 0.4s; }
.thinking-text { font-size: 12px; color: var(--color-text-muted); }
@keyframes dotPulse { 0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1.2); } }
.cursor { animation: blink 0.8s infinite; color: var(--color-primary); font-weight: 700; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.chat-empty-inline { flex: 1; display: flex; align-items: center; justify-content: center; }
.chat-empty-inline p { font-size: 13px; color: var(--color-text-muted); }

.input-area { padding: 14px 24px; border-top: 1px solid var(--color-border); }
.input-wrapper { display: flex; gap: 10px; align-items: flex-end; }
.chat-input { flex: 1; }
.chat-input :deep(.el-textarea__inner) { border-radius: var(--radius-lg) !important; padding: 10px 16px; line-height: 1.5; font-size: 14px; resize: none; }
.send-btn { width: 42px; height: 42px; border-radius: var(--radius-md) !important; padding: 0 !important; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.input-options { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.deep-mode-hint { font-size: 12px; color: var(--color-primary); }

.quality-badge { display: flex; gap: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--color-border-light); }
</style>
