with open("v3/src/core/agents/orchestrator.py", "r", encoding="utf-8") as f: oc = f.read()
with open("v3/src/api.py", "r", encoding="utf-8") as f: ac = f.read()
with open("v3/src/core/agents/planner_agent.py", "r", encoding="utf-8") as f: plc = f.read()
with open("v3/src/core/agents/profile_agent.py", "r", encoding="utf-8") as f: pc = f.read()

n = 0

# ===== 1. orchestrator: trigger condition =====
old = "if self.profile_agent and (chat_signals or study_records or evaluation_history):"
new = "if self.profile_agent and course_title:"
oc = oc.replace(old, new); n += 1; print(f"{n}. orchestrator trigger")

# ===== 2. orchestrator: knowledge_context from course_knowledge =====
old = "                knowledge_snippets = []\n                if self.rag and course_knowledge:"
new = "                knowledge_snippets = []\n                for item in (course_knowledge or [])[:10]:\n                    title = item.get(\"title\", \"\")\n                    desc = item.get(\"description\", \"\")\n                    content = item.get(\"content\", \"\")\n                    snippet = f\"[{title}]\"\n                    if desc:\n                        snippet += f\" - {desc}\"\n                    if content:\n                        snippet += f\": {content[:300]}\"\n                    knowledge_snippets.append(snippet)\n\n                if self.rag and course_knowledge:"
oc = oc.replace(old, new); n += 1; print(f"{n}. orchestrator kctx")

with open("v3/src/core/agents/orchestrator.py", "w", encoding="utf-8") as f: f.write(oc)

# ===== 3. api.py: init_db =====
old = '    logger.info("Agent Service 启动中...")\n\n    # 初始化 LLM'
new = '    logger.info("Agent Service 启动中...")\n\n    # 初始化数据库表\n    from src.db.database import init_db\n    await init_db()\n    logger.info("数据库表初始化完成")\n\n    # 初始化 LLM'
ac = ac.replace(old, new); n += 1; print(f"{n}. api init_db")

with open("v3/src/api.py", "w", encoding="utf-8") as f: f.write(ac)

# ===== 4. planner_agent: system_prompt - KEEP 8 principles, ADD rule 0 =====
old = """你的原则:
1. 由浅入深，循序渐进，先打基础再进阶
2. 根据学生画像调整侧重点和学习方式
3. 每个步骤必须详细列出需要掌握的具体知识点（3-5个知识点）
4. 每个知识点要有明确的说明：是什么、为什么重要、怎么学
5. 合理分配学习时间，给出可执行的学习建议
6. 设置阶段性检查点，让学生知道何时算"学会了"
7. 每个步骤必须关联知识库条目，指导学生按知识库内容学习
8. 在 description 中详细说明学什么、怎么学、学到什么程度

输出必须是结构化的 JSON 格式，不要输出其他文字。"""
new = """你的原则:
0. 绝不编造知识内容。所有步骤必须基于课程知识库，没有匹配知识库条目时knowledge_ids留空
1. 由浅入深，循序渐进，先打基础再进阶
2. 根据学生画像调整侧重点和学习方式
3. 每个步骤必须详细列出需要掌握的具体知识点（3-5个知识点）
4. 每个知识点要有明确的说明：是什么、为什么重要、怎么学
5. 合理分配学习时间，给出可执行的学习建议
6. 设置阶段性检查点，让学生知道何时算"学会了"
7. 每个步骤必须关联知识库条目，指导学生按知识库内容学习
8. 在 description 中详细说明学什么、怎么学、学到什么程度
9. 禁止使用泛化阶段名（如"课程入门""基础构建""知识概览""综合实战"等），阶段名必须包含课程领域术语

输出必须是结构化的 JSON 格式，不要输出其他文字。"""
plc = plc.replace(old, new); n += 1; print(f"{n}. planner sys")

# ===== 5. planner_agent: generate_path prompt - KEEP requirements, ADD example+blacklist =====
old = """        prompt = f"""你是教育规划专家。为课程"{course_title}"生成个性化学习路径。
{f"课程描述: {course_description}\n" if course_description else ""}目标: {goal}
学生画像: {profile_summary}
知识库: {knowledge_summary}
{f"课表: {schedule_text}\n" if schedule_text else ""}
要求: 分3-5阶段(phases),每阶段3-8步,共15-30步。每阶段末至少1步设is_checkpoint=true。
每步必含:order,title,description(含学什么/怎么学/学到什么程度,200字以上),knowledge_ids(知识库id数组),key_points(3-5个要点),estimated_hours(概念0.5-1h,练习1-2h,复习1-2h,项目2-3h),resources(推荐资源数组),milestone(is_checkpoint=true时必填),is_checkpoint。
输出纯JSON(不要markdown代码块,不要额外文字):
{{"title":"路径标题","description":"概述(200字)","phases":[{{"phase_name":"阶段名","phase_goal":"目标","phase_order":1,"steps":[{{"order":1,"title":"步骤","description":"详细描述","knowledge_ids":[1],"key_points":["要点1"],"estimated_hours":0.5,"resources":["资源"],"milestone":"里程碑","is_checkpoint":false}}]}}],"total_estimated_hours":30}}"""''

new = """        prompt = f"""你是教育规划专家。为课程"{course_title}"生成个性化学习路径。

【参考示例——数据库课程的正确路径】
{{
  "title": "数据库原理 - 从SQL入门到查询优化",
  "phases": [
    {{
      "phase_name": "SQL基础查询与数据操作",
      "phase_goal": "掌握SELECT/INSERT/UPDATE/DELETE及基本过滤排序",
      "phase_order": 1,
      "steps": [
        {{
          "order": 1,
          "title": "SELECT查询与WHERE过滤",
          "description": "学习SELECT语句基本结构，掌握WHERE条件过滤。通过LeetCode题目练习，达到独立写出5表以内JOIN查询的程度。",
          "knowledge_ids": [1, 2],
          "key_points": ["SELECT语法", "WHERE过滤", "ORDER BY排序", "LIMIT分页"],
          "estimated_hours": 1.5,
          "resources": ["教材第3章", "LeetCode SQL入门"],
          "milestone": "",
          "is_checkpoint": false
        }}
      ]
    }}
  ],
  "total_estimated_hours": 25
}}

{f"课程描述: {course_description}\n" if course_description else ""}目标: {goal}
学生画像: {profile_summary}
知识库: {knowledge_summary}
{f"课表: {schedule_text}\n" if schedule_text else ""}
要求: 分3-5阶段(phases),每阶段3-8步,共15-30步。每阶段末至少1步设is_checkpoint=true。
每步必含:order,title,description(含学什么/怎么学/学到什么程度,200字以上),knowledge_ids(知识库id数组,必须引用真实id，无匹配则留[]),key_points(3-5个要点),estimated_hours(概念0.5-1h,练习1-2h,复习1-2h,项目2-3h),resources(推荐资源数组),milestone(is_checkpoint=true时必填),is_checkpoint。
阶段名禁止使用: 课程入门、基础构建、知识概览、进阶提升、综合实战、项目实战、课程总结。阶段名必须包含课程领域术语（参考示例）。
输出纯JSON(不要markdown代码块,不要额外文字):
{{"title":"路径标题","description":"概述(200字)","phases":[{{"phase_name":"阶段名","phase_goal":"目标","phase_order":1,"steps":[{{"order":1,"title":"步骤","description":"详细描述","knowledge_ids":[1],"key_points":["要点1"],"estimated_hours":0.5,"resources":["资源"],"milestone":"里程碑","is_checkpoint":false}}]}}],"total_estimated_hours":30}}"""''

plc = plc.replace(old, new); n += 1; print(f"{n}. planner prompt")

with open("v3/src/core/agents/planner_agent.py", "w", encoding="utf-8") as f: f.write(plc)

# ===== 6. profile_agent: analyze_course_profile prompt =====
old = """        prompt = f"""请根据学生的基础画像和本课程的对话历史，生成该课程特有的学生理解。

【基础画像（跨课程共享）】
{profile_text}

【本课程对话历史（最近30条）】
{history_text}

【本课程学习记录】
{records_text}

【课程知识库】
{knowledge_text}

【对话信号】
{signals_text}

请输出 JSON 格式的课程画像:
{{
  "course_strengths": ["本课程中学生表现好的知识点"],
  "course_weaknesses": ["本课程中学生遇到困难的知识点"],
  "topics_discussed": ["已讨论的主题"],
  "engagement_level": "HIGH|MEDIUM|LOW",
  "questions_frequency": "FREQUENT|MODERATE|RARE",
  "summary": "一句话总结该学生在本课程中的表现"
}}

注意：只关注本课程内的表现，不要引入基础画像中已有的通用结论。"""''
new = """        prompt = f"""请根据学生的基础画像和本课程的对话历史，生成该课程特有的学生理解。

你需要输出的是教学决策依据，不要用"本会话正在讨论xxx"替代具体教学分析。

【基础画像（跨课程共享）】
{profile_text}

【本课程对话历史（最近30条）】
{history_text}

【本课程学习记录】
{records_text}

【课程知识库】
{knowledge_text}

【对话信号】
{signals_text}

请输出 JSON 格式的课程画像:
{{
  "course_strengths": ["本课程中学生表现好的知识点"],
  "course_weaknesses": ["本课程中学生遇到困难的知识点"],
  "topics_discussed": ["对话中涉及的具体知识主题，如SQL JOIN、索引原理"],
  "engagement_level": "HIGH|MEDIUM|LOW",
  "questions_frequency": "FREQUENT|MODERATE|RARE",
  "summary": "一句话总结该学生在本课程中的表现和教学建议"
}}

注意：只关注本课程内的表现，不要引入基础画像中已有的通用结论。topics_discussed必须是具体知识点名称，不能是泛化描述。"""''

pc = pc.replace(old, new); n += 1; print(f"{n}. profile course prompt")

# ===== 7. profile_agent: enrich_for_path prompt =====
# The old prompt has garbled Chinese, we need to search by unique f-string pattern
# Find the prompt that follows "knowledge_snippet = "
ks_idx = pc.find("knowledge_snippet = knowledge_context[:1500]")
prompt_idx = pc.find("prompt = f", ks_idx)
ls = pc.rfind("\n", 0, prompt_idx) + 1
em = "}}" + chr(34)*3
pe = pc.find(em, prompt_idx) + len(em)
old_enrich = pc[ls:pe]

new_enrich = '        prompt = f"""你是教育评估专家。课程"{course_title}"的学员画像分析。\n\n你需要输出的是教学决策依据，不要用"本会话正在讨论xxx"替代教学分析。请基于以下数据做出判断：\n\n[学员基础画像]\n{profile_text}\n\n[课程知识库内容节选]\n{knowledge_snippet}\n\n[近期学习记录]\n{records_text}\n\n[历史评估]\n{eval_text}\n\n[聊天信号]\n{signals_text}\n\n[历史学习路径]\n{paths_text}\n\n输出严格JSON(不要额外文字)：\n{{\n  "learning_style": "VISUAL/AUDITORY/READING/KINESTHETIC",\n  "grade_level": "ZERO_BASIC/BEGINNER/INTERMEDIATE/ADVANCED",\n  "course_specific_strengths": ["学员在本课程中已掌握的具体知识点"],\n  "course_specific_weaknesses": ["学员在课程中的薄弱知识点"],\n  "knowledge_gaps": ["需要优先学习的知识盲区，按重要性排序"],\n  "topic_interests": ["学员对课程中哪些具体主题有兴趣"],\n  "estimated_course_level": "学员在该课程中的真实水平描述（如SQL中级/数据库设计入门）",\n  "recommended_pace": "slow/moderate/fast",\n  "recommended_strategy": "针对该学员的教学策略建议",\n  "attention_points": ["教学过程中需要特别关注的方面"],\n  "preferred_resource_types": ["推荐的资源类型：视频/文档/练习/项目"],\n  "change_summary": "一句话总结学员在这门课中的定位和教学建议"\n}}\n\n规则：所有字段必须基于实际数据推断，无数据的字段留空或默认值。知识点名称必须来自知识库或课程标题相关领域。"""'

pc = pc.replace(old_enrich, new_enrich); n += 1; print(f"{n}. profile enrich prompt")

with open("v3/src/core/agents/profile_agent.py", "w", encoding="utf-8") as f: f.write(pc)

print(f"TOTAL: {n} patches")