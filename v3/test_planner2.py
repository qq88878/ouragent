import asyncio
import json
from src.core.llm import create_llm_provider
from src.core.agents.planner_agent import PlannerAgent
from src.core.utils import parse_llm_json

async def test():
    llm = create_llm_provider()
    agent = PlannerAgent(llm)
    
    # Build the prompt manually to see what the LLM gets
    knowledge_summary = agent._build_knowledge_summary([])
    profile_summary = agent._build_profile_summary({"learning_style": "VISUAL", "grade_level": "BEGINNER"})
    
    prompt = f"""你是教育规划专家。为课程"数据库系统概论"生成个性化学习路径。
课程描述: 基于王珊、萨师煊《数据库系统概论（第5版）》，涵盖关系模型、SQL、数据库设计、规范化理论
目标: 系统掌握数据库核心理论与应用

【知识库内容——优先使用】
{knowledge_summary}

【课程信息——知识库为空时的备选参考】
课程名称: 数据库系统概论
课程描述: 基于王珊、萨师煊《数据库系统概论（第5版）》，涵盖关系模型、SQL、数据库设计、规范化理论
当知识库暂无内容时，基于课程名称和描述中的学科领域，生成该学科公认的核心知识模块作为学习步骤。

【学生画像】
{profile_summary}

请以JSON格式输出（不要输出其他文字）:
{{
  "title": "课程名 - 学习路径主题",
  "description": "路径描述",
  "phases": [
    {{
      "phase_name": "阶段名称（包含课程术语）",
      "steps": [
        {{
          "title": "步骤标题（包含课程具体术语）",
          "description": "学什么、怎么学、学到什么程度",
          "estimated_hours": 3,
          "knowledge_ids": []
        }}
      ]
    }}
  ]
}}

规则：
1. 步骤标题必须包含数据库领域具体术语（如"关系代数与SQL查询"而非"基础入门"）
2. 至少生成5个步骤，最多15个
3. phases按知识领域划分，不是按难度划分"""

    print("=== PROMPT ===")
    print(prompt[:500])
    print("...")
    print("=== LLM RESPONSE ===")
    response = await llm.chat([{"role": "user", "content": prompt}], max_tokens=4096)
    print(response[:1000])
    print("=== PARSED ===")
    result = parse_llm_json(response, fallback={"title": "test", "steps": []})
    print(json.dumps(result, ensure_ascii=False, indent=2)[:500])

asyncio.run(test())
