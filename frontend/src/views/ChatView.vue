<template>
  <div class="chat-page">
    <!-- 侧边栏 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-select v-model="selectedCourseId" placeholder="选择课程（不选则AI自动识别）" clearable size="default" style="width: 100%; margin-bottom: 10px;" @change="onCourseChange">
          <el-option label="不指定课程（AI自动选择）" :value="null" />
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

      <!-- 学习画像面板 -->
      <div v-if="currentSessionId && signals" class="signals-panel">
        <div class="signals-header">学习画像</div>

        <div v-if="signals.active_topics?.length" class="signals-section">
          <div class="signals-label">讨论知识点</div>
          <div class="signals-tags">
            <el-tag v-for="(t, i) in signals.active_topics.slice(0, 6)" :key="i" size="small" effect="plain" type="primary">{{ t }}</el-tag>
          </div>
        </div>

        <div v-if="signals.difficulty_distribution" class="signals-section">
          <div class="signals-label">难度感知</div>
          <div class="signals-difficulty">
            <span class="difficulty-bar">
              <span class="difficulty-fill beginner" :style="{ width: difficultyPercent('beginner') }"></span>
              <span class="difficulty-fill neutral" :style="{ width: difficultyPercent('neutral') }"></span>
              <span class="difficulty-fill advanced" :style="{ width: difficultyPercent('advanced') }"></span>
            </span>
            <span class="difficulty-text">{{ difficultyLabel }}</span>
          </div>
        </div>

        <div v-if="signals.gap_keywords?.length" class="signals-section">
          <div class="signals-label">困惑点</div>
          <div class="signals-tags">
            <el-tag v-for="(g, i) in signals.gap_keywords.slice(0, 3)" :key="i" size="small" effect="plain" type="warning">{{ g }}</el-tag>
          </div>
        </div>

        <div class="signals-meta">已对话 {{ signals.exchange_count || 0 }} 轮</div>
      </div>
    </div>
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
            <el-button
              type="warning"
              size="small"
              plain
              :icon="MapLocation"
              :loading="pathLoading"
              :disabled="messages.length === 0"
              @click="generateLearningPath"
              style="margin-left: auto;"
            >
              生成学习路径
            </el-button>
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

    <!-- 学习路径弹窗 -->
    <el-dialog v-model="pathDialogVisible" title="基于对话的个性化学习路径" width="680px" top="5vh" destroy-on-close>
      <div v-if="pathLoading" class="path-loading">
        <el-skeleton :rows="6" animated />
      </div>
      <div v-else-if="pathData" class="path-content">
        <div class="path-header">
          <h3>{{ pathData.title }}</h3>
          <p>{{ pathData.description }}</p>
        </div>

        <!-- 已讨论知识点 -->
        <div v-if="pathData.discussed_topics?.length" class="path-section">
          <h4 class="section-title">
            <el-icon><ChatDotRound /></el-icon>
            已讨论的知识点（{{ pathData.discussed_topics.length }}）
          </h4>
          <div class="discussed-tags">
            <el-tag v-for="(t, i) in pathData.discussed_topics" :key="i" type="success" effect="plain" size="default">
              {{ t.topic }}
              <span class="tag-count">({{ t.message_count || 0 }}次)</span>
            </el-tag>
          </div>
        </div>

        <!-- 学习步骤时间线 -->
        <div class="path-section">
          <h4 class="section-title">
            <el-icon><MapLocation /></el-icon>
            学习路径（{{ pathData.total_steps || pathData.steps?.length || 0 }}步）
          </h4>
          <div class="path-timeline">
            <div v-for="(step, idx) in pathData.steps" :key="idx" class="timeline-item" :class="{ completed: step.status === 'completed' }">
              <div class="timeline-dot" :class="{ completed: step.status === 'completed' }">
                <span v-if="step.status === 'completed'">✓</span>
                <span v-else>{{ step.order || idx + 1 }}</span>
              </div>
              <div class="timeline-line" v-if="idx < pathData.steps.length - 1"></div>
              <div class="timeline-content">
                <div class="step-header">
                  <span class="step-title">{{ step.title }}</span>
                  <el-tag v-if="step.status === 'completed'" type="success" size="small" effect="plain">已讨论</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain">待学习</el-tag>
                  <span v-if="step.estimated_hours" class="step-hours">{{ step.estimated_hours }}h</span>
                </div>
                <p class="step-desc">{{ step.description }}</p>
                <div v-if="step.checkpoint" class="step-checkpoint">
                  <strong>检验方式：</strong>{{ step.checkpoint }}
                </div>
                <!-- 关联知识库内容 -->
                <el-collapse v-if="step.knowledge_items?.length" class="step-knowledge">
                  <el-collapse-item :title="`关联知识库内容（${step.knowledge_items.length}条）`">
                    <div v-for="(ki, kiIdx) in step.knowledge_items" :key="kiIdx" class="knowledge-item">
                      <div class="ki-source">{{ ki.source || `知识片段 #${ki.id}` }}</div>
                      <div class="ki-content">{{ ki.content }}</div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </div>

        <div class="path-footer">
          <span class="path-meta">共检索到 {{ pathData.knowledge_items_count || 0 }} 条知识库内容</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="pathDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { chatApi, courseApi, agentApi, learningApi } from '@/api';
import { useChatStore } from '@/stores/chat';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, ChatDotRound, Plus, Promotion, MapLocation } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();

const userInitial = computed(() => (authStore.user?.nickname || authStore.user?.username || '?')[0]);

const difficultyPercent = (level) => {
  const dist = signals.value?.difficulty_distribution || {};
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  return total > 0 ? Math.round((dist[level] || 0) / total * 100) + '%' : '33%';
};
const difficultyLabel = computed(() => {
  const dist = signals.value?.difficulty_distribution || {};
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  if (total === 0) return '中等';
  const max = Math.max(dist.beginner || 0, dist.neutral || 0, dist.advanced || 0);
  if (max === (dist.beginner || 0)) return '入门水平';
  if (max === (dist.advanced || 0)) return '进阶水平';
  return '中等水平';
});

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

// 实时学习画像
const signals = ref(null);

// 学习路径
const pathDialogVisible = ref(false);
const pathLoading = ref(false);
const pathData = ref(null);

let abortController = null;

onMounted(async () => {
  await Promise.all([loadSessions(), loadCourses()]);
  const saved = localStorage.getItem('chatCourseId');
  if (saved) selectedCourseId.value = Number(saved);
  if (route.params.sessionId) selectSession(Number(route.params.sessionId));
});

onUnmounted(() => {
  chatStore.setChatPageActive(false);
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
async function loadSignals(sessionId) {
  if (!sessionId) { signals.value = null; return; }
  try {
    const r = await chatApi.getSignals(sessionId);
    signals.value = r.code === 200 ? r.data?.signals : null;
  } catch { signals.value = null; }
}
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
    loadSignals(id);
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
    loadSignals(currentSessionId.value);
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
            loadSignals(currentSessionId.value);
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

async function generateLearningPath() {
  if (messages.value.length === 0) return;

  // 检查问卷完成状态
  try {
    const qs = await learningApi.getQuestionnaireStatus();
    if (!qs.data || !qs.data.completed) {
      try {
        await ElMessageBox.confirm('完成学习画像问卷可获得更精准的个性化路径，是否先去完成？', '提示', {
          confirmButtonText: '去完成问卷',
          cancelButtonText: '跳过，直接生成',
          type: 'info',
        });
        router.push('/profile');
        return;
      } catch {
        // 用户点了"跳过"，继续生成
      }
    }
  } catch {
    // 接口失败不阻塞生成
  }

  pathDialogVisible.value = true;
  pathLoading.value = true;
  pathData.value = null;

  const currentCourse = courses.value.find(c => c.id === selectedCourseId.value);
  const chatMessages = messages.value.map(m => ({ role: m.role, content: m.content }));

  try {
    const res = await agentApi.generateLearningPathFromChat(
      chatMessages,
      selectedCourseId.value ? String(selectedCourseId.value) : null,
      currentCourse?.title || '',
    );
    pathData.value = res;
  } catch (e) {
    ElMessage.error('生成学习路径失败: ' + (e.response?.data?.detail || e.message || '网络错误'));
    pathDialogVisible.value = false;
  } finally {
    pathLoading.value = false;
  }
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

/* 学习路径弹窗 */
.path-loading { padding: 16px 0; }
.path-header { margin-bottom: 20px; }
.path-header h3 { font-size: 18px; font-weight: 700; color: var(--color-text); margin-bottom: 6px; }
.path-header p { font-size: 13px; color: var(--color-text-muted); line-height: 1.6; }

.path-section { margin-bottom: 20px; }
.section-title { font-size: 14px; font-weight: 600; color: var(--color-text); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }

.discussed-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.discussed-tags .el-tag { font-size: 13px; }
.tag-count { font-size: 11px; opacity: 0.7; margin-left: 2px; }

.path-timeline { position: relative; padding-left: 8px; }
.timeline-item { display: flex; position: relative; padding-bottom: 20px; }
.timeline-item:last-child { padding-bottom: 0; }
.timeline-dot {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff;
  background: var(--color-primary); z-index: 1;
}
.timeline-dot.completed { background: var(--color-success); }
.timeline-line {
  position: absolute; left: 13px; top: 28px; width: 2px;
  height: calc(100% - 28px); background: var(--color-border);
}
.timeline-content { flex: 1; margin-left: 12px; min-width: 0; }
.step-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.step-title { font-size: 14px; font-weight: 600; color: var(--color-text); }
.step-hours { font-size: 11px; color: var(--color-text-muted); margin-left: auto; }
.step-desc { font-size: 13px; color: var(--color-text-secondary); line-height: 1.6; margin-bottom: 6px; }
.step-checkpoint { font-size: 12px; color: var(--color-text-muted); padding: 6px 10px; background: var(--color-bg); border-radius: var(--radius-sm); }
.step-knowledge { margin-top: 8px; }
.step-knowledge :deep(.el-collapse-item__header) { font-size: 12px; height: 32px; }
.knowledge-item { padding: 8px; background: var(--color-bg); border-radius: var(--radius-sm); margin-bottom: 6px; }
.ki-source { font-size: 11px; color: var(--color-primary); font-weight: 600; margin-bottom: 4px; }
.ki-content { font-size: 12px; color: var(--color-text-secondary); line-height: 1.5; }

.path-footer { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--color-border); }
.path-meta { font-size: 12px; color: var(--color-text-muted); }

/* 学习画像面板 */
.signals-panel { padding: 12px 16px; border-top: 1px solid var(--color-border); background: var(--color-bg-card); font-size: 12px; }
.signals-header { font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 10px; }
.signals-section { margin-bottom: 8px; }
.signals-label { color: var(--color-text-muted); margin-bottom: 4px; font-size: 11px; }
.signals-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.signals-difficulty { display: flex; align-items: center; gap: 8px; }
.difficulty-bar { display: flex; height: 6px; flex: 1; border-radius: 3px; overflow: hidden; background: var(--color-border); }
.difficulty-fill { height: 100%; transition: width 0.3s; }
.difficulty-fill.beginner { background: #67C23A; }
.difficulty-fill.neutral { background: #E6A23C; }
.difficulty-fill.advanced { background: #F56C6C; }
.difficulty-text { font-size: 11px; color: var(--color-text-secondary); white-space: nowrap; }
.signals-meta { color: var(--color-text-muted); font-size: 11px; margin-top: 4px; }
</style>
