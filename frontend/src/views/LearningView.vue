<template>
  <div class="learning-page">
    <div class="page-header">
      <h3>我的学习路径</h3>
      <span style="color:#909399;font-size:13px;">在课程AI对话中自动生成</span>
    </div>

    <el-empty v-if="paths.length===0&&!loading" description="暂无学习路径，进入课程后在AI对话中说出你的学习目标即可自动生成" />

    <div v-loading="loading">
      <el-card v-for="path in paths" :key="path.id" class="path-card" shadow="hover" style="margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div>
            <h4>{{ path.title }}</h4>
            <p style="color:#909399;font-size:13px;margin:4px 0;">{{ path.description }}</p>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <el-tag :type="['warning','success','info'][path.status]" size="small">{{ ['进行中','已完成','已放弃'][path.status] }}</el-tag>
            <el-button text type="danger" size="small" @click="removePath(path.id)">删除</el-button>
          </div>
        </div>

        <div style="margin:16px 0;">
          <el-progress :percentage="path.totalSteps?Math.round(path.completedSteps/path.totalSteps*100):0" :stroke-width="10" :color="progressColor" />
          <div style="font-size:12px;color:#909399;margin-top:4px;">{{ path.completedSteps }} / {{ path.totalSteps }} 步</div>
        </div>

        <div v-if="path.steps&&path.steps.length">
          <div v-for="step in path.steps" :key="step.id" class="step-row" :class="'s'+step.status" @click="cycleStep(path.id, step)">
            <div class="step-dot">
              <el-icon v-if="step.status===2" color="#67c23a"><CircleCheckFilled /></el-icon>
              <el-icon v-else-if="step.status===1" color="#409eff"><CircleCheck /></el-icon>
              <div v-else class="dot-empty"></div>
            </div>
            <div class="step-line"></div>
            <div class="step-body">
              <div class="step-title">{{ step.stepOrder }}. {{ step.title }}</div>
              <div class="step-desc">{{ step.description }}</div>
            </div>
            <el-tag size="small" :type="['info','','success'][step.status]" style="width:70px;text-align:center;">
              {{ ['待开始','进行中','已完成'][step.status] }}
            </el-tag>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { learningApi } from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { CircleCheckFilled, CircleCheck } from '@element-plus/icons-vue';

const paths = ref([]);
const loading = ref(false);
const progressColor = [{color:'#f56c6c',percentage:20},{color:'#e6a23c',percentage:50},{color:'#409eff',percentage:80},{color:'#67c23a',percentage:100}];

onMounted(() => loadPaths());

async function loadPaths() { loading.value=true; try { const r=await learningApi.listPaths(); if(r.code===200) paths.value=r.data||[]; } catch{} finally {loading.value=false;} }

function cycleStep(pathId, step) {
  const next = step.status === 2 ? 0 : step.status + 1;
  learningApi.updateStepStatus(pathId, step.id, ['pending','in_progress','completed'][next]).then(() => loadPaths());
}

async function removePath(id) {
  try {
    await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' });
    await learningApi.deletePath(id);
    await loadPaths();
    ElMessage.success('已删除');
  } catch { /* cancel */ }
}
</script>

<style scoped>
.learning-page { max-width: 800px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.path-card { transition: box-shadow .2s; }
.step-row { display:flex; align-items:flex-start; gap:12px; padding:10px 0; cursor:pointer; transition:background .15s; border-radius:6px; }
.step-row:hover { background:#f5f7fa; }
.step-dot { width:24px; height:24px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.dot-empty { width:10px; height:10px; border-radius:50%; border:2px solid #c0c4cc; }
.step-line { width:2px; min-height:24px; background:#e4e7ed; flex-shrink:0; margin-top:24px; display:none; }
.step-row:not(:last-child) .step-line { display:block; }
.step-body { flex:1; }
.step-title { font-size:14px; font-weight:500; color:#303133; }
.step-desc { font-size:12px; color:#909399; margin-top:2px; }
.s2 .step-title, .s2 .step-desc { text-decoration:line-through; opacity:.6; }
</style>