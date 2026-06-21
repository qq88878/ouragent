<template>
  <div class="schedule-page">
    <!-- ====== 初始配置 ====== -->
    <template v-if="!configured">
      <div class="setup-card">
        <div class="setup-illustration">
          <svg viewBox="0 0 200 120" fill="none"><rect width="200" height="120" rx="16" fill="url(#setupGrad)"/><rect x="30" y="40" width="140" height="55" rx="6" fill="rgba(255,255,255,0.15)"/><line x1="45" y1="52" x2="155" y2="52" stroke="rgba(255,255,255,0.2)" stroke-width="1"/><line x1="45" y1="60" x2="130" y2="60" stroke="rgba(255,255,255,0.15)" stroke-width="1"/><line x1="45" y1="68" x2="145" y2="68" stroke="rgba(255,255,255,0.15)" stroke-width="1"/><defs><linearGradient id="setupGrad" x1="0" y1="0" x2="200" y2="120"><stop stop-color="#C1783A"/><stop offset="1" stop-color="#D4945A"/></linearGradient></defs></svg>
        </div>
        <h3>课表初始设置</h3>
        <p class="setup-desc">设置开学日期和时间段，即可开始使用智能课表</p>
        <el-form :model="configForm" label-width="100px" class="setup-form">
          <el-form-item label="开学日期" required>
            <el-date-picker v-model="configForm.semesterStartDate" type="date" placeholder="选择开学日期" value-format="YYYY-MM-DD" style="width: 260px" />
          </el-form-item>
          <el-form-item label="时间段">
            <div class="period-list">
              <div v-for="(p, i) in configForm.periodConfig" :key="i" class="period-row">
                <span class="period-index">{{ i + 1 }}</span>
                <el-input v-model="p.name" placeholder="名称" style="width: 110px" size="default" />
                <el-time-picker v-model="p.startTimeRaw" placeholder="开始" format="HH:mm" value-format="HH:mm" style="width: 130px" size="default" />
                <span class="period-sep">—</span>
                <el-time-picker v-model="p.endTimeRaw" placeholder="结束" format="HH:mm" value-format="HH:mm" style="width: 130px" size="default" />
                <el-button type="danger" :icon="Delete" circle size="small" @click="removePeriod(i)" :disabled="configForm.periodConfig.length <= 1" />
              </div>
            </div>
            <el-button :icon="Plus" size="small" @click="addPeriod" style="margin-top: 10px" plain>添加时间段</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveConfig" :loading="saving" size="large">开始使用 →</el-button>
          </el-form-item>
        </el-form>
      </div>
    </template>

    <!-- ====== 课表视图 ====== -->
    <template v-else>
      <!-- 统计栏 -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-num">{{ courses.length }}</span>
          <span class="stat-label">课程总数</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num">{{ displayPeriods.length }}</span>
          <span class="stat-label">每日节次</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num">{{ weekData?.weekNumber || '-' }}</span>
          <span class="stat-label">当前周次</span>
        </div>
      </div>

      <!-- 周导航 -->
      <div class="week-nav">
        <div class="nav-main">
          <el-button :icon="ArrowLeft" circle :disabled="weekOffset <= 0" @click="prevWeek" size="default" class="nav-arrow" />
          <div class="week-info">
            <div class="week-number">第 {{ weekData?.weekNumber || '-' }} 周</div>
            <div class="week-range">{{ formatDateShort(weekData?.weekStartDate) }} — {{ formatDateShort(weekData?.weekEndDate) }}</div>
          </div>
          <el-button :icon="ArrowRight" circle @click="nextWeek" size="default" class="nav-arrow" />
          <el-button size="small" plain @click="goToCurrentWeek" style="margin-left: 4px;">本周</el-button>
        </div>
        <div class="nav-actions">
          <el-button @click="showConfigDialog = true" size="small" plain>
            <el-icon :size="14"><Setting /></el-icon> 设置
          </el-button>
          <el-button type="primary" @click="openAddCourse" size="small">
            <el-icon :size="14"><Plus /></el-icon> 添加课程
          </el-button>
        </div>
      </div>

      <!-- 主体 -->
      <div class="schedule-body">
        <!-- 左侧课程列表 -->
        <div class="course-panel">
          <div class="panel-header">
            <h4>课程列表</h4>
            <el-tag size="small" round>{{ courses.length }}</el-tag>
          </div>
          <div v-if="courses.length === 0" class="panel-empty">
            <el-icon :size="28" color="#C4BAB0"><FolderOpened /></el-icon>
            <p>暂无课程</p>
            <span>点击右上角添加</span>
          </div>
          <div v-for="c in courses" :key="c.id" class="course-list-item">
            <div class="color-strip" :style="{ background: getCourseColor(c.id) }"></div>
            <div class="course-list-info">
              <div class="course-list-name">{{ c.name }}</div>
              <div class="course-list-meta">
                <span>周{{ c.dayOfWeeks?.map(d => weekDayLabel(d)).join('、') || '-' }}</span>
                <span>{{ c.periodIndexes?.map(i => displayPeriods[i]?.name || ('节次' + (i + 1))).join('、') || '-' }}</span>
                <span v-if="c.location">📍{{ c.location }}</span>
                <span>{{ formatWeekDisplay(c.weekNumbers) }}</span>
              </div>
            </div>
            <div class="course-list-actions">
              <el-button :icon="Edit" size="small" text @click="editCourse(c)" />
              <el-button :icon="Delete" size="small" text @click="handleDeleteCourse(c)" />
            </div>
          </div>
        </div>

        <!-- 右侧课表 Grid -->
        <div class="grid-container">
          <div class="schedule-grid" ref="gridRef" @touchstart="onTouchStart" @touchend="onTouchEnd">
            <div class="grid-header">
              <div class="corner-cell"><span class="corner-text">节次\星期</span></div>
              <div v-for="day in weekDays" :key="day.value" class="header-cell" :class="{ today: isToday(getDateForDay(day.value)) }">
                <div class="header-weekday">{{ day.label }}</div>
                <div class="header-date">
                  <span class="date-badge" :class="{ 'today-badge': isToday(getDateForDay(day.value)) }">
                    {{ formatDateShort(getDateForDay(day.value)) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 数据行 -->
            <div v-for="(period, pi) in displayPeriods" :key="pi" class="grid-row">
              <div class="period-cell">
                <div class="period-name">{{ period.name }}</div>
                <div class="period-time">{{ period.startTime || '--' }}<br/>{{ period.endTime || '--' }}</div>
              </div>
              <div v-for="day in weekDays" :key="day.value" class="course-cell" :class="{ 'today-col': isToday(getDateForDay(day.value)) }">
                <template v-if="getCourseAt(day.value, pi)">
                  <div class="course-block" :style="{ background: getCourseBg(getCourseAt(day.value, pi).courseId), borderLeftColor: getCourseColor(getCourseAt(day.value, pi).courseId) }">
                    <div class="course-block-name">{{ getCourseAt(day.value, pi).courseName }}</div>
                    <div v-if="getCourseAt(day.value, pi).location" class="course-block-loc">
                      <el-icon :size="11"><LocationFilled /></el-icon>
                      {{ getCourseAt(day.value, pi).location }}
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="cell-empty"></div>
                </template>
              </div>
            </div>

            <div v-if="displayPeriods.length === 0" class="grid-empty">
              <el-empty description="暂无时间段数据，请检查课表设置" :image-size="80" />
            </div>
          </div>
        </div>
      </div>

      <!-- 添加/编辑课程弹窗 -->
      <el-dialog v-model="showCourseDialog" :title="editingCourse ? '编辑课程' : '添加课程'" width="600px" :close-on-click-modal="false">
        <el-form :model="courseForm" label-width="80px" class="course-dialog-form">
          <el-form-item label="课程名称" required>
            <el-input v-model="courseForm.name" placeholder="如：高等数学" />
          </el-form-item>
          <el-form-item label="上课周数" required>
            <div class="week-picker">
              <div class="week-actions">
                <el-button size="small" @click="selectAllWeeks">全选</el-button>
                <el-button size="small" @click="clearWeeks">清空</el-button>
                <el-button size="small" @click="selectWeeksRange">按范围选择</el-button>
              </div>
              <div class="week-grid">
                <el-check-tag v-for="w in 20" :key="w" :checked="courseForm.weekNumbers.includes(w)" @change="(checked) => toggleWeek(w, checked)" size="small">{{ w }}</el-check-tag>
              </div>
              <div class="week-summary" v-if="courseForm.weekNumbers.length > 0">
                已选：{{ formatWeekDisplay(courseForm.weekNumbers) }}
              </div>
              <div class="week-summary" v-else style="color: var(--color-danger);">请至少选择一个周次</div>
            </div>
          </el-form-item>
          <el-form-item label="星期" required>
            <div class="day-check-group">
              <el-check-tag v-for="d in weekDays" :key="d.value" :checked="courseForm.dayOfWeeks.includes(d.value)" @change="(checked) => toggleDay(d.value, checked)" size="default">{{ d.label }}</el-check-tag>
            </div>
            <div class="field-hint" v-if="courseForm.dayOfWeeks.length === 0" style="color: var(--color-danger);">请至少选择一个星期</div>
          </el-form-item>
          <el-form-item label="节次" required>
            <div class="period-check-group" v-if="displayPeriods.length > 0">
              <el-check-tag v-for="(p, i) in displayPeriods" :key="i" :checked="courseForm.periodIndexes.includes(i)" @change="(checked) => togglePeriod(i, checked)" size="default">
                {{ p.name }}<br/><small>{{ p.startTime||'--' }}-{{ p.endTime||'--' }}</small>
              </el-check-tag>
            </div>
            <div v-if="displayPeriods.length === 0" class="field-hint">暂无可选节次，请先在设置中配置时间段</div>
            <div v-else-if="courseForm.periodIndexes.length === 0" class="field-hint" style="color: var(--color-danger);">请至少选择一个节次</div>
          </el-form-item>
          <el-form-item label="教室">
            <el-input v-model="courseForm.location" placeholder="如：教学楼A101" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="courseForm.remark" type="textarea" :rows="2" placeholder="选填" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCourseDialog = false">取消</el-button>
          <el-button type="primary" :loading="savingCourse" @click="saveCourse">
            {{ editingCourse ? '保存修改' : '添加课程' }}
          </el-button>
        </template>
      </el-dialog>

      <!-- 修改设置弹窗 -->
      <el-dialog v-model="showConfigDialog" title="课表设置" width="520px" @open="onConfigDialogOpen" @close="onConfigDialogClose">
        <el-form :model="configDialogForm" label-width="100px" v-if="configDialogReady">
          <el-form-item label="开学日期">
            <el-date-picker v-model="configDialogForm.semesterStartDate" type="date" value-format="YYYY-MM-DD" style="width: 240px" />
          </el-form-item>
          <el-form-item label="时间段">
            <div class="period-list">
              <div v-for="(p, i) in configDialogForm.periodConfig" :key="i" class="period-row">
                <span class="period-index">{{ i + 1 }}</span>
                <el-input v-model="p.name" placeholder="名称" style="width: 100px" size="small" />
                <el-time-picker v-model="p.startTimeRaw" format="HH:mm" value-format="HH:mm" style="width: 120px" size="small" />
                <span class="period-sep">—</span>
                <el-time-picker v-model="p.endTimeRaw" format="HH:mm" value-format="HH:mm" style="width: 120px" size="small" />
                <el-button type="danger" :icon="Delete" circle size="small" @click="removeDialogPeriod(i)" :disabled="configDialogForm.periodConfig.length <= 1" />
              </div>
            </div>
            <el-button :icon="Plus" size="small" @click="addDialogPeriod" style="margin-top: 8px" plain>添加时间段</el-button>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showConfigDialog = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveDialogConfig">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { scheduleApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Delete, Edit, ArrowLeft, ArrowRight, Setting, FolderOpened, LocationFilled } from '@element-plus/icons-vue';

// ---- State ----
const configured = ref(false);
const saving = ref(false);
const periodsRaw = ref([]);       // raw periods from API (for compatibility)
const weekData = ref(null);
const courses = ref([]);
const weekOffset = ref(0);
const gridRef = ref(null);

const configForm = reactive({
  semesterStartDate: '',
  periodConfig: [{ name: '第一节课', startTimeRaw: '08:00', endTimeRaw: '08:45' }],
});
const showConfigDialog = ref(false);
const configDialogReady = ref(false);
const configDialogForm = reactive({
  semesterStartDate: '',
  periodConfig: [{ name: '第一节课', startTimeRaw: '08:00', endTimeRaw: '08:45' }],
});

const showCourseDialog = ref(false);
const editingCourse = ref(null);
const savingCourse = ref(false);
const courseForm = reactive({ name: '', weekNumbers: [], dayOfWeeks: [], periodIndexes: [], location: '', remark: '' });

const weekDayLabels = ['', '一', '二', '三', '四', '五', '六', '日'];
const weekDays = [
  { label: '周一', value: 1 }, { label: '周二', value: 2 }, { label: '周三', value: 3 },
  { label: '周四', value: 4 }, { label: '周五', value: 5 }, { label: '周六', value: 6 }, { label: '周日', value: 7 },
];

// ---- Computed ----
// 优先用 API 返回的 periods，fallback 到 configForm.periodConfig
const displayPeriods = computed(() => {
  if (periodsRaw.value && periodsRaw.value.length > 0) return periodsRaw.value;
  // fallback: 从 config 构造
  return configForm.periodConfig.map(p => ({
    name: p.name || '',
    startTime: p.startTimeRaw || '',
    endTime: p.endTimeRaw || '',
  }));
});

// 从 weekData 获取某天某节次的课程
function getCourseAt(dayOfWeek, periodIndex) {
  if (!weekData.value?.days) return null;
  const day = weekData.value.days.find(d => d.dayOfWeek === dayOfWeek);
  if (!day?.periods) return null;
  return day.periods[periodIndex] || null;
}

// 根据 dayOfWeek 从 weekData 获取日期字符串
function getDateForDay(dayOfWeek) {
  if (!weekData.value?.days) return '';
  const day = weekData.value.days.find(d => d.dayOfWeek === dayOfWeek);
  return day?.date || '';
}

const courseColorPalette = ['#B5651D', '#5B8C5A', '#C1803A', '#5B8BA8', '#7B5EA7', '#C44B4B', '#D4945A', '#6B8C5A', '#A55B6E', '#4A8C7A'];
const getCourseColor = (id) => courseColorPalette[(id || 0) % courseColorPalette.length];
const getCourseBg = (id) => getCourseColor(id) + '12';

function weekDayLabel(d) { return weekDayLabels[d] || ''; }

// ---- Touch swipe ----
let touchStartX = 0; let touchStartY = 0;
function onTouchStart(e) { touchStartX = e.touches[0].clientX; touchStartY = e.touches[0].clientY; }
function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
    if (dx > 0) prevWeek(); else nextWeek();
  }
}

// ---- API ----
async function loadConfig() {
  try {
    const res = await scheduleApi.getConfig();
    if (res.code === 200 && res.data) {
      configForm.semesterStartDate = res.data.semesterStartDate || '';
      const pc = res.data.periodConfig || [];
      if (pc.length > 0) {
        configForm.periodConfig = pc.map(p => ({
          name: p.name || '',
          startTimeRaw: p.startTime || p.startTimeRaw || '',
          endTimeRaw: p.endTime || p.endTimeRaw || '',
        }));
      }
      configured.value = true;
    }
  } catch { configured.value = false; }
}

async function saveConfig() {
  if (!configForm.semesterStartDate) { ElMessage.warning('请选择开学日期'); return; }
  saving.value = true;
  try {
    const payload = {
      semesterStartDate: configForm.semesterStartDate,
      periodConfig: configForm.periodConfig.map(p => ({
        name: p.name, startTime: p.startTimeRaw, endTime: p.endTimeRaw,
      })),
    };
    const res = await scheduleApi.saveConfig(payload);
    if (res.code === 200) {
      ElMessage.success('配置已保存');
      configured.value = true;
      showConfigDialog.value = false;
      await loadWeekView();
      await loadCourses();
    } else {
      ElMessage.error(res.message || '保存失败');
    }
  } catch { ElMessage.error('请求失败'); }
  finally { saving.value = false; }
}

function addPeriod() {
  configForm.periodConfig.push({
    name: '第' + (configForm.periodConfig.length + 1) + '节课',
    startTimeRaw: '', endTimeRaw: '',
  });
}
function removePeriod(i) { configForm.periodConfig.splice(i, 1); }

// ---- Config dialog helpers (work on copy) ----
function onConfigDialogOpen() {
  configDialogForm.semesterStartDate = configForm.semesterStartDate;
  configDialogForm.periodConfig = configForm.periodConfig.map(p => ({
    name: p.name || '', startTimeRaw: p.startTimeRaw || '', endTimeRaw: p.endTimeRaw || '',
  }));
  configDialogReady.value = true;
}
function onConfigDialogClose() {
  configDialogReady.value = false;
}
function addDialogPeriod() {
  configDialogForm.periodConfig.push({
    name: '第' + (configDialogForm.periodConfig.length + 1) + '节课',
    startTimeRaw: '', endTimeRaw: '',
  });
}
function removeDialogPeriod(i) {
  configDialogForm.periodConfig.splice(i, 1);
}
async function saveDialogConfig() {
  if (!configDialogForm.semesterStartDate) { ElMessage.warning('请选择开学日期'); return; }
  saving.value = true;
  try {
    // Apply dialog changes to real configForm
    configForm.semesterStartDate = configDialogForm.semesterStartDate;
    configForm.periodConfig = configDialogForm.periodConfig.map(p => ({
      name: p.name || '', startTimeRaw: p.startTimeRaw || '', endTimeRaw: p.endTimeRaw || '',
    }));
    const payload = {
      semesterStartDate: configForm.semesterStartDate,
      periodConfig: configForm.periodConfig.map(p => ({
        name: p.name, startTime: p.startTimeRaw, endTime: p.endTimeRaw,
      })),
    };
    const res = await scheduleApi.saveConfig(payload);
    if (res.code === 200) {
      ElMessage.success('配置已保存');
      configured.value = true;
      showConfigDialog.value = false;
      await loadWeekView();
      await loadCourses();
    } else {
      ElMessage.error(res.message || '保存失败');
    }
  } catch { ElMessage.error('请求失败'); }
  finally { saving.value = false; }
}

async function loadWeekView() {
  try {
    const res = await scheduleApi.getWeekView(weekOffset.value);
    if (res.code === 200) {
      weekData.value = res.data;
      // 尝试多种字段名
      const rawPeriods = res.data.periods || res.data.periodConfig || res.data.timeSlots || [];
      if (rawPeriods.length > 0) {
        periodsRaw.value = rawPeriods.map(p => ({
          name: p.name || p.periodName || '',
          startTime: p.startTime || p.startTimeRaw || '',
          endTime: p.endTime || p.endTimeRaw || '',
        }));
      }
    }
  } catch (e) { console.error('loadWeekView:', e); }
}

async function loadCourses() {
  try {
    const res = await scheduleApi.listCourses();
    if (res.code === 200) courses.value = res.data || [];
  } catch {}
}

// "本周"按钮：基于开学日期计算实际当前周 offset
function goToCurrentWeek() {
  if (configForm.semesterStartDate) {
    const start = new Date(configForm.semesterStartDate);
    const now = new Date();
    const diffDays = Math.floor((now - start) / (1000 * 60 * 60 * 24));
    weekOffset.value = Math.max(0, Math.floor(diffDays / 7));
  } else {
    weekOffset.value = 0;
  }
  loadWeekView();
}

function prevWeek() { if (weekOffset.value > 0) { weekOffset.value--; loadWeekView(); } }
function nextWeek() { weekOffset.value++; loadWeekView(); }

function openAddCourse() {
  Object.assign(courseForm, { name: '', weekNumbers: [], dayOfWeeks: [], periodIndexes: [], location: '', remark: '' });
  editingCourse.value = null;
  showCourseDialog.value = true;
}

function editCourse(c) {
  Object.assign(courseForm, {
    name: c.name || '',
    weekNumbers: c.weekNumbers ? [...c.weekNumbers] : [],
    dayOfWeeks: c.dayOfWeeks ? [...c.dayOfWeeks] : [],
    periodIndexes: c.periodIndexes ? [...c.periodIndexes] : [],
    location: c.location || '', remark: c.remark || '',
  });
  editingCourse.value = c;
  showCourseDialog.value = true;
}

async function saveCourse() {
  if (!courseForm.name.trim()) { ElMessage.warning('请输入课程名称'); return; }
  if (courseForm.weekNumbers.length === 0) { ElMessage.warning('请选择上课周数'); return; }
  if (courseForm.dayOfWeeks.length === 0) { ElMessage.warning('请选择星期'); return; }
  if (courseForm.periodIndexes.length === 0) { ElMessage.warning('请选择节次'); return; }
  savingCourse.value = true;
  try {
    const payload = {
      name: courseForm.name.trim(),
      weekNumbers: [...courseForm.weekNumbers].sort((a, b) => a - b),
      dayOfWeeks: [...courseForm.dayOfWeeks].sort((a, b) => a - b),
      periodIndexes: [...courseForm.periodIndexes].sort((a, b) => a - b),
      location: courseForm.location || '', remark: courseForm.remark || '',
    };
    const res = editingCourse.value
      ? await scheduleApi.updateCourse(editingCourse.value.id, payload)
      : await scheduleApi.createCourse(payload);
    if (res.code === 200) {
      ElMessage.success(editingCourse.value ? '课程已更新' : '课程已添加');
      showCourseDialog.value = false;
      editingCourse.value = null;
      await loadCourses();
      await loadWeekView();
    } else {
      ElMessage.error(res.message || '操作失败');
    }
  } catch { ElMessage.error('请求失败'); }
  finally { savingCourse.value = false; }
}

async function handleDeleteCourse(c) {
  try {
    await ElMessageBox.confirm('确定删除课程《' + c.name + '》？', '确认', { type: 'warning' });
    const res = await scheduleApi.deleteCourse(c.id);
    if (res.code === 200) { ElMessage.success('已删除'); await loadCourses(); await loadWeekView(); }
    else { ElMessage.error(res.message || '删除失败'); }
  } catch {}
}

// ---- Week/Day/Period helpers ----
function toggleWeek(w, checked) {
  if (checked) { if (!courseForm.weekNumbers.includes(w)) courseForm.weekNumbers.push(w); }
  else { const idx = courseForm.weekNumbers.indexOf(w); if (idx >= 0) courseForm.weekNumbers.splice(idx, 1); }
}
function toggleDay(d, checked) {
  if (checked) { if (!courseForm.dayOfWeeks.includes(d)) courseForm.dayOfWeeks.push(d); }
  else { const idx = courseForm.dayOfWeeks.indexOf(d); if (idx >= 0) courseForm.dayOfWeeks.splice(idx, 1); }
}
function togglePeriod(i, checked) {
  if (checked) { if (!courseForm.periodIndexes.includes(i)) courseForm.periodIndexes.push(i); }
  else { const idx = courseForm.periodIndexes.indexOf(i); if (idx >= 0) courseForm.periodIndexes.splice(idx, 1); }
}
function selectAllWeeks() {
  courseForm.weekNumbers = Array.from({ length: 20 }, (_, i) => i + 1);
}
function clearWeeks() {
  courseForm.weekNumbers = [];
}
function selectWeeksRange() {
  ElMessageBox.prompt('请输入周次范围（如 1-18）', '选择周次范围', {
    confirmButtonText: '确定', cancelButtonText: '取消',
    inputPattern: /^\d+-\d+$/, inputErrorMessage: '格式错误，请如 1-18',
  }).then(({ value }) => {
    const [s, e] = value.split('-').map(Number);
    if (s > 0 && e >= s && e <= 20) {
      for (let i = s; i <= e; i++) { if (!courseForm.weekNumbers.includes(i)) courseForm.weekNumbers.push(i); }
    }
  }).catch(() => {});
}
function formatWeekDisplay(weeks) {
  if (!weeks || weeks.length === 0) return '';
  const sorted = [...weeks].sort((a, b) => a - b);
  const ranges = [];
  let start = sorted[0], prev = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] !== prev + 1) { ranges.push(start === prev ? `${start}` : `${start}-${prev}`); start = sorted[i]; }
    prev = sorted[i];
  }
  ranges.push(start === prev ? `${start}` : `${start}-${prev}`);
  return ranges.join(', ') + ' 周';
}

function formatDateShort(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return (d.getMonth() + 1) + '/' + d.getDate();
}
function isToday(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const today = new Date();
  return d.getFullYear() === today.getFullYear() && d.getMonth() === today.getMonth() && d.getDate() === today.getDate();
}

onMounted(async () => {
  await loadConfig();
  if (configured.value) {
    // 首次进入时跳到当前周
    if (configForm.semesterStartDate) {
      const start = new Date(configForm.semesterStartDate);
      const now = new Date();
      const diffDays = Math.floor((now - start) / (1000 * 60 * 60 * 24));
      weekOffset.value = Math.max(0, Math.floor(diffDays / 7));
    }
    await loadWeekView();
    await loadCourses();
  }
});
</script>

<style scoped>
.schedule-page { max-width: 1260px; margin: 0 auto; }

/* ===== Setup Card ===== */
.setup-card {
  max-width: 560px; margin: 0 auto; padding: 40px;
  background: var(--color-bg-card); border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card); text-align: center;
}
.setup-illustration { margin-bottom: 24px; }
.setup-illustration svg { width: 200px; height: 120px; }
.setup-card h3 { font-size: 22px; font-weight: 700; color: var(--color-text); margin-bottom: 8px; letter-spacing: -0.01em; }
.setup-desc { font-size: 14px; color: var(--color-text-muted); margin-bottom: 28px; }
.setup-form { text-align: left; }
.setup-form :deep(.el-form-item__label) { font-weight: 600; color: var(--color-text-secondary); }

.period-list { display: flex; flex-direction: column; gap: 8px; }
.period-row { display: flex; align-items: center; gap: 8px; }
.period-index {
  width: 28px; height: 28px; border-radius: 8px; background: var(--color-bg);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: var(--color-text-secondary); flex-shrink: 0;
}
.period-sep { font-size: 13px; color: var(--color-text-muted); }

/* ===== Stats Bar ===== */
.stats-bar {
  display: flex; align-items: center; justify-content: center; gap: 0;
  background: var(--color-bg-card); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card); padding: 16px 0; margin-bottom: 18px;
}
.stat-item { text-align: center; padding: 0 32px; }
.stat-num { font-size: 26px; font-weight: 700; color: var(--color-primary); display: block; line-height: 1.1; letter-spacing: -0.02em; }
.stat-label { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-divider { width: 1px; height: 32px; background: var(--color-border); }

/* ===== Week Navigation ===== */
.week-nav {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; padding: 0 4px;
}
.nav-main { display: flex; align-items: center; gap: 4px; }
.nav-arrow { border: 1px solid var(--color-border) !important; box-shadow: var(--shadow-xs); }
.week-info { text-align: center; min-width: 160px; }
.week-number { font-size: 18px; font-weight: 700; color: var(--color-text); letter-spacing: -0.01em; }
.week-range { font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }
.nav-actions { display: flex; gap: 8px; }

/* ===== Schedule Body ===== */
.schedule-body { display: flex; gap: 16px; height: calc(100vh - 260px); min-height: 400px; }

.course-panel {
  width: 260px; flex-shrink: 0; background: var(--color-bg-card);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
  display: flex; flex-direction: column; overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 18px; border-bottom: 1px solid var(--color-border);
}
.panel-header h4 { font-size: 15px; font-weight: 700; color: var(--color-text); }
.panel-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--color-text-placeholder); font-size: 13px; text-align: center; gap: 6px; }
.panel-empty p { font-weight: 600; color: var(--color-text-secondary); margin-top: 10px; }

.course-list-item { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--color-border-light); transition: background 0.15s ease; cursor: pointer; }
.course-list-item:hover { background: var(--color-bg-hover); }
.color-strip { width: 4px; height: 38px; border-radius: 2px; flex-shrink: 0; }
.course-list-info { flex: 1; min-width: 0; }
.course-list-name { font-size: 13px; font-weight: 600; color: var(--color-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.course-list-meta { display: flex; gap: 8px; margin-top: 3px; font-size: 11px; color: var(--color-text-muted); flex-wrap: wrap; }
.course-list-meta span { white-space: nowrap; }
.course-list-actions { display: flex; gap: 2px; flex-shrink: 0; opacity: 0; transition: opacity 0.15s ease; }
.course-list-item:hover .course-list-actions { opacity: 1; }

/* ===== Grid ===== */
.grid-container {
  flex: 1; overflow: hidden; background: var(--color-bg-card);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
}
.schedule-grid { min-width: 840px; height: 100%; overflow: auto; user-select: none; }
.grid-empty { display: flex; align-items: center; justify-content: center; height: 200px; }

.grid-header { display: flex; position: sticky; top: 0; z-index: 2; background: var(--color-bg-card); }
.corner-cell {
  width: 110px; min-width: 110px; padding: 14px 8px;
  border-bottom: 2px solid var(--color-border); display: flex;
  align-items: center; justify-content: center;
}
.corner-text { font-size: 11px; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.header-cell {
  flex: 1; text-align: center; padding: 12px 6px;
  border-left: 1px solid var(--color-border); border-bottom: 2px solid var(--color-border);
}
.header-cell.today { background: var(--color-primary-light); }
.header-weekday { font-size: 15px; font-weight: 700; color: var(--color-text); }
.header-date { margin-top: 5px; }
.date-badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 11px; color: var(--color-text-secondary); background: var(--color-bg); font-weight: 500; }
.today-badge { background: var(--color-primary); color: #fff; font-weight: 600; }

.grid-row { display: flex; border-bottom: 1px solid var(--color-border-light); }
.grid-row:last-child { border-bottom: none; }
.period-cell {
  width: 110px; min-width: 110px; padding: 10px 6px; text-align: center;
  border-right: 1px solid var(--color-border); display: flex;
  flex-direction: column; justify-content: center;
}
.period-name { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }
.period-time { font-size: 10px; color: var(--color-text-placeholder); margin-top: 3px; }

.course-cell { flex: 1; min-height: 60px; padding: 4px; border-left: 1px solid var(--color-border-light); display: flex; align-items: stretch; }
.course-cell.today-col { background: rgba(181,101,29,0.02); }
.cell-empty { flex: 1; border-radius: 8px; }

.course-block {
  flex: 1; padding: 8px 10px; border-radius: 8px; border-left: 4px solid;
  display: flex; flex-direction: column; justify-content: center;
  transition: all 0.2s ease; cursor: default; position: relative;
}
.course-block:hover { transform: scale(1.03); box-shadow: 0 2px 12px rgba(30,24,18,0.10); z-index: 1; }
.course-block-name { font-size: 12px; font-weight: 600; color: var(--color-text); line-height: 1.35; }
.course-block-loc { font-size: 10px; color: var(--color-text-muted); display: flex; align-items: center; gap: 3px; margin-top: 4px; }

/* ===== Course Dialog ===== */
.course-dialog-form .el-select { width: 100%; }
.week-range-row { display: flex; align-items: center; gap: 8px; }
.range-label { font-size: 13px; color: var(--color-text-secondary); white-space: nowrap; }
.week-hint { font-size: 11px; color: var(--color-text-muted); margin-top: 8px; padding-left: 4px; line-height: 1.5; }
.field-hint { font-size: 11px; color: var(--color-text-muted); margin-top: 6px; line-height: 1.4; }

.week-picker { width: 100%; }
.week-actions { display: flex; gap: 8px; margin-bottom: 10px; }
.week-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.week-grid .el-check-tag { min-width: 38px; justify-content: center; font-size: 12px; padding: 3px 4px; border-radius: 6px !important; }
.week-summary { font-size: 12px; color: var(--color-text-secondary); margin-top: 8px; font-weight: 500; }

.day-check-group { display: flex; gap: 6px; flex-wrap: wrap; }
.day-check-group .el-check-tag { min-width: 58px; justify-content: center; border-radius: 8px !important; }
.period-check-group { display: flex; gap: 6px; flex-wrap: wrap; }
.period-check-group .el-check-tag { min-width: 84px; justify-content: center; text-align: center; line-height: 1.5; border-radius: 8px !important; }
.period-check-group .el-check-tag small { font-size: 10px; color: inherit; opacity: 0.75; }
</style>