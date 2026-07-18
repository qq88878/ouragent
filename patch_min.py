# This script reads Chinese text from the original files to avoid encoding issues.
# It makes minimal changes to orchestrator, api, planner, and profile_agent.
import re

def readf(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def writef(p, c):
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)

oc = readf("v3/src/core/agents/orchestrator.py")
ac = readf("v3/src/api.py")
plc = readf("v3/src/core/agents/planner_agent.py")
pc = readf("v3/src/core/agents/profile_agent.py")
n = 0
NL = "\n"

# === 1. orchestrator: trigger condition ===
oc = oc.replace(
    "if self.profile_agent and (chat_signals or study_records or evaluation_history):",
    "if self.profile_agent and course_title:"
)
n += 1; print(f"{n}. orchestrator trigger")

# === 2. orchestrator: knowledge_context from course_knowledge ===
old = "                knowledge_snippets = []\n                if self.rag and course_knowledge:"
new = "                knowledge_snippets = []\n                for item in (course_knowledge or [])[:10]:\n                    title = item.get(\"title\", \"\")\n                    desc = item.get(\"description\", \"\")\n                    content = item.get(\"content\", \"\")\n                    snippet = f\"[{title}]\"\n                    if desc:\n                        snippet += f\" - {desc}\"\n                    if content:\n                        snippet += f\": {content[:300]}\"\n                    knowledge_snippets.append(snippet)\n\n                if self.rag and course_knowledge:"
oc = oc.replace(old, new)
n += 1; print(f"{n}. orchestrator kctx")
writef("v3/src/core/agents/orchestrator.py", oc)

# === 3. api: init_db ===
old = '    logger.info("Agent Service \u542f\u52a8\u4e2d...")\n\n    # \u521d\u59cb\u5316 LLM'
new = '    logger.info("Agent Service \u542f\u52a8\u4e2d...")\n\n    # \u521d\u59cb\u5316\u6570\u636e\u5e93\u8868\n    from src.db.database import init_db\n    await init_db()\n    logger.info("\u6570\u636e\u5e93\u8868\u521d\u59cb\u5316\u5b8c\u6210")\n\n    # \u521d\u59cb\u5316 LLM'
ac = ac.replace(old, new)
n += 1; print(f"{n}. api init_db")
writef("v3/src/api.py", ac)

# === 4. planner: system_prompt ===
# Extract the old system_prompt block
sys_start = plc.find("\u4f60\u7684\u539f\u5219:")  # 你的原则
sys_line_start = plc.rfind(NL, 0, sys_start) + 1
# Find the closing """ after the system prompt
sys_end = plc.find('"""\n', sys_start + 200)
if sys_end < 0:
    sys_end = plc.find('"""', sys_start + 50)
sys_end += 3
old_sys = plc[sys_line_start:sys_end]

# Extract the 8 principles from original
principles = []
for i in range(1, 9):
    pat = str(i) + ". "
    p_start = old_sys.find(pat)
    if p_start >= 0:
        p_end = old_sys.find(NL, p_start)
        principles.append(old_sys[p_start:p_end])

# Build new system_prompt: add rule 0 before, rule 9 after
new_sys = '        return """\u4f60\u662f\u4e00\u4f4d\u7ecf\u9a8c\u4e30\u5bcc\u7684\u6559\u80b2\u89c4\u5212\u4e13\u5bb6\uff0c\u64c5\u957f\u5236\u5b9a\u4e2a\u6027\u5316\u5b66\u4e60\u8ba1\u5212\u3002\n\n\u4f60\u7684\u539f\u5219:\n'
new_sys += '0. \u7edd\u4e0d\u7f16\u9020\u77e5\u8bc6\u5185\u5bb9\u3002\u6240\u6709\u6b65\u9aa4\u5fc5\u987b\u57fa\u4e8e\u8bfe\u7a0b\u77e5\u8bc6\u5e93\uff0c\u6ca1\u6709\u5339\u914d\u77e5\u8bc6\u5e93\u6761\u76ee\u65f6knowledge_ids\u7559\u7a7a\n'
for p in principles:
    new_sys += p + NL
new_sys += '9. \u7981\u6b62\u4f7f\u7528\u6cdb\u5316\u9636\u6bb5\u540d\uff08\u5982\u201c\u8bfe\u7a0b\u5165\u95e8\u201d\u201c\u57fa\u7840\u6784\u5efa\u201d\u201c\u77e5\u8bc6\u6982\u89c8\u201d\u201c\u7efc\u5408\u5b9e\u6218\u201d\u7b49\uff09\uff0c\u9636\u6bb5\u540d\u5fc5\u987b\u5305\u542b\u8bfe\u7a0b\u9886\u57df\u672f\u8bed\n\n\u8f93\u51fa\u5fc5\u987b\u662f\u7ed3\u6784\u5316\u7684 JSON \u683c\u5f0f\uff0c\u4e0d\u8981\u8f93\u51fa\u5176\u4ed6\u6587\u5b57\u3002"""'

plc = plc.replace(old_sys, new_sys)
n += 1; print(f"{n}. planner sys")
writef("v3/src/core/agents/planner_agent.py", plc)

# === 5. planner: generate_path prompt ===
pg_start = plc.find("\u4f60\u662f\u6559\u80b2\u89c4\u5212\u4e13\u5bb6\u3002\u4e3a\u8bfe\u7a0b")  # 你是教育规划专家。为课程
if pg_start < 0:
    pg_start = plc.find("prompt = f")
    while pg_start >= 0:
        if pg_start > 100:
            break
        pg_start = plc.find("prompt = f", pg_start + 1)

pg_ls = plc.rfind(NL, 0, pg_start) + 1
pg_end_marker = '}}"""'
pg_end = plc.find(pg_end_marker, pg_start) + len(pg_end_marker)
old_pg = plc[pg_ls:pg_end]

# Build example JSON (pure ASCII-safe)
example = """\u3010\u53c2\u8003\u793a\u4f8b\u2014\u2014\u6570\u636e\u5e93\u8bfe\u7a0b\u7684\u6b63\u786e\u8def\u5f84\u3011
{
  "title": "\u6570\u636e\u5e93\u539f\u7406 - \u4eceSQL\u5165\u95e8\u5230\u67e5\u8be2\u4f18\u5316",
  "phases": [
    {
      "phase_name": "SQL\u57fa\u7840\u67e5\u8be2\u4e0e\u6570\u636e\u64cd\u4f5c",
      "phase_goal": "\u638c\u63e1SELECT/INSERT/UPDATE/DELETE\u53ca\u57fa\u672c\u8fc7\u6ee4\u6392\u5e8f",
      "phase_order": 1,
      "steps": [
        {
          "order": 1,
          "title": "SELECT\u67e5\u8be2\u4e0eWHERE\u8fc7\u6ee4",
          "description": "\u5b66\u4e60SELECT\u8bed\u53e5\u57fa\u672c\u7ed3\u6784\uff0c\u638c\u63e1WHERE\u6761\u4ef6\u8fc7\u6ee4\u3002\u901a\u8fc7LeetCode\u9898\u76ee\u7ec3\u4e60\uff0c\u8fbe\u5230\u72ec\u7acb\u5199\u51fa5\u8868\u4ee5\u5185JOIN\u67e5\u8be2\u7684\u7a0b\u5ea6\u3002",
          "knowledge_ids": [1, 2],
          "key_points": ["SELECT\u8bed\u6cd5", "WHERE\u8fc7\u6ee4", "ORDER BY\u6392\u5e8f", "LIMIT\u5206\u9875"],
          "estimated_hours": 1.5,
          "resources": ["\u6559\u6750\u7b2c3\u7ae0", "LeetCode SQL\u5165\u95e8"],
          "milestone": "",
          "is_checkpoint": false
        }
      ]
    }
  ],
  "total_estimated_hours": 25
}

"""

# Insert example after the first line of the prompt body
body_start = old_pg.find(NL) + 1  # skip "prompt = f..."
first_nl = old_pg.find(NL, body_start) + 1
prompt_body = old_pg[body_start:]
new_body = prompt_body[:first_nl - body_start] + NL + example + prompt_body[first_nl - body_start:]

# Add blacklist before requirements
req_marker = "\u6bcf\u6b65\u5fc5\u542b:"  # 每步必含
req_idx = new_body.find(req_marker)
if req_idx >= 0:
    req_line_start = new_body.rfind(NL, 0, req_idx) + 1
    blacklist = "\u9636\u6bb5\u540d\u7981\u6b62\u4f7f\u7528: \u8bfe\u7a0b\u5165\u95e8\u3001\u57fa\u7840\u6784\u5efa\u3001\u77e5\u8bc6\u6982\u89c8\u3001\u8fdb\u9636\u63d0\u5347\u3001\u7efc\u5408\u5b9e\u6218\u3001\u9879\u76ee\u5b9e\u6218\u3001\u8bfe\u7a0b\u603b\u7ed3\u3002\u9636\u6bb5\u540d\u5fc5\u987b\u5305\u542b\u8bfe\u7a0b\u9886\u57df\u672f\u8bed\uff08\u53c2\u8003\u793a\u4f8b\uff09\u3002\n"
    new_body = new_body[:req_line_start] + blacklist + new_body[req_line_start:]

new_pg = old_pg[:body_start] + new_body
plc = plc.replace(old_pg, new_pg)
n += 1; print(f"{n}. planner prompt")
writef("v3/src/core/agents/planner_agent.py", plc)

# === 6. profile: analyze_course_profile prompt ===
cp_start = pc.find("\u8bf7\u6839\u636e\u5b66\u751f\u7684\u57fa\u7840\u753b\u50cf")  # 请根据学生的基础画像
if cp_start < 0:
    cp_start = pc.find("prompt = f")
    while cp_start >= 0:
        if 160 < pc.rfind(NL, 0, cp_start) < 200:
            break
        cp_start = pc.find("prompt = f", cp_start + 1)
    cp_start = pc.rfind(NL, 0, cp_start) + 1 + len("prompt = f")
    cp_start = pc.find(NL, cp_start) + 1  # body start

cp_ls = pc.rfind(NL, 0, cp_start - 1) + 1  # line with "prompt = f"
cp_end_marker = '}"""'
search_from = pc.find("\u6ce8\u610f\uff1a\u53ea\u5173\u6ce8\u672c\u8bfe\u7a0b", cp_start)  # 注意：只关注本课程
cp_end = pc.find(cp_end_marker, search_from) + len(cp_end_marker)
old_cp = pc[cp_ls:cp_end]

# Insert emphasis after first line
body_s = old_cp.find(NL) + 1
first_nl2 = old_cp.find(NL, body_s) + 1
emphasis = "\u4f60\u9700\u8981\u8f93\u51fa\u7684\u662f\u6559\u5b66\u51b3\u7b56\u4f9d\u636e\uff0c\u4e0d\u8981\u7528\u201c\u672c\u4f1a\u8bdd\u6b63\u5728\u8ba8\u8bbaxxx\u201d\u66ff\u4ee3\u5177\u4f53\u6559\u5b66\u5206\u6790\u3002\n\n"
new_cp_body = old_cp[body_s:first_nl2] + NL + emphasis + old_cp[first_nl2:]

# Improve field descriptions
new_cp_body = new_cp_body.replace(
    "\u5df2\u8ba8\u8bba\u7684\u4e3b\u9898",  # 已讨论的主题
    "\u5bf9\u8bdd\u4e2d\u6d89\u53ca\u7684\u5177\u4f53\u77e5\u8bc6\u4e3b\u9898\uff0c\u5982SQL JOIN\u3001\u7d22\u5f15\u539f\u7406"  # 对话中涉及的具体知识主题，如SQL JOIN、索引原理
)
new_cp_body = new_cp_body.replace(
    "\u4e00\u53e5\u8bdd\u603b\u7ed3\u8be5\u5b66\u751f\u5728\u672c\u8bfe\u7a0b\u4e2d\u7684\u8868\u73b0",
    "\u4e00\u53e5\u8bdd\u603b\u7ed3\u8be5\u5b66\u751f\u5728\u672c\u8bfe\u7a0b\u4e2d\u7684\u8868\u73b0\u548c\u6559\u5b66\u5efa\u8bae"
)
# Add rule at end
old_note = "\u6ce8\u610f\uff1a\u53ea\u5173\u6ce8\u672c\u8bfe\u7a0b\u5185\u7684\u8868\u73b0\uff0c\u4e0d\u8981\u5f15\u5165\u57fa\u7840\u753b\u50cf\u4e2d\u5df2\u6709\u7684\u901a\u7528\u7ed3\u8bba\u3002"
new_note = "\u6ce8\u610f\uff1a\u53ea\u5173\u6ce8\u672c\u8bfe\u7a0b\u5185\u7684\u8868\u73b0\uff0c\u4e0d\u8981\u5f15\u5165\u57fa\u7840\u753b\u50cf\u4e2d\u5df2\u6709\u7684\u901a\u7528\u7ed3\u8bba\u3002topics_discussed\u5fc5\u987b\u662f\u5177\u4f53\u77e5\u8bc6\u70b9\u540d\u79f0\uff0c\u4e0d\u80fd\u662f\u6cdb\u5316\u63cf\u8ff0\u3002"
new_cp_body = new_cp_body.replace(old_note, new_note)

new_cp = old_cp[:body_s] + new_cp_body
pc = pc.replace(old_cp, new_cp)
n += 1; print(f"{n}. profile course")

# === 7. profile: enrich_for_path prompt ===
ks_idx = pc.find("knowledge_snippet = knowledge_context[:1500]")
ep_idx = pc.find("prompt = f", ks_idx)
ep_ls = pc.rfind(NL, 0, ep_idx) + 1
ep_end = pc.find(pg_end_marker, ep_idx) + len(pg_end_marker)
old_ep = pc[ep_ls:ep_end]

# Insert emphasis
body_s3 = old_ep.find(NL) + 1
first_nl3 = old_ep.find(NL, body_s3) + 1
ep_body = old_ep[body_s3:]
emphasis3 = "\u4f60\u9700\u8981\u8f93\u51fa\u7684\u662f\u6559\u5b66\u51b3\u7b56\u4f9d\u636e\uff0c\u4e0d\u8981\u7528\u201c\u672c\u4f1a\u8bdd\u6b63\u5728\u8ba8\u8bbaxxx\u201d\u66ff\u4ee3\u6559\u5b66\u5206\u6790\u3002\u8bf7\u57fa\u4e8e\u4ee5\u4e0b\u6570\u636e\u505a\u51fa\u5224\u65ad\uff1a\n\n"
ep_body = ep_body[:first_nl3 - body_s3] + NL + emphasis3 + ep_body[first_nl3 - body_s3:]

# Fix estimated_course_level
ep_body = ep_body.replace("??/??/??", "\u5b66\u5458\u5728\u8be5\u8bfe\u7a0b\u4e2d\u7684\u771f\u5b9e\u6c34\u5e73\u63cf\u8ff0\uff08\u5982SQL\u4e2d\u7ea7/\u6570\u636e\u5e93\u8bbe\u8ba1\u5165\u95e8\uff09")

# Add rules before closing """
last_quote = ep_body.rfind('"""')
rules3 = "\n\n\u89c4\u5219\uff1a\u6240\u6709\u5b57\u6bb5\u5fc5\u987b\u57fa\u4e8e\u5b9e\u9645\u6570\u636e\u63a8\u65ad\uff0c\u65e0\u6570\u636e\u7684\u5b57\u6bb5\u7559\u7a7a\u6216\u9ed8\u8ba4\u503c\u3002\u77e5\u8bc6\u70b9\u540d\u79f0\u5fc5\u987b\u6765\u81ea\u77e5\u8bc6\u5e93\u6216\u8bfe\u7a0b\u6807\u9898\u76f8\u5173\u9886\u57df\u3002"
ep_body = ep_body[:last_quote] + rules3 + ep_body[last_quote:]

new_ep = old_ep[:body_s3] + ep_body
pc = pc.replace(old_ep, new_ep)
n += 1; print(f"{n}. profile enrich")

writef("v3/src/core/agents/profile_agent.py", pc)

print(f"TOTAL: {n} patches applied")