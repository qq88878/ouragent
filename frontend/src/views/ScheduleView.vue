<template>
  <div class="schedule-page">
    <template v-if="!configured">
      <el-card class="config-card">
        <template #header>
          <span class="config-title">课表初始设置</span>
        </template>
        <el-form :model="configForm" label-width="120px">
          <el-form-item label="开学日期" required>
            <el-date-picker
              v-model="configForm.semesterStartDate"
              type="date"
              placeholder="选择开学日期"
              value-format="YYYY-MM-DD"
              style="width: 240px"
            />
          </el-form-item>
          <el-form-item label="时间段设置">
            <div class="period-list">
              <div v-for="(p, i) in configForm.periodConfig" :key="i" class="period-row">
                <el-input v-model="p.name" placeholder="名称" style="width: 100px" size="small" />
                <el-time-picker v-model="p.startTimeRaw" placeholder="开始" format="HH:mm" value-format="HH:mm" style="width: 120px" size="small" />
                <span class="period-dash">—</span>
                <el-time-picker v-model="p.endTimeRaw" placeholder="结束" format="HH:mm" value-format="HH:mm" style="width: 120px" size="small" />
                <el-button type="danger" :icon="Delete" circle size="small" @click="removePeriod(i)" :disabled="configForm.periodConfig.length <= 1" />
              </div>
            </div>
            <el-button type="primary" :icon="Plus" size="small" @click="addPeriod" style="margin-top: 8px">添加时间段</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <template v-else>
      <div class="week-nav">
        <el-button :icon="ArrowLeft" circle :disabled="weekOffset <= 0" @click="prevWeek" />
        <div class="week-info">
          <span class="week-label">第 {{ weekData?.weekNumber || 1 }} 周</span>
          <span class="week-date-range">{{ formatDate(weekData?.weekStartDate) }} — {{ formatDate(weekData?.weekEndDate) }}</span>
        </div>
        <el-button :icon="ArrowRight" circle @click="nextWeek" />
        <el-button type="primary" size="small" style="margin-left: 16px" @click="openAddCourse">添加课程</el-button>
      </div>

      <div class="schedule-body">
        <div class="course-sidebar">
          <h4>我的课程</h4>
          <div v-if="courses.length === 0" class="empty-hint">暂无课程</div>
          <div v-for="c in courses" :key="c.id" class="course-item">
            <span class="course-name">{{ c.name }}</span>
            <div class="course-actions">
              <el-button :icon="Edit" size="small" text @click="editCourse(c)" />
              <el-button :icon="Delete" size="small" text @click="handleDeleteCourse(c)" />
            </div>
          </div>
          <el-divider />
          <el-button size="small" text type="primary" style="width: 100%" @click="showConfigDialog = true">修改课表设置</el-button>
        </div>

        <div class="schedule-grid-wrapper">
          <div class="schedule-grid" ref="gridRef" @touchstart="onTouchStart" @touchend="onTouchEnd">
            <div class="grid-header">
              <div class="header-period"></div>
              <div v-for="day in weekData?.days" :key="day.dayOfWeek" class="header-day"
                   :class="{ today: isToday(day.date) }">
                <div class="day-label">{{ day.dayLabel }}</div>
                <div class="day-date">{{ formatDateShort(day.date) }}</div>
              </div>
            </div>
            <div v-for="(period, pi) in periods" :key="pi" class="grid-row">
              <div class="period-label">
                <div>{{ period.name }}</div>
                <div class="period-time">{{ period.startTime }}-{{ period.endTime }}</div>
              </div>
              <div v-for="day in weekData?.days" :key="day.dayOfWeek" class="grid-cell"
                   :class="{ 'has-course': day.periods[pi]?.courseName }">
                <template v-if="day.periods[pi]?.courseName">
                  <span class="cell-course">{{ day.periods[pi].courseName }}</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-dialog v-model="showCourseDialog" :title="editingCourse ? '编辑课程' : '添加课程'" width="500px">
        <el-form :model="courseForm" label-width="80px">
          <el-form-item label="课程名称" required>
            <el-input v-model="courseForm.name" placeholder="如：高等数学" />
          </el-form-item>
          <el-form-item label="上课周数" required>
            <el-select v-model="courseForm.weekNumbers" multiple placeholder="选择周数" style="width: 100%">
              <el-option v-for="w in 20" :key="w" :label="'第' + w + '周'" :value="w" />
            </el-select>
          </el-form-item>
          <el-form-item label="星期" required>
            <el-select v-model="courseForm.dayOfWeeks" multiple placeholder="选择星期" style="width: 100%">
              <el-option v-for="d in dayOptions" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间段" required>
            <el-select v-model="courseForm.periodIndexes" multiple placeholder="选择时间段" style="width: 100%">
              <el-option v-for="(p, i) in periods" :key="i" :label="p.name + ' (' + p.startTime + '-' + p.endTime + ')'" :value="i" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCourseDialog = false">取消</el-button>
          <el-button type="primary" @click="saveCourse" :loading="savingCourse">{{ editingCourse ? '保存' : '添加' }}</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showConfigDialog" title="修改课表设置" width="500px">
        <el-form :model="configForm" label-width="100px">
          <el-form-item label="开学日期">
            <el-date-picker v-model="configForm.semesterStartDate" type="date" value-format="YYYY-MM-DD" style="width: 240px" />
          </el-form-item>
          <el-form-item label="时间段设置">
            <div class="period-list">
              <div v-for="(p, i) in configForm.periodConfig" :key="i" class="period-row">
                <el-input v-model="p.name" placeholder="名称" style="width: 80px" size="small" />
                <el-time-picker v-model="p.startTimeRaw" placeholder="开始" format="HH:mm" value-format="HH:mm" style="width: 110px" size="small" />
                <span class="period-dash">—</span>
                <el-time-picker v-model="p.endTimeRaw" placeholder="结束" format="HH:mm" value-format="HH:mm" style="width: 110px" size="small" />
                <el-button type="danger" :icon="Delete" circle size="small" @click="removePeriod(i)" :disabled="configForm.periodConfig.length <= 1" />
              </div>
            </div>
            <el-button type="primary" :icon="Plus" size="small" @click="addPeriod" style="margin-top: 8px">添加时间段</el-button>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showConfigDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfigFromDialog" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Delete, Edit, ArrowLeft, ArrowRight } from '@element-plus/icons-vue';
import { scheduleApi } from '@/api';

const configured = ref(false);
const saving = ref(false);

const defaultPeriods = () => [
  { name: '第1节', startTime: '08:00', endTime: '08:45', startTimeRaw: '08:00', endTimeRaw: '08:45' },
  { name: '第2节', startTime: '08:55', endTime: '09:40', startTimeRaw: '08:55', endTimeRaw: '09:40' },
  { name: '第3节', startTime: '10:00', endTime: '10:45', startTimeRaw: '10:00', endTimeRaw: '10:45' },
  { name: '第4节', startTime: '10:55', endTime: '11:40', startTimeRaw: '10:55', endTimeRaw: '11:40' },
  { name: '第5节', startTime: '14:00', endTime: '14:45', startTimeRaw: '14:00', endTimeRaw: '14:45' },
  { name: '第6节', startTime: '14:55', endTime: '15:40', startTimeRaw: '14:55', endTimeRaw: '15:40' },
  { name: '第7节', startTime: '16:00', endTime: '16:45', startTimeRaw: '16:00', endTimeRaw: '16:45' },
  { name: '第8节', startTime: '16:55', endTime: '17:40', startTimeRaw: '16:55', endTimeRaw: '17:40' },
];

const configForm = ref({
  semesterStartDate: '',
  periodConfig: defaultPeriods(),
});

const periods = computed(() =>
  configForm.value.periodConfig.map(p => ({
    name: p.name,
    startTime: p.startTimeRaw || p.startTime,
    endTime: p.endTimeRaw || p.endTime,
  }))
);

function addPeriod() {
  const n = configForm.value.periodConfig.length + 1;
  configForm.value.periodConfig.push({ name: '第' + n + '节', startTime: '', endTime: '', startTimeRaw: '', endTimeRaw: '' });
}
function removePeriod(i) {
  configForm.value.periodConfig.splice(i, 1);
}

async function loadConfig() {
  try {
    const res = await scheduleApi.getConfig();
    if (res.code === 200 && res.data?.semesterStartDate) {
      configForm.value.semesterStartDate = res.data.semesterStartDate;
      if (res.data.periodConfig?.length) {
        configForm.value.periodConfig = res.data.periodConfig.map(p => ({
          ...p,
          startTimeRaw: p.startTime,
          endTimeRaw: p.endTime,
        }));
      }
      configured.value = true;
    }
  } catch {
    // 未配置或后端未就绪
  }
}

function buildConfigPayload() {
  const periodConfig = configForm.value.periodConfig.map(p => ({
    name: p.name,
    startTime: p.startTimeRaw || p.startTime,
    endTime: p.endTimeRaw || p.endTime,
  }));
  return {
    semesterStartDate: configForm.value.semesterStartDate,
    periodConfig,
  };
}

async function saveConfig() {
  if (!configForm.value.semesterStartDate) {
    ElMessage.warning('请选择开学日期');
    return;
  }
  saving.value = true;
  try {
    const payload = buildConfigPayload();
    const res = await scheduleApi.saveConfig(payload);
    if (res.code === 200) {
      ElMessage.success('配置保存成功');
      configured.value = true;
      configForm.value.periodConfig = payload.periodConfig.map(p => ({
        ...p, startTimeRaw: p.startTime, endTimeRaw: p.endTime,
      }));
      await loadWeekView();
      await loadCourses();
    } else {
      ElMessage.error(res.message || '保存失败');
    }
  } catch (e) {
    console.error('saveConfig error:', e);
    ElMessage.error('请求失败，请确认后端服务已启动');
  } finally {
    saving.value = false;
  }
}

const showConfigDialog = ref(false);
async function saveConfigFromDialog() {
  await saveConfig();
  if (configured.value) {
    showConfigDialog.value = false;
  }
}

// ========== Week View ==========
const weekOffset = ref(0);
const weekData = ref(null);

async function loadWeekView() {
  try {
    const res = await scheduleApi.getWeekView(weekOffset.value);
    if (res.code === 200) {
      weekData.value = res.data;
    }
  } catch {
    // ignored
  }
}

function prevWeek() { if (weekOffset.value > 0) { weekOffset.value--; loadWeekView(); } }
function nextWeek() { weekOffset.value++; loadWeekView(); }

let touchStartX = 0;
const gridRef = ref(null);
function onTouchStart(e) { touchStartX = e.touches[0].clientX; }
function onTouchEnd(e) {
  const diff = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(diff) > 60) {
    if (diff > 0) prevWeek(); else nextWeek();
  }
}

// ========== Courses ==========
const courses = ref([]);
const showCourseDialog = ref(false);
const editingCourse = ref(null);
const savingCourse = ref(false);
const courseForm = ref({ name: '', weekNumbers: [1], dayOfWeeks: [1], periodIndexes: [0] });

const dayOptions = [
  { label: '周一', value: 1 }, { label: '周二', value: 2 }, { label: '周三', value: 3 },
  { label: '周四', value: 4 }, { label: '周五', value: 5 }, { label: '周六', value: 6 }, { label: '周日', value: 7 },
];

function openAddCourse() {
  editingCourse.value = null;
  courseForm.value = { name: '', weekNumbers: [1], dayOfWeeks: [1], periodIndexes: [0] };
  showCourseDialog.value = true;
}

async function loadCourses() {
  try {
    const res = await scheduleApi.listCourses();
    if (res.code === 200) courses.value = res.data;
  } catch {
    // ignored
  }
}

function editCourse(c) {
  editingCourse.value = c;
  courseForm.value = {
    name: c.name,
    weekNumbers: [...c.weekNumbers],
    dayOfWeeks: [...c.dayOfWeeks],
    periodIndexes: [...c.periodIndexes],
  };
  showCourseDialog.value = true;
}


function hasConflict(newWeeks, newDays, newPeriods, excludeId) {
  for (const c of courses.value) {
    if (excludeId && c.id === excludeId) continue;
    for (const w of newWeeks) {
      if (!c.weekNumbers.includes(w)) continue;
      for (const d of newDays) {
        if (!c.dayOfWeeks.includes(d)) continue;
        for (const p of newPeriods) {
          if (c.periodIndexes.includes(p)) return c.name;
        }
      }
    }
  }
  return null;
}
async function saveCourse() {
  if (!courseForm.value.name) { ElMessage.warning('请输入课程名称'); return; }
  if (!courseForm.value.weekNumbers.length) { ElMessage.warning('请选择上课周数'); return; }
  if (!courseForm.value.dayOfWeeks.length) { ElMessage.warning('请选择星期'); return; }
  if (!courseForm.value.periodIndexes.length) { ElMessage.warning('请选择时间段'); return; }
  const conflict = hasConflict(courseForm.value.weekNumbers, courseForm.value.dayOfWeeks, courseForm.value.periodIndexes, editingCourse.value?.id);
  if (conflict) { ElMessage.warning('与课程「' + conflict + '」时间冲突，请调整'); return; }
  savingCourse.value = true;
  try {
    const payload = {
      name: courseForm.value.name,
      weekNumbers: courseForm.value.weekNumbers,
      dayOfWeeks: courseForm.value.dayOfWeeks,
      periodIndexes: courseForm.value.periodIndexes,
    };
    let res;
    if (editingCourse.value) {
      res = await scheduleApi.updateCourse(editingCourse.value.id, payload);
    } else {
      res = await scheduleApi.createCourse(payload);
    }
    if (res.code === 200) {
      ElMessage.success(editingCourse.value ? '课程已更新' : '课程已添加');
      showCourseDialog.value = false;
      editingCourse.value = null;
      await loadCourses();
      await loadWeekView();
    } else {
      ElMessage.error(res.message || '操作失败');
    }
  } catch {
    ElMessage.error('请求失败，请确认后端服务已启动');
  } finally {
    savingCourse.value = false;
  }
}

async function handleDeleteCourse(c) {
  try {
    await ElMessageBox.confirm('确定删除课程「' + c.name + '」？', '确认', { type: 'warning' });
    const res = await scheduleApi.deleteCourse(c.id);
    if (res.code === 200) {
      ElMessage.success('已删除');
      await loadCourses();
      await loadWeekView();
    } else {
      ElMessage.error(res.message || '删除失败');
    }
  } catch {
    // cancelled or error
  }
}

// ========== Helpers ==========
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日';
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
  return d.getFullYear() === today.getFullYear() &&
         d.getMonth() === today.getMonth() &&
         d.getDate() === today.getDate();
}

onMounted(async () => {
  await loadConfig();
  if (configured.value) {
    await loadWeekView();
    await loadCourses();
  }
});
</script>

<style scoped>
.schedule-page { height: 100%; }
.config-card { max-width: 700px; margin: 0 auto; }
.config-title { font-size: 18px; font-weight: 600; }
.period-list { display: flex; flex-direction: column; gap: 6px; }
.period-row { display: flex; align-items: center; gap: 8px; }
.period-dash { color: #909399; }

.week-nav {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 16px; padding: 12px 16px;
  background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.week-info { display: flex; flex-direction: column; align-items: center; }
.week-label { font-size: 20px; font-weight: 700; color: #303133; }
.week-date-range { font-size: 12px; color: #909399; margin-top: 2px; }

.schedule-body { display: flex; gap: 16px; height: calc(100vh - 170px); }
.course-sidebar {
  width: 180px; min-width: 180px;
  background: #fff; border-radius: 8px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow-y: auto;
}
.course-sidebar h4 { margin: 0 0 8px; font-size: 14px; color: #303133; }
.empty-hint { font-size: 13px; color: #c0c4cc; text-align: center; padding: 20px 0; }
.course-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 8px; border-radius: 4px; margin-bottom: 4px;
  background: #f0f9ff; font-size: 13px;
}
.course-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.course-actions { display: flex; gap: 2px; flex-shrink: 0; }

.schedule-grid-wrapper { flex: 1; overflow-x: auto; }
.schedule-grid {
  display: flex; flex-direction: column;
  background: #fff; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  min-width: 840px; user-select: none;
}

.grid-header { display: flex; border-bottom: 2px solid #e4e7ed; }
.header-period { width: 90px; min-width: 90px; padding: 8px 4px; font-size: 12px; color: #909399; }
.header-day {
  flex: 1; text-align: center; padding: 8px 4px;
  border-left: 1px solid #ebeef5;
}
.header-day.today { background: #ecf5ff; }
.day-label { font-size: 14px; font-weight: 600; color: #303133; }
.day-date { font-size: 12px; color: #909399; margin-top: 2px; }
.header-day.today .day-label { color: #409eff; }
.header-day.today .day-date { color: #409eff; }

.grid-row { display: flex; border-bottom: 1px solid #ebeef5; }
.grid-row:last-child { border-bottom: none; }
.period-label {
  width: 90px; min-width: 90px; padding: 8px 4px;
  text-align: center; font-size: 12px; color: #606266;
  border-right: 1px solid #ebeef5; display: flex;
  flex-direction: column; justify-content: center;
}
.period-time { font-size: 10px; color: #c0c4cc; }
.grid-cell {
  flex: 1; min-height: 48px; padding: 4px;
  border-left: 1px solid #ebeef5;
  display: flex; align-items: center; justify-content: center;
}
.grid-cell.has-course {
  background: #ecf5ff; border-radius: 4px; margin: 2px;
}
.cell-course { font-size: 13px; color: #409eff; font-weight: 500; text-align: center; }
</style>