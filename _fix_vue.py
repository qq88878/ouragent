import re

file_path = r"C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\PathDetailView.vue"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "autoGenerateIfNeeded" in content:
    print("Already modified - skipping")
else:
    # Change 1: Add generatingHint after currentIndex computed
    old1 = '  return path.value.steps?.findIndex(s => s.id === currentStep.value.id) ?? -1;\n});'
    new1 = '''  return path.value.steps?.findIndex(s => s.id === currentStep.value.id) ?? -1;
});

// AI background auto-generation hint
const generatingHint = computed(() => {
  const steps = path.value.steps || [];
  const emptyContent = steps.filter(s => !s.content || s.content.length < 20).length;
  const emptyExercises = steps.filter(s => !s.exercises || s.exercises === "{}").length;
  if (emptyContent === 0 && emptyExercises === 0) return "";
  if (emptyContent > 0 && emptyExercises > 0) return \x60AI正在后台生成…… (剩${emptyContent}步内容, ${emptyExercises}步练习)\x60;
  if (emptyContent > 0) return \x60生成教学内容中… (剩${emptyContent}步)\x60;
  return \x60生成练习题中… (剩${emptyExercises}步)\x60;
});'''
    content = content.replace(old1, new1)
    print("Change 1: generatingHint added")

    # Change 2: Replace selectStep ending + add autoGenerateIfNeeded
    old2_start = "  // 如果步骤有练习结果，解析它"
    old2_end = "async function loadPath()"
    
    idx_start = content.find(old2_start)
    idx_end = content.find(old2_end, idx_start)
    
    if idx_start >= 0 and idx_end >= 0:
        new2 = """  autoGenerateIfNeeded(step);
}

let autoGenBusy = false;
async function autoGenerateIfNeeded(step) {
  if (!step || !path.value || autoGenBusy) return;
  autoGenBusy = true;
  const pid = path.value.id, sid = step.id;
  try {
    const s = (path.value.steps || []).find(x => x.id === sid) || step;
    if (!s.content || s.content.length < 20) {
      generatingContent.value = true;
      const r = await stepApi.generateContent(pid, sid);
      path.value = r.data || r;
      const u = (path.value.steps || []).find(x => x.id === sid);
      if (u) currentStep.value = u;
    }
    const cur = (path.value.steps || []).find(x => x.id === sid) || step;
    if (!cur.exercises || cur.exercises === "{}" || (typeof cur.exercises === "string" && cur.exercises.length < 20)) {
      generatingExercises.value = true;
      const r = await stepApi.generateExercises(pid, sid, 3);
      path.value = r.data || r;
      const u = (path.value.steps || []).find(x => x.id === sid);
      if (u) currentStep.value = u;
    }
  } catch(e) {}
  generatingContent.value = false;
  generatingExercises.value = false;
  autoGenBusy = false;
}

async function loadPath()"""
        
        content = content[:idx_start] + new2 + content[idx_end + len(old2_end):]
        print("Change 2: autoGenerateIfNeeded + selectStep call added")
    else:
        print(f"Change 2: markers not found! idx_start={idx_start}, idx_end={idx_end}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("File written successfully")
