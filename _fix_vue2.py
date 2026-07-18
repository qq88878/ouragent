with open("frontend/src/views/PathDetailView.vue", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add auto-trigger content + exercises generation in selectStep
old_select = """function selectStep(step) {
  currentStep.value = step;
  userAnswers.value = {};
  exerciseResults.value = null;
  // 如果有保存的练习结果则加载
  if (step.exerciseResults) {
    try {
      const data = typeof step.exerciseResults === 'string'
        ? JSON.parse(step.exerciseResults)
        : step.exerciseResults;
      exerciseResults.value = data;
    } catch {}
  }
}"""

new_select = """function selectStep(step) {
  currentStep.value = step;
  userAnswers.value = {};
  exerciseResults.value = null;
  if (step.exerciseResults) {
    try {
      const data = typeof step.exerciseResults === 'string'
        ? JSON.parse(step.exerciseResults)
        : step.exerciseResults;
      exerciseResults.value = data;
    } catch {}
  }
  // Auto-generate content and exercises if empty
  autoGenerateIfNeeded(step);
}

async function autoGenerateIfNeeded(step) {
  if (!step || !path.value) return;
  const pid = path.value.id;
  const sid = step.id;
  let needUpdate = false;
  if (!step.content || step.content.length < 20) {
    generatingContent.value = true;
    try {
      const res = await stepApi.generateContent(pid, sid);
      path.value = res.data || res;
      const updated = (path.value.steps || []).find(s => s.id === sid);
      if (updated) { currentStep.value = updated; needUpdate = false; }
    } catch (e) { /* silent */ }
    generatingContent.value = false;
  }
  if (!step.exercises || step.exercises === '{}' || (typeof step.exercises === 'string' && step.exercises.length < 20)) {
    generatingExercises.value = true;
    try {
      const res = await stepApi.generateExercises(pid, sid, 3);
      path.value = res.data || res;
      const updated = (path.value.steps || []).find(s => s.id === sid);
      if (updated) { currentStep.value = updated; }
    } catch (e) { /* silent */ }
    generatingExercises.value = false;
  }
}"""

content = content.replace(old_select, new_select)

with open("frontend/src/views/PathDetailView.vue", "w", encoding="utf-8") as f:
    f.write(content)
print("Auto-gen trigger added")
