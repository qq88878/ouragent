"""学习计划生成工具 - 根据学生画像生成个性化学习路径"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import Tool

logger = logging.getLogger(__name__)


class StudyPlanTool(Tool):
    """
    学习计划/路径生成工具

    根据学生画像（学习风格、薄弱点、兴趣）和课程知识列表，
    调用 LLM 生成个性化的学习路径。
    """

    name = "study_plan"
    description = "生成个性化学习路径和学习计划"
    parameters = {
        "type": "object",
        "properties": {
            "student_profile": {
                "type": "object",
                "description": "学生画像（学习风格、薄弱点、兴趣等）",
            },
            "course_title": {"type": "string", "description": "课程名称"},
            "goal": {"type": "string", "description": "学习目标"},
            "knowledge_list": {
                "type": "array",
                "items": {"type": "object"},
                "description": "课程知识条目列表",
            },
        },
        "required": ["course_title"],
    }

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        course_title: str,
        student_profile: Optional[Dict[str, Any]] = None,
        goal: str = "掌握课程核心知识",
        knowledge_list: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        profile_text = json.dumps(student_profile, ensure_ascii=False) if student_profile else "无画像信息"
        knowledge_text = json.dumps(knowledge_list, ensure_ascii=False) if knowledge_list else "无知识列表"

        prompt = f"""你是一位教育规划专家。请根据以下信息生成个性化学习路径。

课程: {course_title}
学习目标: {goal}
学生画像: {profile_text}
可用知识资源: {knowledge_text}

请严格按照以下 JSON 格式输出，不要输出其他内容:
{{
  "title": "学习路径标题",
  "description": "路径描述",
  "total_steps": 总步骤数,
  "steps": [
    {{
      "order": 1,
      "title": "步骤标题",
      "description": "步骤描述和学习建议",
      "knowledge_ids": [1, 2],
      "estimated_hours": 2,
      "resources": ["推荐资源类型或链接"]
    }}
  ]
}}

要求:
- 步骤应由浅入深排列
- 根据学生画像调整侧重点（如视觉型学习者多推荐图表资源）
- 每个步骤包含具体的学习建议
"""

        messages = [
            {"role": "system", "content": "你是一个教育规划专家，只输出JSON格式的学习路径。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm.chat(messages, temperature=0.6)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM 返回的学习路径不是有效 JSON")
            return {"title": course_title, "steps": [], "raw_response": response}
        except Exception as e:
            logger.error("学习路径生成失败: %s", e)
            return {"title": course_title, "steps": [], "error": str(e)}
