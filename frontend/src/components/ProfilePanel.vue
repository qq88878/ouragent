<template>
  <div class="pp-root" :class="{ collapsed: profileStore.panelCollapsed }">
    <!-- 折叠/展开按钮 -->
    <div class="pp-toggle" @click="profileStore.panelCollapsed = !profileStore.panelCollapsed" :title="profileStore.panelCollapsed ? '展开用户画像' : '收起用户画像'">
      <span v-if="profileStore.panelCollapsed">&#9664;</span>
      <span v-else>&#9654;</span>
    </div>

    <div v-show="!profileStore.panelCollapsed" class="pp-inner">
      <!-- 头部 -->
      <div class="pp-header">
        <span class="pp-title">学习画像</span>
        <button class="pp-btn" @click="refresh" :disabled="profileStore.refreshing">
          {{ profileStore.refreshing ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <!-- 会话标签 -->
      <div v-if="sessionId" class="pp-session-badge">
        当前对话画像
        <span v-if="sessionSignals?.exchange_count" class="pp-exchange-badge">{{ sessionSignals.exchange_count }} 轮</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="profileStore.loading && !profileStore.hasProfile" class="pp-loading">
        <span class="pp-spinner"></span>
        <span>加载画像数据中...</span>
      </div>

      <!-- ===== 第一部分：完整文字画像 ===== -->
      <div v-if="profileStore.hasProfile || basicProfile" class="pp-section">
        <div class="pp-section-title">
          <svg viewBox="0 0 16 16" width="14" height="14"><rect x="2" y="2" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="5" y1="6" x2="11" y2="6" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="9" x2="9" y2="9" stroke="currentColor" stroke-width="1.2"/></svg>
          完整画像描述
        </div>
        <div class="pp-text-profile">
          {{ generatedProfileText }}
        </div>
      </div>

      <!-- ===== 第二部分：雷达图 ===== -->
      <div v-if="radarDims.length >= 3" class="pp-section">
        <div class="pp-section-title">
          <svg viewBox="0 0 16 16" width="14" height="14"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="8" cy="8" r="2" fill="none" stroke="currentColor" stroke-width="1"/><line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="0.5" opacity="0.3"/><line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="0.5" opacity="0.3"/></svg>
          能力维度雷达图
        </div>
        <div class="pp-radar-wrap">
          <svg :viewBox="'0 0 200 200'" class="pp-radar-svg">
            <!-- 背景网格 -->
            <polygon v-for="level in [1,2,3,4]"
              :key="'grid-'+level"
              :points="getRadarPoints(25 * level)"
              fill="none"
              :stroke="level === 4 ? '#C9CDD4' : '#E8ECF3'"
              stroke-width="0.8"
            />
            <!-- 轴线 -->
            <line v-for="(d, i) in radarDims" :key="'axis-'+i"
              :x1="100" :y1="100"
              :x2="100 + 95 * Math.cos(radarAngle(i) - Math.PI/2)"
              :y2="100 + 95 * Math.sin(radarAngle(i) - Math.PI/2)"
              stroke="#E8ECF3" stroke-width="0.5"
            />
            <!-- 数据多边形 -->
            <polygon
              :points="getRadarPoints(null)"
              fill="rgba(91, 106, 240, 0.2)"
              stroke="#5B6AF0"
              stroke-width="1.5"
            />
            <!-- 数据点 -->
            <circle v-for="(d, i) in radarDims" :key="'dot-'+i"
              :cx="100 + (d.value / 100 * 90) * Math.cos(radarAngle(i) - Math.PI/2)"
              :cy="100 + (d.value / 100 * 90) * Math.sin(radarAngle(i) - Math.PI/2)"
              r="3" fill="#5B6AF0"
            />
            <!-- 标签 -->
            <text v-for="(d, i) in radarDims" :key="'label-'+i"
              :x="100 + 105 * Math.cos(radarAngle(i) - Math.PI/2)"
              :y="100 + 105 * Math.sin(radarAngle(i) - Math.PI/2)"
              text-anchor="middle" dominant-baseline="central"
              font-size="10" fill="#555"
            >{{ d.label }}</text>
            <!-- 数值 -->
            <text v-for="(d, i) in radarDims" :key="'val-'+i"
              :x="100 + (d.value / 100 * 90 + 14) * Math.cos(radarAngle(i) - Math.PI/2)"
              :y="100 + (d.value / 100 * 90 + 14) * Math.sin(radarAngle(i) - Math.PI/2)"
              text-anchor="middle" dominant-baseline="central"
              font-size="9" font-weight="700" :fill="'#5B6AF0'"
            >{{ d.value }}</text>
          </svg>
        </div>
        <!-- 维度条形图 -->
        <div class="pp-dim-bars">
          <div v-for="d in radarDims" :key="'bar-'+d.key" class="pp-dim-bar-row">
            <span class="pp-dim-label">{{ d.label }}</span>
            <div class="pp-dim-track">
              <div class="pp-dim-fill" :style="{ width: d.value + '%', background: barColor(d.value) }"></div>
            </div>
            <span class="pp-dim-val">{{ d.value }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 第三部分：会话实时信号 ===== -->
      <div v-if="sessionId && sessionSignals" class="pp-section">
        <div class="pp-section-title">
          <svg viewBox="0 0 16 16" width="14" height="14"><circle cx="8" cy="8" r="3" fill="currentColor" opacity="0.3"/><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
          当前会话信号
        </div>

        <!-- 讨论知识点 -->
        <div v-if="sessionSignals.active_topics?.length" class="pp-signal-row">
          <span class="pp-signal-key">讨论知识点</span>
          <div class="pp-signal-tags">
            <el-tag v-for="(t, i) in sessionSignals.active_topics.slice(0, 8)" :key="'t-'+i" size="small" effect="plain" type="primary">{{ t }}</el-tag>
          </div>
        </div>

        <!-- 难度感知 -->
        <div v-if="sessionSignals.difficulty_distribution" class="pp-signal-row">
          <span class="pp-signal-key">难度感知</span>
          <div class="pp-difficulty-bar-wrap">
            <div class="pp-difficulty-bar">
              <span class="pp-diff-fill beginner" :style="{ width: diffPercent('beginner') }"></span>
              <span class="pp-diff-fill neutral" :style="{ width: diffPercent('neutral') }"></span>
              <span class="pp-diff-fill advanced" :style="{ width: diffPercent('advanced') }"></span>
            </div>
            <span class="pp-diff-label">{{ diffLabel }}</span>
          </div>
        </div>

        <!-- 困惑点 -->
        <div v-if="sessionSignals.gap_keywords?.length" class="pp-signal-row">
          <span class="pp-signal-key">知识困惑点</span>
          <div class="pp-signal-tags">
            <el-tag v-for="(g, i) in sessionSignals.gap_keywords.slice(0, 5)" :key="'g-'+i" size="small" effect="plain" type="warning">{{ g }}</el-tag>
          </div>
        </div>

        <!-- 问题类型分布 -->
        <div v-if="sessionSignals.question_type_dist && Object.keys(sessionSignals.question_type_dist).length" class="pp-signal-row">
          <span class="pp-signal-key">提问类型</span>
          <div class="pp-signal-tags">
            <el-tag v-for="(count, qtype) in sessionSignals.question_type_dist" :key="'qt-'+qtype" size="small" effect="plain" type="info">{{ qtype }} {{ count }}次</el-tag>
          </div>
        </div>
      </div>

      <!-- 无会话时显示基础信息 -->
      <div v-if="!sessionId && profileStore.hasProfile" class="pp-section">
        <div class="pp-info-text">
          选择一个对话以查看该会话的实时学习画像。基础画像会随对话动态更新。
        </div>
      </div>

      <!-- 页脚 -->
      <div v-if="profileStore.lastUpdated" class="pp-footer">
        更新于 {{ fmtTime(profileStore.lastUpdated) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'

const props = defineProps({
  sessionId: { type: [String, Number], default: null },
  signals: { type: Object, default: null }
})

const profileStore = useProfileStore()

// 便捷访问
const basicProfile = computed(() => profileStore.basicProfile)
const sessionSignals = computed(() => {
  // 优先使用 props 传入的 signals，其次使用 store 中的 session signals
  if (props.signals) return props.signals
  return profileStore.sessionSignals
})

// ===== 完整文字画像：综合基础数据 + 会话实时信号 =====
const generatedProfileText = computed(() => {
  const bp = basicProfile.value
  if (!bp) return '暂未获取到画像数据，请完成初始问卷或与AI对话以生成画像。'

  const parts = []

  // 学习风格描述
  const styleMap = {
    VISUAL: '视觉型学习者，擅长通过图表、视频、思维导图等视觉材料理解和记忆知识',
    AUDITORY: '听觉型学习者，擅长通过听课、讨论、音频材料来吸收知识',
    READING: '阅读型学习者，偏好通过阅读书籍、文档和笔记来深入学习',
    KINESTHETIC: '实践型学习者，倾向于通过动手操作、实验和实际项目来掌握技能'
  }
  const styleText = styleMap[bp.learningStyle] || `${bp.learningStyle}型学习者`
  parts.push(styleText)

  // 等级描述
  const levelMap = {
    ZERO_BASIC: '当前为零基础入门阶段，需要从最基础的概念和技能开始学习',
    BEGINNER: '处于初级水平，已掌握基本概念，能够完成简单的练习和任务',
    INTERMEDIATE: '达到中级水平，能够独立解决常见问题，正在向深入理解迈进',
    ADVANCED: '具备高级水平，能够解决复杂问题并探索前沿知识'
  }
  if (bp.gradeLevel) {
    parts.push(levelMap[bp.gradeLevel] || `当前学习等级为${bp.gradeLevel}`)
  }

  // 优势
  if (bp.strengths) {
    parts.push(`学习优势方面：${bp.strengths}`)
  }

  // 不足
  if (bp.weaknesses) {
    parts.push(`需要加强方面：${bp.weaknesses}`)
  }

  // 兴趣
  if (bp.interests) {
    parts.push(`兴趣方向：${bp.interests}`)
  }

  // 偏好设置
  let prefs = bp.preferences
  if (typeof prefs === 'string') {
    try { prefs = JSON.parse(prefs) } catch { prefs = null }
  }
  if (prefs) {
    if (prefs.education_level) {
      const eduMap = { HIGH_SCHOOL: '高中', ASSOCIATE: '大专', BACHELOR: '本科', MASTER: '硕士', PHD: '博士', OTHER: '其他' }
      parts.push(`学历背景：${eduMap[prefs.education_level] || prefs.education_level}`)
    }
    if (prefs.major) {
      parts.push(`专业方向：${prefs.major}`)
    }
    if (prefs.study_pace) {
      const paceMap = { SLOW: '慢速扎实型，倾向逐步深入', MODERATE: '中等节奏，平衡深度与广度', FAST: '快速学习型，高效吸收新知识' }
      parts.push(`学习节奏：${paceMap[prefs.study_pace] || prefs.study_pace}`)
    }
    if (prefs.recommended_strategy) {
      parts.push(`推荐学习策略：${prefs.recommended_strategy}`)
    }
  }

  // 注入当前会话的实时信号
  const sig = sessionSignals.value
  if (sig) {
    if (sig.active_topics && sig.active_topics.length > 0) {
      parts.push(`本会话正在讨论：${sig.active_topics.slice(0, 5).join('、')}`)
    }
    if (sig.gap_keywords && sig.gap_keywords.length > 0) {
      parts.push(`当前暴露的知识薄弱点：${sig.gap_keywords.slice(0, 3).join('、')}`)
    }
    if (sig.exchange_count > 0) {
      parts.push(`本会话已进行 ${sig.exchange_count} 轮对话`)
    }
    const dist = sig.difficulty_distribution
    if (dist) {
      const total = (dist.beginner || 0) + (dist.neutral || 0) + (dist.advanced || 0)
      if (total > 0) {
        const advRatio = Math.round((dist.advanced || 0) / total * 100)
        const begRatio = Math.round((dist.beginner || 0) / total * 100)
        if (advRatio > 40) {
          parts.push(`当前对话难度偏高，建议补充基础知识`)
        } else if (begRatio > 60) {
          parts.push(`当前对话偏基础，可以适当增加挑战性内容`)
        }
      }
    }
    // 维度总结
    const dims = profileStore.liveDimensions
    if (dims && Object.keys(dims).length > 0) {
      const entries = Object.entries(dims).sort((a, b) => b[1] - a[1])
      const top = entries[0]
      const bottom = entries[entries.length - 1]
      if (top && bottom && top[1] - bottom[1] > 15) {
        parts.push(`当前能力画像：${top[0]}较强（${Math.round(top[1])}分），${bottom[0]}有待提升（${Math.round(bottom[1])}分）`)
      }
    }
  }

  return parts.join('。') + '。'
})

// ===== 雷达图数据 =====
const radarDims = computed(() => {
  const dims = profileStore.liveDimensions
  if (!dims || typeof dims !== 'object' || Object.keys(dims).length === 0) return []

  const labelMap = {
    '理论知识': '理论知识',
    '实践能力': '实践能力',
    '问题解决': '问题解决',
    '创新思维': '创新思维',
    '协作能力': '协作能力'
  }

  return Object.entries(dims).map(([k, v]) => ({
    key: k,
    label: labelMap[k] || k.slice(0, 4),
    value: Math.max(0, Math.min(100, Math.round(Number(v) || 0)))
  }))
})

function radarAngle(index) {
  const n = radarDims.value.length
  if (n === 0) return 0
  return (2 * Math.PI * index) / n
}

function getRadarPoints(scaleValue) {
  const dims = radarDims.value
  if (dims.length === 0) return ''
  return dims.map((d, i) => {
    const val = scaleValue !== null ? scaleValue : (d.value / 100 * 90)
    const x = 100 + val * Math.cos(radarAngle(i) - Math.PI / 2)
    const y = 100 + val * Math.sin(radarAngle(i) - Math.PI / 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

// ===== 难度分布 =====
function diffPercent(level) {
  const dist = sessionSignals.value?.difficulty_distribution || {}
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  return total > 0 ? Math.round((dist[level] || 0) / total * 100) + '%' : '33%'
}

const diffLabel = computed(() => {
  const dist = sessionSignals.value?.difficulty_distribution || {}
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  if (total === 0) return '中等'
  const max = Math.max(dist.beginner || 0, dist.neutral || 0, dist.advanced || 0)
  if (max === (dist.advanced || 0)) return '进阶'
  if (max === (dist.beginner || 0)) return '入门'
  return '中等'
})

function barColor(v) {
  if (v >= 80) return '#5B8FA5'
  if (v >= 60) return '#C1783A'
  if (v >= 40) return '#DF9B2C'
  return '#E6A77E'
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return (d.getMonth() + 1) + '-' + d.getDate() + ' ' +
    String(d.getHours()).padStart(2, '0') + ':' +
    String(d.getMinutes()).padStart(2, '0')
}

async function refresh() { await profileStore.loadBasicProfile(true) }

onMounted(() => {
  if (!profileStore.hasProfile) {
    profileStore.loadBasicProfile()
  }
})
</script>

<style scoped>
.pp-root {
  width: 340px;
  min-width: 340px;
  height: 100%;
  position: relative;
  background: #FAFBFC;
  border-left: 1px solid #E8ECF3;
  display: flex;
  flex-direction: column;
  transition: width 0.3s, min-width 0.3s;
  font-size: 13px;
  color: #333;
  overflow: hidden;
}
.pp-root.collapsed {
  width: 36px;
  min-width: 36px;
}
.pp-toggle {
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: #fff;
  border: 1px solid #E8ECF3;
  border-radius: 6px 0 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  font-size: 10px;
  color: #999;
  transition: color 0.2s;
}
.pp-toggle:hover { color: #5B6AF0; }
.pp-inner {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 头部 */
.pp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pp-title {
  font-size: 16px;
  font-weight: 700;
  color: #1D2129;
}
.pp-btn {
  background: #F0F5FF;
  border: 1px solid #5B6AF0;
  color: #5B6AF0;
  padding: 4px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s;
}
.pp-btn:hover { background: #5B6AF0; color: #fff; }
.pp-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 会话标签 */
.pp-session-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #EEF0FF;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #5B6AF0;
}
.pp-exchange-badge {
  font-size: 10px;
  background: #5B6AF0;
  color: #fff;
  padding: 1px 8px;
  border-radius: 10px;
  font-weight: 500;
}

/* 加载 */
.pp-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px 0;
  justify-content: center;
  color: #999;
  font-size: 13px;
}

/* 分区 */
.pp-section {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid #E8ECF3;
}
.pp-section-title {
  font-size: 12px;
  font-weight: 700;
  color: #6B7280;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 完整文字画像 */
.pp-text-profile {
  font-size: 13px;
  line-height: 1.8;
  color: #374151;
  word-break: break-word;
}

/* 雷达图 */
.pp-radar-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}
.pp-radar-svg {
  width: 180px;
  height: 180px;
}

/* 维度条形图 */
.pp-dim-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.pp-dim-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pp-dim-label {
  width: 56px;
  font-size: 11px;
  color: #6B7280;
  text-align: right;
  flex-shrink: 0;
}
.pp-dim-track {
  flex: 1;
  height: 8px;
  background: #E8ECF3;
  border-radius: 4px;
  overflow: hidden;
}
.pp-dim-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.pp-dim-val {
  width: 24px;
  font-size: 11px;
  font-weight: 700;
  color: #374151;
  text-align: left;
  flex-shrink: 0;
}

/* 信号行 */
.pp-signal-row {
  margin-bottom: 10px;
}
.pp-signal-row:last-child { margin-bottom: 0; }
.pp-signal-key {
  display: block;
  font-size: 11px;
  color: #9CA3AF;
  margin-bottom: 5px;
  font-weight: 600;
}
.pp-signal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* 难度条 */
.pp-difficulty-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pp-difficulty-bar {
  display: flex;
  flex: 1;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: #E8ECF3;
}
.pp-diff-fill {
  height: 100%;
  transition: width 0.3s;
}
.pp-diff-fill.beginner { background: #67C23A; }
.pp-diff-fill.neutral { background: #E6A23C; }
.pp-diff-fill.advanced { background: #F56C6C; }
.pp-diff-label {
  font-size: 11px;
  color: #6B7280;
  white-space: nowrap;
}

/* 无会话提示 */
.pp-info-text {
  font-size: 12px;
  color: #9CA3AF;
  line-height: 1.6;
  text-align: center;
}

/* 页脚 */
.pp-footer {
  margin-top: auto;
  padding-top: 8px;
  font-size: 11px;
  color: #C9CDD4;
  text-align: center;
}

/* 滚动条 */
.pp-inner::-webkit-scrollbar { width: 4px; }
.pp-inner::-webkit-scrollbar-thumb { background: #E8ECF3; border-radius: 2px; }

/* 旋转加载 */
.pp-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #E8ECF3;
  border-top-color: #5B6AF0;
  border-radius: 50%;
  animation: pp-spin 0.8s linear infinite;
}
@keyframes pp-spin { to { transform: rotate(360deg); } }
</style>
